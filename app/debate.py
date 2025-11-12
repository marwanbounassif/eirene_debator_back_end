import os
from pathlib import Path
import json
from dotenv import load_dotenv
from app.characters import get_character_description
from app.model_interface.lang_graph_debator import LangGraphDebator
from typing import List
from app.utils.logging import setup_logging


load_dotenv()
HF_API_KEY = os.getenv("HF_API_KEY")
HF_MODEL = os.getenv("MODEL_ID")
LANG_GRAPH_DEBATOR = LangGraphDebator(model_name=HF_MODEL, api_key=HF_API_KEY)


DEBATE_CONFIG_PATH = Path(os.getenv("DEBATE_CONFIG_PATH"))
DEBATE_CONFIG = json.loads(DEBATE_CONFIG_PATH.read_text())


# Setup logging
logger = setup_logging(__name__)


def start_turn_based_debate(
    prompt: str, char_a: str, char_b: str, debate_rounds_count: int = None
) -> str:
    a = get_character_description(char_a)
    b = get_character_description(char_b)

    a_context = LangGraphDebator.format_character_for_prompt(a)
    b_context = LangGraphDebator.format_character_for_prompt(b)

    if not debate_rounds_count:
        debate_rounds_count = DEBATE_CONFIG.get("debate_rounds_count", 5)

    history = _make_opening_statements(a_context, b_context, prompt)
    debate_output = _run_turn_based_debate(
        a_context, b_context, history, debate_rounds_count - 1
    )

    return debate_output


def _make_opening_statements(a_context, b_context, prompt):

    opening_statement_prompt = DEBATE_CONFIG.get("opening_statement_prompt") + prompt
    a_response = LANG_GRAPH_DEBATOR.debate(a_context, opening_statement_prompt)
    b_response = LANG_GRAPH_DEBATOR.debate(b_context, opening_statement_prompt)
    return [a_response, b_response]


def _run_turn_based_debate(
    a_context, b_context, history: List[str], remaining_turns: int
):
    if remaining_turns == 1:
        debate_output = _end_debate(a_context, b_context, history)
        return debate_output

    else:
        history = _run_debate(a_context, b_context, history)
        return _run_turn_based_debate(
            a_context, b_context, history, remaining_turns - 1
        )


def _end_debate(a_context, b_context, history: List[str]):
    closing_statement_prompt = DEBATE_CONFIG.get("closing_statement_prompt")
    a_response = LANG_GRAPH_DEBATOR.debate(a_context, history + [closing_statement_prompt])
    b_response = LANG_GRAPH_DEBATOR.debate(b_context, history + [closing_statement_prompt])

    return history + [a_response, b_response]


def _run_debate(a_context, b_context, history: List[str]) -> str:
    a_response = LANG_GRAPH_DEBATOR.debate(a_context, history)
    b_response = LANG_GRAPH_DEBATOR.debate(b_context, history + [a_response])

    history = history + [a_response, b_response]
    return history
