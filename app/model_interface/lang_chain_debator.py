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
    
    def intialize_agent(self, user_input: str):
        system_prompt = self.create_character_from_description(user_input)
        agent = create_agent(
            model=self._model_name,
            tools=[],
            system_prompt= system_prompt
        )
        return agent
