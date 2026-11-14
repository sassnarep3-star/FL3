# Origination output - Week 10 slate

These are our numbers for the games still to come in Week 10, produced by the pipeline on
[Model](model.html) and written to `data/lines_origination.csv`. **They are not bettable prices.** The
status column says so on every row, and the reason is structural, not cosmetic:

1. the constants behind them are fitted on 33 games in-sample (`beta 1.14`, `sigma 11.92`);
2. there is no home-field term you could defend (`alpha = -0.82 ± 2.09`);
3. no schedule adjustment exists;
4. **no market number exists to compare against** - the `market_*` and `gap_to_market` columns are blank
   because no official source publishes odds ([FLG-010](flagged.html), [Q-01](questions.html));
5. availability adjustment is `null`, so a team missing its starting QB (MIN, SEA) is priced the same as
   one that is healthy - note `availability_flags` and see [Injuries](injuries.html).

## The slate

:::table lines_origination.csv | 14 games: our number, the market's number (blank), and the availability events we can see | game_date,kickoff_et,away,home,expected_home_margin,model_spread_home,model_p_home,model_total,hfa_applied,market_spread,market_total,gap_to_market,availability_flags,status,source_id

## How to read a row

**The one played game is the only honest test available.** Thursday's Washington at New York finished
24-21 ([SRC-008](sources.html)): our model expected a home margin of **+3.5** (Giants favored) on a
total of **44.9**. The game landed at **-3** on a total of **45**. One game proves nothing - the point is
that the pipeline produces a falsifiable pair of numbers *before* kickoff, and the error is
computable afterwards. That is the whole mechanism: 33 games of those pairs is what turns `beta` and
`sigma` into something you can defend.

**The unplayed slate shows the failure mode.** Buffalo at the Jets carries `model_spread_home = +15.8`
(New York a 15.8-point home dog, i.e. our line is Buffalo -15.8 on the road) - a number no sensible
operator would stake. The mean absolute spread across the slate is **8.6 points**, and
`model_total` ranges **29.8 to 59.5** (mean 47.1 against a verified league average of 45.92). Same
diagnosis in both cases, and both are visible in the register:

| What is wrong | Where it shows up | What fixes it |
|---|---|---|
| no shrinkage / regression to a prior | `beta = 1.14` in [calibration](model.html); mean absolute spread ~8.6 pts is far too wide | full-season fit ([Q-04](questions.html), gate G-05) |
| no schedule adjustment | `provisional-unadjusted` on every rating row | game-level opponents ([Q-04](questions.html)) |
| no availability adjustment | MIN and SEA each have a starting QB Out and the number does not move | lineups + IR merge ([Q-02](questions.html), [Q-03](questions.html)) |
| no vig / market comparison | blank `market_*` columns | odds licence ([Q-01](questions.html)) |

The totals are *level-correct* (47.1 vs 45.9) and *dispersion-wrong* (29.8 to 59.5 is not a real range
for 14 games) - an unidentified `gamma` on 33 games ([FLG-026](flagged.html)).

## Why publishing this anyway is the right call

A dashboard that only shows numbers the pipeline is confident in would show an empty table on 2026-11-14.
So the site publishes the output with its status on every row, and the [abstain rule](model.html) keeps
`actionable = no`. When Q-01 and Q-04 land, this table gains `close_spread`, `gap`, `ev`, `stake` and a
per-row `gate_status`, and becomes the screen where every bet is recorded *before* it is placed (gate
G-12). Nothing about the page has to be redesigned - only the blanks get filled.

