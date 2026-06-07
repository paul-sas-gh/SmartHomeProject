"""
graphdb_client.py — Client HTTP pentru GraphDB: creare repository, upload RDF, interogări SPARQL.

GraphDB rulează în Docker pe localhost:7200.
Serviciul svc-api rulează local și comunică cu GraphDB prin HTTP.

Funcții principale:
    create_repository(repo_name)              → creează repository dacă nu există
    upload_ttl(repo_name, ttl_content)        → POST Turtle la /repositories/{repo}/statements
    clear_repository(repo_name)               → DELETE toate tripletele din repository
    run_sparql_query(repo_name, query)        → POST SPARQL SELECT, returnează dict binding-uri

Interogări predefinite (5 + 1 bonus):
    PREDEFINED_QUERIES dict — indexate 1-6
    run_predefined_query(repo_name, query_id) → rulează query-ul predefinit cu ID-ul dat
"""

import logging
from typing import Any

import requests

from app.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Namespace-uri folosite în query-uri SPARQL
# ---------------------------------------------------------------------------

_SH_ONT = "http://smarthome.org/ontology#"
_SH_INST = "http://smarthome.org/instance#"
_SH_SPG = "http://smarthome.org/smarthome.spg#"
_ADOXX_MM = "https://www.adoxx.org/mm#"

_SPARQL_PREFIXES = f"""
PREFIX rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl:  <http://www.w3.org/2002/07/owl#>
PREFIX xsd:  <http://www.w3.org/2001/XMLSchema#>
PREFIX sh:   <{_SH_ONT}>
PREFIX shi:  <{_SH_INST}>
PREFIX sh_spg: <{_SH_SPG}>
PREFIX mm:   <{_ADOXX_MM}>
""".strip()


def _base_url() -> str:
    return settings.graphdb_url.rstrip("/")


# ---------------------------------------------------------------------------
# Repository management
# ---------------------------------------------------------------------------

def repository_exists(repo_name: str) -> bool:
    """Verifică dacă repository-ul există în GraphDB."""
    url = f"{_base_url()}/rest/repositories"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        repos = resp.json()
        exists = any(r.get("id") == repo_name for r in repos)
        logger.debug("Repository '%s' exists: %s", repo_name, exists)
        return exists
    except requests.RequestException as exc:
        logger.error("Eroare la verificarea repository-urilor: %s", exc)
        raise


def create_repository(repo_name: str) -> None:
    """
    Creează un repository GraphDB dacă nu există deja.

    GraphDB 11.x acceptă configurație Turtle trimisă ca multipart/form-data
    la POST /rest/repositories (câmpul 'config').
    """
    if repository_exists(repo_name):
        logger.info("Repository '%s' există deja — skip creare.", repo_name)
        return

    url = f"{_base_url()}/rest/repositories"
    config_ttl = f"""
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix rep:  <http://www.openrdf.org/config/repository#> .
@prefix sr:   <http://www.openrdf.org/config/repository/sail#> .
@prefix sail: <http://www.openrdf.org/config/sail#> .
@prefix graphdb: <http://www.ontotext.com/config/graphdb#> .

[] a rep:Repository ;
   rep:repositoryID "{repo_name}" ;
   rdfs:label "{repo_name} Smart Home Knowledge Graph" ;
   rep:repositoryImpl [
      rep:repositoryType "graphdb:SailRepository" ;
      sr:sailImpl [
         sail:sailType "graphdb:Sail" ;
         graphdb:ruleset "rdfsplus-optimized" ;
         graphdb:disableSameAs "false"
      ]
   ] .
""".strip()

    try:
        files = {"config": ("config.ttl", config_ttl.encode("utf-8"), "text/turtle")}
        resp = requests.post(url, files=files, timeout=30)
        resp.raise_for_status()
        logger.info("Repository '%s' creat cu succes.", repo_name)
    except requests.RequestException as exc:
        logger.error("Eroare la crearea repository-ului '%s': %s", repo_name, exc)
        raise


