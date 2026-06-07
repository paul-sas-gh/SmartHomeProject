import json
import logging
from app.config import settings
from app.clients.ollama_client import ollama_client
from app.clients.gemini_client import gemini_client
from app import graphdb_client

logger = logging.getLogger(__name__)

# Prompt pentru Agentul 1: Extracție Entități și Relații
SYSTEM_PROMPT_EXTRACTOR = """
Ești un expert în extragerea de informații din text pentru un sistem Smart Home.
Sarcina ta este să extragi entitățile (dispozitive, camere, locații generale precum "apartament") și relațiile dintre ele dintr-un text în limbaj natural.

Entitățile pot fi:
- Dispozitive (senzori, actuatoare, hub-uri).
- Camere (Bucătărie, LivingRoom, EntryRoom, KidsDorm1, KidsDorm2, ParentsDorm).
- Locații (Apartament - se referă la întreaga casă).

IMPORTANT:
- Dacă textul menționează "apartament", "toate aparatele" sau similar, adaugă o entitate {"label": "Apartament", "type": "Location"}.
- Numele camerelor trebuie să fie cele oficiale: Kitchen, LivingRoom, EntryRoom, KidsDorm1, KidsDorm2, ParentsDorm.

Relațiile pot fi:
- "se află în" (dispozitiv -> cameră/apartament)
- "comunică cu" (dispozitiv -> dispozitiv/hub)

Răspunde EXCLUSIV întrun format JSON valid cu următoarea structură:
{
  "entities": [
    {"label": "Nume Entitate", "type": "Sensor/Actuator/SmartHub/Room/Location"}
  ],
  "relations": [
    {"subject": "Nume Sursă", "predicate": "locatedIn/communicatesWith", "object": "Nume Destinație"}
  ]
}
"""

# Prompt pentru Agentul 2: Generare SPARQL
SYSTEM_PROMPT_QUERY_BUILDER = """
Ești un expert SPARQL pentru o bază de date GraphDB Smart Home.
Schema bazei de date combină un model structural (exportat din ADOxx) cu date comerciale.

PREFIX sh: <http://smarthome.org/ontology#>
PREFIX shi: <http://smarthome.org/instance#>
PREFIX sh_spg: <http://smarthome.org/smarthome.spg#>
PREFIX mm: <https://www.adoxx.org/mm#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

ONTOLOGIE (Clase și Proprietăți):
- sh_spg:o_Actuator : Clasa generală pentru actuatoare.
- sh_spg:o_Sensor : Clasa generală pentru senzori.
- sh_spg:o_Smart%20Hub : Hub central.
- sh_spg:o_Room : Camere.

DATE COMERCIALE (PROPRIETĂȚI):
- sh:brand : Brandul dispozitivului (ex: "Samsung", "Philips", "Bosch", "Sony", "Daikin", "Yale").
- sh:price : Prețul dispozitivului (numeric).
- sh:energyClass : Clasa energetică (ex: "A+++", "A++", "A+", "A", "B").

REGULI DE JOIN (IMPORTANT):
1. Dispozitivele din modelul structural (subiecte ?device) au un rdfs:label.
2. Datele comerciale sunt atașate instanțelor din namespace-ul `shi:`.
3. Join-ul se face astfel: str(?device_comercial) = concat("http://smarthome.org/instance#", str(?label))
   Unde ?label este rdfs:label al ?device din modelul structural.

EXEMPLU QUERY PENTRU FILTRARE DUPĂ BRAND (ex: Samsung):
SELECT ?device ?label ?brand WHERE {
  ?device rdf:type ?type .
  ?device rdfs:label ?label .
  FILTER(?type IN (sh_spg:o_Actuator, sh_spg:o_Sensor, sh_spg:o_Smart%20Hub))
  
  # Join cu date comerciale
  BIND(IRI(CONCAT("http://smarthome.org/instance#", STR(?label))) AS ?shi_inst)
  ?shi_inst sh:brand ?brand .
  
  FILTER(CONTAINS(LCASE(STR(?brand)), "samsung"))
}

REGULI IMPORTANTE DE LOCALIZARE:
1. NU există o legătură directă între aparate și camere în baza de date.
2. Legătura se face prin SMART HUB-URI: Un aparat este într-o cameră DACĂ este conectat (communicatesWith) la Hub-ul din acea cameră.
3. Dacă se cere "APARTAMENT" sau "toate aparatele", returnează toate instanțele de tip Actuator și Sensor fără a filtra după cameră.
4. MAPARE HUB -> CAMERĂ:
   - LivingRoom: Hub-ul cu label "Smart Hub"
   - EntryRoom: ATENȚIE! Dispozitivele din EntryRoom sunt conectate tot la "Smart Hub" (din LivingRoom).
   - Kitchen: Hub-ul cu label "Smart Hub 4"
   - KidsDorm1: Hub-ul cu label "Smart Hub 1"
   - KidsDorm2: Hub-ul cu label "Smart Hub 2"
   - ParentsDorm: Hub-ul cu label "Smart Hub 3"

RELAȚII STRUCTURALE (ADOxx):
- Relațiile de comunicare:
  ?rel rdf:type sh_spg:r_Communicates%20With .
  ?rel mm:from ?hub .
  ?rel mm:to ?device .

EXEMPLU QUERY PENTRU APARATE DINTR-O CAMERĂ (ex: Kitchen):
SELECT ?device ?label WHERE {
  ?hub rdf:type sh_spg:o_Smart%20Hub .
  ?hub rdfs:label "Smart Hub 4" .
  ?rel rdf:type sh_spg:r_Communicates%20With .
  ?rel mm:from ?hub .
  ?rel mm:to ?device .
  ?device rdfs:label ?label .
  ?device rdf:type ?type .
  FILTER(?type IN (sh_spg:o_Actuator, sh_spg:o_Sensor))
}

VALORI sh_spg:a_type: "actuator", "movement-sensor", "speaker", "air-conditioner", "temparature-sensor", "light-bulb", "coffee-machine", "smoke-sensor", "smart-tv", "alarm-bell".

REGULI DE QUERY:
- NU folosi funcția LABEL(). Folosește rdfs:label.
- Pentru filtrare pe text în label, folosește: FILTER(CONTAINS(LCASE(STR(?label)), "text")).
- Pentru filtrare pe brand/clasa energetica, folosește join-ul cu shi: descris mai sus.
- NU inventa proprietăți. Folosește mm:from și mm:to pentru relații.

Sarcina ta este să generezi un query SPARQL SELECT valid.
Răspunde EXCLUSIV cu query-ul SPARQL.
"""

