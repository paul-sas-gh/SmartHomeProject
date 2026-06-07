"""
rule_patterns.py — Pattern-uri spaCy și regex pentru detecția entităților Smart Home.

Structură:
    ROOM_PATTERNS       — uri_name → token pattern spaCy
    SENSOR_PATTERNS     — uri_name → token pattern spaCy
    ACTUATOR_PATTERNS   — uri_name → token pattern spaCy
    SMART_HUB_PATTERNS  — uri_name → token pattern spaCy
    NAMED_STEP_PATTERNS — uri_name → (entity_type_str, token pattern spaCy)
    ACTION_REGEX_PATTERNS — [(regex, uri_name, canonical_label)]

Notă: pattern-urile mai lungi vor câștiga la filtrarea suprapunerilor (filter_spans),
deci ordinea din dict nu contează pentru corectitudinea extracției.
"""

# ---------------------------------------------------------------------------
# Rooms
# ---------------------------------------------------------------------------
# uri_name → listă de token dicts spaCy (atribut LOWER = lowercase insensibil la majuscule)

ROOM_PATTERNS: dict[str, list[dict]] = {
    "EntryRoom": [{"LOWER": "entryroom"}],
    "EntryRoom_alt": [{"LOWER": "entry"}, {"LOWER": "room"}],
    "KidsDorm1": [{"LOWER": "kidsdorm1"}],
    "KidsDorm1_alt": [{"LOWER": "kids"}, {"LOWER": "dorm"}, {"LOWER": "1"}],
    "KidsDorm2": [{"LOWER": "kidsdorm2"}],
    "KidsDorm2_alt": [{"LOWER": "kids"}, {"LOWER": "dorm"}, {"LOWER": "2"}],
    "LivingRoom": [{"LOWER": "livingroom"}],
    "LivingRoom_alt": [{"LOWER": "living"}, {"LOWER": "room"}],
    "ParentsDorm": [{"LOWER": "parentsdorm"}],
    "ParentsDorm_alt": [{"LOWER": "parents"}, {"LOWER": "dorm"}],
    "kitchen": [{"LOWER": "kitchen"}],
}

# ---------------------------------------------------------------------------
# Sensors (subclasă Device)
# ---------------------------------------------------------------------------

SENSOR_PATTERNS: dict[str, list[dict]] = {
    "MSensor0": [{"LOWER": "msensor0"}],
    "MSensor1": [{"LOWER": "msensor1"}],
    "MSensor2": [{"LOWER": "msensor2"}],
    "MSensor3": [{"LOWER": "msensor3"}],
    "MSensor4": [{"LOWER": "msensor4"}],
    "MSensorEntry": [{"LOWER": "msensorentry"}],
    "SmokeSensor": [{"LOWER": "smokesensor"}],
    "TSensor1": [{"LOWER": "tsensor1"}],
    "TSensor2": [{"LOWER": "tsensor2"}],
    "TSensor3": [{"LOWER": "tsensor3"}],
    "Tsensor0": [{"LOWER": "tsensor0"}],
    # Generic patterns for natural language
    "MotionSensor": [{"LOWER": "motion"}, {"LOWER": "sensor"}],
    "TemperatureSensor": [{"LOWER": "temperature"}, {"LOWER": "sensor"}],
}

# ---------------------------------------------------------------------------
# Actuators (subclasă Device)
# ---------------------------------------------------------------------------

ACTUATOR_PATTERNS: dict[str, list[dict]] = {
    "AirCondtioner0": [{"LOWER": "aircondtioner0"}],
    "AirCondtioner1": [{"LOWER": "aircondtioner1"}],
    "AirCondtioner2": [{"LOWER": "aircondtioner2"}],
    "AirCondtioner3": [{"LOWER": "aircondtioner3"}],
    "Alarm0": [{"LOWER": "alarm0"}],
    "Alarm1": [{"LOWER": "alarm1"}],
    "CoffeMachine": [{"LOWER": "coffemachine"}],
    "RoomLight0": [{"LOWER": "roomlight0"}],
    "RoomLight1": [{"LOWER": "roomlight1"}],
    "RoomLight2": [{"LOWER": "roomlight2"}],
    "RoomLight3": [{"LOWER": "roomlight3"}],
    "RoomLight4": [{"LOWER": "roomlight4"}],
    "Shutter0": [{"LOWER": "shutter0"}],
    "Shutter1": [{"LOWER": "shutter1"}],
    "Shutter2": [{"LOWER": "shutter2"}],
    "Shutter3": [{"LOWER": "shutter3"}],
    "SmartTV0": [{"LOWER": "smarttv0"}],
    "SmartTV1": [{"LOWER": "smarttv1"}],
    "SmartTV2": [{"LOWER": "smarttv2"}],
    "SmartTV3": [{"LOWER": "smarttv3"}],
    "Speaker0": [{"LOWER": "speaker0"}],
    "Speaker1": [{"LOWER": "speaker1"}],
    "Speaker2": [{"LOWER": "speaker2"}],
    "Speaker3": [{"LOWER": "speaker3"}],
    "Speaker4": [{"LOWER": "speaker4"}],
    # Generic patterns
    "AirConditioner": [{"LOWER": "air"}, {"LOWER": "conditioner"}],
    "Light": [{"LOWER": "light"}],
    "TV": [{"LOWER": "tv"}],
}

