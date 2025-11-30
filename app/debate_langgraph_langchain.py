import os
from pathlib import Path
import json
from typing import List, TypedDict, Annotated, Literal, Optional, Dict
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from app.characters import get_character_description
from app.utils.logging import setup_logging

# Import the LangChain debator instead of Llama debator
from app.model_interface.langchain_debator import LangChainDebator

# Load environment variables and setup
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # Changed from HF_API_KEY
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4")  # Changed from MODEL_ID

# Initialize the LangChain debator
DEBATOR = LangChainDebator(model_name=MODEL_NAME, api_key=OPENAI_API_KEY)

DEBATE_CONFIG_PATH = Path(os.getenv("DEBATE_CONFIG_PATH"))
DEBATE_CONFIG = json.loads(DEBATE_CONFIG_PATH.read_text())

# Setup logging
logger = setup_logging(__name__)


# Define the state structure for the debate
class DebateState(TypedDict):
    """State structure for managing the debate flow"""
    prompt: str
    character_a: str
    character_b: str
    a_context: str
    b_context: str
    a_agent: Optional[Dict]  # Store the actual agent for character A
    b_agent: Optional[Dict]  # Store the actual agent for character B
    history: Annotated[List[str], add_messages]
    current_round: int
    max_rounds: int
    debate_phase: Literal["opening", "debate", "closing", "complete"]
    use_memory: bool  # Whether to maintain memory across turns


# Node functions for the debate graph
def initialize_debate(state: DebateState) -> DebateState:
    """Initialize the debate with character contexts and agents"""
    logger.info(f"Initializing debate between {state['character_a']} and {state['character_b']}")
    
    # Get character descriptions
    a_desc = get_character_description(state['character_a'])
    b_desc = get_character_description(state['character_b'])
    
    # Format characters for prompts using the LangChain debator's method
    a_context = LangChainDebator.format_character_for_prompt(a_desc)
    b_context = LangChainDebator.format_character_for_prompt(b_desc)
    
    # Initialize agents for both characters
    a_agent = DEBATOR.initialize_agent(a_context, character_id=state['character_a'])
    b_agent = DEBATOR.initialize_agent(b_context, character_id=state['character_b'])
    
    # Set max rounds if not specified
    max_rounds = state.get('max_rounds') or DEBATE_CONFIG.get("debate_rounds_count", 5)
    
    # Use memory by default
    use_memory = state.get('use_memory', True)
    
    return {
        **state,
        'a_context': a_context,
        'b_context': b_context,
        'a_agent': a_agent,
        'b_agent': b_agent,
        'current_round': 0,
        'max_rounds': max_rounds,
        'history': [],
        'debate_phase': 'opening',
        'use_memory': use_memory
    }


def character_a_opening(state: DebateState) -> DebateState:
    """Character A makes their opening statement"""
    logger.info(f"Character A ({state['character_a']}) making opening statement")
    
    opening_prompt = DEBATE_CONFIG.get("opening_statement_prompt") + state['prompt']
    
    # Use the agent or context depending on configuration
    if state['use_memory'] and state['a_agent']:
        a_response = DEBATOR.debate(state['a_agent'], opening_prompt)
    else:
        a_response = DEBATOR.debate(state['a_context'], opening_prompt)
    
    return {
        **state,
        'history': state['history'] + [a_response]
    }


def character_b_opening(state: DebateState) -> DebateState:
    """Character B makes their opening statement"""
    logger.info(f"Character B ({state['character_b']}) making opening statement")
    
    opening_prompt = DEBATE_CONFIG.get("opening_statement_prompt") + state['prompt']
    
    # Use the agent or context depending on configuration
    if state['use_memory'] and state['b_agent']:
        b_response = DEBATOR.debate(state['b_agent'], opening_prompt)
    else:
        b_response = DEBATOR.debate(state['b_context'], opening_prompt)
    
    return {
        **state,
        'history': state['history'] + [b_response],
        'debate_phase': 'debate',
        'current_round': 1
    }


def character_a_debate(state: DebateState) -> DebateState:
    """Character A responds in the debate"""
    logger.info(f"Character A ({state['character_a']}) responding - Round {state['current_round']}")
    
    # Prepare the conversation history for the debate
    if state['use_memory'] and state['a_agent']:
        # If using memory, just pass the latest opponent response
        a_response = DEBATOR.debate(state['a_agent'], state['history'][-1])
    else:
        # Pass full history if not using memory
        a_response = DEBATOR.debate(state['a_context'], state['history'])
    
    return {
        **state,
        'history': state['history'] + [a_response]
    }


