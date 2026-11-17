# Injury / availability ablation (chronological holdout)

The full ablation study lives on the sibling dashboard:
**[Ablations at the site root](../ablations.html)** — the identical originated-line model is run
twice on the same Week 10 holdout: once **with** the verified availability features (Week 10
official injury-report game statuses) and once **without** them. This is the brief's requirement
to replace fixed injury penalties with *measured* ablations (readiness **R028 / R029**).

## What was compared

* **Variant A — availability ON:** the published model, applying the capped availability adjustment
  built from the official Week 10 injury report (Out / Doubtful / Questionable).
* **Variant B — availability OFF:** the identical model with the availability adjustment zeroed.
* The two variants share the **same** power ratings (calibrated on verified Weeks 1-9 only) and
  differ **only** in the availability adjustment.

## Method and uncertainty

* **Chronological split:** ratings are fixed on verified Weeks 1-9; every forecast is scored against
  the verified Week 10 results played afterwards.
* **Metrics:** MAE and RMSE for the spread and the total; Brier for the home win probability.
* **Uncertainty:** non-parametric bootstrap over the holdout games (seed 20261117, 20,000 reps),
  95% percentile intervals, plus a paired difference (ON − OFF) for each metric.

## Honest result

The head-to-head is on the root page. On the Week 10 holdout the availability features show **no
demonstrated spread-MAE or Brier advantage** (both paired 95% CIs span zero). The total-MAE paired
difference is negative with a CI that excludes zero, but with only the scored Week 10 games in the
holdout the sample is small, so it is reported as a single-window result — **no skill advantage is
claimed**. These are model-evaluation numbers and are **not** leaderboard entries; the brief forbids
backtest numbers on the leaderboard.

## Sources and authority

* Availability: the [official NFL Week 10 injury report](https://www.nfl.com/injuries/league/2026/reg10)
  (`data/injuries_week10.json`), captured 2026-11-14/16.
* Results: the verified per-game results corpus `data/week_results_2026.csv` (Weeks 1-10, every row
  linked to an official [NFL.com schedule](https://www.nfl.com/schedules/2026/REG10) page).
* Ratings: power ratings built from Weeks 1-9 cumulative standings reconstructed from those verified
  scores.

## Exclusions and limitations

* **Depth-tier features are excluded.** The depth-tier source is unverified for most clubs
  (readiness R042 is BLOCKED), so the brief's own gate forbids building that feature until a route
  is verified for all 32 clubs.
* Availability is captured for Week 10 only, so the head-to-head comparison is on the scored Week 10
  holdout (small n; wide intervals).
* No market price is used and no bet is recommended. Model output only.
