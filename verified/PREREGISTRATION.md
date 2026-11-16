# Pre-registration — FL3 shadow baseline, version 1

**Registered:** 2026-11-16 · **Registration commit:** the commit that adds this file to `arena/03e651e0-fl3`
**Status:** frozen. The rule text below, the sample window and every gate are fixed *before* any
prospective forecast exists. Changing any of them creates version 2 with a new commit and the change is
published; version 1 is never edited.

This file exists because a strategy that can be re-described after its results are seen is not evidence.
The commit hash is the registration.

---

## 1. What is being registered

A **singles-only shadow baseline**: a team-strength rating model that originates a spread, a total and a
moneyline for every remaining 2026 regular-season game, published before kickoff, never staked.

It is a *baseline*, not a product. Its purpose is to be the thing every future strategy must beat. If a
more elaborate model cannot beat this, the elaborate model is not worth running.

| Field | Value |
|---|---|
| Model ID | `FL3-SHADOW-1` |
| Market families | side (spread), then total, then moneyline — in that publication order, per game |
| Bet structure | **singles only**. No parlays, no same-game parlays, no prop combos (§7) |
| Staking | none. Zero currency is risked. Any ROI figure is hypothetical and must be labelled so |
| Evaluation | proper scores (Brier / log loss) plus calibration, both with game-cluster CIs |

## 2. The model, stated completely

Fitted only on games whose official final score exists and whose kickoff is before the forecast deadline.

```
For each club t:
    games        g_t
    points for   pf_t          (sum of its own scores, all games to date)
    points against pa_t
    shrink       w = g_t / (g_t + k),   k = 4.0
    offence      off_t = w * (pf_t / g_t) + (1 - w) * L
    defence      def_t = w * (pa_t / g_t) + (1 - w) * L
    L = 22.0 points per club per game

For a game away A at home H:
    exp_away = L + (off_A - L) + (def_H - L)
    exp_home = L + (off_H - L) + (def_A - L) + HFA
    HFA      = 1.9 points        (declared constant, NOT fitted; see §8)
    spread_home = -(exp_home - exp_away)
    total       = exp_away + exp_home
    p_home      = 1 / (1 + exp(-(exp_home - exp_away) / (sigma * 0.55)))
    sigma       = 8.5            (declared constant, NOT fitted; see §8)
```

Every constant above is fixed now. **`k`, `L`, `HFA` and `sigma` are not to be re-tuned** during the
evaluation window. That is the whole point: a parameter that can move with the results cannot be tested.

`scripts/preregister_model.py` implements exactly this text. The registered output is a hash of the
model's forecast for every fixture in the window, so a later change to the implementation is detectable
even if the prose is untouched.

## 3. Publication deadline (no lookahead, ever)

A forecast enters the record only if it is committed **before** the earliest of:

* the official scheduled kickoff, and
* any observed line movement or news event for that game.

A forecast for a game that has already kicked off is **rejected**, not back-filled. The record keeps
rejected attempts with the reason, so the rejection rate is auditable.

This rule exists because the repo already contains one contaminated forecast: the Week 10 model file
(`data/lines_week10.json`) includes WAS at NYG, which was FINAL before the file was committed. That game
is excluded from every score on this site and is recorded as excluded in `data/line_eval.json`.

## 4. Sample window

| | |
|---|---|
| Ramp | 2026 Week 11 through Week 13 — forecasts published, scored, **not** used to rank anything |
| Evaluation | 2026 Week 14 through Week 18 |
| Minimum n to publish a skill figure | **80 scored singles** |
| Minimum n to rank a strategy above another | **200 scored singles** |
| Season rollover | the window closes at the end of Week 18 and is never extended after the fact |

At roughly 14–16 games per week and one side per game, the ramp yields about 45 forecasts and the
evaluation window about 80. **The baseline will therefore be eligible to publish a skill figure only near
the end of the season, and eligible to rank against another strategy not at all this season.** That is
stated here, before the fact, so that a thin result cannot later be presented as a thick one.

## 5. Primary metric, fixed now

**Primary:** Brier score on the moneyline win probability, scored at the club level (two forecasts per
game), reported as skill relative to a coin flip:

```
BSS = 1 - (Brier_model / Brier_coin)
```

**Secondary, reported but never substituted for the primary:**

