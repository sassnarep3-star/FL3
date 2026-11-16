# Official Week 10 injury capture and reconciliation

**Captured:** 2026-11-16 (UTC), from the official NFL.com page
[Injury Report - Week 10 of the 2026 Season](https://www.nfl.com/injuries/league/2026/reg10) (SRC-018).
**Method:** every row was transcribed by hand from the page's rendered table text, line by line, and
grouped by game as the page prints them. The raw HTML was **not** kept, so no byte-level hash of the
page exists. The sha256 of the transcription file is in `data/official_capture/manifest-2026-reg10.json`.
A script (`scripts/reconcile_injury_capture.py`) checks the structure: 14 game sections, 28 clubs, one
row per listed player, and only the status words the page uses.

## What this page is for

Until this capture the board carried several Week 10 injury tables with different row counts
(345, 162 and 160), and none was marked as the official one. This page makes the 2026-11-16 capture the
reference, and shows every difference against each copy. **Nothing in the older copies has been
overwritten.** Several verifiers and builds hard-code their counts, so the correction is listed as an
open decision in [Flagged for review](flagged.html) (FLG-046) rather than made silently.

## How to read the tables

- **Canonical capture** - every listed player, with the game section, practice status and game status
  exactly as printed. Blank means the official cell was blank.
- **Reconciliation** - every field where the primary repo table (`data/injuries_2026_wk10.csv`, 345 rows)
  differs from the official value. Injury lists are compared as sets, so `Ankle; Knee` and `Ankle, Knee`
  are treated as the same value.
- **Copy audit** - row count and club coverage of each Week 10 injury copy in the repo.

Each row carries the source id and the official URL. Blank cells are blank in the source, not guessed.
