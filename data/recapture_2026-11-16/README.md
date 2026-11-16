# Week 10 official injury report — live re-check, 2026-11-16 (UTC)

**Source:** https://www.nfl.com/injuries/league/2026/reg10 (NFL.com, official league injury report page)

**Method:** The page was read through the agent's page-fetch tool in 8 chunks (chunks 0–7, 2026-11-16).
Each club's table was counted row by row. No raw HTML bytes were retained, so **no raw-content hash exists
for this capture**. That is a known gap: the next capture must store the raw bytes and a SHA-256 hash.

**Files**

- `manifest_team_counts.csv` — per-club row counts: live page vs `data/injuries_2026_wk10.csv` (2026-11-14 capture).
- `discrepancies.csv` — each discrepancy, its status, and the source link. Brief claims that were not reproduced are kept and labelled.

**Not changed:** `data/injuries_2026_wk10.csv` and `data/injuries_2026_w10.json` are preserved as-is. Adding the two
missing Ravens rows is a separate re-transcription task, because it changes the published row count (345 → 347)
and the verifier checks that count.

**Limits:** counts for all 28 clubs; a field-level check of the 3 Lions rows; spot-checks of Seattle and Cincinnati
statuses. A full field-level re-transcription of all 347 rows is still open.
