"""Orchestrates signals -> LLM -> validated response.

Owner: shared (lead). Teammates should not need to edit this file.
"""
import logging
import uuid

from app.models import AnalyzeRequest, AnalyzeResponse, EvidenceHighlight, tier_for_score
from app.services.llm import LLMClient, LLMError
from app.services.signals import extract_signals, rule_score

log = logging.getLogger("trustlens.analyzer")


def analyze_message(req: AnalyzeRequest, llm: LLMClient) -> tuple[str, AnalyzeResponse]:
    """Returns (analysis_id, response). Falls back to rule-only output if the LLM fails."""
    analysis_id = str(uuid.uuid4())
    signals = extract_signals(req.message_text)
    hints = [
        {"quote": s.quote, "type": s.type, "reason": s.reason, "weight": s.weight}
        for s in signals
    ]
    floor = rule_score(signals)

    try:
        raw = llm.analyze(req.message_text, req.channel, hints)
    except LLMError as exc:
        log.warning("LLM failed, using rule-only fallback: %s", exc)
        raw = {
            "risk_score": floor,
            "language": "Unknown",
            "summary": "AI analysis unavailable; result is based on rule checks only.",
            "evidence_highlights": hints[:5],
            "recommended_action": "Verify with the official app or branch before acting.",
        }

    # Score never drops below the rule floor; the LLM can only raise it.
    score = max(int(raw.get("risk_score", 0)), floor)
    score = max(0, min(100, score))

    highlights = []
    for h in raw.get("evidence_highlights", [])[:5]:
        # Drop any quote the LLM invented that is not in the original text.
        if h.get("quote") and h["quote"] in req.message_text:
            highlights.append(EvidenceHighlight(**{k: h[k] for k in ("quote", "type", "reason")}))

    response = AnalyzeResponse(
        risk_score=score,
        risk_tier=tier_for_score(score),
        language=raw.get("language", "Unknown"),
        summary=raw.get("summary", ""),
        evidence_highlights=highlights,
        recommended_action=raw.get("recommended_action", ""),
    )
    return analysis_id, response
