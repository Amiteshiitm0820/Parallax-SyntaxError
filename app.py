"""TRUSTLENS — polished Streamlit frontend (Person 4: UI & Pitch Deck Lead)

Run:
    python -m pip install streamlit requests
    streamlit run app.py

The frontend sends messages to FastAPI. Risk scores and tiers are supplied by
the backend; this file does not calculate them.
"""

from __future__ import annotations

import html
import os
import json
import re
from pathlib import Path
from typing import Any

import requests
import streamlit as st
REQUEST_TIMEOUT = 30

# ---------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------
st.set_page_config(
    page_title="TRUSTLENS | Message Security",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

DEFAULT_API_URL = os.getenv(
    "API_BASE_URL",
    "http://localhost:8000"
)
QUEST_TIMEOUT = 30

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

        # Standard phishing and safe messages (25)
        for item in data_config.MESSAGES_DATASET:
            label = (
                f"{item['id']} · {item['type'].capitalize()} "
                f"· {item['lang'].capitalize()}"
            )
            samples[label] = item["text"]

        # Extended threat scenarios (15)
        for item in data_config.EXTENDED_DATASET:
            label = (
                f"{item['id']} · Extended · {item['type'].capitalize()} "
                f"· {item['lang'].capitalize()}"
            )
            samples[label] = item["text"]

        # Obfuscated edge cases (10)
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
        "risk_score", "risk_tier", "language", "summary",
        "evidence_highlights", "recommended_action",
    )
    missing = [field for field in required if field not in payload]
    if missing:
        raise RuntimeError("Backend response is missing: " + ", ".join(missing))
    return payload


def submit_feedback(message_text: str, reason: str) -> dict[str, Any]:
    # Confirm the exact field names with the backend lead if their request model differs.
    response = requests.post(
        api_url("/api/report-false-positive"),
        json={"message_text": message_text, "reason": reason},
        headers={"Content-Type": "application/json"},
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    try:
        return response.json()
    except ValueError:
        return {"status": "success"}


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
    """Highlight only exact evidence quotes returned by the backend."""
    quotes = []
    for item in evidence_items:
        if isinstance(item, dict):
            quote = item.get("quote")
            if isinstance(quote, str) and quote and quote in message:
                quotes.append(quote)

    quotes = sorted(set(quotes), key=len, reverse=True)
    if not quotes:
        return html.escape(message).replace("\n", "<br>")

    pattern = re.compile("|".join(re.escape(quote) for quote in quotes))
    output, cursor = [], 0
    for match in pattern.finditer(message):
        output.append(html.escape(message[cursor:match.start()]))
        output.append("<mark>" + html.escape(match.group(0)) + "</mark>")
        cursor = match.end()
    output.append(html.escape(message[cursor:]))
    return "".join(output).replace("\n", "<br>")


# ---------------------------------------------------------------------
# Session state and page header
# ---------------------------------------------------------------------
if "api_base_url" not in st.session_state:
    st.session_state.api_base_url = DEFAULT_API_URL
if "message_text" not in st.session_state:
    st.session_state.message_text = ""
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None
if "sample_choice" not in st.session_state:
    st.session_state.sample_choice = ""

samples = load_samples()


def load_selected_sample() -> None:
    selected = st.session_state.get("sample_choice", "")
    st.session_state.message_text = samples.get(selected, "")
    st.session_state.analysis_result = None


st.markdown(
    """
    <div class="tl-hero">
      <div class="tl-kicker">TRUSTLENS / DIGITAL SAFETY INTELLIGENCE</div>
      <div class="tl-hero-title">See the threat. <span style="color:#63D8E8">Before you click.</span></div>
      <div class="tl-hero-sub">
        A privacy-first assistant for spotting phishing and social-engineering messages
        across SMS, WhatsApp and email — including Hindi and Hinglish.
      </div>
      <div style="margin-top:1rem"><span class="tl-pill">Links analysed as text · Never opened</span></div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------
# Sidebar: connection controls
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
    st.markdown("#### Safety reminder")
    st.caption("Never share OTPs, UPI PINs or passwords. Verify requests through an official app or website.")

# ---------------------------------------------------------------------
# Main two-column workspace
# ---------------------------------------------------------------------
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

    scan_clicked = st.button("⌕  Analyse message", type="primary", use_container_width=True)
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
            key="feedback_reason",
        )
        if st.button("↗  Submit feedback", use_container_width=True):
            try:
                with st.spinner("Sending feedback…"):
                    feedback_result = submit_feedback(data["message_text"], feedback_reason)
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
                st.error(f"Feedback was not accepted (HTTP {status}). Confirm the feedback API contract.")
            except requests.exceptions.RequestException as exc:
                st.error(f"Could not submit feedback: {exc}")

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
