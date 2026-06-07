"""
routers/sparql.py — Endpoint-uri pentru interogări SPARQL pe GraphDB.

Endpoints:
    POST /sparql                          — Execută un query SPARQL custom
    GET  /sparql/predefined/{query_id}    — Execută una din interogările predefinite (1-6)
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Path
from pydantic import BaseModel

from app.config import settings
from app.graphdb_client import PREDEFINED_QUERIES, run_predefined_query, run_sparql_query

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sparql", tags=["SPARQL"])


# ---------------------------------------------------------------------------
# POST /sparql  — query custom
# ---------------------------------------------------------------------------

class SparqlRequest(BaseModel):
    query: str
    repository: str | None = None  # dacă None, folosește settings.graphdb_repository


class SparqlResponse(BaseModel):
    repository: str
    query: str
    result_count: int
    results: list[dict]


@router.post("", response_model=SparqlResponse, summary="Execută query SPARQL custom")
def run_custom_sparql(body: SparqlRequest) -> SparqlResponse:
    """
    Execută un query SPARQL SELECT arbitrar pe GraphDB și returnează rezultatele
    în format JSON (structura W3C: bindings list).
    """
    if not body.query.strip():
        raise HTTPException(status_code=422, detail="Query-ul SPARQL este gol.")

    repo = body.repository or settings.graphdb_repository

    try:
        raw = run_sparql_query(repo, body.query)
    except Exception as exc:
        logger.exception("Eroare SPARQL custom pe '%s': %s", repo, exc)
        raise HTTPException(status_code=502, detail=f"Eroare GraphDB: {exc}")

    bindings = raw.get("results", {}).get("bindings", [])
    # Simplifică valorile: {'var': {'type': 'uri', 'value': '...'}} → {'var': '...'}
    simplified = [{k: v["value"] for k, v in row.items()} for row in bindings]

    return SparqlResponse(
        repository=repo,
        query=body.query,
        result_count=len(simplified),
        results=simplified,
    )


# ---------------------------------------------------------------------------
# GET /sparql/predefined/{query_id}
# ---------------------------------------------------------------------------

class PredefinedQueryResponse(BaseModel):
    query_id: int
    query_name: str
    description: str
    result_count: int
    results: list[dict]


@router.get(
    "/predefined/{query_id}",
    response_model=PredefinedQueryResponse,
    summary="Execută interogare predefinită",
)
def run_predefined(
    query_id: int = Path(..., ge=1, le=6, description="ID-ul interogării predefinite (1–6)"),
) -> PredefinedQueryResponse:
    """
    Execută una din cele 6 interogări SPARQL predefinite.

    - **1** — Actuatoare în LivingRoom
    - **2** — Actuatoare cu brand și preț (date externe OntoRefine)
    - **3** — Pași din rutină și secvența lor (hasNext)
    - **4** — Acțiuni și actuatoarele folosite
    - **5** — Camere unde au loc acțiuni
    - **6** — Integrare completă: acțiune + actuator + cameră + preț
    """
    if query_id not in PREDEFINED_QUERIES:
        raise HTTPException(
            status_code=404,
            detail=f"Query predefinit #{query_id} nu există. ID-uri valide: {sorted(PREDEFINED_QUERIES)}",
        )

    repo = settings.graphdb_repository
    try:
        result = run_predefined_query(repo, query_id)
    except Exception as exc:
        logger.exception("Eroare query predefinit #%d pe '%s': %s", query_id, repo, exc)
        raise HTTPException(status_code=502, detail=f"Eroare GraphDB: {exc}")

    # Simplifică valorile
    simplified = [
        {k: v["value"] for k, v in row.items()}
        for row in result.get("results", [])
    ]

    meta = PREDEFINED_QUERIES[query_id]
    return PredefinedQueryResponse(
        query_id=query_id,
        query_name=meta["name"],
        description=meta["description"],
        result_count=result.get("result_count", len(simplified)),
        results=simplified,
    )