def character_b_debate(state: DebateState) -> DebateState:
    """Character B responds in the debate"""
    logger.info(f"Character B ({state['character_b']}) responding - Round {state['current_round']}")
    
    # Prepare the conversation history for the debate
    if state['use_memory'] and state['b_agent']:
        # If using memory, just pass the latest opponent response
        b_response = DEBATOR.debate(state['b_agent'], state['history'][-1])
    else:
        # Pass full history if not using memory
        b_response = DEBATOR.debate(state['b_context'], state['history'])
    
    # Increment round counter after both have spoken
    new_round = state['current_round'] + 1
    
    # Check if we should transition to closing statements
    debate_phase = 'closing' if new_round >= state['max_rounds'] - 1 else 'debate'
    
    return {
        **state,
        'history': state['history'] + [b_response],
        'current_round': new_round,
        'debate_phase': debate_phase
    }


def character_a_closing(state: DebateState) -> DebateState:
    """Character A makes their closing statement"""
    logger.info(f"Character A ({state['character_a']}) making closing statement")
    
    closing_prompt = DEBATE_CONFIG.get("closing_statement_prompt")
    
    if state['use_memory'] and state['a_agent']:
        # With memory, agent already has context
        a_response = DEBATOR.debate(state['a_agent'], closing_prompt)
    else:
        # Without memory, provide full history
        a_response = DEBATOR.debate(
            state['a_context'], 
            state['history'] + [closing_prompt]
        )
    
    return {
        **state,
        'history': state['history'] + [a_response]
    }


def character_b_closing(state: DebateState) -> DebateState:
    """Character B makes their closing statement"""
    logger.info(f"Character B ({state['character_b']}) making closing statement")
    
    closing_prompt = DEBATE_CONFIG.get("closing_statement_prompt")
    
    if state['use_memory'] and state['b_agent']:
        # With memory, agent already has context
        b_response = DEBATOR.debate(state['b_agent'], closing_prompt)
    else:
        # Without memory, provide full history
        b_response = DEBATOR.debate(
            state['b_context'], 
            state['history'] + [closing_prompt]
        )
    
    # Clean up agents if they were using memory
    if state['use_memory']:
        DEBATOR.reset_agent_memory(state['character_a'])
        DEBATOR.reset_agent_memory(state['character_b'])
    
    return {
        **state,
        'history': state['history'] + [b_response],
        'debate_phase': 'complete'
    }


def should_continue_debate(state: DebateState) -> Literal["character_a_debate", "character_a_closing", END]:
    """Determine the next step in the debate flow"""
    if state['debate_phase'] == 'complete':
        return END
    elif state['debate_phase'] == 'closing':
        return "character_a_closing"
    else:
        return "character_a_debate"


# Build the debate graph
def create_debate_graph():
    """Create and compile the LangGraph debate orchestration graph"""
    
    # Initialize the graph with our state structure
    graph = StateGraph(DebateState)
    
    # Add nodes for each agent/action
    graph.add_node("initialize", initialize_debate)
    graph.add_node("character_a_opening", character_a_opening)
    graph.add_node("character_b_opening", character_b_opening)
    graph.add_node("character_a_debate", character_a_debate)
    graph.add_node("character_b_debate", character_b_debate)
    graph.add_node("character_a_closing", character_a_closing)
    graph.add_node("character_b_closing", character_b_closing)
    
    # Define the flow edges
    graph.set_entry_point("initialize")
    
    # Opening statements flow
    graph.add_edge("initialize", "character_a_opening")
    graph.add_edge("character_a_opening", "character_b_opening")
    
    # Main debate flow with conditional routing
    graph.add_conditional_edges(
        "character_b_opening",
        should_continue_debate,
        {
            "character_a_debate": "character_a_debate",
            "character_a_closing": "character_a_closing",
            END: END
        }
    )
    
    # Debate rounds
    graph.add_edge("character_a_debate", "character_b_debate")
    graph.add_conditional_edges(
        "character_b_debate",
        should_continue_debate,
        {
            "character_a_debate": "character_a_debate",
            "character_a_closing": "character_a_closing",
            END: END
        }
    )
    
    # Closing statements flow
    graph.add_edge("character_a_closing", "character_b_closing")
    graph.add_edge("character_b_closing", END)
    
    # Compile the graph
    return graph.compile()


# Main function to start the debate
def start_turn_based_debate(
    prompt: str, 
    char_a: str, 
    char_b: str, 
    debate_rounds_count: int = None,
    use_memory: bool = True
) -> str:
    """
    Start a turn-based debate using LangGraph orchestration with LangChain agents
    
    Args:
        prompt: The debate topic/prompt
        char_a: Name/ID of character A
        char_b: Name/ID of character B
        debate_rounds_count: Number of debate rounds (optional)
        use_memory: Whether to maintain conversation memory across turns
    
    Returns:
        The complete debate history as a formatted string
    """
    logger.info(f"Starting debate: {prompt}")
    logger.info(f"Memory enabled: {use_memory}")
    
    # Create the debate graph
    debate_graph = create_debate_graph()
    
    # Initialize the state
    initial_state = {
        'prompt': prompt,
        'character_a': char_a,
        'character_b': char_b,
        'max_rounds': debate_rounds_count,
        'history': [],
        'current_round': 0,
        'debate_phase': 'opening',
        'use_memory': use_memory,
        'a_agent': None,
        'b_agent': None
    }
    
    # Run the debate
    final_state = debate_graph.invoke(initial_state)
    
    # Format and return the debate output
    debate_output = format_debate_output(final_state)
    
    logger.info("Debate completed successfully")
    return debate_output


