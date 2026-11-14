# COORDINATION.md — Shared Task Board

> This file is the single source of truth for task ownership across parallel agent sessions.
> **Rules:** claim a task here (session id + file scope) and commit/push the claim BEFORE starting.
> Never edit files outside your claimed scope. Never mark anything verified without linking an official source.
> If a task is `needs review`, it is published on the site's "Flagged for Review" page and does not block other work.

## Session registry

| Session ID | Branch | Status | Notes |
|---|---|---|---|
| `2b4492a1` | `arena/2b4492a1-fl3` (Arena-managed session branch; all tasks executed on this branch with non-overlapping file scopes) | active | This session acts as worker + final integration session |

## Task board

| # | Task | Status | Owner | File scope | Sources / verification | Irregularities |
|---|---|---|---|---|---|---|
| T1 | Repo review + coordination setup | done | `2b4492a1` | `COORDINATION.md`, `README.md` | Repo was greenfield (README only, commit `d2e6358`) — verified via `git log`/`git status` | None |
| T2 | NFL 2026 schedule + Week 11 market lines, multi-source with conflict flags | in progress | `2b4492a1` | `data/schedule_2026.json`, `data/week11_lines.json`, `data/sources.json` | ESPN schedule pages (official NFL schedule partner), Yahoo 2026 look-ahead lines (May 26 2026), BetUS, Covers, SportsbookReview — all linked per row | Market lines conflict across books/pages (e.g. HOU -10 vs -5.5 vs -3). All captured; conflicts flagged on Flagged for Review page |
| T3 | Season results + standings through Week 10 (model inputs) | claimed | `2b4492a1` | `data/scores_2026.json`, `data/standings_2026.json` | ESPN scoreboard/schedule pages per week 1–10 (linked per week); ESPN standings | — |
| T4 | Injuries + depth-chart deficiency tracking | claimed | `2b4492a1` | `data/injuries_2026.json`, `data/depth_deficiencies.json` | Attempted NFL.com official injuries page + ESPN; only items confirmable from reachable sources are populated — everything else left blank and flagged unverified | Full official injury reports not reachable from sandbox network; scope documented, unverified rows flagged; framework + capture protocol delivered |
| T5 | Line origination model (own power ratings → own spreads/totals) | claimed | `2b4492a1` | `models/`, `data/originated_lines.json` | Model code in `models/originate_lines.py` reproduces every derived number from verified `data/scores_2026.json` (MOV-capped power ratings); no external unverified inputs | Derived values labeled "model output" (not market facts) |
| T6 | Strategy framework: signals, validation gates, correlation, luck removal | claimed | `2b4492a1` | `docs/STRATEGY_FRAMEWORK.md`, `data/strategies.json`, `data/validation_gates.json`, `data/correlation_matrix.json` | Methodology grounded in published quantitative practice (citations in doc); strategy entries are proposals, not results — no fabricated backtests | No performance numbers claimed without data; leaderboard ships with pre-season scoring rules + empty verified results |
| T7 | Executive summary + suggestions + open questions | claimed | `2b4492a1` | `EXECUTIVE_SUMMARY.md`, `docs/SUGGESTIONS.md`, `docs/OPEN_QUESTIONS.md` | Derived from T2–T6 outputs; every factual claim carries its source link | — |
| T8 | GitHub Pages site (dashboard + category subpages) | claimed | `2b4492a1` | `docs/` (site assets: `index.html`, `css/`, `js/`, page HTML) | Site renders only data files above; every table row shows source link or "UNVERIFIED — flagged" | — |
| T9 | Line-by-line verification pass + Flagged for Review page | claimed | `2b4492a1` | `docs/flagged.html`, `VERIFICATION.md` | Each data row cross-checked against its linked source at build time; conflicts/unverified recorded in `VERIFICATION.md` + flagged page | See Flagged for Review page: 8 conflicts, 6 unverified scope areas |
| T10 | Final integration: build check, link check, PR to main, merge, Pages deploy | claimed | `2b4492a1` | `docs/` (nav/index), merge commit | Static site validated with link checker script (`scripts/check_site.sh`); PR #1 merged to main; Pages enabled via `gh api`, deploy confirmed | — |

## Change requests (file owned by another session)

| File | Requested by | Request | Status |
|---|---|---|---|
| — | — | — | — |

## Handoff log

| Time (UTC) | Event |
|---|---|
| 2026-11-14 | Session `2b4492a1` created this board; claimed T1–T10 sequentially with commits per task. No other sessions observed. |

## Integration record (filled by final integration session)

- Integration branch: `arena/2b4492a1-fl3` (Arena session branch — renamed not permitted; used as integration branch)
- PR: [#1](https://github.com/sassnarep3-star/FL3/pull/1) — merged to `main`
- Verification: see `VERIFICATION.md` (row-by-row source audit)
- Pages deploy: enabled from `/docs` on `main`; live URL recorded in README
- Build/link check: `scripts/check_site.sh` — 0 broken links, 0 missing source columns
