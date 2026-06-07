"""
entity_extractor.py — Extracție entități Smart Home cu spaCy Matcher și regex.

Strategia de detecție:
    1. spaCy Matcher — entități fizice (Room, Sensor, Actuator, SmartHub)
       și pași de rutină denumiți explicit (ArrivingHomeRoutine, CheckPresence).
    2. Regex fallback — acțiuni sintetizate din fraze trigger
       (TurnLightsOn, TurnMusicOn, CheckTemperature, AdjustTemperature).

Deduplicare: o singură entitate per (entity_type, uri_name).
Suprapuneri: filter_spans() — câștigă span-ul mai lung
(ex: "Garage Door Sensor" > "Garage" ca Room).

Utilizare:
    extractor = EntityExtractor()
    entities = extractor.extract(text)
"""

import logging
import re

import spacy
from spacy.matcher import Matcher
from spacy.util import filter_spans

from app.config import settings
from app.models import (
    ActionEntity,
    ActuatorEntity,
    DeviceEntity,
    EndEventEntity,
    Entity,
    EntityType,
    RoomEntity,
    RoutineStepEntity,
    SensorEntity,
    SmartHubEntity,
    StartEventEntity,
    VerificationEntity,
)
from app.extractors.rule_patterns import (
    ACTION_REGEX_PATTERNS,
    ACTUATOR_PATTERNS,
    NAMED_STEP_PATTERNS,
    ROOM_PATTERNS,
    SENSOR_PATTERNS,
    SMART_HUB_PATTERNS,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Singleton loader — modelul spaCy se încarcă o singură dată
# ---------------------------------------------------------------------------
_extractor_instance: "EntityExtractor | None" = None


def get_extractor() -> "EntityExtractor":
    """Returnează instanța singleton a EntityExtractor (lazy init)."""
    global _extractor_instance
    if _extractor_instance is None:
        _extractor_instance = EntityExtractor()
    return _extractor_instance


# ---------------------------------------------------------------------------
# EntityExtractor
# ---------------------------------------------------------------------------

class EntityExtractor:
    """
    Extrage entități din descrieri Smart Home în limbaj natural.

    Detectează:
    - Room (Living Room, Kitchen, Entry Hall, Garage, Bedroom, Bathroom)
    - Sensor (Front Door Sensor, Presence Sensor, Motion Sensor, etc.)
    - Actuator (Smart Lights, Smart Lock, Bedroom Thermostat, etc.)
    - SmartHub (Multimedia Hub, Comfort Hub, Home Automation Gateway)
    - StartEvent, Verification, Action (pași de rutină)
    """

    def __init__(self) -> None:
        self._nlp = spacy.load(settings.spacy_model)
        self._matcher = Matcher(self._nlp.vocab)
        # rule_id → (EntityType, uri_name)
        self._rule_map: dict[str, tuple[EntityType, str]] = {}
        self._build_matcher()
        logger.info(
            "EntityExtractor inițializat cu modelul '%s' (%d reguli Matcher)",
            settings.spacy_model,
            len(self._rule_map),
        )

    # ------------------------------------------------------------------
    # Construcție Matcher
    # ------------------------------------------------------------------

    def _register(
        self,
        prefix: str,
        entity_type: EntityType,
        uri_name: str,
        pattern: list[dict],
    ) -> None:
        """Înregistrează o regulă în Matcher și în rule_map."""
        rule_id = f"{prefix}__{uri_name}"
        self._matcher.add(rule_id, [pattern])
        self._rule_map[rule_id] = (entity_type, uri_name)

    def _build_matcher(self) -> None:
        """Populează Matcher-ul cu toate pattern-urile definite în rule_patterns."""
        for uri_name, pattern in ROOM_PATTERNS.items():
            self._register("ROOM", EntityType.ROOM, uri_name, pattern)

        for uri_name, pattern in SENSOR_PATTERNS.items():
            self._register("SENSOR", EntityType.SENSOR, uri_name, pattern)

        for uri_name, pattern in ACTUATOR_PATTERNS.items():
            self._register("ACTUATOR", EntityType.ACTUATOR, uri_name, pattern)

        for uri_name, pattern in SMART_HUB_PATTERNS.items():
            self._register("HUB", EntityType.SMART_HUB, uri_name, pattern)

        for uri_name, (step_type_str, pattern) in NAMED_STEP_PATTERNS.items():
            entity_type = EntityType(step_type_str)
            self._register("STEP", entity_type, uri_name, pattern)

        logger.debug("Matcher construit: %d reguli", len(self._rule_map))

    # ------------------------------------------------------------------
    # Construcție entități
    # ------------------------------------------------------------------

    @staticmethod
    def _make_entity(
        entity_type: EntityType,
        uri_name: str,
        label: str,
        source_text: str,
    ) -> Entity:
        """Instanțiază subclasa corectă de Entity în funcție de entity_type."""
        kwargs: dict = dict(label=label, uri_name=uri_name, source_text=source_text)
        match entity_type:
            case EntityType.ROOM:
                return RoomEntity(**kwargs)
            case EntityType.SENSOR:
                return SensorEntity(**kwargs)
            case EntityType.ACTUATOR:
                return ActuatorEntity(**kwargs)
            case EntityType.SMART_HUB:
                return SmartHubEntity(**kwargs)
            case EntityType.START_EVENT:
                return StartEventEntity(**kwargs)
            case EntityType.VERIFICATION:
                return VerificationEntity(**kwargs)
            case EntityType.ACTION:
                return ActionEntity(**kwargs)
            case EntityType.END_EVENT:
                return EndEventEntity(**kwargs)
            case _:
                return Entity(entity_type=entity_type, **kwargs)

    # ------------------------------------------------------------------
    # Extracție Matcher
    # ------------------------------------------------------------------

    def _extract_from_matcher(self, doc) -> list[Entity]:
        """
        Rulează Matcher pe doc, filtrează suprapunerile și returnează entitățile.

        Logica filter_spans: dacă "Garage" (Room) și "Garage Door Sensor" (Sensor)
        se suprapun, câștigă span-ul mai lung → "Garage Door Sensor".
        """
        raw_matches = self._matcher(doc)

        # Construiește span-uri și mapare id → rule_id
        spans: list = []
        span_to_rule: dict[int, str] = {}

        for match_id, start, end in raw_matches:
            span = doc[start:end]
            rule_id = self._nlp.vocab.strings[match_id]
            spans.append(span)
            span_to_rule[id(span)] = rule_id

        filtered = filter_spans(spans)

        seen: set[str] = set()
        entities: list[Entity] = []

        for span in filtered:
            rule_id = span_to_rule.get(id(span))
            if rule_id is None or rule_id not in self._rule_map:
                continue

            entity_type, uri_name = self._rule_map[rule_id]
            # Normalize uri_name for _alt patterns
            clean_uri = uri_name.replace("_alt", "")
            
            dedup_key = f"{entity_type.value}__{clean_uri}"
            if dedup_key in seen:
                continue
            seen.add(dedup_key)

            entity = self._make_entity(entity_type, clean_uri, span.text, span.text)
            entities.append(entity)
            logger.info(
                "  [Matcher] %-30s %-14s ← '%s'",
                clean_uri, entity_type.value, span.text,
            )

        return entities

    # ------------------------------------------------------------------
    # Extracție Regex (acțiuni sintetizate)
    # ------------------------------------------------------------------

    def _extract_actions_regex(self, text: str) -> list[Entity]:
        """
        Detectează acțiuni de rutină prin regex și le sintetizează ca ActionEntity.

        Fiecare regex din ACTION_REGEX_PATTERNS caută un trigger phrase în text.
        Entitatea sintetizată primește uri_name și label pre-definite.
        """
        seen: set[str] = set()
        entities: list[Entity] = []

        for pattern, uri_name, label in ACTION_REGEX_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match and uri_name not in seen:
                seen.add(uri_name)
                entity = ActionEntity(
                    label=label,
                    uri_name=uri_name,
                    source_text=match.group(0),
                )
                entities.append(entity)
                logger.info(
                    "  [regex]   %-30s %-14s ← '%s'",
                    uri_name, EntityType.ACTION.value, match.group(0),
                )

        return entities

    # ------------------------------------------------------------------
    # Interfața publică
    # ------------------------------------------------------------------

    def extract(self, text: str) -> list[Entity]:
        """
        Extrage toate entitățile unice din text.

        Args:
            text: Textul curat (output din text_loader.load_text).

        Returns:
            Listă de entități unice, deduplicate pe (entity_type, uri_name).
        """
        logger.info("--- Extracție entități START ---")
        doc = self._nlp(text)

        matcher_entities = self._extract_from_matcher(doc)
        regex_entities = self._extract_actions_regex(text)

        # Deduplicare finală (matcher + regex pot genera același uri_name)
        seen: set[str] = set()
        unique: list[Entity] = []
        for entity in matcher_entities + regex_entities:
            key = f"{entity.entity_type.value}__{entity.uri_name}"
            if key not in seen:
                seen.add(key)
                unique.append(entity)

        rooms = [e for e in unique if e.entity_type == EntityType.ROOM]
        devices = [
            e for e in unique
            if e.entity_type in (EntityType.SENSOR, EntityType.ACTUATOR, EntityType.SMART_HUB, EntityType.DEVICE)
        ]
        steps = [
            e for e in unique
            if e.entity_type in (
                EntityType.START_EVENT, EntityType.VERIFICATION,
                EntityType.ACTION, EntityType.END_EVENT, EntityType.ROUTINE_STEP,
            )
        ]

        logger.info(
            "--- Extracție entități DONE: %d total | %d Room | %d Device | %d RoutineStep ---",
            len(unique), len(rooms), len(devices), len(steps),
        )
        return unique
