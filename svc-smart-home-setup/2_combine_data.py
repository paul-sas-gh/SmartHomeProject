import csv
import os
import requests
import sys

# Configurație GraphDB
GRAPHDB_URL = "http://localhost:7200"
REPOSITORY_NAME = "smarthome"

# Căi fișiere
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Folosim fișierul generat anterior în svc-api/data/external/
CSV_FILE_PATH = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "svc-smart-home-setup", "devices.csv"))

# Prefixuri RDF
PREFIXES = """
@prefix rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd:  <http://www.w3.org/2001/XMLSchema#> .
@prefix sh:   <http://smarthome.org/ontology#> .
@prefix shi:  <http://smarthome.org/instance#> .
"""

def generate_turtle_from_csv(csv_path):
    if not os.path.exists(csv_path):
        print(f"Eroare: Fișierul CSV nu a fost găsit la {csv_path}")
        return None

    ttl_triples = [PREFIXES]
    
    try:
        with open(csv_path, mode='r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                device_name = row['Device']
                brand = row['Brand']
                price = row['Price']
                energy_class = row['EnergyClass']
                
                # Normalizăm numele pentru URI (eliminăm spațiile dacă există, deși în CSV sunt deja compacte)
                uri_name = device_name.replace(" ", "")
                
                # Generăm triplele pentru acest device
                # Folosim shi: ca namespace pentru instanțe conform devices_ontorefine.ttl
                triple = f"""
shi:{uri_name}
    sh:brand "{brand}"^^xsd:string ;
    sh:price "{price}"^^xsd:integer ;
    sh:energyClass "{energy_class}"^^xsd:string .
"""
                ttl_triples.append(triple)
        
        return "\n".join(ttl_triples)
    except Exception as e:
        print(f"Eroare la procesarea CSV: {e}")
        return None

def upload_to_graphdb(repo_name, ttl_content):
    print(f"Se încarcă datele combinate în repository-ul '{repo_name}'...")
    url = f"{GRAPHDB_URL}/repositories/{repo_name}/statements"
    headers = {"Content-Type": "text/turtle;charset=UTF-8"}
    
    try:
        # Folosim POST pentru a adăuga triplele la cele existente
        resp = requests.post(url, data=ttl_content.encode("utf-8"), headers=headers, timeout=60)
        if resp.status_code >= 400:
            print(f"Eroare de la server (HTTP {resp.status_code}): {resp.text}")
        resp.raise_for_status()
        print(f"Datele au fost încărcate cu succes (HTTP {resp.status_code}).")
        return True
    except Exception as e:
        print(f"Eroare la comunicarea cu GraphDB: {e}")
        return False

if __name__ == "__main__":
    print("--- Start Script Combinare Date (CSV + RDF) ---")
    
    # 1. Generăm Turtle din CSV
    print(f"Citesc datele din {CSV_FILE_PATH}...")
    ttl_data = generate_turtle_from_csv(CSV_FILE_PATH)
    
    if ttl_data:
        # 2. Încărcăm în GraphDB
        if upload_to_graphdb(REPOSITORY_NAME, ttl_data):
            print("Combinarea datelor a fost finalizată cu succes.")
        else:
            print("Eroare la încărcarea datelor în GraphDB.")
            sys.exit(1)
    else:
        print("Nu s-au putut genera datele Turtle.")
        sys.exit(1)
        
    print("--- Finalizare Script ---")
