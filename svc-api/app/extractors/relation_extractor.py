"""
relation_extractor.py — Extracție relații semantice între entitățile Smart Home.

Relații detectate (cu strategia de detecție):
    locatedIn        — "The [Room] contains [Device, ...]"
    requiresSensor   — "Step ... using [Sensor]" / trigger pe Sensor
    requiresActuator — "Step ... using/through [Actuator]"
    takesPlaceIn     — "Step ... in the [Room]"
    hasNext          — Ordinea apariției pașilor de rutină în text
    communicatesWith — Device co-localizat cu SmartHub în aceeași propoziție
                       + Action care utilizează explicit un SmartHub

Strategia generală:
    1. Propoziție cu "contains" → locatedIn + communicatesWith (device-hub în aceeași cameră)
    2. Propoziție cu Step + Device → requiresSensor / requiresActuator / communicatesWith
    3. Propoziție cu Step + Room → takesPlaceIn
    4. Ordinea primei apariții a pașilor în text → hasNext

Note:
    - Entitățile de tip Action sunt sintetizate (label ≠ text verbatim),
      deci sunt localizate în propoziții prin source_text (regex match text).
    - Deduplicare finală pe (subject, predicate, object).
"""

import logging
import re
from itertools import pairwise

from app.config import settings
from app.models import Entity, EntityType, Relation, RelationType
from app.extractors.rule_patterns import ACTION_REGEX_PATTERNS

logger = logging.getLogger(__name__)

# Singleton
_extractor_instance: "RelationExtractor | None" = None


def get_relation_extractor() -> "RelationExtractor":
    """Returnează instanța singleton a RelationExtractor (lazy init)."""
    global _extractor_instance
    if _extractor_instance is None:
        _extractor_instance = RelationExtractor()
    return _extractor_instance


# ---------------------------------------------------------------------------
# Tipuri utilitare
# ---------------------------------------------------------------------------

_DEVICE_TYPES: frozenset[EntityType] = frozenset({
    EntityType.SENSOR, EntityType.ACTUATOR,
    EntityType.SMART_HUB, EntityType.DEVICE,
})

_STEP_TYPES: frozenset[EntityType] = frozenset({
    EntityType.START_EVENT, EntityType.VERIFICATION,
    EntityType.ACTION, EntityType.END_EVENT,
    EntityType.ROUTINE_STEP,
})


# ---------------------------------------------------------------------------
# RelationExtractor
# ---------------------------------------------------------------------------

