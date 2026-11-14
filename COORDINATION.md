# COORDINATION.md — FL3 Shared Task Board

Shared task board for the FL3 project. Every session must read this file before
starting work. Claim a task by writing your session ID and file scope here, then
commit and push the claim immediately. Never start a task another session has
claimed. Keep scopes non-overlapping.

## Sessions

| Session ID | Branch | Status | Notes |
| --- | --- | --- | --- |
| 576c1890 | `arena/576c1890-fl3` | active | Sole active session for this repo at this time. Operates on the single tracked session branch `arena/576c1890-fl3` (per session policy, all work is committed/pushed to this branch only). No parallel sessions are currently present, so this session has claimed all tasks below. |

## Task Board

| ID | Task | Status | Owner | Files touched |
| --- | --- | --- | --- | --- |
| T1 | Repo review & verification audit (structure, history, irregularities) | in progress | 576c1890 | `COORDINATION.md`, `docs/review/repo-review.html`, `docs/review/flagged-review.html` |
| T2 | Requirements capture & executive summary | in progress | 576c1890 | `docs/executive-summary.html` |
| T3 | Decision prerequisites: questions, information & answers | in progress | 576c1890 | `docs/questions.html` |
| T4 | Suggestions section & decision framework | in progress | 576c1890 | `docs/suggestions.html` |
| T5 | NFL lines strategy research (signals, leaderboard, bet types, validation gates, correlation, luck removal) | in progress | 576c1890 | `docs/nfl-lines/strategies.html`, `docs/nfl-lines/validation.html`, `docs/nfl-lines/leaderboard.html` |
| T6 | Injury tracking & depth-chart deficiency design (offense/defense, 2nd/3rd/4th string) | in progress | 576c1890 | `docs/injuries/tracking.html`, `docs/injuries/depth-charts.html` |
| T7 | Data verification & collection from official sources (standings, injuries, lines) | in progress | 576c1890 | `data/*.json` |
| T8 | Site build: generator, landing page, subpages, styling | in progress | 576c1890 | `build.py`, `docs/*.html` |
| T9 | Flagged for Review page (irregularities + unverified items) | in progress | 576c1890 | `docs/review/flagged-review.html` |
| T10 | Integration, PR to main, merge, GitHub Pages deploy, final log | pending | 576c1890 | `COORDINATION.md`, all `docs/*` |

## Claim Protocol (this session)

- Session 576c1890 is the only active session. All tasks T1–T10 are claimed by
  576c1890 as of this commit. No other session may claim them unless this claim
  is more than 60 minutes old with no commits (none are; commits follow each
  completed work item).
- Work is committed frequently on branch `arena/576c1890-fl3`.

## Verification Record

(Completed per task — sources checked, verification performed, irregularities found.)

- **T1 Repo review**: Repo at branch `arena/576c1890-fl3` contains only
  `README.md` ("# FL3", 5 bytes) and a single initial commit `d2e6358`.
  No source code, data files, config, or documentation exist. Irregularities
  logged on the Flagged for Review page: none found beyond the empty repo state.
  Verified via `git log`, `git status`, file listing — see repo-review page.

## Integration Log

- (Final integration session fills this in: merged branches, re-verified combined
  data line by line, confirmed build + no broken links, Pages publish result,
  PR link and merge result.)
