# Plan: Rulare Locală Gemma 4 cu Docker + Web UI Chat

## Configurație detectată — acest laptop

| Componentă | Specificație | Evaluare |
|------------|-------------|----------|
| **CPU**    | Intel Core i7-8550U @ 1.80GHz (4 core / 8 thread) | ⚠️ CPU laptop gen 8 (2017), inferență lentă |
| **RAM**    | 24 GB       | ✅ Suficient pentru modele până la 12B |
| **GPU**    | Intel UHD Graphics 620 — 1 GB VRAM (integrat) | ❌ Fără GPU dedicat, fără CUDA/ROCm |
| **Disk C** | 71.7 GB liberi / 476 GB total | ✅ Spațiu suficient |

### ⭐ Model recomandat: `gemma4:4b`

> **Motivare:** Fără GPU dedicat, inferența rulează exclusiv pe CPU. `gemma4:4b` necesită ~5–8 GB RAM (din cei 24 GB disponibili), lasă suficient spațiu pentru OS + Docker, și oferă o viteză acceptabilă de **~5–12 tok/s** pe acest CPU. Modelele mai mari (12B, 27B) ar fi extrem de lente (~1–3 tok/s) sau imposibil de rulat (27B depășește RAM-ul disponibil).

| Model | RAM necesar | Viteză estimată (CPU i7-8550U) | Verdict |
|-------|------------|-------------------------------|---------|
| `gemma4:1b` | ~3 GB | ~25–40 tok/s | ✅ Rapid, calitate de bază |
| **`gemma4:4b`** | **~6 GB** | **~8–15 tok/s** | **⭐ RECOMANDAT** |
| `gemma4:4b-q4` | ~3.5 GB | ~12–18 tok/s | ✅ Mai rapid, calitate ușor redusă |
| `gemma4:12b` | ~14 GB | ~2–4 tok/s | ⚠️ Posibil, dar lent |
| `gemma4:27b` | ~32 GB | N/A | ❌ Depășește RAM disponibil |

> **Sfat:** Dacă vrei viteza maximă pe acest hardware, folosește `gemma4:4b-q4` (varianta cuantizată Q4 — ~30% mai rapidă cu pierdere minimă de calitate).

**Setare în `.env`:**
```env
OLLAMA_MODEL=gemma4:4b
# alternativă mai rapidă:
# OLLAMA_MODEL=gemma4:4b-q4
```

---

## Cuprins

