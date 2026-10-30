"""Tests for rule-based signals."""
from app.services.signals import extract_signals, rule_score

SBI_PHISH = (
    "ALERT: Your SBI NetBanking account is blocked due to missing re-kyc updates. "
    "Click http://sbi-verify-kyc.xyz immediately to recover."
)


def test_phishing_message_scores_high():
    signals = extract_signals(SBI_PHISH)
    types = {s.type for s in signals}
    assert "Domain Inconsistency" in types
    assert "Artificial Urgency" in types
    assert "Credential Harvesting" in types
    assert rule_score(signals) >= 60


def test_official_domain_is_not_flagged():
    signals = extract_signals("Your SBI transaction was successful. Details at https://sbi.co.in")
    assert not any(s.type in ("Domain Inconsistency", "Suspicious URL") for s in signals)


def test_genuine_message_scores_zero():
    assert rule_score(extract_signals("Your transaction on sbi.co.in was successful. Thank you.")) == 0


def test_empty_text_is_safe():
    assert extract_signals("") == []
    assert rule_score([]) == 0


def test_hinglish_message_scores_and_quotes_are_exact():
    sample = "Apka account bandh ho jayega turant check http://secure-pay.click"
    signals = extract_signals(sample)
    assert rule_score(signals) > 0
    for s in signals:
        assert s.quote in sample


def test_score_is_capped_at_100():
    assert rule_score(extract_signals(" ".join([SBI_PHISH] * 10))) == 100
