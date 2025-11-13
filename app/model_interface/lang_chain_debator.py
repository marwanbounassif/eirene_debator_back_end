from app.model_interface.debator_interface import DebatorInterface
from app.utils.logging import setup_logging

import os
from typing import List
import json
from pathlib import Path
import hashlib

from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, SystemMessage
from langchain.agents import create_agent

logger = setup_logging(__name__)

CHARACTER_DUMP_PATH = Path(os.getenv("CHARACTER_DUMP_PATH"))

DEBATE_CONFIG_PATH = Path(os.getenv("DEBATE_CONFIG_PATH"))
DEBATE_CONFIG = json.loads(DEBATE_CONFIG_PATH.read_text())

class LangChainDebator(DebatorInterface):
    def __init__(self, model_name: str, api_key: str):
        self._model_name = model_name
        self._api_key = api_key
        self.llm = ChatOpenAI(model_name=self._model_name, openai_api_key=self._api_key, temperature=0)

    def create_character_from_description(self, user_input: str) -> dict:
        character_creation_prompt = DEBATE_CONFIG.get("interpreted_character_creation_prompt")
        character_creation_prompt = "\n".join(character_creation_prompt)

        try:
            # Call the LLM with the system prompt and user input
            response = self.llm.invoke([SystemMessage(character_creation_prompt),
                                 AIMessage(user_input)])

            # Parse the response
            response_content = response.content
            logger.info("LLM response: %s", response_content)
            hashed_id = hashlib.sha256(response_content.encode()).hexdigest()[:12]
            character_data = {hashed_id: response_content}

            output_path = CHARACTER_DUMP_PATH / f"{hashed_id}.json"
            with output_path.open("w") as f:
                json.dump(character_data, f, indent=2)

            return character_data
        except json.JSONDecodeError as e:
            logger.error("JSON decoding error: %s", e)
            logger.info("Failed response content: %s", response_content)
            return {"error": f"Failed to parse character JSON, with response: {response_content}"}
        except Exception as e:
            logger.error("Unexpected error: %s", e)
            return {"error": "An unexpected error occurred while creating the character"}
        
    def debate(self, char_description: str, prompt: List[str]):
        return "Not implemented yet."
    
    def format_character_for_prompt(self, character: dict) -> str:
        return "Not implemented yet."
    
    def intialize_agent(self, character_id: str):
        """Initialize an agent from a saved character file.

        This function will:
        - verify the character file exists
        - parse the JSON safely
        - extract the system prompt for the given character_id (with a fallback)
        - log useful errors and return None on failure
        """
        logger.info("Initializing agent for character ID: %s", character_id)

        try:
            file_path = CHARACTER_DUMP_PATH.joinpath(f"{character_id}.json")

            if not file_path.exists():
                logger.error("Character file not found: %s", file_path)
                return None

            # Read and parse JSON
            with file_path.open("r") as f:
                data = json.load(f)

            # If file is a dict keyed by id, fetch by character_id
            if isinstance(data, dict) and character_id in data:
                system_prompt = data[character_id]
            else:   
                system_prompt = data
                
            agent = create_agent(
                model=self._model_name,
                tools=[],
                system_prompt=system_prompt,
            )

            logger.info("Agent initialized for character ID: %s", character_id)
            return agent

        except json.JSONDecodeError as e:
            logger.error("Failed to parse JSON from %s: %s", file_path, e)
            return None
        except Exception:
            logger.exception("Unexpected error initializing agent for %s", character_id)
            return None
