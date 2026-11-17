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
