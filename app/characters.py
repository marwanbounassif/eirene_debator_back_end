CHARACTERS = {
    "Dr. Logic": {
        "style": "methodical and formal",
        "description": "A calm academic who uses evidence-based reasoning.",
    },
    "Ms. Firebrand": {
        "style": "emotional and passionate",
        "description": "A fiery orator who appeals to heart and instinct.",
    },
    "Prof. History": {
        "style": "reflective and contextual",
        "description": "Uses historical knowledge to support arguments.",
    },
    "The Skeptic": {
        "style": "critical and questioning",
        "description": "Dissects flaws and plays devil's advocate.",
    },
}


def get_character_names():
    return list(CHARACTERS.keys())


def get_character_description(name):
    return CHARACTERS.get(name, {"style": "unknown", "description": "No info found."})
