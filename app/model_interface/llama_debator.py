from huggingface_hub import InferenceClient
from app.model_interface.debator_interface import DebatorInterface
import json
import os
from dotenv import load_dotenv
from pathlib import Path
import hashlib
from typing import List
from app.utils.logging import setup_logging


# Setup logging
logger = setup_logging(__name__)

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
            logger.error("Unexpected response format: %s", e)
            return "[Error parsing model output]"

    def format_character_for_prompt(character: dict) -> str:
        """
        Format a character dictionary into a context string for prompting the Llama Model.

        Expected keys:
            - name
            - debate_style
            - personality_description
            - extra_details

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
        character_creation_prompt = DEBATE_CONFIG.get("interpreted_character_creation_prompt")
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
            logger.info("Raw response from model: %s", response_str)

            # Clean up the response string
            cleaned = response_str.strip().lstrip("`json").strip("`")

            # Attempt to parse the JSON
            character_data = json.loads(cleaned)

            # Generate a unique hash ID for the character
            hash_input = json.dumps(character_data, sort_keys=True).encode()
            hashed_id = hashlib.sha256(hash_input).hexdigest()[:12]

            # Save the character data to a file
            output_path = CHARACTER_DUMP_PATH / f"{hashed_id}.json"
            with output_path.open("w") as f:
                json.dump(character_data, f, indent=2)

            return character_data
        except json.JSONDecodeError as e:
            logger.error("JSON decoding error: %s", e)
            logger.info("Failed response content: %s", response_str)
            return {"error": f"Failed to parse character JSON, with response: {response_str}"}
        except Exception as e:
            logger.error("Unexpected error: %s", e)
            return {"error": "An unexpected error occurred while creating the character"}
