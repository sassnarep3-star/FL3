# Line Origination Methodology (our own prices)

Status: **method documentation** — no prices have been generated against a market, and no
edge claims are made anywhere on the site. Until suggestion S-05 (licensed odds source) is
approved, everything this desk produces is a **fair-value estimate**, not a betting line
with a claimed edge.

## Inputs (what we can verify today)

1. **Availability layer** — point-in-time injury snapshots
   (`data/injuries_2026_wk10.csv`; 345 rows, official source per row). Fields: injury,
   practice status, game status. Derived per-team deficiency counts by unit are published
   on `pages/data-injuries.html`. Historical replay requires S-01/S-02 first.
2. **Depth layer** — currently **empty by design** (flag F-05): no verified starter→backup
   mapping exists, so replacement quality cannot be quantified yet. Proposal S-03.
3. **Fundamentals layer** — verified standings through Week 9: PF, PA, net points, home/
   road/division/conference splits (`data/standings_2026_wk9.csv`).
4. **Schedule layer** — verified Week 10 schedule incl. kickoffs, networks, international
   venue, byes (`data/schedule_2026_wk10.csv`).
5. **Stats layer** — not yet ingested (S-04).

## Origination pipeline

1. **Define the market.** For each game: moneyline (3 outcomes), spread, total. Player
   props and combos are deferred until the correlation layer exists (see
   [signals-and-validation.md](signals-and-validation.md) §4).
2. **Model a probability distribution.** Start with an explicit, simple, reproducible
   baseline (points-based differential model using PF/PA and home/road splits), then add
   features one at a time, each pre-registered with its source and expected direction.
   Every feature must be reconstructible from archived, dated official snapshots —
   otherwise it is not usable (no "current" page scraping into backtests).
3. **Availability adjustments.** Apply status-based adjustments only from verified
   snapshots (e.g., QB Out, RB Out), keyed to report timestamp. Depth-string adjustments
   wait for S-03. Never hand-adjust from news narratives; if it matters, it belongs in a
   registered feature.
4. **Convert distribution → fair price.** Fair odds = inverse of model probabilities with
   no vig. Spreads/totals from the distribution's quantiles. Publish as fair-value
   estimates with the model version, feature list, and snapshot timestamps attached.
5. **Edge measurement (blocked).** Once a licensed odds archive exists (S-05), edge =
   model probability − market-implied (vig-removed) probability at a recorded timestamp;
   closing-line comparison only after the same freeze rules are applied to our own line.
6. **Governance.** Every published line carries: snapshot IDs used, model version,
   feature list, generation timestamp. Changes to methodology are versioned; a changed
   model re-opens the validation gates (see validation page).

## Explicit non-goals (per site policy)

- No "current odds" on the site; no third-party odds scraping.
- No picks or betting recommendations; paper-only until governance review (F-07).
- No value is inferred to fill a blank: an unavailable input blocks the feature, and the
  block is published on the Flagged page instead.
