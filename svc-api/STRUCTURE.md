# Structura Proiectului svc-api

Acest document prezintă structura serviciului `svc-api` și rolul fiecărui script în cadrul pipeline-ului de procesare a limbajului natural (NLP) și integrare cu baza de date orientată pe grafuri (GraphDB).

## Prezentare Generală
`svc-api` este o aplicație construită cu **FastAPI** care are rolul de a transforma descrieri de tip "Smart Home" din limbaj natural în triple RDF, de a le stoca în **GraphDB** și de a permite interogarea acestora prin **SPARQL** (inclusiv NL2SPARQL).

## Structura de Directoare și Fișiere

```text
svc-api/
├── app/
│   ├── extractors/          # Logica de extracție a informațiilor din text
│   │   ├── entity_extractor.py    # Extracție de entități (Senzori, Actuatoare, etc.) folosind spaCy/Regex
│   │   ├── relation_extractor.py  # Extracție de relații (locatedIn, communicatesWith, etc.)
│   │   └── query_builder.py       # NL2SPARQL: Mapare text -> Interogări SPARQL predefinite
│   ├── parsers/             # Utilitare pentru procesarea textului
│   │   └── text_loader.py         # Încărcare, curățare și segmentare text
│   ├── routers/             # Endpoint-urile API (FastAPI Routers)
│   │   ├── entities.py            # Acces la entitățile și relațiile extrase în ultimul run
│   │   ├── graph.py               # Export RDF (Turtle) și vizualizare stare graf
│   │   ├── process.py             # Endpoint-uri principale pentru procesare text (/process)
│   │   └── sparql.py              # Interogări SPARQL (custom și predefinite)
│   ├── config.py            # Configurația aplicației (Pydantic Settings, .env)
│   ├── graphdb_client.py    # Client pentru comunicarea cu API-ul REST al GraphDB
│   ├── main.py              # Punctul de intrare în aplicație, configurare FastAPI și routere
│   ├── models.py            # Modele de date Pydantic (Request/Response, PipelineState)
│   ├── ontology.py          # Definiții de namespace-uri, clase și proprietăți RDF
│   ├── pipeline.py          # Orchestratorul principal: NLP -> RDF -> GraphDB
│   └── rdf_writer.py        # Generarea și serializarea grafului RDF (rdflib)
├── data/                    # Stocare locală pentru date
│   ├── external/            # Date externe (ex: devices.csv, devices_ontorefine.ttl)
│   ├── input/               # Fișiere text de test
│   └── `output/              # Rezultatele procesării (fișiere .ttl)`
├── .env                     # Variabile de mediu (URL GraphDB, Repo name)
├── docker-compose.yml       # Configurare Docker pentru GraphDB
├── README.md                # Instrucțiuni de instalare și rulare
└── requirements.txt         # Dependențele Python (fastapi, spacy, rdflib, requests)
```

## Descrierea Scripturilor Principalelor

### 1. `app/main.py`
Punctul de pornire al aplicației. Configurează instanța FastAPI, Middleware-ul CORS (pentru frontend) și include toate routerele din `app/routers/`.

### 2. `app/pipeline.py`
Inima sistemului. Acesta coordonează pașii:
1.  Primește textul.
2.  Folosește `text_loader` pentru curățare.
3.  Apelează `entity_extractor` și `relation_extractor`.
4.  Construiește graful RDF via `rdf_writer`.
5.  Integreză datele externe (OntoRefine).
6.  Rulează NL2SPARQL prin `query_builder`.
7.  Uploadează rezultatul în GraphDB folosind `graphdb_client`.

### 3. `app/graphdb_client.py`
Gestionează interacțiunea cu serverul GraphDB. Conține funcții pentru crearea repository-ului, upload de date Turtle, executarea de query-uri SPARQL și exportul grafului curent. De asemenea, stochează definițiile pentru cele **6 interogări SPARQL predefinite**.

### 4. `app/extractors/query_builder.py`
Implementează funcționalitatea de **NL2SPARQL**. Analizează textul utilizatorului după cuvinte cheie și decide care dintre cele 6 interogări SPARQL predefinite este cea mai relevantă.

### 5. `app/ontology.py`
Definește schema (T-Box) a sistemului:
*   **Namespace-uri**: `SH` (Ontologie), `SH_INST` (Instanțe).
*   **Mapări**: Legătura între tipurile de entități din cod și URIRef-urile RDF corespunzătoare.

### 6. `app/rdf_writer.py`
Transformă obiectele Python (Entități și Relații) în triple RDF folosind biblioteca `rdflib`. Se ocupă de serializarea în format Turtle.

### 7. `app/config.py`
Folosește `pydantic-settings` pentru a citi configurația din variabile de mediu sau din fișierul `.env`. Gestionează setările pentru GraphDB, modelul spaCy și căile de directoare.

## Fluxul de Date (Data Flow)
1.  **Input**: Utilizatorul trimite o descriere prin `POST /process/text`.
2.  **NLP**: `pipeline.py` extrage structura logică (cine, ce face, unde).
3.  **Knowledge Graph**: `rdf_writer.py` generează triplele.
4.  **Enrichment**: Se adaugă datele comerciale (brand, preț) din `devices.csv` (via `devices_ontorefine.ttl`).
5.  **Storage**: Datele sunt trimise către GraphDB.
6.  **Query**: Dacă textul conține o întrebare, `query_builder.py` returnează rezultatele direct din baza de date în răspunsul API-ului.
