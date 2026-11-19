# FL3 — NFL line-origination research dashboard

**Status reviewed:** 2026-11-19 UTC
**Live site:** [sassnarep3-star.github.io/FL3](https://sassnarep3-star.github.io/FL3/)
**Purpose:** collect sourced NFL facts, originate model forecasts, and evaluate strategies only after the required data and validation gates are met. This is research software, not betting advice.

## Executive state

The repository contains several dashboard tracks and substantial research infrastructure, but it is **not yet a decision-ready betting system**. Passing a page/data check does not make a forecast profitable, prospective, or fully verified.

| Area | Current evidence in this checkout | Decision status | Official source / evidence |
|---|---|---|---|
| Requirements and gates | 75 unique readiness rows; 53 have official source links and 22 explicitly identify a source gap (`scripts/build_readiness.py --check`) | Useful for triage; source gaps remain open | [NFL schedule](https://www.nfl.com/schedules/2026/by-week/week-11), [NFL injury report](https://www.nfl.com/injuries/league/2026/reg11); row-by-row register: `data/requirements_readiness.csv` |
| Week 11 originated prices | `data/pricing/current_prices.csv` has 13 model originations. Opening model values are timestamped 2026-11-17; close columns and market-price columns are empty. | Model outputs only; no closing-line value, market edge, or ROI claim | [Official Week 11 schedule](https://www.nfl.com/schedules/2026/by-week/week-11); `data/pricing/` |
| Results corpus | `data/week_results_2026.csv` has 148 rows. `data/official/results_feed.json` describes a 149-game corrected corpus, so the declared count and the CSV do not agree. | Do not treat the corpus as complete until reconciled | [Official Week 10 schedule/results](https://www.nfl.com/schedules/2026/by-week/week-10); `data/week_results_2026.csv`, `data/official/results_feed.json` |
| Injury evidence | The Week 10 capture manifest reports 347 official rows and 36 field differences against the 345-row main table. The latest capture-log entry is 2026-11-19 04:10Z, but its raw path is blank; the logged hash alone cannot replay the page. | Point-in-time integrity and reconciliation are incomplete | [NFL Week 10 injury report](https://www.nfl.com/injuries/league/2026/reg10), [NFL Week 11 injury report](https://www.nfl.com/injuries/league/2026/reg11); `data/official_capture/manifest-2026-reg10.json`, `snapshots/index.csv` |
| Strategy ranking | The ranked comparison file is explicitly `RETROSPECTIVE_BACKTEST`; the governance check prevents it being represented as a prospective leaderboard. | Research only; no prospective winner or reward eligibility | `data/lab/leaderboard_v2.json`, `scripts/check_leaderboard_governance.py` |
| Market price policy | PD-01 says no licensed price is held; market fields remain blank and ROI is unavailable (not zero). | ROI, CLV and vig-free consensus are blocked | `data/official/results_feed.json` (PD-01), `data/pricing/current_prices.csv` |

The NFL pages linked above are official source pages. Values produced by FL3 (ratings, fair lines, probabilities, correlations, and skill scores) are model calculations, not NFL facts. Read the source register and flagged findings before relying on any result.

## Start here

- [Dashboard](index.html) — overview and readiness.
- [Executive summary](executive-summary.html) — current decision status, blockers and next steps.
- [Decision questions](decisions.html) — knowns, unknowns and clearance metrics.
- [Suggestions](suggestions.html) — reviewable paths and recommendations before implementation.
- [Lines](lines.html) and [strategies](strategies.html) — model output and validation gates.
- [Availability](availability.html), [depth evidence](depth/), and [matchups](matchups.html) — injury and personnel evidence, with gaps distinguished from verified facts.
- [Results](results.html), [correlations](correlation.html), and [ablations](ablations.html) — evaluation methods and current limitations.
- [Flagged for Review](flagged.html) — irregularities and unverified claims.
- [Sources](sources.html) and [methodology](methodology.html) — provenance and checks.

There are also separate builds under [`board/`](board/), [`docs/`](docs/), [`verified/`](verified/), [`depth/`](depth/), and [`site-9b181d31/`](site-9b181d31/). They are companion/historical tracks, not one automatically reconciled database. When values disagree, use the readiness and flagged registers; do not silently choose one copy.

## Hard limits before decisions

1. **No licensed market prices.** The system can publish its own fair-line estimates, but cannot claim an edge, ROI, CLV, or vig-free consensus. The written policy is PD-01; market columns must stay blank until a permitted source, terms, capture timestamps, and settlement mapping are established.
2. **Results feed is inconsistent.** The CSV has 148 data rows while the canonical JSON says the corrected corpus has 149. A repeated or absent fixture cannot be assumed away; reconcile each game ID to an official NFL schedule/game centre before backtest outputs are used.
3. **Availability capture is not yet replayable end-to-end.** A hash for a capture without its retained raw body does not recreate the source as it appeared at that time. The Week 10 audit also records a 347-versus-345 row discrepancy and 36 field differences between the capture and the main table.
4. **Depth is not jersey order.** Do not infer a replacement rank from jersey number, experience, salary, or a depth-chart row label. Require an admissible club source or validated official participation data; preserve shared/empty slots and roster events.
5. **A retrospective ranking is not a leaderboard win.** Keep signal skill separate from staking; qualify with proper scores, game-cluster uncertainty, controls, multiplicity adjustment, and prospective validation. ROI stays unavailable without licensed prices.
6. **The current data span is not enough to establish durable skill.** Backtests are retrospective and single-season. Do not advertise a strategy as proven or reward-eligible from these results.

## Verification

The following checks were run on this checkout on 2026-11-19:

- `python3 scripts/check_site.py` — 6,216 assertions, pass.
- `python3 scripts/check_verified_site.py` — 645 assertions, pass.
- `python3 scripts/check_links.py` — 31 pages, internal links/anchors resolved, pass.
- `python3 scripts/check_verify.py` — 323 assertions, pass.
- `python3 scripts/check_coverage_audit.py` — 69 bullets, pass.
- `python3 scripts/check_depth_links.py` — internal links resolved, pass.
- `python3 scripts/check_leaderboard_governance.py` — 10 governance checks, pass.
- `python3 scripts/verify.py` — G-10 pass with the already recorded FLG-025 source-level discrepancy; its V-09b scoring/turnover identity does **not** pass.
- `python3 scripts/build_readiness.py --check` — 75 rows, 53 linked / 22 source-gap, pass.

These checks validate repository structure, constraints, and reproducibility. They do not resolve the result-feed or injury-capture discrepancies above, nor do they show predictive skill.

## Repository map

- `data/` — registers, source-linked tables, model outputs, capture logs and audit results.
- `data/requirements_readiness.csv` — requirement-by-requirement status, blocking gate, missing information and clearance metric.
- `data/official/` — official-source-derived fixture, results and rulebook artifacts, with capture metadata.
- `data/pricing/` — immutable model-originated snapshots and the separate market fields (currently blank under PD-01).
- `scripts/` — data builders, deterministic model code, page builders and verifiers.
- `docs/` — executive summary and methodology material.
- `COORDINATION.md` — task claims, scopes, verification records and handoffs.

## Local verification

```bash
python3 scripts/build_readiness.py --check
python3 scripts/check_site.py
python3 scripts/check_verified_site.py
python3 scripts/check_links.py
python3 scripts/check_verify.py
python3 scripts/check_coverage_audit.py
python3 scripts/check_depth_links.py
python3 scripts/check_leaderboard_governance.py
```
