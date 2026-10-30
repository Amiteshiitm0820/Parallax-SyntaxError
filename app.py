"""
TRUSTLENS - app.py  (Person 4: Frontend & UI)

Run with:  streamlit run app.py

This file ONLY does presentation. It calls:
  extractor.extract_signals(text) -> dict          (Person 2)
  scorer.calculate_score(signals) -> dict          (Person 3)
  scorer.save_feedback(text, reason)               (Person 3)
and reads samples from data_config.py / dataset.json (Person 1).

If a teammate's file is not ready yet, the app falls back to a tiny
DEMO stub so you can keep building the UI. A yellow banner tells you when.
"""

import html
import json
import re
from pathlib import Path

import streamlit as st

# --------------------------------------------------------------------------
# 1. Import teammates' code (with safe fallbacks so the UI never crashes)
# --------------------------------------------------------------------------
USING_STUB_EXTRACTOR = False
USING_STUB_SCORER = False

try:
    from extractor import extract_signals
except Exception:
    USING_STUB_EXTRACTOR = True

    def extract_signals(text: str) -> dict:
        urls = re.findall(r"https?://[^\s]+|\b[\w-]+\.(?:com|in|co\.in|xyz|ly)/?\S*", text)
        urgency = [w for w in ["blocked", "KYC", "OTP", "urgent", "कट जाएगी", "ब्लॉक"]
                   if w.lower() in text.lower()]
        return {"urls": urls, "urgency_phrases": urgency}

try:
    from scorer import calculate_score, save_feedback
