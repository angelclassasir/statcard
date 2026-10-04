# statcard v2 — Infrastructure & Web App Design

Status: approved 2026-10-04. Scope: v2 = public web app. v3 = CS2 + integrations
(see README roadmap). This document locks the decisions; do not deviate without
an explicit owner decision recorded here.

## 1. Architecture overview

    Browser
      │  (static HTML/JS, no build step)
      ▼
    Cloudflare Pages  ──frontend/──►  fetch PNG/JSON
      ▼
    FastAPI backend (Railway, single free-tier instance)
      │  server-side only: the HenrikDev key NEVER leaves this process
      ▼
    HenrikDev API  ◄──  disk cache (.cache/, TTL 1 h, shared across visitors)

## 2. Locked decisions

| # | Decision | Choice | Why |
|---|----------|--------|-----|
| 1 | Repo layout | Monorepo: `src/statcard` (core) + `src/web` (API) + `frontend/` (static) | One push deploys everything; backend imports the core lib directly; best portfolio readability |
| 2 | Frontend | Vanilla HTML/CSS/JS, no build step | CF Pages serves `frontend/` as-is; zero toolchain |
| 3 | Rate limit | 3 req/min per client IP on `/api/*`; global cap 20 req/min | HenrikDev free tier = 30 req/min; per-user = 10% of it; global cap keeps headroom for concurrent users + owner CLI |
| 4 | Cache | Reuse `statcard.cache` (SHA-1 disk cache), web TTL = 3600 s | Shared across visitors; CLI (600 s) and web coexist on the same dir (TTL checked per read) |
| 5 | Domain | `https://<project>.pages.dev` now; custom domain deferred | Free forever; custom only if the project grows/gets monetized (v3+ decision) |
| 6 | Hosting | Primary: Railway free plan. B: Render free + pinger. C: HF Spaces | See §9; verify free-tier terms at setup |
| 7 | License | Unchanged: PolyForm NC + commercial on request | Public web service is non-commercial |

## 3. Monorepo layout (v2 final)

    statcard/
    ├── src/
    │   ├── statcard/            # core library (v1): models, cache, render, providers, CLI
    │   └── web/                 # v2 FastAPI backend
    │       ├── __init__.py
    │       ├── app.py           # app factory, CORS, healthz
    │       ├── api.py           # /api/valorant routes (PNG + JSON)
    │       ├── ratelimit.py     # sliding-window limiter (per-IP + global)
    │       └── settings.py      # env-driven settings
    ├── frontend/                # v2 static site → Cloudflare Pages output dir
    │   ├── index.html
    │   ├── app.js
    │   ├── config.js            # window.STATCARD_API base URL (edited once after backend deploy)
    │   └── styles.css
    ├── docs/
    │   └── INFRASTRUCTURE.md    # this document
    ├── tests/
    │   └── test_web.py          # offline FastAPI TestClient tests
    └── (v1 files unchanged)

## 4. Backend contract

- `GET /healthz` → 200 `{"status":"ok","version":...}`. Exempt from rate limit.
  Used by Railway healthcheck and by the Plan-B pinger.
- `GET /api/valorant/{riot_id}?region=eu` → 200 `image/png` (rendered card).
  Header: `Cache-Control: public, max-age=3600` (mirrors cache TTL).
- `GET /api/valorant/{riot_id}/json` → 200 `application/json`
  (`PlayerStats.model_dump(mode="json")`). Debug + future bot reuse.
- `riot_id` arrives URL-encoded (`Name%23TAG`); backend unquotes and validates
  the `Name#TAG` shape before calling the provider.

Error mapping (provider errors → HTTP):

| Condition | Status | Body |
|-----------|--------|------|
| Malformed id (no `#`, empty name/tag) | 400 | `{"detail": ...}` |
| Player not found (upstream 404) | 404 | `{"detail": ...}` |
| Local rate limit hit | 429 | `{"detail","retry_after"}` + `Retry-After` header |
| Upstream HenrikDev 429 | 503 | `{"detail":"Upstream rate limited, try again soon"}` |
| Missing/invalid API key (upstream 401) | 500 | `{"detail":"Server misconfiguration"}` (never leak key info) |
| Network/other upstream error | 502 | `{"detail":"Upstream unavailable"}` |

## 5. Rate limiting design

- Sliding 60 s window, in-process: `dict[ip, deque[timestamps]]`, pruned on access.
- Caps: `RATE_LIMIT_PER_MIN` (default 3) per IP; `RATE_LIMIT_GLOBAL_PER_MIN`
  (default 20) across all IPs.
