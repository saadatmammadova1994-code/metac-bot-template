# FutureEval V2 — experimental, opt-in integration

**Status:** Prepared in a separate GitHub branch, NOT a submitted tournament entry.
No claimed improvement over the official Fall 2026 template. No model credentials
are stored in this repository. Prize eligibility/payout for Azerbaijan is unconfirmed.

## What changes
- The stock `FallTemplateBot2026` is wrapped with `GuardedFallBot2026`.
- Binary outcomes can optionally be post-processed by an odds-shrinkage rule.
- The default environment variable `FORECAST_GUARD_SHRINK=0.0` means **the
  actual forecasts are unchanged**. Leave it off until real chronological
  out-of-sample evaluation demonstrates a benefit.
- Multi-option, numeric, date and conditional handling remain upstream.
- `forecast_core.py` and `chronological_backtest.py` are OFFLINE utilities;
  they do not send forecasts or contact Metaculus.

## Verification
Run `python -m unittest discover -s tests -v` (requires Python).
Confirm a separate bot profile exists, and follow the official instructions:
https://github.com/Metaculus/metac-bot-template#quick-start---fork-and-use-github-actions

1. Register the bot under the **human** Metaculus account via
   https://www.metaculus.com/futureeval/participate/
2. Fill in the required form before submitting tournament forecasts.
3. In fork repository Settings > Secrets and variables > Actions set
   `METACULUS_TOKEN` and a supported model provider key
   (`OPENROUTER_API_KEY`, etc). **Never paste secrets into chat or GitHub code**.
4. Do not enable the scheduled production workflow yet.
5. With the official `Test Bot` workflow, confirm a forecast actually appears
   on the BOT profile in the test tournament. A green checkmark alone is
   insufficient.
6. Confirm tournament-specific rules, residency/payout eligibility and budget.
7. Benchmark the OFF guard vs any experimental variant using genuinely
   timestamped, resolved questions before choosing a value other than 0.

## Evidence standards
- Local syntax/tests are not proof of a successful SDK run.
- A backtest using synthetic or post-outcome predictions is not evidence.
- Do not claim any percentage accuracy improvement or likelihood of winning
  until verified on genuine held-out or live data.
- Competition pool is not an individual guaranteed award.

## OpenRouter unavailable: Google AI Studio free-tier alternative (17 Nov 2026)

- A separate, manually invoked `Test Bot` workflow on `main` and this branch
  uses only `gemini/gemini-3.1-flash-lite` for model roles and no researcher.
- Google AI Studio supports Azerbaijan. Obtain a `GEMINI_API_KEY` using
  https://aistudio.google.com/api-keys and save it in **GitHub Actions Secrets**.
- **Use a non-billing project.** Do not link Cloud Billing or enable a paid tier.
  If a key is associated with billing, the free-tier assumption is invalid.
- `METACULUS_TOKEN` is already configured by the account owner (not visible
  to the assistant). Do not reveal it in code, screenshots, or chat.
- The baseline one-question Gemini smoke test succeeded on 17 Nov 2026 (test area,
  question 43327, under bot account MerryCreater-bot). This establishes API
  connectivity only, NOT forecasting skill. The experimental research variant
  has NOT been tested against Metaculus.

## Experimental research branch — no-cost, opt-in

- `grounded_bot.py` extends the existing `GuardedFallBot2026` with source
  discovery that is **off by default**.
- `research_sources.py` issues **at most one** GDELT DOC 2.0 request per question
  (up to six dated news **headlines**, NOT full article text). GDELT requires
  no API key but may return 429 rate limits or incomplete coverage.
- Headlines are unverified leads: they are NOT confirmed facts, authoritative
  evidence, or a replacement for checking original publisher content.
- The default `main` branch test remains the proven no-research baseline.
  On `feature/futureeval-v2-guard-review`, the **manual Test Bot** workflow
  sets `EXPERIMENTAL_NEWS_RESEARCH=1` and tests one binary question from the
  unscored bot-testing area. Do not run the scheduled competition workflow.
- A query-planning Gemini invocation and GDELT call are extra requests, so
  free-tier quotas may be hit. No billed Google Search grounding is enabled.
- The model is pinned to `gemini/gemini-3.1-flash-lite` for all AI roles, and
  the experimental research calls GDELT directly. Never link billing solely
  to bypass free-tier limits.

## Evidence and data permissions

- Metaculus official API rules restrict reuse of Metaculus question/forecast
  data to train, evaluate or develop models without prior written permission:
  https://www.metaculus.com/api/
  Request benchmarking access through the official **Metaculus Data Needs**
  form before downloading/rescoring historical Metaculus datasets.
- The offline `chronological_backtest.py` accepts independently and lawfully
  acquired labeled records; **no Metaculus history has been downloaded**.
- Brier score and log loss are diagnostic, not the tournament's official
  weighted **Peer Score**. No measured improvement over the standard bot exists.
- The automated tests use fabricated deterministic fixtures, not real events.
- Both tournament and Metaculus Cup live schedules are disabled on `main`;
  all live submissions require a separate manual decision and verified budget.
