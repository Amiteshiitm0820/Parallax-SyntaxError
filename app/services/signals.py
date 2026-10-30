"""Fast rule-based signal extraction. No LLM calls here.

Owner: teammate A.

Each detector returns a list of Signal objects. The analyzer passes these to the
LLM as hints and uses them as a floor for the risk score.
"""
import re
from dataclasses import dataclass
from urllib.parse import urlparse

URL_RE = re.compile(r"(?:https?://|www\.)[^\s<>\"']+|\b[a-z0-9-]+\.[a-z]{2,}(?:/[^\s]*)?", re.IGNORECASE)

# Domains that are official for Indian banks/government. Extend as needed.
OFFICIAL_DOMAINS = {
    "sbi.co.in", "onlinesbi.sbi", "yonobysbi.com",
    "hdfcbank.com", "icicibank.com", "axisbank.com", "npci.org.in",
    "incometax.gov.in", "uidai.gov.in", "gov.in", "nic.in",
}

# Top-level domains commonly abused in phishing campaigns.
SUSPICIOUS_TLDS = {"xyz", "top", "click", "link", "buzz", "rest", "icu", "tk", "ml", "ga", "cf"}

URGENCY_PATTERNS = [
    r"\burgent(ly)?\b",
    r"\bimmediately\b",
    r"\bwithin \d+\s*(hour|hr|minute|min|day)s?\b",
    r"\bterminat\w*\b",
    r"\bblock(ed)?\b",
    r"\bsuspend(ed)?\b",
    r"\bexpire[sd]?\b",
    r"\blast (warning|chance)\b",
]

CREDENTIAL_PATTERNS = [
    r"\b(verify|update|confirm|re-?activate)\b.{0,30}\b(kyc|account|details|password|otp|pin|upi)\b",
    r"\b(share|send|enter|provide)\b.{0,20}\b(otp|pin|password|cvv|card number)\b",
    r"\bkyc\b",
]

REWARD_PATTERNS = [
    r"\bcongratulations\b",
    r"\byou (have )?won\b",
    r"\bcashback\b",
    r"\bfree (gift|recharge|prize)\b",
    r"\bclaim (now|your)\b",
]


@dataclass
class Signal:
    quote: str
    type: str
    reason: str
    weight: int  # contribution to the rule-based score, 0-100


def _find_all(patterns: list[str], text: str) -> list[str]:
    hits = []
    for pat in patterns:
        for m in re.finditer(pat, text, flags=re.IGNORECASE):
            hits.append(m.group(0))
    return hits


def extract_urls(text: str) -> list[str]:
    urls = []
    for raw in URL_RE.findall(text):
        candidate = raw.rstrip(".,;:!?)")
        urls.append(candidate)
    return urls


def _host(url: str) -> str:
    if not url.startswith(("http://", "https://")):
        url = "http://" + url
    return (urlparse(url).hostname or "").lower()


def check_domains(text: str) -> list[Signal]:
    signals = []
    for url in extract_urls(text):
        host = _host(url)
        if not host:
            continue
        tld = host.rsplit(".", 1)[-1]
        is_official = any(host == d or host.endswith("." + d) for d in OFFICIAL_DOMAINS)
        if is_official:
            continue
        if tld in SUSPICIOUS_TLDS:
            signals.append(Signal(
                quote=url,
                type="Domain Inconsistency",
                reason=f"Uses the '.{tld}' domain, which is commonly abused for phishing and is not an official bank or government domain.",
                weight=30,
            ))
        elif re.search(r"\b(sbi|hdfc|icici|axis|kyc|upi|bank|update|verify)\b", host):
            signals.append(Signal(
                quote=url,
                type="Domain Inconsistency",
                reason="Domain imitates a bank or government service but is not an official domain.",
                weight=35,
            ))
        else:
            signals.append(Signal(
                quote=url,
                type="Suspicious URL",
                reason="Contains an external link that cannot be verified as official.",
                weight=10,
            ))
    return signals


def check_urgency(text: str) -> list[Signal]:
    return [
        Signal(quote=q, type="Artificial Urgency",
               reason="Imposes a deadline or threat to force quick action.", weight=12)
        for q in _find_all(URGENCY_PATTERNS, text)
    ]


def check_credentials(text: str) -> list[Signal]:
    return [
        Signal(quote=q, type="Credential Harvesting",
               reason="Asks for banking details, OTP, or KYC verification, which legitimate institutions do not request by message link.",
               weight=25)
        for q in _find_all(CREDENTIAL_PATTERNS, text)
    ]


def check_rewards(text: str) -> list[Signal]:
    return [
        Signal(quote=q, type="Unsolicited Reward",
               reason="Promises a prize or cashback to lure the reader.", weight=15)
        for q in _find_all(REWARD_PATTERNS, text)
    ]


def extract_signals(text: str) -> list[Signal]:
    """Run every detector. Returns all signals in one flat list."""
    return (
        check_domains(text)
        + check_urgency(text)
        + check_credentials(text)
        + check_rewards(text)
    )


def rule_score(signals: list[Signal]) -> int:
    """Combine signal weights into a 0-100 score. Capped at 100."""
    return min(100, sum(s.weight for s in signals))
