"""
rdf_writer.py — Construcție graf RDF și serializare Turtle din rezultatul extracției NLP.

Funcții principale:
    build_graph(extraction_result)           → rdflib.Graph cu triple entități + relații
    add_ontology_axioms(graph)               → adaugă declarații OWL (clase, subClass, domenii)
    serialize_ttl(graph, output_path)        → scrie fișierul .ttl
    merge_external_rdf(main_graph, ttl_path) → fuzionează date externe (OntoRefine)

Convenție URI:
    Instanțe: SH_INST:<uri_name>   ex: http://smarthome.org/instance#LivingRoom
    Clase:    SH:<ClassName>        ex: http://smarthome.org/ontology#Room
"""

import logging
import os

from rdflib import OWL, RDF, RDFS, Graph, Literal, URIRef
from rdflib.namespace import XSD

from app.models import ExtractionResult
from app.ontology import (
    CLASS_HIERARCHY,
    ENTITY_CLASS_MAP,
    ONTOLOGY_URI,
    PROPERTY_DOMAIN_RANGE,
    RELATION_PROPERTY_MAP,
    SH,
    SH_INST,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Construcție graf principal
# ---------------------------------------------------------------------------

def build_graph(extraction_result: ExtractionResult) -> Graph:
    """
    Construiește un graf RDF din rezultatul extracției NLP.

    Triple generate per entitate:
        <instance> rdf:type          <Class>
        <instance> rdfs:label        "label"@en

    Triple generate per relație:
        <subject_instance> <property> <object_instance>

    Args:
        extraction_result: Rezultatul complet al pipeline-ului NLP (entități + relații).

    Returns:
        rdflib.Graph populat, cu namespace-urile SH și SH_INST legate.
    """
    graph = Graph()
    graph.bind("sh", SH)
    graph.bind("shi", SH_INST)
    graph.bind("owl", OWL)
    graph.bind("rdf", RDF)
    graph.bind("rdfs", RDFS)

    # --- Entități ---
    entity_count = 0
    for entity in extraction_result.entities:
        class_uri = ENTITY_CLASS_MAP.get(entity.entity_type.value)
        if class_uri is None:
            logger.warning("Tip entitate necunoscut: %s — skip", entity.entity_type.value)
            continue

        instance_uri = SH_INST[entity.uri_name]
        graph.add((instance_uri, RDF.type, class_uri))
        graph.add((instance_uri, RDFS.label, Literal(entity.label, lang="en")))
        entity_count += 1

    logger.info("Triple entități adăugate: %d entități", entity_count)

    # --- Relații ---
    relation_count = 0
    for relation in extraction_result.relations:
        prop_uri = RELATION_PROPERTY_MAP.get(relation.predicate.value)
        if prop_uri is None:
            logger.warning("Tip relație necunoscut: %s — skip", relation.predicate.value)
            continue

        subject_uri = SH_INST[relation.subject]
        object_uri = SH_INST[relation.object]
        graph.add((subject_uri, prop_uri, object_uri))
        relation_count += 1

    logger.info("Triple relații adăugate: %d relații", relation_count)
    logger.info(
        "Graf construit: %d triple total",
        len(graph),
    )
    return graph


# ---------------------------------------------------------------------------
# Axiome OWL (schema ontologiei)
# ---------------------------------------------------------------------------

def add_ontology_axioms(graph: Graph) -> None:
    """
    Adaugă declarații OWL de bază la graful existent:
    - Declarație ontologie
    - Clase ca owl:Class
    - Ierarhie subClass
    - Domenii și range-uri pentru proprietăți
    - Proprietăți ca owl:ObjectProperty

    Apelabil înainte sau după build_graph — nu suprascrie triple existente.
    """
    # Declarație ontologie
    graph.add((ONTOLOGY_URI, RDF.type, OWL.Ontology))

    # Clase
    for class_uri in ENTITY_CLASS_MAP.values():
        graph.add((class_uri, RDF.type, OWL.Class))

    # Ierarhie subClass
    for sub, sup in CLASS_HIERARCHY:
        graph.add((sub, RDFS.subClassOf, sup))

    # Proprietăți obiect
    for prop_uri in RELATION_PROPERTY_MAP.values():
        graph.add((prop_uri, RDF.type, OWL.ObjectProperty))

    # Domenii și range-uri
    for prop_uri, domain_uri, range_uri in PROPERTY_DOMAIN_RANGE:
        graph.add((prop_uri, RDFS.domain, domain_uri))
        graph.add((prop_uri, RDFS.range, range_uri))

    logger.info("Axiome OWL adăugate la graf (%d triple total)", len(graph))


# ---------------------------------------------------------------------------
# Serializare Turtle
# ---------------------------------------------------------------------------

def serialize_ttl(graph: Graph, output_path: str) -> None:
    """
    Serializează graful RDF în format Turtle (.ttl) și îl salvează pe disc.

    Args:
        graph:       Graful RDF de serializat.
        output_path: Calea absolută sau relativă a fișierului de output.
    """
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    graph.serialize(destination=output_path, format="turtle")
    triple_count = len(graph)
    file_size = os.path.getsize(output_path)
    logger.info(
        "Turtle serializat: %s (%d triple, %d bytes)",
        output_path, triple_count, file_size,
    )


# ---------------------------------------------------------------------------
# Fuzionare date externe (OntoRefine)
# ---------------------------------------------------------------------------

def merge_external_rdf(main_graph: Graph, external_ttl_path: str) -> Graph:
    """
    Fuzionează un graf extern (ex: output OntoRefine) cu graful principal.

    Strategia de fuzionare:
    - Parcurge entitățile din graful extern care au rdfs:label.
    - Caută o instanță cu același label în graful principal.
    - Dacă există, copiază toate proprietățile date (sh:brand, sh:price, etc.)
      de la nodul extern la nodul din graful principal.
    - Dacă nu există match, adaugă nodul extern ca atare.

    Args:
        main_graph:        Graful principal construit din NLP.
        external_ttl_path: Calea fișierului .ttl extern.

    Returns:
        Graful principal îmbogățit cu datele externe.
    """
    external_graph = Graph()
    external_graph.parse(external_ttl_path, format="turtle")
    logger.info(
        "Graf extern încărcat: %s (%d triple)",
        external_ttl_path, len(external_graph),
    )

    # Construiește index label_lower → URIRef pentru instanțele din graful principal
    main_label_index: dict[str, URIRef] = {}
    for subj, pred, obj in main_graph.triples((None, RDFS.label, None)):
        if isinstance(subj, URIRef):
            main_label_index[str(obj).lower()] = subj

    merged = 0
    appended = 0

    for ext_subj in set(external_graph.subjects()):
        if not isinstance(ext_subj, URIRef):
            continue

        # Caută label-ul nodului extern
        ext_labels = list(external_graph.objects(ext_subj, RDFS.label))
        main_uri: URIRef | None = None

        for ext_label in ext_labels:
            main_uri = main_label_index.get(str(ext_label).lower())
            if main_uri:
                break

        if main_uri:
            # Copiază proprietățile date de la nodul extern la cel din main
            for pred, obj in external_graph.predicate_objects(ext_subj):
                if pred not in (RDF.type, RDFS.label):
                    main_graph.add((main_uri, pred, obj))
            merged += 1
            logger.info("  Merge: %s ← %s", main_uri, ext_subj)
        else:
            # Copiază nodul extern integral
            for pred, obj in external_graph.predicate_objects(ext_subj):
                main_graph.add((ext_subj, pred, obj))
            appended += 1

    logger.info(
        "Fuzionare completă: %d noduri merge, %d noduri noi, %d triple total",
        merged, appended, len(main_graph),
    )
    return main_graph
