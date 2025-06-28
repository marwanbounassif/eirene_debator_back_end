import os
from pathlib import Path
import json
from app.model_interface.llama_debator import LlamaDebator
from dotenv import load_dotenv

load_dotenv()

HF_API_KEY = os.getenv("HF_API_KEY")
HF_MODEL = os.getenv("MODEL_ID")
LLAMA_DEBATOR = LlamaDebator(model_name=HF_MODEL, api_key=HF_API_KEY)

CHARACTER_DUMP_PATH = Path(os.getenv("CHARACTER_DUMP_PATH"))

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
    base_characters = list(CHARACTERS_BASE.keys())
    custom_charaters = load_character_names_from_dump()

    return base_characters + custom_charaters


def get_character_description(name):
    return CHARACTERS_BASE.get(
        name, {"style": "unknown", "description": "No info found."}
    )


def create_character(user_input: str):
    character_json = LLAMA_DEBATOR.create_character_from_description(
        user_input=user_input
    )
    return character_json


def load_character_names_from_dump():
    characters = []

    for file in CHARACTER_DUMP_PATH.glob("*.json"):
        try:
            with open(file, "r") as f:
                character = json.load(f)
                characters.append(character["name"])
        except Exception as e:
            print(f"Failed to load {file.name}: {e}")

    return characters
