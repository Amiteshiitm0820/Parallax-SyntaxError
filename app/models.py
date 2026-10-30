"""Pydantic request/response schemas. This is the contract shared with the frontend.

Owner: shared. Change these only after telling the frontend teammate.
"""
from typing import Literal, Optional

from pydantic import BaseModel, Field


RiskTier = Literal["Low Risk", "Medium Risk", "High Risk", "Critical Risk"]


class AnalyzeRequest(BaseModel):
    message_text: str = Field(..., description="Raw pasted message text")
    channel: Literal["sms", "email", "whatsapp", "other"] = "sms"


class EvidenceHighlight(BaseModel):
    quote: str
    type: str
    reason: str


class AnalyzeResponse(BaseModel):
    analysis_id: str
    risk_score: int = Field(..., ge=0, le=100)
    risk_tier: RiskTier
    language: str
    summary: str
    evidence_highlights: list[EvidenceHighlight]
    recommended_action: str


class FeedbackRequest(BaseModel):
    analysis_id: Optional[str] = None
    message_text: str
    original_risk_score: Optional[int] = None
    user_comment: Optional[str] = None


class FeedbackResponse(BaseModel):
    status: str
    message: str


def tier_for_score(score: int) -> RiskTier:
    """Map a 0-100 score to a tier label. Used by the analyzer, not the LLM."""
    if score >= 80:
        return "Critical Risk"
    if score >= 60:
        return "High Risk"
    if score >= 30:
        return "Medium Risk"
    return "Low Risk"