def format_debate_output(state: DebateState) -> str:
    """
    Format the debate history for output
    
    Args:
        state: The final debate state
    
    Returns:
        Formatted debate transcript
    """
    output_lines = [
        f"DEBATE: {state['prompt']}",
        f"Participants: {state['character_a']} vs {state['character_b']}",
        f"Memory Mode: {'Enabled' if state['use_memory'] else 'Disabled'}",
        "=" * 80,
        ""
    ]
    
    history = state['history']
    round_num = 0
    
    # Format opening statements
    if len(history) >= 2:
        output_lines.append("OPENING STATEMENTS:")
        output_lines.append(f"\n{state['character_a']}: {history[0]}")
        output_lines.append(f"\n{state['character_b']}: {history[1]}")
        output_lines.append("\n" + "=" * 80 + "\n")
        
        # Format debate rounds
        if len(history) > 2:
            debate_start = 2
            closing_start = len(history) - 2 if state['debate_phase'] == 'complete' else len(history)
            
            if closing_start > debate_start:
                output_lines.append("DEBATE ROUNDS:")
                for i in range(debate_start, closing_start, 2):
                    round_num += 1
                    output_lines.append(f"\nRound {round_num}:")
                    if i < len(history):
                        output_lines.append(f"{state['character_a']}: {history[i]}")
                    if i + 1 < len(history):
                        output_lines.append(f"{state['character_b']}: {history[i + 1]}")
                
                output_lines.append("\n" + "=" * 80 + "\n")
            
            # Format closing statements
            if state['debate_phase'] == 'complete' and len(history) >= 2:
                output_lines.append("CLOSING STATEMENTS:")
                output_lines.append(f"\n{state['character_a']}: {history[-2]}")
                output_lines.append(f"\n{state['character_b']}: {history[-1]}")
    
    return "\n".join(output_lines)


# Function to create a character and start a debate
def create_character_and_debate(
    character_description: str,
    opponent_character_id: str,
    debate_topic: str,
    rounds: int = 3
) -> str:
    """
    Create a new character and immediately use it in a debate
    
    Args:
        character_description: Description for creating a new character
        opponent_character_id: ID of the existing opponent character
        debate_topic: The topic to debate
        rounds: Number of debate rounds
    
    Returns:
        The debate output
    """
    # Create the new character
    new_character = DEBATOR.create_character_from_description(character_description)
    
    if "error" in new_character:
        return f"Failed to create character: {new_character['error']}"
    
    # Get the new character's ID
    new_char_id = list(new_character.keys())[0]
    
    # Start the debate
    return start_turn_based_debate(
        prompt=debate_topic,
        char_a=new_char_id,
        char_b=opponent_character_id,
        debate_rounds_count=rounds,
        use_memory=True
    )


# Optional: Async version for better performance
async def start_turn_based_debate_async(
    prompt: str, 
    char_a: str, 
    char_b: str, 
    debate_rounds_count: int = None,
    use_memory: bool = True
) -> str:
    """
    Async version of the debate orchestration for better performance
    """
    logger.info(f"Starting async debate: {prompt}")
    
    # Create the debate graph
    debate_graph = create_debate_graph()
    
    # Initialize the state
    initial_state = {
        'prompt': prompt,
        'character_a': char_a,
        'character_b': char_b,
        'max_rounds': debate_rounds_count,
        'history': [],
        'current_round': 0,
        'debate_phase': 'opening',
        'use_memory': use_memory,
        'a_agent': None,
        'b_agent': None
    }
    
    # Run the debate asynchronously
    final_state = await debate_graph.ainvoke(initial_state)
    
    # Format and return the debate output
    debate_output = format_debate_output(final_state)
    
    logger.info("Async debate completed successfully")
    return debate_output


if __name__ == "__main__":
    # Example usage
    
    # Example 1: Simple debate with existing characters
    result = start_turn_based_debate(
        prompt="Should AI be regulated?",
        char_a="tech_optimist",
        char_b="ethics_advocate",
        debate_rounds_count=3,
        use_memory=True  # Enable conversation memory
    )
    print(result)
    
    # Example 2: Create a new character and debate
    # new_debate = create_character_and_debate(
    #     character_description="A cautious AI safety researcher who believes in careful, measured progress",
    #     opponent_character_id="tech_optimist",
    #     debate_topic="Should we pause AI development for safety assessments?",
    #     rounds=4
    # )
    # print(new_debate)
