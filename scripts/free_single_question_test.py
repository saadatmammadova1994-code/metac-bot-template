"""One-question, Gemini free-tier Metaculus bot smoke test.

Run manually via the GitHub "Test Bot" action. Never forecasts on the live
competition, never schedules another run, and never selects a paid LLM.
Requires a GOOGLE AI STUDIO FREE-TIER project with billing NOT enabled.
A key from a billing-enabled project may create charges; never use one here.
Free-tier usage can still fail due to quota or availability.
"""
from __future__ import annotations

import asyncio
import os
import sys

from bot_helpers import print_run_summary_banner
from forecasting_tools import (
    BinaryQuestion,
    ForecastReport,
    GeneralLlm,
    MetaculusClient,
)

FREE_MODEL = "gemini/gemini-3.1-flash-lite"
TEST_TOURNAMENT = "bot-testing-area"


def free_model_config() -> dict:
    if FREE_MODEL != "gemini/gemini-3.1-flash-lite":
        raise RuntimeError("Refusing non-free model in the smoke test.")
    # All model functions are explicitly set, blocking the SDK's paid defaults.
    return {
        "default": GeneralLlm(model=FREE_MODEL, temperature=0.2, timeout=120, allowed_tries=1),
        "parser": GeneralLlm(model=FREE_MODEL, temperature=0.0, timeout=120, allowed_tries=1),
        "summarizer": GeneralLlm(model=FREE_MODEL, temperature=0.0, timeout=120, allowed_tries=1),
        "researcher": "no_research",
    }


def main() -> None:
    if not os.getenv("METACULUS_TOKEN"):
        raise SystemExit("Missing METACULUS_TOKEN")
    if not os.getenv("GEMINI_API_KEY"):
        raise SystemExit("Missing GEMINI_API_KEY; refusing to use another provider")
    # The test is run from main (stock template) OR from the experimental branch.
    # In either case, all model roles are fixed to a free endpoint.
    from main import FallTemplateBot2026
    bot_class = FallTemplateBot2026
    if os.getenv("EXPERIMENTAL_NEWS_RESEARCH") == "1":
        from grounded_bot import ResearchFallBot2026
        bot_class = ResearchFallBot2026
        print("Experimental GDELT headline research enabled; metadata is not verified.")

    bot = bot_class(
        research_reports_per_question=1,
        predictions_per_research_report=1,
        use_research_summary_to_forecast=False,
        publish_reports_to_metaculus=True,
        skip_previously_forecasted_questions=False,
        folder_to_save_reports_to=None,
        llms=free_model_config(),
    )
    questions = MetaculusClient().get_all_open_questions_from_tournament(TEST_TOURNAMENT)
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
