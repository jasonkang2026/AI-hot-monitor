# AI Hot Monitor

A lightweight web dashboard that aggregates **trending AI topics** from multiple sources in real-time.

## Features

- 🔥 **Multi-source aggregation** — fetches hot stories from Hacker News, GitHub, and Reddit AI communities
- ⚡ **15-minute caching** — avoids hammering external APIs while keeping data fresh
- 🎛️ **Per-source filtering** — quickly switch between Hacker News, GitHub, and Reddit views
- 🌑 **Dark theme UI** — clean, responsive Bootstrap 5 dashboard

## Sources

| Source | Data | Sorted by |
|--------|------|-----------|
| Hacker News | AI/ML stories via Algolia API | Points |
| GitHub | AI/ML repositories via GitHub Search API | Stars |
| Reddit | Hot posts from r/MachineLearning, r/artificial, r/LocalLLaMA, r/singularity, r/OpenAI | Score |

## Requirements

- Python 3.12+

## Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/jasonkang2026/AI-hot-monitor.git
cd AI-hot-monitor

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the application
python app.py
```

Then open http://localhost:5000 in your browser.

## Project Structure

```
AI-hot-monitor/
├── app.py                  # Flask application & API endpoints
├── requirements.txt
├── scrapers/
│   ├── __init__.py
│   ├── hacker_news.py      # Hacker News Algolia API scraper
│   ├── github_trending.py  # GitHub Search API scraper
│   └── reddit.py           # Reddit JSON API scraper
├── templates/
│   └── index.html          # Dashboard HTML
├── static/
│   ├── css/style.css
│   └── js/app.js
└── tests/
    └── test_app.py
```

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /` | Web dashboard |
| `GET /api/topics` | All trending topics (sorted by score) |
| `GET /api/topics/<source>` | Topics from a specific source (`hacker_news`, `github`, `reddit`) |
| `GET /api/sources` | List of available sources |

## Running Tests

```bash
pip install -r requirements.txt
python -m pytest tests/ -v
```

