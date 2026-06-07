"""
routers/entities.py — Endpoint-uri pentru lista entităților și relațiilor extrase.

Endpoints:
    GET /entities   — Returnează entitățile din ultimul run al pipeline-ului
    GET /relations  — Returnează relațiile din ultimul run al pipeline-ului
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.pipeline import get_state

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Extraction"])


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------

class EntityOut(BaseModel):
    label: str
    uri_name: str
    entity_type: str
    confidence: float
    source_text: str


class RelationOut(BaseModel):
    subject: str
    predicate: str
    object: str
    confidence: float
    source_text: str


class EntitiesResponse(BaseModel):
    source: str
    total: int
    entities: list[EntityOut]


class RelationsResponse(BaseModel):
    source: str
    total: int
    relations: list[RelationOut]


# ---------------------------------------------------------------------------
# GET /entities
# ---------------------------------------------------------------------------

@router.get("/entities", response_model=EntitiesResponse, summary="Entitățile extrase")
def get_entities() -> EntitiesResponse:
    """
    Returnează toate entitățile extrase în ultimul run al pipeline-ului.
    Disponibile după cel puțin un apel la POST /process sau POST /process/text.
    """
    state = get_state()
    if state.result is None:
        raise HTTPException(
            status_code=404,
            detail="Nicio extracție disponibilă. Rulează mai întâi POST /process sau POST /process/text.",
        )

    extraction = state.result.extraction
    entities = [
        EntityOut(
            label=e.label,
            uri_name=e.uri_name,
            entity_type=e.entity_type.value,
            confidence=e.confidence,
            source_text=e.source_text,
        )
        for e in extraction.entities
    ]

    return EntitiesResponse(
        source=extraction.source_file,
        total=len(entities),
        entities=entities,
    )


# ---------------------------------------------------------------------------
# GET /relations
# ---------------------------------------------------------------------------

@router.get("/relations", response_model=RelationsResponse, summary="Relațiile extrase")
def get_relations() -> RelationsResponse:
    """
    Returnează toate relațiile extrase în ultimul run al pipeline-ului.
    Disponibile după cel puțin un apel la POST /process sau POST /process/text.
    """
    state = get_state()
    if state.result is None:
        raise HTTPException(
            status_code=404,
            detail="Nicio extracție disponibilă. Rulează mai întâi POST /process sau POST /process/text.",
        )

    extraction = state.result.extraction
    relations = [
        RelationOut(
            subject=r.subject,
            predicate=r.predicate.value,
            object=r.object,
            confidence=r.confidence,
            source_text=r.source_text,
        )
        for r in extraction.relations
    ]

    return RelationsResponse(
        source=extraction.source_file,
        total=len(relations),
        relations=relations,
    )
