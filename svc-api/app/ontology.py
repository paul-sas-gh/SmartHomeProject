"""
ontology.py — Namespace-uri RDF, clase OWL și proprietăți pentru ontologia Smart Home.

Namespace principal:
    SH = http://smarthome.org/ontology#

Clase OWL (mapate din EntityType):
    SH.Room, SH.Device, SH.Sensor, SH.Actuator, SH.SmartHub,
    SH.RoutineStep, SH.StartEvent, SH.Verification, SH.Action, SH.EndEvent

Proprietăți obiect (mapate din RelationType):
    SH.locatedIn, SH.requiresSensor, SH.requiresActuator,
    SH.takesPlaceIn, SH.hasNext, SH.communicatesWith

Proprietăți date (pentru datele externe din OntoRefine):
    SH.brand, SH.price, SH.energyClass, SH.protocol, SH.label
"""

from rdflib import OWL, RDF, RDFS, Namespace
from rdflib.term import URIRef

# ---------------------------------------------------------------------------
# Namespace-uri
# ---------------------------------------------------------------------------

SH = Namespace("http://smarthome.org/ontology#")
SH_INST = Namespace("http://smarthome.org/instance#")

# ---------------------------------------------------------------------------
# Clase OWL
# ---------------------------------------------------------------------------

# Mapare EntityType.value → URIRef clasă OWL
ENTITY_CLASS_MAP: dict[str, URIRef] = {
    "Room":        SH.Room,
    "Device":      SH.Device,
    "Sensor":      SH.Sensor,
    "Actuator":    SH.Actuator,
    "SmartHub":    SH.SmartHub,
    "RoutineStep": SH.RoutineStep,
    "StartEvent":  SH.StartEvent,
    "Verification": SH.Verification,
    "Action":      SH.Action,
    "EndEvent":    SH.EndEvent,
}

# ---------------------------------------------------------------------------
# Proprietăți obiect
# ---------------------------------------------------------------------------

# Mapare RelationType.value → URIRef proprietate OWL
RELATION_PROPERTY_MAP: dict[str, URIRef] = {
    "locatedIn":        SH.locatedIn,
    "requiresSensor":   SH.requiresSensor,
    "requiresActuator": SH.requiresActuator,
    "takesPlaceIn":     SH.takesPlaceIn,
    "hasNext":          SH.hasNext,
    "communicatesWith": SH.communicatesWith,
}

# ---------------------------------------------------------------------------
# Proprietăți date (pentru datele externe)
# ---------------------------------------------------------------------------

DATA_PROPERTIES: dict[str, URIRef] = {
    "brand":       SH.brand,
    "price":       SH.price,
    "energyClass": SH.energyClass,
    "protocol":    SH.protocol,
}

# ---------------------------------------------------------------------------
# Definiții axiome OWL de bază (pentru prefixarea ontologiei în fișierul TTL)
# ---------------------------------------------------------------------------

ONTOLOGY_URI = URIRef("http://smarthome.org/ontology")

# Ierarhia subClass
CLASS_HIERARCHY: list[tuple[URIRef, URIRef]] = [
    # subclase ale Device
    (SH.Sensor,      SH.Device),
    (SH.Actuator,    SH.Device),
    (SH.SmartHub,    SH.Device),
    # subclase ale RoutineStep
    (SH.StartEvent,  SH.RoutineStep),
    (SH.Verification, SH.RoutineStep),
    (SH.Action,      SH.RoutineStep),
    (SH.EndEvent,    SH.RoutineStep),
]

# Domeniile și rangele proprietăților obiect (opțional, pentru validare SPARQL)
PROPERTY_DOMAIN_RANGE: list[tuple[URIRef, URIRef, URIRef]] = [
    (SH.locatedIn,        SH.Device,      SH.Room),
    (SH.requiresSensor,   SH.RoutineStep, SH.Sensor),
    (SH.requiresActuator, SH.RoutineStep, SH.Actuator),
    (SH.takesPlaceIn,     SH.RoutineStep, SH.Room),
    (SH.hasNext,          SH.RoutineStep, SH.RoutineStep),
    (SH.communicatesWith, SH.Device,      SH.SmartHub),
]
