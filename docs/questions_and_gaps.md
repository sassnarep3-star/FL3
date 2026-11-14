# Open Questions, Information Gaps, and How to Discover the Missing Pieces

Purpose: a clear list of questions, the information we already have and do not have, and
the answers that must be established **before** a reasonable decision can be made. Each
item includes a discovery suggestion. The user-visible version of this register lives at
`pages/questions.html` (rows A-01…A-12 plus the original framework).

Legend — **Have (V)** = verified from an official source (link in the data pages);
**Have (D)** = documented method only; **Lack** = missing; **Discover** = proposed way to
obtain it.

## Q1. Scope & rights
- **Question:** Which weeks/seasons/markets do we originate lines for first?
- **Have (V):** Week 10, 2026 schedule (14 games, 4 byes) — official links per game.
- **Lack:** market list; season horizon; product decision (what the "output" is).
- **Discover:** reviewer decision + inventory official stats coverage per candidate feature
  ([NFL team stats](https://www.nfl.com/stats/team-stats/)).

## Q2. Data rights
- **Question:** What reuse terms apply to officially published values stored in this repo?
- **Have (V):** every published value carries its official source link; snapshots are small
  and cited.
- **Lack:** rights review for storage/redistribution; correction-handling policy.
- **Discover:** legal/terms review before any bulk ingestion; keep row-level citation in the
  meantime.

## Q3. Injury signal inputs
- **Question:** Which report fields are decision-grade, and at what report age?
- **Have (V):** final Week 10 league report snapshot — 345 rows: injury, practice status,
  game status ([source](https://www.nfl.com/injuries/league/2026/reg10)).
- **Lack:** what was knowable *before kickoff* in past weeks (point-in-time history);
  update cadence semantics (when do statuses change during the week).
- **Discover:** scheduled collection at fixed milestones (final Friday report, Saturday
  designations, final inactives) with content hashes (suggestions S-01/S-02); validate
  against [official inactives](https://www.nfl.com/inactives/).

## Q4. Starter vs backup quality
- **Question:** How do we quantify 2nd/3rd/4th-string replacement strength without inventing depth?
- **Have (V):** per-team Out/Doubtful/Questionable counts by unit (derived from the report);
  e.g., Week 10: GB — Jacobs (RB) and Parsons (LB) Out; MIN — Murray (QB) Out; SEA —
  Darnold (QB) Out with official news confirming Lock starts; HOU — Harrison Jr. (WR) and
  Hunter (DE) Out.
- **Lack:** verified dated depth order for every team (flag F-05); backup performance data.
- **Discover:** ingest officially published team depth charts
  ([team directory](https://www.nfl.com/teams/)); where a team publishes none, design and
  validate a labeled participation proxy (snap counts from official stats) instead of
  guessing rank.

## Q5. Edge measurement
- **Question:** Can we measure edge at all without odds?
- **Have (V/D):** documented fair-price methodology
  ([line-origination.md](strategy/line-origination.md)); **no** odds data.
- **Lack:** licensed point-in-time odds archive; settlement conventions; market list.
- **Discover:** reviewer selects a licensed provider and verifies historical access
  (S-05); until then the site publishes fair-value estimates only.

## Q6. Correlation for combinations
- **Question:** How will parlay / player-prop-combo correlations be determined?
- **Have (D):** method — paired historical joint outcomes; dependence estimated with
  uncertainty ([NIST correlation definition](https://www.itl.nist.gov/div898/handbook/glossary.htm)).
- **Have (V):** none — and the site explicitly publishes no correlation values.
- **Lack:** joint outcome dataset; estimated dependence with confidence intervals.
- **Discover:** acquire paired outcomes (game × player props), pre-register dependence
  hypotheses, stress-test with and without correlation caps (S-08).

## Q7. Validation standards
- **Question:** What sample size / uncertainty standard must a strategy clear?
- **Have (D):** published gates (pre-registration, chronological holdouts, calibration,
  baselines, replication) on `pages/validation.html`.
- **Lack:** reviewer-chosen numeric thresholds (minimum bets, CI width, minimum edge).
- **Discover:** fix thresholds *before* first test using
  [NIST confidence-limit guidance](https://www.itl.nist.gov/div898/handbook/eda/section3/eda352.htm);
  record them in the pre-registration template (S-06).

## Q8. Leaderboard rewards & governance
- **Question:** What reward can top strategies earn, under what rules?
- **Have (D):** paper-only leaderboard design (versioned rules, published uncertainty).
- **Lack:** legal/tax/eligibility review; auditable scoring; appeal path.
- **Discover:** governance review; keep paper-only until cleared
  ([NFL gambling policy / integrity](https://media.nfl.com/lsb)); record any decision per S-12.

## Q9. Bet-type rollout
- **Question:** Singles first, or parlays/prop combos from the start?
- **Have (V):** Week 10 schedule/records to define matchups; verified deficiency snapshot.
- **Lack:** reviewer decision; joint-outcome data for combos (Q6).
- **Discover:** adopt S-11 (singles first — cleanest skill isolation) or justify otherwise
  in a pre-registration note.

## Q10. Snapshot cadence & retention
- **Question:** How often are official pages refreshed, and how long retained?
- **Have (V):** one dated cycle completed (Nov 14, 2026) with per-row sources.
- **Lack:** cadence policy; collector; retention/versioning scheme.
- **Discover:** weekly collection tied to official report milestones + archived snapshots
  (S-01/S-02/S-10); keep one folder per week.

## Q11. Bye weeks & schedule edge cases
- **Question:** How do models treat byes and 14-game weeks?
- **Have (V):** Week 10 byes verified: CHI, DEN, PHI, TB
  ([schedule](https://www.nfl.com/schedules/2026/REG10)).
- **Lack:** model specification decision (exclude vs flag).
- **Discover:** decide in the pre-registration note before testing (S-06).

## Q12. Parallel-session governance
- **Question:** Who integrates, in what order, and how are conflicts resolved?
- **Have (D):** COORDINATION.md board in use; one live conflict already resolved without
  discarding either session's work (logged Nov 14).
- **Lack:** standing integration order; review SLA; takeover rule enforcement.
- **Discover:** adopt change control (S-09) and decision logging (S-12);
  [Football Operations](https://operations.nfl.com/) style versioned-rules discipline as the model.

## Summary of discovery priorities
1. S-01/S-02 — archive + scheduled injury collection (unblocks Q3, Q10).
2. S-05 — odds provider decision (unblocks Q5, and the leaderboard's meaning).
3. S-03 — official depth charts (unblocks Q4).
4. S-06/S-07 — pre-registration + validation thresholds (unblocks Q7, Q11).
5. S-08 — joint outcomes for correlation (unblocks Q6, then parlays/props).
6. S-07 — governance review (unblocks Q8).
