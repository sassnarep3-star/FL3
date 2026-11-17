# Strategy comparison lab

The full lab is published at the site root: **[Compare strategies](../compare.html)** — four
origination strategies and four controls, scored walk-forward over the 148 verified games in
`data/week_results_2026.csv`, with game-cluster intervals, a published multiplicity adjustment and
per-game ledger.

The one-page version is **[Executive summary](../executive-summary.html)**.

## What it establishes

* Every strategy beats a coin flip on the Brier score, and three of four beat a pick'em control on
  spread error.
* **No strategy survives the Bonferroni-adjusted threshold** for the 12 comparisons the page
  declares. The claim on the page is therefore "not established", not "wins".
* Predicted totals have no measurable relationship with actual totals (r = −0.03, n = 148), and a
  trailing-league-mean control beats every strategy on total error.
* The model is under-dispersed: its opinions are 0.26–0.58 as wide as reality, which is the
  mechanical reason no line can beat a price yet.

## What it does not do

No ROI, no CLV, no edge. No licensed price exists in this repository, so the staking column stays
blank by policy (readiness R005, R010). No retrospective number from this page may appear on the
prospective leaderboard.

## Sources

* Results: the official NFL per-week schedule pages,
  [Week 10](https://www.nfl.com/schedules/2026/by-week/week-10), identity-checked against the
  [league standings](https://www.nfl.com/standings/league/2026/reg).
* Week 11 fixtures: the [official Week 11 schedule](https://www.nfl.com/schedules/2026/by-week/week-11)
  (read 2026-11-17; the Week 11 injury report was not published at that time).
* Everything else on the page is model output and is labelled as such.

## Reproduce

```bash
python3 scripts/build_compare.py --check    # fails if the committed lab is stale
```
