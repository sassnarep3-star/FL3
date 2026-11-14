# Week 10 availability - injuries, backups and what they cost a team

Source: the [official NFL injury report for Week 10](https://www.nfl.com/injuries/league/2026/reg10)
(SRC-001), read 2026-11-14T03:08Z–03:16Z. All 28 clubs in the Week 10 slate were read (the page renders
in 8 chunks; chunks 0-6 carry the club tables), but **only 26 of them contribute a row with a game
status**: Baltimore's section carries practice designations with no Out/Doubtful/Questionable value, and
the Chargers' section contributes none — and those two clubs play each other on Monday night, so their
`availability_flags` on [Lines](lines.html) are blank *because nothing was published*, not because anyone
is healthy ([FLG-028](flagged.html)). The Monday and Thursday slates are included.

## What the table below is

Every player on the Week 10 report who carries a **game status** (Out / Doubtful / Questionable), with
the injury text, the final practice participation and the game they belong to. 160 rows.
Rows with only a practice designation (no game status) are counted per club in the availability-load
table below, not listed individually, because the point of this page is *what a lineup looks like after
the designations land*.

`position_group` is an internal mapping from the report's position string (T/G/C → line, DE/DT → front,
CB/S → secondary, etc.) and is labelled as such - the report's own position field is not always right
(Seahawks QB Patrick O'Connell appears as `LB`, [FLG-007](flagged.html)).

:::table injuries_2026_w10.csv | 160 designated players, Week 10 slate | game_date,team_abbr,player,pos,injury,practice_status,game_status,flag,source_id | 60

(The complete 160-row table is in [data/injuries_2026_w10.csv](data/injuries_2026_w10.csv); the site
shows the first 60 rows for legibility.)

## Availability load by club - the "who is replacing whom" question

:::table derived_team_metrics.csv | Week 10 designation counts per club, grouped by position unit | team,abbr,avail_out,avail_doubtful,avail_questionable,avail_ol_out,avail_db_out,avail_dl_out,avail_qb_out,status

**What the counts show for the Sunday slate:** Minnesota and Seattle each have a QB listed Out
(Murray; Darnold), Green Bay is missing a starting RB and a starting edge rusher, Cleveland's report is
nearly empty while Houston's is missing a pass-rusher and a top receiver, New Orleans has three
offensive-line designations, and so on.

**What they do not show:** Baltimore's report contains eight rows and *no* game status at all, while the
official news feed on the same page says the franchise quarterback is expected to miss 6-10 weeks
([FLG-005](flagged.html)). **A player on injured reserve does not appear on the weekly report.** Any
deficiency metric built from the report alone will therefore call the most important absence of the week
"healthy" - which is the single most important fact on this page.

## Rules this page is built on

- **Filing cadence** (SRC-011, official): clubs file a Practice Report by 4:00 p.m. New York time on
  Wednesday, Thursday and Friday for a Sunday game; Monday/Tuesday/Wednesday for a Thursday game;
  Thursday/Friday/Saturday for a Monday game; and the equivalents for other days. The fetcher is
  scheduled to those deadlines, not to an arbitrary cron.
- **A rested player is on the report too**: the policy lists non-injury absences as
  `Not injury related - resting player` (five such rows this week), and the game status can still be
  `Out` (JAX Bates, JAX Davis, HOU Al-Shaair). "Out" is therefore not always medical.
- **Full practice + Questionable is normal** (NYJ Wilson, KC Walker III, MIA Baker Jr…) and so is
  **full practice + Out** (JAX Green II). The designation is a disclosure obligation, not a prediction
  ([FLG-009](flagged.html)).
- **Probable is not in the modern report.** The page's own vocabulary is Out / Doubtful / Questionable
  and `V-10` rejects anything else; the historical probability language ("Questionable = 50%") is not
  part of the policy and is not used anywhere in this repo.

## How a model is supposed to use this

1. `designation` → **availability event** (who is unavailable, for which game).
2. `position group × unit` → **which phase is degraded** (line, front seven, secondary, backfield).
3. *missing* `depth chart` → **how degraded** — this step is currently impossible from official data
   and is why `availability_adjustment` in the model register is `value: null`
   ([Q-02](questions.html), [FLG-017](flagged.html)).
4. `practice trajectory` → **probability the designation converts to active**, which is the input to
   signal [SIG-02](signals.html) and cannot be read from a single day's report at all - the fetcher
   therefore stores every filing per week, not just the last one.

## Irregularities on this page, listed plainly

- 8 clubs have a player listed on their report who, before 2026, was associated with another club
  ([FLG-006](flagged.html)); all are marked `FLG-012` in the row's `flag` column and none was silently
  corrected.
- One row (NE, Hunter Henry) is `Questionable` with an **empty injury field**; the blank is published as
  a blank ([FLG-008](flagged.html)).
- The context statements on this page (Jackson 6-10 weeks, Darnold out / Lock starting, Willis to IR,
  Nacua to IR, Jacobs surgery) come from **headline text on the official page**; the articles behind them
  were not opened this session, so they are inputs to the *research queue*, not to any price
  ([FLG-022](flagged.html)).