class RelationExtractor:
    """
    Extrage relații semantice între entitățile Smart Home dintr-un text.

    Primește entitățile deja detectate de EntityExtractor și returnează
    o listă de Relation deduplicate.
    """

    def __init__(self) -> None:
        import spacy
        self._nlp = spacy.load(settings.spacy_model)
        logger.info(
            "RelationExtractor inițializat cu modelul '%s'",
            settings.spacy_model,
        )

    # ------------------------------------------------------------------
    # Interfața publică
    # ------------------------------------------------------------------

    def extract(self, text: str, entities: list[Entity]) -> list[Relation]:
        """
        Extrage relații semantice din text folosind entitățile deja detectate.

        Args:
            text:     Textul curat (output din text_loader.load_text).
            entities: Entitățile detectate de EntityExtractor.

        Returns:
            Listă de relații unice, deduplicate pe (subject, predicate, object).
        """
        logger.info("--- Extracție relații START ---")

        doc = self._nlp(text)
        sentences = [str(sent).strip() for sent in doc.sents if str(sent).strip()]

        # Construiește index și mapare acțiuni → propoziție
        label_index = self._build_label_index(entities)
        action_sentence_map = self._map_actions_to_sentences(sentences, entities)

        raw: list[Relation] = []
        raw += self._extract_located_in(sentences, entities, label_index)
        raw += self._extract_communicates_with_from_room(sentences, entities, label_index)
        raw += self._extract_step_device_relations(
            sentences, entities, label_index, action_sentence_map
        )
        raw += self._extract_takes_place_in(
            sentences, entities, label_index, action_sentence_map
        )
        raw += self._extract_has_next(text, entities)

        # Deduplicare
        seen: set[str] = set()
        unique: list[Relation] = []
        for rel in raw:
            key = f"{rel.subject}__{rel.predicate.value}__{rel.object}"
            if key not in seen:
                seen.add(key)
                unique.append(rel)

        # Sumar pe tip relație
        counts: dict[str, int] = {}
        for rel in unique:
            counts[rel.predicate.value] = counts.get(rel.predicate.value, 0) + 1

        logger.info(
            "--- Extracție relații DONE: %d total | %s ---",
            len(unique),
            " | ".join(f"{k}:{v}" for k, v in counts.items()),
        )
        return unique

    # ------------------------------------------------------------------
    # Index și utilități
    # ------------------------------------------------------------------

    @staticmethod
    def _build_label_index(entities: list[Entity]) -> dict[str, Entity]:
        """Index case-insensitive: label_lower → Entity și uri_name_lower → Entity."""
        index: dict[str, Entity] = {}
        for entity in entities:
            index[entity.label.lower()] = entity
            index[entity.uri_name.lower()] = entity
        return index

    @staticmethod
    def _map_actions_to_sentences(
        sentences: list[str],
        entities: list[Entity],
    ) -> dict[str, str]:
        """
        Mapare uri_name → propoziție pentru entitățile de tip Action.

        Acțiunile sunt sintetizate prin regex (label-ul lor nu apare verbatim
        în text), deci localizarea lor se face prin re-rularea regex-urilor
        per propoziție.
        """
        action_uris = {e.uri_name for e in entities if e.entity_type == EntityType.ACTION}
        mapping: dict[str, str] = {}

        for sentence in sentences:
            for pattern, uri_name, _ in ACTION_REGEX_PATTERNS:
                if uri_name in action_uris and uri_name not in mapping:
                    if re.search(pattern, sentence, re.IGNORECASE):
                        mapping[uri_name] = sentence

        return mapping

    def _find_entities_in_text(
        self,
        text: str,
        entities: list[Entity],
        filter_types: frozenset[EntityType] | None = None,
        action_sentence_map: dict[str, str] | None = None,
    ) -> list[Entity]:
        """
        Găsește entitățile care apar în text-ul dat.

        Strategii:
        - Label: word-boundary regex match (case-insensitive)
        - URI name fallback: pentru entități scrise concatenat (ArrivingHomeRoutine)
        - Action fallback: source_text match (pentru acțiuni sintetizate)
          sau action_sentence_map lookup
        """
        found: list[Entity] = []
        seen_uris: set[str] = set()

        # Sortare descrescătoare după lungimea label-ului (evită match-uri parțiale)
        candidates = sorted(entities, key=lambda e: len(e.label), reverse=True)

        for entity in candidates:
            if filter_types and entity.entity_type not in filter_types:
                continue
            if entity.uri_name in seen_uris:
                continue

            # Strategie 1: label verbatim
            label_pat = r"\b" + re.escape(entity.label) + r"\b"
            if re.search(label_pat, text, re.IGNORECASE):
                found.append(entity)
                seen_uris.add(entity.uri_name)
                continue

            # Strategie 2: uri_name (pentru entități scrise concatenat, ex. "ArrivingHomeRoutine")
            uri_pat = r"\b" + re.escape(entity.uri_name) + r"\b"
            if re.search(uri_pat, text, re.IGNORECASE):
                found.append(entity)
                seen_uris.add(entity.uri_name)
                continue

            # Strategie 3: Action sintetizată — verifică dacă propoziția curentă
            # este propoziția în care a fost detectată această acțiune
            if (
                entity.entity_type == EntityType.ACTION
                and action_sentence_map
                and entity.uri_name in action_sentence_map
                and action_sentence_map[entity.uri_name] == text
            ):
                found.append(entity)
                seen_uris.add(entity.uri_name)

        return found

    # ------------------------------------------------------------------
    # locatedIn: "The [Room] contains [Device, ...]"
    # ------------------------------------------------------------------

    def _extract_located_in(
        self,
        sentences: list[str],
        entities: list[Entity],
        label_index: dict[str, Entity],
    ) -> list[Relation]:
        """Device locatedIn Room din propoziții cu 'contains'."""
        relations: list[Relation] = []

        for sentence in sentences:
            if "contains" not in sentence.lower():
                continue

            rooms = self._find_entities_in_text(sentence, entities, frozenset({EntityType.ROOM}))
            if not rooms:
                continue
            room = rooms[0]

            devices = self._find_entities_in_text(sentence, entities, _DEVICE_TYPES)
            for device in devices:
                rel = Relation(
                    subject=device.uri_name,
                    predicate=RelationType.LOCATED_IN,
                    object=room.uri_name,
                    source_text=sentence,
                )
                relations.append(rel)
                logger.info(
                    "  [locatedIn]     %-30s locatedIn %s",
                    device.uri_name, room.uri_name,
                )

        return relations

    # ------------------------------------------------------------------
    # communicatesWith (co-localizare Room): Device ↔ SmartHub în aceeași propoziție de tip "contains"
    # ------------------------------------------------------------------

    def _extract_communicates_with_from_room(
        self,
        sentences: list[str],
        entities: list[Entity],
        label_index: dict[str, Entity],
    ) -> list[Relation]:
        """
        Extrage Device communicatesWith SmartHub când sunt co-localizate
        în aceeași propoziție de tip '[Room] contains [...Hub...]'.
        """
        relations: list[Relation] = []
        non_hub_device_types = frozenset({EntityType.SENSOR, EntityType.ACTUATOR, EntityType.DEVICE})

        for sentence in sentences:
            if "contains" not in sentence.lower():
                continue

            hubs = self._find_entities_in_text(sentence, entities, frozenset({EntityType.SMART_HUB}))
            if not hubs:
                continue

            devices = self._find_entities_in_text(sentence, entities, non_hub_device_types)

            for device in devices:
                for hub in hubs:
                    rel = Relation(
                        subject=device.uri_name,
                        predicate=RelationType.COMMUNICATES_WITH,
                        object=hub.uri_name,
                        source_text=sentence,
                    )
                    relations.append(rel)
                    logger.info(
                        "  [commWith]      %-30s communicatesWith %s",
                        device.uri_name, hub.uri_name,
                    )

        return relations

    # ------------------------------------------------------------------
    # requiresSensor / requiresActuator / communicatesWith (din context rutină)
    # ------------------------------------------------------------------

    def _extract_step_device_relations(
        self,
        sentences: list[str],
        entities: list[Entity],
        label_index: dict[str, Entity],
        action_sentence_map: dict[str, str],
    ) -> list[Relation]:
        """
        Extrage:
        - Step requiresSensor   Sensor    (Step menționat în propoziție cu Sensor)
        - Step requiresActuator Actuator  (Step menționat în propoziție cu Actuator)
        - Step communicatesWith SmartHub  (Step menționat în propoziție cu SmartHub)

        Lucrează la nivel de propoziție. Entitățile de tip Action sunt
        localizate prin action_sentence_map.
        """
        relations: list[Relation] = []

        # Construiește lista de propoziții relevante pentru fiecare step
        # (named steps: localizate prin label/uri_name; actions: prin action_sentence_map)
        named_step_types = frozenset({
            EntityType.START_EVENT, EntityType.VERIFICATION,
            EntityType.END_EVENT, EntityType.ROUTINE_STEP,
        })

        # Propoziții cu named steps (non-Action)
        for sentence in sentences:
            named_steps = self._find_entities_in_text(sentence, entities, named_step_types)
            action_steps = [
                e for e in entities
                if e.entity_type == EntityType.ACTION
                and action_sentence_map.get(e.uri_name) == sentence
            ]
            steps = named_steps + action_steps
            if not steps:
                continue

            devices = self._find_entities_in_text(
                sentence, entities,
                frozenset({EntityType.SENSOR, EntityType.ACTUATOR, EntityType.SMART_HUB}),
            )
            if not devices:
                continue

            for step in steps:
                for device in devices:
                    predicate = _device_type_to_predicate(device.entity_type)
                    if predicate is None:
                        continue
                    rel = Relation(
                        subject=step.uri_name,
                        predicate=predicate,
                        object=device.uri_name,
                        source_text=sentence,
                    )
                    relations.append(rel)
                    logger.info(
                        "  [%-14s] %-30s %s %s",
                        predicate.value, step.uri_name, predicate.value, device.uri_name,
                    )

        return relations

    # ------------------------------------------------------------------
    # takesPlaceIn: Step + "in the [Room]"
    # ------------------------------------------------------------------

    def _extract_takes_place_in(
        self,
        sentences: list[str],
        entities: list[Entity],
        label_index: dict[str, Entity],
        action_sentence_map: dict[str, str],
    ) -> list[Relation]:
        """Step takesPlaceIn Room din propoziții cu 'in the [Room]'."""
        relations: list[Relation] = []

        named_step_types = frozenset({
            EntityType.START_EVENT, EntityType.VERIFICATION,
            EntityType.END_EVENT, EntityType.ROUTINE_STEP,
        })

        for sentence in sentences:
            if not re.search(r"\bin\s+the\b", sentence, re.IGNORECASE):
                continue

            named_steps = self._find_entities_in_text(sentence, entities, named_step_types)
            action_steps = [
                e for e in entities
                if e.entity_type == EntityType.ACTION
                and action_sentence_map.get(e.uri_name) == sentence
            ]
            steps = named_steps + action_steps
            rooms = self._find_entities_in_text(sentence, entities, frozenset({EntityType.ROOM}))

            if not steps or not rooms:
                continue

            for step in steps:
                for room in rooms:
                    rel = Relation(
                        subject=step.uri_name,
                        predicate=RelationType.TAKES_PLACE_IN,
                        object=room.uri_name,
                        source_text=sentence,
                    )
                    relations.append(rel)
                    logger.info(
                        "  [takesPlaceIn]  %-30s takesPlaceIn %s",
                        step.uri_name, room.uri_name,
                    )

        return relations

    # ------------------------------------------------------------------
    # hasNext: Secvența pașilor în ordinea apariției în text
    # ------------------------------------------------------------------

    def _extract_has_next(
        self,
        text: str,
        entities: list[Entity],
    ) -> list[Relation]:
        """
        Detectează secvența pașilor de rutină în ordinea primei apariții în text.

        Strategii de localizare per tip entitate:
        - Named steps (StartEvent, Verification): caută label sau uri_name verbatim.
        - Action (sintetizate): caută source_text (regex match original) în text,
          deoarece label-ul ("Turn on Smart Lights") nu apare verbatim.
        """
        step_positions: list[tuple[int, Entity]] = []

        for entity in entities:
            if entity.entity_type not in _STEP_TYPES:
                continue

            m = None

            if entity.entity_type == EntityType.ACTION:
                # Acțiunile sintetizate se localizează prin source_text (textul regex match-ului)
                if entity.source_text:
                    m = re.search(re.escape(entity.source_text), text, re.IGNORECASE)
            else:
                # Named steps: caută label verbatim, fallback uri_name
                m = re.search(r"\b" + re.escape(entity.label) + r"\b", text, re.IGNORECASE)
                if not m:
                    m = re.search(r"\b" + re.escape(entity.uri_name) + r"\b", text, re.IGNORECASE)

            if m:
                step_positions.append((m.start(), entity))

        step_positions.sort(key=lambda x: x[0])
        ordered = [entity for _, entity in step_positions]

        relations: list[Relation] = []
        for current, nxt in pairwise(ordered):
            rel = Relation(
                subject=current.uri_name,
                predicate=RelationType.HAS_NEXT,
                object=nxt.uri_name,
                source_text=f"Sequence: {current.uri_name} → {nxt.uri_name}",
            )
            relations.append(rel)
            logger.info(
                "  [hasNext]       %-30s hasNext %s",
                current.uri_name, nxt.uri_name,
            )

        return relations


# ---------------------------------------------------------------------------
# Funcție utilitară
# ---------------------------------------------------------------------------

def _device_type_to_predicate(entity_type: EntityType) -> RelationType | None:
    """Mapează tipul dispozitivului la predicatul relației corespunzătoare."""
    match entity_type:
        case EntityType.SENSOR:
            return RelationType.REQUIRES_SENSOR
        case EntityType.ACTUATOR:
            return RelationType.REQUIRES_ACTUATOR
        case EntityType.SMART_HUB:
            return RelationType.COMMUNICATES_WITH
        case _:
            return None
