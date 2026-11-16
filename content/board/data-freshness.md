# Data freshness — the snapshot is two days old and one round stale

Every page on this site is stamped **"official data read 2026-11-14 UTC."** Today is 2026-11-16.
Week 10's Sunday slate was played on 2026-11-15.

That is not a cosmetic date problem. It means the site, as shipped, prices games that have already
finished using rosters and injury designations that changed after they kicked off. This page
measures the gap instead of describing it in the abstract.

## Standings: 22 of 32 clubs moved in two days

:::table snapshot_delta.csv | Per-club delta between the checked-in 2026-11-14 snapshot and a 2026-11-16 re-capture of the same official page. | section,key,label,n_changes,detail

The changes are the ordinary consequence of a round of football: every club that played gained a
game, points for and points against. 22 clubs played; 22 clubs changed. The 10 that did not are on
bye or played Monday.

**This is the least interesting part of the page, and it is here to make a point:** even the
parts of the site that are pure arithmetic over official figures were two days behind. The
standings table a reader sees on the dashboard is not the league's table.

## The injury report: a clock, not a bug

:::table injury_crosscheck.csv | Two independent transcriptions of the SAME official page, 48 hours apart. Substantive differences only. | kind,club,player,field,value_A_2026_11_16,value_B_2026_11_14,severity

The repository already held a transcription of the Week 10 injury report, read on 2026-11-14. This
session made a second, independent transcription on 2026-11-16. Comparing them is the closest thing
to a controlled experiment this repo has produced, and the result is the single most important
thing learned about the data supply:

**The same URL, read two days apart, produces materially different availability for the games that
had not yet kicked off.**

The pattern is not random and it is not a transcription error:

- **LAC carried a game status on 0 of 19 rows on 2026-11-14 and on 9 of 19 rows on 2026-11-16.**
  That is correct both times. A Monday club's final practice had not happened when the first read
  was taken, so the NFL had published no game designation yet.
- **Practice grades moved the ordinary way:** Awosika, Njoku, Mitchell and Shelley went Limited →
  Full; Pipkins went Limited → DNP.
- **BAL gained two rows** (Calais Campbell, Ronnie Stanley) and **two designations** (Jaylinn
  Hawkins **Out**, Adam Randall **Questionable**) between the reads.
- **IND Arden Key came off the report entirely** — he was Hamstring/Questionable, now no injury and
  no designation.

Both games affected — LAC at BAL and PIT at CIN — are the two games that had not been played.

### Why this changes how the whole site must be read

A single capture is not a snapshot of the truth. **It is a snapshot of a clock.** Freezing one and
pricing from it does not merely risk staleness; it prices **LAC at BAL as though nine Chargers game
designations did not exist**, and it prices the Ravens' availability from a chart and a report taken
before their final practice of the week.

That is lookahead bias running in reverse: not using future information, but using *less*
information than was available and presenting it as the state of the world.

## Two data-hygiene bugs found while measuring this

| Bug | Effect |
|---|---|
| **Rams abbreviation.** `data/injuries_2026_wk10.csv` uses `LAR`; `data/lines_week10.json` and this session's capture use `LA`. | A join on club abbreviation **silently drops all 14 Rams availability rows.** No error, no warning — just a team with no injuries. |
| **Player name.** The page's visible text is *Jacob Hummel*; the link it publishes is `/players/jake-hummel/`. | NFL.com's own inconsistency. Recorded as published and flagged; not silently "corrected". |

## What was done, and what was deliberately not done

**Done:** a dated, hashed re-capture exists alongside the old one (`data/captures/`), the delta is
published, and the two transcriptions are compared row by row rather than one overwriting the
other.

**Not done:** the 2026-11-14 snapshot was **not** overwritten. It is the only pre-kickoff record in
the repository, and pre-kickoff records are the entire basis of a backtest. Overwriting it to make
a date look better would destroy the evidence needed to score the forecast. Superseding it is a
decision with gate consequences, not a side effect of a measurement.

## The requirement this evidences

Per the brief: *"Treat the injury report as a timestamped series, not a weekly snapshot."* This
page is the proof of why that requirement exists, measured rather than argued.

| Requirement | Status | What clears it |
|---|---|---|
| R073 — measure and publish snapshot staleness | **PARTIAL** | A scheduled capture with a clock time on every read, retained side by side |
| Immutable multi-day availability snapshots (R030) | PARTIAL | Append-only store, freshness monitor, alert on schema drift |
| Injury signal as a surprise, not a level (R013) | PARTIAL | Delta between successive timestamped reads — **this page is the first such delta in the repo** |

## Reproduce

```
python3 scripts/capture_official.py      # re-read both official pages, write a dated capture
python3 scripts/snapshot_delta.py        # per-club and per-player delta
python3 scripts/injury_crosscheck.py     # compare two independent transcriptions
```

## Sources

- Injury report (both reads): <https://www.nfl.com/injuries/league/2026/reg10>
- Standings (both reads): <https://www.nfl.com/standings/league/2026/REG>
- Capture manifest with row counts and hashes: `data/captures/manifest.json`
