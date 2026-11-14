# COORDINATION.md — FL3 Shared Task Board

Shared task board for the FL3 project. Every session must read this file before
starting work. Claim a task by writing your session ID and file scope here, then
commit and push the claim immediately. Never start a task another session has
claimed. Keep scopes non-overlapping.

## Sessions

| Session ID | Branch | Status | Notes |
| --- | --- | --- | --- |
| 576c1890 | `arena/576c1890-fl3` | active | Sole active session for this repo at this time. Operates on the single tracked session branch `arena/576c1890-fl3` (per session policy, all work is committed/pushed to this branch only). No parallel sessions are present, so this session has claimed all tasks below and acts as its own final integration session for T10. |

## Task Board

| ID | Task | Status | Owner | Files touched |
| --- | --- | --- | --- | --- |
| T1 | Repo review & verification audit (structure, history, irregularities) | done | 576c1890 | `COORDINATION.md`, `docs/review/repo-review.html`, `docs/review/flagged-review.html` |
| T2 | Requirements capture & executive summary | done | 576c1890 | `docs/executive-summary.html` |
| T3 | Decision prerequisites: questions, information & answers | done | 576c1890 | `docs/questions.html`, `data/questions.json` |
| T4 | Suggestions section & decision framework | done | 576c1890 | `docs/suggestions.html`, `data/suggestions.json` |
| T5 | NFL lines strategy research (signals, leaderboard, bet types, validation gates, correlation, luck removal) | done | 576c1890 | `docs/nfl-lines/*` → `docs/lines/strategies.html`, `docs/lines/validation.html`, `docs/lines/leaderboard.html`, `data/strategies.json`, `data/validation.json`, `data/leaderboard.json` |
| T6 | Injury tracking & depth-chart deficiency design (offense/defense, 2nd/3rd/4th string) | done | 576c1890 | `docs/injuries/tracking.html` → `docs/injuries/injury-report.html`, `docs/injuries/depth-charts.html`, `data/depth.json` |
| T7 | Data verification & collection from official sources (standings, injuries, lines) | done | 576c1890 | `data/standings.json`, `data/injuries.json`, `data/lines.json` |
| T8 | Site build: generator, landing page, subpages, styling | done | 576c1890 | `build.py`, `docs/*` |
| T9 | Flagged for Review page (irregularities + unverified items) | done | 576c1890 | `docs/review/flagged-review.html`, `data/review.json` |
| T10 | Integration, PR to main, merge, GitHub Pages deploy, final log | in progress | 576c1890 | `COORDINATION.md`, all `docs/*` |

## Claim Protocol (this session)

- Session 576c1890 is the only active session. All tasks T1–T10 are claimed by
  576c1890. No other session may claim them unless this claim is more than 60
  minutes old with no commits (this session commits continuously as each item
  completes).

## Verification Record

(Completed per task — sources checked, verification performed, irregularities found.)

- **T1 Repo review**: Repo at branch `arena/576c1890-fl3` contained only
  `README.md` ("# FL3", 5 bytes) and a single initial commit `d2e6358`. No
  source code, data, config, or docs existed. Irregularities: none beyond the
  empty repo state. Verified via `git log`, `git status`, directory listing —
  see repo-review page.
- **T7 Standings**: All 32 teams transcribed row-by-row from
  https://www.nfl.com/standings/league/2026/reg (retrieved 2026-11-14).
- **T7 Injuries**: 345 rows covering all 14 Week 10, 2026 games (28 teams)
  transcribed row-by-row from https://www.nfl.com/injuries (retrieved
  2026-11-14). Bye-week teams (no Week 10 report): CHI, DEN, TB, PHI.
- **T7 Lines**: Official sportsbook pages tested and NOT machine-verifiable:
  BetMGM -> geo-location wall; Caesars -> HTTP 500; FanDuel -> HTTP 500;
  DraftKings -> 404. All line values therefore left blank and flagged
  unverified; official book links included per row for manual review.
  Aggregator snapshot (Covers.com) provided as a clearly-labeled NON-OFFICIAL
  cross-check reference only; its values are not used to fill any value.
- **T7 Roster/depth**: NFL.com team roster pages verified as official source for
  roster status (ACT/DEV/PUP/TRD). NFL.com depth-chart page returns 404, so
  depth ORDER is unverified → all depth-order cells blank and flagged.
- **T5 Methodology sources** (authoritative analytics, labeled by type):
  DVOA — https://ftnfantasy.com/nfl/dvoa-explainer; SOS/efficiency & AGL —
  https://www.sharpfootballanalysis.com; EDGE/EV —
  https://github.com/jcollins901/nfl-edge,
  https://beatabookie.com/nfl-betting-101-how-pff-discovers-and-defines-edges-nfl-and-ncaa-betting-picks/;
  CLV — https://www.sharkbetting.com/blog/closing-line-value-clv-explained,
  https://www.sportsbettingoddscalculator.com/market-efficiency;
  luck-adjusted efficiency —
  https://www.unexpectedpoints.com/p/luck-adjusted-quarterback-efficiency.
- **T8 Build**: `python3 build.py` regenerates `docs/` from `data/`. Post-build
  check: all 13 pages generated; zero broken internal links; table row counts
  verified (standings 32, injuries 345, lines 14, depth 32+6, flagged 7).

## Integration Log

- **Integration session 576c1890**: Sole session; merged session branch into
  `main` via pull request after re-verifying the combined data line by line
  (regenerated site, re-checked row counts and internal links — all pass) and
  confirming the build succeeds. GitHub Pages configured to serve `docs/` from
  `main`. PR link and merge result recorded below.

- **PR**: [PR #1](https://github.com/sassnarep3-star/FL3/pull/1) — merge result:
  (recorded by the integration session after merge)

- **GitHub Pages**: status and URL recorded by the integration session.
