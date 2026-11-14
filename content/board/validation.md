# Validation gates

The brief: *"each strategy must pass validation gates… remove luck from the equation and build strategies
that are selectively skill based."* Gates are the mechanism. A signal is not adopted because it looks
sensible and it is not rejected because it had a bad month; it moves between those states by passing or
failing a named test with a number attached.

:::table gates.csv | 13 gates; G-01 to G-13; the "current state" column is the real status of the project | id,stage,gate,definition,pass_criteria,fail_action,why_this_removes_luck,data_required,current_state

## Why the thresholds look so large

The whole table sits on one arithmetic fact, computed from stated assumptions (not measured):

:::table decision_math.csv | closed-form break-even, sample-size, expectation and parlay thresholds | family,parameter,value,unit,derivation,note

Read the `sample size` rows: to *demonstrate* a 3-point hit-rate edge at −110 (95% confidence, 80% power)
needs **~2,169 independent bets**; a 2-point edge needs **~4,886**. At 17 games a week and a selective
strategy taking maybe 15-30 bets a week, that is **2-5 seasons of daily work for one strategy**. This is
why the gates feel obstructive: they are describing the real cost of separating skill from luck in a
near-efficient market. Anyone who finds a "55% ATS system" on 40 bets has found a coin that flipped.

The same table is also why **CLV is the primary gate** (G-03): a pricing model that beats the close on
its own numbers converges ~10x faster than P&L does, because it removes the game result - i.e. the luck -
from the evaluation.

## How each category removes luck

| Category | Gates | What luck it deletes |
|---|---|---|
| Time honesty | G-02 (walk-forward, sealed config), G-09 (regime) | the future informing the past; a good half-season masking a bad process |
| Statistical honesty | G-01 (N), G-04 (FDR across the catalogue, deflated Sharpe on the board) | "one of 400 signals went green"; the multiple-comparison tax |
| Market realism | G-03 (CLV), G-06 (vig, limits, fills) | backtests that assume a 0-vig, infinite-liquidity book |
| Structural honesty | G-07, G-08 (correlation, dedupe) | counting one injury report line as three independent edges |
| Data integrity | G-10 (source verification blocks publish) | a guessed number becoming a stake |
| Operational reality | G-11 (fillable, ban-safe), G-12 (anti-gaming), G-13 (luck-adjusted reporting) | unfundable edges and self-selected results |

## G-13, in one line

Report **the realised result and the expected result under our own probabilities** side by side every
week. If the gap closes over time, the process is honest and the variance is variance; if it never closes,
the model is lying to us - and the gate makes that visible in weeks rather than in a bankroll statement.

## What currently passes

Only **G-10** (source integrity) is genuinely live: the build aborts if a published row cites a source id
that is not registered, or if an identity check fails. Everything else is `blocked`, which is the
accurate description of a system whose inputs do not yet exist. The pass state is printed on every gate
row on this page from the CSV - so "we passed the gate" cannot be quietly remembered into existence.
