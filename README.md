# Eirene Debator Back End

Small FastAPI backend for running turn-based debates between LLM-powered characters. This repository is intended as a learning project to explore building, running, and deploying a generative AI (GenAI) application.

## What this project contains
- A simple FastAPI app (`app/main.py`) exposing endpoints to list characters, create characters, and run a debate.
- Debate orchestration in `app/debate.py`.
- Character utilities in `app/characters.py`.
- Model adapter interface in `app/model_interface/` and an example adapter `llama_debator.py` using the Hugging Face Inference client.
- Configs in `configs/` (model + debate prompts).

## Running with Docker (recommended)

1. Copy the example env file and fill values:
```bash
cp .env.example .env
# Edit .env and set HF_API_KEY and MODEL_ID
```

2. Build and start the containers:
```bash
docker compose up --build
```

3. Open the API docs at: http://localhost:8000/docs

The app code will hot-reload when you make changes.

## Running locally (alternative)

1. Create a Python virtual environment and activate it:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Copy and configure the env file:
```bash
cp .env.example .env
# Edit .env and set HF_API_KEY, MODEL_ID and paths
```

4. Ensure required directories exist:
```bash
mkdir -p ./characters ./app/logs
```

5. Run the app with uvicorn:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

6. Open the API docs at: http://localhost:8000/docs

## Important environment variables
Use `.env` (not committed) to store secrets and local paths. See `.env.example` for required keys. Key variables used by the app:

- `HF_API_KEY` - Hugging Face (or other provider) API key used by the inference client.
- `MODEL_ID` - Model identifier (e.g., `meta-llama/Meta-Llama-3-8B-Instruct`).
- `MODEL_CONFIG_PATH` - Path to `configs/model_config.json` (default: `./configs/model_config.json`).
- `DEBATE_CONFIG_PATH` - Path to `configs/debate_config.json` (default: `./configs/debate_config.json`).
- `CHARACTER_DUMP_PATH` - Directory for saving generated character JSON files (e.g., `./characters`).

## Endpoints (examples)

- GET `/` — health check.
- GET `/characters/` — list available characters (base + saved).
- POST `/characterCreate/` — form field `user_input` (string). Returns created character JSON.
- POST `/debate/` — form fields: `prompt`, `char_a`, `char_b`, `debate_rounds_count` (int). Returns debate transcript.

Example curl for listing characters:

```bash
curl http://localhost:8000/characters/
```

Example curl to start a debate (form-encoded):

```bash
curl -X POST http://localhost:8000/debate/ \
  -F "prompt=Is AI generally beneficial?" \
  -F "char_a=Dr. Doofenshmirtz" \
  -F "char_b=Phineas Flynn" \
  -F "debate_rounds_count=3"
```

## Next recommended steps (learning & production hardening)
- Add `.env.example` (done). Keep real secrets out of git.
- Add `Dockerfile` and `docker-compose.yml` for local containerized dev.
- Convert endpoints to `async`, reuse the model client, and add retries/timeouts.
- Add unit tests and a CI pipeline.
- Add observability: structured logging, metrics, Sentry/tracing.

If you'd like, I can add a `Dockerfile` and a `docker-compose.yml` next, or refactor the model adapter for client reuse.

## License
This repository is for learning purposes. Add a license as appropriate.
