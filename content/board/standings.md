# 2026 standings - official

Source: the league's own [division standings page](https://www.nfl.com/standings/) (SRC-002), read
2026-11-14T03:12Z. This is the aggregate record of every club through Week 9 plus the Thursday game
of Week 10.

## What was published and what was withheld

The static render carries the numbers but **not the column header row**, so only columns pinned by an
arithmetic identity were accepted:

- `W, L, T` → checked against `games` and against `PCT = (W + 0.5·T) / (W + L + T)`.
- `PCT` → verified for all 32 clubs; the two tie records (NYG, WAS) are only reproducible with the
  0.5·T term, which is why the plain `W/(W+L)` formula fails (found by `V-01`, first run).
- `PF, PA, NET PTS` → verified with `PF − PA = NET`.
- **Withheld: HOME, ROAD, DIV, CONF, STRK** - the values are visible on the page but their labels are
  not machine-readable in this render, and a value assigned to the wrong label would enter the model as
  fact. See [FLG-002](flagged.html).

## Verification that ran on this table

`scripts/verify.py` recomputes, at build time: `V-01` (per-club internal consistency), `V-02`
(net points), `V-03` (league-wide `sum(PF) = sum(PA)` and `sum(W) = sum(L)`), `V-04` (team-games must
be even). All pass. Current report: [verification log](verification.html).

:::table standings_2026.csv | Through Week 9 2026 - 32/32 clubs, every row from SRC-002 | team,abbr,conf,div,games,w,l,t,pct,pf,pa,net_pts,source_id,accessed_utc

## What this table already answers

| Question the line model asks | Answer from this table alone |
|---|---|
| How many games have actually been played? | 137 (`sum(W+L+T) = 274` team-games, `V-04`) |
| League scoring level? | 22.96 pts per club per game (6,291 total points, `sum(PF)=sum(PA)`) |
| Is anyone genuinely unbeaten/winless? | 0-8 LAC is the only 8-loss club; no club is unbeaten |
| How big is the gap between best and worst? | net points: JAX +13.50/g vs LAC −12.25/g → a 25.75 pt spread of *unadjusted* team quality |
| How often does a game end tied? | 1 tie in 137 games = 0.7% - a real push-rate input for spreads and moneylines (see [FLG-021](flagged.html) - the tied fixture itself is not yet in [game results](games.html)) |

## What it cannot answer (and must not be asked of it)

Home/road splits, division strength, schedule difficulty, or any per-game distribution: those need the
game-level rows in [Q-04](questions.html). Points per game here mixes 8- and 9-game clubs, which is
why every derived rate in this repo divides by that club's own `games`.
