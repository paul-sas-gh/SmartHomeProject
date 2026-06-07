"""
pipeline.py — Orchestrare completă NLP → RDF → GraphDB.

Funcția principală: run_pipeline(text, ...) -> PipelineResult

State in-memory: ultimul rezultat al pipeline-ului este păstrat în _state
pentru a putea fi accesat de endpoint-urile /entities, /relations, /graph.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass

from app.config import settings
from app.extractors.entity_extractor import get_extractor
from app.extractors.relation_extractor import get_relation_extractor
from app.graphdb_client import create_repository, upload_ttl
from app.models import ExtractionResult, PipelineResult
from app.parsers.text_loader import load_text_from_string, load_text
from app.rdf_writer import build_graph, merge_external_rdf, serialize_ttl

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# spaCy — inițializare lazily o singură dată
# ---------------------------------------------------------------------------
# State in-memory (ultimul run al pipeline-ului)
# ---------------------------------------------------------------------------
@dataclass
class PipelineState:
    result: PipelineResult | None = None
    ttl_content: str = ""
    """Conținutul Turtle serializat al grafului îmbogățit (NLP + OntoRefine)."""


_state = PipelineState()


def get_state() -> PipelineState:
    """Returnează starea curentă a pipeline-ului (ultimul run)."""
    return _state


# ---------------------------------------------------------------------------
# Pipeline principal
# ---------------------------------------------------------------------------

def run_pipeline(
    text: str,
    source_name: str = "inline",
    upload_to_graphdb: bool = True,
) -> PipelineResult:
    """
    Rulează pipeline-ul complet pe un text dat.

    Args:
        text:              Text în limbaj natural (descriere Smart Home).
        source_name:       Identificator sursă (numele fișierului sau 'inline').
        upload_to_graphdb: Dacă True, uploadează graful în GraphDB după generare.

    Returns:
        PipelineResult cu entități, relații, număr triple și status upload.
    """
    logger.info("--- Pipeline start | sursa: '%s' ---", source_name)

    # 1. Curățare text
    clean = load_text_from_string(text)
    logger.info("Text normalizat: %d caractere.", len(clean))

    # 2. Extracție entități
    entities = get_extractor().extract(clean)
    logger.info("Entități detectate: %d", len(entities))

    # 3. Extracție relații
    relations = get_relation_extractor().extract(clean, entities)
    logger.info("Relații detectate: %d", len(relations))

    extraction = ExtractionResult(
        source_file=source_name,
        raw_text=clean,
        entities=entities,
        relations=relations,
    )

    # 5. Generare graf RDF
    rdf_graph = build_graph(extraction)

    # 6. Merge date externe OntoRefine (dacă există)
    external_ttl = os.path.join(settings.data_external_dir, "devices_ontorefine.ttl")
    if os.path.isfile(external_ttl):
        rdf_graph = merge_external_rdf(rdf_graph, external_ttl)
        logger.info("Date externe OntoRefine merged.")

    # 7. Serializare Turtle (fișier persistent + in-memory)
    output_path = os.path.join(settings.data_output_dir, f"{_safe_name(source_name)}.ttl")
    os.makedirs(settings.data_output_dir, exist_ok=True)
    serialize_ttl(rdf_graph, output_path)

    ttl_content = rdf_graph.serialize(format="turtle")
    triple_count = len(rdf_graph)
    logger.info("Triple RDF generate: %d — fișier: %s", triple_count, output_path)

    # 8. Upload GraphDB
    uploaded = False
    if upload_to_graphdb:
        try:
            create_repository(settings.graphdb_repository)
            upload_ttl(settings.graphdb_repository, ttl_content)
            uploaded = True
            logger.info("Upload GraphDB reușit.")
        except Exception as exc:
            logger.error("Upload GraphDB eșuat: %s", exc)

    # 9. Actualizare state + return
    result = PipelineResult(
        extraction=extraction,
        ttl_path=output_path,
        triple_count=triple_count,
        graphdb_uploaded=uploaded,
        llm_used=False,
    )
    _state.result = result
    _state.ttl_content = ttl_content

    logger.info("--- Pipeline end | triple=%d | uploaded=%s ---", triple_count, uploaded)
    return result


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe_name(name: str) -> str:
    """Convertește un string arbitrar într-un nume de fișier safe."""
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in name).strip("_") or "output"
