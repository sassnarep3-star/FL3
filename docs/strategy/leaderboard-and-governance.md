# Leaderboard Competition Design, Rewards, and Governance

Status: **design only** — the leaderboard has no entries and no rewards exist. Nothing here
is legal, tax, wagering, or financial advice.

## 1 · Competition format (paper-only until governance clears)

1. **Entry.** A strategy is an entry only after it passes the validation gates
   ([signals-and-validation.md](signals-and-validation.md) G1–G8). Entries are versioned;
   the exact rules version is frozen per competition run.
2. **Scoring (pre-declared per run).** Primary metric: baseline-relative net result on
   unit-size-flat, paper-executed singles at recorded fair-value vs (once S-05 lands)
   market prices, with every rank published together with sample size and confidence
   interval. No metric may be changed after outcomes are known.
3. **Divisions.** Separate leaderboards for (a) game singles, (b) parlays (admitted only
   after the dependence audit), (c) player-prop combos (admitted only after the
   correlation layer exists). Mixing bet types in one rank is prohibited because their
   variance profiles differ.
4. **Cadence.** Weekly rolling standings; season-long final ranking. All evaluation on
   chronological, untouched windows.
5. **Anti-gaming.** One entry per methodology version; no mid-run feature changes; late
   registrations start fresh; duplicate strategies under different names are merged by
   reviewer decision.

## 2 · Rewards (deliberately unspecified)

- No reward, prize, cash value, or entry fee exists. The reward system is a design
  question gated on: legal review (jurisdiction, age, gambling-law exposure), tax review,
  platform/data rights, responsible-gambling safeguards, and an auditable, appealable
  scoring pipeline. See flag F-07 and
  [NFL gambling policy / integrity information](https://media.nfl.com/lsb).
- Interim reward: non-monetary recognition (published rank + verified track record).

## 3 · Governance workflow

1. Suggestions are proposed on `pages/suggestions.html` (review-before-implement).
2. Reviewer decisions are recorded there and in `docs/suggestions.md` (S-12).
3. Accepted items are claimed in `COORDINATION.md` (owner session, file scope) and
   implemented on the owning session's branch.
4. Integration re-verifies data line-by-line, runs `scripts/check_site.py`, and only then
   opens/merges a PR. Broken sites are never merged.
5. Every published value keeps its official source link; unverified items stay blank and
   surface on the Flagged for Review page instead.

## 4 · Multi-session operating rules (in effect)

- Sessions claim tasks on the board and never touch another's scope; shared outputs
  (index, nav, table data) change only in the integration pass.
- `git pull --rebase` before every push; conflicts are resolved without discarding the
  other session's work, and the incident is logged (one such conflict was resolved
  2026-11-14).
- A stalled claim (>60 min without commits) may be taken over, with a handoff note on the
  board.

## 5 · Reviewer decision points (summary)

| Decision | Unblocks | Register |
|---|---|---|
| Adopt S-01/S-02 (archive + scheduled collection) | Injury signal backtests | S-01/S-02 |
| Pick licensed odds provider (S-05) | Edge/CLV measurement; leaderboard meaning | S-05 |
| Approve depth-chart ingestion (S-03) | Backup-strength signals | S-03 |
| Fix validation thresholds (S-06) | First strategy ranking | S-06 |
| Approve singles-first rollout (S-11) | Competition start | S-11 |
| Governance/rewards review (S-07) | Any reward design | S-07 |
| Correlation dataset acquisition (S-08) | Parlays & prop combos | S-08 |
