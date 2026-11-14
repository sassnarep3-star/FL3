# Line origination model

The brief: originate our own NFL lines, and know precisely which parts of the number are measured and
which are not. This page is the architecture and the register;
[Lines](lines.html) is today's output; [Validation gates](validation.html) is what the output has to
clear before it is ever called an edge.

## Pipeline

| Stage | Script | Input | Output | Verification |
|---|---|---|---|---|
| ingest | `scripts/fetch_nfl_data.py` | nfl.com pages (and, once licensed, an odds feed) | `data/*.csv` | records URL + UTC timestamp per row |
| verify | `scripts/verify.py` | `data/*.csv` | `data/verification_report.csv` | 13 identity checks; a failure aborts the build |
| derive | `scripts/model.py` | verified rows | `derived_*`, `model_calibration.csv` | only arithmetic over verified values |
| rate | `scripts/model.py` | standings + games | `power_ratings.csv` | no schedule adjustment (Q-04) - stated, not hidden |
| price | `scripts/model.py` | ratings + calibration | `lines_origination.csv` | every constant tagged with `n` and `status` |
| publish | `scripts/build_site.py` | everything | `docs/` | link check + source-registry check |

## Step 1 - team strength

Today: **unadjusted net points per game** from the official standings (`net_ppg` on
[Team stats](team-stats.html)), plus a **Pythagorean expected-win** rating whose exponent was fitted on
this data rather than borrowed (k = 3.4, SSE = 29.95 wins² over 32 clubs).

Both are published side by side in `data/power_ratings.csv` *with the schedule adjustment left blank*:
an opponent-strength correction needs game-level opponents for Weeks 3-9, which are not ingested.
Leaving that column empty is the design decision - the alternative is a rating that looks
opponent-adjusted and is not.

Next (S-12): a second, independent rating from possession efficiency, and publish the **disagreement**
between the two as the uncertainty measure.

## Step 2 - the conversion constants (fitted, not assumed)

`scripts/model.py` fits what it can, on the 33 verified games, and writes the result into the site:

:::table model_calibration.csv | every constant used to price a game, with its method, standard error and sample | constant,value,unit,se,n,method,status,note

Reading the numbers honestly:

- `beta = 1.140 ± 0.271`. Shrinking a rating gap should give `beta < 1`. Getting `beta > 1` in-sample on
  33 games is the fit telling us the sample is too small (and that ratings built from the whole season
  partially contain the games they are being fitted on). Flagged as
  [FLG-026](flagged.html), not smoothed over.
- `alpha = -0.82 ± 2.09` pts: home-field advantage in the ingested sample is **indistinguishable from
  zero**. Anyone quoting "2.0 pts for home" is quoting a memory, not this season.
- `sigma_margin = 11.92` pts: the residual spread a fair line must clear. At -110 you need roughly a
  1.0-1.5 pt better number than the market to be worth betting; with a model error of ~12 pts, that gap
  is enormous, which is the quantitative reason "most signals are noise".
- `gamma = 1.20` (grid boundary) - the multiplicative total model wants an exponent outside the search
  range on this sample, i.e. the total model is not identified yet.
- `r² = 0.364` - an unadjusted net-points gap explains about a third of the variance in a game margin.

## Step 3 - price the game

```
expected_home_margin = alpha + beta * (net_ppg_home - net_ppg_away)
spread_home          = -expected_home_margin          (rounded to 0.5 at publication)
P(home wins)           = Phi(expected_home_margin / sigma_margin)
moneyline             = 1 / P  minus the vig model   (BLOCKED: Q-01 - no official vig source)
total                 = L * (off_h/L)^g * (def_a/L)^g + L * (off_a/L)^g * (def_h/L)^g
prop (team-level)     = verified per-play rate x projected volume   (player-level blocked: Q-08)
availability adj      = null - the report does not identify replacements (Q-02, FLG-017)
```

`L` = 22.96 (league points per club per game, from 137 verified games), `g` = fitted gamma. Volume
inputs (`dropbacks = pass_att + sacks_taken`, `rush_att`) are official and identity-checked, which is
what makes a pace-based total at least *well-founded* even while it is not yet *accurate*.

## Step 4 - from a line to a decision

A price is not a bet. The gate between them is:

```
bet only if |model - market| > (vig + measured model error band)   # S-25 abstain rule
```

Right now `market` does not exist in the repo, so **the abstain rule always fires**, and the honest
output of the whole system is "no bet". That is the correct behaviour for a pipeline whose inputs are
provisional, and it is the difference between this project and a chart of guesses.

## Parameter register

The machine-readable contract is [models/line_model.yaml](https://github.com/sassnarep3-star/FL3/blob/main/models/line_model.yaml),
rendered as a table on the [Parameter register](parameters.html) page: each parameter carries `value`,
`evidence`, `status`, and where it is blocked, `blocked_by`. A parameter may not hold a value unless its
evidence points at a row that passed verification - so the `null` rows are not missing work, they are
the model refusing to guess. Read that page before believing any single number on the site.

## What is deliberately absent

- **No weather term** - nothing read from an official source (SRC-015, [Q-12](questions.html)).
- **No referee/crew term** - registered as [SIG-12](signals.html) with a "test once, then probably kill"
  disposition.
- **No "market bias" priors** ("the public overbets favourites"). Not because it is untrue but because
  the repo has no verified source for it, and an unmeasurable input in a pricing chain is how a model
  quietly becomes a story.
- **No player-level prop rates** ([Q-08](questions.html)).
