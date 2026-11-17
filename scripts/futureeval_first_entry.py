"""Single-question Fall 2026 FutureEval entry, gated by explicit review.

PREVIEW is the default and NEVER publishes. SUBMIT requires a fixed question
ID, a separate checkbox confirmation, and a Gemini Free Tier project.
No schedules, paid search providers, repeated forecasts, or batch submissions.
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
import os
import sys

from bot_helpers import print_run_summary_banner
from forecasting_tools import BinaryQuestion, ForecastReport, MetaculusClient
from scripts.free_single_question_test import free_model_config
from main import FallTemplateBot2026

TOURNAMENT = 33121  # Official Metaculus FE_FALL_2026_ID (SDK constant)
TOURNAMENT_URL = "https://www.metaculus.com/tournament/fall-futureeval-2026/"
MIN_TIME_TO_CLOSE = timedelta(hours=36)


def available_binary_questions(client, now: datetime) -> list[BinaryQuestion]:
    """Only open standalone binary questions not previously forecasted by this bot."""
    questions = client.get_all_open_questions_from_tournament(
        TOURNAMENT, group_question_mode="exclude"
    )
    accepted: list[BinaryQuestion] = []
    diagnostics = {
        "not_binary": 0, "conditional": 0,
        "already_forecast": 0, "no_close_time": 0,
        "naive_close_time": 0, "closing_soon": 0,
        "missing_post_id": 0,
    }
    for q in questions:
        if not isinstance(q, BinaryQuestion):
            diagnostics["not_binary"] += 1
            continue
        if q.conditional_type is not None:
            diagnostics["conditional"] += 1
            continue
        if q.previous_forecasts:
            diagnostics["already_forecast"] += 1
            continue
        if q.close_time is None:
            diagnostics["no_close_time"] += 1
            continue
        close = q.close_time
        if close.tzinfo is None:
            # Never silently assume local timezone.
            diagnostics["naive_close_time"] += 1
            continue
        if close.astimezone(timezone.utc) <= now + MIN_TIME_TO_CLOSE:
            diagnostics["closing_soon"] += 1
            continue
        if q.id_of_post is None:
            diagnostics["missing_post_id"] += 1
            continue
        accepted.append(q)
    print(f"TOURNAMENT API ID: {TOURNAMENT}; open standalone raw questions={len(questions)}")
    print(f"Eligible first-entry binary questions={len(accepted)}")
    print(f"Rejected by reason (first applicable): {diagnostics}")
    # Closest to 7 days away; quick feedback but adequate review window.
    return sorted(
        accepted,
        key=lambda q: (
            abs((q.close_time.astimezone(timezone.utc) - now).total_seconds()
                - 7 * 86400),
            int(q.id_of_post),
        ),
    )


def select_question(questions: list[BinaryQuestion], question_id: str) -> BinaryQuestion:
    if question_id:
        if not question_id.isdecimal():
            raise ValueError("Question ID must contain only digits")
        matches = [q for q in questions if int(q.id_of_post) == int(question_id)]
        if len(matches) != 1:
            raise ValueError(
                "Selected question is no longer open/eligible, or already forecasted. "
                "Re-run PREVIEW; no forecast was submitted."
            )
        return matches[0]
    if not questions:
        raise ValueError(
            "No eligible standalone binary question open with >36h remaining. "
            "No forecast was submitted."
        )
    return questions[0]


def main() -> None:
    mode = os.getenv("FIRST_ENTRY_MODE", "preview")
    question_id = os.getenv("FIRST_ENTRY_QUESTION_ID", "").strip()
    acknowledgement = os.getenv("FIRST_ENTRY_CONFIRM", "false").lower()
    free_tier = os.getenv("FIRST_ENTRY_FREE_TIER_CONFIRMED", "false").lower()
    if free_tier != "true":
        raise SystemExit("Free Tier project not confirmed; no model run or submission")
    if mode not in {"preview", "submit"}:
        raise SystemExit("Unknown execution mode")
    if mode == "submit":
        if acknowledgement != "true" or not question_id:
            raise SystemExit(
                "SUBMIT rejected: requires explicit confirmation and an exact "
                "previewed question ID. Nothing was submitted."
            )
    if not os.getenv("METACULUS_TOKEN") or not os.getenv("GEMINI_API_KEY"):
        raise SystemExit("Missing required token: METACULUS_TOKEN/GEMINI_API_KEY")

    # Competing bot has completed the entry form; this code never creates a new bot.
    client = MetaculusClient()
    now = datetime.now(timezone.utc)
    candidates = available_binary_questions(client, now)
    selected = select_question(candidates, question_id)
    selected_id = int(selected.id_of_post)
    print(f"TOURNAMENT: {TOURNAMENT} (one question only)")
    print(f"MODE: {mode.upper()} | question_id: {selected_id}")
    print(f"QUESTION: {selected.question_text[:480]}")
    print(f"CLOSE UTC: {selected.close_time.astimezone(timezone.utc).isoformat()}")
    print(f"URL: {selected.page_url}")
    if mode == "preview":
        print("DRY RUN: the model's prediction will NOT be submitted.")
    else:
        print("EXPLICIT SUBMIT MODE: ONE LIVE FORECAST will be submitted.")

    bot = FallTemplateBot2026(
        research_reports_per_question=1,
        predictions_per_research_report=1,
        use_research_summary_to_forecast=False,
        publish_reports_to_metaculus=(mode == "submit"),
        skip_previously_forecasted_questions=True,
        extra_metadata_in_explanation=True,
        folder_to_save_reports_to=None,
        llms=free_model_config(),
    )
    reports = asyncio.run(bot.forecast_questions([selected], return_exceptions=True))
    if len(reports) != 1 or not isinstance(reports[0], ForecastReport):
        raise SystemExit("Forecast failed; no successful report")
    report = reports[0]
    if report.errors:
        raise SystemExit(f"Forecast report contains {len(report.errors)} errors")
    if int(report.question.id_of_post) != selected_id:
        raise SystemExit("Question mismatch; do not trust the report")
    print(f"MODEL PROBABILITY: {report.prediction}")
    try:
        rationale = report.first_rationale.replace("\n", " ")
        print(f"RATIONALE EXCERPT: {rationale[:1000]}")
    except (ValueError, IndexError, AttributeError):
        print("Could not extract rationale excerpt; review report in GitHub logs")
    print_run_summary_banner(reports, will_publish=(mode == "submit"),
                             tournament_url=TOURNAMENT_URL)
    if mode == "preview":
        print(f"PREVIEW COMPLETE. Review ID {selected_id}; NO forecast submitted.")
    else:
        print(f"ONE LIVE FORECAST SUBMITTED FOR #{selected_id}; verify on bot profile.")


if __name__ == "__main__":
    main()
