"""Fetch hot posts from AI-related Reddit communities."""

import datetime
import requests

REDDIT_SUBREDDITS = [
    "MachineLearning",
    "artificial",
    "LocalLLaMA",
    "singularity",
    "OpenAI",
]

REDDIT_HEADERS = {
    "User-Agent": "AI-hot-monitor/1.0 (educational project)"
}


def fetch_reddit(limit: int = 20) -> list[dict]:
    """Return hot posts from AI-related subreddits.

    Each item has keys: title, url, score, comments, source, published_at.
    """
    items: list[dict] = []
    per_sub = max(1, limit // len(REDDIT_SUBREDDITS))

    for subreddit in REDDIT_SUBREDDITS:
        if len(items) >= limit:
            break
        try:
            resp = requests.get(
                f"https://www.reddit.com/r/{subreddit}/hot.json",
                params={"limit": per_sub},
                headers=REDDIT_HEADERS,
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception:
            continue

        for post in data.get("data", {}).get("children", []):
            post_data = post.get("data", {})
            if post_data.get("stickied"):
                continue

            created_utc = post_data.get("created_utc", 0)
            published_at = ""
            if created_utc:
                try:
                    published_at = datetime.datetime.fromtimestamp(
                        created_utc, tz=datetime.timezone.utc
                    ).strftime("%Y-%m-%d %H:%M")
                except Exception:
                    pass

            permalink = post_data.get("permalink", "")
            url = post_data.get("url") or f"https://www.reddit.com{permalink}"

            items.append(
                {
                    "title": post_data.get("title", ""),
                    "url": url,
                    "score": post_data.get("score", 0),
                    "comments": post_data.get("num_comments", 0),
                    "source": f"r/{subreddit}",
                    "published_at": published_at,
                }
            )

            if len(items) >= limit:
                break

    items.sort(key=lambda x: x["score"], reverse=True)
    return items[:limit]
