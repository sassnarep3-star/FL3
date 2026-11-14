# FL3 — NFL line origination, signals and verified dashboard

An NFL analytics system that (a) collects only what an official source publishes, (b) verifies it
arithmetically, (c) originates its own spreads and totals from the verified inputs, (d) specifies the
signals that turn a line into a bet, and (e) grades those signals on a leaderboard built so that **luck
cannot win**. A static, fully linked dashboard is published from `docs/` via GitHub Pages.

Live site: <https://sassnarep3-star.github.io/FL3/> ·
Coordination board: [COORDINATION.md](COORDINATION.md)

## The one rule everything else follows

> Every table row carries its source. A value that cannot be confirmed from an official source is left
> **blank and flagged**. Nothing is inferred to fill a gap.

That is why parts of this repo look unfinished: the odds columns are empty because no official source
publishes odds; the availability adjustment is `null` because a designation is not a lineup. A blank with
a reason is the deliverable, not a defect.

## Layout

| Path | What it is |
| --- | --- |
| `data/` | 23 CSVs — the entire knowledge layer: standings, games, team stats, injuries, sources, questions, suggestions, signals, gates, flags, derived metrics, calibration, ratings, priced slate, verification report |
| `content/` | the prose of each site page, with `:::table` directives that pull the CSVs in at build time |
| `docs/` | **generated** site (GitHub Pages) — never hand-edited |
| `scripts/` | `verify.py` (integrity gate), `model.py` (derive → calibrate → rate → price), `stats_tables.py`, `make_leaderboard.py`, `build_site.py`, `check_links.py`, `fetch_nfl_data.py` |
| `models/` | `line_model.yaml` (parameter register), `gates.yaml`, `leaderboard.yaml`, `strategy_registry.yaml` |
| `site/` | build inputs for the site (stylesheet, `.nojekyll`) |
| `COORDINATION.md` | multi-session task board: claims, scopes, source log, conflict log |

## Reproduce it

```bash
python3 scripts/model.py            # derived metrics, calibration, ratings, Week-10 prices
python3 scripts/stats_tables.py     # break-even / minimum-sample / parlay math
python3 scripts/make_leaderboard.py # board schema from the strategy registry
python3 scripts/build_site.py       # verify → render docs/ → link check (aborts on a failure)
```

Standard library only — no `pip install`, so the same build runs on a laptop and in CI.
`python3 scripts/verify.py` alone prints the integrity report; a blocking failure exits 1 and the build
stops (gate G-10). `python3 scripts/fetch_nfl_data.py --weeks 3-9 --what games` is the one command that
removes most of the "provisional" labels — note it has never been run in the authoring sandbox, which had
no route to nfl.com ([`COORDINATION.md`](COORDINATION.md) capability table).

## Status, honestly

| Piece | State |
| --- | --- |
| Data layer + provenance + verification | working; 32/32 clubs, 33/137 games, 160 availability rows |
| Model that prices a slate | runs end to end, **constants fitted on 33 games in-sample** — labelled provisional everywhere |
| Signal catalogue, gates, leaderboard schema | specified; 1 of 13 gates (G-10) is live, the rest wait on market data |
| Site | 20 pages, all generated, link-checked, deployed from the `site` workflow |
| Blockers | market prices (Q-01), lineups (Q-02), IR/transactions (Q-03), game history (Q-04) |

Nothing here is betting advice; nothing here claims a strategy is profitable. The strongest claim the
current data supports is that the pipeline would *detect* an edge, and this repo states exactly what it
still needs before that claim means anything.
