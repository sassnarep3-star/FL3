# COORDINATION.md — Shared Task Board

Repo: `sassnarep3-star/FL3` · Purpose: collect, organize and analyze NFL data to originate our own
lines, score strategies on a leaderboard, and publish a verified dashboard on GitHub Pages.

**Every session must read this file before touching anything, claim a row, and commit the claim
before editing.** Rules are at the bottom of this file.

- Last updated: 2026-11-14T06:20Z
- Active session: `S1-b37bd750` (branch `arena/b37bd750-fl3`)

## Sandbox capability notes (matters for how tasks get done)

Verified 2026-11-14 by `S1-b37bd750` from inside the agent sandbox:

| Capability | Result | Evidence |
| --- | --- | --- |
| `pypi.org` | reachable (HTTP 200) | `curl -o /dev/null -w %{http_code} https://pypi.org/simple/` |
| `api.github.com` | reachable | repo/release metadata reads succeeded |
| `github.com` / `codeload.github.com` git | reachable | `git clone` reached remote auth/404 stage |
| `release-assets.githubusercontent.com` | **blocked** | `SSL_ERROR_SYSCALL` on nflverse release asset download |
| `raw.githubusercontent.com` | **blocked** | `SSL_ERROR_SYSCALL` |
| `www.nfl.com`, `api.nfl.com` from bash | **blocked** | `SSL_ERROR_SYSCALL` |

