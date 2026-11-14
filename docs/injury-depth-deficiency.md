# Injury & Depth Deficiency Tracking Framework

Purpose: define how FL3 tracks injuries and offensive/defensive deficiencies — including
starters replaced by 2nd/3rd/4th-string backups — **without ever inventing depth order**.

## 1 · Data we track (verified layer)

- **League injury report snapshots** — one dated snapshot per week (final Friday report
  for Week 10, 2026 is the first one: `data/injuries_2026_wk10.csv`, 345 rows, official
  source link on every row). Fields: player, position, injury description(s), practice
  status (Did Not Participate / Limited / Full Participation in Practice), game status
  (Out / Doubtful / Questionable / blank = no designation).
- **Inactives** — final inactives to be collected per
  [NFL inactives](https://www.nfl.com/inactives/) going forward (S-02).
- **News/transactions** — official headlines that change roster availability (IR moves,
  trades, surgery timelines) are recorded as rows with links
  (`data/injury_news_2026_wk10.csv`).

## 2 · Derived deficiency snapshot (published, with derivation documented)

From the verified report we compute, per team: counts of **Out**, **Doubtful**,
**Questionable**, plus **key offensive absences** and **key defensive absences**, where:

- Offense unit positions: QB, RB, FB, WR, TE, T, G, C
- Defense unit positions: DT, DE, DL, LB, CB, S, DB
- "Key absences" = players with game status Out or Doubtful in that unit.
- The mapping is a deterministic positional classification (documented here and in
  `scripts/build_data_pages.py`); counts are reproducible from the CSV.

Published at `pages/data-injuries.html` ("Team deficiency snapshot (derived)").

**Explicit limits:** these counts say who is officially unavailable — they do **not** say
how good the replacement is. Claiming a team is "depleted" beyond the official designations
requires the depth layer below, which does not exist yet.

## 3 · Starter vs backup (2nd/3rd/4th string) — the missing layer

- The league report does not publish depth order. No verified, dated 1st/2nd/3rd/4th-string
  mapping exists in this repo; therefore **all depth-string values are blank** and flagged
  (F-05). We never infer "the backup is X" from memory or third-party lists.
- Discovery plan (S-03): ingest officially published, dated team depth charts (starting
  from the [NFL team directory](https://www.nfl.com/teams/)); where a team publishes
  nothing official, design a **labeled participation proxy** (e.g., verified snap-count
  shares from official stats) and validate it before it is used as a feature.
- Once depth is verified: deficiency = starter absence × replacement quality, both
  sourced; the W10 QB cases already verified from official news are recorded as news rows
  (e.g., Darnold out / Lock starts — official headline link).

## 4 · Week 10, 2026 snapshot — notable verified availability facts

Derived mechanically from the verified report (see the data page for the full table and
per-row sources). Examples (each verifiable on the league report):

- **GB:** Josh Jacobs (RB) Out — finger surgery per official news; Micah Parsons (LB) Out.
- **MIN:** Kyler Murray (QB) Out (hamstring); Carson Wentz (QB) on the report with full
  participation — the report does not say who starts, so that stays unclaimed.
- **SEA:** Sam Darnold (QB) Out; official news confirms Drew Lock has no designation and
  will start; LT Charles Cross and G Quenton Nelson Out — two offensive-line starters out.
- **HOU:** Marvin Harrison Jr. (WR) Out, Danielle Hunter (DE) Out, Will Anderson Jr. (DE)
  Questionable — flagged discrepancy on Harrison's injury field (F-09).
- **JAX:** Jessie Bates (S) and Jordan Davis (DT) Out — resting players (not injury).
- **KC:** Kenneth Walker III (RB) Questionable (groin) — team attribution cross-checked
  via CBS/USA Today (logged in COORDINATION.md).
- **LAC:** 19 players on the report (league-high in this snapshot); BAL 8.
- **Byes:** CHI, DEN, PHI, TB.

## 5 · How this feeds signals

Availability/depth signals use (a) verified statuses, (b) derived unit counts, and — once
S-03 lands — (c) verified replacement quality. Point-in-time replay requires archived
snapshots (S-01/S-02): features must only use what was knowable before kickoff.
