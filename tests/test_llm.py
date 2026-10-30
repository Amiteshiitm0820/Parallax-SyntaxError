"""Tests for the LLM layer. No real network calls."""
import json
from unittest.mock import MagicMock, patch

import pytest

from app.services import llm
from app.services.llm import LLMError, MockClient, OpenAICompatibleClient, _parse_json, get_llm_client


def test_parse_strips_markdown_fences():
    raw = "```json\n{\"risk_score\": 10}\n```"
    assert _parse_json(raw)["risk_score"] == 10


def test_parse_extracts_object_from_extra_text():
    raw = "Reasoning: checking the link...\n{\"risk_score\": 42}\nDone."
    assert _parse_json(raw)["risk_score"] == 42


def test_parse_invalid_json_raises():
    with pytest.raises(LLMError):
        _parse_json("not json at all")


def test_default_provider_is_mock(monkeypatch):
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    assert isinstance(get_llm_client(), MockClient)


def test_groq_provider_uses_openai_compatible_client(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.setenv("LLM_API_KEY", "fake-key")
    with patch.object(llm, "_load_system_prompt", return_value="prompt"):
        client = get_llm_client()
    assert isinstance(client, OpenAICompatibleClient)


def test_openai_client_parses_model_reply():
    reply = {"choices": [{"message": {"content": json.dumps({
        "risk_score": 90,
        "language": "English",
        "summary": "Scam found",
        "evidence_highlights": [],
        "recommended_action": "Do not click.",
    })}}]}
    fake_resp = MagicMock()
    fake_resp.read.return_value = json.dumps(reply).encode("utf-8")
    with patch.object(llm, "_load_system_prompt", return_value="prompt"), \
         patch("urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.return_value.__enter__.return_value = fake_resp
        client = OpenAICompatibleClient("https://example.test/v1", "fake-key", "fake-model")
        result = client.analyze("Win 1 crore now!", "sms", [])
    assert result["risk_score"] == 90
