"""
query_builder.py — Transformă textul natural în interogări SPARQL.
Suportă atât mapări pe interogări predefinite, cât și construcție dinamică bazată pe entități.
"""

import logging
from app.models import ExtractionResult

logger = logging.getLogger(__name__)

def build_query_from_text(text: str, extraction: ExtractionResult | None = None) -> tuple[int | None, str | None]:
    """
    Analizează textul și returnează ID-ul interogării (dacă e cazul) și codul SPARQL.
    Se bazează acum predominant pe construcție dinamică.
    """
    text_lower = text.lower().strip()
    logger.info(f"Building query for: {text_lower}")
    
    # Construcție dinamică bazată pe extracție și cuvinte cheie
    dynamic_sparql = _build_dynamic_query(text_lower, extraction)
    if dynamic_sparql:
        return 999, dynamic_sparql # 999 = ID convențional pentru query dinamic

    return None, None

def _build_dynamic_query(text: str, extraction: ExtractionResult | None) -> str | None:
    """
    Construiește un query SPARQL bazat pe entitățile detectate și pe intenția textului.
    """
    prefixes = (
        "PREFIX sh: <http://smarthome.org/ontology#>\n"
        "PREFIX shi: <http://smarthome.org/instance#>\n"
        "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>\n"
        "PREFIX sh_spg: <http://smarthome.org/smarthome.spg#>\n"
        "PREFIX mm: <https://www.adoxx.org/mm#>\n"
    )

    # 1. Detecție Camere
    if extraction and extraction.rooms:
        room_label = extraction.rooms[0].label
        return (
            f"{prefixes}\n"
            f"SELECT ?device ?label ?type\n"
            f"WHERE {{\n"
            f"  ?room_uri rdf:type sh_spg:o_Room .\n"
            f"  ?room_uri rdfs:label ?room_label .\n"
            f"  FILTER(contains(lcase(str(?room_label)), lcase(\"{room_label}\")))\n"
            f"  \n"
            f"  ?rel mm:from ?room_uri .\n"
            f"  ?rel mm:to ?device .\n"
            f"  ?device rdf:type ?type .\n"
            f"  ?device rdfs:label ?label .\n"
            f"  FILTER(?type IN (sh_spg:o_Actuator, sh_spg:o_Sensor, sh_spg:o_Smart%20Hub))\n"
            f"}} LIMIT 100"
        )

    # 2. Detecție Dispozitive Specifice
    if extraction and extraction.devices:
        dev_uri = f"shi:{extraction.devices[0].uri_name}"
        return (
            f"{prefixes}\n"
            f"SELECT ?property ?value\n"
            f"WHERE {{\n"
            f"  {dev_uri} ?property ?value .\n"
            f"  FILTER(strstarts(str(?property), 'http://smarthome.org/ontology#'))\n"
            f"}} LIMIT 100"
        )

    # 3. Intenții bazate pe cuvinte cheie (fără mapare la ID-uri predefinite rigide)
    
    # A. Integrare completă (complexă)
    if any(kw in text for kw in ["full integration", "all details", "toate detaliile", "integrare completă"]):
        return (
            f"{prefixes}\n"
            f"SELECT ?hubLabel ?deviceLabel ?brand ?price ?energyClass\n"
            f"WHERE {{\n"
            f"  ?hub rdf:type sh_spg:o_Smart%20Hub ; rdfs:label ?hubLabel .\n"
            f"  ?rel rdf:type sh_spg:r_Communicates%20With ; mm:from ?hub ; mm:to ?device .\n"
            f"  ?device rdfs:label ?deviceLabel .\n"
            f"  ?deviceComm sh:brand ?brand ; sh:price ?price ; sh:energyClass ?energyClass .\n"
            f"  FILTER(str(?deviceComm) = concat('http://smarthome.org/instance#', str(?deviceLabel)))\n"
            f"}} ORDER BY ?hubLabel ?price"
        )

    # B. Numărare
    if any(kw in text for kw in ["câte", "cate", "how many", "count", "număr", "numar", "total"]):
        return (
            f"{prefixes}\n"
            f"SELECT (COUNT(?s) AS ?total)\n"
            f"WHERE {{\n"
            f"  ?s rdf:type ?type .\n"
            f"  FILTER(?type IN (sh_spg:o_Actuator, sh_spg:o_Sensor, sh_spg:o_Smart%20Hub))\n"
            f"}}"
        )

    # B. Atribute comerciale (Brand, Preț, Energie)
    if any(kw in text for kw in ["brand", "price", "preț", "pret", "energy", "energie", "clasa", "class"]):
        # Dacă se cere și preț mare
        if any(kw in text for kw in ["scump", "expensive", "pret mare", "preț mare", "> 500"]):
            return (
                f"{prefixes}\n"
                f"SELECT ?label ?brand ?price ?energyClass\n"
                f"WHERE {{\n"
                f"  ?deviceComm sh:brand ?brand ; sh:price ?price ; sh:energyClass ?energyClass .\n"
                f"  FILTER(?price > 500)\n"
                f"  BIND(strafter(str(?deviceComm), \"#\") AS ?label)\n"
                f"}} ORDER BY DESC(?price)"
            )
        
        # Dacă se cere și distribuție/grupare
        if any(kw in text for kw in ["distribuția", "distribution", "group by", "grupate"]):
            return (
                f"{prefixes}\n"
                f"SELECT ?class (COUNT(?device) AS ?count)\n"
                f"WHERE {{\n"
                f"  ?device sh:energyClass ?class .\n"
                f"}} GROUP BY ?class ORDER BY ?class"
            )
        # Altfel listă cu brand/preț
        return (
            f"{prefixes}\n"
            f"SELECT ?label ?brand ?price ?energyClass\n"
            f"WHERE {{\n"
            f"  ?deviceModel rdfs:label ?label .\n"
            f"  ?deviceModel rdf:type ?type .\n"
            f"  FILTER(?type IN (sh_spg:o_Actuator, sh_spg:o_Sensor, sh_spg:o_Smart%20Hub))\n"
            f"  ?deviceComm sh:brand ?brand ; sh:price ?price ; sh:energyClass ?energyClass .\n"
            f"  FILTER(str(?deviceComm) = concat('http://smarthome.org/instance#', str(?label)))\n"
            f"}} ORDER BY DESC(?price)"
        )

    # C. Conectivitate / Hubs
    if any(kw in text for kw in ["hub", "connected", "conectate", "comunică", "comunica"]):
        return (
            f"{prefixes}\n"
            f"SELECT ?hubLabel ?deviceLabel\n"
            f"WHERE {{\n"
            f"  ?hub rdf:type sh_spg:o_Smart%20Hub ; rdfs:label ?hubLabel .\n"
            f"  ?rel rdf:type sh_spg:r_Communicates%20With ; mm:from ?hub ; mm:to ?device .\n"
            f"  ?device rdfs:label ?deviceLabel .\n"
            f"}}"
        )

    # D. Listare generală (Fallback)
    if any(kw in text for kw in ["dispozitive", "devices", "list", "arată", "arata", "show", "actuatori", "actuators", "actuatoare", "senzori", "sensors"]):
        # Special case for actuators or sensors list
        target_types = ["sh_spg:o_Actuator", "sh_spg:o_Sensor", "sh_spg:o_Smart%20Hub"]
        
        if any(kw in text for kw in ["actuatori", "actuators", "actuatoare"]):
            target_types = ["sh_spg:o_Actuator"]
        elif any(kw in text for kw in ["senzori", "sensors"]):
            target_types = ["sh_spg:o_Sensor"]
        elif any(kw in text for kw in ["hub", "hubs"]):
            target_types = ["sh_spg:o_Smart%20Hub"]
            
        types_str = ", ".join(target_types)
        return (
            f"{prefixes}\n"
            f"SELECT ?device ?label ?type\n"
            f"WHERE {{\n"
            f"  ?device rdf:type ?type . ?device rdfs:label ?label .\n"
            f"  FILTER(?type IN ({types_str}))\n"
            f"}} ORDER BY ?label"
        )

    return None