1. [Prezentare generală](#1-prezentare-generală)
2. [Cerințe hardware](#2-cerințe-hardware)
3. [Dependințe software](#3-dependințe-software)
4. [Arhitectura serviciilor](#4-arhitectura-serviciilor)
5. [Structura fișierelor](#5-structura-fișierelor)
6. [Configurare pas cu pas](#6-configurare-pas-cu-pas)
7. [Docker Compose complet](#7-docker-compose-complet)
8. [Configurare avansată](#8-configurare-avansată)
9. [Integrare cu serviciile existente](#9-integrare-cu-serviciile-existente)
10. [Troubleshooting](#10-troubleshooting)

---

## 1. Prezentare generală

Acest plan descrie rularea modelului **Google Gemma 4** local, folosind:

| Componentă     | Rol                                     | Imagine Docker              |
|----------------|-----------------------------------------|-----------------------------|
| **Ollama**     | Server de inferență pentru Gemma 4      | `ollama/ollama:latest`      |
| **Open WebUI** | Interfață web chat (compatibil ChatGPT) | `ghcr.io/open-webui/open-webui:main` |
| **Nginx**      | Reverse proxy (opțional)                | `nginx:alpine`              |

Stack-ul este complet offline — modelul rulează exclusiv local, fără dependință de API-uri externe.

---

## 2. Cerințe hardware

### Minimum (CPU only)

| Resursă | Gemma 4 1B | Gemma 4 4B  | Gemma 4 12B  |
|---------|-----------|-------------|--------------|
| RAM     | 4 GB      | 8 GB        | 16 GB        |
| Spațiu  | 2 GB      | 5 GB        | 14 GB        |
| CPU     | 4 cores   | 4 cores     | 8 cores      |

### Recomandat (cu GPU)

| Resursă  | Gemma 4 4B  | Gemma 4 12B  | Gemma 4 27B  |
|----------|-------------|--------------|--------------|
| VRAM GPU | 6 GB        | 12 GB        | 24 GB        |
| RAM      | 16 GB       | 32 GB        | 32 GB        |
| GPU      | NVIDIA ≥ RTX 3060 | RTX 3090 / 4080 | RTX 4090 / A100 |

> **Notă:** Pe CPU, viteza de generare este ~3–8 tok/s. Pe GPU (CUDA), ~30–80 tok/s.

---

## 3. Dependințe software

### 3.1 Sistem de operare

- Windows 10/11 (cu WSL 2 activat), Linux, sau macOS (Apple Silicon)
- WSL 2 cu Ubuntu 22.04+ (recomandat pe Windows)

### 3.2 Docker & containere

| Pachet                          | Versiune minimă | Scop                                  |
|---------------------------------|-----------------|---------------------------------------|
| Docker Engine                   | 24.x            | Runtime containere                    |
| Docker Compose                  | v2.20+          | Orchestrare multi-container           |
| NVIDIA Container Toolkit        | 1.14+           | Suport GPU în Docker (dacă ai NVIDIA) |

### 3.3 Drivere GPU (opțional, pentru accelerare)

- **NVIDIA**: Driver ≥ 525, CUDA ≥ 11.8, `nvidia-docker2`
- **AMD**: ROCm ≥ 5.7 (suport experimental în Ollama)
- **Apple Silicon**: Suport nativ prin Metal (fără configurare suplimentară)

### 3.4 Pachete pentru instalare NVIDIA Container Toolkit (Ubuntu/WSL)

```bash
# Adaugă repository NVIDIA
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list \
  | sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' \
  | sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

---

## 4. Arhitectura serviciilor

```
┌─────────────────────────────────────────────────────────┐
│                    docker-network-llm                    │
│                                                         │
│  ┌──────────────┐        ┌───────────────────────────┐  │
│  │    Ollama    │◄───────│       Open WebUI          │  │
│  │  :11434      │  API   │       :3000               │  │
│  │              │        │  (Chat Interface)         │  │
│  │  Gemma 4     │        └───────────────────────────┘  │
│  │  (model)     │                    ▲                  │
│  └──────────────┘                    │ HTTP             │
│         │                     ┌──────┴──────┐           │
│         │ volume              │    Nginx    │           │
│         ▼                     │  :80 / :443 │           │
│  ollama_models                └─────────────┘           │
│  (~/ollama_data)                    ▲                   │
└─────────────────────────────────────────────────────────┘
                                      │
                              Browser utilizator
                              http://localhost
```

---

## 5. Structura fișierelor

```
svc-llm/
├── docker-compose.yml          # Orchestrare principală
├── .env                        # Variabile de mediu (secret)
├── nginx/
│   └── nginx.conf              # Configurare reverse proxy
├── ollama/
│   └── entrypoint.sh           # Script pull model la start
├── docs/
│   └── plan/
│       └── gemma4-local-docker.md  # (acest fișier)
└── README.md
```

---

## 6. Configurare pas cu pas

### Pasul 1 — Clonează / crează directorul `svc-llm`

```bash
mkdir -p svc-llm/nginx svc-llm/ollama
cd svc-llm
```

### Pasul 2 — Creează fișierul `.env`

```env
# .env
OLLAMA_MODEL=gemma4:4b           # sau gemma4:1b / gemma4:12b / gemma4:27b
OPEN_WEBUI_PORT=3000
OLLAMA_PORT=11434
WEBUI_SECRET_KEY=change-me-in-production
```

### Pasul 3 — Script auto-pull model (`ollama/entrypoint.sh`)

```bash
#!/bin/bash
# Pornește serverul Ollama în background
ollama serve &
OLLAMA_PID=$!

# Așteaptă să fie disponibil
echo "Aștept Ollama să pornească..."
until curl -s http://localhost:11434/api/tags > /dev/null 2>&1; do
  sleep 1
done

# Descarcă modelul dacă nu există deja
echo "Verific / descarc modelul ${OLLAMA_MODEL}..."
ollama pull "${OLLAMA_MODEL:-gemma4:4b}"

echo "Model pregătit. Ollama rulează."
wait $OLLAMA_PID
```

```bash
chmod +x svc-llm/ollama/entrypoint.sh
```

### Pasul 4 — Configurare Nginx (`nginx/nginx.conf`)

```nginx
events {
    worker_connections 1024;
}

http {
    upstream openwebui {
        server open-webui:3000;
    }

    server {
        listen 80;
        server_name localhost;

        client_max_body_size 50M;

        location / {
            proxy_pass http://openwebui;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_read_timeout 300s;
        }
    }
}
```

### Pasul 5 — Pornire

```bash
# Prima rulare (descarcă imaginile și modelul — poate dura 5-30 min)
docker compose up -d

# Urmărește progresul descărcării modelului
docker logs -f llm-ollama

# Verifică că totul rulează
docker compose ps
```

### Pasul 6 — Accesare Web UI

Deschide browserul la: **http://localhost** (sau **http://localhost:3000** fără Nginx)

La primul acces, creează un cont de administrator local (offline, nu necesită internet).

---

## 7. Docker Compose complet

```yaml
# svc-llm/docker-compose.yml
version: '3.8'

services:

  # ─── Ollama — Server de inferență ───────────────────────────
  ollama:
    image: ollama/ollama:latest
    container_name: llm-ollama
    restart: unless-stopped
    ports:
      - "${OLLAMA_PORT:-11434}:11434"
    volumes:
      - ollama_models:/root/.ollama
      - ./ollama/entrypoint.sh:/entrypoint.sh
    entrypoint: ["/bin/bash", "/entrypoint.sh"]
    environment:
      - OLLAMA_MODEL=${OLLAMA_MODEL:-gemma4:4b}
      - OLLAMA_NUM_PARALLEL=2          # Cereri paralele
      - OLLAMA_MAX_LOADED_MODELS=1     # Modele simultan în RAM
      - OLLAMA_KEEP_ALIVE=5m           # Timp model în memorie după cerere
    networks:
      - llm-network
    # ── Activează pentru GPU NVIDIA ──
    # deploy:
    #   resources:
    #     reservations:
    #       devices:
    #         - driver: nvidia
    #           count: 1
    #           capabilities: [gpu]

  # ─── Open WebUI — Interfață chat ────────────────────────────
  open-webui:
    image: ghcr.io/open-webui/open-webui:main
    container_name: llm-open-webui
    restart: unless-stopped
    ports:
      - "${OPEN_WEBUI_PORT:-3000}:8080"
    volumes:
      - open_webui_data:/app/backend/data
    environment:
      - OLLAMA_BASE_URL=http://ollama:11434
      - WEBUI_SECRET_KEY=${WEBUI_SECRET_KEY:-change-me}
      - ENABLE_SIGNUP=true              # Dezactivează după primul cont
      - DEFAULT_MODELS=${OLLAMA_MODEL:-gemma4:4b}
      - WEBUI_NAME=Gemma 4 Local Chat
    depends_on:
      - ollama
    networks:
      - llm-network

  # ─── Nginx — Reverse Proxy (opțional) ───────────────────────
  nginx:
    image: nginx:alpine
    container_name: llm-nginx
    restart: unless-stopped
    ports:
      - "80:80"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - open-webui
    networks:
      - llm-network

# ─── Volume-uri persistente ────────────────────────────────────
volumes:
  ollama_models:
    name: llm-ollama-models        # Modelele descărcate (~5-30 GB)
  open_webui_data:
    name: llm-open-webui-data      # Conversații, utilizatori, setări

# ─── Rețea internă ─────────────────────────────────────────────
networks:
  llm-network:
    name: llm-network
    driver: bridge
```

---

## 8. Configurare avansată

### 8.1 Activare GPU NVIDIA

Decomentează secțiunea `deploy` din serviciul `ollama`:

```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: 1
          capabilities: [gpu]
```

Verificare GPU în container:

```bash
docker exec llm-ollama nvidia-smi
docker exec llm-ollama ollama run gemma4:4b "Salut!"
```

### 8.2 Selectarea variantei de model

Modifică `.env` sau variabila de mediu `OLLAMA_MODEL`:

| Tag model         | Dimensiune | VRAM necesar | Viteză (GPU) |
|-------------------|-----------|--------------|--------------|
| `gemma4:1b`       | ~800 MB   | 2 GB         | ~80 tok/s    |
| `gemma4:4b`       | ~3.3 GB   | 6 GB         | ~50 tok/s    |
| `gemma4:12b`      | ~8 GB     | 12 GB        | ~30 tok/s    |
| `gemma4:27b`      | ~17 GB    | 24 GB        | ~15 tok/s    |
| `gemma4:27b-q4`   | ~9 GB     | 12 GB        | ~20 tok/s    |

> Variantele cuantizate (`-q4`, `-q8`) oferă un raport mai bun performanță/dimensiune.

### 8.3 Parametri de generare (per-cerere în Open WebUI)

Setări recomandate pentru Gemma 4 în interfața Open WebUI:

```json
{
  "temperature": 0.7,
  "top_p": 0.9,
  "top_k": 40,
  "num_ctx": 8192,
  "repeat_penalty": 1.1,
  "num_predict": 2048
}
```

### 8.4 System prompt implicit (Open WebUI → Model → Edit)

```
Ești un asistent AI util, precis și concis. Răspunzi în limba în care 
ți se adresează utilizatorul. Nu inventa fapte; dacă nu știi ceva, 
spune că nu știi.
```

### 8.5 Comenzi Ollama utile

```bash
# Listează modele disponibile local
docker exec llm-ollama ollama list

# Descarcă un alt model
docker exec llm-ollama ollama pull gemma4:12b

# Test rapid în terminal
docker exec -it llm-ollama ollama run gemma4:4b

# Șterge un model
docker exec llm-ollama ollama rm gemma4:1b

# Monitorizare utilizare resurse
docker stats llm-ollama llm-open-webui
```

---

## 9. Integrare cu serviciile existente

Serviciul `svc-llm` poate fi adăugat la `docker-compose.yml` principal al proiectului, conectând rețeaua `llm-network` la `docker-network`:

```yaml
# Adaugă în docker-compose.yml principal
services:
  svc-ai:
    # ... configurare existentă ...
    environment:
      - LLM_BASE_URL=http://llm-ollama:11434   # Accesează Gemma 4 local
    networks:
      - docker-network
      - llm-network                             # Adaugă rețeaua LLM

networks:
  llm-network:
    external: true                              # Rețea din svc-llm
```

### Exemplu apel API din `svc-ai` (Python)

```python
import httpx

async def generate_with_gemma(prompt: str) -> str:
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            "http://llm-ollama:11434/api/generate",
            json={
                "model": "gemma4:4b",
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "num_ctx": 4096
                }
            }
        )
        return response.json()["response"]
```

---

## 10. Troubleshooting

| Problemă | Cauză probabilă | Soluție |
|----------|-----------------|---------|
| `ollama` nu pornește | Port 11434 ocupat | `docker compose down ; docker compose up -d` |
| Model nu se descarcă | Lipsă spațiu pe disc | `docker system df` → eliberează spațiu |
| GPU nu este detectat | NVIDIA toolkit lipsă | Reinstalează `nvidia-container-toolkit` |
| WebUI nu se conectează la Ollama | Rețea Docker izolată | Verifică `OLLAMA_BASE_URL=http://ollama:11434` |
| Răspunsuri lente (CPU) | Model prea mare | Folosește `gemma4:1b` sau `gemma4:4b-q4` |
| `OOM` (out of memory) | RAM insuficient | Micșorează `num_ctx` sau schimbă varianta modelului |
| Context window depășit | `num_ctx` prea mic | Mărește la 8192 sau 16384 |

### Verificare health servicii

```bash
# Status containere
docker compose ps

# Log-uri Ollama
docker logs llm-ollama --tail 50

# Log-uri WebUI
docker logs llm-open-webui --tail 50

# Test API direct
curl http://localhost:11434/api/tags

# Test generare
curl http://localhost:11434/api/generate \
  -d '{"model":"gemma4:4b","prompt":"Salut!","stream":false}'
```

---

## Referințe

- [Ollama Docker Hub](https://hub.docker.com/r/ollama/ollama)
- [Open WebUI GitHub](https://github.com/open-webui/open-webui)
- [Gemma 4 pe Ollama](https://ollama.com/library/gemma4)
- [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)
