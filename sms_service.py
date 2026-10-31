"""
TRUSTLENS - SMS Integration Service (Python Drop-in)

Handles SMS parsing, entity extraction, and Android Web Share payload handling.
Read-only: Never sends or deletes messages.
"""

import re
from datetime import datetime
from typing import Dict, Any, List, Union

class SmsService:
    def parse_sms(self, input_data: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
        raw_text = ""
        manual_sender = ""
        timestamp = datetime.utcnow().isoformat()

        if isinstance(input_data, str):
            raw_text = input_data.strip()
        elif isinstance(input_data, dict):
            raw_text = (input_data.get("text") or input_data.get("message") or input_data.get("body") or "").strip()
            manual_sender = (input_data.get("sender") or input_data.get("from") or "").strip()
            if input_data.get("timestamp"):
                timestamp = input_data["timestamp"]

        if not raw_text:
            raise ValueError("SMS text cannot be empty.")

        clean_body = raw_text
        detected_sender = manual_sender

        # Check for embedded headers like "From: +1555..." or "Sender: ..."
        sender_match = re.match(r"^(?:From|Sender|Source):\s*([^\n\r]+)[\r\n]+", raw_text, re.I)
        if sender_match:
            detected_sender = detected_sender or sender_match.group(1).strip()
            clean_body = raw_text[len(sender_match.group(0)):].strip()

        # Check alphanumeric header e.g. "VK-HDFCBK: Alert..."
        alpha_match = re.match(r"^([A-Z]{2}-[A-Za-z0-9]{5,8}):\s*(.*)$", clean_body, re.S)
        if alpha_match and not detected_sender:
            detected_sender = alpha_match.group(1)
            clean_body = alpha_match.group(2).strip()

        urls = list(set(re.findall(r"https?://[^\s<>\"'{}|\\^`]+", clean_body)))
        phones = list(set(re.findall(r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}|\b\d{5,6}\b", clean_body)))

        lower = clean_body.lower()
        urgency_terms = [k for k in ['urgent', 'immediately', 'suspended', 'blocked', 'locked', 'within 24 hours', 'action required'] if k in lower]
        financial = any(k in lower for k in ['bank', 'account', 'credit card', 'debit card', 'wire', 'debited', 'refund', 'tax', 'irs'])
        delivery = any(k in lower for k in ['delivery', 'package', 'parcel', 'usps', 'fedex', 'ups', 'dhl', 'tracking', 'redelivery'])

        return {
            "type": "sms",
            "rawText": raw_text,
            "cleanBody": clean_body,
            "sender": detected_sender or "Unknown / Not Provided",
            "timestamp": timestamp,
            "charCount": len(clean_body),
            "extractedUrls": urls,
            "extractedPhoneNumbers": phones,
            "indicators": {
                "urgencySignals": urgency_terms,
                "mentionsFinancial": financial,
                "mentionsDelivery": delivery
            }
        }

    def handle_android_share(self, share_dict: Dict[str, Any]) -> Dict[str, Any]:
        parts = []
        if share_dict.get("title") and share_dict["title"] not in share_dict.get("text", ""):
            parts.append(f"Header: {share_dict['title']}")
        if share_dict.get("text"):
            parts.append(share_dict["text"])
        if share_dict.get("url") and share_dict["url"] not in share_dict.get("text", ""):
            parts.append(share_dict["url"])
        
        return self.parse_sms({
            "text": "\n".join(parts).strip(),
            "sender": share_dict.get("title", "")
        })
