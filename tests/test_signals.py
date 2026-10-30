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


def test_repeated_matches_do_not_inflate_score():
    # Same message repeated: each type still counts once, so the score is not pushed to 100.
    assert rule_score(extract_signals(" ".join([SBI_PHISH] * 10))) == rule_score(extract_signals(SBI_PHISH))


def test_score_is_capped_at_100():
    assert 0 <= rule_score(extract_signals(SBI_PHISH)) <= 100


def test_lookalike_netflix_domain_is_flagged():
    from app.services.signals import check_domains
    sigs = check_domains("Netflix billing: netfIix.com")
    assert any(s.type == "Domain Inconsistency" for s in sigs)


def test_lookalike_power_bill_domain_is_flagged():
    from app.services.signals import check_domains
    sigs = check_domains("बिजली बिल: uppcl.0rg/pay")
    assert any(s.type == "Domain Inconsistency" for s in sigs)


def test_real_domain_with_digits_not_flagged_as_lookalike():
    from app.services.signals import check_domains
    sigs = check_domains("Order at 1mg.com today")
    assert not any(s.type == "Domain Inconsistency" for s in sigs)


def test_plain_brand_domain_not_flagged_as_lookalike():
    from app.services.signals import check_domains
    sigs = check_domains("Watch at netflix.com")
    assert not any(s.type == "Domain Inconsistency" for s in sigs)
