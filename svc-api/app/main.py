"""
main.py — Entry point FastAPI pentru svc-api.

Pornire:
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import entities, graph, process, sparql

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(
    title="SmartHome NLP API",
    description="Pipeline NLP → RDF → GraphDB pentru descrieri Smart Home",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# --- CORS (frontend React: localhost:3000 / localhost:5173) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(process.router)
app.include_router(graph.router)
app.include_router(sparql.router)
app.include_router(entities.router)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@app.get("/health", tags=["Infra"])
def health_check() -> dict:
    """Verifică că serviciul este activ."""
    logger.info("Health check requested")
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Startup event
# ---------------------------------------------------------------------------
@app.on_event("startup")
async def on_startup() -> None:
    logger.info("svc-api started — GraphDB: %s | LLM enabled: %s", settings.graphdb_url, settings.llm_enabled)
