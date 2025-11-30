from app.model_interface.debator_interface import DebatorInterface
from app.utils.logging import setup_logging

import os
from typing import List, Dict, Optional, Union
import json
from pathlib import Path
import hashlib

from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage, BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser

logger = setup_logging(__name__)

CHARACTER_DUMP_PATH = Path(os.getenv("CHARACTER_DUMP_PATH"))
DEBATE_CONFIG_PATH = Path(os.getenv("DEBATE_CONFIG_PATH"))
DEBATE_CONFIG = json.loads(DEBATE_CONFIG_PATH.read_text())


class SimpleMemory:
    """Simple memory implementation to replace ConversationBufferMemory"""
    def __init__(self):
        self.messages = []
    
    @property
    def chat_memory(self):
        return self

    def add_user_message(self, message):
        if isinstance(message, str):
            self.messages.append(HumanMessage(content=message))
        elif isinstance(message, HumanMessage):
            self.messages.append(message)

    def add_ai_message(self, message: str):
        if isinstance(message, str):
            self.messages.append(AIMessage(content=message))
        else:
            self.messages.append(message)
    
    def clear(self):
        self.messages = []


class LangChainDebator(DebatorInterface):
    """LangChain-based debator implementation with improved debate capabilities"""
    
    def __init__(self, model_name: str, api_key: str, temperature: float = 0.7):
        self._model_name = model_name
        self._api_key = api_key
        self._temperature = temperature
        self.llm = ChatOpenAI(
            model_name=self._model_name, 
            openai_api_key=self._api_key, 
            temperature=self._temperature
        )
        # Store active agents for reuse
        self._active_agents: Dict[str, Dict] = {}

    def create_character_from_description(self, user_input: str, save_response: bool = True) -> dict:
        """Create a character from user description and save to file"""
        character_creation_prompt = DEBATE_CONFIG.get("interpreted_character_creation_prompt")
        character_creation_prompt = "\n".join(character_creation_prompt)

        try:
            # Call the LLM with the system prompt and user input
            response = self.llm.invoke([
                SystemMessage(content=character_creation_prompt),
                HumanMessage(content=user_input)
            ])

            # Parse the response
            response_content = response.content
            logger.info("LLM response: %s", response_content)
            hashed_id = hashlib.sha256(response_content.encode()).hexdigest()[:12]
            character_data = {"character_id": hashed_id, "system_prompt":  response_content}

            if save_response:
                # Save character to file
                output_path = CHARACTER_DUMP_PATH / f"{hashed_id}.json"
                CHARACTER_DUMP_PATH.mkdir(parents=True, exist_ok=True)
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
    
    def initialize_agent(self, character_context: str, character_id: Optional[str] = None) -> Dict:
        """Initialize an agent with the given character context
        
        Args:
            character_context: The character's system prompt/context
            character_id: Optional character ID for caching
            
        Returns:
            Dictionary containing the agent components
        """
        logger.info("Initializing agent with context")
        
        # Check if we already have this agent cached
        if character_id and character_id in self._active_agents:
            logger.info(f"Using cached agent for character ID: {character_id}")
            return self._active_agents[character_id]
        
        try:
            # Create a chat prompt template with system message and history
            prompt = ChatPromptTemplate.from_messages([
                ("system", character_context),
                MessagesPlaceholder(variable_name="history"),
                ("human", "{input}")
            ])
            
            # Create the chain
            chain = prompt | self.llm | StrOutputParser()
            
            # Create simple memory
            memory = SimpleMemory()
            
            agent_dict = {
                "chain": chain,
                "memory": memory,
                "context": character_context,
                "character_id": character_id
            }
            
            # Cache the agent if it has an ID
            if character_id:
                self._active_agents[character_id] = agent_dict
            
            logger.info(f"Agent initialized successfully")
            return agent_dict
            
        except Exception as e:
            logger.exception(f"Unexpected error initializing agent: {e}")
            return None
        
    def initialize_agent_from_file(self, character_id: str) -> Optional[Dict]:
        """Initialize an agent from a saved character file
        
        Args:
            character_id: The character ID to load
            
        Returns:
            Dictionary containing agent components or None on failure
        """
        logger.info("Initializing agent from file for character ID: %s", character_id)

        try:
            file_path = CHARACTER_DUMP_PATH / f"{character_id}.json"

            if not file_path.exists():
                logger.error("Character file not found: %s", file_path)
                return None

            # Read and parse JSON
            with file_path.open("r") as f:
                data = json.load(f)

            # Extract character context
            if isinstance(data, dict) and character_id in data:
                character_context = data[character_id]
            else:   
                character_context = data

            # Initialize the agent with the loaded context
            return self.initialize_agent(character_context, character_id)

        except json.JSONDecodeError as e:
            logger.error("Failed to parse JSON from %s: %s", file_path, e)
            return None
        except Exception:
            logger.exception("Unexpected error initializing agent from file for %s", character_id)
            return None
    
    def debate(self, character_context: Union[str, Dict], conversation_history: Union[str, List[str]]) -> str:
        """Generate a debate response for the character
        
        Args:
            character_context: Either a string context or an agent dictionary
            conversation_history: The conversation history (string or list of strings)
            
        Returns:
            The character's response
        """
        try:
            # Handle different input types for character_context
            if isinstance(character_context, dict):
                # Already an initialized agent
                agent = character_context
            elif isinstance(character_context, str):
                # Need to initialize an agent
                agent = self.initialize_agent(character_context)
                if not agent:
                    raise ValueError("Failed to initialize agent")
            else:
                raise ValueError(f"Invalid character_context type: {type(character_context)}")
            
            # Convert conversation history to string if it's a list
            if isinstance(conversation_history, list):
                # Format the conversation history
                formatted_history = self._format_conversation_history(conversation_history)
            else:
                formatted_history = conversation_history
            
            # Generate response using the chain
            response = agent["chain"].invoke({
                "input": formatted_history,
                "history": agent["memory"].chat_memory.messages
            })
            
            # Update memory with the exchange
            agent["memory"].chat_memory.add_user_message(formatted_history)
            agent["memory"].chat_memory.add_ai_message(response)
            
            logger.info(f"Generated debate response: {response[:100]}...")
            return response
            
        except Exception as e:
            logger.error(f"Error generating debate response: {e}")
            return f"[Error generating response: {str(e)}]"
    
    def _format_conversation_history(self, history: List[str]) -> str:
        """Format conversation history list into a readable string
        
        Args:
            history: List of conversation turns
            
        Returns:
            Formatted conversation string
        """
        if not history:
            return ""
        
        formatted_parts = []
        for i, turn in enumerate(history):
            # Alternate between speakers for context
            speaker = "Opponent" if i % 2 == 0 else "You"
            formatted_parts.append(f"{speaker}: {turn}")
        
        return "\n\n".join(formatted_parts)
    
    @staticmethod
    def format_character_for_prompt(character_description: dict) -> str:
        """Format a character description for use as a prompt
        
        Args:
            character_description: Dictionary containing character details
            
        Returns:
            Formatted string for use as system prompt
        """
        if isinstance(character_description, dict):
            character_description = character_description.get("system_prompt", "")
            return character_description
        elif isinstance(character_description, str):
            return character_description
        else:
            return str(character_description)
    
    def reset_agent_memory(self, character_id: str):
        """Reset the conversation memory for a specific agent
        
        Args:
            character_id: The character ID whose memory to reset
        """
        if character_id in self._active_agents:
            self._active_agents[character_id]["memory"].clear()
            logger.info(f"Reset memory for character {character_id}")
        else:
            logger.warning(f"No active agent found for character {character_id}")
    
    def get_agent_history(self, character_id: str) -> List[BaseMessage]:
        """Get the conversation history for a specific agent
        
        Args:
            character_id: The character ID
            
        Returns:
            List of messages in the agent's history
        """
        if character_id in self._active_agents:
            return self._active_agents[character_id]["memory"].chat_memory.messages
        return []
