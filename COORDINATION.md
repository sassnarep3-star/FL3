# COORDINATION — shared task board

> **Protocol.** Any session working in this repo must read this file first and claim a task
> before editing files. Claim = write your session ID + file scope here, commit, push.
> A status of **needs review** means the item is published on the *Flagged for Review* page and
> does not block anything. Never mark a task verified without an official source link.
> If a claim is >60 minutes old with no commits, another session may take over (log the handoff).

- **Repo:** `sassnarep3-star/FL3`
- **Pages:** https://sassnarep3-star.github.io/FL3/ (source: branch `main`, path `/`, legacy build)
- **Data snapshot date:** 2026-11-14
- **Seasons in scope:** NFL 2026 regular season, through Week 10

---

## Active session

| Session ID | Branch | Scope | Started (UTC) |
|---|---|---|---|
| `arena-e8bf2075` | `arena/e8bf2075-fl3` | see claims below | 2026-11-14 |

Other sessions: none detected at claim time (`git branch -r` returned only `origin/main`;
`gh api .../branches` returned only `main`).

---

## Task board

| # | Task | Status | Owner | Files touched |
|---|---|---|---|---|
| T01 | Repo review + baseline audit | **done** | `arena-e8bf2075` | `README.md`, `docs/REPO_AUDIT.md` |
| T02 | Source registry (official links only) | **done** | `arena-e8bf2075` | `data/sources.json` |
| T03 | 2026 standings dataset + arithmetic verification | **done** | `arena-e8bf2075` | `data/standings.json` |
| T04 | Week 10 official injury report dataset | **done** | `arena-e8bf2075` | `data/injuries_week10.json` |
| T05 | Week 10 slate / fixtures dataset | **done** | `arena-e8bf2075` | `data/fixtures_week10.json` |
| T06 | Line-origination engine (model lines v0) | **done** | `arena-e8bf2075` | `scripts/compute_lines.py`, `data/lines_week10.json` |
| T07 | Strategy specs + validation gates + leaderboard scoring | **done** | `arena-e8bf2075` | `data/strategies.json` |
| T08 | Correlation registry (parlay/prop combos) | **done** | `arena-e8bf2075` | `data/correlations.json` |
| T09 | Decision register (questions / known / missing) | **done** | `arena-e8bf2075` | `data/decisions.json` |
| T10 | Suggestions with selectable paths | **done** | `arena-e8bf2075` | `data/suggestions.json` |
| T11 | Flagged-for-review register | **done** | `arena-e8bf2075` | `data/flagged.json` |
| T12 | Static site build (dashboard + category pages) | **done** | `arena-e8bf2075` | `scripts/build_site.py`, `assets/*`, `*.html` |
| T13 | Site verifier (links, sources, arithmetic, IDs) | **done** | `arena-e8bf2075` | `scripts/check_site.py` |
| T14 | Automation (refresh + verify in CI) | **done** | `arena-e8bf2075` | `scripts/fetch_official.py`, `.github/workflows/pages.yml` |
| T15 | Executive summary + methodology docs | **done** | `arena-e8bf2075` | `docs/EXECUTIVE_SUMMARY.md`, `docs/METHODOLOGY.md` |
| T16 | Integration: merge, PR, deploy verification | **done** | `arena-e8bf2075` | this file |

**File ownership rule for future sessions:** `data/standings.json`, `data/sources.json`,
`data/flagged.json` and every `*.html` at repo root are **shared outputs**. They are regenerated
by `scripts/build_site.py`; change them only through the generator, and only in an integration
task. `scripts/build_site.py` is single-owner at a time.

---

## Claim log

| UTC | Session | Action |
|---|---|---|
| 2026-11-14T00:00Z | `arena-e8bf2075` | Claimed T01–T05 (repo review + datasets). No competing claims found. |
| 2026-11-14T00:00Z | `arena-e8bf2075` | Claimed T06–T11 (model, gates, registers). Disjoint file sets from T01–T05. |
| 2026-11-14T00:00Z | `arena-e8bf2075` | Claimed T12–T15 (site build + verification + docs). |
| 2026-11-14T00:00Z | `arena-e8bf2075` | Claimed T16 (integration) — sole session, so integration performed by same ID. |

---

## Verification performed (see `docs/METHODOLOGY.md` for the procedure)

1. **Every dataset row carries a `src` field pointing at an official NFL.com URL.** Enforced by
   `scripts/check_site.py` (fails the build if any row lacks a source).
2. **Arithmetic cross-checks on official figures:** for all 32 clubs,
   `PF − PA = Net Pts` and `W + L + T = games played implied by PCT`. The build fails otherwise.
3. **Completeness checks:** 32 clubs present; 8 divisions × 4 clubs; 14 Week 10 games;
   28 clubs on the slate.
4. **Internal-consistency check against a second official page:** club records on the
   Week 10 injury page are compared with the standings snapshot.
5. **Link integrity:** every internal href resolves to a generated file; every external href is
   `https` (or the exact `http` URL NFL.com itself publishes) and non-empty.
6. **No value is inferred.** Where an official source does not state a fact, the cell is left
   empty and the item is listed in `data/flagged.json` and on `flagged.html`.

---

## Irregularities found in the source data (published, do not block)

All are listed with links on **`flagged.html`**. Summary:

| ID | Item | Why it matters |
|---|---|---|
| F01 | `nfl.com/standings` excludes the Week 10 Thursday game (WAS 24–21 NYG) that is marked FINAL on `nfl.com/schedules` | Using standings for Week 10 lines leaves WAS/NYG records one game stale |
| F02 | Ravens QB Lamar Jackson is reported out 6–10 weeks in NFL.com news, but **no Ravens QB appears on the Week 10 injury report table** | The injury table alone is not sufficient to detect every starter change |
| F03 | 2026 rosters differ from public expectation (e.g. Kyler Murray listed under MIN, J.J. McCarthy under NYG, Micah Parsons under GB) | Roster moves were recorded **as published**, not "corrected" to prior-season knowledge |
| F04 | Several listed players have **no** game status (practice-only listings) | These are excluded from the impact board rather than assumed available/unavailable |
| F05 | NFL.com publishes player rows without depth-chart rank | "2nd/3rd/4th string" cannot be confirmed from an official NFL source |
| F06 | `operations.nfl.com` injury-policy page returned an empty body on 2026-11-14 | Policy wording is unverified; not quoted anywhere on the site |
| F07 | No official NFL odds/line feed was reachable or licensed | Market comparison, CLV and "edge vs. market" are **unmeasurable** right now |
| F08 | Sandbox shell has no outbound network (only the agent's fetch tool does) | Refresh must run in CI, not locally |

---

## Handoff / merge record

| Item | Value |
|---|---|
| PR | [#1 — NFL decision system: verified datasets, line engine, and dashboard](https://github.com/sassnarep3-star/FL3/pull/1) |
| Merge result | merged into `main` (merge commit recorded on the PR) |
| Deploy | GitHub Pages, branch `main` / root, verified live after merge |
| Flagged items carried to site | F01–F08 on `flagged.html` |

<!-- INTEGRATION-RECORD -->
