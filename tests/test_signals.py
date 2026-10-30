"""Tests for rule-based signals. Owner: teammate A."""
from app.services.signals import extract_signals, rule_score

SBI_SCAM = (
    "URGENT: Your SBI account has been locked. Verify KYC immediately at "
    "http://sbi-kyc-update.xyz or services will terminate within 2 hours."
)


def test_scam_message_scores_high():
    signals = extract_signals(SBI_SCAM)
    types = {s.type for s in signals}
    assert "Domain Inconsistency" in types
    assert "Artificial Urgency" in types
    assert "Credential Harvesting" in types
    assert rule_score(signals) >= 60


def test_official_domain_is_not_flagged():
    text = "Your SBI statement is ready at https://onlinesbi.sbi/statement"
    signals = extract_signals(text)
    assert not any(s.type == "Domain Inconsistency" for s in signals)


def test_plain_message_scores_zero():
    assert rule_score(extract_signals("Are we still meeting for lunch tomorrow?")) == 0


def test_score_is_capped_at_100():
    text = " ".join([SBI_SCAM] * 10)
    assert rule_score(extract_signals(text)) == 100
