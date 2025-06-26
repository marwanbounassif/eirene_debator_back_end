from fastapi import FastAPI, Form
from app.debate import run_debate
from app.characters import get_character_names, get_character_description

app = FastAPI()


@app.get("/")
def health_check():
    return {"status": "Eirene is running."}


@app.get("/characters/")
def list_characters():
    return {"characters": get_character_names()}


@app.post("/debate/")
def debate_endpoint(
    prompt: str = Form(...), char_a: str = Form(...), char_b: str = Form(...)
):
    response = run_debate(prompt, char_a, char_b)
    return {"prompt": prompt, "debate": response}
