# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/).

## [Unreleased]

### Changed

- **Portfolio link restored** in the footer and both READMEs now that
  `callmeangel.pages.dev` is live again.

## [2.2.1] — 2026-10-25

### Fixed

- **Stable ETag**: a fresh fetch and a later cache hit now share the same
  timestamp, so the first `If-None-Match` revalidation returns 304 instead of
  re-rendering a card whose footer differed by milliseconds.
- **Dead portfolio link** removed from the frontend footer and both READMEs
  (`callmeangel.pages.dev` no longer resolves); the footer now points to the
  roadmap.

## [2.2.0] — 2026-10-25

Hardening pass: bug fixes, cache and performance work, repository hygiene.

### Fixed

- **Player not found returned 502 instead of 404.** The provider raised the
  base `ValorantProviderError` for upstream 401/404/429, so the API mapped every
  failure to "Upstream unavailable". It now raises the specific subclasses that
  `api.py` already knew how to map (404, 503 and 500 respectively).
- **Per-IP rate limiting could be bypassed with a spoofed `X-Forwarded-For`.**
  The leftmost (client-controlled) value is no longer trusted; only the
  rightmost hop appended by the proxy is used.
- **Malformed Riot IDs consumed rate-limit quota.** Path/query validation now
  runs before the limiter, so a typo does not lock the user out.
- **The cache stored the full match payload** (round history + kill feed, ~96%
  of the response, ~9 MB per 10 matches). Payloads are trimmed before caching,
  which drops entries to a few hundred KB and makes cache hits fast.
- **Expired cache entries were never deleted and the store had no size cap.**
  Expired/corrupt entries are removed on read, writes are atomic, and the store
  evicts the oldest entries past 500 files / 64 MB.
- **Cached cards reported the wrong "last updated" time.** It now reflects when
  the data was actually fetched, not when the card was rendered.
- **`kills`/`deaths` were zero when the K/D fell back to `RECENT`.** The JSON
  endpoint exposed a ratio with no underlying totals; both now come from the
  same scope as the ratio.
- **Frontend error handling read the response body twice** (`response.clone()`
  after `response.json()`), which always fell back to the header path.
- **README claimed WOFF2 fonts** while the project serves TTF (reverted in
  v2.1 for Safari glyph coverage).

### Added

- ETag support on the PNG endpoint (`304 Not Modified` on repeat requests).
- `AbortController` timeout in the frontend, with a "server is waking up"
  message for Render cold starts, object-URL cleanup and a `noscript` notice.
- Parallel upstream requests (`account`, `MMR` and `matches` run concurrently).
- PNG rendering runs in a threadpool so it no longer blocks the event loop.
- Structured logging in the provider and API routes (`LOG_LEVEL`).
- `STATCARD_CACHE_DIR` override and documented `RATE_LIMIT_*`, `ALLOWED_ORIGINS`
  and `LOG_LEVEL` variables in `.env.example`.
- `--version` flag and `--region` validation in the CLI; `--output` now accepts
  an explicit path.
- SIL OFL licence texts for every bundled/downloaded font, and the Noto fetcher
  now downloads them next to the fonts.
- `CHANGELOG.md`, `.pre-commit-config.yaml`, and a CI guard that fails if `.env`
  is ever tracked.
- Tests: upstream error mapping, XFF spoofing, invalid-ID quota, ETag/304,
  cache eviction/metadata, payload trimming and long-name rendering.

### Changed

- Player names and long labels are ellipsized instead of overflowing the card.
- Cache hits compute `last_updated` from the entry timestamp; timestamps are
  timezone-aware (UTC).
- `Pillow>=10.1` is now required for `ImageFont.load_default(size)`.
- CS2 logo resized from 7806×7813 (559 KB) to 128×128 (7 KB).
- Repository hygiene: `.gitignore` rewritten (it was wrapped in a Markdown
  block), removed dead code, fixed lint/format violations so CI is green.
- `docs/INFRASTRUCTURE.md` and both READMEs updated to match the implementation.

## [2.1.0] — 2026-10-04

- Game selector with official logos, SEO/OG assets, `_headers` CSP, themed 404,
  accessibility polish, self-hosted fonts, loading skeleton and 429 countdown.

## [2.0.0] — 2026-10-04

- Public web app: FastAPI backend, PNG/JSON endpoints, shared disk cache,
  sliding-window rate limiting and a dependency-free static frontend.

## [1.0.0] — 2026-10-03

- Valorant CLI, HenrikDev provider, Pillow renderer, multi-script fonts,
  disk cache and offline test suite.