* spread error (MAE and RMSE in points) against a pick'em baseline;
* total error against the trailing league mean;
* calibration curve and expected calibration error, with the number of games in each bin;
* log loss, for anyone who prefers it — reported alongside Brier, never instead of it.

**Explicitly not used as a primary metric:** win rate, units won, ROI, "record". A 7–4 run is 11 coin
flips. These may be displayed only next to the primary metric, never ranked by.

## 6. Uncertainty and multiplicity

* **Interval:** 95% percentile interval from at least 4,000 bootstrap resamples taken **by game**, not by
  row, because a game's margin and total move together.
* **Multiplicity:** the leaderboard shows every strategy ever registered, including abandoned ones, and
  applies a Benjamini–Hochberg false-discovery adjustment across the number of live hypotheses. Reporting
  the best of twenty without that adjustment is how noise gets published.
* **Minimum detectable effect:** at n = 200, the 95% interval on Brier skill is roughly ±0.06. A strategy
  claiming +0.03 is claiming something this design cannot see. Stated now so it cannot be argued later.

## 7. What cannot be ranked at all

Parlays, same-game parlays and prop combos are **excluded from the leaderboard entirely** until both
conditions hold:

1. a directly validated *joint* probability exists for the exact combination (not the product of
   marginals — multiplying marginals under dependence overstates the combo's probability), and
2. the operator's void/push/withdrawal rules are obtained from the operator in writing.

Neither condition is met for any combo in this repo. The correlation section publishes what is known about
dependence and states plainly that the naive product is wrong; it does not produce combo probabilities.

## 8. Known weaknesses, declared in advance

These are not excuses to be produced after a bad result; they are stated now.

1. **No opponent adjustment beyond the opponent's own def/off term.** This is a crude two-way rating. It
   is likely to be beaten by any model that uses opponent-adjusted efficiency, and that is a useful
   result if it happens.
2. **`HFA` and `sigma` are declared, not fitted.** With 148 games, fitting them in-sample and then
   scoring on the same games would flatter the model. Declaring them is the honest choice; it is also
   likely to cost accuracy.
3. **No injury signal in the registered baseline.** Availability data is verified but incomplete
   (`data/live_verification.csv` LV-04/LV-05), and adding a feature whose input is known to be partially
   wrong would contaminate the baseline. Injury features are a *separate* registered variant (§9).
4. **Early-season forecasts are weak by construction.** After Week 1 every club has one game, so the
   shrinkage term dominates and the model barely leaves the league mean. Weeks 11+ do not have this
   problem, which is why the window starts at Week 11.

## 9. The only permitted variants, registered at the same time

Each is a separate strategy ID, scored separately, and none may be described as "the model" without its
ID:

| ID | Change from `FL3-SHADOW-1` |
|---|---|
| `FL3-SHADOW-1-A` | adds the availability feature set; same constants, same window |
| `FL3-SHADOW-1-B` | adds rest-days differential from the published schedule; no injury data |

Ablation rule, registered now: the difference between `-1` and `-1-A` is the **measured effect of the
availability features**, reported with its own interval. It is not a fixed points penalty, and no result
from it may be turned into "a missing starter is worth N points" without an interval that excludes zero.

## 10. The "what would change our mind" field, required for every strategy

Any strategy entry on the leaderboard that does not carry both of these is invalid and is not displayed:

* **Disconfirming evidence:** the specific pattern of results that would falsify the strategy's premise.
* **Stopping rule:** the condition under which it is demoted to paper — stated with a number in advance,
  e.g. "demote if the lower bound of its Brier skill interval is below −0.05 after 200 scored singles."

For `FL3-SHADOW-1`:

* **Disconfirming evidence:** a spread RMSE gain over pick'em whose 95% interval includes zero after 200
  scored games, or a Brier skill interval including zero at the same n. Either means the rating carries no
  usable information and should be replaced, not tuned.
* **Stopping rule:** demote to paper — it is already paper — and stop publishing a skill figure if the
  interval lower bound is below −0.05 after 200 scored singles. Retire the model rather than re-fit it
  inside the window.

## 11. What would falsify this whole pre-registration

Recorded so the process can fail visibly:

* if `scripts/preregister_model.py` output does not hash to the registered value, the implementation drifted;
* if any scored forecast has a `published_utc` later than its kickoff, publication discipline failed;
* if a strategy appears on the leaderboard without a registration commit, the registry was bypassed.

Any of those three voids the affected results and is published on the review page, not silently repaired.
