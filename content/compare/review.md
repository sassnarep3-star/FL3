# Session review — 2026-11-17

What this session checked in the repository, what it found, and what it changed. Every finding below
is reproducible from a committed file or a link to the official page.

## 1. Baseline: the repo was green before anything was touched

| Gate | Result |
|---|---|
| `scripts/verify.py` | GATE G-10 **PASS**, with the already-recorded non-blocking `V-09b / FLG-025` |
| `scripts/check_site.py` | 3,064 assertions, **ALL CHECKS PASSED** |
| `scripts/check_links.py` | 29 pages, 0 broken internal links, 0 orphans |
| `scripts/check_verify.py` | 203 assertions, PASS |
| `scripts/check_verified_site.py` | 605 assertions, PASS |

So this session had no broken build to repair. What it did find were **eight defects in the
analysis and the alarms**, listed below in the order they were found.

## 2. Defects found and what happened to each

| # | Defect | Evidence | Status |
|---|---|---|---|
| D1 | The scheduled availability capture has never stored a single capture. Its only run failed (exit 2) because the Week 11 injury route still renders the final Week 10 tables before the league publishes the week — the alarm could not tell "the season has not reached this week" from "our parser is blind". | [run 43974503837](https://github.com/sassnarep3-star/FL3/actions/runs/43974503837) | **fixed** — `classify()` splits `not_published_yet` from `drift`; unit-tested with `--selftest`; recorded in `snapshots/index.csv` |
| D2 | A "full-corpus" total of 148 games and the brief's "136-game log" were both in the repo with no statement of how they relate. | `data/week_results_2026.csv`, `data/standings_2026.csv` | **resolved and proved** — 136 → 137 → 148, points and clubs reconciled (`data/compare/corpus_reconciliation.csv`) |
| D3 | Two of four "independent" origination strategies would have been algebraically the same model, because with a single `pa` table the intelligence-meets-defence expression collapses to a net-points rating. Publishing that as four arms would have inflated the multiplicity count with a duplicate. | `scripts/build_compare.py`, `pa`/`def_rate` | **fixed** — a separate defensive rate, and the collapse is asserted against in the source comment so it cannot recur silently |
| D4 | The "different HFA variant" arm was also identical to its parent: adding hfa/2 to one score and subtracting hfa/2 from the other cancels in the margin, and the total was re-derived from a pace figure that made the two totals equal too. | `scripts/build_compare.py` | **fixed** — replaced with a Pythagorean, luck-stripped rating, which is a genuinely different quantity |
| D5 | The total-estimator comparison returned an exactly zero gap (and was labelled with a "winner") even though all three estimators had identical MAE to four decimals — the comparison could not distinguish them at all. | `data/compare/evaluation.json` before the fix | **fixed** — three distinct estimator families (pace / offence-only / pace+HFA), each with a paired bootstrap z |
| D6 | The published significance rule was "95% interval excludes zero" mixed with a Bonferroni alpha that was never actually applied to any decision. | `scripts/build_compare.py` | **fixed** — the verdict is now estimate / bootstrap SE against the adjusted critical value (z ≥ 2.87 for 12 comparisons), and the interval test is published separately |
| D7 | Two official NFL.com routes publish **different stadium names for the same Week 11 fixture**: the Colts–Texans game centre says `RELIANT STADIUM`; the Week 11 schedule page's own venue link resolves to NRG Stadium. | [game centre](https://www.nfl.com/games/colts-at-texans-2026-reg-11), [schedule](https://www.nfl.com/schedules/2026/by-week/week-11) | **published, not resolved** — `data/compare/week11_venues.csv` (QO-16), with a non-conflicting control row (MIN@SF / ESTADIO BANORTE) so the finding is not just a capture artefact |
| D8 | The Week 10 injury route (`reg11`) serves the **Week 10** tables with a Week 10 title. A reader could easily take `reg11` for Week 11 data. | [reg11](https://www.nfl.com/injuries/league/2026/reg11) (title reads "Week 10 of the 2026 Season") | **published** — no Week 11 availability is used anywhere in this session's output, and the page says so in the Week 11 section |

## 3. What this session did not change

- `data/week_results_2026.*`, `data/standings_2026.csv`, `data/standings_2026_wk10_verified.csv`,
  `data/captures/week10_injuries_2026-11-16.csv`, `data/official_injury_capture_wk10_2026.csv` —
  read-only inputs.
- `data/flags.csv`, `data/requirements_readiness.csv`, `data/questions.csv`, `data/suggestions.csv`,
  `data/sources.csv` — owned by other registers. New findings from this session are filed in
  `data/compare/questions.csv` (QO-01…QO-16) rather than appended to registers another session's
  generators validate.
- `models/**`, `verified/**`, `verify/**`, `docs/**`, `depth/**`, `site-9b181d31/**`, `legacy/**`.

## 4. Open defects this session found but did **not** fix

| # | Item | Why it was left open | Where it is recorded |
|---|---|---|---|
| O1 | Two unmerged pull requests (#23, #34) older than 24 h. | Neither blocks this work, and merging another session's data into the canonical tables is the owner's call, not this session's. | `COORDINATION.md` |
| O2 | Six published dashboards, each with its own numbers, and at least one pair that contradicts on the same figure. | Consolidating them means choosing whose numbers survive. Published as a suggestion (SC-09) instead. | `compare.html` §10 (SC-09) |
| O3 | The board's `data/games_2026.csv` holds 33 verified rows against a 148-game corpus. | Regenerating it needs the board's own generator and an owner decision on the canonical series (R070). | `compare.html` §8 |
| O4 | The root site's Week 10 line page and the board's line series disagree by several points on the same fixtures. | Same cause as O3; already on the Flagged for Review page. | `data/line_provenance_verdict.csv` |

## 5. The verification this session performed on its own output

```
python3 scripts/build_compare.py --check      # the lab reproduces exactly
python3 scripts/build_crosscheck.py --check   # the 136 -> 137 -> 148 chain reproduces
python3 scripts/capture_official_snapshot.py --selftest   # 8/8 classifier cases
python3 scripts/check_site.py                 # 3,450 assertions, ALL CHECKS PASSED
python3 scripts/check_links.py                # 30 pages, 0 broken links, 0 orphans
python3 scripts/verify.py                     # GATE G-10 PASS
```

The strongest single check is the 32-club identity in `data/compare/corpus_identity_32clubs.csv`:
the game rows are transcribed from the official per-week schedule pages, and every club's wins,
losses, ties, points for and points against are then compared with the official standings page. All
32 clubs match on all five figures, and the league balances at 6,824 points each way. A single
transposed score breaks it.
