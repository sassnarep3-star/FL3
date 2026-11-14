# Coordination board

## Active claims

| Task | Status | Owner session | File scope | Notes |
|---|---|---|---|---|
| NFL research, decision framework, sourced dashboard, and static site integration | done | `arena/39f57d31-fl3` | `COORDINATION.md`, `README.md`, `index.html`, `assets/**`, `data/**`, `pages/**`, `scripts/**`, `.github/workflows/**` | Sole active session observed at start; repository contained only README. Working on the assigned Arena branch (branch names are controlled by the session environment). No competing claims found. |

## Completed work / verification log

- Initial inspection: repository contained only the five-byte `README.md` title; no app, dataset, source archive, coordination board, or model. Verified with `git status`, `git log`, `cat README.md`, and `find` on 2026-11-14.
- Built static dashboard pages for executive summary, strategy proposals, validation gates, injury/depth workflow, decision questions, official sources, and flagged items. No third-party statistical values, player status, line, price, injury impact, model result, or correlation values were populated.
- Source pages opened/checked during this work: [NFL injury reports](https://www.nfl.com/injuries/), [NFL inactives](https://www.nfl.com/inactives/), [NFL player stats](https://www.nfl.com/stats/player-stats/), [NFL team stats](https://www.nfl.com/stats/team-stats/), [NFL team directory](https://www.nfl.com/teams/), [NFL Next Gen Stats description](https://operations.nfl.com/gameday/technology/performance-tracking-data-next-gen-stats), [NFL rulebook](https://operations.nfl.com/the-rules/nfl-rulebook), [NFL gambling / integrity overview](https://media.nfl.com/lsb), and NIST references on [confidence limits](https://www.itl.nist.gov/div898/handbook/eda/section3/eda352.htm) and [correlation](https://www.itl.nist.gov/div898/handbook/glossary.htm).
- Irregularity recorded as F-03: NFL injury route `/injuries/league/2025/reg4` produced a title indicating Week 10 while body content indicated Week 4, and search snippets differed. No data from this ambiguous route was imported.
- Explicit gaps flagged: no dataset or odds history; no verified backup string/depth order; no historical injury snapshots; no paired observations/correlation; no test results; and no reward/legal/governance rules.
- Verification: `python3 scripts/check_site.py` checks all seven HTML pages, resolves local links, and requires an approved official-domain source link on every table body row (59 rows). The static GitHub Pages workflow runs this check before deployment.

## Handoff / integration notes

- Static GitHub Pages workflow: `.github/workflows/pages.yml`; publish source is GitHub Actions. The active branch remains `arena/39f57d31-fl3` per Arena's fixed-branch constraint.
- The site is a research blueprint, not a betting service. Dynamic injury/lineup status and betting outcomes remain blank until a timestamped official feed, approved role evidence, historical odds, and backtest data are integrated.
- PR #1: [Build sourced NFL lines research dashboard](https://github.com/sassnarep3-star/FL3/pull/1) — **merged** to `main` with merge commit `4bbc26c82e3b29ff28e3f3ee50d0dd6d10ad0a38` at 2026-11-14 03:01:06 UTC.
- GitHub Pages: [https://sassnarep3-star.github.io/FL3/](https://sassnarep3-star.github.io/FL3/) — Pages API reports `built`, source `main:/`; deploy workflow run [43549389656](https://github.com/sassnarep3-star/FL3/actions/runs/43549389656) completed successfully. PR validation also passed (run [43549332412](https://github.com/sassnarep3-star/FL3/actions/runs/43549332412)).
