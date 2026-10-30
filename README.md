# TrustLens Backend

## Setup

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

## Run

```bash
uvicorn app.main:app --reload --port 8000
```

Open http://localhost:8000/docs to test the endpoints.

## Test

```bash
pytest -q
```

## Layout

| Path | Purpose | Owner |
|------|---------|-------|
| `app/models.py` | Request/response schemas (frontend contract) | shared |
| `app/main.py` | Routes and CORS | lead |
| `app/services/analyzer.py` | Signals + LLM orchestration | lead |
| `app/services/signals.py` | Rule-based detectors | teammate A |
| `app/services/feedback.py` | False-positive storage | teammate A |
| `tests/test_signals.py` | Tests for signals | teammate A |
| `app/services/llm.py` | LLM client and JSON parsing | teammate B |
| `prompts/analysis_prompt.txt` | System prompt | teammate B |

Branch per owner, pull request into `main`. Do not edit each other's files without a message first.
