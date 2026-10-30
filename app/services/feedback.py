"""Stores user challenge reports as JSON lines.

Owner: teammate A.
"""
import json
import os
from datetime import datetime, timezone

FEEDBACK_PATH = os.getenv("FEEDBACK_PATH", "data/feedback.jsonl")


def save_feedback(record: dict) -> None:
    os.makedirs(os.path.dirname(FEEDBACK_PATH) or ".", exist_ok=True)
    entry = {"received_at": datetime.now(timezone.utc).isoformat(), **record}
    with open(FEEDBACK_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
