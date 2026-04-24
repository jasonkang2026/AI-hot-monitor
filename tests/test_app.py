"""Tests for the AI Hot Monitor scrapers and Flask API."""

import json
import pytest
import responses as resp_mock

from scrapers.hacker_news import fetch_hacker_news, HN_SEARCH_URL
from scrapers.github_trending import fetch_github_trending, GITHUB_SEARCH_URL
from scrapers.reddit import fetch_reddit, REDDIT_SUBREDDITS


# ---------------------------------------------------------------------------
# Hacker News scraper
# ---------------------------------------------------------------------------

HN_FIXTURE = {
    "hits": [
        {
            "objectID": "12345",
            "title": "GPT-5 released by OpenAI",
            "url": "https://openai.com/gpt5",
            "points": 500,
            "num_comments": 300,
            "created_at": "2024-03-15T12:00:00.000Z",
        },
        {
            "objectID": "12346",
            "title": "How transformers work",
            "url": "https://example.com/transformers",
            "points": 200,
            "num_comments": 80,
            "created_at": "2024-03-14T09:30:00.000Z",
        },
    ]
}


@resp_mock.activate
def test_fetch_hacker_news_returns_items():
    resp_mock.add(
        resp_mock.GET,
        HN_SEARCH_URL,
        json=HN_FIXTURE,
        status=200,
        match_querystring=False,
    )

    items = fetch_hacker_news(limit=5)

    assert isinstance(items, list)
    assert len(items) >= 1
    first = items[0]
    assert first["title"] == "GPT-5 released by OpenAI"
    assert first["score"] == 500
    assert first["source"] == "Hacker News"
    assert first["url"] == "https://openai.com/gpt5"
    assert "published_at" in first


@resp_mock.activate
def test_fetch_hacker_news_deduplicates():
    """Same objectID should not appear twice."""
    resp_mock.add(
        resp_mock.GET,
        HN_SEARCH_URL,
        json=HN_FIXTURE,
        status=200,
        match_querystring=False,
    )

    items = fetch_hacker_news(limit=50)
    ids = [item["url"] for item in items]
    assert len(ids) == len(set(ids))


@resp_mock.activate
def test_fetch_hacker_news_handles_network_error():
    resp_mock.add(
        resp_mock.GET,
        HN_SEARCH_URL,
        body=Exception("Network error"),
        match_querystring=False,
    )

    items = fetch_hacker_news(limit=5)
    assert items == []


@resp_mock.activate
def test_fetch_hacker_news_missing_url_fallback():
    """Items without a URL should fall back to the HN discussion link."""
    fixture = {
        "hits": [
            {
                "objectID": "99999",
                "title": "Ask HN: Best AI paper of 2024?",
                "url": None,
                "points": 150,
                "num_comments": 60,
                "created_at": "2024-03-15T12:00:00.000Z",
            }
        ]
    }
    resp_mock.add(
        resp_mock.GET,
        HN_SEARCH_URL,
        json=fixture,
        status=200,
        match_querystring=False,
    )

    items = fetch_hacker_news(limit=5)
    assert len(items) >= 1
    assert "99999" in items[0]["url"]


# ---------------------------------------------------------------------------
# GitHub scraper
# ---------------------------------------------------------------------------

GITHUB_FIXTURE = {
    "items": [
        {
            "full_name": "openai/whisper",
            "description": "Robust Speech Recognition via Large-Scale Weak Supervision",
            "html_url": "https://github.com/openai/whisper",
            "stargazers_count": 60000,
            "forks_count": 7000,
            "pushed_at": "2024-03-20T10:00:00Z",
        },
        {
            "full_name": "huggingface/transformers",
            "description": "State-of-the-art ML for Pytorch, TensorFlow, and JAX",
            "html_url": "https://github.com/huggingface/transformers",
            "stargazers_count": 120000,
            "forks_count": 24000,
            "pushed_at": "2024-03-21T08:00:00Z",
        },
    ]
}


@resp_mock.activate
def test_fetch_github_trending_returns_items():
    resp_mock.add(
        resp_mock.GET,
        GITHUB_SEARCH_URL,
        json=GITHUB_FIXTURE,
        status=200,
        match_querystring=False,
    )

    items = fetch_github_trending(limit=10)

    assert len(items) == 2
    assert items[0]["source"] == "GitHub"
    assert items[0]["score"] == 60000
    assert "openai/whisper" in items[0]["title"]


@resp_mock.activate
def test_fetch_github_trending_handles_error():
    resp_mock.add(
        resp_mock.GET,
        GITHUB_SEARCH_URL,
        body=Exception("timeout"),
        match_querystring=False,
    )

    items = fetch_github_trending(limit=5)
    assert items == []


@resp_mock.activate
def test_fetch_github_trending_description_truncated():
    long_desc = "A" * 200
    fixture = {
        "items": [
            {
                "full_name": "user/repo",
                "description": long_desc,
                "html_url": "https://github.com/user/repo",
                "stargazers_count": 1000,
                "forks_count": 50,
                "pushed_at": "2024-03-20T10:00:00Z",
            }
        ]
    }
    resp_mock.add(
        resp_mock.GET,
        GITHUB_SEARCH_URL,
        json=fixture,
        status=200,
        match_querystring=False,
    )

    items = fetch_github_trending(limit=5)
    assert len(items[0]["title"]) < len(long_desc) + 20


# ---------------------------------------------------------------------------
# Reddit scraper
# ---------------------------------------------------------------------------