# ---------------------------------------------------------------------------
# Upload RDF
# ---------------------------------------------------------------------------

def upload_ttl(repo_name: str, ttl_content: str) -> int:
    """
    Încarcă conținut Turtle în GraphDB prin POST la
    /repositories/{repo}/statements.

    Args:
        repo_name:   Numele repository-ului.
        ttl_content: Conținutul fișierului .ttl ca string.

    Returns:
        Numărul estimat de triple (lungimea răspunsului confirmă succesul).
    """
    url = f"{_base_url()}/repositories/{repo_name}/statements"
    headers = {"Content-Type": "text/turtle;charset=UTF-8"}
    try:
        resp = requests.post(url, data=ttl_content.encode("utf-8"), headers=headers, timeout=60)
        resp.raise_for_status()
        logger.info(
            "Upload TTL reușit în repository '%s' (%d bytes, HTTP %d).",
            repo_name, len(ttl_content.encode("utf-8")), resp.status_code,
        )
        # GraphDB returnează 204 No Content la success — query triple count
        count = _get_triple_count(repo_name)
        logger.info("Triple count după upload: %d", count)
        return count
    except requests.RequestException as exc:
        logger.error("Eroare la upload TTL în '%s': %s", repo_name, exc)
        raise


def upload_ttl_file(repo_name: str, ttl_path: str) -> int:
    """Citește un fișier .ttl de pe disc și îl încarcă în GraphDB."""
    with open(ttl_path, "r", encoding="utf-8") as f:
        content = f.read()
    logger.info("Fișier TTL citit: %s (%d bytes)", ttl_path, len(content.encode("utf-8")))
    return upload_ttl(repo_name, content)


def clear_repository(repo_name: str) -> None:
    """Șterge toate tripletele din repository (DELETE /statements)."""
    url = f"{_base_url()}/repositories/{repo_name}/statements"
    try:
        resp = requests.delete(url, timeout=30)
        resp.raise_for_status()
        logger.info("Repository '%s' golit cu succes.", repo_name)
    except requests.RequestException as exc:
        logger.error("Eroare la golirea repository-ului '%s': %s", repo_name, exc)
        raise


def _get_triple_count(repo_name: str) -> int:
    """Returnează numărul total de triple din repository via SPARQL COUNT."""
    try:
        result = run_sparql_query(repo_name, "SELECT (COUNT(*) AS ?count) WHERE { ?s ?p ?o }")
        bindings = result.get("results", {}).get("bindings", [])
        if bindings:
            return int(bindings[0]["count"]["value"])
    except Exception:
        pass
    return -1


# ---------------------------------------------------------------------------
# SPARQL query
# ---------------------------------------------------------------------------

def run_sparql_query(repo_name: str, query: str) -> dict[str, Any]:
    """
    Execută un query SPARQL SELECT pe GraphDB.

    Args:
        repo_name: Numele repository-ului.
        query:     Query SPARQL (cu sau fără PREFIX-uri — acestea sunt adăugate automat
                   dacă query-ul nu conține deja 'PREFIX' sau 'prefix').

    Returns:
        Dict SPARQL JSON (structura W3C: {'head': {...}, 'results': {'bindings': [...]}}).
    """
    url = f"{_base_url()}/repositories/{repo_name}"

    # Adaugă prefix-urile automat dacă lipsesc
    if "prefix" not in query.lower():
        full_query = f"{_SPARQL_PREFIXES}\n\n{query}"
    else:
        full_query = query

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/sparql-results+json",
    }
    try:
        resp = requests.post(url, data={"query": full_query}, headers=headers, timeout=30)
        resp.raise_for_status()
        result = resp.json()
        bindings = result.get("results", {}).get("bindings", [])
        logger.info(
            "SPARQL query pe '%s': %d rezultate returnate.",
            repo_name, len(bindings),
        )
        return result
    except requests.RequestException as exc:
        logger.error("Eroare SPARQL pe '%s': %s", repo_name, exc)
        raise


