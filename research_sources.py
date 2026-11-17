"""Conservative, keyless GDELT DOC news-headline discovery.

An article-list result is NOT a verified primary source. It is editorial
metadata only. No full-page scraping, no copying community predictions,
no Metaculus dataset downloads, no persistent data collection.
Request ceiling: one GDELT request and at most six headlines per question.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from email.message import Message
import json
import re
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen

GDELT_URL = "https://api.gdeltproject.org/api/v2/doc/doc"
MAX_ARTICLES = 6
MAX_BYTES = 300_000
SEARCH_DAYS = 30

_STOPWORDS = set((
    "a an and as at be before by can do does did for from how if in is it "
    "of on or the this that to was were what when where which who why will "
    "would could should any more less than with after under over years year "
    "day days end start result likely question probability forecast 2027"
).split())


def normalize_query(raw: str) -> str:
    """Render an LLM-proposed topic as plain, bounded search terms."""
    if not isinstance(raw, str):
        raise ValueError("Query should be text")
    words = re.findall(r"[A-Za-z][A-Za-z0-9'-]*", raw)
    usable = [w.lower() for w in words if w.lower() not in _STOPWORDS]
    usable = usable[:8]
    if len(usable) < 2:
        raise ValueError("A meaningful 2+ word topic is required")
    return " ".join(usable)[:110]


def gdelt_url(query: str) -> str:
    query = normalize_query(query)
    params = urlencode({
        "query": query,
        "mode": "ArtList",
        "format": "json",
        "sort": "DateDesc",
        "maxrecords": MAX_ARTICLES,
        "timespan": f"{SEARCH_DAYS}d",
    })
    return f"{GDELT_URL}?{params}"


def _parse_date(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.strptime(value, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _safe_text(raw: object, limit: int) -> str:
    if not isinstance(raw, str):
        return ""
    return re.sub(r"\s+", " ", raw).replace("<", "").replace(">", "").strip()[:limit]


def parse_articles(payload: object, now: datetime | None = None) -> list[dict[str, str]]:
    """Validate source metadata and discard future/old/untrusted records."""
    if not isinstance(payload, dict) or not isinstance(payload.get("articles"), list):
        raise ValueError("Unexpected GDELT response shape")
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        raise ValueError("now must contain timezone")
    lower = current - timedelta(days=SEARCH_DAYS)
    seen: set[str] = set()
    result: list[dict[str, str]] = []
    for row in payload["articles"][:50]:
        if not isinstance(row, dict):
            continue
        url = row.get("url")
        title = _safe_text(row.get("title"), 180)
        seen_at = _parse_date(row.get("seendate"))
        if not isinstance(url, str) or len(url) > 1000 or not title or not seen_at:
            continue
        if not lower <= seen_at <= current:
            continue
        parsed = urlsplit(url)
        if parsed.scheme not in ("https", "http") or not parsed.hostname:
            continue
        if parsed.username or parsed.password or parsed.hostname.endswith(".local"):
            continue
        if url in seen:
            continue
        seen.add(url)
        result.append({
            "headline": title,
            "url": url,
            "domain": _safe_text(row.get("domain") or parsed.hostname, 80),
            "date": seen_at.date().isoformat(),
        })
        if len(result) >= MAX_ARTICLES:
            break
    return result


def fetch_recent_headlines(query: str, opener=None) -> list[dict[str, str]]:
    """One bounded request. Failure is handled by caller, never retried."""
    opener = opener or urlopen
    req = Request(
        gdelt_url(query),
        headers={"User-Agent": "FutureEval-source-headlines/0.1 (research metadata; no scraping)",
                 "Accept": "application/json"},
    )
    with opener(req, timeout=10) as response:
        content_type = response.headers.get("Content-Type", "")
        if "json" not in content_type.lower():
            raise ValueError("News service did not return JSON")
        raw = response.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError("News response exceeds size limit")
    return parse_articles(json.loads(raw.decode("utf-8")))


def format_news_brief(articles: list[dict[str, str]], asof: datetime | None = None) -> str:
    current = asof or datetime.now(timezone.utc)
    preamble = (
        f"Headline index checked at {current.isoformat(timespec='minutes')}. "
        "Headlines are UNVERIFIED article metadata, not confirmed event facts. "
        "They can be stale, biased, misleading or unrelated. "
        "Do not invent quotes, data, article contents, or sources. "
        "If evidence is insufficient, explicitly state uncertainty."
    )
    if not articles:
        return preamble + " No relevant, dated headlines retrieved. Base analysis on the question only."
    lines = [preamble, "Indexed headlines (titles only; URLs for independent review):"]
    for idx, row in enumerate(articles[:MAX_ARTICLES], 1):
        lines.append(
            f"[{idx}] {row['date']} | {row['domain']} | "
            f"{row['headline']} | {row['url']}"
        )
    return "\n".join(lines)
