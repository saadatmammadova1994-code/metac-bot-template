# Experimental headline research pilot — FutureEval (17 Nov 2026)

## What is already proved
- \`MerryCreater-bot\` posted a **single** binary test forecast on Metaculus
  test question #43327 from the repository's \`main\` branch.
- GitHub test run:
  https://github.com/saadatmammadova1994-code/metac-bot-template/actions/runs/44043334985
- This validates basic end-to-end connectivity, **not** predictive skill.

## New component
- \`grounded_bot.py\` (feature branch only) overrides \`run_research\`.
- The default \`EXPERIMENTAL_NEWS_RESEARCH\` setting is off. Only the **Test Bot**
  workflow in branch \`feature/source-research-test\` sets it to "1".
- When enabled, the model proposes one short query. \`research_sources.py\`
  queries the keyless GDELT DOC index at most once; if unavailable or empty,
  it tries Google News RSS at most once. It returns up to six recent, timestamped
  article headlines and URLs. Full article content is **not**
  retrieved or verified. On GDELT HTTP 429, timeout, malformed reply or zero matches,
  it tries the RSS fallback. If both fail or return no matches, it returns an
  explicit **no-evidence** message.
- The forecasting and parsing model remains Gemini 3.1 Flash-Lite. This
  experimental version consumes at least one additional model request.
- Headlines are untrusted leads, NOT confirmed evidence. Independent checks
  against original sources are still needed to establish factual accuracy.
- A source count alone is NOT proof of forecasting improvement.

## Safety and limits
- Keep the Google AI Studio project on **Free Tier**, with billing unlinked.
  Google Search grounding for Gemini 3.x is NOT supported in the free API tier.
- No API keys or user data are committed to GitHub; the existing
  \`GEMINI_API_KEY\` and \`METACULUS_TOKEN\` stay encrypted in Secrets.
- All production/tournament workflow schedules remain disabled on \`main\`.
- This feature has **not** been live-tested; only offline source mocks and
  syntax checks are run in CI.
- Do not merge, enable experimental research for live tournament questions,
  or claim a positive skill lift without real tests and source QA.
- GDELT and Google News RSS may impose rate limits; the integration makes
  at most one request per provider (two total), with no automatic retries.

## Real-data evaluation restrictions
Metaculus API documentation says data retrieved via the API must not be used
to train, evaluate or otherwise develop AI/ML models without prior written
permission. Do **not** download or backtest historical Metaculus data using
this repo until the appropriate permission/access is granted:
https://www.metaculus.com/api/

The official competition ranks weighted **Peer Scores**, not simply Brier or
log loss. That requires scored, compliant prospective results before any
claims about rank or prizes.

## How to test the experimental version, once reviewed
1. Confirm that the Google API key is from a **Free Tier** project.
2. Open [Test Bot](https://github.com/saadatmammadova1994-code/metac-bot-template/actions/workflows/test_bot.yaml).
3. Choose **Use workflow from** \`feature/source-research-test\`, then trigger
   one manual run. It forecasts **one test-area binary question**, never a
   live competition question. Do NOT choose the tournament workflow.
4. Review the job log for "Experimental GDELT", whether headlines were
   retrieved, and whether the forecast was submitted.
5. In Metaculus switch to \`MerryCreater-bot\` to verify the private
   explanation and forecast. A green GitHub status alone is not evidence of
   source-grounded accuracy.

Use the stock \`main\` Test Bot as the control, but do not re-run it just
for comparisons without a clear cost/quota reason. No model-performance
comparison is yet possible with a single unresolved question.

## Screenshot-based failure review (17 Nov 2026)

The first live source-aware test on #43327 succeeded at posting a forecast, but
the six retrieved headlines concerned unrelated topics (including geopolitics,
aviation, domestic politics, and transport). The private Research Summary itself
acknowledged that these were insufficient to address the EU-exit question.

**Mitigation added AFTER that test**:
- `filter_relevant_headlines` rejects titles lacking question-specific
  evidence terms before they reach the forecasting prompt.
- For the EU withdrawal question, a title must mention (a) one of the member
  countries named in the question, (b) an exit/withdrawal event term and
  (c) the EU/European Union or a specific exit term (e.g., Frexit).
- For other questions, a deliberately conservative lexical overlap heuristic
  screens titles. It is NOT a verified semantic relevance model.
- When no title survives, the bot explicitly reports no relevant headlines.
  Absence of matching headlines DOES NOT prove the event cannot occur.
- Test log now prints the indexed, accepted and rejected title counts;
  no article content is fetched or independently fact-checked.
- All **29 offline unit tests** passed on GitHub CI run:
  https://github.com/saadatmammadova1994-code/metac-bot-template/actions/runs/44047409082

**Next gate:** the updated relevance filter has NOT yet been run against
Metaculus, GDELT or Google RSS live. Do not claim it improved Brier Score,
Peer Score or competition rank. Leave production scheduling disabled.
