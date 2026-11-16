# Removal of luck — the first prospective grade

This page answers one question, for the first time with evidence rather than assertion:

> **Did the numbers on this site beat a coin flip, or did they get lucky?**

Short answer: **a bit of both, and the sample is far too small to say which.** Read the rest of
this page before quoting that sentence without it.

## Method, and why each choice was made

- **The forecast was frozen before kickoff.** `data/lines_week10.json` carries
  `meta.model_run_date = 2026-11-14`. It was written before the Sunday 2026-11-15 slate.
- **The Thursday game is excluded.** WAS-NYG (24-21) was already final when the forecast file was
  written, so scoring it would be scoring a post-hoc number. It appears in the results table and
  not in the headline sample. **Headline n = 11.**
- **Every game counts once.** The Brier interval is a game-level bootstrap (20,000 resamples,
  seed 20261116), not a per-observation interval, because games are the unit that was forecast.
- **Two benchmarks, both reported.** A coin flip is a weak benchmark; anyone can beat a coin.
  The sample's own base rate is the honest one, and it is the one that hurts.
- **No p-value, no ROI, no CLV.** n=11 cannot support a p-value; there is no licensed price to
  compute ROI or closing-line value against (Q-01 / FLG-010). Both are listed as missing rather
  than estimated.

## What the numbers say

| Test | Model | Benchmark | Result | Reading |
|---|---|---|---|---|
| Brier score (lower is better) | 0.2015 | coin 0.2500 | **beat by 0.048** | better than a coin |
| Brier score | 0.2015 | base rate 0.1983 | **lost by 0.003** | worse than always quoting "27% home" |
| Brier skill vs coin | — | — | **+0.194**, 95% CI **[-0.018, +0.385]** | the interval includes zero |
| Log loss | 0.5932 | coin 0.6931 | beat | consistent with Brier |
| Log loss | 0.5932 | base rate 0.5860 | lost | consistent with Brier |

Two things follow, and they are the whole point of this page:

1. **The coin-flip win is not established.** The bootstrap interval on the skill score runs from
   slightly negative to strongly positive. On 11 games that is what "we cannot tell yet" looks
   like when you write it down honestly instead of rounding it to a win.
2. **The right benchmark beats the model.** Home teams won only 3 of 11 games in this sample. A
   model that never deviates from "27% home" would have scored slightly better. This is a
   property of a small, skewed sample more than a verdict on the model — which is exactly why
   the model cannot be declared good or bad from it.

## Pricing error, decomposed

A single error number hides two different diseases. Bias is a constant offset and is cheap to fix.
Dispersion is how spread out the model's opinions are compared with reality, and it is not cheap.

| Quantity | Value | Why it matters |
|---|---|---|
| Mean signed error (bias) | **+7.91 pts** | the model is systematically ~8 points too "home" |
| Mean absolute error | 12.04 pts | per-game accuracy |
| RMSE | 14.89 pts | punishing large misses, as it should |
| MSE decomposition | 221.7 = bias² 62.6 + error variance 159.2 | ~28% of the error is a fixable constant |
| sd of model margins | 3.41 pts | |
| sd of actual margins | 14.39 pts | |
| **Dispersion ratio** | **0.24** | the model's opinions are ~4× too timid |

**This is the most actionable finding in the repository.** The model varies its forecast spread
across games by about 3.4 points. Reality varied by about 14.4. A forecast that is nearly constant
cannot pass a line test however good its average is, and the repository's own availability
adjustments are applied at a scale far smaller than the noise they are meant to explain. Fixing
bias does not fix this; the opinion distribution itself has to widen, and widening it requires
knowing *which* games are genuinely more uncertain — which needs the inputs this repo does not yet
capture.

## Result luck

| Quantity | Value |
|---|---|
| Picks won | 8 of 11 |
| Expected wins, from the model's own probabilities | 6.61 of 11 |
| **Luck gap** | **+1.39 wins** |

The model won **1.4 more games than it predicted it would**. Those 1.4 wins belong to variance,
not to the model, and a leaderboard that ranked on win rate would have paid for them. This is the
concrete reason the brief asks for signal and staking to be separated: at n=11 the gap between
"What happened" and "What was expected" is larger than most models' entire edge.

## Calibration

| Stated home-win probability | n | Mean stated | Observed home wins |
|---|---|---|---|
| 0.00 – 0.40 | 4 | 0.355 | **0 of 4** |
| 0.40 – 0.50 | 1 | 0.430 | 0 of 1 |
| 0.50 – 0.60 | 4 | 0.553 | 2 of 4 |
| 0.60 – 0.70 | 2 | 0.622 | 1 of 2 |
| 0.70 – 1.00 | 0 | — | — |

The lowest-confidence bucket went 0 for 4. With four games that is noise, and it is reported as
noise. But it is directionally the same skew as the +7.91-point bias: in this sample the model was
too confident about home teams that lost.

## What would change our mind

Per the rule that every strategy entry carries a two-sided reversal condition, so does this page:

- **Evidence the model has skill:** a walk-forward sample of 200+ games, a Brier skill interval
  against the base-rate benchmark whose lower bound clears zero after a multiplicity adjustment
  for the number of strategies tried, and a dispersion ratio that rises above ~0.7.
- **Evidence the model has none:** the same test run on 200+ games where the base-rate benchmark
  still wins. That outcome would retire the model rather than tune it.

Neither test can be run today: the repository has one scored week and 33 verified game rows.

## Reproduce

```
python3 scripts/capture_official.py     # official captures, dated and hashed
python3 scripts/score_week10.py         # this page's numbers, printed and written
```

Machine-readable output: `data/luck_panel.json`, `data/scoring_week10.csv`.

## Sources

- Week 10 final scores: <https://www.nfl.com/schedules/2026/by-week/week-10>
- Frozen forecast: `data/lines_week10.json` (`meta.model_run_date = 2026-11-14`)
- Per-game result rows with their own game-page links: [Results feed](results.html)
