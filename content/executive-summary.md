# Executive summary

**Project:** originate original NFL lines, test whether any strategy has genuine skill, and publish the whole chain so it can be audited.
**Snapshot:** 2026 NFL regular season, entering Week 10. All data captured **2026-11-14**.
**Live site:** https://sassnarep3-star.github.io/FL3/
**Session:** `arena-46e888f0`, branch `arena/46e888f0-fl3`.

---

## 1. The one-paragraph version

The repository was empty, so everything here was built from scratch and verified against official sources line by line.
It now contains a verified league snapshot (32 teams, the 14-game Week 10 slate), the complete official Week 10 injury
report (345 players), a depth-chart analysis that identifies exactly who replaces whom when a starter is ruled out
(43 confirmed starter losses, 27 teams), an original line model built only from published results, and a strategy lab
with eight pre-registered validation gates. The most important finding is a negative one and it is deliberate:
**no strategy can be called skill-based yet**, because there are no settled bets and no market odds to test against.
The site says that on its front page rather than showing a fabricated leaderboard.

---

## 2. What was verified, and how

| Claim | Verified value | Source |
|---|---|---|
| Current season and week | 2026 regular season, Week 10 | [NFL.com injury report](https://www.nfl.com/injuries/), [NFL.com schedule](https://www.nfl.com/schedules/2026/REG/Week10/) |
| Standings, all 32 teams | Transcribed verbatim, including PF/PA, records, streaks | [NFL.com standings](https://www.nfl.com/standings/league/2026/REG) |
| Week 10 slate | 14 games, 4 byes (CHI, DEN, PHI, TB), Thursday WAS 24–NYG 21 | [NFL.com schedule](https://www.nfl.com/schedules/2026/REG/Week10/) |
| Injury designations | 345 players across 28 teams; Out / Doubtful / Questionable / none | [NFL.com injuries](https://www.nfl.com/injuries/) |
| Depth order and draft pedigree | 27 team charts, decoded with the published key | [Ourlads](https://www.ourlads.com/nfldepthcharts/) |
| Thursday result cross-check | Matches independently | [ESPN scoreboard](https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?dates=20261112) |

**Two integrity checks passed that would catch a transcription error:**
- Across all 32 teams, points-for equals points-against equals **6,291**. That identity must hold physically.
- All 32 winning percentages recompute exactly from their own W-L-T records.

An automated harness (`scripts/verify.py`) re-runs 14 checks on every build and fails it if any break. It has already
caught two real defects during this session — an unreconciled rounding error in the line model, and a broken internal link.

---

## 3. The single most useful finding

**Ourlads and the official NFL report disagreed 14 times on player availability in one week.**

Examples: Ourlads marks Buffalo's Dion Dawkins as out; the official report gives him full participation and no
designation. Same for Seattle's Rashid Shaheed, Baltimore's Nate Wiggins and Houston's Reed Blankenship.

The resolution adopted — and **flagged for your confirmation** — is that the **official NFL report governs availability**
while **Ourlads governs depth order only**. Every disagreement is published, not averaged. This matters because it is
exactly the kind of silent error that would corrupt every downstream injury signal.

---

## 4. Injury and backup-deficiency analysis

43 confirmed starter losses were logged. The index weights how much *proven investment* a team loses when a starter
is ruled out, using draft round and depth position as proxies:

| Rank | Team | Starter losses | Risk index | Worst gap |
|---|---|---|---|---|
| 1 | Tennessee Titans | 4 | 1.62 | Carnell Tate (WR, Out) → Elic Ayomanor |
| 2 | Minnesota Vikings | 3 | 1.00 | T.J. Hockenson (TE, Out) → Josh Oliver |
| 3 | Houston Texans | 2 | 0.86 | Keylan Rutledge (G, Out) → Wyatt Teller |
| 4 | Seattle Seahawks | 4 | 0.76 | Charles Cross (T, Out) → Josh Jones |
| 5 | Green Bay Packers | 3 | 0.74 | Sean Rhyan (C, Out) → John Williams |

**Read this as an exposure ranking, not a prediction.** The weights are a stated proxy, and a late-round starter who
has played well scores badly. Snap-count data would fix it.

---

## 5. Line origination — what exists and what is missing

13 original lines were produced from published season results, using a shrunk offense/defense model. League scoring
baseline (**22.96 points per team-game**) is computed from the data, not assumed.

Three deliberate omissions, each published on the site and in the flagged register:

1. **Home-field advantage = 0.0.** No home/away *scoring* split was available. nfl.com publishes home/road win-loss
   records but not points. Inventing 2.5 points from memory would have been a hallucination.
2. **No injury adjustment.** The exposure index exists but has never been validated against outcomes, so it has not
   earned a place in the line.
3. **No market comparison.** No odds feed was reachable from this environment — so no closing-line value, no
   vig-adjusted EV, no "edge vs market" figure anywhere.

**Consequence:** the model lines are line *origination*, and they are compressed toward pick'em because of point 1.

---

## 6. Strategy validation

Eight strategies are registered, including the brief's requested forms: single bets, two-leg same-game parlays,
three-leg team-total parlays and player-prop combinations. Each must clear eight gates before it may appear on the
leaderboard: sample size (≥200 bets), holdout discipline, permutation noise floor, closing-line value, vig
survivorship at −110, stability, correlation control and luck removal.

- **Leaderboard: empty by design.** No bets have been settled, so gate G1 cannot pass.
- **Four strategies are blocked on missing input** — chiefly per-player game logs and a licensed odds feed. They are
  registered as `blocked-input` rather than quietly omitted.
- **Correlation is priced, not multiplied.** The engine uses a Gaussian copula and *refuses* to price a parlay when the
  correlation has not been estimated. Demonstrated: two 55% legs at ρ=0.6 have a true joint probability of **40.4%**,
  not the naive 30.3%.

---

## 7. Decisions only you can make

13 questions are open. These are the ones that gate everything else:

| ID | Question | Why it matters |
|---|---|---|
| **Q-04** | Can a licensed closing-line source be obtained? | Unblocks CLV, gate G4, market comparison, and one strategy |
| **Q-02** | Where does settled-bet history come from? | Without it the leaderboard can never fill |
| **Q-03** | Is Friday's report or the inactives list the grading truth? | Injury signals cannot be scored otherwise |
| **Q-08** | Will you ratify the skill thresholds *before* results exist? | Thresholds chosen afterwards are not evidence |
| **Q-01** | What home-field term should the model use? | Every line is compressed until this is answered |

---

## 8. Flagged for review

**30 items** are published on the Flagged for Review page, including 14 direct source conflicts, each with links.
Nothing there blocks publication; it is there so you can review after go-live. The three most consequential:

- **F-03** — no odds data exists anywhere in the repo.
- **F-04** — home-field advantage is 0.0.
- **F-11** — the leaderboard is empty because no bets are graded.

---

## 9. Bottom line

The data layer is verified and the methodology is written down and falsifiable. The honest current answer to
"which strategies have skill?" is **none proven, and the site says so**. The fastest route to a real answer is
**Q-04 plus Q-02**: a closing-line source and a settled-bet log would turn the existing machinery from a
well-specified test into a running experiment.
