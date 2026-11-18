# FL3 — Executive Summary

**Snapshot:** 2026-11-14 · **Season:** 2026 regular season, through Week 10
**Live site:** https://sassnarep3-star.github.io/FL3/

---

## 1. What was asked for, and what exists now

| Requirement | Status | Where |
|---|---|---|
| Collect and organise a full list of requirements | **Done** — 12 numbered decisions, 16 suggestions, 10 information gaps | `data/decisions.json`, `data/suggestions.json`, `decisions.html`, `suggestions.html` |
| Suggestions to improve decision-making, in a reviewable section | **Done** — every suggestion has 2–3 selectable paths, effort, cost, pros/cons and a recommendation | `suggestions.html` |
| A clear list of questions, knowns, unknowns before any decision | **Done** — 12 questions, 9 of them blocking, each with a "what discovers it" column | `decisions.html` |
| Suggestions that discover missing information | **Done** — all 10 gaps map to at least one suggestion | `decisions.html` ↔ `suggestions.html` |
| Originate our own NFL lines | **Done** — 14 Week 10 games, spread + total + win probability, each with a 90% band | `data/lines_week10.json`, `lines.html` |
| Strategies as a leaderboard with rewards | **Built, deliberately empty** — 8 specs, 8 gates, 5 tiers. Zero graded results, and the site says why | `strategies.html` |
| Single bet, parlay, player-prop combos | **Single + cross-game parlay specced; props blocked** with the exact missing input named | `data/strategies.json` |
| Every strategy passes validation gates | **Enforced** — 8 gates, machine-checked where possible; a gate that cannot run is a fail | `data/strategies.json` |
| Correlation values | **4 measured from verified data; 6 declared as assumptions with direction only** | `correlation.html` |
| Remove luck; be selectively skill-based | **Luck measured per club** (Pythagorean, ±2.17 wins range) and **a luck penalty in the score** | `standings.html`, `strategies.html` |
| Track injuries and defensive/offensive depth deficiencies | **Injuries done** (345 official rows, split by side of ball). **Depth ordinal is honestly blocked** — no official source exists | `injuries.html`, flag F05 |
| Executive summary | **This document**, plus the site dashboard | `docs/EXECUTIVE_SUMMARY.md`, `index.html` |
| No manual input; verification with source links | **6,154 automated assertions pass** (re-verified 2026-11-18 on branch `arena/0c322b0e-fl3`); every table row carries an official link | `scripts/check_site.py`, `sources.html` |
| GitHub Pages live site | **Done** | https://sassnarep3-star.github.io/FL3/ |

---

## 2. The five things that matter

**1. The data is real and it reconciles.**
All 32 clubs' 2026 records were read off NFL.com and cross-checked against a second official page.
`PF − PA = Net` holds for all 32. Every club's printed win percentage matches `(W + ½T) / games`.
The half-win tie rule itself is quoted from the official tie-breaking page, not from memory.

**2. We originate lines rather than import them.**
Each of the 14 Week 10 games gets an expected score for both clubs, derived from shrunk
offence/defence ratings, a 1.9-point home-field term, and a side-of-the-ball availability adjustment
(from the official injury report). Margin and total are the difference and sum of those two
expected scores — one coherent scoring model, not two unrelated formulas. Uncertainty widens as
evidence thins.

**3. Almost nothing can yet be called "good", and the site says so.**
Zero bets have been graded. The leaderboard is live and empty. Every strategy is a *spec*. The
Champion and Proven tiers are unreachable because **no licensed market price exists** (flag F07).
This is the single largest constraint in the project, and no amount of modelling fixes it.

**4. The depth-chart request cannot be answered from official data — so it is flagged, not faked.**
No NFL source publishes a 2nd/3rd/4th-string ordinal (flag F05). The line engine therefore applies a
per-position availability penalty with separate offence/defence caps, and labels it a model constant.
Suggestion SG-05 proposes participation counts as the honest substitute.

**5. Two official page contradictions were found, not smoothed over.**
The standings page does not yet include a game the schedule page marks FINAL (flag F01). And the
Week 10 injury table lists no Ravens quarterback, while NFL.com's own news module on the same page
reports Lamar Jackson out 6–10 weeks (flag F02). An engine reading only the injury table would miss
a starting-QB absence entirely. Both are published with links.

---

## 3. Measured facts worth acting on

| Finding | Value | Consequence |
|---|---|---|
| Win% vs point differential per game | **r = 0.878** (n=32, t=10.05, r²=0.771) | Scoring margin is the right primary rating input |
| Offence vs defence independence | **r = −0.204** (r²=0.042) | "Good offence + bad defence" is **not** a hedge; the intuition is wrong |
| Offence alone vs win% | **r = 0.698** (r²=0.487) | Offence-only signals need a wider band |
| Defence alone vs win% | **r = −0.664** (r²=0.441) | Defence-only signals need a wider band too |
| Luck range across the league | **+2.17 (DEN) to −2.17 (TB)** | Up to ~2 wins of a 9-game record are margin-unexplained |
| Week 10 injury rows with **no** game status | **185 of 345** | Availability signal is structurally incomplete |

---

## 4. What has to be decided before this becomes useful

In priority order — full detail on `suggestions.html`:

1. **SG-13** Capture game-by-game results. Without it nothing can ever be graded or calibrated.
2. **SG-02** Freeze each week's line at kickoff. Otherwise no future grade means anything.
3. **SG-06** Decide the market-price question. This decides whether "edge" is in scope at all.
4. **SG-10** Capture official player-game stats. Unblocks every player-prop correlation.
5. **SG-05** Adopt participation counts as the depth ordinal (the honest version of your request).

Each has 2–3 paths with costs written down. Nothing beyond what you see here was implemented
without a path already chosen.

---

## 5. Honest limitations of this build

- **8–9 games per club.** Every rating is provisional and the bands are wide on purpose.
- **League aggregates only.** No opponent adjustment, so a club that has played strong teams looks
  worse than it is.
- **One captured week.** No calibration, no backtest, no leaderboard entries.
- **No price.** No edge, no closing-line value, no top-tier strategies.
- **No player-level data.** Props stay blocked.
- **The Munich game** (NE @ DET) is at a neutral site but receives a full home-field advantage
  (flag F09) — worth up to ~1.9 points of error.
- **The local shell has no internet.** Refreshing data must run in CI (flag F08).

None of these are hidden. Each is a row on `flagged.html` with a link.

---

## 6. Verification

`python3 scripts/check_site.py` runs **6,154 assertions** and passes with zero warnings, covering:
Re-verified 2026-11-18 on branch `arena/0c322b0e-fl3`: ALL CHECKS PASSED, zero warnings. The count grew from 3,064 as sessions added the readiness register, matchup matrix, ablations, acceptance audit, comparison lab and character-split regression guards.

- arithmetic on official figures, for all 32 clubs
- completeness (32 clubs / 8 divisions × 4 / 14 games / 28 clubs on the slate / no club twice)
- source coverage (every dataset row has an absolute https source)
- link integrity (every internal href resolves, every anchor exists, no broken local targets)
- recomputation (the line, luck and correlation engines must reproduce the committed numbers)
- blank honesty (reported blank counts must match the actual data)
- flag publication (every flag is on the page with its evidence link)

Run it yourself:

```bash
python3 scripts/compute_lines.py
python3 scripts/compute_luck.py
python3 scripts/compute_correlation.py
python3 scripts/build_site.py
python3 scripts/check_site.py
```

Any number that changes is a bug, not an opinion.
