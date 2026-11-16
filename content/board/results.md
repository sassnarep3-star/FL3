# Verified results feed — Week 10, 2026

**This page did not exist before 2026-11-16, and the site could not be scored without it.**

Every line, rating and availability number on this site was originated from a snapshot read on
2026-11-14. Week 10's Sunday slate was played on 2026-11-15. Until this page was built the site
priced twelve games that had already finished and had no record of how any of them ended. That
is the difference between a model and a press release.

## What is verified here, and how

Each row below is a score read from the NFL's own Week 10 schedule page on **2026-11-16 at
01:30 UTC**, with the individual game page for that fixture as the per-row link. Two of the
fourteen games had not finished at that clock time; they are **blank and marked not-final**.
They are not estimated, and they are not marked as anything they are not.

:::table captures_week10_results.csv | 14 Week 10 fixtures. Blank scores are games that had not finished at capture — not missing data, and deliberately not inferred. | game_id,away,home,away_pts,home_pts,state_as_published,capture_utc,game_page

## The two games that were still open

| Game | Kickoff (ET) | State at 2026-11-16T01:30Z | What this means |
|---|---|---|---|
| PIT at CIN | Nov 15, 8:20 PM | not final | Sunday Night Football; kicked off ~50 minutes after this capture |
| LAC at BAL | Nov 16, 8:15 PM | not played | Monday Night Football; the only Week 10 game with no result at all |

Both remain blank in every table on this site. `data/captures/week10_results_2026-11-16.csv`
carries an empty `away_pts`/`home_pts` and the literal string *KICKOFF … not played at capture*
for each. A later capture can fill them; nothing here guesses them.

## Why the feed is built this way

- **One row per fixture, keyed on the same `game_id` the slate uses.** The three line files in
  this repository key games three different ways (`W10-01`, `WAS-NYG-W10`, and full club names).
  Joining them by name is how the errors on the [lines page](lines.html) went unnoticed.
- **A clock time on every capture.** Not a build date, not a "retrieved" note — the UTC instant
  of the read, so a future scoring run can prove what was knowable and when.
- **No score is taken from a standings table.** Standings are derived and lag; the schedule page
  is the primary record. See [F01](../flagged.html) for the case where the two disagreed.

## What this unlocks, and what it still does not

It unlocks **scoring**: see the [removal-of-luck panel](luck.html) for the first prospective
grades this repository has ever produced.

It does **not** unlock ROI. A return needs a price, and this repository holds no licensed market
price (Q-01 / [FLG-010](../flagged.html)). The two market quotes that do exist in
`data/2026-week10-lines.csv` are attributed to ESPN and Sportsbook Review — third-party media,
not an odds vendor, and quoting them is not a licence to compute a return on them.

## Coverage, stated honestly

| Item | Value |
|---|---|
| Week 10 fixtures | 14 |
| Settled at capture | 12 |
| Not yet played | 2 |
| Seasons with a verified results feed | **1 week** |
| Games in `data/games_2026.csv` (the older corpus) | 33 of 137 through the point it covers |

One week is not a backtest corpus. The brief asks for the 136-game log to become a
pre-registered corpus; the gap between 33 and 137 rows is tracked as
[FLG-016] and is still open.

## Source

- Week 10 schedule with per-game final scores and game-page links:
  <https://www.nfl.com/schedules/2026/by-week/week-10>
- Per-fixture game pages are linked on every row above.
- Capture manifest with row counts and hashes: `data/captures/manifest.json`
