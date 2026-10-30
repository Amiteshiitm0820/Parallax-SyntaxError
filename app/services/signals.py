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
    "gov.in", "nic.in", "jio.com", "airtel.in", "echallan.parivahan.gov.in",
}

SUSPICIOUS_TLDS = {
    "xyz", "top", "click", "win", "bid", "club", "site", "online",
    "support", "info", "cc", "icu", "biz", "work", "link", "tk", "ml", "ga", "cf",
    "in", "co",  # commonly abused in India-targeted phishing
}

# ---------------------------------------------------------------------------
# URGENCY — English + Hindi + Hinglish
# ---------------------------------------------------------------------------
URGENCY_PATTERNS = [
    # English
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
    r"\bdeactivat\w*\b",
    r"\brestrict\w*\b",
    # Hinglish
    r"\bturant\b",
    r"\bjaldi\s*(se|karo|karen)?\b",
    r"\bbandh ho jayega\b",
    r"\bblock ho jayega\b",
    r"\baccount ban\b",
    r"\bsuspend ho gaya\b",
    r"\bwarna\b",                    # "otherwise" — used in threats
    r"\bkal se\b",                   # "from tomorrow" — deadline signal
    r"\baaj raat\b",                 # "tonight"
    r"\bابھی\b",                     # Urdu/Hindi "abhi" = right now
    # Hindi (Devanagari)
    r"कट जाएगी",
    r"ब्लॉक",
    r"बंद",                          # "closed/cut off"
    r"तुरंत",                        # "immediately"
    r"सस्पेंड",
    r"चेतावनी",                      # "warning"
    r"अभी",                          # "right now"
    r"कल से",                        # "from tomorrow"
    r"आज रात",                       # "tonight"
    r"बकाया",                        # "overdue/pending"
    r"ज़ब्त",                         # "seized/confiscated"
]

# ---------------------------------------------------------------------------
# CREDENTIAL HARVESTING — English + Hindi + Hinglish
# ---------------------------------------------------------------------------
CREDENTIAL_PATTERNS = [
    # English
    r"\b(verify|update|confirm|re-?activate)\b.{0,30}\b(kyc|account|details|password|otp|pin|upi)\b",
    r"\b(share|send|enter|provide)\b.{0,20}\b(otp|pin|password|cvv|card number)\b",
    r"\bkyc\b",
    r"\botp\b",
    r"\bupi pin\b|\bmpin\b|\bcvv\b",
    r"\bpan card verification\b|\baadhaar? (card )?update\b",
    r"\bpan.{0,10}aadhaar\b|\baadhaar.{0,10}pan\b",   # PAN-Aadhaar linking scams
    # Hinglish
    r"\bkyc update karo\b|\bkyc update kar\b",
    r"\bkyc complete karo\b",
    r"\blink karo\b|\blink karein\b",                  # "link now"
    r"\bregister karo\b|\bregister karein\b",
    r"\bprocess fee\b",                                 # fake loan processing fee
    r"\bjoining fee\b|\bregistration fee\b",
    # Hindi (Devanagari)
    r"केवाईसी",                      # KYC in Hindi
    r"लिंक करें",                    # "link now"
    r"अपडेट करें",                   # "update now"
    r"पैन कार्ड",                    # PAN card mention
    r"आधार",                         # Aadhaar mention
    r"खाता",                         # bank account
    r"सत्यापन",                      # "verification"
    r"भुगतान करें",                  # "make payment"
]

