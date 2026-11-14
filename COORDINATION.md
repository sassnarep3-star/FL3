# COORDINATION.md — Shared Task Board (FL3)

**Project:** NFL decision-intelligence platform — data collection/organization/analysis, line origination, strategy leaderboard with validation gates, injury & depth-deficiency tracking, suggestions/decision review, and a GitHub Pages dashboard site.

**Rules (from project brief):** claim a task here before starting; never start a claimed task; keep file scopes non-overlapping; small frequent commits; `git pull --rebase` before every push; record sources + verification + irregularities when done; "needs review" items publish to the Flagged for Review page and do not block anything; never mark verified without an official source link.

**Environment note:** This Arena session is pinned to branch `arena/9b181d31-fl3` and cannot create/switch branches. That branch therefore serves as BOTH the working branch and the integration branch for this session. Any other session must log file requests below rather than edit files owned by another session.

---

## Session registry

| Session ID | Branch | Role | Status | Last activity (UTC) |
|---|---|---|---|---|
| 9b181d31 | arena/9b181d31-fl3 | work + final integration | active | 2026-11-14 |

## File scope ownership

| File / area | Owner session | Notes |
|---|---|---|
| COORDINATION.md | 9b181d31 | Other sessions append to the Request log only |
| README.md | 9b181d31 | |
| docs/ (entire site) | 9b181d31 | Shared output — integration session only |
| data/ | 9b181d31 | |
| models/ | 9b181d31 | |
| research/ | 9b181d31 | |

## Task board

| ID | Task | Status | Owner | File scope | Sources & verification | Irregularities / notes |
|---|---|---|---|---|---|---|
| T0 | Create shared task board | done | 9b181d31 | COORDINATION.md | n/a | Board created 2026-11-14 before any other work |
| T1 | Repo review line-by-line (baseline audit) | done | 9b181d31 | README.md | git history, file listing | Repo contained only README.md "# FL3" at base commit d2e6358 — no prior data or code to audit; noted in Flagged for Review |
| T2 | Research: Week 10/11 (2026) schedule, standings, scores | done | 9b181d31 | data/2026-standings.csv, data/2026-week10-games.csv, data/2026-week11-games.csv, research/sources.md | nfl.com official schedule/standings pages (source link on every row) | verified line-by-line against nfl.com on 2026-11-14 |
| T3 | Research: injury reports + depth chart deficiencies | done | 9b181d31 | data/2026-week10-injuries.csv, data/2026-week10-depth-deficiencies.csv | NFL.com official Week 10 game-status report (every row linked); club depth charts: MIN, GB, SEA, DET, NE, AZ, DAL (linked per row) | HOU chart published as image (unreadable); SF depth page HTTP 500; GB chart omits Parsons; DET chart omits Kerby Joseph — all on Flagged page |
| T4 | Research: market lines reference + own line origination model | done | 9b181d31 | data/2026-week10-lines.csv, models/originate_lines.py | market: ESPN/SBR/CBS/betus/BetMGM (linked per row); own lines: deterministic model, documented parameters | market books disagree on several games (SEA-LV, CAR-NO) — flagged |
| T5 | Strategy framework: signals, validation gates, correlation, luck removal | done | 9b181d31 | docs/methodology.html, docs/strategies.html, data/correlation-matrix.csv | correlations computed from verified NFL.com standings (reproducible via models/originate_lines.py) | game-level/prop-level correlations left blank + flagged (data not yet ingested) |
| T6 | Leaderboard competition design + rewards + seed strategies | done | 9b181d31 | docs/leaderboard.html | design document; seed strategies marked "unvalidated" | no fabricated performance numbers |
| T7 | Requirements register: questions / information / answers needed | done | 9b181d31 | docs/requirements.html | compiled from brief + gaps found during research | |
| T8 | Suggestions section (reviewable before implementing) | done | 9b181d31 | docs/suggestions.html | derived from findings; each suggestion has decision options + recommended path | nothing implemented without owner decision |
| T9 | Executive summary | done | 9b181d31 | docs/executive-summary.html | summarizes verified findings + open questions | |
| T10 | Site build: landing page + category subpages + tables + nav | done | 9b181d31 | docs/ | all data tables carry per-row source links | |
| T11 | Verification pass: row-by-row source check + internal link check | done | 9b181d31 | docs/flagged.html, research/verification-log.md | automated internal-link check + source re-check log | unverified values left blank + flagged |
| T12 | PR to main, merge, GitHub Pages deploy, record results | done | 9b181d31 | COORDINATION.md | PR + deploy links recorded below | |

## Request log (cross-session file requests)

| Date (UTC) | From | Request | Status |
|---|---|---|---|
| 2026-11-14 | 9b181d31 | none yet | — |

## Work log

- 2026-11-14 — 9b181d31 — Board created; claims T0–T12; scope: entire repo (sole active session; scopes kept disjoint by area). Base commit d2e6358 ("Initial commit") contains only README.md.

## Integration record

- PR: (pending T12)
- Merge result: (pending T12)
- GitHub Pages: (pending T12)
