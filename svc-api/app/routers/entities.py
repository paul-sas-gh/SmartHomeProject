"""
routers/entities.py — Endpoint-uri pentru lista entităților și relațiilor extrase.

Endpoints:
    GET /entities   — Returnează entitățile din ultimul run al pipeline-ului
    GET /relations  — Returnează relațiile din ultimul run al pipeline-ului
"""

from __future__ import annotations

import logging

from fastapi import APIRouter
from pydantic import BaseModel

from app.graphdb_client import get_all_entities, get_all_relations
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Extraction"])


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------

class EntityOut(BaseModel):
    label: str
    uri: str
    type: str


class RelationOut(BaseModel):
    subject: str
    predicate: str
    object: str


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

@router.get("/entities", response_model=EntitiesResponse, summary="Entitățile din GraphDB")
def get_entities() -> EntitiesResponse:
    """
    Returnează toate entitățile principale (Camere, Dispozitive) stocate în GraphDB.
    """
    repo = settings.graphdb_repository
    bindings = get_all_entities(repo)

    entities = [
        EntityOut(
            label=b["label"]["value"],
            uri=b["uri"]["value"],
            type=b["type"]["value"].split("#")[-1],
        )
        for b in bindings
    ]

    return EntitiesResponse(
        source=f"GraphDB Repository: {repo}",
        total=len(entities),
        entities=entities,
    )


# ---------------------------------------------------------------------------
# GET /relations
# ---------------------------------------------------------------------------

@router.get("/relations", response_model=RelationsResponse, summary="Relațiile din GraphDB")
def get_relations() -> RelationsResponse:
    """
    Returnează toate relațiile (Communicates With, Contains) stocate în GraphDB.
    """
    repo = settings.graphdb_repository
    bindings = get_all_relations(repo)

    relations = []
    for b in bindings:
        subject = b["s_label"]["value"]
        obj = b["o_label"]["value"]
        
        # Predicatul poate veni din label sau din URI
        if "p_label" in b:
            predicate = b["p_label"]["value"]
        else:
            uri_p = b["p"]["value"]
            if "#" in uri_p:
                predicate = uri_p.split("#")[-1]
            else:
                predicate = uri_p.split("/")[-1]

        # Decodare URL (ex: %20 -> spațiu)
        from urllib.parse import unquote
        predicate = unquote(predicate)

        relations.append(
            RelationOut(
                subject=subject,
                predicate=predicate,
                object=obj,
            )
        )

    return RelationsResponse(
        source=f"GraphDB Repository: {repo}",
        total=len(relations),
        relations=relations,
    )