class AIService:
    def __init__(self):
        self._update_client()

    def _update_client(self):
        provider = settings.llm_provider.lower()
        if provider == "gemini":
            self.client = gemini_client
            logger.info("AIService utilizează Gemini ca provider LLM.")
        else:
            self.client = ollama_client
            logger.info("AIService utilizează Ollama ca provider LLM.")

    def process_with_ai(self, text: str):
        """
        Procesează textul folosind cei doi agenți AI.
        """
        # Ne asigurăm că folosim clientul configurat (în caz că s-a schimbat la runtime/test)
        self._update_client()
        
        # Pas 1: Extracție entități
        logger.info(f"Pas 1: Extracție entități pentru: {text}")
        extraction_data = self.client.generate_json(
            prompt=f"Extrage entitățile și relațiile din următorul text: {text}",
            system_prompt=SYSTEM_PROMPT_EXTRACTOR
        )
        
        # Pas 2: Generare SPARQL
        logger.info(f"Pas 2: Generare SPARQL bazat pe: {extraction_data}")
        entities_str = json.dumps(extraction_data.get("entities", []))
        relations_str = json.dumps(extraction_data.get("relations", []))
        
        prompt_query = f"""
        Cerință utilizator: {text}
        Entități extrase: {entities_str}
        Relații extrase: {relations_str}
        
        Generează un query SPARQL pentru a răspunde cerinței.
        """
        
        sparql_query = self.client.chat(
            messages=[{"role": "user", "content": prompt_query}],
            system_prompt=SYSTEM_PROMPT_QUERY_BUILDER
        )
        
        # Curățare query (uneori LLM pune ```sparql ... ```)
        sparql_query = sparql_query.replace("```sparql", "").replace("```", "").strip()
        
        # Elimină eventuale comentarii de tip # dintr-un query de o singură linie sau formatări ciudate
        if sparql_query.startswith("#"):
             lines = sparql_query.split("\n")
             sparql_query = "\n".join([line for line in lines if not line.strip().startswith("#")])

        # Pas 3: Execuție query
        logger.info(f"Pas 3: Execuție SPARQL: {sparql_query}")
        try:
            results_dict = graphdb_client.run_sparql_query(settings.graphdb_repository, sparql_query)
            results = results_dict.get("results", {}).get("bindings", [])
            return {
                "query": sparql_query,
                "extraction": extraction_data,
                "results": results
            }
        except Exception as e:
            logger.error(f"Eroare la execuția query-ului AI: {e}")
            return {
                "query": sparql_query,
                "extraction": extraction_data,
                "error": str(e),
                "results": []
            }

ai_service = AIService()
