"""Fetch trending AI/ML repositories from GitHub."""

import requests
from dateutil import parser as dateparser

GITHUB_SEARCH_URL = "https://api.github.com/search/repositories"

AI_TOPICS = "artificial-intelligence OR machine-learning OR deep-learning OR llm OR nlp OR generative-ai"


def fetch_github_trending(limit: int = 20) -> list[dict]:
    """Return recently-active GitHub repositories related to AI/ML.

    Each item has keys: title, url, score, comments, source, published_at.
    The 'score' field contains the star count and 'comments' is the fork count.
    """
    headers = {
        "Accept": "application/vnd.github+json",
    }
    try:
        resp = requests.get(
            GITHUB_SEARCH_URL,
            params={
                "q": f"topic:({AI_TOPICS}) pushed:>2024-01-01",
                "sort": "stars",
                "order": "desc",
                "per_page": limit,
            },
            headers=headers,
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return []

    items: list[dict] = []
    for repo in data.get("items", [])[:limit]:
        pushed_at = ""
        raw_ts = repo.get("pushed_at")
        if raw_ts:
            try:
                pushed_at = dateparser.parse(raw_ts).strftime("%Y-%m-%d %H:%M")
            except Exception:
                pushed_at = raw_ts

        description = repo.get("description") or ""
        title = repo.get("full_name", "")
        if description:
            title = f"{title} — {description[:80]}"

        items.append(
            {
                "title": title,
                "url": repo.get("html_url", ""),
                "score": repo.get("stargazers_count", 0),
                "comments": repo.get("forks_count", 0),
                "source": "GitHub",
                "published_at": pushed_at,
            }
        )

    return items
