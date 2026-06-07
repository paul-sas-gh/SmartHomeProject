"""
routers/process.py — Endpoint-uri pentru procesarea textului prin pipeline NLP.

Endpoints:
    POST /process       — Upload fișier .txt → rulare pipeline → JSON result
    POST /process/text  — Text string direct → rulare pipeline → JSON result
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from pydantic import BaseModel

from app.pipeline import run_pipeline

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/process", tags=["Process"])


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------

class EntityOut(BaseModel):
    label: str
    uri_name: str
    entity_type: str
    confidence: float


class RelationOut(BaseModel):
    subject: str
    predicate: str
    object: str
    confidence: float


class ProcessResponse(BaseModel):
    source: str
    entity_count: int
    relation_count: int
    triple_count: int
    graphdb_uploaded: bool
    entities: list[EntityOut]
    relations: list[RelationOut]
    ttl_path: str


# ---------------------------------------------------------------------------
# POST /process  — fișier .txt
# ---------------------------------------------------------------------------

@router.post("", response_model=ProcessResponse, summary="Procesează fișier .txt")
async def process_file(
    file: UploadFile = File(..., description="Fișier text (.txt) cu descriere Smart Home"),
    upload: bool = Query(default=True, description="Uploadează graful în GraphDB după procesare"),
) -> ProcessResponse:
    """
    Primește un fișier .txt, rulează pipeline-ul NLP complet și returnează
    entitățile, relațiile și numărul de triple RDF generate.
    """
    if not file.filename or not file.filename.endswith(".txt"):
        raise HTTPException(status_code=422, detail="Fișierul trebuie să fie de tip .txt")

    raw_bytes = await file.read()
    try:
        text = raw_bytes.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=422, detail="Fișierul nu este în format UTF-8.")

    if not text.strip():
        raise HTTPException(status_code=422, detail="Fișierul este gol.")

    source_name = file.filename.removesuffix(".txt")

    try:
        result = run_pipeline(text, source_name=source_name, upload_to_graphdb=upload)
    except Exception as exc:
        logger.exception("Eroare pipeline pentru fișier '%s': %s", file.filename, exc)
        raise HTTPException(status_code=500, detail=f"Eroare pipeline: {exc}")

    return _build_response(result, source=file.filename)


# ---------------------------------------------------------------------------
# POST /process/text  — text direct
# ---------------------------------------------------------------------------

class TextInput(BaseModel):
    text: str
    source_name: str = "inline"
    upload: bool = True


@router.post("/text", response_model=ProcessResponse, summary="Procesează text direct")
def process_text(body: TextInput) -> ProcessResponse:
    """
    Primește un text în limbaj natural direct în body, rulează pipeline-ul
    NLP complet și returnează entitățile, relațiile și triple count.
    """
    if not body.text.strip():
        raise HTTPException(status_code=422, detail="Câmpul 'text' este gol.")

    try:
        result = run_pipeline(
            body.text,
            source_name=body.source_name,
            upload_to_graphdb=body.upload,
        )
    except Exception as exc:
        logger.exception("Eroare pipeline pentru text inline: %s", exc)
        raise HTTPException(status_code=500, detail=f"Eroare pipeline: {exc}")

    return _build_response(result, source=body.source_name)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _build_response(result, source: str) -> ProcessResponse:
    entities = [
        EntityOut(
            label=e.label,
            uri_name=e.uri_name,
            entity_type=e.entity_type.value,
            confidence=e.confidence,
        )
        for e in result.extraction.entities
    ]
    relations = [
        RelationOut(
            subject=r.subject,
            predicate=r.predicate.value,
            object=r.object,
            confidence=r.confidence,
        )
        for r in result.extraction.relations
    ]
    return ProcessResponse(
        source=source,
        entity_count=len(entities),
        relation_count=len(relations),
        triple_count=result.triple_count,
        graphdb_uploaded=result.graphdb_uploaded,
        entities=entities,
        relations=relations,
        ttl_path=result.ttl_path,
    )