# ---------------------------------------------------------------------------
# Interogări predefinite
# ---------------------------------------------------------------------------

PREDEFINED_QUERIES: dict[int, dict[str, str]] = {
    1: {
        "name": "Toate dispozitivele din model (Actuatoare, Senzori, Hub-uri)",
        "description": "Returnează toate dispozitivele definite în modelul structural, grupate pe tip.",
        "sparql": """
SELECT ?device ?label ?type
WHERE {
  ?device rdf:type ?type .
  ?device rdfs:label ?label .
  FILTER(?type IN (sh_spg:o_Actuator, sh_spg:o_Sensor, sh_spg:o_Smart%20Hub))
}
ORDER BY ?type ?label
""".strip(),
    },
    2: {
        "name": "Dispozitive + Atribute comerciale (Brand, Preț)",
        "description": "Combină datele structurale cu datele din CSV (brand, preț) prin corelarea numelor.",
        "sparql": """
SELECT ?label ?brand ?price ?energyClass
WHERE {
  ?deviceModel rdfs:label ?label .
  ?deviceModel rdf:type ?type .
  FILTER(?type IN (sh_spg:o_Actuator, sh_spg:o_Sensor, sh_spg:o_Smart%20Hub))
  
  ?deviceComm sh:brand ?brand ;
              sh:price ?price ;
              sh:energyClass ?energyClass .
  FILTER(str(?deviceComm) = concat('http://smarthome.org/instance#', str(?label)))
}
ORDER BY DESC(?price)
""".strip(),
    },
    3: {
        "name": "Smart Hub-uri și dispozitivele conectate",
        "description": "Afișează ce dispozitive sunt controlate de fiecare Smart Hub conform relațiilor de comunicare.",
        "sparql": """
SELECT ?hubLabel ?deviceLabel
WHERE {
  ?hub rdf:type sh_spg:o_Smart%20Hub ; rdfs:label ?hubLabel .
  ?rel rdf:type sh_spg:r_Communicates%20With ;
       mm:from ?hub ;
       mm:to ?device .
  ?device rdfs:label ?deviceLabel .
}
ORDER BY ?hubLabel
""".strip(),
    },
    4: {
        "name": "Distribuția dispozitivelor pe Clase Energetice",
        "description": "Analizează eficiența energetică a dispozitivelor din casă, grupându-le pe clase (A+++, A++, etc.).",
        "sparql": """
SELECT ?energyClass (COUNT(?device) AS ?count)
WHERE {
  ?device sh:energyClass ?energyClass .
}
GROUP BY ?energyClass
ORDER BY ?energyClass
""".strip(),
    },
    5: {
        "name": "Dispozitive cu consum ridicat / Preț mare",
        "description": "Selectează dispozitivele scumpe (> 500) și clasa lor energetică.",
        "sparql": """
SELECT ?label ?brand ?price ?energyClass
WHERE {
  ?deviceComm sh:brand ?brand ;
              sh:price ?price ;
              sh:energyClass ?energyClass .
  FILTER(?price > 500)
  BIND(strafter(str(?deviceComm), "#") AS ?label)
}
ORDER BY DESC(?price)
""".strip(),
    },
    6: {
        "name": "Integrare Completă: Hub -> Dispozitiv -> Brand -> Preț",
        "description": "Query complex care traversează ierarhia de control și extrage toate detaliile disponibile.",
        "sparql": """
SELECT ?hubLabel ?deviceLabel ?brand ?price ?energyClass
WHERE {
  ?hub rdf:type sh_spg:o_Smart%20Hub ; rdfs:label ?hubLabel .
  ?rel rdf:type sh_spg:r_Communicates%20With ;
       mm:from ?hub ;
       mm:to ?device .
  ?device rdfs:label ?deviceLabel .
  
  ?deviceComm sh:brand ?brand ;
              sh:price ?price ;
              sh:energyClass ?energyClass .
  FILTER(str(?deviceComm) = concat('http://smarthome.org/instance#', str(?deviceLabel)))
}
ORDER BY ?hubLabel ?price
""".strip(),
    },
}


