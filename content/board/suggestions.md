# Suggestion register

This is the section you asked for: **suggestions on how to improve the site and the system, collected
so a best path can be chosen before anything is implemented.** Nothing in `proposed` status has been
built; the six rows marked `implemented-in-v1` were the minimum needed to make the rest auditable
(row provenance, badges, the comparison layout, the review queue, regeneration and the reward formula).

Each row is written so it can be decided without a meeting: the problem it solves, the proposal, the
impact, the effort, the risk, what it depends on, and whether we recommend it.

**To decide:** set `data/suggestions.csv` → `owner_decision` to `approved: <date>`, `rejected: <reason>`
or `defer`, and commit. `status` moves to `approved` only in the same commit, so the register is also
the decision log. (See [S-05](suggestions.html) for a one-click version of that.)

:::table suggestions.csv | 25 suggestions, 6 already implemented in v1 - approve, reject or defer the rest | id,type,title,problem_this_solves,proposal,expected_impact,effort,risk,depends_on,recommended,status,owner_decision

## The recommended path, in order

| Order | Suggestion | Why it comes at this point |
|---|---|---|
| 1 | **S-11** game-level history | it is the only blocker that costs engineering time and no money; it also unlocks S-12, S-13, gates G-01/G-05 and every correlation |
| 2 | **S-08 + S-09** availability merge + affiliation audit | your brief is specifically about backup-driven deficiencies; today that number is not computable, and 8 rows in it are actively suspicious |
| 3 | **S-18 + S-01 + S-02 + S-06** reproducibility and audit discipline | already partly in v1: keep it, because it is what stops the next 6 months of work from rotting |
| 4 | **S-25** the abstain rule | at −110, a 52.4% hit rate is break-even, so the *pass* decision is where the edge lives; this costs nothing and prevents the classic self-deception |
| 5 | **S-15 → S-16 → S-17 → S-24** prediction-quality grading, sealed walk-forward, FDR control, anti-gaming rewards | the leaderboard must be built on the grading system, not the other way round; if rewards are paid on ROI the prize selects for variance |
| 6 | **Q-01 / S-11 vendor step** - buy the odds feed | converts the pipeline from "we produce lines" to "we produce lines we can score" |
| 7 | **S-19 + S-20** stake ladder + bet ledger | nothing can be promoted to real money without a ledger that timestamps our number against the market's |
| 8 | **S-12, S-13, S-21, S-23, S-07, S-22** model and site refinements | genuine, but each one is only measurable after 1-7 |

## Explicitly not recommended (yet)

- **S-23 weather**, **S-07 model-health page**, **S-22 changelog** - useful later, and if built now
  they add a way to look busy while the inputs are still provisional.
- **Any signal-to-money path.** No signal in [the catalogue](signals.html) has passed a gate; the
  correct use of the current pipeline is elimination, not staking.

## What each type of suggestion is for

- **SITE** - the review surface: how you see verification, deltas and decisions without reading CSVs.
- **DATA** - inputs that do not exist in the repo yet, each with the exact source to obtain it from.
- **MODEL** - changes to how a line is produced (all of which are blocked on the DATA rows).
- **PROCESS** - the anti-luck machinery: grading, walk-forward discipline, multiple-comparison control,
  bet ledger. This is the category with the highest value-per-dollar, because it is what prevents a
  lucky month from becoming a strategy.
- **OPS** - bankroll, limits, and the human decisions that no pipeline can make for you.
