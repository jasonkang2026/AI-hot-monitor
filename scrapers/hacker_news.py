"""Fetch trending AI topics from Hacker News via the Algolia search API."""

import requests
from dateutil import parser as dateparser

HN_SEARCH_URL = "https://hn.algolia.com/api/v1/search"

AI_KEYWORDS = [
    "AI", "artificial intelligence", "machine learning", "deep learning",
    "LLM", "GPT", "neural network", "OpenAI", "Anthropic", "Gemini",
]


def fetch_hacker_news(limit: int = 20) -> list[dict]:
    """Return top HN stories matching AI-related keywords.

    Each item has keys: title, url, score, comments, source, published_at.
    """
    seen_ids: set[int] = set()
    items: list[dict] = []

    for keyword in AI_KEYWORDS:
        if len(items) >= limit:
            break
        try:
            resp = requests.get(
                HN_SEARCH_URL,
                params={
                    "query": keyword,
                    "tags": "story",
                    "hitsPerPage": limit,
                    "numericFilters": "points>10",
                },
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception:
            continue

        for hit in data.get("hits", []):
            object_id = hit.get("objectID")
            if not object_id or int(object_id) in seen_ids:
                continue
            seen_ids.add(int(object_id))

            hn_url = hit.get("url") or f"https://news.ycombinator.com/item?id={object_id}"
            published_at = ""
            raw_ts = hit.get("created_at")
            if raw_ts:
                try:
                    published_at = dateparser.parse(raw_ts).strftime("%Y-%m-%d %H:%M")
                except Exception:
                    published_at = raw_ts

            items.append(
                {
                    "title": hit.get("title", ""),
                    "url": hn_url,
                    "score": hit.get("points", 0),
                    "comments": hit.get("num_comments", 0),
                    "source": "Hacker News",
                    "published_at": published_at,
                }
            )

            if len(items) >= limit:
                break

    items.sort(key=lambda x: x["score"], reverse=True)
    return items[:limit]
