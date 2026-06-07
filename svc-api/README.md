# SmartHome NLP API — svc-api

Pipeline Python: **Text în limbaj natural → NLP → RDF → GraphDB**

---

## Cerințe sistem

- Python 3.13+
- Docker & Docker Compose (pentru GraphDB)

---

## Setup local

### 1. Creare virtual environment și instalare dependențe

```bash
cd svc-api
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### 2. Configurare `.env`

Copiază `.env` și ajustează după nevoie:

```bash
cp .env .env.local   # opțional, pentru valori personalizate
```

Variabile importante:
| Variabilă | Default | Descriere |
|---|---|---|
| `GRAPHDB_URL` | `http://localhost:7200` | URL GraphDB |
| `GRAPHDB_REPOSITORY` | `smarthome` | Nume repository |
| `LLM_ENABLED` | `false` | Activează apelurile LLM |
| `LLM_PROVIDER` | `ollama` | `ollama` sau `openai` |
| `OPENAI_API_KEY` | _(gol)_ | Necesar dacă `LLM_PROVIDER=openai` |

### 3. Pornire GraphDB cu Docker

```bash
docker-compose up graphdb -d
```

GraphDB va fi disponibil la: [http://localhost:7200](http://localhost:7200)

### 4. Pornire API

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API disponibil la: [http://localhost:8000](http://localhost:8000)  
Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## Verificare rapidă

```bash
curl http://localhost:8000/health
# {"status":"ok"}
```

---

## Pornire completă cu Docker Compose

```bash
docker-compose up --build
```

---

## Structură proiect

```
svc-api/
├── app/
│   ├── config.py          # pydantic-settings: toate variabilele de config
│   ├── main.py            # FastAPI app + CORS + health check
│   ├── pipeline.py        # orchestrare pipeline complet (Faza 10)
│   ├── models.py          # Pydantic models (Faza 2)
│   ├── ontology.py        # namespace-uri RDF/OWL (Faza 5)
│   ├── rdf_writer.py      # generare + serializare RDF (Faza 5)
│   ├── graphdb_client.py  # upload + SPARQL (Faza 7)
│   ├── llm_client.py      # 2 apeluri LLM în lanț (Faza 8)
│   ├── utils.py           # normalizare text, logging helpers
│   ├── extractors/
│   │   ├── entity_extractor.py   # spaCy Matcher (Faza 3)
│   │   ├── relation_extractor.py # DependencyMatcher + regex (Faza 4)
│   │   └── rule_patterns.py      # pattern-uri spaCy + regex
│   └── parsers/
│       └── text_loader.py        # citire + normalizare .txt (Faza 2)
├── data/
│   ├── input/             # fișiere text de input
│   ├── output/            # fișiere .ttl generate
│   ├── external/          # date externe OntoRefine (CSV/RDF)
│   └── ontology/          # ontologie de bază
├── tests/
│   ├── test_entities.py
│   ├── test_relations.py
│   └── test_rdf.py
├── docker-compose.yml
├── Dockerfile
├── .env
├── requirements.txt
└── README.md
```

---

## Rulare teste

```bash
pytest tests/ -v
```

---

## Faze de implementare

| Fază | Descriere | Status |
|------|-----------|--------|
| 1 | Infrastructură de bază | ✅ |
| 2 | Parsare input + modele Pydantic | — |
| 3 | Extracție entități (spaCy) | — |
| 4 | Extracție relații | — |
| 5 | Generare RDF (rdflib) | — |
| 6 | Integrare date externe OntoRefine | — |
| 7 | Persistență GraphDB + SPARQL | — |
| 8 | Integrare LLM (2 apeluri în lanț) | — |
| 9 | API REST complet (FastAPI) | — |
| 10 | Orchestrare pipeline + testare | — |
