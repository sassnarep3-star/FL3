# Depth and replacement evidence — what the club pages actually publish

The brief asks the system to track "2nd, 3rd or 4th string backups having to replace starters."
This page records what could be verified about that **from the clubs' own pages on 2026-11-16**,
and — just as importantly — what those pages cannot be made to say.

Every claim below was checked against the live page. Where the brief's description did not match
what the page publishes, the page wins and the discrepancy is recorded.

## The five formatting failures, confirmed or refuted

| # | Claim in the brief | Verdict | What the page actually shows |
|---|---|---|---|
| 1 | Texans publish depth as an image | **CONFIRMED** | The heading is the literal string *"Unofficial Depth Chart"* and the body is one raster image. No player name exists in the HTML. |
| 2 | Packers prepend jersey numbers to names | **CONFIRMED** | Every cell reads `"9 Christian Watson"` — integer, space, name, no separator. Recoverable: split the leading integer, store jersey and name separately. Both are kept in `data/depth_blocks.csv`. |
| 3 | Baltimore still lists Lamar Jackson and Tyler Huntley at QB | **REFUTED** | The page reads **QB1 Jacoby Brissett, QB2 Joe Fagnano, QB3 Kedon Slovis**. Neither Jackson nor Huntley appears. The staleness story is real, but not this one. |
| 4 | Seattle puts two players in one slot | **CONFIRMED** | One WR cell contains **two** players: Cooper Kupp and Rashid Shaheed. The club named no starter. |
| 5 | Washington leaves a slot empty | **NOT CHECKED** | Not read this session. The Ravens *do* leave rank 1 empty (kicker), so the phenomenon is real; the Washington instance is unverified and is left blank rather than asserted. |

## The grammar a depth chart uses — and why "column 1 = the starter" is false

:::table depth_grammar_findings.csv | Every structural irregularity found in the three transcribed charts, with the page it came from. | club,kind,row,detail,url

Six distinct structures break a naive parse, and all six are present in just three clubs:

- **shared_slot** — two players in one cell. Seattle WR. Whoever reads column 1 as "the WR1"
  invents a starter the club did not name.
- **duplicate_rank1** — one player at rank 1 of two positions. Green Bay publishes **Kitan
  Oladapo** at rank 1 of *both* safety spots. That is one player covering two slots, not two
  starters. Reading it as two starters would double-count him in any availability calculation.
- **duplicate_rank2** — one backup, two roles. Baltimore's **Ryan Neuzil** is rank 2 at both LG
  and C; **Carson Vinson** is rank 2 at both LT and RT. Losing one starter promotes the same man.
- **empty_rank1** — Baltimore publishes **no kicker at all** at rank 1.
- **continuation_row** — Green Bay's RB4 **Kaleb Johnson** sits under a *blank position cell*,
  continuing the row above. A parser keyed on the position column silently drops him.
- **image_only** — Houston. The data is not in the document at all.

## Staleness is published, or it is not

| Club | Effective date the page publishes | Age on 2026-11-16 |
|---|---|---|
| Green Bay | **"Unofficial, Nov. 10, 2026"** | **6 days** |
| Seattle | *none* | unknown |
| Baltimore | *none* | unknown |

Two of three charts carry **no date whatsoever**. A chart with no date cannot be versioned, cannot
be proved pre-kickoff, and cannot enter a backtest without lookahead risk. This is the concrete
reason the brief's "official depth-chart register with date and source per row" requirement cannot
be met from club pages alone: **the clubs do not publish the date.**

## What the depth data *does* unlock: confirmed replacements

Joining each chart's rank-1 player to the official Week 10 injury report produces the
starter-replacement list the brief asks for — with the named backup and **that backup's own
designation**, so the depth of the replacement is tracked, not just the fact of it.

:::table depth_starter_out.csv | Rank-1 players who are also Out or Doubtful on the official Week 10 report, with the club's own named replacement. | club,position,starter,designation,named_backup,backup_designation,chart_date,source_depth,source_injury

This is a real, sourced, reproducible feature — and it is the one place this repository can
honestly say it detects "a backup replacing a starter" rather than inferring it.

## And here is what it does not unlock

**Depth rank is not talent.** The chart tells us *who* is next. It says nothing about *how much
worse* next is. Every availability constant in this repository (`QB 2.6`, `WR 0.55`, `CB 0.5`, …,
in `data/lines_week10.json`) is an assumption dressed as a parameter. The brief's own requirement
is the correct one: replace those constants with an **ablation** — run the identical model with and
without the availability features and report the difference with uncertainty. That cannot be done
until there are enough settled games to measure it, and there is exactly one week.

## One cautionary observation, offered as an observation

In the two games where these charts can be checked against a result:

- **Seattle** had its **starting quarterback, left tackle, left guard and top defensive tackle**
  all Out — and won 21-13.
- **Green Bay** had its **starting running back, centre and a starting linebacker** Out — and lost
  30-10.

That is one favourable and one unfavourable case, which is another way of saying it is evidence of
nothing. It is recorded here because it is a useful antidote to the intuition that a long injury
list must move a line, and because a future ablation will need exactly this kind of pairing.

## Reproduce

```
python3 scripts/build_depth_blocks.py    # transcriptions + grammar findings + starter-out join
```

Sources: the three club depth-chart pages and the official injury report, each linked per row.
Houston's chart is linked too, with the reason it cannot be transcribed.
