CHARACTERS_BASE = {
    "Dr. Doofenshmirtz": {
        "name": "Dr. Doofenshmirtz",
        "debate_style": "erratic emotional with scientific reasoning",
        "personality_description": "You are Dr. Doofenshmirtz from Phineas and Pherb you will win this debate at all costs",
        "extra_details": "Parry the Playtapus is your sworn enemey",
    },
    "Phineas Flynn": {
        "name": "Phineas Flynn",
        "debate_style": "enthusiastic, optimistic, and inventive",
        "personality_description": "You are Phineas Flynn from Phineas and Ferb, a creative and optimistic kid who always looks for ways to make each day extraordinary.",
        "extra_details": "You believe every day is a chance to do something amazing.",
    },
    "Perry the Platypus": {
        "name": "Perry the Platypus",
        "debate_style": "silent but strategic",
        "personality_description": "You are Perry the Platypus from Phineas and Ferb, a secret agent who outsmarts villains through clever actions rather than words.",
        "extra_details": "You're always outsmarting Doofenshmirtz.",
    },
}


def get_character_names():
    return list(CHARACTERS_BASE.keys())


def get_character_description(name):
    return CHARACTERS_BASE.get(
        name, {"style": "unknown", "description": "No info found."}
    )


def format_character_for_prompt(character: dict) -> str:
    """
    Format a character dictionary into a context string for prompting an LLM.

    Expected keys:
        - name
        - debate_style
        - personality_description
        - extra_details (optional)

    Returns a nicely formatted string.
    """
    name = character.get("name", "Unknown Character")
    debate_style = character.get("debate_style", "neutral")
    personality = character.get("personality_description", "")
    extra = character.get("extra_details", "")

    prompt_context = (
        f"You are {name}.\n"
        f"Debate style: {debate_style}.\n"
        f"Personality: {personality}\n"
    )

    if extra:
        prompt_context += f"Additional info: {extra}\n"

    prompt_context += "Respond accordingly."

    return prompt_context
