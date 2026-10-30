"""Fast rule-based signal extraction. No LLM calls here.

Owner: teammate.

Each detector returns Signal objects. The analyzer passes them to the LLM as
hints and uses their weights as a score floor.
"""
import re
from dataclasses import dataclass
from urllib.parse import urlparse

URL_RE = re.compile(
    r"(?:https?://|www\.)[^\s<>\"']+|\b[a-z0-9-]+(?:\.[a-z0-9-]+)+(?:/[^\s]*)?",
    re.IGNORECASE,
)

OFFICIAL_DOMAINS = {
    "sbi.co.in", "onlinesbi.sbi", "yonobysbi.com",
    "hdfcbank.com", "icicibank.com", "axisbank.com",
    "paytm.com", "phonepe.com", "amazon.in", "flipkart.com", "cricbuzz.com",
    "npci.org.in", "incometax.gov.in", "uidai.gov.in", "indiapost.gov.in",
    "gov.in", "nic.in",
}

SUSPICIOUS_TLDS = {
    "xyz", "top", "click", "win", "bid", "club", "site", "online",
    "support", "info", "cc", "icu", "biz", "work", "link", "tk", "ml", "ga", "cf",
}

URGENCY_PATTERNS = [
    r"\burgent(ly)?\b",
    r"\bimmediately\b",
    r"\bwithin \d+\s*(hour|hr|minute|min|day)s?\b",
    r"\bterminat\w*\b",
    r"\bblock(ed)?\b",
    r"\bsuspend(ed)?\b",
    r"\bexpire[sd]?\b",
    r"\blast (warning|chance)\b",
    r"\bfinal notice\b",
    r"\bpower cut-?off\b|\belectricity cut\b",
    r"\bturant\b",
    r"\bjaldi\b",
    r"\bbandh ho jayega\b",
]

CREDENTIAL_PATTERNS = [
    r"\b(verify|update|confirm|re-?activate)\b.{0,30}\b(kyc|account|details|password|otp|pin|upi)\b",
    r"\b(share|send|enter|provide)\b.{0,20}\b(otp|pin|password|cvv|card number)\b",
    r"\bkyc\b",
    r"\botp\b",
    r"\bupi pin\b|\bmpin\b|\bcvv\b",
    r"\bpan card verification\b|\baadhaar? (card )?update\b",
]

REWARD_PATTERNS = [
    r"\bcongratulations\b",
    r"\byou (have )?won\b",
    r"\bcashback\b",
    r"\blottery\b|\blucky draw\b",
    r"\bfree (gift|recharge|prize)\b",
    r"\bclaim (now|your|bonus)\b",
]


@dataclass
class Signal:
    quote: str
    type: str
    reason: str
    weight: int  # contribution to the rule score, 0-100


def _find_all(patterns: list[str], text: str) -> list[str]:
    hits = []
    for pat in patterns:
        for m in re.finditer(pat, text, flags=re.IGNORECASE):
            hits.append(m.group(0))
    return hits


def extract_urls(text: str) -> list[str]:
    return [raw.rstrip(".,;:!?)") for raw in URL_RE.findall(text)]


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
                reason=f"Uses the '.{tld}' domain, which is often abused for phishing and is not an official domain.",
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
               reason="Asks for banking details, OTP, or KYC verification, which legitimate institutions do not request through message links.",
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
    """Run every detector and return one flat list."""
    if not text:
        return []
    return (
        check_domains(text)
        + check_urgency(text)
        + check_credentials(text)
        + check_rewards(text)
    )


def rule_score(signals: list[Signal]) -> int:
    """Sum the weights, add a bonus when several categories fire, cap at 100."""
    if not signals:
        return 0
    total = sum(s.weight for s in signals)
    if len({s.type for s in signals}) >= 2:
        total += 20
    return min(100, total)
