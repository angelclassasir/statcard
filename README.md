   **Language:** [English](README.md) | [Español](README.es.md)

# 🎴 StatCard

> Generate visual, shareable stat cards for your favorite FPS games.

[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Ruff](https://img.shields.io/badge/style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

`statcard` fetches your stats from **Valorant**, **CS2 (FACEIT)**, and **CS2 (Premier/MM)**, unifies them into a common format, and renders them into a polished PNG card ready for Discord, social media, or your GitHub profile.

> ⚠️ **Project Status:** Active development (Phase 1). Currently building the backend foundation and API integrations.

---

## ✨ Features

- 🎮 **Multi-game support**
  - **Valorant** via [HenrikDev API](https://docs.henrikdev.xyz)
  - **CS2 (FACEIT)** via the official FACEIT API
  - **CS2 (Premier/MM)** via Leetify
- 🎨 **Unified dark theme** across all cards
- 🖼️ **Dynamic backgrounds** selected based on your stats (agents, maps, ranks)
- 💾 **Smart disk caching** to respect API rate limits
- ⚡ **CLI-first design**: one command, one card
- 🌐 **Web interface** *(planned)*: generate your card without installing anything

## 🖼️ Examples

> Cards will appear here once Phase 2 is complete.

| Valorant | CS2 (FACEIT) | CS2 (Premier) |
| :---: | :---: | :---: |
| *Coming soon* | *Coming soon* | *Coming soon* |

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
| Future Web API | FastAPI + Cloudflare Pages |

## 🗺️ Roadmap

| Phase | Description | Status |
| :---: | --- | :---: |
| 0 | Repository setup and initial structure | ✅ Done |
| 1 | Valorant API integration (HenrikDev) + data models | 🚧 In Progress |
| 2 | First card render with Pillow + dark theme | ⬜ |
| 3 | Disk caching + error handling | ⬜ |
| 4 | CS2 (FACEIT) integration | ⬜ |
| 5 | CS2 (Premier/MM) integration via Leetify | ⬜ |
| 6 | CLI polish, tests, and CI | ⬜ |
| 7 | Presentation: README, examples, legal notices | ⬜ |
| 8 | *(Future)* FastAPI backend + web frontend | ⬜ |
| 9 | *(Optional)* Discord bot with `/stats` command | ⬜ |

## 🚀 Getting Started

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (recommended) or `pip` + `venv`
- API keys:
  - **Valorant:** [HenrikDev Dashboard](https://dashboard.henrikdev.xyz/)
  - **CS2 (FACEIT):** [FACEIT Developers](https://developers.faceit.com/)
  - **CS2 (Premier/MM):** Leetify API

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/angelclassasir/statcard.git
cd statcard

# 2. Install dependencies
uv sync

# 3. Configure your API keys
cp .env.example .env
# Edit .env and add your keys
```
### Usage

```bash
# Valorant
python -m statcard valorant "YourName#YourTag"

# CS2 via FACEIT
python -m statcard faceit "your_faceit_nickname"
    
# CS2 Premier/MM via Leetify
python -m statcard cs2 "your_steamid"
```
Output images are saved to output/.

### 📁 Project Structure
statcard/
├── src/statcard/
│   ├── __main__.py       # CLI entry point
│   ├── models.py         # Common stat format (pydantic)
│   ├── cache.py          # Disk cache with expiration
│   ├── render.py         # Card rendering (Pillow)
│   ├── providers/
│   │   ├── valorant.py   # HenrikDev → common format
│   │   ├── faceit.py     # FACEIT → common format
│   │   └── cs2.py        # Leetify → common format
│   └── themes/
│       └── dark.py       # Colors, fonts, sizes
├── assets/               # Fonts, icons, backgrounds (free licenses)
├── tests/
│   ├── fixtures/         # Saved API responses for offline testing
│   └── test_*.py
├── examples/             # Sample cards for this README
├── output/               # Generated cards (git-ignored)
├── .env.example          # Template for API keys
└── pyproject.toml

Key design principle: Each game has its own provider that always returns the same common format. The renderer never knows where the data came from. Adding a new game is just writing one more provider module.

### ⚖️ Legal Notices

This is a fan-made, non-commercial educational project.

    Not affiliated with, endorsed by, or sponsored by Riot Games, Valve Corporation, FACEIT, or Leetify.
    Valorant data is fetched via the unofficial HenrikDev API
    .
    CS2 data is fetched via the official FACEIT API and/or Leetify, with proper attribution.
    Assets: All visual assets (backgrounds, icons, fonts) are either original, self-created, or sourced from free/open licenses. Game trademarks belong to their respective owners.

### 📄 License
This project is licensed under the MIT License.