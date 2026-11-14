# Leaderboard, rewards and staking

The brief wants the strategies competing on a leaderboard that pays the best ones. That is a good idea
with a fatal failure mode: **if the reward is paid on realised profit, the rational entry is a
high-variance bettor, and the prize selects for luck.** Everything below is designed so that the strategy
that *wins the board* is the strategy that is actually good at pricing.

## The board, as it stands today

:::table leaderboard.csv | every specified strategy enters at zero; no metric is filled until a settled bet exists | strategy_id,strategy,family,tier,exposure_group,bets,beats_close_pct,mean_clv_pts,log_loss_vs_market,roi_units,luck_adjusted_roi,max_drawdown,gate_status,config_hash

Sixteen strategies, all `no settled bets`. **No number on this table has been invented.** That is the
point: the board is a real object in the repo, its schema is the evaluation contract, and filling it is
the work.

## Scoring

```
skill_score =  w1 * (-log_loss_vs_market, z-scored)          # prediction quality  - primary
             + w2 * (mean CLV in points, z-scored)           # market-beating      - primary
             + w3 * sign(luck_adjusted_roi) * min(1, bets/N_min)   # profitability, sample-weighted
             - w4 * (max_drawdown / bankroll_limit)
             - penalty(gate breaches)                        # G-02/G-10/G-12 breaches -> demote + void
weights:  w1 = 0.35, w2 = 0.35, w3 = 0.25, w4 = 0.05
```

Two choices matter:

- **Prediction quality is scored on log-loss, not on win/loss.** Log-loss punishes a 70% claim that
  loses and rewards a well-calibrated 55% claim; it is measurable on ~200 bets where ROI needs thousands
  (see the [decision math](data/decision_math.csv) sample-size rows).
- **Profit is *sample-weighted*, never displayed raw.** A strategy with 40 bets at +18% ROI ranks below
  one with 900 bets at +4% ROI, and `min(1, bets/N_min)` is what encodes that.

Rewards are then allocated from `skill_score`, with a **share cap per strategy** so the board cannot be
won by one oversized lucky week, and a **freeze**: a strategy's method hash is recorded at entry (gate
G-12) and changing the model mid-season forfeits the standing. Full formula and tier rules live in
[models/leaderboard.yaml](https://github.com/sassnarep3-star/FL3/blob/main/models/leaderboard.yaml).

## Tiers

| Tier | Entry requirement | Bankroll | Consequence of a gate breach |
|---|---|---|---|
| spec | written inputs + hypothesis | none | - |
| paper | inputs verified (G-10) | simulated units only | reset to spec |
| capped-live | G-01 `N_min` met on paper + G-03 positive CLV | fixed 0.25u per bet, 2u slate cap | stake halved for 4 weeks |
| funded | G-03, G-04, G-05, G-09 all pass | fractional Kelly (0.25) of measured edge | demoted to capped-live |
| retired | fails twice in one season | 0 | results frozen and published as a negative |

**Reward design:** the pool is paid 60% on the season's `skill_score`, 25% on the **improvement** in
skill_score (so a new strategy can earn without an all-time record), and 15% to the best *documented
negative result* - a prize for killing a popular signal with evidence. That last line is deliberate:
a board that only pays winners produces a research culture that never publishes losses, which is exactly
the failure mode the rest of this repo exists to prevent.

## Staking rules (all of them, because they are short)

1. Break-even is **52.38%** at −110 and **54.55%** at −120 props; below that nothing compounds.
2. Fractional Kelly at 0.25 of the measured edge; never of the *assumed* edge.
3. Per-bet cap 2% of bankroll; per-slate cap 8%; per-causal-driver cap 3% (gate G-08's exposure rule).
4. Stand-down after two consecutive gate breaches, or any G-10 data failure.
5. A bet is void for scoring if it was placed after our published number was updated (timestamp check).

These are parameter choices, not truths - and the caps themselves await [Q-17](questions.html): the
owner has to state the bankroll and the acceptable drawdown. Until then the tiers are the policy, and the
numbers inside them are placeholders by design.

## What the board will look like in four weeks if nothing else is approved

Identical to the table above. Filling it requires [Q-01](questions.html) (prices) and
[Q-04](questions.html) (games), and that is the honest dependency chain: **no leaderboard can be built on
a data layer that does not exist yet** - which is the correct answer to "why is the board empty".