def run_predefined_query(repo_name: str, query_id: int) -> dict[str, Any]:
    """
    Rulează una din cele 6 interogări predefinite.

    Args:
        repo_name: Numele repository-ului GraphDB.
        query_id:  ID-ul query-ului (1-6).

    Returns:
        Dict cu 'query_name', 'description', 'results' (SPARQL JSON bindings).

    Raises:
        ValueError: Dacă query_id nu există.
    """
    if query_id not in PREDEFINED_QUERIES:
        raise ValueError(f"Query ID {query_id} inexistent. Valori valide: {list(PREDEFINED_QUERIES.keys())}")

    q = PREDEFINED_QUERIES[query_id]
    logger.info("Rulare query predefinit #%d: %s", query_id, q["name"])

    result = run_sparql_query(repo_name, q["sparql"])
    bindings = result.get("results", {}).get("bindings", [])

    return {
        "query_id": query_id,
        "query_name": q["name"],
        "description": q["description"],
        "sparql": q["sparql"],
        "result_count": len(bindings),
        "results": bindings,
    }


def get_repository_turtle(repo_name: str) -> str:
    """
    Exportă întreg repository-ul în format Turtle.
    Folosește endpoint-ul /repositories/{repo}/statements cu Accept: text/turtle.
    """
    url = f"{_base_url()}/repositories/{repo_name}/statements"
    headers = {"Accept": "text/turtle"}
    try:
        resp = requests.get(url, headers=headers, timeout=60)
        resp.raise_for_status()
        logger.info("Export Turtle reușit pentru repository '%s' (%d bytes).", repo_name, len(resp.content))
        return resp.text
    except requests.RequestException as exc:
        logger.error("Eroare la exportul Turtle din '%s': %s", repo_name, exc)
        raise


def get_all_entities(repo_name: str) -> list[dict[str, Any]]:
    """
    Extrage toate entitățile principale (Senzori, Actuatoare, Hub-uri, Camere) din GraphDB.
    """
    query = f"""
{_SPARQL_PREFIXES}
SELECT ?uri ?label ?type
WHERE {{
  {{ ?uri rdf:type sh_spg:o_Room . }}
  UNION
  {{ ?uri rdf:type sh_spg:o_Sensor . }}
  UNION
  {{ ?uri rdf:type sh_spg:o_Actuator . }}
  UNION
  {{ ?uri rdf:type sh_spg:o_Smart%20Hub . }}
  
  ?uri rdfs:label ?label .
  ?uri rdf:type ?type .
  FILTER(?type IN (sh_spg:o_Room, sh_spg:o_Sensor, sh_spg:o_Actuator, sh_spg:o_Smart%20Hub))
}}
ORDER BY ?type ?label
""".strip()
    result = run_sparql_query(repo_name, query)
    return result.get("results", {}).get("bindings", [])


def get_all_relations(repo_name: str) -> list[dict[str, Any]]:
    """
    Extrage doar relațiile de tipul "Communicates With" din GraphDB.
    """
    query = f"""
{_SPARQL_PREFIXES}
SELECT ?s_label ?p_label ?o_label ?p
WHERE {{
  ?rel mm:from ?s ; 
       mm:to ?o ; 
       rdf:type ?p .
  
  ?s rdfs:label ?s_label .
  ?o rdfs:label ?o_label .
  
  OPTIONAL {{ ?p rdfs:label ?p_label . }}
  
  FILTER(?p = sh_spg:r_Communicates%20With)
}}
""".strip()
    result = run_sparql_query(repo_name, query)
    return result.get("results", {}).get("bindings", [])
