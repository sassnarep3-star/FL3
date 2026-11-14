# Signal Research, Validation Gates, and Luck Removal

Status: **research plan** — no signal has been tested; the leaderboard is empty by design
until the gates below are satisfied.

## 1 · Candidate signal families (each must be pre-registered)

| Family | Verified inputs available | First testable when |
|---|---|---|
| Availability/depth | W10 injury snapshot (345 rows, official source per row); derived deficiency counts | S-01/S-02 give point-in-time history |
| Fundamentals | Standings: PF, PA, net pts, home/road/div/conf splits | Now (baseline-only), richer with S-04 |
| Situational | Schedule: rest days, kickoffs, international venue, byes | Now (baseline-only) |
| Market-relative | — | Blocked on S-05 (licensed odds archive) |
| Depth-string (2nd/3rd/4th string) | — | Blocked on S-03 (verified depth charts) |

## 2 · Signal design rules

1. **Hypothesis first.** Each signal is registered with: name, market, exact feature
   definitions and their official sources, expected direction, exclusion rules, and the
   evaluation window — committed before any test.
2. **Point-in-time integrity.** Features may only use what was knowable before kickoff
   (archived snapshots). Final injury reports may never be substituted for pre-kickoff
   states (this is the leak the F-04 flag protects against).
3. **Blank discipline.** A missing verified value is a missing feature — not a zero, not
   an average, not "no injury".
4. **No narrative features.** Anything that matters becomes a measured, sourced feature;
   stories do not enter the model.

## 3 · Validation gates (a strategy passes all gates before ranking)

- **G1 Pre-registration** — hypothesis, features, costs, scoring, and gates committed
  before testing (S-06).
- **G2 Chronological holdout** — parameters tuned on earlier weeks/seasons only; the
  declared evaluation window is untouched until the final run.
- **G3 Baseline comparison** — must beat (i) a naive baseline (e.g., points-differential
  favorite) and (ii) a no-skill baseline, on the same windows and costs.
- **G4 Calibration** — predicted probabilities track observed frequencies (reliability
  curve; calibration error with confidence bounds per
  [NIST uncertainty guidance](https://www.itl.nist.gov/div898/handbook/eda/section3/eda352.htm)).
- **G5 Sample & significance** — pre-declared minimum sample and uncertainty interval;
  a record without its interval is not a result.
- **G6 Dependence audit** — bets within a strategy are tested for clustering/dependence
  (same-game legs, correlated props) before ROI is reported.
- **G7 Replication** — the run is reproducible from committed code + archived snapshots
  by another session.
- **G8 Review** — a human reviewer confirms the gates on the Flagged/coordination record
  before the strategy is listed.

## 4 · Correlation (determination plan)

- Paired historical outcomes are collected (game outcomes × prop outcomes) with
  timestamps and sources.
- Dependence is estimated (rank correlation / logistic dependence models) **with
  uncertainty intervals**, never point values alone.
- Parlay pricing uses the estimated joint distribution; stress tests re-price with
  dependence at the interval bounds.
- Until this dataset exists, no correlation value appears anywhere on the site, and
  combos stay out of leaderboard scope (S-11).

## 5 · Removing luck from the verdict

Luck cannot be deleted; it can be bounded and made visible:

1. Pre-declared sample sizes and scoring before outcomes are known.
2. Confidence intervals on every published rate (NIST-style limits).
3. Calibration (G4) separates good forecasts from lucky records.
4. Baseline-relative scoring (G3) removes the "everything wins in a friendly sample" effect.
5. Replication (G7) re-runs the exact pipeline on untouched data.
6. The leaderboard publishes rank **with** sample size, interval, and gate status — a
   streak alone is never a rank.

## 6 · Luck vs skill in bet types

- **Singles:** cleanest skill isolation — one event, one distribution; primary leaderboard
  currency (S-11).
- **Parlays:** variance compounds; only admitted after G6 dependence audit and priced from
  measured joint distributions.
- **Player-prop combos / same-game combos:** strongest dependence; require the correlation
  layer first; correlation caps stress-tested.
