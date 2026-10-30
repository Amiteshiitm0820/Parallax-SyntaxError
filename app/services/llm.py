"""LLM client layer. Returns the analysis dict or raises LLMError.

Owner: teammate.

LLM_PROVIDER: "mock" (default, no key needed), "gemini", "groq", "openrouter",
"mistral", or "openai". The last four all use the OpenAI-compatible client.
"""
import json
import os
import re
import time
import urllib.error
import urllib.request
from typing import Protocol

PROMPT_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "prompts", "analysis_prompt.txt"
)

# Defaults per OpenAI-compatible provider. Check each provider's current model names.
OPENAI_COMPATIBLE_DEFAULTS = {
    "groq": ("https://api.groq.com/openai/v1", "llama-3.3-70b-versatile"),
    "openrouter": ("https://openrouter.ai/api/v1", "meta-llama/llama-3.3-70b-instruct:free"),
    "mistral": ("https://api.mistral.ai/v1", "mistral-small-latest"),
    "openai": ("https://api.openai.com/v1", "gpt-4o-mini"),
}


class LLMError(Exception):
    pass


class LLMClient(Protocol):
    def analyze(self, message_text: str, channel: str, hints: list[dict]) -> dict: ...


def _load_system_prompt() -> str:
    with open(PROMPT_PATH, encoding="utf-8") as f:
        return f.read()


def _user_payload(message_text: str, channel: str, hints: list[dict]) -> str:
    return json.dumps(
        {"message_text": message_text, "channel": channel, "rule_hints": hints},
        ensure_ascii=False,
    )


def _parse_json(raw: str) -> dict:
    """Pull the JSON object out of a model reply.

    Handles markdown fences, and extra text or reasoning before/after the object.
    """
    text = raw.strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        raise LLMError("LLM reply contained no JSON object.")
    try:
        return json.loads(text[start:end + 1])
    except json.JSONDecodeError as exc:
        raise LLMError(f"LLM returned invalid JSON: {exc}") from exc


class GeminiClient:
    def __init__(self, api_key: str, model: str = "gemini-3.5-flash-lite"):
        from google import genai  # lazy import so mock mode needs no package
        self._client = genai.Client(api_key=api_key)
        self._model = model
        self._system = _load_system_prompt()

    def analyze(self, message_text: str, channel: str, hints: list[dict]) -> dict:
        try:
            response = self._client.models.generate_content(
                model=self._model,
                contents=_user_payload(message_text, channel, hints),
                config={
                    "system_instruction": self._system,
                    "response_mime_type": "application/json",
                    "temperature": 0.1,
                },
            )
        except Exception as exc:
            raise LLMError(f"Gemini request failed: {exc}") from exc
        return _parse_json(response.text or "")


class OpenAICompatibleClient:
    """Works with Groq, OpenRouter, Mistral and OpenAI via base_url."""

    def __init__(self, base_url: str, api_key: str, model: str) -> None:
        self._url = f"{base_url.rstrip('/')}/chat/completions"
        self._api_key = api_key
        self._model = model
        self._system = _load_system_prompt()

    def analyze(self, message_text: str, channel: str, hints: list[dict]) -> dict:
        body = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": self._system},
                {"role": "user", "content": _user_payload(message_text, channel, hints)},
            ],
            "temperature": 0.1,
        }
        data = json.dumps(body).encode("utf-8")
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        for attempt in range(2):  # one retry on 429
            req = urllib.request.Request(self._url, data=data, headers=headers, method="POST")
            try:
                with urllib.request.urlopen(req, timeout=20) as resp:
                    payload = json.loads(resp.read().decode("utf-8"))
                content = payload["choices"][0]["message"]["content"]
                return _parse_json(content)
            except urllib.error.HTTPError as exc:
                if exc.code == 429 and attempt == 0:
                    time.sleep(2)
                    continue
                raise LLMError(f"Upstream HTTP error {exc.code}") from exc
            except (urllib.error.URLError, KeyError, IndexError, json.JSONDecodeError) as exc:
                raise LLMError(f"Unexpected LLM response: {exc}") from exc
        raise LLMError("Still rate limited after retry.")


class MockClient:
    """Deterministic fake for local development and tests. Uses the rule hints."""

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
        return GeminiClient(api_key=key, model=os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite"))
    if provider in OPENAI_COMPATIBLE_DEFAULTS:
        default_url, default_model = OPENAI_COMPATIBLE_DEFAULTS[provider]
        return OpenAICompatibleClient(
            base_url=os.getenv("LLM_BASE_URL", default_url),
            api_key=os.getenv("LLM_API_KEY", ""),
            model=os.getenv("LLM_MODEL", default_model),
        )
    return MockClient()
