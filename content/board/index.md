# FL3 - NFL line origination and signal board

A working system for **originating NFL lines**, turning them into **betting signals**, and
**grading the strategies that produce them** - built only from data that can be traced to an
official source, with every unconfirmable value left blank and listed on the
[Flagged for review](flagged.html) page.

**Two tracks, one repo.** A parallel session built a dashboard from the repo root
(`../index.html`, generated from `data/*.json` by its own `scripts/build_site.py`). This board is the
`S1-b37bd750` track: CSV-first data, an arithmetic verification gate, and a model whose constants are
fitted rather than assumed. Neither track overwrites the other's files, and both are published from the
same Pages build. Cross-references are one click away in the left rail.

The board is generated. Every table you see is rendered from `data/*.csv` by `scripts/build_board.py`;
if a value is not in the CSV it does not exist on the site, and if a CSV row fails an identity check
the build stops. Start with the [Executive summary](executive-summary.html), then decide the items in
the [Suggestion register](suggestions.html).

## What is real right now

- **32 of 32 clubs** loaded from the official [standings](standings.html) page, identity-checked
  (`sum(PF) = sum(PA) = 6,291`, `sum(W) = sum(L) = 136`).
- **33 row-verified games** of the 137 games the league has actually played through Week 9
  ([game results](games.html)) - the rest is a *coverage gap we declare*, not a gap we paper over.
- **160 availability rows** for the Week 10 slate, read off the [official injury report](injuries.html),
  including the backup-vs-starter damage per position group.
- **A priced Week 10 slate** with fitted constants - see [Lines](lines.html). The market columns are
  blank on purpose: **no official source publishes odds**, so nothing was filled in by hand.
- **15 signals, 13 validation gates, 20 open questions, 25 suggestions** - each with a stated
  dependency, so you can see what has to be bought or read before a decision is defensible.

## The one-line status

The **architecture, the data discipline and the evaluation machinery are done and reproducible.**
The **pricing itself is not trustworthy yet**, and it is not presented as such: the four numbers that
make a spread into a price (home-field value, residual SD, shrinkage, vig) are fitted on 33 games and
are labelled `provisional-in-sample` everywhere they appear.

## Blocking list

| # | Blocker | Why it is blocking | Fix |
|---|---|---|---|
| 1 | No market prices | Without opening/closing lines there is no CLV, no gate G-03, no leaderboard scoring | licence a vendor - [Q-01](questions.html) |
| 2 | No lineups / depth charts | "Which backup is in" cannot be computed from the weekly report | club charts + inactive lists - [Q-02](questions.html) |
| 3 | IR is invisible in the report | Baltimore's Week 10 report looks healthy while its franchise QB is out 6-10 weeks | merge transactions - [Q-03](questions.html) |
| 4 | Only 33 of 137 games ingested | Every distribution is provisional | run `scripts/fetch_nfl_data.py` on a networked host - [Q-04](questions.html) |
| 5 | No owner mandate | Stake sizes, kill switch and rewards need an owner, not an agent | [Q-17](questions.html), [S-19](suggestions.html) |

## Read it in this order

1. [Executive summary](executive-summary.html) - findings, not features.
2. [Questions & gaps](questions.html) - what must be answered before any decision.
3. [Suggestions](suggestions.html) - the paths, with impact/effort/risk; approve the ones you want.
4. [Model](model.html) → [Lines](lines.html) → [Signals](signals.html) → [Correlation](correlation.html)
   → [Validation gates](validation.html) → [Leaderboard & rewards](leaderboard.html).
5. [Methodology](methodology.html) and [Verification log](verification.html) to audit the numbers,
   and [Sources](sources.html) to click through to the official page behind any cell.

> Nothing on this site is betting advice, and nothing here says a strategy is profitable. The best
> claim the current data supports is: *this pipeline would detect it, and this is the evidence it
> still needs.*
