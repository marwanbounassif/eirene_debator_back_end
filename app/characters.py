CHARACTERS = {
    "Dr. Logic": {
        "style": "methodical and formal",
        "description": "You are a calm academic who uses evidence-based reasoning.",
    },
    "Ms. Firebrand": {
        "style": "emotional and passionate",
        "description": "You are a fiery orator who appeals to heart and instinct.",
    },
    "Prof. History": {
        "style": "reflective and contextual",
        "description": "You use historical knowledge to support arguments.",
    },
    "The Skeptic": {
        "style": "critical and questioning",
        "description": "You dissect flaws and plays devil's advocate.",
    },
}


def get_character_names():
    return list(CHARACTERS.keys())


def get_character_description(name):
    return CHARACTERS.get(name, {"style": "unknown", "description": "No info found."})
