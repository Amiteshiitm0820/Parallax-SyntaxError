"""TRUSTLENS — polished Streamlit frontend (Person 4: UI & Pitch Deck Lead)

Run:
    python -m pip install streamlit requests
    streamlit run app.py

The frontend sends messages to FastAPI. Risk scores and tiers are supplied by
the backend; this file does not calculate them.
"""

from __future__ import annotations

import html
import json
import re
from pathlib import Path
from typing import Any

import requests
import streamlit as st

# ---------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------
st.set_page_config(
    page_title="TRUSTLENS | Message Security",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

import os
DEFAULT_API_URL = os.getenv("API_BASE_URL", "https://trustlens-backend-q0oj.onrender.com")
REQUEST_TIMEOUT = 30

CHANNELS = {
    "SMS": "sms",
    "WhatsApp": "whatsapp",
    "Email": "email",
    "Other": "other",
}

TIER_STYLE = {
    "Low Risk": {"color": "#35C98A", "soft": "rgba(53,201,138,.12)", "icon": "●"},
    "Medium Risk": {"color": "#E9B44C", "soft": "rgba(233,180,76,.12)", "icon": "●"},
    "High Risk": {"color": "#F28B50", "soft": "rgba(242,139,80,.12)", "icon": "●"},
    "Critical Risk": {"color": "#FF647C", "soft": "rgba(255,100,124,.12)", "icon": "●"},
}

FALLBACK_SAMPLES = {
    "SBI KYC alert · English SMS": (
        "URGENT: Your SBI account has been locked. Verify KYC immediately at "
        "http://sbi-kyc-update.xyz or services will terminate within 2 hours."
    ),
    "Electricity threat · Hinglish SMS": (
        "Aapki bijli kal raat tak kat jayegi! Abhi bill pay karo: "
        "http://bijli-bill-payment.xyz"
    ),
    "Bank alert · Hindi SMS": (
        "आपका खाता ब्लॉक हो जाएगा। अभी KYC अपडेट करें और OTP साझा करें: "
        "http://hdfc-secure-login.xyz"
    ),
    "Courier fee · WhatsApp": (
        "Your parcel is on hold. Pay ₹25 delivery reattempt fee now to avoid "
        "return: http://parcel-redelivery-fee.xyz"
    ),
    "Routine transaction · Safe example": (
        "Your transaction on sbi.co.in was successful. Thank you."
    ),
}

# Indian verification resources for SMS module
INDIA_VERIFICATION = {
    "banking": [
        {"name": "SBI Official", "domain": "https://www.sbi.co.in"},
        {"name": "HDFC Bank", "domain": "https://www.hdfcbank.com"},
        {"name": "ICICI Bank", "domain": "https://www.icicibank.com"},
        {"name": "RBI Kehta Hai", "domain": "https://rbi.org.in"},
    ],
    "government": [
        {"name": "Cyber Crime Portal", "domain": "https://cybercrime.gov.in"},
        {"name": "UIDAI (Aadhaar)", "domain": "https://uidai.gov.in"},
        {"name": "Income Tax", "domain": "https://www.incometax.gov.in"},
    ],
    "delivery": [
        {"name": "India Post Tracking", "domain": "https://www.indiapost.gov.in"},
        {"name": "DTDC Official", "domain": "https://www.dtdc.in"},
        {"name": "Blue Dart Official", "domain": "https://www.bluedart.com"},
    ],
    "general": [
        {"name": "Cyber Crime Helpline", "domain": "https://cybercrime.gov.in"},
        {"name": "Sanchar Saathi (TRAI)", "domain": "https://sancharsaathi.gov.in"},
    ],
}


# ---------------------------------------------------------------------
# Styling
# ---------------------------------------------------------------------
st.markdown(
    """
    <style>
    :root {
        --tl-bg: #080E1A;
        --tl-panel: #101A2B;
        --tl-panel-2: #142238;
        --tl-line: rgba(154, 177, 211, .16);
        --tl-text: #EAF1FC;
        --tl-muted: #91A2BC;
        --tl-cyan: #63D8E8;
        --tl-violet: #9B8CFF;
    }

    .stApp {
        background:
          radial-gradient(ellipse at 12% 0%, rgba(65, 119, 180, .16), transparent 34%),
          radial-gradient(ellipse at 90% 8%, rgba(91, 74, 174, .13), transparent 30%),
          var(--tl-bg);
        color: var(--tl-text);
    }
    [data-testid="stHeader"] { background: rgba(8,14,26,.82); }
    [data-testid="stSidebar"] {
        background: #0B1423;
        border-right: 1px solid var(--tl-line);
    }
    [data-testid="stSidebar"] > div { background: transparent; }
    .block-container { max-width: 1450px; padding-top: 2rem; padding-bottom: 2.5rem; }
    h1, h2, h3, p, label, [data-testid="stMarkdownContainer"] { color: var(--tl-text); }
    .tl-kicker {
        color: var(--tl-cyan); font-size: .72rem; font-weight: 800;
        letter-spacing: .2em; text-transform: uppercase; margin-bottom: .45rem;
    }
    .tl-hero {
        border: 1px solid var(--tl-line);
        border-radius: 22px;
        padding: 1.35rem 1.55rem;
        background: linear-gradient(115deg, rgba(20,34,56,.96), rgba(13,24,42,.88));
        box-shadow: 0 16px 45px rgba(0,0,0,.18);
        margin-bottom: 1.35rem;
    }
    .tl-hero-title { font-size: 2.05rem; font-weight: 850; letter-spacing: -.045em; margin: 0; }
    .tl-hero-sub { color: var(--tl-muted); margin-top: .35rem; font-size: .96rem; }
    .tl-pill {
        display: inline-block; padding: .35rem .65rem; border-radius: 999px;
        border: 1px solid rgba(99,216,232,.28); color: var(--tl-cyan);
        background: rgba(99,216,232,.07); font-size: .72rem; font-weight: 750;
        letter-spacing: .08em; text-transform: uppercase;
    }
    .tl-panel {
        background: linear-gradient(145deg, rgba(17,29,48,.98), rgba(13,23,39,.98));
        border: 1px solid var(--tl-line); border-radius: 18px;
        padding: 1.15rem 1.25rem; margin-bottom: 1rem;
    }
    .tl-panel-label {
        color: var(--tl-muted); font-size: .72rem; font-weight: 800;
        letter-spacing: .14em; text-transform: uppercase; margin-bottom: .55rem;
    }
    .tl-muted { color: var(--tl-muted); }
    .tl-risk {
        border: 1px solid var(--tl-line); border-radius: 18px;
        padding: 1.25rem 1.35rem; margin: .65rem 0 .8rem 0;
        background: linear-gradient(135deg, rgba(20,34,56,.96), rgba(12,22,38,.98));
    }
    .tl-risk-score { font-size: 2.8rem; line-height: 1; font-weight: 850; letter-spacing: -.06em; }
    .tl-evidence {
        border: 1px solid var(--tl-line); background: rgba(12,22,38,.82);
        padding: 1rem 1.1rem; border-radius: 14px; line-height: 1.85;
        overflow-wrap: anywhere;
    }
    .tl-evidence mark {
        background: rgba(233,180,76,.24); color: #FFE6A6;
        border: 1px solid rgba(233,180,76,.35); padding: 2px 4px;
        border-radius: 5px; font-weight: 750;
    }
    .tl-foot {
        color: #8192AA; font-size: .78rem; border-top: 1px solid var(--tl-line);
        padding-top: 1rem; margin-top: 1.5rem;
    }
    .tl-verify-card {
        background: rgba(99,216,232,.06); border: 1px solid rgba(99,216,232,.18);
        border-radius: 12px; padding: .75rem 1rem; margin-bottom: .5rem;
    }
    div.stButton > button[kind="primary"] {
        background: linear-gradient(100deg, #3CBFD1, #7770E8);
        border: 0; color: #07111E; font-weight: 850; min-height: 3rem;
        border-radius: 11px;
    }
    div.stButton > button {
        border-radius: 10px; border-color: var(--tl-line);
    }
    div[data-testid="stTextArea"] textarea,
    div[data-testid="stTextInput"] input,
    div[data-testid="stSelectbox"] > div > div {
        background: #0B1627 !important; color: var(--tl-text) !important;
        border-color: var(--tl-line) !important; border-radius: 10px !important;
    }
    [data-testid="stMetric"] {
        background: rgba(20,34,56,.65); border: 1px solid var(--tl-line);
        border-radius: 13px; padding: .8rem 1rem;
    }
    [data-testid="stMetricLabel"] { color: var(--tl-muted) !important; }
    [data-testid="stProgressBar"] > div > div { background: linear-gradient(90deg,#3CBFD1,#7770E8); }
    hr { border-color: var(--tl-line); }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------
# Sample loading
# ---------------------------------------------------------------------
def load_samples() -> dict[str, str]:
    """Load all standard, extended and edge-case test messages."""
    try:
        import data_config

        samples = {}

        for item in data_config.MESSAGES_DATASET:
            label = (
                f"{item['id']} · {item['type'].capitalize()} "
                f"· {item['lang'].capitalize()}"
            )
            samples[label] = item["text"]

        for item in data_config.EXTENDED_DATASET:
            label = (
                f"{item['id']} · Extended · {item['type'].capitalize()} "
                f"· {item['lang'].capitalize()}"
            )
            samples[label] = item["text"]

        for item in data_config.OBFUSCATED_EDGE_CASES:
            label = (
                f"{item['id']} · Edge Case "
                f"· {item['lang'].capitalize()}"
            )
            samples[label] = item["text"]

        return samples

    except (ImportError, AttributeError, KeyError, TypeError) as exc:
        st.warning(f"Could not load the TRUSTLENS test dataset: {exc}")
        return FALLBACK_SAMPLES


# ---------------------------------------------------------------------
# Backend communication
# ---------------------------------------------------------------------
def api_url(path: str) -> str:
    base = st.session_state.get("api_base_url", DEFAULT_API_URL).rstrip("/")
    return f"{base}{path}"


def check_backend() -> tuple[bool, str]:
    try:
        response = requests.get(api_url("/health"), timeout=5)
        response.raise_for_status()
        if response.json().get("status") == "ok":
            return True, "Backend online"
        return False, "Backend responded with an unexpected health status."
    except requests.exceptions.ConnectionError:
        return False, "Backend is unreachable. Confirm that FastAPI is running."
    except requests.exceptions.Timeout:
        return False, "Backend health check timed out."
    except (requests.exceptions.RequestException, ValueError) as exc:
        return False, f"Health check failed: {exc}"


def analyze_message(message_text: str, channel: str) -> dict[str, Any]:
    response = requests.post(
        api_url("/api/analyze"),
        json={"message_text": message_text, "channel": channel},
        headers={"Content-Type": "application/json"},
        timeout=REQUEST_TIMEOUT,
    )
    if response.status_code == 400:
        try:
            detail = response.json().get("detail", "The backend rejected the message.")
        except ValueError:
            detail = "The backend rejected the message."
        raise ValueError(str(detail))
    if response.status_code == 503:
        raise RuntimeError("Backend service unavailable (HTTP 503). Check backend configuration.")
    response.raise_for_status()

    try:
        payload = response.json()
    except ValueError as exc:
        raise RuntimeError("Backend returned invalid JSON.") from exc

    required = (
        "analysis_id", "risk_score", "risk_tier", "language", "summary",
        "evidence_highlights", "recommended_action",
    )
    missing = [field for field in required if field not in payload]
    if missing:
        raise RuntimeError("Backend response is missing: " + ", ".join(missing))
    return payload


def submit_feedback(
    message_text: str,
    reason: str,
    analysis_id: str | None = None,
    original_risk_score: int | None = None,
) -> dict[str, Any]:
    payload = {
        "message_text": message_text,
        "user_comment": reason,
        "analysis_id": analysis_id,
        "original_risk_score": original_risk_score,
    }
    response = requests.post(
        api_url("/api/report-false-positive"),
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    try:
        return response.json()
    except ValueError:
        return {"status": "success"}


# ---------------------------------------------------------------------
# SMS helper — extract signals client-side for display
# ---------------------------------------------------------------------
def parse_sms_locally(text: str) -> dict[str, Any]:
    """Light client-side SMS parsing for display only. Scoring is done by backend."""
    urls = list(set(re.findall(r"https?://[^\s<>\"'{}|\\^`]+", text)))
    phones = list(set(re.findall(
        r"(?:\+?91[\s\-]?)?[6-9]\d{9}|\b\d{5,6}\b", text
    )))
    lower = text.lower()
    urgency = [k for k in [
        "urgent", "immediately", "suspended", "blocked", "locked",
        "within 24 hours", "action required", "कट जाएगी", "ब्लॉक",
        "तुरंत", "अभी", "बंद", "jaldi", "turant",
    ] if k in lower or k in text]
    financial = any(k in lower for k in [
        "bank", "kyc", "otp", "upi", "account", "credit", "debit",
        "sbi", "hdfc", "icici", "paytm", "phonepe",
    ])
    delivery = any(k in lower for k in [
        "delivery", "package", "parcel", "courier", "tracking",
        "india post", "dtdc", "bluedart",
    ])
    category = "general"
    if financial:
        category = "banking"
    elif delivery:
        category = "delivery"
    elif any(k in lower for k in ["gov", "aadhaar", "pan", "income tax", "uidai", "trai"]):
        category = "government"
    return {
        "urls": urls,
        "phones": phones,
        "urgency_signals": urgency,
        "is_financial": financial,
        "is_delivery": delivery,
        "category": category,
        "char_count": len(text),
    }


# ---------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------
def safe_score(value: Any) -> int:
    try:
        score = int(value)
    except (TypeError, ValueError) as exc:
        raise RuntimeError("Backend returned an invalid risk score.") from exc
    if not 0 <= score <= 100:
        raise RuntimeError("Backend risk score is outside the expected 0–100 range.")
    return score


def highlight_message(message: str, evidence_items: list[dict[str, Any]]) -> str:
    quotes = []
    for item in evidence_items:
        if isinstance(item, dict):
            quote = item.get("quote")
            if isinstance(quote, str) and quote and quote in message:
                quotes.append(quote)
    quotes = sorted(set(quotes), key=len, reverse=True)
    if not quotes:
        return html.escape(message).replace("\n", "<br>")
    pattern = re.compile("|".join(re.escape(q) for q in quotes))
    output, cursor = [], 0
    for match in pattern.finditer(message):
        output.append(html.escape(message[cursor:match.start()]))
        output.append("<mark>" + html.escape(match.group(0)) + "</mark>")
        cursor = match.end()
    output.append(html.escape(message[cursor:]))
    return "".join(output).replace("\n", "<br>")


def render_analysis_result(data: dict) -> None:
    """Shared result renderer used by both the Message tab and SMS tab."""
    result = data["result"]
    try:
        score = safe_score(result["risk_score"])
    except RuntimeError as exc:
        score = None
        st.error(str(exc))

    tier = str(result.get("risk_tier", "Unknown"))
    style = TIER_STYLE.get(tier, {"color": "#9AAAC0", "soft": "rgba(154,170,192,.1)", "icon": "●"})

    if score is not None:
        st.markdown(
            f"""
            <div class="tl-risk" style="border-left:5px solid {style['color']}">
              <div class="tl-panel-label">RISK CLASSIFICATION</div>
              <div style="display:flex;align-items:flex-end;justify-content:space-between;gap:1rem;flex-wrap:wrap">
                <div>
                  <div style="font-size:1.55rem;font-weight:850;color:{style['color']}">
                    {style['icon']} {html.escape(tier)}
                  </div>
                  <div class="tl-muted" style="margin-top:.35rem">Backend-generated assessment</div>
                </div>
                <div style="text-align:right">
                  <div class="tl-risk-score" style="color:{style['color']}">{score}<span style="font-size:1rem;color:#91A2BC"> / 100</span></div>
                  <div class="tl-muted" style="font-size:.75rem;margin-top:.25rem">RISK SCORE</div>
                </div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.progress(score / 100)

    metric_a, metric_b = st.columns(2)
    with metric_a:
        st.metric("Detected language", str(result.get("language", "Not specified")))
    with metric_b:
        st.metric("Source channel", data["channel"].capitalize())

    summary = result.get("summary")
    if summary:
        st.markdown("#### Assessment summary")
        st.markdown(f'<div class="tl-panel">{html.escape(str(summary))}</div>', unsafe_allow_html=True)

    evidence = result.get("evidence_highlights") or []
    if not isinstance(evidence, list):
        evidence = []

    st.markdown("#### Evidence in the message")
    st.markdown(
        '<div class="tl-evidence">' +
        highlight_message(data["message_text"], evidence) +
        '</div>',
        unsafe_allow_html=True,
    )

    if evidence:
        st.markdown("#### Why these signals matter")
        for item in evidence:
            if not isinstance(item, dict):
                continue
            quote = str(item.get("quote", "Suspicious text"))
            evidence_type = str(item.get("type", "Suspicious indicator"))
            reason = str(item.get("reason", ""))
            st.markdown(
                f'<div class="tl-panel" style="padding:.85rem 1rem">'
                f'<div style="color:#63D8E8;font-size:.72rem;font-weight:800;letter-spacing:.1em;text-transform:uppercase">{html.escape(evidence_type)}</div>'
                f'<div style="font-weight:750;margin:.3rem 0">{html.escape(quote)}</div>'
                f'<div class="tl-muted">{html.escape(reason)}</div></div>',
                unsafe_allow_html=True,
            )
    else:
        st.success("No suspicious text indicators were highlighted by the backend.")

    recommended_action = result.get("recommended_action")
    if recommended_action:
        st.markdown("#### Recommended next step")
        st.info(str(recommended_action), icon="🛡️")

    with st.expander("View raw API response"):
        st.json(result)

    st.divider()
    st.markdown("#### Help improve TRUSTLENS")
    st.caption("If this result seems incorrect, send feedback to the backend.")
    feedback_reason = st.selectbox(
        "Feedback reason",
        [
            "This is a legitimate message (false alarm)",
            "This is a scam but the risk score is too low",
            "Wrong language or phrase detected",
            "Other",
        ],
        key=f"feedback_reason_{data.get('tab','main')}",
    )
    if st.button("↗  Submit feedback", use_container_width=True, key=f"fb_btn_{data.get('tab','main')}"):
        try:
            with st.spinner("Sending feedback…"):
                feedback_result = submit_feedback(
                    data["message_text"],
                    feedback_reason,
                    analysis_id=data["result"].get("analysis_id"),
                    original_risk_score=data["result"].get("risk_score"),
                )
            if feedback_result.get("status") == "success":
                st.success("Feedback recorded. Thank you.")
            else:
                st.success("Feedback submitted.")
        except requests.exceptions.ConnectionError:
            st.error("Cannot reach the backend. Check that FastAPI is running.")
        except requests.exceptions.Timeout:
            st.error("Feedback request timed out.")
        except requests.exceptions.HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else "unknown"
            st.error(f"Feedback was not accepted (HTTP {status}).")
        except requests.exceptions.RequestException as exc:
            st.error(f"Could not submit feedback: {exc}")


# ---------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------
if "api_base_url" not in st.session_state:
    st.session_state.api_base_url = DEFAULT_API_URL
if "message_text" not in st.session_state:
    st.session_state.message_text = ""
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None
if "sample_choice" not in st.session_state:
    st.session_state.sample_choice = ""
if "sms_text" not in st.session_state:
    st.session_state.sms_text = ""
if "sms_result" not in st.session_state:
    st.session_state.sms_result = None

samples = load_samples()


def load_selected_sample() -> None:
    selected = st.session_state.get("sample_choice", "")
    st.session_state.message_text = samples.get(selected, "")
    st.session_state.analysis_result = None


# ---------------------------------------------------------------------
# Page header
# ---------------------------------------------------------------------
st.markdown(
    """
    <div class="tl-hero">
      <div class="tl-kicker">TRUSTLENS / DIGITAL SAFETY INTELLIGENCE</div>
      <div class="tl-hero-title">See the threat. <span style="color:#63D8E8">Before you click.</span></div>
      <div class="tl-hero-sub">
        A privacy-first assistant for spotting phishing and social-engineering messages
        across SMS, WhatsApp and email — including Hindi and Hinglish.
      </div>
      <div style="margin-top:1rem">
        <span class="tl-pill">Links analysed as text · Never opened</span>
        &nbsp;
        <span class="tl-pill" style="border-color:rgba(155,140,255,.28);color:#9B8CFF;background:rgba(155,140,255,.07)">SMS Scanner · New</span>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------
with st.sidebar:
    st.markdown("## 🛡️ TRUSTLENS")
    st.caption("Frontend control centre")
    st.divider()
    st.markdown("#### Backend connection")
    st.text_input(
        "FastAPI base URL",
        key="api_base_url",
        help="Use http://localhost:8000 when the backend is running on this Mac.",
    )
    if st.button("↻ Check connection", use_container_width=True):
        ok, status_text = check_backend()
        st.session_state.backend_status = (ok, status_text)
    if "backend_status" in st.session_state:
        is_online, status_text = st.session_state.backend_status
        if is_online:
            st.success("● " + status_text)
        else:
            st.warning("● " + status_text)
    else:
        st.caption("Connection status has not been checked yet.")

    st.divider()
    st.markdown("#### API routes")
    st.code("GET  /health\nPOST /api/analyze\nPOST /api/report-false-positive", language="text")
    st.caption("The backend owns all scoring and risk-tier decisions.")
    st.divider()
    st.markdown("#### Safety reminder")
    st.caption(
        "Never share OTPs, UPI PINs or passwords. "
        "Verify requests through an official app or website. "
        "Report fraud: call **1930** or visit cybercrime.gov.in"
    )

# ---------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------
tab_message, tab_sms = st.tabs(["📨  Message Scanner", "📱  SMS Scanner"])

# =====================================================================
# TAB 1 — original message scanner (unchanged behaviour)
# =====================================================================
with tab_message:
    input_col, report_col = st.columns([0.94, 1.06], gap="large")

    with input_col:
        st.markdown('<div class="tl-panel-label">01 / MESSAGE INPUT</div>', unsafe_allow_html=True)
        st.markdown("### Inspect a message")
        st.markdown('<p class="tl-muted">Paste the message exactly as you received it.</p>', unsafe_allow_html=True)

        st.selectbox(
            "Load a test scenario",
            options=[""] + list(samples.keys()),
            key="sample_choice",
            on_change=load_selected_sample,
            format_func=lambda value: "Choose a sample message…" if value == "" else value,
        )
        channel_label = st.selectbox("Message source", list(CHANNELS.keys()), index=0)
        st.text_area(
            "Message content",
            key="message_text",
            height=245,
            placeholder="Example: Your bank account will be blocked. Update KYC now…",
            help="Paste text only. Do not open suspicious links.",
            label_visibility="visible",
        )
        count = len(st.session_state.message_text)
        st.markdown(
            f'<p class="tl-muted" style="text-align:right;font-size:.75rem">{count:,} characters</p>',
            unsafe_allow_html=True,
        )

        scan_clicked = st.button("⌕  Analyse message", type="primary", use_container_width=True, key="scan_main")
        st.caption("Your message is sent to the configured backend for analysis.")

        if scan_clicked:
            submitted_text = st.session_state.message_text.strip()
            if not submitted_text:
                st.warning("Paste a message or select a sample before scanning.")
            else:
                with st.spinner("Analysing message signals…"):
                    try:
                        result = analyze_message(submitted_text, CHANNELS[channel_label])
                        st.session_state.analysis_result = {
                            "message_text": submitted_text,
                            "channel": CHANNELS[channel_label],
                            "result": result,
                            "tab": "main",
                        }
                    except ValueError as exc:
                        st.session_state.analysis_result = None
                        st.error(f"Invalid request: {exc}")
                    except requests.exceptions.ConnectionError:
                        st.session_state.analysis_result = None
                        st.error(
                            "Cannot reach FastAPI. Check that the backend is running and "
                            f"that the URL is correct: {st.session_state.api_base_url}"
                        )
                    except requests.exceptions.Timeout:
                        st.session_state.analysis_result = None
                        st.error("The analysis request timed out. Please try again.")
                    except requests.exceptions.HTTPError as exc:
                        st.session_state.analysis_result = None
                        status = exc.response.status_code if exc.response is not None else "unknown"
                        st.error(f"Backend returned HTTP {status}. Check the backend logs.")
                    except (requests.exceptions.RequestException, RuntimeError) as exc:
                        st.session_state.analysis_result = None
                        st.error(f"Analysis failed: {exc}")

    with report_col:
        st.markdown('<div class="tl-panel-label">02 / THREAT ASSESSMENT</div>', unsafe_allow_html=True)
        st.markdown("### Analysis report")
        data = st.session_state.analysis_result

        if not data:
            st.markdown(
                """
                <div class="tl-panel" style="min-height:230px;display:flex;flex-direction:column;justify-content:center">
                  <div style="font-size:2rem;margin-bottom:.55rem">◈</div>
                  <div style="font-size:1.08rem;font-weight:750">Your report will appear here</div>
                  <p class="tl-muted" style="margin:.35rem 0 0 0">
                    Submit a message to see its risk tier, exact evidence and recommended next steps.
                  </p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown("#### What TRUSTLENS looks for")
            check_a, check_b = st.columns(2)
            with check_a:
                st.markdown("**⌁ Suspicious links**")
                st.caption("Unusual domains and link patterns")
                st.markdown("**◷ Artificial urgency**")
                st.caption("Threats, countdowns and pressure")
            with check_b:
                st.markdown("**◎ Sensitive requests**")
                st.caption("OTP, KYC and account verification")
                st.markdown("**文 Regional context**")
                st.caption("Hindi, Hinglish and local scam cues")
        else:
            render_analysis_result(data)


# =====================================================================
# TAB 2 — SMS Scanner with Verification Assistant
# =====================================================================
with tab_sms:
    st.markdown('<div class="tl-panel-label">SMS SCANNER + VERIFICATION ASSISTANT</div>', unsafe_allow_html=True)
    st.markdown("### Scan an SMS")
    st.markdown(
        '<p class="tl-muted">Paste an SMS exactly as you received it. '
        'The scanner extracts signals and sends the text to the backend for a full risk assessment. '
        'Links are never opened.</p>',
        unsafe_allow_html=True,
    )

    sms_col, sms_report_col = st.columns([0.94, 1.06], gap="large")

    with sms_col:
        # Quick-paste presets
        SMS_PRESETS = {
            "Jio lottery · Hindi": "बधाई हो! आपने Jio लकी ड्रा में ₹1,00,000 जीते हैं। क्लेम करने के लिए: jio-winner-prize.com",
            "PAN-Aadhaar threat · Hindi": "ध्यान दें! आपका पैन कार्ड आधार से लिंक नहीं है, कल से बैंक खाता बंद। अभी लिंक करें: aadhar-pan-link.com",
            "Bijli cut-off · Hinglish": "Aapki bijli kal raat tak kat jayegi! Abhi bill pay karo: bit.ly/bijli-pay",
            "SBI KYC · English": "URGENT: Your SBI account has been locked. Verify KYC at http://sbi-kyc-update.xyz within 2 hours.",
            "Safe OTP · English": "Your SBI OTP for transaction of Rs. 500 is 847291. Do not share this with anyone.",
        }

        def on_preset_change():
            chosen = st.session_state.sms_preset
            if chosen:
                st.session_state.sms_input_area = SMS_PRESETS[chosen]
                st.session_state.sms_result = None

        st.selectbox(
            "Load a preset SMS",
            options=[""] + list(SMS_PRESETS.keys()),
            format_func=lambda x: "Choose a preset…" if x == "" else x,
            key="sms_preset",
            on_change=on_preset_change,
        )

        if "sms_input_area" not in st.session_state:
            st.session_state.sms_input_area = ""

        sms_input = st.text_area(
            "SMS content",
            height=200,
            placeholder="Paste your SMS here…",
            key="sms_input_area",
        )
        st.markdown(
            f'<p class="tl-muted" style="text-align:right;font-size:.75rem">{len(sms_input):,} / 1600 characters</p>',
            unsafe_allow_html=True,
        )

        # Show extracted signals before scanning
        if sms_input.strip():
            parsed = parse_sms_locally(sms_input)
            if parsed["urls"] or parsed["urgency_signals"] or parsed["phones"]:
                with st.expander("🔍 Pre-scan signal preview", expanded=False):
                    if parsed["urls"]:
                        st.markdown(f"**Links found:** {len(parsed['urls'])}")
                        for u in parsed["urls"]:
                            st.code(u)
                    if parsed["urgency_signals"]:
                        st.markdown(f"**Urgency triggers:** `{'`, `'.join(parsed['urgency_signals'])}`")
                    if parsed["phones"]:
                        st.markdown(f"**Phone numbers:** `{'`, `'.join(parsed['phones'])}`")

        sms_scan_clicked = st.button(
            "⌕  Scan SMS",
            type="primary",
            use_container_width=True,
            key="scan_sms",
        )
        st.caption("Text is sent to the backend for analysis. Links are never opened.")

        if sms_scan_clicked:
            sms_text = sms_input.strip()
            st.session_state.sms_text = sms_text
            if not sms_text:
                st.warning("Paste an SMS or choose a preset before scanning.")
            else:
                with st.spinner("Scanning SMS…"):
                    try:
                        result = analyze_message(sms_text, "sms")
                        st.session_state.sms_result = {
                            "message_text": sms_text,
                            "channel": "sms",
                            "result": result,
                            "tab": "sms",
                            "parsed": parse_sms_locally(sms_text),
                        }
                    except ValueError as exc:
                        st.session_state.sms_result = None
                        st.error(f"Invalid request: {exc}")
                    except requests.exceptions.ConnectionError:
                        st.session_state.sms_result = None
                        st.error("Cannot reach the backend. Check the connection in the sidebar.")
                    except requests.exceptions.Timeout:
                        st.session_state.sms_result = None
                        st.error("Request timed out. Try again.")
                    except (requests.exceptions.RequestException, RuntimeError) as exc:
                        st.session_state.sms_result = None
                        st.error(f"Scan failed: {exc}")

    with sms_report_col:
        sms_data = st.session_state.sms_result

        if not sms_data:
            st.markdown(
                """
                <div class="tl-panel" style="min-height:200px;display:flex;flex-direction:column;justify-content:center">
                  <div style="font-size:2rem;margin-bottom:.55rem">📱</div>
                  <div style="font-size:1.08rem;font-weight:750">SMS scan results will appear here</div>
                  <p class="tl-muted" style="margin:.35rem 0 0 0">
                    Paste an SMS and click Scan SMS to get a full risk assessment plus
                    safe verification steps tailored for India.
                  </p>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            # Risk result
            render_analysis_result(sms_data)

            # Verification Assistant
            st.divider()
            st.markdown("### 🛡️ Verification Assistant")
            st.markdown(
                '<p class="tl-muted">Independent steps to verify this message safely — without clicking any link.</p>',
                unsafe_allow_html=True,
            )

            parsed = sms_data.get("parsed", {})
            category = parsed.get("category", "general")
            score = sms_data["result"].get("risk_score", 0)
            tier = sms_data["result"].get("risk_tier", "Low Risk")

            # What to avoid
            avoid_list = [
                "❌ DO NOT click any link inside the message.",
                "❌ DO NOT call any number listed in the message.",
                "❌ DO NOT share your OTP, UPI PIN, or Aadhaar number.",
            ]
            if category == "banking":
                avoid_list.append("❌ DO NOT transfer money to any 'safe account'.")
                avoid_list.append("❌ DO NOT share your net banking password or CVV.")
            elif category == "delivery":
                avoid_list.append("❌ DO NOT pay any 'redelivery fee' through a message link.")
            elif category == "government":
                avoid_list.append("❌ DO NOT pay fines via gift cards or crypto.")

            if score >= 30:
                st.markdown("#### What to avoid")
                for item in avoid_list:
                    st.markdown(item)

            # Independent verification steps
            if score >= 30:
                st.markdown("#### How to verify independently")
                if category == "banking":
                    st.markdown("1. **Call the number on the back of your bank card** — not any number in the message.")
                    st.markdown("2. **Open your official bank app** directly from your phone's home screen.")
                    st.markdown("3. **Check your account** in the app for any actual alerts.")
                elif category == "delivery":
                    st.markdown("1. **Copy only the tracking number** from the message (not the link).")
                    st.markdown("2. **Go directly to the carrier's website** by typing it manually in your browser.")
                    st.markdown("3. **Paste the tracking number** in the official site's search box.")
                elif category == "government":
                    st.markdown("1. **Search for the official government portal** using Google.")
                    st.markdown("2. **Look for `.gov.in` domains only** — these are genuine.")
                    st.markdown("3. **Call 1930** to report cyber fraud.")
                else:
                    st.markdown("1. **Search for the sender's official contact** using Google.")
                    st.markdown("2. **Call their official helpline** to verify the message.")
                    st.markdown("3. **Never act on urgency** — real organisations give you time.")

            # Safe verification links
            st.markdown("#### Safe official resources")
            resources = INDIA_VERIFICATION.get(category, INDIA_VERIFICATION["general"])
            cols = st.columns(2)
            for i, resource in enumerate(resources):
                with cols[i % 2]:
                    st.markdown(
                        f'<div class="tl-verify-card">'
                        f'<div style="font-weight:750;font-size:.9rem">{html.escape(resource["name"])}</div>'
                        f'<div class="tl-muted" style="font-size:.78rem">{html.escape(resource["domain"])}</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

            # Report guidance
            st.markdown("#### Report this SMS")
            report_a, report_b = st.columns(2)
            with report_a:
                st.info("📱 Forward to **1909** to report spam SMS to TRAI's DND registry.", icon="📨")
            with report_b:
                st.info("🚨 Report cyber fraud at **cybercrime.gov.in** or call **1930**.", icon="🚨")


# ---------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------
st.markdown(
    """
    <div class="tl-foot">
      <b>TRUSTLENS</b> · Explainable phishing and social-engineering detection for Indian users<br>
      Stay cautious. Never share your OTP, UPI PIN or password. If you lose money to cyber fraud in India,
      call <b>1930</b> or report it at <b>cybercrime.gov.in</b>.
    </div>
    """,
    unsafe_allow_html=True,
)
