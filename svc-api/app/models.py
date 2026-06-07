"""
models.py — Modele Pydantic pentru entități, relații și rezultatul extracției.

Ierarhie entități:
    Entity (bază)
    ├── RoomEntity
    ├── DeviceEntity (bază)
    │   ├── SensorEntity
    │   ├── ActuatorEntity
    │   └── SmartHubEntity
    └── RoutineStepEntity (bază)
        ├── StartEventEntity
        ├── VerificationEntity
        ├── ActionEntity
        └── EndEventEntity
"""

from __future__ import annotations

from enum import Enum
from typing import Annotated, Union

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class EntityType(str, Enum):
    ROOM = "Room"
    SENSOR = "Sensor"
    ACTUATOR = "Actuator"
    SMART_HUB = "SmartHub"
    DEVICE = "Device"                # tip generic dacă subtipul nu e determinat
    START_EVENT = "StartEvent"
    VERIFICATION = "Verification"
    ACTION = "Action"
    END_EVENT = "EndEvent"
    ROUTINE_STEP = "RoutineStep"     # tip generic dacă subtipul nu e determinat


class RelationType(str, Enum):
    LOCATED_IN = "locatedIn"
    REQUIRES_SENSOR = "requiresSensor"
    REQUIRES_ACTUATOR = "requiresActuator"
    TAKES_PLACE_IN = "takesPlaceIn"
    HAS_NEXT = "hasNext"
    COMMUNICATES_WITH = "communicatesWith"


# ---------------------------------------------------------------------------
# Entități de bază
# ---------------------------------------------------------------------------

class Entity(BaseModel):
    """Entitate extrasă din text."""
    label: str = Field(..., description="Eticheta originală din text (ex: 'Living Room')")
    uri_name: str = Field(..., description="Numele normalizat pentru URI RDF (ex: 'LivingRoom')")
    entity_type: EntityType
    source_text: str = Field(default="", description="Fragmentul de text din care a fost extrasă")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class RoomEntity(Entity):
    entity_type: EntityType = EntityType.ROOM


class DeviceEntity(Entity):
    entity_type: EntityType = EntityType.DEVICE
    room: str | None = Field(default=None, description="URI room în care este amplasat dispozitivul")


class SensorEntity(DeviceEntity):
    entity_type: EntityType = EntityType.SENSOR


class ActuatorEntity(DeviceEntity):
    entity_type: EntityType = EntityType.ACTUATOR


class SmartHubEntity(DeviceEntity):
    entity_type: EntityType = EntityType.SMART_HUB


class RoutineStepEntity(Entity):
    entity_type: EntityType = EntityType.ROUTINE_STEP
    routine_name: str | None = Field(default=None, description="Rutina din care face parte")


class StartEventEntity(RoutineStepEntity):
    entity_type: EntityType = EntityType.START_EVENT


class VerificationEntity(RoutineStepEntity):
    entity_type: EntityType = EntityType.VERIFICATION


class ActionEntity(RoutineStepEntity):
    entity_type: EntityType = EntityType.ACTION


class EndEventEntity(RoutineStepEntity):
    entity_type: EntityType = EntityType.END_EVENT


# Union tip pentru annotare generică
AnyEntity = Annotated[
    Union[
        RoomEntity,
        SensorEntity,
        ActuatorEntity,
        SmartHubEntity,
        DeviceEntity,
        StartEventEntity,
        VerificationEntity,
        ActionEntity,
        EndEventEntity,
        RoutineStepEntity,
    ],
    Field(discriminator="entity_type"),
]


# ---------------------------------------------------------------------------
# Relații
# ---------------------------------------------------------------------------

class Relation(BaseModel):
    """Relație semantică între două entități."""
    subject: str = Field(..., description="URI name al subiectului (ex: 'SmartLights')")
    predicate: RelationType
    object: str = Field(..., description="URI name al obiectului (ex: 'EntryHall')")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    source_text: str = Field(default="", description="Propoziția sursă")


# ---------------------------------------------------------------------------
# Rezultat extracție
# ---------------------------------------------------------------------------

class ExtractionResult(BaseModel):
    """Rezultatul complet al unui ciclu de extracție NLP."""
    source_file: str = Field(default="", description="Calea fișierului sursă")
    raw_text: str = Field(default="", description="Textul original curat")
    entities: list[Entity] = Field(default_factory=list)
    relations: list[Relation] = Field(default_factory=list)

    @property
    def rooms(self) -> list[Entity]:
        return [e for e in self.entities if e.entity_type == EntityType.ROOM]

    @property
    def devices(self) -> list[Entity]:
        return [e for e in self.entities if e.entity_type in (
            EntityType.SENSOR, EntityType.ACTUATOR, EntityType.SMART_HUB, EntityType.DEVICE
        )]

    @property
    def routine_steps(self) -> list[Entity]:
        return [e for e in self.entities if e.entity_type in (
            EntityType.START_EVENT, EntityType.VERIFICATION,
            EntityType.ACTION, EntityType.END_EVENT, EntityType.ROUTINE_STEP
        )]

    def summary(self) -> dict:
        return {
            "total_entities": len(self.entities),
            "rooms": len(self.rooms),
            "devices": len(self.devices),
            "routine_steps": len(self.routine_steps),
            "relations": len(self.relations),
        }


# ---------------------------------------------------------------------------
# Rezultat pipeline complet (utilizat în Faza 10)
# ---------------------------------------------------------------------------

class QueryResult(BaseModel):
    """Rezultatul unei interogări SPARQL declanșate de text."""
    query_id: int | None = None
    query: str
    results: list[dict] = Field(default_factory=list)


class PipelineResult(BaseModel):
    """Rezultatul orchestrării complete a pipeline-ului."""
    extraction: ExtractionResult
    ttl_path: str = Field(default="", description="Calea fișierului .ttl generat")
    triple_count: int = Field(default=0)
    graphdb_uploaded: bool = Field(default=False)
    llm_used: bool = Field(default=False)
    query_result: QueryResult | None = None