except Exception:
    USING_STUB_SCORER = True

    def calculate_score(signals: dict) -> dict:
        score = min(100, 25 * len(signals.get("urgency_phrases", []))
                    + 30 * len(signals.get("urls", [])))
        tier = "High" if score >= 70 else "Medium" if score >= 30 else "Low"
        return {
            "score": score,
            "tier": tier,
            "evidence": signals.get("urgency_phrases", []) + signals.get("urls", []),
            "reasons": ["DEMO stub - real scorer.py not connected yet"],
            "steps": ["Do not click any link.", "Open the official app yourself."],
        }

    def save_feedback(text: str, reason: str):
        Path("feedback_demo.json").write_text(
            json.dumps({"text": text, "reason": reason}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

# --------------------------------------------------------------------------
# 2. Load sample messages (Person 1's data, with fallbacks)
# --------------------------------------------------------------------------
FALLBACK_SAMPLES = {
    "SBI KYC (English SMS)": "Dear customer, your SBI account will be blocked today. "
                             "Complete KYC now: http://sbi-kyc-verify.com/update",
    "Bijli bill (Hinglish SMS)": "Aapki bijli kal raat tak kat jayegi! Abhi bill pay karo: "
                                 "bit.ly/pay-bijli-now",
    "Bank alert (Hindi SMS)": "आपका खाता ब्लॉक हो जाएगा। अभी KYC अपडेट करें और OTP साझा करें: "
                              "http://hdfc-secure-login.xyz",
    "Normal message (safe)": "Hi, your Amazon order has been delivered. "
                             "Track it in the official Amazon app.",
}


def _normalize(items) -> dict:
    """Accept a list of strings / dicts, or a dict, and return {label: text}."""
    out = {}
    if isinstance(items, dict):
        items = [{"label": k, "text": v} for k, v in items.items()]
    for i, item in enumerate(items, 1):
        if isinstance(item, str):
            out[f"Sample {i}"] = item
        elif isinstance(item, dict):
            text = item.get("text") or item.get("message") or item.get("body") or item.get("content")
            label = item.get("label") or item.get("title") or item.get("name") or f"Sample {i}"
            if text:
                out[f"{i}. {label}"] = text
    return out


def load_samples() -> dict:
    # a) data_config.py - tries common variable names
    try:
        import data_config
        for name in ("SAMPLES", "SAMPLE_MESSAGES", "DATASET", "DATA", "SAMPLE_DATA", "MESSAGES"):
            if hasattr(data_config, name):
                samples = _normalize(getattr(data_config, name))
                if samples:
                    return samples
    except Exception:
        pass
    # b) dataset.json
    try:
        data = json.loads(Path("dataset.json").read_text(encoding="utf-8"))
        samples = _normalize(data)
        if samples:
            return samples
    except Exception:
        pass
    # c) built-in fallback
    return FALLBACK_SAMPLES


# --------------------------------------------------------------------------
# 3. Helpers for displaying results
# --------------------------------------------------------------------------
TIER_STYLE = {
    "High": ("#d32f2f", "🔴"),
    "Medium": ("#f57c00", "🟠"),
    "Low": ("#2e7d32", "🟢"),
}


def as_text_list(items) -> list:
    """Turn evidence (strings or dicts) into a flat list of strings."""
    out = []
    for it in items or []:
        if isinstance(it, str):
            out.append(it)
        elif isinstance(it, dict):
            val = it.get("phrase") or it.get("text") or it.get("evidence") or it.get("match")
            if val:
                out.append(str(val))
    return out


def highlight(text: str, phrases: list) -> str:
    """Return HTML with evidence phrases highlighted (text is escaped first = safe)."""
    safe = html.escape(text)
    for p in sorted(set(phrases), key=len, reverse=True):
        if not p:
            continue
        pattern = re.compile(re.escape(html.escape(p)), re.IGNORECASE)
        safe = pattern.sub(
            lambda m: f"<mark style='background:#ffe082;padding:0 3px;border-radius:3px'>{m.group(0)}</mark>",
            safe,
        )
    return safe.replace("\n", "<br>")


# --------------------------------------------------------------------------
# 4. Page setup
# --------------------------------------------------------------------------
st.set_page_config(page_title="TrustLens", page_icon="🛡️", layout="wide")

st.title("🛡️ TrustLens")
st.caption("Privacy-first phishing scanner for English, हिन्दी & Hinglish messages. "
           "Links are analysed as text only - never opened.")

if USING_STUB_EXTRACTOR or USING_STUB_SCORER:
    missing = [n for n, s in (("extractor.py", USING_STUB_EXTRACTOR), ("scorer.py", USING_STUB_SCORER)) if s]
    st.warning(f"⚠️ DEMO MODE: could not import {', '.join(missing)}. Using placeholder logic.")

samples = load_samples()

if "msg" not in st.session_state:
    st.session_state.msg = ""
if "result" not in st.session_state:
    st.session_state.result = None


def on_sample_change():
    choice = st.session_state.sample_choice
    st.session_state.msg = samples.get(choice, "")
    st.session_state.result = None


# --------------------------------------------------------------------------
# 5. Layout: input (left)  |  results (right)
# --------------------------------------------------------------------------
left, right = st.columns([1, 1.2], gap="large")

with left:
    st.subheader("1. Paste a suspicious message")
    st.selectbox(
        "Or load a sample",
        options=[""] + list(samples.keys()),
        key="sample_choice",
        on_change=on_sample_change,
        format_func=lambda x: "— choose a sample —" if x == "" else x,
    )
    st.text_area("Message (SMS / Email)", key="msg", height=220,
                 placeholder="Paste the message here...")

    if st.button("🔍 Scan message", type="primary", use_container_width=True):
        text = st.session_state.msg.strip()
        if not text:
            st.error("Please paste or select a message first.")
        else:
            try:
                signals = extract_signals(text)
                result = calculate_score(signals)
                st.session_state.result = {"text": text, "signals": signals, "score": result}
            except Exception as e:
                st.session_state.result = None
                st.error(f"Something went wrong while scanning: {e}")

with right:
    st.subheader("2. Result")
    data = st.session_state.result

    if not data:
        st.info("Scan a message to see the risk tier, evidence and safety steps.")
    else:
        res = data["score"]
        score = int(res.get("score", 0))
        tier = res.get("tier", "Low")
        color, icon = TIER_STYLE.get(tier, TIER_STYLE["Low"])

        # Risk card
        st.markdown(
            f"""
            <div style="border-left:8px solid {color};background:{color}15;
                        padding:16px 20px;border-radius:8px;margin-bottom:12px">
              <div style="font-size:14px;color:#555">RISK TIER</div>
              <div style="font-size:34px;font-weight:700;color:{color}">{icon} {tier.upper()}</div>
              <div style="font-size:16px">Risk score: <b>{score}/100</b></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.progress(min(max(score, 0), 100) / 100)

        # Evidence highlighting
        evidence = as_text_list(res.get("evidence"))
        signals = data["signals"]
        extra = as_text_list(signals.get("urgency_phrases")) + as_text_list(signals.get("urls"))
        st.markdown("**🔎 Evidence found in the message**")
        st.markdown(
            f"<div style='padding:12px;border:1px solid #ddd;border-radius:8px'>"
            f"{highlight(data['text'], evidence + extra)}</div>",
            unsafe_allow_html=True,
        )

        if evidence:
            st.markdown("**Cited signals:**")
            for e in evidence:
                st.markdown(f"- `{e}`")

        reasons = as_text_list(res.get("reasons"))
        if reasons:
            st.markdown("**Why this tier?**")
            for r in reasons:
                st.markdown(f"- {r}")

        # Safety guidance
        steps = as_text_list(res.get("steps") or res.get("guidance") or res.get("actions"))
        if steps:
            st.markdown("**✅ What to do now**")
            for s in steps:
                st.markdown(f"- {s}")

        with st.expander("Raw extracted signals (for judges / debugging)"):
            st.json(signals)

        # Challenge loop
        st.divider()
        st.markdown("**Think this result is wrong?**")
        reason = st.selectbox(
            "Reason",
            ["This is a legitimate message (false alarm)",
             "This is a scam but risk is too low",
             "Wrong language / phrase detected",
             "Other"],
            key="fb_reason",
        )
        if st.button("🚩 Challenge this result"):
            try:
                save_feedback(data["text"], reason)
                st.success("Thanks! Your feedback was saved and will help refine our rules.")
            except Exception as e:
                st.error(f"Could not save feedback: {e}")

st.divider()
st.caption("TrustLens • deterministic & explainable • no links are ever opened • "
           "Never share OTPs. Report fraud: call 1930 or visit cybercrime.gov.in")
