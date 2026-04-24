"""AI Hot Monitor — Flask web application.

Aggregates trending AI topics from Hacker News, GitHub, and Reddit and
serves them via a lightweight web dashboard.
"""

import datetime
import sys
import threading
from flask import Flask, jsonify, render_template
from cachetools import TTLCache

from scrapers import fetch_hacker_news, fetch_github_trending, fetch_reddit

app = Flask(__name__)

# Cache results for 15 minutes to avoid hammering external APIs
_CACHE_TTL = 900  # seconds
_cache: TTLCache = TTLCache(maxsize=10, ttl=_CACHE_TTL)
_cache_lock = threading.Lock()

# Maps source key -> (display name, module-level attribute name of the fetcher).
# Using the attribute name (string) lets tests monkeypatch the function while
# keeping it callable at request time.
SOURCES: dict[str, tuple[str, str]] = {
    "hacker_news": ("Hacker News", "fetch_hacker_news"),
    "github": ("GitHub", "fetch_github_trending"),
    "reddit": ("Reddit", "fetch_reddit"),
}


def _get_fetcher(source_key: str):
    """Return the current module-level fetcher function for *source_key*.

    Looking up via ``sys.modules`` ensures that any monkeypatching done by
    tests (e.g. ``monkeypatch.setattr("app.fetch_hacker_news", ...)``) is
    respected.
    """
    _, attr_name = SOURCES[source_key]
    return getattr(sys.modules[__name__], attr_name)


def _get_cached(source_key: str) -> list[dict]:
    with _cache_lock:
        if source_key in _cache:
            return _cache[source_key]
    fetcher = _get_fetcher(source_key)
    items = fetcher(limit=20)
    with _cache_lock:
        _cache[source_key] = items
    return items


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/topics")
def api_topics():
    """Return aggregated topics from all sources."""
    all_items: list[dict] = []
    for key in SOURCES:
        try:
            all_items.extend(_get_cached(key))
        except Exception:
            pass

    all_items.sort(key=lambda x: x.get("score", 0), reverse=True)
    return jsonify(
        {
            "items": all_items,
            "updated_at": datetime.datetime.now(tz=datetime.timezone.utc).strftime(
                "%Y-%m-%d %H:%M UTC"
            ),
        }
    )


@app.route("/api/topics/<source>")
def api_topics_source(source: str):
    """Return topics from a specific source."""
    if source not in SOURCES:
        return jsonify({"error": f"Unknown source '{source}'"}), 404
    try:
        items = _get_cached(source)
    except Exception:
        return jsonify({"error": "Failed to fetch topics from this source"}), 500
    return jsonify(
        {
            "items": items,
            "updated_at": datetime.datetime.now(tz=datetime.timezone.utc).strftime(
                "%Y-%m-%d %H:%M UTC"
            ),
        }
    )


@app.route("/api/sources")
def api_sources():
    """Return available data sources."""
    return jsonify(
        {
            "sources": [
                {"key": key, "name": name} for key, (name, _) in SOURCES.items()
            ]
        }
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