def _reddit_fixture(subreddit, num_posts=3):
    children = [
        {
            "data": {
                "title": f"Post {i} about AI in r/{subreddit}",
                "url": f"https://example.com/post-{subreddit}-{i}",
                "score": 100 * (num_posts - i),
                "num_comments": 20 * i,
                "created_utc": 1710500000.0 + i * 3600,
                "permalink": f"/r/{subreddit}/comments/{i}/post_{i}/",
                "stickied": False,
            }
        }
        for i in range(num_posts)
    ]
    return {"data": {"children": children}}


@resp_mock.activate
def test_fetch_reddit_returns_items():
    for sub in REDDIT_SUBREDDITS:
        resp_mock.add(
            resp_mock.GET,
            f"https://www.reddit.com/r/{sub}/hot.json",
            json=_reddit_fixture(sub),
            status=200,
            match_querystring=False,
        )

    items = fetch_reddit(limit=20)

    assert isinstance(items, list)
    assert len(items) > 0
    for item in items:
        assert item["source"].startswith("r/")
        assert "title" in item
        assert "score" in item


@resp_mock.activate
def test_fetch_reddit_skips_stickied_posts():
    fixture = {
        "data": {
            "children": [
                {
                    "data": {
                        "title": "Rules and guidelines",
                        "url": "https://example.com/rules",
                        "score": 9999,
                        "num_comments": 0,
                        "created_utc": 1710500000.0,
                        "permalink": "/r/MachineLearning/comments/0/rules/",
                        "stickied": True,
                    }
                },
                {
                    "data": {
                        "title": "Real AI post",
                        "url": "https://example.com/real",
                        "score": 500,
                        "num_comments": 100,
                        "created_utc": 1710500000.0,
                        "permalink": "/r/MachineLearning/comments/1/real/",
                        "stickied": False,
                    }
                },
            ]
        }
    }
    for sub in REDDIT_SUBREDDITS:
        resp_mock.add(
            resp_mock.GET,
            f"https://www.reddit.com/r/{sub}/hot.json",
            json=fixture if sub == "MachineLearning" else {"data": {"children": []}},
            status=200,
            match_querystring=False,
        )

    items = fetch_reddit(limit=20)
    titles = [item["title"] for item in items]
    assert "Rules and guidelines" not in titles
    assert "Real AI post" in titles


@resp_mock.activate
def test_fetch_reddit_handles_network_error():
    for sub in REDDIT_SUBREDDITS:
        resp_mock.add(
            resp_mock.GET,
            f"https://www.reddit.com/r/{sub}/hot.json",
            body=Exception("timeout"),
            match_querystring=False,
        )

    items = fetch_reddit(limit=5)
    assert items == []


# ---------------------------------------------------------------------------
# Flask API endpoints
# ---------------------------------------------------------------------------

@pytest.fixture
def client(monkeypatch):
    import app as flask_app

    # Patch all fetchers to return deterministic data
    monkeypatch.setattr(
        "app.fetch_hacker_news",
        lambda limit=20: [
            {"title": "HN AI story", "url": "https://hn.example.com", "score": 100,
             "comments": 50, "source": "Hacker News", "published_at": "2024-03-15 12:00"}
        ],
    )
    monkeypatch.setattr(
        "app.fetch_github_trending",
        lambda limit=20: [
            {"title": "openai/gpt — AI repo", "url": "https://github.com/openai/gpt",
             "score": 5000, "comments": 300, "source": "GitHub", "published_at": "2024-03-20 10:00"}
        ],
    )
    monkeypatch.setattr(
        "app.fetch_reddit",
        lambda limit=20: [
            {"title": "Reddit AI news", "url": "https://reddit.com/r/ML/post1",
             "score": 800, "comments": 200, "source": "r/MachineLearning", "published_at": "2024-03-18 09:00"}
        ],
    )

    # Clear cache between tests
    flask_app._cache.clear()

    flask_app.app.config["TESTING"] = True
    with flask_app.app.test_client() as c:
        yield c


def test_index_page(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"AI Hot Monitor" in resp.data


def test_api_topics_all(client):
    resp = client.get("/api/topics")
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert "items" in data
    assert "updated_at" in data
    sources = {item["source"] for item in data["items"]}
    assert "Hacker News" in sources
    assert "GitHub" in sources
    assert "r/MachineLearning" in sources


def test_api_topics_sorted_by_score(client):
    resp = client.get("/api/topics")
    data = json.loads(resp.data)
    scores = [item["score"] for item in data["items"]]
    assert scores == sorted(scores, reverse=True)


def test_api_topics_source_hacker_news(client):
    resp = client.get("/api/topics/hacker_news")
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert len(data["items"]) >= 1
    assert data["items"][0]["source"] == "Hacker News"


def test_api_topics_source_github(client):
    resp = client.get("/api/topics/github")
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data["items"][0]["source"] == "GitHub"


def test_api_topics_source_reddit(client):
    resp = client.get("/api/topics/reddit")
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data["items"][0]["source"] == "r/MachineLearning"


def test_api_topics_unknown_source(client):
    resp = client.get("/api/topics/unknown_source")
    assert resp.status_code == 404
    data = json.loads(resp.data)
    assert "error" in data


def test_api_sources(client):
    resp = client.get("/api/sources")
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert "sources" in data
    keys = [s["key"] for s in data["sources"]]
    assert "hacker_news" in keys
    assert "github" in keys
    assert "reddit" in keys
