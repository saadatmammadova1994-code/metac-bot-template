"""One-question, free-model-only Metaculus bot smoke test.

Run manually via the GitHub "Test Bot" action. Never forecasts on the live
competition, never schedules another run, and never selects a paid LLM.
A free endpoint can still reject requests due to quota or availability.
"""
from __future__ import annotations

import asyncio
import os
import sys

from bot_helpers import check_environment, print_run_summary_banner
from forecasting_tools import (
    BinaryQuestion,
    ForecastReport,
    GeneralLlm,
    MetaculusClient,
)

FREE_MODEL = "openrouter/nvidia/nemotron-3.5-super-vl:free"
TEST_TOURNAMENT = "bot-testing-area"


def free_model_config() -> dict:
    if not FREE_MODEL.startswith("openrouter/") or not FREE_MODEL.endswith(":free"):
        raise RuntimeError("Refusing non-free model in the smoke test.")
    # All model functions are explicitly set, blocking the SDK's paid defaults.
    return {
        "default": GeneralLlm(model=FREE_MODEL, temperature=0.2, timeout=120, allowed_tries=1),
        "parser": GeneralLlm(model=FREE_MODEL, temperature=0.0, timeout=120, allowed_tries=1),
        "summarizer": GeneralLlm(model=FREE_MODEL, temperature=0.0, timeout=120, allowed_tries=1),
        "researcher": "no_research",
    }


def main() -> None:
    check_environment(strict=True)
    if not os.getenv("OPENROUTER_API_KEY"):
        raise SystemExit("Missing OPENROUTER_API_KEY; refusing to use any other provider")
    # The test is run from main (stock template) OR from the experimental branch.
    # In either case, all model roles are fixed to a free endpoint.
    from main import FallTemplateBot2026

    bot = FallTemplateBot2026(
        research_reports_per_question=1,
        predictions_per_research_report=1,
        use_research_summary_to_forecast=False,
        publish_reports_to_metaculus=True,
        skip_previously_forecasted_questions=False,
        folder_to_save_reports_to=None,
        llms=free_model_config(),
    )
    questions = MetaculusClient.get_all_open_questions_from_tournament(TEST_TOURNAMENT)
    binary = next((q for q in questions if isinstance(q, BinaryQuestion) and
                   getattr(q, "conditional_type", None) is None), None)
    if binary is None:
        raise SystemExit("No open standalone binary question in test tournament")
    print(f"Test-only forecast target: {binary.page_url}")
    reports = asyncio.run(bot.forecast_questions([binary], return_exceptions=True))
    print_run_summary_banner(reports, will_publish=True,
                             tournament_url="https://www.metaculus.com/tournament/bot-testing-area/")
    if len(reports) != 1 or not isinstance(reports[0], ForecastReport):
        raise SystemExit("One-question test did not produce a valid forecast report")
    if reports[0].errors:
        raise SystemExit(f"Forecast report contains {len(reports[0].errors)} error(s)")
    print("Test job ended. Verify a forecast actually appears on YOUR BOT profile.")


if __name__ == "__main__":
    main()
