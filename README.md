# 🎴 StatCard

> Generate visual, shareable stat cards for your favorite FPS games.

[![Python](https://img.shields.io/badge/Python-3.12%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-Dual%20%28PolyForm%20NC%20%2B%20Commercial%29-lightgrey.svg)](LICENSE)
[![Ruff](https://img.shields.io/badge/style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

**Language:** **English** | [Español](README.es.md)

---

StatCard fetches your stats from **Valorant**, unifies them into a common format and renders a polished PNG card, ready for Discord, social media or your GitHub profile. It ships both as a **CLI** and as a **public web app**.

> 🌐 **Live demo:** [statcard.pages.dev](https://statcard.pages.dev) — generate your card without installing anything.

> 📦 **Status:** v1 (CLI), v2 (public web app) and v2.1 (quality and polish) are shipped and in production. v3 (more games and integrations) is planned. See the [Roadmap](#roadmap).

---

## Screenshot

[CAPTURA DE LA WEB]
<!-- Replace the line above with: ![StatCard web app](docs/images/web-screenshot.png) -->

## Example card

![Valorant card example](examples/valorant_card.png)

## Features

- 🎮 **Valorant support** via the [HenrikDev API](https://docs.henrikdev.xyz)
- 🌐 **Public web app**: pick a game, enter your Riot ID and region, get a PNG card. No install, no account
- ⚡ **CLI-first core**: one command, one card
- 🎨 **Dark theme** with a clean, modern palette
- 🔤 **Script-aware fonts**: Latin and Thai (Chakra Petch), Korean, Japanese and Chinese (Noto Sans KR / JP / SC), Cyrillic (Noto Sans). Player names render correctly regardless of script
- 💾 **Smart disk caching** to respect API limits: 10 min TTL on the CLI, 1 h shared cache on the web
- 🛡️ **Rate limiting**: sliding window of 3 requests/min per IP and 20/min global
- 🔒 **Privacy and security**: API key never leaves the server, CSP and security headers via `_headers`, no cookies
- ♿ **Accessible**: contrast ≥ 4.5:1, skip-to-content link, visible keyboard focus, labeled fields, `prefers-reduced-motion` respected
- 🧪 **Offline test suite** using saved API fixtures

## How it works

```
Browser ──► Cloudflare Pages (static frontend, vanilla HTML/JS/CSS)
                │  fetch
                ▼
        FastAPI backend on Render ──► HenrikDev API (Valorant data)
                │
                └─ Pillow renders the PNG card · disk cache · rate limiter
```

Key design principle: each game has its own **provider** that always returns the same common format. The renderer never knows where the data came from. Adding a new game is just writing one more provider module.

The full v2 design is documented in [`docs/INFRASTRUCTURE.md`](docs/INFRASTRUCTURE.md).

## Tech stack

| Component              | Tool                                                |
| ---------------------- | --------------------------------------------------- |
| Language               | Python 3.12+                                        |
| Backend                | FastAPI (served with uvicorn)                       |
| HTTP client            | `httpx`                                             |
| Data validation        | `pydantic`                                          |
| Image rendering        | `Pillow`                                            |
| Frontend               | Vanilla HTML / CSS / JS, no build step              |
| Hosting                | Cloudflare Pages (frontend) + Render free tier (backend) |
| Environment management | `uv`                                                |
| Testing                | `pytest`                                            |
| Linting & formatting   | `ruff`                                              |
| Type checking          | `pyrefly`                                           |

## Roadmap

### v1 — Valorant CLI (shipped ✅)

- HenrikDev provider with season K/D (SEASON/RECENT fallback)
- Multi-script fonts (Latin, Thai, CJK, Cyrillic)
- Disk cache (10 min TTL), argparse CLI, offline test suite
- Dual license (PolyForm NC + commercial on request)

### v2 — Public web app (shipped ✅)

- FastAPI backend (`src/statcard/web/`): `/healthz`, `/api/valorant/{riot_id}` (PNG), `/api/valorant/{riot_id}/json`
- Sliding-window rate limit (3/min per IP + 20/min global) and shared disk cache (1 h TTL)
- Vanilla HTML/JS/CSS frontend (`frontend/`), no build step
- Production: backend on Render free tier (keep-awake pinger) and frontend on Cloudflare Pages

### v2.1 — Web quality, polish and game selector (shipped ✅)

- **Game selector** with official logos: Valorant live, CS2 disabled with a "v3" badge
- **SEO and identity**: unique title, meta description, canonical, SVG favicon, `robots.txt`, `sitemap.xml`, themed `404.html`
- **Social sharing**: Open Graph and `twitter:card = summary_large_image` with a 1200×630 preview rendered by our own Pillow pipeline
- **Performance**: self-hosted WOFF2 fonts (no CDNs), lazy-loaded images with explicit dimensions, zero JS dependencies
- **Accessibility**: contrast ≥ 4.5:1, skip-to-content link, visible keyboard focus, labeled fields, `alt` texts, `prefers-reduced-motion` respected
- **Security**: `_headers` with CSP, `X-Content-Type-Options` and `Referrer-Policy`; immutable font caching; API key never leaves the server
- **UX polish**: hero glow, sample-card showcase, loading skeleton, card entrance animation, region pills, visual countdown on 429
- **Trust**: privacy note (Riot ID sent to HenrikDev, cached ≤ 1 h, no cookies), trademark notices, contact links

### v3 — More games and integrations (planned 📋)

- CS2 provider (FACEIT Data API vs Leetify; source TBD)
- Discord bot (`/stats`) reusing the providers
- Match pagination for exact full-season K/D
- Auto region detection (try `eu` / `na` / `ap` / `kr` until data is returned)

> **About CS2:** Valve does not expose a public API for CS2 competitive stats. The alternatives either require identity verification (FACEIT Data API) or depend on the player using a third-party analytics service (Leetify). CS2 support will land in v3 once the data source is chosen.

## Getting started

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

### CLI usage

```bash
# Generate a Valorant card
python -m statcard valorant "YourName#YourTag"

# Force a fresh fetch (skip cache)
python -m statcard valorant "YourName#YourTag" --no-cache

# Specify a different region
python -m statcard valorant "YourName#YourTag" --region na
```

Output images are saved to `output/`.

### Running the web app locally

Open two terminals in the repo root:

```bash
# Terminal 1: start the FastAPI backend
uv run uvicorn statcard.web.app:app --port 8000

# Terminal 2: serve the static frontend
cd frontend
uv run python -m http.server 8080
```

Then open <http://127.0.0.1:8080> in your browser. The frontend will hit the local backend at <http://127.0.0.1:8000>.

💡 FastAPI also serves an auto-generated Swagger UI at <http://127.0.0.1:8000/docs>.

### Running the tests

```bash
uv run pytest
```

The suite is fully offline: it runs against saved API fixtures.

## Fonts

The project uses fonts under the SIL Open Font License:

- **Chakra Petch** (Latin + Thai): bundled with the repo.
- **Noto Sans KR / JP / SC + Noto Sans** (CJK + Cyrillic fallbacks): heavy (~40 MB total), so they are downloaded locally and git-ignored. See [`assets/fonts/README.md`](assets/fonts/README.md) for the download commands.

## Project structure

```
statcard/
├── src/statcard/
│   ├── __main__.py            # CLI entry point (argparse)
│   ├── models.py              # Common stat format (pydantic)
│   ├── cache.py               # Disk cache with expiration
│   ├── render.py              # Card rendering (Pillow)
│   ├── providers/
│   │   └── valorant.py        # HenrikDev -> common format
│   ├── themes/
│   │   └── dark.py            # Colors, fonts, sizes
│   └── web/                   # FastAPI backend (v2)
│       ├── app.py             # App factory + CORS + /healthz
│       ├── api.py             # /api/valorant routes (PNG + JSON)
│       ├── ratelimit.py       # Sliding-window limiter (per-IP + global)
│       └── settings.py        # Environment-driven config
├── frontend/                  # Static web app -> Cloudflare Pages
│   ├── index.html             # Game selector, form, preview, showcase
│   ├── app.js                 # Fetch, validation, skeleton, 429 countdown
│   ├── config.js              # Backend URL (Render)
│   ├── styles.css             # Self-hosted WOFF2, glow, animations, a11y
│   ├── 404.html               # Themed "PLAYER NOT FOUND" page
│   ├── _headers               # CSP, nosniff, Referrer-Policy, cache rules
│   ├── robots.txt             # Crawl rules + sitemap reference
│   ├── sitemap.xml            # Single-page sitemap
│   ├── favicon.svg            # statcard mark
│   └── assets/                # Fonts, game logos, OG image, sample cards
├── assets/fonts/              # SIL OFL TTF sources
├── tests/                     # pytest suite (offline, saved fixtures)
├── scripts/
│   ├── smoke_valorant.py      # Manual live-API check
│   └── render_social.py       # Generates the 1200×630 OG image
├── docs/
│   ├── INFRASTRUCTURE.md      # v2 web app design doc
│   └── images/                # README screenshots
├── examples/                  # Sample cards for this README
├── .env.example               # Template for API keys
└── pyproject.toml
```

## Legal notices

This is a fan-made, non-commercial educational project.

- Not affiliated with, endorsed by, or sponsored by Riot Games.
- Valorant data is fetched via the unofficial HenrikDev API.
- Valorant and related trademarks are property of Riot Games, Inc.
- All visual assets (backgrounds, icons, fonts) are either original, self-created, or sourced from free/open licenses (SIL OFL), except the third-party game logos used in the game selector, which belong to their respective owners.

## License

This project uses a **dual license**:

- **Non-commercial use** (personal, educational, hobby): free under the [PolyForm Noncommercial License 1.0.0](https://polyformproject.org/licenses/noncommercial/1.0.0).
- **Commercial use**: requires express written authorization from the author. Want to use StatCard commercially? [Open an issue](https://github.com/angelclassasir/statcard/issues) to start the conversation.

See the [LICENSE](LICENSE) file for the full terms.

## Author

Built by **Angel**, systems and networks student. [Portfolio](https://callmeangel.pages.dev/en/) · [GitHub](https://github.com/angelclassasir)
