# research/verification-log.md — line-by-line verification (session 9b181d31)

Date: 2026-11-14. Rule applied: every table row carries a source link; values that
could not be confirmed from an official source are **blank and flagged**, never
inferred. This log records what was checked and how.

## 1 · Data integrity checks (automated, reproducible)
Run: `python3 models/originate_lines.py`

| Check | Result |
|---|---|
| sum(PF) == sum(PA) across 32 teams | PASS — 6,291 == 6,291 (league accounting must balance) |
| total team-games even (each game counted twice) | PASS — 274 (137 games) |
| every injury row has status ∈ {OUT, DOUBTFUL, QUESTIONABLE, IR} | PASS — 162 rows, all valid (160 transcribed from the official report + 2 IR rows from team-statement reporting) |
| every injury row links its source | PASS — 160/160 report rows link the official report; 2/2 IR rows link The Athletic / NBC Sports |
| every deficiency row with a replacement also links a club depth chart | PASS — 35/35 verified-replacement rows |
| every deficiency row without verified tier has empty tier cells + flag | PASS — no inferred values |
| every standings row links nfl.com standings | PASS — 32/32 |
| every lines row links a market source + lists other books | PASS — 13/13 |
| correlation rows computed from standings (reproducible) | PASS — 6 Pearson + Pythagorean fit; 3 cells intentionally blank+flagged (no data) |
| games CSVs match NFL.com week pages incl. byes | PASS — W10: 14 games + 4 byes; W11: 13 games + 6 byes |

## 2 · Row-by-row source re-checks (manual spot audit)
- Standings: 32/32 rows re-read against the NFL.com standings table (W-L-T, PF, PA,
  streak) — no discrepancies. (Check yourself: every row on
  https://www.nfl.com/standings/league/2026/REG.)
- Week 10 report: statuses re-checked game-by-game against
  https://www.nfl.com/news/nfl-week-10-injury-report-2026-season — 160 rows, no
  discrepancies; games with zero designations (LAC-BAL) recorded as such (F10).
- Depth tiers: each tier/replacement pair re-checked against its club chart page
  (7 charts; links in research/sources.md). Mismatches vs the official report were
  NOT resolved by guessing — they are published as F1/F2/F3.
- Market rows: each primary value re-checked against its linked article; secondary
  book values recorded as ranges with links (F4/F5/F12 document disagreements).
- TNF result (WAS 24-NYG 21) re-checked on the NFL.com game page.

## 3 · Site verification
- `docs/injuries.html` and `docs/data.html` are **generated from the CSVs**
  (models/build_pages.py) so site rows == CSV rows by construction (no transcription
  drift). Injuries page: 293 table rows, 329 links at build time.
- Internal-link check run over `docs/`: every href to a local page/asset/CSV must
  resolve to a file in the repo (script output attached in the commit message).
- Every site table row that states a fact carries a source chip (external link) or a
  "no source"/"blank — unverified" marker. Model values are badged `model output`.

## 4 · Irregularities found (all published on docs/flagged.html)
F1 GB chart omits Parsons · F2 DET chart omits Joseph · F3 MIN chart stale on Cousins ·
F4 SEA-LV market spread 3.5–6.5 · F5 CAR-NO favorite flip · F6 ESPN "opened" total
anomaly · F7 HOU chart is an image · F8 SF chart HTTP 500 · F9 charts self-labeled
"unofficial" · F10 LAC-BAL clean report · F11 JAX "rest" designations · F12 total
disagreements · F13 empty base repo · F14 large model edges (v0.1 caution) ·
F15 Wednesday-only practice snapshot.

## 5 · What was deliberately NOT done
- No value was filled from memory, inference, or non-fetched sources.
- No performance numbers for strategies (no bets graded — columns left blank).
- No game/prop-level correlations (no data — cells left blank + flagged).
- Stale search results (ESPN 2001 report; CBS Week 11 **2025** article) were discarded
  and are not used anywhere.

## 6 · Cross-session fold-in (BAL QB case, 2026-11-14)
Parallel session `arena-e8bf2075` flagged (their F02) that the Week 10 report lists no
Ravens QB although Lamar Jackson is out. Independently verified and expanded:
- The Athletic + NBC Sports (team statement, HC Jesse Minter): Jackson thumb surgery,
  out 6–10 weeks (IR); Tyler Huntley season-ending toe; Jacoby Brissett acquired from AZ.
- baltimoreravens.com official chart: QB1 Brissett / QB2 Joe Fagnano / QB3 Kedon Slovis;
  **kicker slot empty** (Riley Patterson signed).
- Model changes: 2 IR rows added (162 total, 160 report + 2 IR), QB-room cap introduced
  (only top-of-room QB absence priced — Jackson 3.5, Huntley flagged), W10-14 updated
  (model BAL −2.0/41.5, edges −2.5/+3.0). Counts refreshed: deficiency rows 78.
- Flags updated: F10 rewritten (was "clean bill" — corrected), F16 added (systemic gap:
  weekly reports omit IR/transaction-driven starter changes).
