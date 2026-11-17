"""Offline chronological scoring. This cannot prove data provenance or real skill.

CSV columns: question_id,forecast_time,outcome_known_at,model_probability,
baseline_probability,outcome,source. Times require ISO 8601 offsets.
"""
from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime
from pathlib import Path
from forecast_core import brier, log_loss, check_probability

FIELDS = {
    "question_id", "forecast_time", "outcome_known_at",
    "model_probability", "baseline_probability", "outcome", "source",
}


def timestamp(value: str) -> datetime:
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None or result.utcoffset() is None:
        raise ValueError("Timezone offset required")
    return result


def load_rows(path: str) -> list[dict]:
    with Path(path).open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if not FIELDS.issubset(reader.fieldnames or []):
            raise ValueError("Missing required CSV columns")
        rows = list(reader)
    seen = set()
    for row in rows:
        qid = row["question_id"].strip()
        if not qid or qid in seen:
            raise ValueError("Blank or duplicate question ID")
        seen.add(qid)
        if not row["source"].strip():
            raise ValueError("Missing provenance/source label")
        row["at"] = timestamp(row["forecast_time"])
        if row["at"] >= timestamp(row["outcome_known_at"]):
            raise ValueError("Forecast must precede outcome being known")
        for key in ("model_probability", "baseline_probability"):
            row[key] = check_probability(row[key])
        if row["outcome"] not in ("0", "1"):
            raise ValueError("Non-binary outcome")
        row["outcome"] = int(row["outcome"])
    return sorted(rows, key=lambda row: row["at"])


def evaluate(rows: list[dict], holdout: float = 0.3) -> dict:
    if len(rows) < 10 or not 0 < holdout < 1:
        raise ValueError("At least ten rows and valid holdout fraction required")
    cutoff = max(1, min(len(rows) - 1, int((1-holdout)*len(rows))))
    last = rows[cutoff:]
    def average(metric, key):
        return round(sum(metric(row[key], row["outcome"]) for row in last)/len(last), 6)
    synthetic = any("synthetic" in row["source"].lower() for row in rows)
    return {
        "rows": len(rows),
        "chronological_holdout_rows": len(last),
        "model_brier": average(brier, "model_probability"),
        "baseline_brier": average(brier, "baseline_probability"),
        "model_log_loss": average(log_loss, "model_probability"),
        "baseline_log_loss": average(log_loss, "baseline_probability"),
        "synthetic_data_detected": synthetic,
        "warning": "DEMONSTRATION, NOT EVIDENCE" if synthetic
                   else "Verify genuine pre-outcome source data and no selection bias.",
    }


if __name__ == "__main__":
    cli = argparse.ArgumentParser()
    cli.add_argument("csv")
    cli.add_argument("--holdout", type=float, default=0.3)
    args = cli.parse_args()
    print(json.dumps(evaluate(load_rows(args.csv), args.holdout), indent=2))
