# COORDINATION.md — Shared Task Board

Repo: `sassnarep3-star/FL3` · Purpose: collect, organize and analyze NFL data to originate our own
lines, score strategies on a leaderboard, and publish a verified dashboard on GitHub Pages.

**Every session must read this file before touching anything, claim a row, and commit the claim
before editing.** Rules are at the bottom of this file.

- Last updated: 2026-11-14T03:05Z
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
| T1 | Source registry + verification protocol (`data/sources.csv`) | in progress | S1-b37bd750 | `data/sources.csv`, `docs/methodology/**` | Official-source-only rule; source classes defined here |
| T2 | League facts & rulebook inputs needed by the model | in progress | S1-b37bd750 | `docs/model/league-facts.md` | Roster/injury-report/OT/scheduling rules from the Official Playing Rules |
| T3 | 2026 season results & standings (official) → derived margin/total distributions | in progress | S1-b37bd750 | `data/games_2026.csv`, `data/standings_2026.csv`, `data/derived_stats.csv` | Only rows read off nfl.com get a value; the rest stay blank |
| T4 | Injury + availability dataset (official injury report) incl. backup/depthchart deficiency logic | in progress | S1-b37bd750 | `data/injuries_2026_w10.csv`, `docs/model/availability.md` | Week 10 report as of read time |
| T5 | Line origination model spec (spread, total, moneyline, props) | in progress | S1-b37bd750 | `docs/model/**`, `models/*.yaml` | Power ratings → margin/total → prices |
| T6 | Signal catalogue (single, parlay, prop combos) + leaderboard + reward design | in progress | S1-b37bd750 | `docs/signals/**`, `models/signals.yaml` | |
| T7 | Validation gates (anti-luck / skill isolation) + correlation policy | in progress | S1-b37bd750 | `docs/validation/**`, `models/gates.yaml` | Gate definitions, minimum-N math |
| T8 | Open questions, required information, known gaps | in progress | S1-b37bd750 | `docs/questions/**` | Blocking vs non-blocking |
| T9 | Suggestions register (review + choose best path before implementing) | in progress | S1-b37bd750 | `docs/suggestions/**` | No suggestion is implemented without an owner decision |
| T10 | Site generator + Pages publish + link checker | in progress | S1-b37bd750 | `site/**`, `scripts/build_site.py`, `docs/**` (static output) | `python3 scripts/build_site.py` |
| T11 | Flagged for Review page (irregularities + unverified items) | in progress | S1-b37bd750 | `data/flags.csv` | |
| T12 | Executive summary | in progress | S1-b37bd750 | `docs/executive-summary.md` | |
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
| — | — | (nothing yet) |

## Source log (task → official source → what was checked)

Filled in as each task completes. Format: `task | source | URL | accessed UTC | what was verified | irregularities`.

## Handoff log

| Time (UTC) | From | To | Task | Reason |
| --- | --- | --- | --- | --- |
| — | — | — | — | — |

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
8. **Shared outputs** (`data/*`, site index, navigation, `docs/` static build) are rewritten only by
   the final integration session.
9. A claim older than 60 minutes with no commits may be taken over; note the handoff in the Handoff
   log.

## Change requests

| Time (UTC) | From | Target file | Owner | Request |
| --- | --- | --- | --- | --- |
| — | — | — | — | — |
