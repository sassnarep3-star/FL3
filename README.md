# FL3 — NFL Decision System

A verified-data dashboard for originating NFL lines, grading strategies against validation gates, and
tracking availability risk — with every league value linked to an official NFL.com source.

**Live site:** https://sassnarep3-star.github.io/FL3/
**Snapshot:** 2026-11-14 · 2026 regular season, through Week 10

---

## What this is

| | |
|---|---|
| **Data** | 32 clubs' 2026 records, the full Week 10 slate, and 345 official injury-report rows — all read from NFL.com and reconciled |
| **Lines** | 14 originated spreads and totals with explicit uncertainty bands. Not copied from a sportsbook |
| **Strategies** | 8 specs, 8 validation gates, 5 reward tiers, and an honest empty leaderboard |
| **Decisions** | 12 questions with what is known, what is not, and what unblocks each |
| **Suggestions** | 17 suggestions, each with 2–3 selectable paths and a recommendation |
| **Flags** | 13 irregularities on a dedicated review page, each with its evidence link |

## What this is not

Not betting advice. Not a sportsbook quote. Not a track record — **zero strategies have graded
results**, and the site says so on every relevant page. Where a value could not be confirmed against
an official source, the cell is blank and the gap is listed on the Flagged for Review page.

---

## Repository map

```
index.html … methodology.html     generated site (11 pages, no JS, no framework)
assets/site.css                   the only stylesheet
data/
  standings.json                  32 clubs, official 2026 figures, each row sourced
  injuries_week10.json            345 official injury rows across 14 games
  lines_week10.json               originated lines + uncertainty
  team_power.json                 the ratings behind the lines
  luck.json                       Pythagorean luck decomposition
  correlations.json               4 measured r values + 6 declared assumptions
  strategies.json                 8 specs, 8 gates, 5 tiers
  decisions.json                  12 questions, facts, and 10 information gaps
  suggestions.json                16 suggestions with selectable paths
  flagged.json                    10 review items with evidence
  sources.json                    every source used, plus the ones rejected
scripts/
  compute_lines.py                ratings + originated lines (deterministic)
  compute_luck.py                 Pythagorean luck
  compute_correlation.py          measured correlations, drift-checked
  build_site.py                   renders the 11 pages
  check_site.py                   1124 assertions; exit 1 on any failure
  fetch_official.py               optional refresh: reports changes, never auto-writes
docs/
  EXECUTIVE_SUMMARY.md            the summary
  METHODOLOGY.md                  verification record, constant by constant
legacy/                           archived data-free blueprint from a parallel session
COORDINATION.md                   shared task board + merge/collision record
```

## Build and verify

```bash
python3 scripts/compute_lines.py
python3 scripts/compute_luck.py
python3 scripts/compute_correlation.py
python3 scripts/build_site.py
python3 scripts/check_site.py      # must print ALL CHECKS PASSED
```

Deterministic: no randomness anywhere, so a re-run must produce identical files. CI enforces this
and fails on any diff.

## Source policy

Only `nfl.com` and `operations.nfl.com` count as evidence. Third-party aggregators, DFS projections
and public consensus lines are explicitly rejected in `data/sources.json` with the reason recorded.
A model output is always labelled as model output and never phrased as a league fact.

## Known constraints

- 8–9 games per club, so every rating is provisional and the bands are wide on purpose.
- League aggregates only — no opponent adjustment.
- One captured week — no calibration or backtest.
- **No licensed market price**, so edge, closing-line value and the top two reward tiers are out of
  scope until that is resolved (flag F07/suggestion SG-06).
- No official depth-chart ordinal exists, so "2nd/3rd/4th string" is a model estimate, not a fact
  (flag F05/suggestion SG-05).

All of these are on the live Flagged for Review page with links.

## Parallel sessions

Read `COORDINATION.md` before editing anything. Claim a task, keep scopes non-overlapping, and never
mark something verified without an official source link.

---

## Session `arena/9b181d31` subsite (`docs/`) and data/model layer

A parallel session built a second, self-contained dashboard under `docs/` plus a
deterministic line-origination engine and CSV datasets. It coexists with the root
site above (published at `/docs/` on Pages).

- `docs/` — 12-page dashboard: dashboard, executive summary, requirements register
  (Q1–Q14), suggestions board (S1–S8 with options + recommended path), originated
  lines vs the market (Week 10), injuries & depth-deficiency tracker (generated from
  the CSVs), strategy catalog behind validation gates G0–G8, leaderboard design,
  methodology, data hub, source registry, flagged-for-review (F1–F16).
- `data/*.csv` — machine-readable datasets with per-row source links (162 tracked
  injury rows = 160 official report + 2 IR rows; 78 deficiency rows; 32-team
  standings; W10/W11 slates; originated lines; correlation matrix). Unverified
  cells are **blank + flagged**, never inferred.
- `models/originate_lines.py` — deterministic engine (stdlib only): net-points
  ratings + HFA + transparent injury weights + QB-room cap. `models/build_pages.py`
  renders the CSV-driven pages and syncs `docs/data`, `docs/models`, `docs/research`.
- `research/sources.md` (fetch log, 23 sources + cross-session fold-ins) and
  `research/verification-log.md` (checks: sum PF = sum PA = 6,291 ✓; 274 team-games
  even ✓; every row sourced ✓).

Market references (ESPN, SBR/bet365, CBS, betus, BetMGM) are labeled **trusted
market** — never "official" — and used only as the comparison column for our own
originated lines. Model output is badged as model output everywhere.
