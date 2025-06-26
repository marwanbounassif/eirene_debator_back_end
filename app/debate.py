import os
from dotenv import load_dotenv
from app.characters import get_character_description
from huggingface_hub import InferenceClient

load_dotenv()
HF_API_KEY = os.getenv("HF_API_KEY")
HF_MODEL = os.getenv("MODEL_ID")

headers = {"Authorization": f"Bearer {HF_API_KEY}"}


def run_debate(prompt: str, char_a: str, char_b: str) -> str:
    a = get_character_description(char_a)
    b = get_character_description(char_b)

    a_response = _call_meta_llama(a, prompt)
    b_response = _call_meta_llama(b, prompt)

    output = f"🎙️ Debate on: {prompt}\n\n"
    output += f"{char_a} ({a['style']}):\n{a_response}\n\n"
    output += f"{char_b} ({b['style']}):\n{b_response}\n"

    return output


def _call_meta_llama(char_description: str, prompt: str):
    client = InferenceClient(
        provider="novita",
        api_key=HF_API_KEY,
    )

    completion = client.chat.completions.create(
        model=HF_MODEL,
        messages=[{"role": "user", "content": prompt, "system": char_description}],
    )

    try:
        return completion.choices[0].message.content
    except Exception as e:
        print("Unexpected response format:", e)
        return "[Error parsing model output]"
