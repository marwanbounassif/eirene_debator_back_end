from app.characters import get_character_description


def run_debate(prompt: str, char_a: str, char_b: str) -> str:
    a = get_character_description(char_a)
    b = get_character_description(char_b)

    # Simulated basic output (placeholder)
    output = f"🎙️ Debate on: {prompt}\n\n"
    output += f"{char_a} ({a['style']}):\n"
    output += f"“I believe {prompt.lower()} because... [custom logic here]”\n\n"

    output += f"{char_b} ({b['style']}):\n"
    output += f"“On the contrary, {prompt.lower()} is flawed because... [custom logic here]”\n"

    return output