- Client IP: leftmost `X-Forwarded-For` if present, else `request.client.host`.
  Spoofable by design: this is a courtesy/abuse deterrent, not a security boundary.
- Applies only to `/api/*`; `/healthz` and `/docs` exempt.
- Single-instance assumption (Railway free = 1 instance). Multi-instance upgrade
  path = Redis-backed limiter (v2.x); keep the limiter backend swappable.

## 6. Caching

- Reuse `src/statcard/cache.py` unchanged. Web reads/writes with
  `ttl=WEB_CACHE_TTL` (default 3600).
- Railway filesystem is ephemeral: cache lost on redeploy. Acceptable (cache is
  an optimization, not correctness). No paid volumes.
- Upgrade path: Redis only if multi-instance becomes real.

## 7. Frontend contract

- `index.html`: form (Riot ID input, region select, button), `<img>` preview,
  status line.
- `app.js`: `fetch(STATCARD_API + /api/valorant/<encoded>?region=...)`;
  200 → blob → objectURL → `<img>`; 4xx/5xx → show JSON `detail`
  (429 also shows `retry_after`).
- `config.js`: `window.STATCARD_API = "https://<railway>.up.railway.app";`
  The only file edited between deploys.
- CORS: backend allows origins from `ALLOWED_ORIGINS` (local dev + pages.dev).

## 8. Environment variables (Railway dashboard, never in repo)

- `HENRIKDEV_API_KEY` (required)
- `WEB_CACHE_TTL` (int seconds, default 3600)
- `RATE_LIMIT_PER_MIN` (int, default 3)
- `RATE_LIMIT_GLOBAL_PER_MIN` (int, default 20)
- `ALLOWED_ORIGINS` (comma-separated, default local dev + pages.dev URL)

## 9. Hosting plan (free, 24/7 target)

Primary — Railway free plan:
- Builder Nixpacks (uv-aware). Install: `uv sync --frozen --no-dev`.
  Start: `uv run uvicorn statcard.web.app:app --host 0.0.0.0 --port ${PORT:-8000}`.
- Resource caps to fit the free credit: 0.5 vCPU / 512 MB max.
- Healthcheck: `/healthz`. Public subdomain `*.up.railway.app` = STATCARD_API.
- VERIFY AT SETUP: current free-plan credit/hours vs a 24/7 small service.

Plan B — Render free web service + external pinger (UptimeRobot/cron-job.org,
every 5-10 min against `/healthz`). Sleeps after ~15 min idle otherwise;
cold start ~30 s.

Plan C — Hugging Face Spaces free CPU (Docker). Generally always-on, no SLA.

## 10. Deploy order (chicken-and-egg resolved)

1. Merge v2 code to master.
2. Deploy backend on Railway → obtain `https://xxx.up.railway.app`.
3. Put that URL in `frontend/config.js`; set `ALLOWED_ORIGINS` on Railway to the
   future `https://<cf-project>.pages.dev`.
4. Create CF Pages project (repo, output dir `frontend`, no build command).
5. End-to-end verify; update README URLs/badges.

## 11. Testing (offline, no API key)

`tests/test_web.py` with `fastapi.testclient.TestClient`:
- Monkeypatch the web fetch layer to build `PlayerStats` from `tests/fixtures/*`;
  assert 200 + PNG magic bytes + `Cache-Control` header.
- 400 on malformed id; 404 when provider raises not-found.
- Rate limit: 4th call inside the window → 429 with `Retry-After`;
  `/healthz` never limited.
- JSON endpoint exposes `kd_scope`.

## 12. Security & legal

- API key server-side only; absent from every response and from all JS.
- Rate limit = courtesy + upstream protection, not authentication. No accounts in v2.
- License unchanged; public web service = non-commercial use.

## 13. v3 hooks

- Route family designed for growth: `/api/valorant/...` today,
  `/api/cs2/...` later, no breaking changes.
- Redis cache/limiter, custom domain, CDN edge caching (headers already set).

## 14. Open verification items at setup

- [ ] Railway free-plan terms as of deploy date (credit vs hours).
- [ ] Nixpacks uv detection on Railway (fallback: 15-line Dockerfile).
- [ ] Final CF Pages project name → pages.dev origin for ALLOWED_ORIGINS.
- [ ] Confirm HenrikDev free-tier current limit (30 req/min figure).