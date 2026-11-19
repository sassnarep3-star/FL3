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

## Week 11 — immutable machine capture (2026-11-19)

**Captured:** 2026-11-19 05:27:43 UTC from [Official NFL Injury Report - Week 11 of the 2026 Season](https://www.nfl.com/injuries/league/2026/reg11) (SRC-037).
**Stored:** the raw body, gzip-compressed and never overwritten, at `snapshots/raw/injuries/reg11/2026-11-19T052743Z_f58ecb73ed91.html.gz`
(374,013 bytes; sha256 `f58ecb73ed91b237829f7678388553b23dab8ab4cc908addb83c9067ee54b528`).

**Method:** a script parses the stored bytes (`scripts/parse_official_snapshot.py`), so no value was typed by hand. Pinned checks passed:
26 clubs on the matchup strips = 24 club tables + 2 "No Injuries Reported" sections; 13 game pairs; 253 player rows = 253 Practice Status cells.
The club set matches the official schedule: 13 games, and the six byes (Falcons, Browns, Packers, Rams, Patriots, Seahawks) are the six clubs with no section.

**Cross-check:** the 51 rows of IND at HOU and PIT at PHI were read again from the live page and compared field by field (`scripts/check_official_readings.py`): all match.

**Why the earlier captures showed nothing:** the 2026-11-18 and 2026-11-19 scheduled runs recorded `empty` because the parser counted only one literal URL form. The official page uses relative player links. See [Flagged for review](flagged.html) FLG-067.

**Not yet automatic:** the scheduled workflow does not yet run the parser; each week is parsed by hand until FLG-068 is closed.