# ---------------------------------------------------------------------------
# REWARD BAIT — English + Hindi + Hinglish
# ---------------------------------------------------------------------------
REWARD_PATTERNS = [
    # English
    r"\bcongratulations\b",
    r"\byou (have )?won\b",
    r"\bcashback\b",
    r"\blottery\b|\blucky draw\b|\blucky ड्रा\b",
    r"\bfree (gift|recharge|prize)\b",
    r"\bclaim (now|your|bonus)\b",
    r"\bwinner\b",
    r"\bprize\b",
    r"\breward\b",
    r"\bpart.?time job\b|\bwork from home\b|\bwfh job\b",
    r"\bearn.{0,20}per day\b|\bdaily earning\b",
    # Hinglish
    r"\bjeet[ae]?\b",                # "won" in Hinglish
    r"\bclam karo\b|\bclaim karlo\b|\bclaim kar\b",
    r"\bkamai\b",                    # "earnings"
    r"\bpart time\b",
    r"\byoutube (video )?like\b",    # YouTube task scam
    r"\bwhatsapp group\b.{0,30}(join|earn|kamai)",
    r"\btelegram.{0,20}(earn|job|recruiter)\b",
    # Hindi (Devanagari)
    r"बधाई हो",                      # "congratulations"
    r"जीते हैं",                     # "you have won"
    r"लॉटरी",                        # lottery
    r"क्लेम",                        # "claim"
    r"इनाम",                         # "prize/reward"
    r"मुफ्त",                        # "free"
    r"कमाएं",                        # "earn"
]

# ---------------------------------------------------------------------------
# URL SHORTENERS — high suspicion
# ---------------------------------------------------------------------------
URL_SHORTENERS = {"bit.ly", "tinyurl.com", "t.co", "goo.gl", "is.gd",
                  "cutt.ly", "rebrand.ly", "ow.ly", "wa.me", "chat.whatsapp.com"}


@dataclass
class Signal:
    quote: str
    type: str
    reason: str
    weight: int  # contribution to the rule score, 0-100


def _find_all(patterns: list[str], text: str) -> list[str]:
    hits = []
    seen = set()
    for pat in patterns:
        for m in re.finditer(pat, text, flags=re.IGNORECASE):
            hit = m.group(0)
            if hit not in seen:
                seen.add(hit)
                hits.append(hit)
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

        # URL shorteners — very high suspicion
        if host in URL_SHORTENERS:
            signals.append(Signal(
                quote=url,
                type="URL Shortener",
                reason="Uses a link shortener to hide the real destination — a common phishing tactic.",
                weight=50,
            ))
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
                weight=40,
            ))
        elif re.search(
            r"\b(sbi|hdfc|icici|axis|kyc|upi|bank|update|verify|gov|uidai|"
            r"income.?tax|jio|airtel|yono|epf|challan|customs|fedex|amazon|"
            r"netflix|whatsapp|apple|loan|prize|winner|refund|yojana)\b",
            host,
        ):
            signals.append(Signal(
                quote=url,
                type="Domain Inconsistency",
                reason="Domain imitates a bank, government service, or known brand but is not an official domain.",
                weight=40,
            ))
        else:
            signals.append(Signal(
                quote=url,
                type="Suspicious URL",
                reason="Contains an external link that cannot be verified as official.",
                weight=15,
            ))
    return signals


def check_urgency(text: str) -> list[Signal]:
    return [
        Signal(quote=q, type="Artificial Urgency",
               reason="Imposes a deadline or threat to force quick action.", weight=20)
        for q in _find_all(URGENCY_PATTERNS, text)
    ]


def check_credentials(text: str) -> list[Signal]:
    return [
        Signal(quote=q, type="Credential Harvesting",
               reason="Asks for banking details, OTP, KYC, or personal verification — legitimate institutions never request these through message links.",
               weight=35)
        for q in _find_all(CREDENTIAL_PATTERNS, text)
    ]


def check_rewards(text: str) -> list[Signal]:
    return [
        Signal(quote=q, type="Unsolicited Reward",
               reason="Promises a prize, cashback, or easy income to lure the reader — a classic social engineering tactic.",
               weight=25)
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
    """Score from rules. Each signal type counts once at its strongest weight.

    Multi-type bonus applied when 2+ different types fire. Capped at 100.
    """
    if not signals:
        return 0
    best_by_type: dict[str, int] = {}
    for s in signals:
        best_by_type[s.type] = max(best_by_type.get(s.type, 0), s.weight)
    total = sum(best_by_type.values())
    # Bonus for multiple signal types (more types = stronger evidence)
    n = len(best_by_type)
    if n >= 3:
        total += 30
    elif n == 2:
        total += 20
    return min(100, total)