# ---------------------------------------------------------------------------
# SmartHubs (subclasă Device)
# ---------------------------------------------------------------------------

SMART_HUB_PATTERNS: dict[str, list[dict]] = {
    "SmartHub": [{"LOWER": "smart"}, {"LOWER": "hub"}],
    "SmartHub1": [{"LOWER": "smart"}, {"LOWER": "hub"}, {"LOWER": "1"}],
    "SmartHub2": [{"LOWER": "smart"}, {"LOWER": "hub2"}],
    "SmartHub3": [{"LOWER": "smart"}, {"LOWER": "hub"}, {"LOWER": "3"}],
    "SmartHub4": [{"LOWER": "smart"}, {"LOWER": "hub"}, {"LOWER": "4"}],
}

# ---------------------------------------------------------------------------
# Named RoutineStep patterns (apar verbatim în text)
# uri_name → (entity_type_str, token pattern)
# entity_type_str: "StartEvent" | "Verification" | "Action" | "EndEvent"
# ---------------------------------------------------------------------------

NAMED_STEP_PATTERNS: dict[str, tuple[str, list[dict]]] = {
    # Rutina → StartEvent (declanșată de senzor, nu are un pas anterior)
    "ArrivingHomeRoutine": (
        "StartEvent",
        [{"LOWER": "arrivinghomeroutine"}],
    ),
    # Pas de verificare explicit denumit în text
    "CheckPresence": (
        "Verification",
        [{"LOWER": "checkpresence"}],
    ),
}

# ---------------------------------------------------------------------------
# Action regex patterns (entități sintetizate din fraze trigger)
#
# Fiecare tuple: (regex_pattern, uri_name, canonical_label)
# Regex este case-insensitive și caută în textul complet.
# Ordinea contează: pattern-urile mai specifice trebuie să fie primele.
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Relații — cuvinte cheie și pattern-uri regex
# ---------------------------------------------------------------------------

# locatedIn — propoziții de tip "Room contains Device"
CONTAINS_KEYWORDS: list[str] = ["contains"]

# hasNext — cuvinte cheie care marchează un pas următor în secvența rutinei
SEQUENCE_KEYWORDS: list[str] = [
    "then", "after that", "next", "finally", "subsequently", "if no one", "if no one is present",
]

# requiresSensor / requiresActuator / communicatesWith — context de utilizare dispozitiv
USING_KEYWORDS: list[str] = ["using", "through", "via"]

# takesPlaceIn — prepoziție spațială
SPATIAL_PREPOSITIONS: list[str] = ["in the", "in", "at the", "at"]

# ---------------------------------------------------------------------------
# Action regex patterns (entități sintetizate din fraze trigger)
# ---------------------------------------------------------------------------

ACTION_REGEX_PATTERNS: list[tuple[str, str, str]] = [
    # "turns on the Smart Lights in the Entry Hall" → TurnLightsOn
    (
        r"turns?\s+on\s+(?:the\s+)?(?:RoomLight|Smart\s+Lights)",
        "TurnLightsOn",
        "Turn on Smart Lights",
    ),
    # "turns on music in the Living Room" → TurnMusicOn
    (
        r"turns?\s+on\s+music|turns?\s+on\s+Speaker",
        "TurnMusicOn",
        "Turn on music",
    ),
    # "checks the temperature in the Bedroom" → CheckTemperature
    (
        r"checks?\s+the\s+temperature|checks?\s+TSensor",
        "CheckTemperature",
        "Check temperature",
    ),
    # "adjusts it through the Bedroom Thermostat" → AdjustTemperature
    (
        r"adjusts?\s+it\s+through|adjusts?\s+AirCondtioner",
        "AdjustTemperature",
        "Adjust temperature",
    ),
]
