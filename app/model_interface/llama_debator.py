from huggingface_hub import InferenceClient
from app.model_interface.debator_interface import DebatorInterface


class LlamaDebator(DebatorInterface):
    def __init__(self, model_name: str, api_key: str):
        self._model_name = model_name
        self._api_key = api_key

    def debate(self, char_description: str, prompt: str):
        client = InferenceClient(
            provider="novita",
            api_key=self._api_key,
        )

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

        prompt_context += "Respond accordingly."

        return prompt_context
