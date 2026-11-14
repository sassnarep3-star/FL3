# Flagged for review

Everything the pipeline could not confirm, or found in conflict - with the source link beside it, so a
decision here is one click from the evidence. **None of these items block the deploy**; they block *trust*
in a specific cell, which is the thing that actually has to be protected.

**How to work this page:** for each row either (a) confirm the value from the linked official source and
update `data/`, (b) approve the value as-is and record the exception in `COORDINATION.md`, or (c) mark it
`resolved: <what changed>` in `data/flags.csv` and rebuild.

:::table flags.csv | 26 open items: 7 high, 12 medium, 7 low and info | id,severity,page,item,finding,action_required,source_url,status

## The six that matter most

| Flag | One-line summary | Cost of ignoring it |
|---|---|---|
| **FLG-005** | IR players never appear on the weekly report, so "healthy" can mean "missing a franchise QB" | the availability module inverts its own signal |
| **FLG-006** | 8 clubs list players who, before 2026, played elsewhere - real transactions or feed errors, unconfirmed | a model trained on the wrong roster for 8 teams |
| **FLG-010** | no official source publishes odds | no CLV, no market gate, no leaderboard, no edge measurement |
| **FLG-016** | 33 of 137 games ingested | every distribution and every calibrated constant is provisional |
| **FLG-017** | no depth chart or snap-count feed exists league-wide | "4th-string backup" cannot be computed, only assumed |
| **FLG-025** | the league's own offense and defense tables disagree on TDs (414/415) and INTs (202/200) | a model silently built on mutually inconsistent scoring data |

## Two that are worth reading because they are *uncomfortable*, not because they are big

- **FLG-026** - the calibration returned `beta = 1.14` (anti-shrinkage) and pushed the total-model exponent
  to its grid boundary. The tempting response is to clamp the numbers into something that looks sane; the
  correct response is what happened here: publish the anomaly, and let it stand as the measurement of how
  little 33 games tell you.
- **FLG-024** - the fetch scripts in this repo have **never been executed**. They ship labelled as
  untested, because the alternative (claiming an auto-refreshing data layer that was never run) is the
  kind of fiction that would make every other number on the site untrustworthy.

## Resolution protocol

1. A flag is opened by any session in `data/flags.csv`; the site picks it up on the next build.
2. `severity: high` items that touch a *published value* also get a row-level marker in the data file
   (e.g. the `flag` column on [injury rows](injuries.html)), so a downstream consumer cannot miss it.
3. Resolving means the data changed, the source changed, or the owner recorded an exception. Marking a
   flag `resolved` without one of those three in the commit message is treated as a gate failure (G-12).
