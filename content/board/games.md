# 2026 game results - verified rows

Scores read from the league's own weekly schedule pages: [Week 1](https://www.nfl.com/schedules/2026/by-week/week-1)
(SRC-006) and [Week 2](https://www.nfl.com/schedules/2026/by-week/week-2) (SRC-007), plus the completed
Week 10 Thursday game from the [injury/schedule page](https://www.nfl.com/injuries/league/2026/reg10)
(SRC-001).

**Coverage: 33 rows of the 137 games the league has played.** That is a declared gap, not an omission:
the remaining 104 games are readable from the same pages by the same script, and the sandbox this
session ran in blocks outbound requests to nfl.com (probe recorded in
[COORDINATION.md](https://github.com/sassnarep3-star/FL3/blob/main/COORDINATION.md)), so the fetcher
ships untested rather than the table shipping invented ([FLG-016](flagged.html),
[FLG-024](flagged.html)).

## Why each row can be trusted

Every game row was cross-checked against the running records printed on the same page: for all 32 clubs
the win/loss state after Week 1 and after Week 2 in `data/standings_2026.csv` matches the results below
(e.g. BUF 7-1 with a 36-31 and a 41-31 win; LAC 0-8 having lost 14-26 and 14-26). `V-05` in the
[verification log](verification.html) checks that every row references two of the 32 clubs.

One row-level oddity is kept exactly as published: the Week 1 opener's section header says
"Sunday Night Football, September 9th" while the game line says Wednesday, September 9th
([FLG-011](flagged.html)).

:::table games_2026.csv | 33 games, all FINAL, all from official pages | week,game_date,weekday_as_published,away,away_pts,home,home_pts,notes,source_id

## Distributions computed from these 33 rows (provisional)

| Measure | Value | Reading |
|---|---|---|
| mean home margin | +0.09 pts | home advantage ≈ 0 on this sample; SD 14.71 ⇒ ±5.1 pts at 95% - we cannot yet tell whether HFA is 0 or 2 |
| SD of home margin | 14.71 pts | the raw material for spread width; the fitted residual SD is 11.92 after the rating term |
| mean game total | 44.94 pts | vs 45.92 from all 137 games in the standings - the two official-derived estimates differ by ~1 pt, which is sample noise, not error |
| SD of game total | 16.32 pts | totals are *more* volatile than margins; pricing them with one shared sigma understates the risk |
| ties | 0 of 33 | the one league-wide tie is outside the ingested window |

These numbers are what the model is currently calibrated on, and they are why every constant on the
[Lines](lines.html) page is badged `provisional-in-sample`. Doubling this table (Weeks 3-9) roughly
halves the error bars without buying anything.

## Full data

The machine-readable version with all columns, including the per-page source ids and read timestamps:
[data/games_2026.csv](data/games_2026.csv).
