# Decision queue — 73 requirements, 7 decisions

The [requirement register](readiness.html) lists 73 requirements, each with the gate that blocks it
and the number that would clear it. It is complete and it is not actionable: nobody reviews 73 rows
and makes a call.

This page collapses it. Every requirement names a blocking gate; every gate is released by one owner
decision. **Grouping by gate produces seven decisions, and one of them releases a third of the
register.**

## The queue, sorted by what it releases

:::table decisions_queue.csv | Each gate, the number of requirements behind it, whether those rows have an official source, and the single owner decision that releases them.

## What that table is telling you

**Q-02 releases 24 of 73 requirements and is a procurement decision, not a code decision.** Every
one of those 24 rows already has an official source registered. The blocker is not that we cannot
find the data — it is that nobody has decided which of the available routes is authoritative:
club pages verified club by club, an authorised structured feed, or publishing the field as unknown.
That is one conversation.

**Q-01 and G-03 release 10 rows between them and all 10 have no official source.** They are the same
decision counted twice: license a market price, or write down that no ROI, CLV or edge figure will be
published. Both answers are defensible. What is not defensible is publishing a comparison against a
price nobody licensed — which is why those columns are blank on every table on this site.

**G-10 releases 15 rows and is the only purely engineering item.** Scheduled capture with a clock
time and an immutable store. This session proved the need for it rather than asserting it: the same
official injury URL, read 48 hours apart, gave LAC a game status on 0 of 19 rows and then 9 of 19
([data freshness](data-freshness.html)).

**35 rows sit behind protocol decisions that cost nothing but resolve arguments.** Sample window, fold
dates, multiplicity rule, whether correlation may be measured on a priced market. These need no
procurement and no code; they need someone to write them down and commit the text.

**Q-04 (3 rows) and one row with no stated gate were not classified by this script.** Their blocking
gate is a coverage threshold rather than a single owner decision, so the queue says
`UNCLASSIFIED` and lists the requirement IDs rather than inventing a decision for them.

## What is already done, so it does not get re-decided

Not every row in the register is open. This session moved six rows forward and wrote down exactly
how:

| Row | Was | Now | What changed |
|---|---|---|---|
| R002 Results feed | PARTIAL | PARTIAL (**first working feed**) | 12 of 14 Week 10 games verified, one row per fixture, game-page link per row |
| R069 Luck panel | — | PARTIAL | First prospective grade computed; interval published including its lower bound below zero |
| R070 Canonical line | — | NOT STARTED (**defect now measured**) | Three series reconciled; 6.72-pt disagreement published |
| R071 Depth as grid | — | PARTIAL | 3 clubs transcribed with cell structure; 6 failure modes documented |
| R072 Parse failures | — | PARTIAL | Packers solved; Texans confirmed impossible from the source |
| R073 Staleness | — | PARTIAL | Measured: 22/32 clubs, 160→347 injury rows |

## Read the top of the queue in one minute

1. **Decide the availability/depth source route** (Q-02, 24 rows). Highest leverage, no cost.
2. **Freeze the evaluation protocol** (G-02/G-04/G-12/G-01/G-07, 35 rows). No cost, ends the
   "is this in-sample?" argument permanently.
3. **Set the price-data policy** (Q-01/G-03, 10 rows). Either license or accept the restriction in
   writing.
4. **Stand up scheduled capture** (G-10, 15 rows). The only item that needs engineering time.
5. **Define the demotion state machine** (G-11, 1 row). Small, but it is what makes a live strategy
   revertible.

## Reproduce

```
python3 scripts/build_decisions_queue.py
```

It reads `data/requirements_readiness.csv` and changes nothing in it. Rows can sit behind more than
one gate, so per-gate counts sum above 73 — that is stated in the output rather than adjusted away.
