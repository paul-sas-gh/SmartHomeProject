"""
routers/graph.py — Endpoint-uri pentru graful RDF curent.

Endpoints:
    GET  /graph/turtle  — Returnează graful curent serializat Turtle
    POST /graph/upload  — Uploadează graful curent în GraphDB
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from app.config import settings
from app.graphdb_client import create_repository, upload_ttl
from app.pipeline import get_state

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/graph", tags=["Graph"])


# ---------------------------------------------------------------------------
# GET /graph/turtle
# ---------------------------------------------------------------------------

@router.get(
    "/turtle",
    response_class=PlainTextResponse,
    summary="Returnează graful curent ca Turtle",
    responses={200: {"content": {"text/turtle": {}}}},
)
def get_turtle() -> str:
    """
    Returnează conținutul Turtle al grafului generat de ultimul run al pipeline-ului.
    """
    state = get_state()
    if not state.ttl_content:
        raise HTTPException(
            status_code=404,
            detail="Niciun graf disponibil. Rulează mai întâi POST /process sau POST /process/text.",
        )
    return PlainTextResponse(content=state.ttl_content, media_type="text/turtle")


# ---------------------------------------------------------------------------
# POST /graph/upload
# ---------------------------------------------------------------------------

class UploadResponse(BaseModel):
    repository: str
    triple_count: int
    message: str


@router.post("/upload", response_model=UploadResponse, summary="Uploadează graful în GraphDB")
def upload_graph() -> UploadResponse:
    """
    Uploadează graful curent (din ultimul run al pipeline-ului) în GraphDB.
    """
    state = get_state()
    if not state.ttl_content:
        raise HTTPException(
            status_code=404,
            detail="Niciun graf disponibil. Rulează mai întâi POST /process sau POST /process/text.",
        )

    repo = settings.graphdb_repository
    try:
        create_repository(repo)
        triple_count = upload_ttl(repo, state.ttl_content)
    except Exception as exc:
        logger.exception("Upload GraphDB eșuat: %s", exc)
        raise HTTPException(status_code=502, detail=f"Upload GraphDB eșuat: {exc}")

    return UploadResponse(
        repository=repo,
        triple_count=triple_count,
        message=f"Graf uploadat cu succes în repository '{repo}'.",
    )
