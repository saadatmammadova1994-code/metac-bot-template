"""Read-only Metaculus feed diagnostics, WITHOUT forecasting or LLM calls.

Fetch only small counts and structural post types. Do not log credentials, titles,
IDs, private content, raw API responses, or account data.
"""
from __future__ import annotations

from collections import Counter
import json
import os
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ENDPOINT = "https://www.metaculus.com/api/posts/"
PROBES = (
    ("tournament_open_id", {"tournaments": 33121, "statuses": "open", "limit": 5}),
    ("tournament_open_slug", {"tournaments": "fall-futureeval-2026", "statuses": "open", "limit": 5}),
    ("tournament_all_statuses", {"tournaments": 33121, "limit": 5}),
    ("tournament_upcoming", {"tournaments": 33121, "statuses": "upcoming", "limit": 5}),
    ("global_open_control", {"statuses": "open", "limit": 5}),
)


def structural_summary(document: object) -> dict:
    """Summarize only aggregate shape, never raw post records."""
    if not isinstance(document, dict):
        return {"shape": type(document).__name__}
    results = document.get("results")
    if not isinstance(results, list):
        return {"shape": "dict-without-list-results"}
    statuses: Counter[str] = Counter()
    types: Counter[str] = Counter()
    for item in results:
        if not isinstance(item, dict):
            continue
        status = item.get("status")
        statuses[str(status) if isinstance(status, str) else "(missing)"] += 1
        kind = (
            "group" if "group_of_questions" in item
            else "conditional" if "conditional" in item
            else "individual" if isinstance(item.get("question"), dict)
            else "other"
        )
        types[kind] += 1
    total = document.get("count")
    return {
        "returned": len(results),
        "reported_count": total if isinstance(total, int) else "unavailable",
        "types": dict(types),
        "statuses": dict(statuses),
    }


def run() -> None:
    token = os.getenv("METACULUS_TOKEN")
    if not token:
        raise SystemExit("Missing token; no request made")
    headers = {"Authorization": "Token " + token, "Accept": "application/json"}
    for name, query in PROBES:
        request = Request(ENDPOINT + "?" + urlencode(query), headers=headers)
        try:
            with urlopen(request, timeout=12) as response:
                raw = response.read(700001)
                if len(raw) > 700000:
                    print(f"{name}: HTTP {response.status}, response too large")
                    continue
                payload = json.loads(raw)
                print(f"{name}: HTTP {response.status}; {json.dumps(structural_summary(payload), sort_keys=True)}")
        except HTTPError as e:
            print(f"{name}: HTTP {e.code}; body redacted")
        except (URLError, TimeoutError, ValueError, json.JSONDecodeError) as e:
            print(f"{name}: request/parse error type={type(e).__name__}")
    print("READ-ONLY DIAGNOSTICS COMPLETE; no AI call, no forecast, no state mutation.")


if __name__ == "__main__":
    run()
