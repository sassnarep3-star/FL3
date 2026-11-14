# Team efficiency inputs - official

Three pages from the league's own team-stats section, read 2026-11-14:
[offense passing](https://www.nfl.com/stats/team-stats/offense/passing/2026/reg/all) (SRC-003),
[offense rushing](https://www.nfl.com/stats/team-stats/offense/rushing/2026/reg/all) (SRC-004),
[defense passing](https://www.nfl.com/stats/team-stats/defense/passing/2026/reg/all) (SRC-005).

These are the inputs the line model is allowed to use today: **volume** (pass attempts, dropbacks,
rush attempts), **efficiency** (yards per attempt, completion rate, sacks taken) and **opponent-side
reflections** (what each defence gave up).

## The column-label problem, and how it was solved

The static HTML renders 15 (passing) and 10 (rushing) numeric columns **with no label row**. Two steps
made the mapping provable instead of plausible:

1. **Per-row identities.** Only columns whose value is reproducible from other columns were accepted:
   `CMP% = CMP/ATT`, `YDS/ATT = YDS/ATT`, `1ST% = 1st downs/ATT`. 32 clubs × 8 rate columns all reconcile
   (`V-06`, `V-07`, `V-08`). Five of them sit on the .x5 rounding boundary and pass only with rounding
   slack - reported as a warning, not silently accepted (`V-11`).
2. **League-wide identities.** Every attempt faced by a defence is an attempt thrown by an offence, so
   the two independent tables must sum to the same number. They do, exactly:

| Stat | Sum over 32 offenses | Sum over 32 defenses | Result |
|---|---|---|---|
| pass attempts | 9,037 | 9,037 | identity holds |
| completions | 5,787 | 5,787 | identity holds |
| pass yards | 64,098 | 64,098 | identity holds |
| pass 1st downs | 3,026 | 3,026 | identity holds |
| sacks | 643 | 643 | identity holds |
| **pass TD** | **414** | **415** | **mismatch of 1 - [FLG-025](flagged.html)** |
| **interceptions** | **202** | **200** | **mismatch of 2 - [FLG-025](flagged.html)** |

The five clean identities are what prove the mapping. The two broken ones are what prove the discipline:
a normal pipeline would have used `pass_td` and `pass_int` in a model and never noticed they came from
tables that do not agree with each other. **Those four columns are published but marked
pricing-ineligible.**

Withheld entirely (no label, no identity): rushing TD, fumbles, 20+/40+ plays, longest, and the trailing
column on each table - 11 of 39 columns ([FLG-014](flagged.html)).

## Offense - passing (verified columns)

:::table team_pass_off_2026.csv | 2026 regular season through Week 9 - official per-club passing totals | team,abbr,games,pass_att,pass_cmp,cmp_pct,pass_yds,yds_per_att,sacks_taken,sack_yds_lost,pass_1st_downs,pass_1st_down_pct,source_id

## Offense - rushing (verified columns)

:::table team_rush_off_2026.csv | rushing volume and efficiency; the TD/fumble columns are withheld (FLG-014) | team,abbr,games,rush_att,rush_yds,yds_per_att,rush_1st_downs,rush_1st_down_pct,source_id

## Defense - passing (verified columns)

:::table team_pass_def_2026.csv | what each defence allowed; sacks is the last column, mapping confirmed by the 643 = 643 identity above | team,abbr,games,opp_pass_att,opp_pass_cmp,opp_cmp_pct,opp_pass_yds,opp_yds_per_att,opp_pass_1st_downs,opp_pass_1st_down_pct,def_sacks,source_id

## Derived per-game metrics (computed, not read)

`scripts/model.py` turns the three tables above into the per-club rates the model actually consumes -
points for/against per game, dropbacks per game (`pass_att + sacks_taken`), rush attempts per game,
pass rate, yards per play, opponent-side equivalents, Pythagorean expected wins with the **fitted**
exponent (k = 3.4, chosen on this data to reproduce the official W-L records) and the Week 10
availability load per position group.

:::table derived_team_metrics.csv | derived from SRC-002/003/004/005 + SRC-001; every column is a computation over the tables above | team,abbr,games,ppg,papg,net_ppg,pyth_expected_wins,dropbacks_per_game,rush_att_per_game,pass_rate_pct,yds_per_play,sacks_taken_per_game,opp_dropbacks_per_game,opp_pass_yds_per_game,def_sacks_per_game,status

## Where this is still weak

- **No games-played normalisation is available in the source**, so clubs with 8 games and clubs with 9
  are mixed in the totals; every rate here divides by that club's own `games` to stay honest.
- **Defence-side rushing and scoring pages are not what their names suggest**:
  `/stats/team-stats/defense/scoring/` returns defensive touchdowns, not points allowed
  ([FLG-015](flagged.html)), so points allowed comes from the standings instead.
- **No player-level rates at all** - which is the hard blocker for pricing individual props
  ([Q-08](questions.html)).
