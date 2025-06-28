import os
from dotenv import load_dotenv
from app.characters import get_character_description
from app.model_interface.llama_debator import LlamaDebator

load_dotenv()
HF_API_KEY = os.getenv("HF_API_KEY")
HF_MODEL = os.getenv("MODEL_ID")
LLAMA_DEBATOR = LlamaDebator(model_name=HF_MODEL, api_key=HF_API_KEY)


def run_debate(prompt: str, char_a: str, char_b: str) -> str:
    a = get_character_description(char_a)
    b = get_character_description(char_b)

    a_context = LlamaDebator.format_character_for_prompt(a)
    b_context = LlamaDebator.format_character_for_prompt(b)

    a_response = LLAMA_DEBATOR.debate(a_context, prompt)
    b_response = LLAMA_DEBATOR.debate(b_context, prompt)

    output = f"🎙️ Debate on: {prompt}\n\n"
    output += f"{char_a} : {a_response}\n\n"
    output += f"{char_b} : {b_response}\n"

    return output
