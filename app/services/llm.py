"""LLM client wrapper. Returns parsed JSON or raises LLMError.

Owner: teammate B.

Provider is chosen with the LLM_PROVIDER env var ("gemini" or "mock").
The mock provider lets the whole API run without any API key.
"""
import json
import os
import re
from typing import Protocol

PROMPT_PATH = os.path.join(os.path.dirname(__file__), "..", "prompts", "analysis_prompt.txt")


class LLMError(Exception):
    pass


class LLMClient(Protocol):
    def analyze(self, message_text: str, channel: str, hints: list[dict]) -> dict: ...


def _load_system_prompt() -> str:
    with open(PROMPT_PATH, encoding="utf-8") as f:
        return f.read()


def _parse_json(raw: str) -> dict:
    """Models sometimes wrap JSON in markdown fences. Strip them, then parse."""
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip())
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise LLMError(f"LLM returned invalid JSON: {exc}") from exc


class GeminiClient:
    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
        from google import genai  # imported lazily so mock mode needs no package
        self._client = genai.Client(api_key=api_key)
        self._model = model
        self._system = _load_system_prompt()

    def analyze(self, message_text: str, channel: str, hints: list[dict]) -> dict:
        user_block = json.dumps(
            {"message_text": message_text, "channel": channel, "rule_hints": hints},
            ensure_ascii=False,
        )
        response = self._client.models.generate_content(
            model=self._model,
            contents=user_block,
            config={
                "system_instruction": self._system,
                "response_mime_type": "application/json",
                "temperature": 0.1,
            },
        )
        return _parse_json(response.text or "")


class MockClient:
    """Deterministic fake for local development and tests."""

    def analyze(self, message_text: str, channel: str, hints: list[dict]) -> dict:
        score = min(100, sum(h.get("weight", 0) for h in hints))
        return {
            "risk_score": score,
            "language": "English",
            "summary": "Mock analysis based on rule hints only.",
            "evidence_highlights": [
                {"quote": h["quote"], "type": h["type"], "reason": h["reason"]}
                for h in hints[:5]
            ],
            "recommended_action": "Verify with the official app or branch before acting.",
        }


def get_llm_client() -> LLMClient:
    provider = os.getenv("LLM_PROVIDER", "mock").lower()
    if provider == "gemini":
        key = os.getenv("GEMINI_API_KEY")
        if not key:
            raise LLMError("GEMINI_API_KEY is not set.")
        return GeminiClient(api_key=key, model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash"))
    return MockClient()
