# FL3 — NFL Decision Intelligence

Collect, organize, and analyze NFL information for decision-making — with a source
link on every row, self-originated lines, a luck-removing strategy competition, and
injury/depth-deficiency tracking. Live site: GitHub Pages (`docs/` on `main`).

## Site map (docs/)
| Page | Contents |
|---|---|
| `index.html` | Dashboard — status, verified highlights, navigation |
| `executive-summary.html` | Key findings, model summary, decisions needed |
| `requirements.html` | Questions / information / answers required before decisions |
| `suggestions.html` | Suggestions board — review & choose a path before implementation |
| `lines.html` | Our originated lines vs the market (Week 10) with edges + flags |
| `injuries.html` | Official Week 10 injury report + depth-deficiency tracker (generated from CSVs) |
| `strategies.html` | Strategy catalog (singles, parlays, prop combos) behind validation gates |
| `leaderboard.html` | Competition design, luck-free scoring, reward options |
| `methodology.html` | Line model, signal research, correlations, validation gates |
| `data.html` | Standings, schedules, correlations, CSV index (generated from CSVs) |
| `sources.html` | Source registry (official / club / trusted tiers) |
| `flagged.html` | Flagged irregularities & unverified items for review |

## Data & model
- `data/*.csv` — machine-readable source of truth; every row links its source.
  Unverified cells are **blank + flagged**, never inferred.
- `models/originate_lines.py` — deterministic line-origination engine (stdlib only):
  net-points ratings + home field + transparent injury weights; also computes the
  correlation matrix and writes all CSVs. Run: `python3 models/originate_lines.py`
- `models/build_pages.py` — renders `docs/injuries.html` + `docs/data.html` from the
  CSVs so the site always matches the data.
- `research/sources.md` — fetch-by-fetch source log · `research/verification-log.md` —
  verification steps and checks · `COORDINATION.md` — shared task board (multi-session).

## Data provenance (as of 2026-11-14)
Official: NFL.com (standings, Week 10/11 schedules, official Week 10 game-status
injury report, news roundup) + club depth charts (MIN, GB, SEA, DET, NE, AZ, DAL).
Trusted market references: ESPN, SBR/bet365, CBS, betus, BetMGM/USA TODAY (always
labeled, never "official"). Model output is badged as such everywhere.

## Ground rules
1. Every fact links an official or labeled-trusted source.
2. If a value can't be confirmed, it stays blank and is flagged — never inferred.
3. Model output is labeled, never presented as verified fact.
4. Strategies enter the leaderboard only after passing the validation gates
   (see `docs/methodology.html` §4); performance columns stay empty until bets grade.
5. Suggestions are proposals — nothing is implemented before a recorded decision.
