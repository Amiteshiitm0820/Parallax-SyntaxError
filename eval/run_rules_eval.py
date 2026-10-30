"""Run the rule-based detector over the full dataset and report misses.

Usage (from the project root, with data_config.py in the project root):
    python -m eval.run_rules_eval

Does not use dataset labels for scoring. Labels are only used to compare results.
"""
import csv
from pathlib import Path

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))  # so data_config.py in the project root is importable

from app.services.signals import extract_signals, rule_score
from data_config import EXTENDED_DATASET, MESSAGES_DATASET, OBFUSCATED_EDGE_CASES

OUT = Path(__file__).resolve().parent / "rules_only_results.csv"
FLAG_THRESHOLD = 30  # score at or above this counts as flagged


def main() -> None:
    items = [(m["id"], m["type"], m["text"]) for m in MESSAGES_DATASET]
    items += [(m["id"], m["type"], m["text"]) for m in EXTENDED_DATASET]
    items += [(e["id"], "phishing", e["text"]) for e in OBFUSCATED_EDGE_CASES]

    rows = []
    for mid, label, text in items:
        signals = extract_signals(text)
        score = rule_score(signals)
        rows.append({
            "id": mid,
            "expected": label,
            "score": score,
            "signals": "; ".join(sorted({s.type for s in signals})),
            "flagged": score >= FLAG_THRESHOLD,
        })

    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    phish = [r for r in rows if r["expected"] == "phishing"]
    safe = [r for r in rows if r["expected"] == "safe"]
    missed = [r for r in phish if not r["flagged"]]
    false_alarms = [r for r in safe if r["flagged"]]

    print(f"Phishing: {len(phish)}  caught: {len(phish) - len(missed)}  missed (Low): {len(missed)}")
    print(f"Safe: {len(safe)}  false alarms: {len(false_alarms)}")
    print("\nMissed phishing:")
    for r in missed:
        print(f"  {r['id']} score={r['score']} signals={r['signals'] or 'none'}")
    print("\nFalse alarms:")
    for r in false_alarms:
        print(f"  {r['id']} score={r['score']} signals={r['signals']}")
    print(f"\nFull results: {OUT}")


if __name__ == "__main__":
    main()
