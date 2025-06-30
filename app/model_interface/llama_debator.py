from huggingface_hub import InferenceClient
from app.model_interface.debator_interface import DebatorInterface
import json
import os
from dotenv import load_dotenv
from pathlib import Path
import hashlib
import logging
from typing import List, Optional


BASE_DIR = Path(__file__).resolve().parent.parent
LOG_PATH = BASE_DIR / "logs" / "app.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH),
        logging.StreamHandler(),  # prints to console
    ],
)
logger = logging.getLogger(__name__)

load_dotenv()

MODEL_CONFIG_PATH = Path(os.getenv("MODEL_CONFIG_PATH"))
MODEL_CONFIG = json.loads(MODEL_CONFIG_PATH.read_text())

CHARACTER_DUMP_PATH = Path(os.getenv("CHARACTER_DUMP_PATH"))


DEBATE_CONFIG_PATH = Path(os.getenv("DEBATE_CONFIG_PATH"))
DEBATE_CONFIG = json.loads(DEBATE_CONFIG_PATH.read_text())


class LlamaDebator(DebatorInterface):
    def __init__(self, model_name: str, api_key: str):
        self._model_name = model_name
        self._api_key = api_key

    def debate(self, char_description: str, prompt: List[str]):
        client = InferenceClient(
            provider="novita",
            api_key=self._api_key,
        )

        if isinstance(prompt, str):
            prompt = [prompt]

        logger.info(prompt)

        prompt = "\n".join(prompt)

        completion = client.chat.completions.create(
            model=self._model_name,
            messages=[
                {"role": "user", "content": prompt},
                {"role": "system", "content": char_description},
            ],
        )

        try:
            return completion.choices[0].message.content
        except Exception as e:
            print("Unexpected response format:", e)
            return "[Error parsing model output]"

    def format_character_for_prompt(character: dict) -> str:
        """
        Format a character dictionary into a context string for prompting the Llama Model.

        Expected keys:
            - name
            - debate_style
            - personality_description
            - extra_details (optional)

        Returns a nicely formatted string.

        TODO: MAKE THIS CONFIGURABLE
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

        prompt_context += DEBATE_CONFIG.get("context_response_prompt")

        return prompt_context

    def create_character_from_description(self, user_input: dict) -> json:
        character_creation_prompt = MODEL_CONFIG[self._model_name][
            "character_creation_prompt"
        ]
        character_creation_prompt = "\n".join(character_creation_prompt)

        client = InferenceClient(
            provider="novita",
            api_key=self._api_key,
        )

        completion = client.chat.completions.create(
            model=self._model_name,
            messages=[
                {"role": "user", "content": user_input},
                {"role": "system", "content": character_creation_prompt},
            ],
        )

        try:
            response_str = completion.choices[0].message.content
            cleaned = response_str.strip().lstrip("`json").strip("`")
            character_data = json.loads(cleaned)
            hash_input = json.dumps(character_data, sort_keys=True).encode()
            hashed_id = hashlib.sha256(hash_input).hexdigest()[:12]
            output_path = CHARACTER_DUMP_PATH / f"{hashed_id}.json"
            with output_path.open("w") as f:
                json.dump(character_data, f, indent=2)
            return character_data
        except Exception as e:
            print("Unexpected response format:", e)
            return {"error": "Failed to parse or save character"}
