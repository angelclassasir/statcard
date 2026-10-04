# 🎴 StatCard

> Generate visual, shareable stat cards for your favorite FPS games.

[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-Dual%20%28PolyForm%20NC%20%2B%20Commercial%29-lightgrey.svg)](LICENSE)
[![Ruff](https://img.shields.io/badge/style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

**Language:** **English** | [Español](README.es.md)


---

`statcard` fetches your stats from **Valorant**, unifies them into a common format, and renders them into a polished PNG card ready for Discord, social media, or your GitHub profile.

> 🌐 **Live demo:** [statcard.pages.dev](https://statcard.pages.dev) — generate your card without installing anything.

> ⚠️ **Project status:** v1 (Valorant CLI) and v2 (public web app) are shipped and in production. v2.1 (UI/UX aesthetic polish) is in progress. See [Roadmap](#-roadmap).

---



## ✨ Features

- 🎮 **Valorant support** via the [HenrikDev API](https://docs.henrikdev.xyz)
- 🎨 **Dark theme** with a clean, modern palette
- 🔤 **Script-aware fonts**: Latin (Chakra Petch), Korean (Noto Sans KR), Japanese (Noto Sans JP), Chinese (Noto Sans SC), Cyrillic (Noto Sans) — player names render correctly regardless of script
- 💾 **Smart disk caching** (10 min TTL) to respect API rate limits
- ⚡ **CLI-first design**: one command, one card
- 🧪 **Offline test suite** using saved API fixtures
- 🌐 **Web interface** *(planned for v2)*: generate your card without installing anything

## 🖼️ Example

| Valorant |
| :---: |
| ![Valorant card example](examples/valorant_card.png) |

## 🛠️ Tech Stack

| Component | Tool |
| --- | --- |
| Language | Python 3.12+ |
| HTTP Client | `httpx` |
| Data Validation | `pydantic` |
| Image Rendering | `Pillow` |
| Environment Management | `uv` |
| Testing | `pytest` |
| Linting & Formatting | `ruff` |
| Type Checking | `pyrefly` |

## 🗺️ Roadmap

### v1 — Valorant CLI (shipped ✅)

- HenrikDev provider with season K/D (SEASON/RECENT fallback)
- Multi-script fonts (Latin, Thai, CJK, Cyrillic)
- Disk cache (10 min TTL), argparse CLI, offline test suite
- Dual license (PolyForm NC + commercial on request)

### v2 — Public web app (shipped ✅)

- FastAPI backend (`src/statcard/web/`): `/healthz`, `/api/valorant/{riot_id}` (PNG), `/api/valorant/{riot_id}/json`
- Sliding-window rate limit (3/min per IP + 20/min global) + shared disk cache (1 h TTL)
- Vanilla HTML/JS/CSS frontend (`frontend/`), no build step
- Production: backend on Render free tier (keep-awake pinger) + frontend on Cloudflare Pages → [statcard.pages.dev](https://statcard.pages.dev)
- Design doc: [`docs/INFRASTRUCTURE.md`](docs/INFRASTRUCTURE.md)

### v2.1 — Web quality, polish & game selector (shipped ✅)

- **Game selector** with official logos: Valorant live, CS2 disabled with a "v3" badge
- **SEO & identity**: unique title, meta description, canonical, SVG favicon, `robots.txt`, `sitemap.xml`, themed `404.html`
- **Social sharing**: Open Graph + `twitter:card = summary_large_image` with a 1200×630 preview rendered by our own Pillow pipeline
- **Performance**: self-hosted WOFF2 fonts (no CDNs), lazy-loaded images with explicit dimensions, zero JS dependencies
- **Accessibility**: contrast ≥ 4.5:1, skip-to-content link, visible keyboard focus, labeled fields, `alt` texts, `prefers-reduced-motion` respected
- **Security**: `_headers` with CSP, `X-Content-Type-Options`, `Referrer-Policy`; immutable font caching; API key never leaves the server
- **UX polish**: hero glow, sample-card showcase, loading skeleton, card entrance animation, region pills, visual countdown on 429
- **Trust**: privacy note (Riot ID sent to HenrikDev, cached ≤ 1 h, no cookies), trademark notices, contact links


### v3 — More games & integrations (planned 📋)

- CS2 provider (FACEIT Data API vs Leetify — source TBD)
- Discord bot (`/stats`) reusing providers
- Match pagination for exact full-season K/D
- Auto region detection (try `eu`/`na`/`ap`/`kr` until data is returned)

> **About CS2:** Valve does not expose a public API for CS2 competitive stats. The alternatives either require identity verification (FACEIT Data API) or depend on the player using a third-party analytics service (Leetify). CS2 support will land in v3 once the data source is chosen.

## 🚀 Getting Started

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (recommended) or `pip` + `venv`
- A HenrikDev API key: [get one here](https://dashboard.henrikdev.xyz/)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/angelclassasir/statcard.git
cd statcard

# 2. Install dependencies
uv sync

# 3. Configure your API key
cp .env.example .env
# Edit .env and add your HENRIKDEV_API_KEY
```
### Usage

```bash
# Generate a Valorant card
python -m statcard valorant "YourName#YourTag"

# Force a fresh fetch (skip cache)
python -m statcard valorant "YourName#YourTag" --no-cache

# Specify a different region
python -m statcard valorant "YourName#YourTag" --region na
```
Output images are saved to output/.

### Running the web app locally
Open two terminals in the repo root:

```bash
# Terminal 1: start the FastAPI backend
uv run uvicorn statcard.web.app:app --port 8000

# Terminal 2: serve the static frontend
cd frontend
uv run python -m http.server 8080
```
Then open http://127.0.0.1:8080 in your browser. The frontend will hit the local backend at http://127.0.0.1:8000.

💡 FastAPI also serves an auto-generated Swagger UI at http://127.0.0.1:8000/docs

## Fonts
The project uses fonts under the SIL Open Font License:

    Chakra Petch (Latin + Thai) — bundled with the repo.
    Noto Sans KR / JP / SC + Noto Sans (CJK + Cyrillic fallbacks) — heavy (~40 MB total), so they are downloaded locally and git-ignored. See assets/fonts/README.md
     for the download commands.

## 📁 Project Structure
```text
statcard/
├── src/statcard/
│   ├── __init__.py
│   ├── __main__.py            # CLI entry point (argparse)
│   ├── models.py              # Common stat format (pydantic)
│   ├── cache.py               # Disk cache with expiration
│   ├── render.py              # Card rendering (Pillow)
│   ├── providers/
│   │   ├── __init__.py
│   │   └── valorant.py        # HenrikDev -> common format
│   ├── themes/
│   │   ├── __init__.py
│   │   └── dark.py            # Colors, fonts, sizes
│   └── web/                   # FastAPI backend (v2)
│       ├── app.py             # App factory + CORS + /healthz
│       ├── api.py             # /api/valorant routes (PNG + JSON)
│       ├── ratelimit.py       # Sliding-window limiter (per-IP + global)
│       └── settings.py        # Environment-driven config
├── frontend/                  # Static web app (v2/v2.1) → Cloudflare Pages
│   ├── index.html             # Game selector, form, preview, showcase
│   ├── app.js                 # Fetch, validation, skeleton, 429 countdown
│   ├── config.js              # Backend URL (Render)
│   ├── styles.css             # Self-hosted WOFF2, glow, animations, a11y
│   ├── 404.html               # Themed "PLAYER NOT FOUND" page
│   ├── _headers               # CSP, nosniff, Referrer-Policy, cache rules
│   ├── robots.txt             # Crawl rules + sitemap reference
│   ├── sitemap.xml            # Single-page sitemap
│   ├── favicon.svg            # statcard mark
│   └── assets/
│       ├── fonts/             # Chakra Petch WOFF2 (self-hosted)
│       ├── logo-valorant.png  # Selector icon (third-party trademark)
│       ├── logo-cs2.png       # Selector icon (third-party trademark, v3)
│       ├── og-1200x630.png    # Social preview (scripts/render_social.py)
│       ├── showcase-1.png     # Sample card: Horcus
│       └── showcase-2.png     # Sample card: Mabi
├── assets/
│   └── fonts/                 # SIL OFL TTF sources (see assets/fonts/README.md)
├── tests/
│   ├── fixtures/              # Saved API responses for offline testing
│   ├── test_valorant.py
│   ├── test_cache.py
│   ├── test_cli.py
│   └── test_web.py            # FastAPI TestClient tests (offline)
├── scripts/
│   ├── smoke_valorant.py      # Manual live-API check (Horcus#1995)
│   └── render_social.py       # Generates frontend/assets/og-1200x630.png
├── docs/
│   └── INFRASTRUCTURE.md      # v2 web app design doc
├── examples/                  # Sample cards for this README
├── output/                    # Generated cards (git-ignored)
├── .env.example               # Template for API keys
└── pyproject.toml
```

Key design principle: Each game has its own provider that always returns the same common format. The renderer never knows where the data came from. Adding a new game is just writing one more provider module.

## ⚖️ Legal Notices
This is a fan-made, non-commercial educational project.

    Not affiliated with, endorsed by, or sponsored by Riot Games.
    Valorant data is fetched via the unofficial HenrikDev API.

    Valorant and related trademarks are property of Riot Games, Inc.
    Assets: all visual assets (backgrounds, icons, fonts) are either original, self-created, or sourced from free/open licenses (SIL OFL).

## 📄 License

This project uses a **dual license**:

- **Non-commercial use** (personal, educational, hobby): free under the [PolyForm Noncommercial License 1.0.0](https://polyformproject.org/licenses/noncommercial/1.0.0).
- **Commercial use**: requires express written authorization from the author. Want to use statcard commercially? [Open an issue](https://github.com/angelclassasir/statcard/issues) or contact me to negotiate a commercial license.

See the [LICENSE](LICENSE) file for the full terms.