# Methodology and verification record

This document records exactly what was verified, against which URL, on which date, and what
remains unverified. It is the human-readable twin of `scripts/check_site.py`.

## 1. Capture log

| Dataset | Official URL | Method | Date | Rows |
|---|---|---|---|---|
| Standings | https://www.nfl.com/standings/division/2026/REG | Page read, all 8 division tables | 2026-11-14 | 32 clubs |
| Standings cross-check | https://www.nfl.com/standings/league/2026/REG | Second rendering, different sort | 2026-11-14 | 32 clubs |
| Week 10 injuries | https://www.nfl.com/injuries/ | All 8 page chunks read end to end | 2026-11-14 | 345 player rows, 28 clubs |
| Week 10 schedule | https://www.nfl.com/schedules/2026/REG/ | Fixture list, kickoff, network, final scores | 2026-11-14 | 14 games |
| Week 10 by-week schedule | https://www.nfl.com/schedules/2026/by-week/week-10 | Confirmed same 14-game slate | 2026-11-14 | 14 games |
| Tie-breaking rules | https://www.nfl.com/standings/tie-breaking-procedures | Quoted the half-win tie rule | 2026-11-14 | policy |
| Injury policy | https://operations.nfl.com/the-rules/nfl-injury-report-policy/ | **Returned an empty body** | 2026-11-14 | 0 — flag F06 |

## 2. Verification performed

### 2.1 Arithmetic on official figures (all 32 clubs)

For every club: `PF − PA == Net Pts` exactly, and the printed `PCT` equals `(W + ½·T) / games`
to printed precision. Both are asserted in `check_arithmetic()`.

```
BUF  256−187 = 69   = printed Net   ✓
SF   235−156 = 79   = printed Net   ✓
LAC  121−219 = −98  = printed Net   ✓
NYG  5+0.5·1 / 9 = 0.611             ✓
WAS  3+0.5·1 / 9 = 0.389             ✓
```

### 2.2 Completeness

- 32 clubs present, 8 divisions, exactly 4 clubs per division
- 14 Week 10 games
- 28 clubs on the slate, none appearing twice
- 4 clubs absent (CHI, DEN, PHI, TB) — confirmed against two official schedule URLs
- Every `game_id` in the line file exists in the injury file and vice versa

### 2.3 Source coverage

Every dataset row carries a `src` field. The verifier regex-requires `^https://` and fails the
build otherwise. No row on the site can render without a source link.

### 2.4 Link integrity

Every `href` in every generated page is checked:
- external links must be non-empty and https
- internal links must resolve to a file that exists
- internal anchors (`page.html#anchor`) must match an `id=` in the target

### 2.5 Recomputation

`check_recompute()` re-runs the line engine, the luck model and the correlation engine. The
correlation engine compares its freshly computed values against `data/correlations.json` and
exits non-zero on any drift. This is how the four measured `r` values stay honest.

### 2.6 Blank honesty

The injury page states how many rows carry no game status. The verifier recomputes that count
from the data and fails if the page disagrees. A blank cell in the source stays blank on the site.

### 2.7 Flag publication

Every item in `data/flagged.json` must appear on `flagged.html` with its evidence URL. Resolved
items may omit links; open items may not.

## 3. Models and their declared constants

Everything below is a **model choice**, not a league fact. All are displayed on `lines.html`.

| Constant | Value | Justification |
|---|---|---|
| Home-field advantage | 1.9 pts | Declared; not fitted to a market |
| Prior strength | 2.0 games | Shrinks early-season ratings to league average |
| Single-game sigma | 8.5 pts | Game-to-game scoring noise floor |
| Sigma growth `k` | 8.0 | `sigma = base · sqrt(1 + k/games)` |
| Cap — offence | 3.5 pts | Stops one long injury list dominating |
| Cap — defence | 3.0 pts | Same, other side of the ball |
| Cap — specialists | 1.0 pt | Kicker/punter effect is real but small |
| Status weight — Out | 1.00 | Ruled out |
| Status weight — Doubtful | 0.60 | Convention |
| Status weight — Questionable | 0.25 | Convention |
| Pythagorean exponent | 2.37 | Standard NFL value, declared |
| Cross-game parlay haircut | 0.05 | Absorbs league-wide scoring shocks |

**None of these weights is quoted as a league rule.** The official page that would define
practice-status semantics returned an empty body (flag F06).

## 4. Judgment calls, stated openly

1. **Side-of-ball split.** A missing offensive player lowers his club's expected points; a missing
   defensive player raises the opponent's. Getting this wrong would push every injured team's total
   in the same direction. This is the most consequential modelling choice in the build.
2. **Blank status = zero penalty.** Conservative and symmetric. It understates risk for both clubs
   equally rather than inventing a probability.
3. **No market comparison at all.** Stated on every line rather than approximated from an unofficial
   source.
4. **Leaderboard left empty.** A populated leaderboard with n=0 would be fabrication.
5. **S04 (luck fade) kept on the board despite failing the spirit of gate G3.** It is the
   counter-example the luck filter exists to catch, and deleting it would hide that.

## 5. What was NOT verified, and why

| Item | Reason | Flag |
|---|---|---|
| Injury-report policy wording | Page returned empty body | F06 |
| Depth-chart ordinals | No official source publishes them | F05 |
| Market prices / closing lines | No official or licensed feed | F07 |
| Player-level per-game stats | Not captured in this build | — (M03) |
| Turnover margin | Not in the official standings table | — (M07) |
| CI network reachability to nfl.com | Workflow written but not yet executed live | F08 |
| Weather / venue conditions | Out of scope for v0 | F09 |

## 6. Reproducing this build

```bash
python3 scripts/compute_lines.py        # ratings + originated lines
python3 scripts/compute_luck.py         # Pythagorean luck decomposition
python3 scripts/compute_correlation.py  # measured r values, drift-checked
python3 scripts/build_site.py           # renders the 11 pages
python3 scripts/check_site.py           # 1124 assertions; exit 1 on any failure
```

Deterministic: the line engine uses no randomness. Re-running produces identical numbers.
