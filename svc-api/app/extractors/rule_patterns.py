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
    "LivingRoom": [{"LOWER": "living"}, {"LOWER": "room"}],
    "Kitchen":    [{"LOWER": "kitchen"}],
    "EntryHall":  [{"LOWER": "entry"}, {"LOWER": "hall"}],
    "Garage":     [{"LOWER": "garage"}],
    "Bedroom":    [{"LOWER": "bedroom"}],
    "Bathroom":   [{"LOWER": "bathroom"}],
}

# ---------------------------------------------------------------------------
# Sensors (subclasă Device)
# ---------------------------------------------------------------------------

SENSOR_PATTERNS: dict[str, list[dict]] = {
    # Senzori cu 3+ token-uri — vor câștiga la overlap față de Garage/FrontDoor singulare
    "FrontDoorSensor": [
        {"LOWER": "front"}, {"LOWER": "door"}, {"LOWER": "sensor"},
    ],
    "GarageDoorSensor": [
        {"LOWER": "garage"}, {"LOWER": "door"}, {"LOWER": "sensor"},
    ],
    "TemperatureHumiditySensor": [
        {"LOWER": "temperature"}, {"LOWER": "and"},
        {"LOWER": "humidity"}, {"LOWER": "sensor"},
    ],
    # Senzori cu 2 token-uri
    "PresenceSensor": [{"LOWER": "presence"}, {"LOWER": "sensor"}],
    "MotionSensor":   [{"LOWER": "motion"}, {"LOWER": "sensor"}],
    "SmokeSensor":    [{"LOWER": "smoke"}, {"LOWER": "sensor"}],
}

# ---------------------------------------------------------------------------
# Actuators (subclasă Device)
# ---------------------------------------------------------------------------

ACTUATOR_PATTERNS: dict[str, list[dict]] = {
    # 2 token-uri
    "SmartTV":          [{"LOWER": "smart"}, {"LOWER": "tv"}],
    "SmartSpeakers":    [{"LOWER": "smart"}, {"LOWER": "speakers"}],
    "SmartLights":      [{"LOWER": "smart"}, {"LOWER": "lights"}],
    "SmartBlinds":      [{"LOWER": "smart"}, {"LOWER": "blinds"}],
    "SmartLock":        [{"LOWER": "smart"}, {"LOWER": "lock"}],
    "SmartFridge":      [{"LOWER": "smart"}, {"LOWER": "fridge"}],
    "BedroomThermostat":[{"LOWER": "bedroom"}, {"LOWER": "thermostat"}],
}

# ---------------------------------------------------------------------------
# SmartHubs (subclasă Device)
# ---------------------------------------------------------------------------

SMART_HUB_PATTERNS: dict[str, list[dict]] = {
    "MultimediaHub": [{"LOWER": "multimedia"}, {"LOWER": "hub"}],
    "ComfortHub":    [{"LOWER": "comfort"}, {"LOWER": "hub"}],
    "HomeAutomationGateway": [
        {"LOWER": "home"}, {"LOWER": "automation"}, {"LOWER": "gateway"},
    ],
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
        r"turns?\s+on\s+(?:the\s+)?Smart\s+Lights",
        "TurnLightsOn",
        "Turn on Smart Lights",
    ),
    # "turns on music in the Living Room" → TurnMusicOn
    (
        r"turns?\s+on\s+music",
        "TurnMusicOn",
        "Turn on music",
    ),
    # "checks the temperature in the Bedroom" → CheckTemperature
    (
        r"checks?\s+the\s+temperature",
        "CheckTemperature",
        "Check temperature",
    ),
    # "adjusts it through the Bedroom Thermostat" → AdjustTemperature
    (
        r"adjusts?\s+it\s+through",
        "AdjustTemperature",
        "Adjust temperature",
    ),
]
