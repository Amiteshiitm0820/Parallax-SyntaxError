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
    "parivahan.gov.in",
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
    r"तुरंत|तुरन्त|जल्दी|बंद हो|बंद कर|ब्लॉक|निलंबित|समाप्त|कल से",
    r"\bband ho\b|\bblock ho\b|\bdisconnect\b",
]

CREDENTIAL_PATTERNS = [
    r"\b(verify|update|confirm|re-?activate)\b.{0,30}\b(kyc|account|details|password|otp|pin|upi)\b",
    r"\b(share|send|enter|provide)\b.{0,20}\b(otp|pin|password|cvv|card number)\b",
    r"\bkyc\b",
    r"\botp\b",
    r"\bupi pin\b|\bmpin\b|\bcvv\b",
    r"\bpan card verification\b|\baadhaar? (card )?update\b",
    r"केवाईसी|केवायसी|ओटीपी|आधार|पैन कार्ड|यूपीआई पिन|पासवर्ड",
    r"\b(aadhaar?|pan)\b.{0,20}\b(link|linking|update|verify|verification)\b",
]

REWARD_PATTERNS = [
    r"\bcongratulations\b",
    r"\byou (have )?won\b",
    r"\bcashback\b",
    r"\blottery\b|\blucky draw\b",
    r"\bfree (gift|recharge|prize)\b",
    r"\bclaim (now|your|bonus)\b",
    r"जीत|जीते|इनाम|लॉटरी|कैशबैक|बधाई|मुफ्त|मुफ़्त|पुरस्कार",
    r"part[- ]time|work from home|\bwfh\b|per day|daily earn|earn (rs|rupees|\d)",
    r"घर बैठे|पार्ट टाइम|रोज़ाना|रोजाना|कमाएं|कमाए",
]

# Messaging-app links are a common way to move victims into scam chats.
CONTACT_LINK_RE = re.compile(r"(?:t\.me|wa\.me|chat\.whatsapp\.com|telegram\.me)/[^\s]+", re.IGNORECASE)

# Words that make a non-official domain look like a bank, government or prize scheme.
LURE_TOKENS = {
    "prize", "winner", "win", "reward", "rewards", "claim", "refund", "cashback",
    "offer", "bonus", "gift", "lucky", "lottery", "kyc", "pan", "aadhar", "aadhaar",
    "link", "verify", "update", "secure", "login", "bank", "sbi", "hdfc", "icici",
    "axis", "upi", "jio", "airtel", "paytm", "phonepe", "gpay", "netbanking",
    "loan", "yojana", "support", "recovery", "delivery", "tracker", "redelivery",
    "parcel", "billing", "subscription", "epf", "uan", "fee", "payment", "recharge",
    "scheme", "subsidy", "kbc", "govt", "gov", "alert", "reactivate", "unlock",
    "pay", "challan", "echallan", "customs", "duty", "clearance", "penalty",
}

# Known names scammers imitate. Used after undoing look-alike character swaps.
BRAND_TOKENS = {
    "netflix", "amazon", "flipkart", "paypal", "google", "microsoft", "whatsapp",
    "irctc", "epfo", "uidai", "uppcl", "bescom", "mseb", "tneb", "bsnl", "incometax",
}

# Characters commonly swapped in for letters: 0->o, 1->l, ! or | -> i/l, capital I -> l.
LOOKALIKE_MAP = str.maketrans({"0": "o", "1": "l", "!": "i", "|": "l", "I": "l"})

IP_HOST_RE = re.compile(r"^\d{1,3}(\.\d{1,3}){3}$")


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


def _raw_host(url: str) -> str:
    """Host with its original characters, so look-alike swaps can be detected."""
    if not url.startswith(("http://", "https://")):
        url = "http://" + url
    netloc = urlparse(url).netloc
    return netloc.split("@")[-1].split(":")[0]


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
        if IP_HOST_RE.match(host):
            signals.append(Signal(
                quote=url,
                type="Domain Inconsistency",
                reason="Link points to a raw IP address instead of a named website.",
                weight=35,
            ))
            continue
        disguised = _raw_host(url).translate(LOOKALIKE_MAP).lower()
        if disguised != _raw_host(url).lower():
            labels = set(re.split(r"[.\-]", disguised))
            if labels & (LURE_TOKENS | BRAND_TOKENS):
                signals.append(Signal(
                    quote=url,
                    type="Domain Inconsistency",
                    reason="Uses look-alike characters (such as 0 for o or I for l) to imitate a known name.",
                    weight=35,
                ))
                continue
        if tld in SUSPICIOUS_TLDS:
            signals.append(Signal(
                quote=url,
                type="Domain Inconsistency",
                reason=f"Uses the '.{tld}' domain, which is often abused for phishing and is not an official domain.",
                weight=30,
            ))
        elif set(re.split(r"[.\-]", host)) & LURE_TOKENS or host.endswith(".gov.in"):
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


def check_contact_links(text: str) -> list[Signal]:
    return [
        Signal(quote=m.group(0), type="Scam Chat Link",
               reason="Links to a messaging app. Scammers use these to move victims into private chats.",
               weight=25)
        for m in CONTACT_LINK_RE.finditer(text)
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
        + check_contact_links(text)
    )


def rule_score(signals: list[Signal]) -> int:
    """Score from rules. Each signal type counts once, at its strongest weight.

    This stops repeated matches (e.g. four urgency words) from inflating the score.
    A small bonus applies when several different types fire. Capped at 100.
    """
    if not signals:
        return 0
    best_by_type: dict[str, int] = {}
    for s in signals:
        best_by_type[s.type] = max(best_by_type.get(s.type, 0), s.weight)
    total = sum(best_by_type.values())
    if len(best_by_type) >= 2:
        total += 20
    return min(100, total)
