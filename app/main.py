from fastapi import FastAPI, Form
from app.debate import start_turn_based_debate
from app.characters import get_character_names, create_character
from app.string_processor import preprocess_input_string

app = FastAPI()


@app.get("/")
def health_check():
    return {"status": "Eirene is running."}


@app.get("/characters/")
def list_characters():
    return {"characters": get_character_names()}


@app.post("/debate/")
def debate_endpoint(
    prompt: str = Form(...),
    char_a: str = Form(...),
    char_b: str = Form(...),
    debate_rounds_count: int = Form(...),
):
    response = start_turn_based_debate(prompt, char_a, char_b, debate_rounds_count)
    return {"prompt": prompt, "debate": response}


@app.post("/characterCreate/")
def character_create_endpoint(user_input: str = Form(...)):
    user_input = preprocess_input_string(user_input)
    response = create_character(user_input)
    return {"character": response}
