# Suggestion Register (canonical)

The site's dedicated, reviewable version lives at `pages/suggestions.html`. This file is
the canonical copy. **Workflow:** every suggestion starts `PROPOSED`; nothing is
implemented until a reviewer records a decision (ACCEPTED / REJECTED with date + reviewer
ID) on the site page and in this file, and the task is claimed in `COORDINATION.md`.

| ID | Suggestion | Area | Expected benefit | Priority | Status | Decision |
|---|---|---|---|---|---|---|
| S-01 | Archive every official page before ingesting values (content hash + retrieval timestamp); re-fetch on a fixed schedule | Data integrity | Makes every published value reproducible; prevents wrong-week/wrong-version attribution (F-03/F-04) | High | PROPOSED | — |
| S-02 | Scheduled weekly collection of league injury report + final inactives into versioned CSV snapshots | Injury tracking | Builds the point-in-time history availability signals need (today only Nov 14 W10 snapshot exists) | High | PROPOSED | — |
| S-03 | Ingest officially published, dated team depth charts to verify starter→backup mapping before any depth-string claim | Depth verification | Replacement-strength analysis becomes evidence-based; keeps F-05 from being "solved" by guesswork | High | PROPOSED | — |
| S-04 | Connect official team/player stats endpoints to extend snapshots beyond PF/PA | Signal research | Real feature base for fundamentals signals | Medium | PROPOSED | — |
| S-05 | Choose and document a licensed odds provider before any edge/implied-probability/CLV computation | Line origination | "Edge" becomes measurable; without it we publish fair-value estimates only (F-02) | High | PROPOSED | — |
| S-06 | Require a committed pre-registration note (features, splits, costs, scoring, gates) before any strategy test | Validation | Prevents hindsight-fitting and multiple-testing inflation | High | PROPOSED | — |
| S-07 | Paper-only leaderboard until governance review; publish ranks with sample size + uncertainty | Leaderboard & rewards | Prevents unvalidated prize claims and post-hoc rule changes (F-07) | High | PROPOSED | — |
| S-08 | Estimate parlay-leg correlations from paired historical outcomes only; ban narrative-implied values | Correlation | Combo pricing stops depending on vibes; dependence gets uncertainty bands | Medium | PROPOSED | — |
| S-09 | Change control: new data columns/features/pages must reference a suggestion ID + coordination claim before merge | Process | Parallel sessions stop colliding; shared outputs change only under review | Medium | PROPOSED | — |
| S-10 | "Last verified" banner on every data table + repo changelog of which official pages were checked per build | Transparency | Stale snapshots can't masquerade as current status | Medium | PROPOSED | — |
| S-11 | Singles first; parlays/prop combos admitted to the leaderboard only after joint-outcome data + dependence estimates exist | Strategy rollout | Isolates skill before compounding dependence/variance | Medium | PROPOSED | — |
| S-12 | Persist accept/reject decisions (date, reviewer) and link accepted items to implementing PRs | Auditability | Makes the review-then-implement workflow real and auditable | Medium | PROPOSED | — |

## Improvement suggestions for the site itself (decision-making support)

These overlap the register but are scoped to the dashboard experience:

1. **Snapshot freshness surface** — every table already cites its source per row; add a
   visible "last verified" date per page (S-10) so decisions are made against known-age data.
2. **Flag-driven review queue** — the Flagged for Review page now carries 14 flags (F-01…F-14);
   sort by which blocked decision each flag unblocks (already mapped in
   [questions_and_gaps.md](questions_and_gaps.md)) so the reviewer can clear decision paths,
   not just bugs.
3. **Search over all tables** — the search helper currently filters one table at a time;
   a cross-page data search would speed manual verification passes.
4. **Data dictionary page** — one place defining each column (practice-status semantics,
   designation semantics) so reviewers don't re-derive meanings; blanks mean "official page
   showed nothing", never zero.
5. **Decision log page** — a visible trail of accepted suggestions and their PRs (S-12)
   keeps the review-before-implement contract honest.
