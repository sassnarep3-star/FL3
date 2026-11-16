# Our line — three files, three answers

**Read this before trusting any number on the [lines page](lines.html).**

The repository publishes "our line" for the same Week 10 fixtures from **three different files**,
and they do not agree. This is not a rounding dispute. On the same game they can be seven points
apart, on opposite sides of the number, and both are presented to a reader as our own forecast.

| File | Written by | Rendered where | Keyed by |
|---|---|---|---|
| `data/lines_week10.json` | `scripts/compute_lines.py` | the **root site** (`lines.html`, live on GitHub Pages) | `WAS-NYG-W10` |
| `data/lines_origination.csv` | `scripts/model.py` | the **board site** (`board/lines.html`) | full club names |
| `data/2026-week10-lines.csv` | *nothing* — committed by hand, no generator writes it | nowhere, but it is the only file with market quotes | `W10-01` |

Three files, three key formats, no generator overlap. That is why this went unnoticed: no single
script ever loaded two of them at once.

## The convention trap

`scripts/compute_lines.py` emits `home_spread = round(-margin, 1)`. `scripts/model.py` emits
`expected_home_margin` with the opposite sign convention. So the two files are on **inverted axes**
*and* **different levels**. Anyone comparing them naively, or joining them by club name, gets a
number that is wrong twice over.

Every value on this page is converted to **one axis: signed home margin, positive = home wins by
that many points.**

## The same fixtures, side by side

:::table line_provenance_reconciliation.csv | All 14 Week 10 fixtures on one axis. A = root site, B = board site, C = the unowned CSV. Blank C cells are games it does not price. | game_id,away,home,A_home_margin,B_home_margin,C_home_margin,actual_home_margin,settled

Work through W10-01. The game finished **WAS 24, NYG 21** — the away side by 3.

- **A** says home **+4.1** → about 7 points on the wrong side of the result
- **B** says home **+3.5** → about 6.5 points on the wrong side, in the *other direction*
- **C** does not price the game at all

A and B are **7.6 points apart from each other** on a game that was decided by 3.

## Aggregate, on the twelve settled games

:::table line_provenance_verdict.csv | How each series did against the settled results. n is stated because it is small. | metric,value,note

Three things to take from this table, and one thing not to.

**What it shows:**

1. **A and B disagree with each other by more than either disagrees with reality.** Mean absolute
   disagreement between our own two files is **6.72 points**. A model whose internal disagreement
   exceeds its external error is not one model with two outputs — it is two models.
2. **The live root site renders the worst of the three.** A's MAE is 11.62 against B's 8.02. The
   file a public reader actually sees is the one that leans hardest toward home teams, with a
   bias of **+7.84 points**.
3. **None of them beats a naive pick-em by much.** Always forecasting a zero home margin scores
   13.00 MAE. B scores 8.02, which is better; A scores 11.62, which is close enough to the
   do-nothing benchmark that its apparent sophistication is not buying much.

**What it does not show — and this is important:**

n = 12. That is a provenance audit, not a model evaluation. Ranking A against B at n=12 is not
statistically meaningful and this page does not do it. B being closer on twelve games is a reason
to investigate B's convention, not a reason to promote B. Any promotion has to go through the
gates in `data/strategies.json`, and one 12-game sample clears none of them.

## Why this is the most serious finding in the repository

Every other defect found this session is a gap — missing data, missing pages, missing timestamps.
A gap is honest: the cell is blank and the reader knows. This one is different. **Two files with
cannot-both-be-true values are both published, both labelled as ours, on two different pages of
the same site, with no reconciliation anywhere.** A reader who visits the root dashboard and then
the board gets two different answers to "what did we think the line was", and nothing tells them
that.

## What is being done about it, and what is not

**Done this session:** the three files are reconciled on one axis, the disagreement is published
here and as `data/line_provenance_reconciliation.csv`, and the convention difference is documented
in code.

**Not done, deliberately:** no file was rewritten, no model was promoted, and the root site was
not switched to B. Choosing a canonical series is a modelling decision with gate consequences. It
gets a register row and an owner decision, not a silent swap by a session that also wrote the
comparison.

## The decision that has to be made

| Question | Options | Why it is blocked |
|---|---|---|
| Which series is "our line"? | A, B, or a new engine | Choosing requires a walk-forward comparison, and B's own documentation calls itself `provisional-fitted-not-bettable` |
| Can the third file stay? | delete, or give it an owner | It is the only source of market quotes in the repo, but no generator writes it and it is not licensed |
| Should the root site render A at all? | yes with a caveat, or no | A is the worst performer on the only settled sample, but n=12 |

## Sources

- Results and per-game links: [verified results feed](results.html) ·
  <https://www.nfl.com/schedules/2026/by-week/week-10>
- The three line files are in `data/` and are linked from their generator scripts.
- Working: `python3 scripts/reconcile_lines.py`
