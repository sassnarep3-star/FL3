# Signal catalogue

Sixteen candidate signals, written as *falsifiable specifications* rather than opinions. Every signal
carries: the hypothesis, the trigger that must fire from data the repo actually has, the market it
points at, its sample status, its gate status, and - critically - **its correlation with the other
signals and with the same game's other bets**.

Nothing here is "live": all 16 are `blocked` at gate G-01 or worse, because the inputs that would test
them (market prices, full game history, lineups) do not exist in the repo yet. That is the state of the
art on 2026-11-14, and pretending otherwise is the specific failure this whole project is built to
avoid.

:::table signals.csv | 16 specified signals across single bets, parlays and prop combos | id,name,family,hypothesis,trigger_rule,market,direction,expected_magnitude_status,sample_status,gate_status,correlation_note,source_class_of_trigger

## Families

| Family | Signals | What they share |
|---|---|---|
| Availability-driven | SIG-01, 03, 04, 05, 06, 08, 11 | one root cause: the *official report* - so they must never be treated as independent evidence (gate G-08) |
| Schedule-driven | SIG-07 | rest/travel, from official dates; includes the two 2026 international fixtures (Munich, East Melbourne) |
| Market-driven | SIG-09, 10, 16 | require prices ([Q-01](questions.html)) - the only family that can measure a real edge |
| Structural / parlay | SIG-13, 14, 15 | defined by the [correlation](correlation.html) between their own legs |
| Kill-it-first | SIG-12 (officials) | specified so it can be tested once and retired, not kept as a story |

## Two of them are worth reading in full

**SIG-01 - starting-QB replacement.** Hypothesis: the move that matters is not the designation but the
*identity of the replacement*, and the market is slowest exactly when the replacement is a third-stringer
because the report does not say who that is. Trigger today: a QB is `Out` on the report (this week:
Kyler Murray at MIN, Sam Darnold at SEA) or an official wire says the IR designation has landed. Required
input the repo does **not** have: the next QB up and how many career attempts he has
([Q-02](questions.html)). Until then the direction is stated, the size is `unmeasured`, and no stake is
computed. The correlation note matters as much: this signal is *the same event* as every passing-volume
prop in the game, so a "three-leg parlay" built from it is one bet with extra vig.

**SIG-16 - model-vs-market residual at the close.** This is not really a signal; it is the *scoring
function* for all of them. Definition: take the game only when `|model − close|` exceeds the abstain
threshold; evaluate with mean CLV and log-loss versus the close. Every other row in this table should be
promotable to "bet" only by improving SIG-16's numbers, not by its own P&L. If a signal cannot be
expressed as an improvement in SIG-16, it is a narrative.

## The promotion ladder

1. **spec** (all 16 today) - written, inputs named, no numbers.
2. **backtest-eligible** - inputs exist and pass gate G-10; still no money.
3. **paper** - runs against live data with timestamped predictions (hash-committed, gate G-12); ≥ N_min
   bets (gate G-01 - see [Validation](validation.html): a 3-point hit-rate edge at -110 needs about 2,169
   bets to be *shown* at 95% confidence, not 30).
4. **capped-live** - small fixed stake, CLV tracked, limits and fill-rate logged (G-06, G-11).
5. **funded** - only after G-03 (CLV), G-04 (FDR), G-05 (sensitivity), G-09 (regime) all pass.

Signals are allowed to move down the ladder instantly. A gate breach (G-02 violated, G-10 failed, or a
flagged input used) demotes to `spec` and voids the results - which is what makes the reward on the
[leaderboard](leaderboard.html) mean something.