Consequence: bulk datasets (nflverse parquet/CSVs) **cannot** be pulled inside the sandbox, and no
live HTTP fetcher can be exercised here. Data in `data/` is therefore entered from pages read
through the agent's HTTP-proxying fetch tool and each row carries the exact official URL plus the
read timestamp. Fetcher scripts in `scripts/` are written for a networked host (GitHub Actions or
the owner's machine) and are labelled `not executed in sandbox` where that is true — never claim a
script as "verified" unless it was actually run.

## Task board

| ID | Task | Status | Owner | File scope | Notes |
| --- | --- | --- | --- | --- | --- |
| T0 | Repo review, COORDINATION.md, sandbox capability probe | done | S1-b37bd750 | `README.md`, `COORDINATION.md`, `.gitignore` | Repo contained only a 5-byte `README.md`; nothing to review |
| T1 | Source registry + verification protocol (`data/sources.csv`) | done | S1-b37bd750 | `data/sources.csv`, `content/methodology.md` | Official-source-only rule; source classes defined here |
| T2 | League facts & rulebook inputs needed by the model | done | S1-b37bd750 | `data/league_facts.csv`, `content/league-facts.md` | Roster/injury-report/OT/scheduling rules from the Official Playing Rules |
| T3 | 2026 season results & standings (official) → derived margin/total distributions | done | S1-b37bd750 | `data/games_2026.csv`, `data/standings_2026.csv`, `data/team_*_2026.csv`, `data/derived_*.csv` | Only rows read off nfl.com get a value; the rest stay blank |
| T4 | Injury + availability dataset (official injury report) incl. backup/depthchart deficiency logic | done | S1-b37bd750 | `data/injuries_2026_w10.csv`, `data/slate_2026_w10.csv`, `content/injuries.md` | Week 10 report as of read time |
| T5 | Line origination model spec (spread, total, moneyline, props) | done | S1-b37bd750 | `models/line_model.yaml`, `data/lines_origination.csv`, `data/model_calibration.csv`, `content/model.md`, `content/lines.md`, `content/parameters.md` | Power ratings → margin/total → prices |
| T6 | Signal catalogue (single, parlay, prop combos) + leaderboard + reward design | done | S1-b37bd750 | `data/signals.csv`, `models/strategy_registry.yaml`, `models/leaderboard.yaml`, `data/leaderboard.csv`, `content/signals.md`, `content/leaderboard.md` | |
| T7 | Validation gates (anti-luck / skill isolation) + correlation policy | done | S1-b37bd750 | `data/gates.csv`, `models/gates.yaml`, `data/decision_math.csv`, `content/validation.md`, `content/correlation.md` | Gate definitions, minimum-N math |
| T8 | Open questions, required information, known gaps | done | S1-b37bd750 | `data/questions.csv`, `content/questions.md` | Blocking vs non-blocking |
| T9 | Suggestions register (review + choose best path before implementing) | done | S1-b37bd750 | `data/suggestions.csv`, `content/suggestions.md` | No suggestion is implemented without an owner decision |
| T10 | Site generator + Pages publish + link checker | done | S1-b37bd750 | `site/**`, `scripts/**`, `docs/**` (generated), `content/**`, `.github/workflows/site.yml`, `README.md`, `.gitignore` | `python3 scripts/build_board.py` |
| T11 | Flagged for Review page (irregularities + unverified items) | done | S1-b37bd750 | `data/flags.csv`, `content/flagged.md` | |
| T12 | Executive summary | done | S1-b37bd750 | `content/executive-summary.md` | |
| T13 | Final integration: pull --rebase, rebuild, link check, PR → main, merge, confirm Pages | in progress | S1-b37bd750 | whole repo | Runs last |

Statuses: `unclaimed` → `in progress` → `needs review` (published on Flagged for Review, non-blocking)
→ `done`.

## Claim log

| Time (UTC) | Session | Action |
| --- | --- | --- |
| 2026-11-14T03:05Z | S1-b37bd750 | Created board, claimed T0–T13 (whole repo, greenfield — no other session had claimed anything; branch `arena/b37bd750-fl3`) |

## Integration log

| Time (UTC) | Session | Action |
| --- | --- | --- |
| 2026-11-14T04:05Z | S1-b37bd750 | Wrote the data layer (`data/`: standings, team stats, games, injuries, sources, facts, questions, suggestions) from fetch-tool reads of official pages; `scripts/lib_fl3.py` + `scripts/verify.py` added |
| 2026-11-14T05:20Z | S1-b37bd750 | Added `scripts/model.py` (derive → calibrate → rate → price) and `models/line_model.yaml`; first `verify.py` run exited 1 and found three real defects (PCT formula, rounding tolerance, source TD/INT mismatch) instead of passing silently |
| 2026-11-14T05:55Z | S1-b37bd750 | `scripts/stats_tables.py` (break-even / minimum-sample / parlay math), `scripts/make_leaderboard.py`, `scripts/fetch_nfl_data.py` (written, **not executed** - see FLG-024), `models/gates.yaml`, `models/leaderboard.yaml`, `models/strategy_registry.yaml` |
| 2026-11-14T06:15Z | S1-b37bd750 | Site generator `scripts/build_board.py` + `scripts/check_links.py`: 20 pages in `board/`, every table rendered from `data/`, verify+link gates wired into the build, `README.md`, `.gitignore`, `.github/workflows/site.yml` (Pages via upload/deploy-pages) |
| 2026-11-14T06:35Z | S1-b37bd750 | Pages settings checked: `build_type=legacy`, source `main`/`docs`; `PUT /pages {build_type: workflow}` returned **403 Resource not accessible by integration**, so deployment stays branch-based and `.github/workflows/site.yml` is a gate (regenerate → verify → build → link check → staleness check) rather than the publisher. The build was made deterministic (no timestamp in any page) so the staleness check is meaningful. Logged as FLG-027 |
| 2026-11-14T06:20Z | S1-b37bd750 | **Structural data bug found and fixed**: `data/suggestions.csv` (21 rows), `data/sources.csv` (5 rows), `data/signals.csv` (1 row) and `data/games_2026.csv` (2 rows) had unquoted commas / a missing column, which silently shifted `source_id` and `accessed_utc` into the wrong cells. Rewritten through `csv.writer`. Added `verify.py` check **I-07** (every CSV row must parse with exactly its header's field count) so this class of error now fails the build; negative-tested by corrupting a row and confirming exit 1 | |

## Source log (task → official source → what was checked)

Format: `task | source | URL | accessed UTC | what was verified | irregularities`.
`data/sources.csv` is the authoritative registry (SRC-001 … SRC-017) and every data row cites it.

| Task | Source | URL | Accessed (UTC) | What was checked | Irregularities found |
| --- | --- | --- | --- | --- | --- |
| T3 | NFL division standings (SRC-002) | https://www.nfl.com/standings/ | 03:12 | 32 clubs × W/L/T/PCT/PF/PA/NET; `PCT=(W+0.5T)/(W+L+T)`; `sum(PF)=sum(PA)=6291`; `sum(W)=sum(L)=136`; 274 team-games → 137 games | HOME/ROAD/DIV/CONF/STRK values render with **no header row** → withheld (FLG-002); 1 tie in the standings has no fixture in `games_2026.csv` (FLG-021) |
| T3 | NFL team stats - offense passing / rushing, defense passing (SRC-003/004/005) | https://www.nfl.com/stats/team-stats/offense/passing/2026/reg/all (+2) | 03:30 | 28 of 39 columns accepted after arithmetic proof; league identities att 9037 / cmp 5787 / yds 64098 / 1st 3026 / sacks 643 all hold off=def | **offense TD 414 vs defense TD allowed 415; INT 202 vs 200** → those 4 columns published but pricing-ineligible (FLG-025); 11 columns withheld (FLG-014); the "defense scoring" page is not points allowed (FLG-015) |
| T4 | NFL official injury report, Week 10 (SRC-001) | https://www.nfl.com/injuries/league/2026/reg10 | 03:08–03:16 | 160 designated rows across 28 clubs; only Out/Doubtful/Questionable accepted (`V-10`) | IR players absent from the report entirely (BAL example) → FLG-005; 8 cross-club affiliations unconfirmed → FLG-006/FLG-012; 1 row with an empty injury field → FLG-008; "Out" also used for rested players → FLG-009 |
| T2 | NFL important dates / practice-report policy (SRC-011) | https://www.nfl.com/news/2026-27-national-football-league-important-dates | 03:45 | filing cadence (Wed/Thu/Fri 4pm ET for Sunday games etc.), rested-player vocabulary | only reachable as a search snippet of the official page → `verified-from-snippet`, not used for pricing |
| T2 | 2026 NFL Rulebook landing page (SRC-009/010) | https://operations.nfl.com/rules-officiating/2026-nfl-rulebook | 03:50 | the four listed 2026 amendments (6-1-3, 6-1-5, 6-1-6, 19-2) | the rulebook PDF itself was not parsed → Rule 16 OT and roster/elevation rules remain unverified (FLG-003/FLG-004) |
| T3 | NFL weekly schedule pages (SRC-006/007) + scores (SRC-008) | https://www.nfl.com/schedules/2026/by-week/week-1 (…week-2, /scores/) | 03:22, 04:10 | 33 games cross-checked against the running records printed on the same pages | Week 1 opener labelled both "Sunday Night Football, September 9th" and Wednesday 2026-09-09 (FLG-011); `api.nfl.com/feed/schedule` returns 401/Varnish 54113 → not usable as an endpoint (FLG-013) |
| — | Absence check: no official odds | nfl.com (all pages read this session) | 03:00–04:10 | no spread/total/moneyline/prop price published by any league-controlled page | every `market_*` column on the site is blank by policy (F-14, FLG-010, Q-01) |

## Handoff log

| Time (UTC) | From | To | Task | Reason |
| --- | --- | --- | --- | --- |
| 2026-11-14T06:20Z | S1-b37bd750 | (any follow-on session) | T13 integration | Board is ready for PR → merge: run `python3 scripts/model.py && python3 scripts/build_board.py` after any `data/` edit; `fetch_nfl_data.py` still needs one run on a networked host (FLG-024) | |

## Conflict log

| Time (UTC) | Files | Other session | Resolution |
| --- | --- | --- | --- | --- |
| — | — | — | — |

---

## Rules (all sessions)

1. **Read this file first.** If a task is `in progress` with a live claim (< 60 min of commits),
   do not start it.
2. **Claim before editing**: write your session ID + file scope in the board, commit and push the
   claim immediately, then work.
3. **Non-overlapping scopes.** Work on your own branch `session-<id>/<task>`. Touch only files in
   your claimed scope. If you need a file another session owns, log a request in the *Change
   requests* section instead of editing it.
4. **Small frequent commits**; `git pull --rebase` before every push.
5. **Conflicts**: stop, resolve without discarding the other session's work, log it in the Conflict
   log.
6. **Finish with evidence**: record sources, verification performed and irregularities here, then
   mark `done`.
7. **Never mark verified without checking an official source and linking it.** Blank + flagged beats
   guessed. No inferred values.
8. **Shared outputs** (`data/*`, site index, navigation, `board/` static build) are rewritten only by
   the final integration session.
9. A claim older than 60 minutes with no commits may be taken over; note the handoff in the Handoff
   log.

## Change requests

| Time (UTC) | From | Target file | Owner | Request |
| --- | --- | --- | --- | --- |
| — | — | — | — | — |
