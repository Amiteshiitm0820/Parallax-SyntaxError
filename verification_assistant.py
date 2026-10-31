"""
TRUSTLENS - Verification Assistant (Python Drop-in)

Generates safe verification guidance for suspicious messages.
Never automatically opens links or contacts third parties.
"""

import re
from typing import Dict, Any, List

class VerificationAssistant:
    def __init__(self):
        self.verified_directories = {
            "banking": [
                {"name": "Card Back Helpline", "advice": "Call the phone number printed on the back of your physical card."},
                {"name": "Official Bank App", "advice": "Open your mobile banking app directly from your phone's home screen."}
            ],
            "delivery": [
                {"name": "USPS Official Tracking", "domain": "https://www.usps.com", "trackingUrl": "https://tools.usps.com/go/TrackConfirmAction"},
                {"name": "FedEx Official Portal", "domain": "https://www.fedex.com", "trackingUrl": "https://www.fedex.com/en-us/tracking.html"},
                {"name": "UPS Official Portal", "domain": "https://www.ups.com", "trackingUrl": "https://www.ups.com/track"}
            ],
            "government": [
                {"name": "USA.gov Official Portal", "domain": "https://www.usa.gov"},
                {"name": "IRS Official Website", "domain": "https://www.irs.gov"},
                {"name": "FTC Fraud Reporting", "domain": "https://reportfraud.ftc.gov"}
            ]
        }

    def generate_guidance(self, text: str, sender: str = "", msg_type: str = "sms", extracted_urls: List[str] = None, detection_result: Dict[str, Any] = None) -> Dict[str, Any]:
        extracted_urls = extracted_urls or []
        detection_result = detection_result or {}

        category = self._detect_category(text, sender)
        why_suspicious = self._analyze_signals(text, sender, msg_type, extracted_urls, detection_result)
        what_to_avoid = self._get_avoid_list(category, msg_type)
        independent_steps = self._get_independent_steps(category)
        next_steps = self._get_next_steps(msg_type)

        return {
            "category": category["name"],
            "categoryId": category["id"],
            "whySuspicious": why_suspicious,
            "whatToAvoid": what_to_avoid,
            "howToIndependentlyVerify": independent_steps,
            "recommendedNextSteps": next_steps,
            "safeVerificationTools": {
                "disclaimer": "TRUSTLENS never automatically follows suspicious links. Use these verified official directories.",
                "officialDirectories": self.verified_directories.get(category["id"], [])
            }
        }

    def _detect_category(self, text: str, sender: str) -> Dict[str, str]:
        comb = f"{sender} {text}".lower()
        if re.search(r"(bank|chase|wells fargo|citi|bofa|paypal|venmo|credit card|debit card|unauthorized charge|wire transfer|account locked)", comb):
            return {"id": "banking", "name": "Financial & Banking Scam"}
        if re.search(r"(delivery|package|parcel|shipment|courier|tracking|usps|fedex|ups|dhl|redelivery)", comb):
            return {"id": "delivery", "name": "Parcel & Delivery Smishing"}
        if re.search(r"(irs|tax refund|social security|ssa|gov|dmv|court|warrant|fine)", comb):
            return {"id": "government", "name": "Government Impersonation Scam"}
        return {"id": "general", "name": "Suspicious Phishing / Smishing"}

    def _analyze_signals(self, text: str, sender: str, msg_type: str, urls: List[str], detection: Dict[str, Any]) -> List[Dict[str, str]]:
        signals = []
        if re.search(r"(immediate|urgent|within (?:24|12|48) hours|suspended|blocked)", text, re.I):
            signals.append({
                "title": "Artificial Urgency Pressure",
                "detail": "Scammers fabricate imminent deadlines to induce panic before you can independently check."
            })
        if urls:
            signals.append({
                "title": "Unverified Hyperlinks",
                "detail": f"Contains {len(urls)} link(s) that may redirect to lookalike harvesting websites."
            })
        if re.search(r"(otp|pin|password|passcode|ssn)", text, re.I):
            signals.append({
                "title": "Credential Solicitation",
                "detail": "Legitimate organizations never ask for one-time passwords or credentials over SMS/email."
            })
        if not signals:
            signals.append({
                "title": "Unsolicited Communication Patterns",
                "detail": "Message language matches common fraudulent patterns."
            })
        return signals

    def _get_avoid_list(self, category: Dict[str, str], msg_type: str) -> List[str]:
        avoid = [
            "❌ DO NOT click on any link or button inside the message.",
            "❌ DO NOT call any phone number listed inside the message text."
        ]
        if category["id"] == "banking":
            avoid.append("❌ DO NOT share your OTP, PIN, card details, or internet banking password.")
            avoid.append("❌ DO NOT transfer money to any 'safe holding account'.")
        elif category["id"] == "delivery":
            avoid.append("❌ DO NOT pay any 'redelivery fee' or 'customs fee' via the message link.")
        elif category["id"] == "government":
            avoid.append("❌ DO NOT buy gift cards or crypto to settle alleged legal fines.")
        if msg_type == "email":
            avoid.append("❌ DO NOT download or open any attachments.")
        return avoid

    def _get_independent_steps(self, category: Dict[str, str]) -> List[Dict[str, Any]]:
        if category["id"] == "banking":
            return [
                {"step": 1, "title": "Check Card Back", "action": "Call the phone number printed on the back of your genuine bank card."},
                {"step": 2, "title": "Launch Mobile App", "action": "Open your official banking app directly from your smartphone home screen."}
            ]
        elif category["id"] == "delivery":
            return [
                {"step": 1, "title": "Copy Tracking ID Only", "action": "Copy only the tracking number string without clicking the link."},
                {"step": 2, "title": "Visit Carrier Directly", "action": "Type usps.com or fedex.com into your browser and search the tracking number there."}
            ]
        return [
            {"step": 1, "title": "Search Official Directory", "action": "Search for the organization using a verified official portal or directory."}
        ]

    def _get_next_steps(self, msg_type: str) -> List[str]:
        if msg_type == "sms":
            return [
                "📱 Forward the SMS to 7726 (SPAM) to notify your mobile carrier.",
                "🚫 Block the sender number.",
                "🗑️ Delete the message thread."
            ]
        return [
            "🚨 Mark as Phishing in your email client.",
            "📧 Report to reportphishing@apwg.org.",
            "🚫 Block the sender domain."
        ]
