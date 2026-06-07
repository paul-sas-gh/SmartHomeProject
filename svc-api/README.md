# SmartHome NLP API — `svc-api`

API FastAPI pentru pipeline-ul Smart Home:

**Text în limbaj natural → NLP → RDF → GraphDB → SPARQL**

---

## Ce face proiectul

`svc-api` procesează descrieri Smart Home, extrage entități și relații, generează graf RDF, îl salvează local și îl încarcă în GraphDB. În plus, expune endpoint-uri pentru:

- procesarea textului din fișier sau din body JSON;
- exportul grafului Turtle curent;
- upload-ul grafului în GraphDB;
- interogări SPARQL custom și predefinite;
- listarea entităților și relațiilor extrase din GraphDB;
- procesare AI asistată prin provider-ul configurat.

---

## Cerințe

- Python 3.13+
- Docker și Docker Compose
- GraphDB disponibil local la `http://localhost:7200`

---

## Instalare locală

### 1. Creează mediul virtual și instalează dependențele

```powershell
cd svc-api
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### 2. Configurează variabilele de mediu

Fișierul `.env` este citit automat de `app/config.py`.

Variabile importante:

| Variabilă | Default | Descriere |
|---|---:|---|
| `GRAPHDB_URL` | `http://localhost:7200` | URL-ul instanței GraphDB |
| `GRAPHDB_REPOSITORY` | `smarthome` | Repository-ul folosit de API |
| `SPACY_MODEL` | `en_core_web_sm` | Modelul spaCy folosit la NLP |
| `LLM_ENABLED` | `true` | Activează/dezactivează fluxul AI |
| `LLM_PROVIDER` | `gemini` | `gemini`, `ollama` sau alt provider suportat de implementare |
| `LLM_MODEL` | `gemini-3.1-flash-lite` | Modelul LLM folosit |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | URL Ollama |
| `OPENAI_API_KEY` | gol | Cheie OpenAI, dacă este folosită |
| `GEMINI_API_KEY` | gol | Cheie Gemini, dacă este folosită |
| `DATA_INPUT_DIR` | `data/input` | Director input |
| `DATA_OUTPUT_DIR` | `data/output` | Director output Turtle |
| `DATA_EXTERNAL_DIR` | `data/external` | Director pentru date externe |
| `ONTOLOGY_DIR` | `data/ontology` | Director pentru ontologie |
| `APP_HOST` | `0.0.0.0` | Host-ul serverului FastAPI |
| `APP_PORT` | `8000` | Portul serverului FastAPI |

---

## Pornire GraphDB

Din directorul `svc-api`:

```powershell
docker-compose up graphdb -d
```

GraphDB va fi disponibil la:

- `http://localhost:7200`

---

## Pornire API

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API va fi disponibil la:

- `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## Verificare rapidă

```powershell
Invoke-RestMethod http://localhost:8000/health
```

Răspuns așteptat:

```json
{"status":"ok"}
```

---

## Endpoint-uri disponibile

### Infra

- `GET /health` — verifică dacă serviciul rulează.

### Process

- `POST /process` — primește un fișier `.txt` și rulează pipeline-ul complet;
- `POST /process/text` — primește text direct în JSON;
- `POST /process/ai/text` — procesează textul prin fluxul AI configurat.

### Graph

- `GET /graph/turtle` — returnează graful curent serializat în Turtle;
- `POST /graph/upload` — încarcă graful curent în GraphDB.

### Extraction

- `GET /entities` — returnează entitățile extrase din GraphDB;
- `GET /relations` — returnează relațiile extrase din GraphDB.

### SPARQL

- `POST /sparql` — execută un query SPARQL custom;
- `GET /sparql/predefined/{query_id}` — execută una dintre interogările predefinite.

---

## Structura proiectului

```text
svc-api/
├── app/
│   ├── ai_service.py        # Flux AI în doi pași: extracție + query SPARQL
│   ├── clients/             # Clienți LLM (Gemini, Ollama)
│   ├── config.py            # Setări centralizate din .env
│   ├── extractors/          # Extracție entități, relații și query builder
│   ├── graphdb_client.py    # Client HTTP pentru GraphDB
│   ├── main.py              # Entry point FastAPI
│   ├── models.py            # Modele Pydantic pentru pipeline
│   ├── ontology.py          # Namespace-uri și mapări RDF
│   ├── parsers/             # Încărcare și normalizare text
│   ├── pipeline.py          # Orchestrarea NLP → RDF → GraphDB
│   ├── rdf_writer.py        # Generare și serializare RDF/Turtle
│   └── routers/             # Endpoint-uri FastAPI
├── data/
│   ├── external/            # Date externe, ex. `devices_ontorefine.ttl`
│   ├── input/               # Fișiere text de intrare
│   └── output/              # Turtle generat de pipeline
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── STRUCTURE.md
├── .env.sample
└── README.md
```

---

## Flux de lucru recomandat

1. Pornește GraphDB.
2. Pornește API-ul FastAPI.
3. Trimite un text la `POST /process/text` sau un fișier la `POST /process`.
4. Verifică rezultatul în răspunsul API sau prin `GET /graph/turtle`.
5. Încarcă graful în GraphDB cu `POST /graph/upload` dacă ai dezactivat upload-ul automat.
6. Rulează interogări SPARQL prin `POST /sparql` sau `GET /sparql/predefined/{query_id}`.

---

## Observații

- `app/pipeline.py` păstrează în memorie ultimul rezultat al procesării pentru endpoint-urile de graf și extracție.
- `app/graphdb_client.py` conține utilitare pentru repository, upload Turtle, export Turtle și query-uri SPARQL.
- `app/routers/entities.py` citește direct din GraphDB și decodifică relațiile pentru afișare.
- `LLM_PROVIDER` și cheile aferente sunt relevante doar dacă folosești fluxul AI din `POST /process/ai/text`.

---

## Comenzi utile

```powershell
# instalare dependențe
pip install -r requirements.txt

# pornire API
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# pornire GraphDB
docker-compose up graphdb -d

# verificare health
Invoke-RestMethod http://localhost:8000/health
```

---

## Notă despre dezvoltare

Documentația din acest fișier este aliniată cu structura curentă din workspace la data ultimei actualizări. Dacă adaugi noi routere, clienți sau variabile de configurare, actualizează și acest README.
