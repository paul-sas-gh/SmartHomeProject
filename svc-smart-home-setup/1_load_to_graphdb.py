import requests
import os
import sys

# Configurație GraphDB
GRAPHDB_URL = "http://localhost:7200"
REPOSITORY_NAME = "smarthome"

# Cale robustă către fișierul TTL (relativ la acest script)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TTL_FILE_PATH = os.path.join(SCRIPT_DIR, "..", "data", "SmartHomeModel.ttl")

def check_graphdb_alive():
    """Verifică dacă GraphDB este pornit."""
    try:
        response = requests.get(f"{GRAPHDB_URL}/rest/repositories", timeout=5)
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"Eroare: Nu s-a putut contacta GraphDB la {GRAPHDB_URL}. Asigurați-vă că Docker-ul rulează.")
        print(f"Detalii: {e}")
        return False

def repository_exists(repo_name):
    """Verifică dacă repository-ul există deja."""
    url = f"{GRAPHDB_URL}/rest/repositories"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        repos = resp.json()
        return any(r.get("id") == repo_name for r in repos)
    except Exception as e:
        print(f"Eroare la verificarea repository-urilor: {e}")
        return False

def create_repository(repo_name):
    """Creează un repository nou în GraphDB."""
    if repository_exists(repo_name):
        print(f"Repository-ul '{repo_name}' există deja.")
        return True

    print(f"Se creează repository-ul '{repo_name}'...")
    url = f"{GRAPHDB_URL}/rest/repositories"
    
    # Configurație standard pentru un repository GraphDB
    config_ttl = f"""
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix rep:  <http://www.openrdf.org/config/repository#> .
@prefix sr:   <http://www.openrdf.org/config/repository/sail#> .
@prefix sail: <http://www.openrdf.org/config/sail#> .
@prefix graphdb: <http://www.ontotext.com/config/graphdb#> .

[] a rep:Repository ;
   rep:repositoryID "{repo_name}" ;
   rdfs:label "{repo_name} Repository" ;
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
        print(f"Repository-ul '{repo_name}' a fost creat cu succes.")
        return True
    except Exception as e:
        print(f"Eroare la crearea repository-ului: {e}")
        return False

def upload_ttl_file(repo_name, file_path):
    """Încarcă datele din fișierul TTL în repository-ul specificat."""
    if not os.path.exists(file_path):
        print(f"Eroare: Fișierul {file_path} nu a fost găsit.")
        return False

    print(f"Se încarcă datele din {file_path} în repository-ul '{repo_name}'...")
    # Adăugăm un baseURI pentru a evita eroarea "MALFORMED DATA: no base URI has been set"
    # Folosim un namespace generic dacă nu este specificat în fișier (formatat corect cu < >)
    url = f"{GRAPHDB_URL}/repositories/{repo_name}/statements?baseURI=%3Chttp://smarthome.org/instance%23%3E"
    headers = {"Content-Type": "text/turtle;charset=UTF-8"}
    
    try:
        with open(file_path, "rb") as f:
            data = f.read()
        
        resp = requests.post(url, data=data, headers=headers, timeout=60)
        if resp.status_code >= 400:
            print(f"Eroare de la server (HTTP {resp.status_code}): {resp.text}")
        resp.raise_for_status()
        print(f"Datele au fost încărcate cu succes (HTTP {resp.status_code}).")
        return True
    except Exception as e:
        print(f"Eroare la încărcarea datelor: {e}")
        return False

if __name__ == "__main__":
    print("--- Start Script Încărcare Date în GraphDB ---")
    
    if not check_graphdb_alive():
        sys.exit(1)
        
    if create_repository(REPOSITORY_NAME):
        upload_ttl_file(REPOSITORY_NAME, TTL_FILE_PATH)
    
    print("--- Finalizare Script ---")
