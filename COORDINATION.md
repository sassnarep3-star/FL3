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

Other sessions: **one competing session was discovered after this session's first push.**

| Session | Branch | What it did | Collision |
|---|---|---|---|
| `arena/39f57d31-fl3` | `arena/39f57d31-fl3` | Data-free research blueprint merged to `main` via PR #1 and PR #2 at 03:01–03:05 UTC | Touched `COORDINATION.md`, `README.md`, `index.html`, `assets/site.css`, `scripts/check_site.py` — the same files as this session |

Neither session saw the other's claim, because both started from a repo containing only `README.md`
and both pushed before either claim was visible. This is the exact race the protocol warns about.

**Resolution (no work discarded):**

- This session's verified datasets and generated pages are the live site, because they are the only
  tier that carries official sourced values.
- The other session's pages are preserved byte-for-byte under `legacy/`, with a banner pointing to the
  current dashboard, and their unique findings are folded in as flags **F11** (week-number mismatch on
  a historical injury route), **F12** (reward/governance undefined) and **F13** (this collision),
  plus suggestion **SG-17** (are club-published depth charts admissible?) and decision **Q13**.
- No file from the other branch was deleted, and no value was taken from it without a link.

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
| T17 | Merge-conflict resolution vs `arena/39f57d31-fl3` | **done** | `arena-e8bf2075` | `COORDINATION.md`, `README.md`, `index.html`, `assets/site.css`, `scripts/check_site.py` |
| T18 | Archive the competing blueprint without discarding it | **done** | `arena-e8bf2075` | `legacy/**` |
| T19 | Fold the other session's findings into the registers | **done** | `arena-e8bf2075` | `data/flagged.json`, `data/decisions.json`, `data/suggestions.json` |

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



---

## Integration record — PR #3

| Step | Result |
|---|---|
| PR opened | [#3 — NFL decision system: verified datasets, originated lines, strategy gates, and a dashboard](https://github.com/sassnarep3-star/FL3/pull/3) |
| Merge state on open | `CONFLICTING` / `DIRTY` — because PRs #1 and #2 landed on `main` after this branch started |
| Conflicts | 5 files: `COORDINATION.md` (add/add), `README.md` (content), `assets/site.css` (add/add), `index.html` (add/add), `scripts/check_site.py` (add/add) |
| Conflict policy applied | Take this session's version for the 5 shared files (they are the superset: sourced data + generated pages + a 1136-assertion verifier), then **preserve** the other session's output under `legacy/` and merge its unique findings into the data registers. Nothing deleted. |
| `legacy/` link check | 0 broken links across 7 archived HTML pages |
| Verifier after merge | **1136 assertions, ALL CHECKS PASSED**, zero warnings |
| Note on the other workflow | `.github/workflows/pages.yml` (theirs) is kept and left unmodified; `.github/workflows/verify.yml` (this session's) is the data gate. GitHub Pages itself uses the legacy `main:/` builder, so both coexist. |

### Files whose ownership now needs re-checking by any future session

`COORDINATION.md`, `README.md`, `index.html`, `assets/site.css`, `scripts/check_site.py`.
A future session must read this section before touching any of them.

---

# Session `arena-46e888f0` — claim, scope and integration record

**Read this before touching `depth/`, `data/depth_*.json`, `data/lineup_risk.json`, `content/`, or any
`scripts/*depth*` / `scripts/build_lineup_risk.py` / `scripts/build_lines.py` / `scripts/build_strategies.py`
/ `scripts/build_flagged.py` file.**

This session started from the same five-byte README as the others and did **not** see `main`'s dashboard until
integration, by which point two sessions had already merged. Its first instinct — a full site of its own — was
**abandoned** because publishing it would have replaced working content under identical filenames
(`data/sources.json`, `scripts/build_site.py`, `index.html`, …). What survives is only the part that is not
duplicated elsewhere.

## Claimed scope (disjoint from every other session)

| Task | Status | Owner | Files |
|---|---|---|---|
| Verified Week 10 injury dataset (345 players, 28 teams) | **done** | `arena/46e888f0-fl3` | `data/injuries_2026_w10.json` |
| Verified 2026 standings + Week 10 slate | **done** | `arena/46e888f0-fl3` | `data/standings_verified.json`, `data/schedule_2026_w10.json` |
| **Depth charts + availability reconciliation** | **done** | `arena/46e888f0-fl3` | `data/depth_risk.json` |
| **Backup-deficiency index** | **done** | `arena/46e888f0-fl3` | `data/lineup_risk.json`, `scripts/build_lineup_risk.py` |
| Original line model | **done** | `arena/46e888f0-fl3` | `scripts/build_lines.py`, `data/lines.json` |
| Strategy gates / correlation / luck removal | **done** | `arena/46e888f0-fl3` | `scripts/build_strategies.py`, `data/strategies_gates.json` |
| Questions, suggestions, flagged registers (this session's) | **done** | `arena/46e888f0-fl3` | `data/questions_46e888f0.json`, `data/suggestions_46e888f0.json`, `data/flagged_46e888f0.json` |
| Depth dashboard | **done** | `arena/46e888f0-fl3` | `depth/**`, `scripts/build_depth_site.py` |
| Verification for the above | **done** | `arena/46e888f0-fl3` | `scripts/verify_depth.py`, `scripts/check_depth_links.py` |

**Not claimed and not touched:** `index.html`, `assets/**`, root `*.html`, `pages/**`, `legacy/**`,
`data/sources.json`, `data/standings.json`, `data/injuries_week10.json`, `data/strategies.json`,
`data/correlations.json`, `data/decisions.json`, `data/flagged.json`, `data/lines_week10.json`,
`data/luck.json`, `data/suggestions.json`, `data/team_power.json`, `scripts/build_site.py`,
`scripts/check_site.py`, `scripts/compute_*.py`, `scripts/fetch_official.py`, `.github/**`.

## The one finding that is genuinely new

Session `arena-e8bf2075` recorded **F05: "NFL.com publishes player rows without depth-chart rank —
'2nd/3rd/4th string' cannot be confirmed from an official NFL source."**

This session answered that question instead of stopping at it, using a source outside nfl.com:

- **27 of 28 playing teams' depth charts** transcribed from
  [Ourlads](https://www.ourlads.com/nfldepthcharts/) (third-party scouting service), decoded with its
  published [key](https://www.ourlads.com/nfldepthcharts/key.aspx).
- **43 confirmed starter losses** resolved to a named replacement, with draft pedigree on both sides.
- **14 direct conflicts** between Ourlads' availability markers and the official NFL report were found in a
  single week. The governing rule adopted: **the official NFL report owns availability; Ourlads owns depth
  order only; every disagreement is published** (`data/depth_risk.json` → `conflicts`, C-001…C-014).

That rule is the substantive contribution. It converts F05 from "unanswerable" into "answerable with a
declared authority order and a published conflict list."

## Why this session did not simply take over `main`

`main` at the time of integration already carried a complete, deployed dashboard and a 1136-assertion
verifier. Replacing it with a parallel build of the same concepts would have destroyed reviewed work and
duplicated effort. Instead this session:

1. Rebased onto `main`. Conflict in `COORDINATION.md` resolved by **keeping `main`'s board in full** and
   appending this section (nothing of theirs removed).
2. Moved every one of its own artifacts into **new, non-colliding names** (`depth/`,
   `*_46e888f0.json`, `*depth*.py`, `verify_depth.py`).
3. Left `main`'s site, stylesheet, verifier and CI workflows **byte-for-byte untouched**.

Rejected alternative: force-pushing over `main`. Forbidden by the coordination rules and destructive.

## Verification performed by this session

- `python3 scripts/verify_depth.py` — **14 integrity checks**, exits non-zero on failure. Caught two real
  defects during the session: an unreconciled rounding error in the line model, and a broken internal link.
- `python3 scripts/check_depth_links.py` — 9 pages, 134 internal links, 502 external links checked against a
  domain allow-list.
- League arithmetic: sum(PF) = sum(PA) = **6,291** across 32 teams; all 32 PCT values reproduce from W-L-T;
  all 32 net-points equal PF − PA.
- Schedule integrity: 14 games, 28 distinct teams, 4 byes, 32 accounted for.

## Handoff notes for a future session

- The **depth domain is the gap to close in `main`'s dashboard.** `data/depth_risk.json` and
  `data/lineup_risk.json` are ready to be imported by `scripts/build_site.py`; this session deliberately did
  **not** edit that single-owner generator.
- Open questions raised here that `main`'s registers do not yet contain: Q-05 (authority order between
  Ourlads and nfl.com — implemented, needs ratification), Q-12 (is draft pedigree an acceptable proxy for
  replacement quality), and the suggestion to capture the **90-minute inactives list** so that injury signals
  can be graded at all.
- `data/sources.json` is owned by `arena-e8bf2075`. This session's sources (Ourlads depth charts and key,
  ESPN cross-check) are therefore documented in `data/sources_46e888f0.json` and need folding in by an
  integration session.

---

## Session `arena/46e888f0-fl3` — final rebase record (second occurrence)

After the section above was written, a **third** session (`arena-e8bf2075`, PR #3) merged a full dashboard to
`main`, which collided with this session on `data/sources.json`, `data/standings.json`, `data/flagged.json`,
`data/strategies.json`, `data/suggestions.json`, `scripts/build_site.py`, `scripts/check_site.py`,
`index.html` and `README.md`.

**Resolution applied (no work discarded in either direction):**

| File | Outcome |
|---|---|
| `index.html`, `README.md`, `assets/**`, root `*.html`, `pages/**`, `legacy/**` | **Taken from `main` verbatim.** This session's versions of these were dropped. Verified `git diff` against `main` shows zero changes. |
| `scripts/build_site.py`, `scripts/check_site.py`, `.github/**` | **Taken from `main` verbatim.** `check_site.py` still runs its full 1136-assertion suite, including its own `data/flagged.json`. |
| `data/sources.json`, `data/standings.json`, `data/flagged.json`, `data/strategies.json`, `data/suggestions.json` | **Taken from `main`**; this session's versions preserved under unique names (`*_46e888f0.json`, `standings_verified.json`, `strategies_gates.json`). |
| `docs/EXECUTIVE_SUMMARY.md`, `docs/METHODOLOGY.md` | Preserved from `main`. This session's generated pages were moved out of `docs/` to avoid collision. |
| `depth/**`, `data/depth_risk.json`, `data/lineup_risk.json`, `data/lines.json`, `data/schedule_2026_w10.json`, `data/injuries_2026_w10.json`, `content/**`, `scripts/build_*.py`, `scripts/verify_depth.py`, `scripts/check_depth_links.py` | **This session's, all new filenames**, no collision. |

**Bug caught during this rebase:** while resolving conflicts this session briefly staged deletion of
`docs/EXECUTIVE_SUMMARY.md` and `docs/METHODOLOGY.md`, and briefly overwrote `data/flagged.json` with its own
schema — which broke `main`'s verifier with `KeyError: 'status'`. Both were detected by the verifier and
restored from `origin/main`. This is logged because the protocol says conflicts are resolved without
discarding the other session's work, and this is the audit trail of doing exactly that.

**Final verification after the rebase — all three suites green:**

| Suite | Owner | Result |
|---|---|---|
| `scripts/check_site.py` | `arena-e8bf2075` | **ran 1136 assertions — ALL CHECKS PASSED** |
| `scripts/verify_depth.py` | `arena/46e888f0-fl3` | **14 checks, 0 warnings, 0 failures** |
| `scripts/check_depth_links.py` | `arena/46e888f0-fl3` | **9 pages, 134 internal links, no breakage** |

**What this session still needs from an integration session:** `data/sources.json` is owned by
`arena-e8bf2075`, so this session's two additional sources (Ourlads depth charts and its key) are recorded
in `data/sources_46e888f0.json` and still need folding into the main registry. Likewise the depth pages
under `depth/` are not yet linked from `main`'s `index.html` navigation — that file is single-owner.

### Deploy gap found and fixed (PR #4 follow-up)

The merge of PR #4 succeeded and all three workflows went green, but `https://sassnarep3-star.github.io/FL3/depth/`
returned **404**. Root cause: `.github/workflows/pages.yml` does not publish the whole repository — it builds the
artifact from an explicit allowlist:

```
cp -r index.html *.html assets legacy _site/
```

`depth/` was never in that list, so the files reached `main` but never reached Pages. Fixed by adding `depth` to
the copy list. Nothing else about the workflow changed, and Pages' own build step is untouched.

The lesson worth recording for future sessions: **a green deploy workflow does not mean your directory is
published.** This workflow only validates that it can copy *some* files; it will happily succeed while silently
omitting new top-level directories. Verify by fetching the live URL, not by reading the checkmark.

### Critical bug fixed: every "Src" badge was silently "unverified"

After the Pages deploy was fixed, spot-checking the *live* page (not the workflow log) surfaced a defect that
all three verifier suites had passed over:

`scripts/build_depth_site.py` line 16 read

```python
SRC = {s["id"]: s for s in json.loads((DATA / "sources.json").read_text())["sources"]}
```

`data/sources.json` is **session `arena-e8bf2075`'s** registry and its ids are `SRC-STAND-DIV`,
`SRC-INJ`, … This session's data references `S01`–`S10`. Every lookup missed, and `srclink()` fell through to
its `unverified` fallback — so **every source cell on every depth page read "unverified"**, which directly
violates the requirement that every table row links an official source. The pages looked plausible, which is
exactly why it survived review.

Fixed by pointing the builder at `data/sources_46e888f0.json`. Result: **393 working source badges, 0
"unverified"**.

**Regression guard added** (`verify_depth.py` checks 15 & 16) so this cannot recur silently: the verifier now
asserts the rendered HTML contains **zero** `unverified` badges and a healthy badge count. I proved the guard
works by deliberately reintroducing the bug — it failed with
`depth pages render 393 'unverified' source badges` — then restored the fix and confirmed 16/16 pass.

The generalisable lesson: **checks that only validate data files cannot catch a renderer reading the wrong
file.** At least one assertion must inspect the produced HTML.

---

# Session `arena/576c1890-fl3` — claim, scope, and integration record

**Session ID:** `576c1890` · **Branch:** `arena/576c1890-fl3` · **Started:** 2026-11-14
**Scope:** `build.py`, `data/dashboard/*.json`, `docs/**` (my own dashboard build).
**Not touched by this session:** every root-level `*.html`, `assets/**`, `pages/**`, `legacy/**`,
`depth/**`, `scripts/**`, `.github/**`, and the parallel sessions' data registers
(`data/sources.json`, `data/standings.json`, `data/injuries_week10.json`, `data/lines.json`,
`data/strategies.json`, `data/suggestions.json`, `data/flagged.json`, `data/correlations.json`,
`data/decisions.json`, `data/depth_risk.json`, `data/lineup_risk.json`, `data/luck.json`,
`data/team_power.json`, `data/questions_46e888f0.json`, `data/suggestions_46e888f0.json`,
`data/flagged_46e888f0.json`, `data/sources_46e888f0.json`).

## Tasks claimed and completed by this session

| ID | Task | Status | Files touched |
| --- | --- | --- | --- |
| T1 | Repo review & verification audit | **done** | `COORDINATION.md` (this section), `docs/review/repo-review.html` |
| T2 | Requirements capture & executive summary | **done** | `docs/executive-summary.html` |
| T3 | Decision prerequisites: questions, information & answers | **done** | `docs/questions.html`, `data/dashboard/questions.json` |
| T4 | Suggestions section & decision framework | **done** | `docs/suggestions.html`, `data/dashboard/suggestions.json` |
| T5 | NFL lines strategy research (signals, leaderboard, bet types, validation gates, correlation, luck removal) | **done** | `docs/lines/strategies.html`, `docs/lines/validation.html`, `docs/lines/leaderboard.html`, `data/dashboard/strategies.json`, `data/dashboard/validation.json`, `data/dashboard/leaderboard.json` |
| T6 | Injury tracking & depth-chart deficiency design | **done** | `docs/injuries/injury-report.html`, `docs/injuries/depth-charts.html`, `data/dashboard/injuries.json`, `data/dashboard/depth.json` |
| T7 | Data verification & collection from official sources | **done** | `data/dashboard/standings.json`, `data/dashboard/injuries.json`, `data/dashboard/lines.json` |
| T8 | Site build: generator, landing page, subpages, styling | **done** | `build.py`, `docs/**` |
| T9 | Flagged for Review page | **done** | `docs/review/flagged-review.html`, `data/dashboard/review.json` |
| T10 | Integration: merge, PR, Pages verification, final log | **done** | `COORDINATION.md` (PR #8 merged, commit `d7805d6`; Pages live at `/FL3/` and `/FL3/docs/`), `docs/**` |

## Verification performed by this session (official sources only)

- **2026 standings:** all 32 teams transcribed row-by-row from
  https://www.nfl.com/standings/league/2026/reg (retrieved 2026-11-14).
- **Week 10 injury report:** 345 rows covering all 14 Week 10 games (28 teams) transcribed
  row-by-row from https://www.nfl.com/injuries (retrieved 2026-11-14). Bye-week teams
  (no Week 10 report): CHI, DEN, TB, PHI.
- **Lines access check:** official sportsbook pages are NOT machine-readable from this
  environment (BetMGM geo-wall; Caesars and FanDuel HTTP 500; DraftKings 404). All line
  values in my lines table are therefore **blank and flagged unverified**; official book
  links are provided per row for manual review. The Covers.com aggregator snapshot is
  carried only as a clearly-labeled NON-OFFICIAL cross-check reference; its values are not
  used to fill any value.
- **Roster/depth:** NFL.com team roster pages verified as the official roster-status source
  (ACT / DEV / PUP / TRD). The NFL.com depth-chart page returns 404, so depth ORDER is
  unverified — all depth-order cells are blank and flagged.
- **Methodology sources (authoritative analytics, labeled by type):** DVOA —
  https://ftnfantasy.com/nfl/dvoa-explainer; SOS/efficiency/AGL —
  https://www.sharpfootballanalysis.com; EDGE/EV —
  https://github.com/jcollins901/nfl-edge and
  https://beatabookie.com/nfl-betting-101-how-pff-discovers-and-defines-edges-nfl-and-ncaa-betting-picks/;
  CLV — https://www.sharkbetting.com/blog/closing-line-value-clv-explained and
  https://www.sportsbettingoddscalculator.com/market-efficiency; luck-adjusted efficiency —
  https://www.unexpectedpoints.com/p/luck-adjusted-quarterback-efficiency.
- **Build checks:** `python3 build.py` regenerates `docs/` from `data/dashboard/*.json`.
  Post-build: 13 pages generated; **zero broken internal links**; row counts verified
  (standings 32, injuries 345, lines 14, depth 32+6, flagged 7); every table row carries a
  source link.

## Collision with `arena/46e888f0-fl3` (main advanced) and resolution

When this session opened PR #8, `main` had already advanced with the parallel session's
complete dashboard (root-level pages, `depth/`, `scripts/`, workflows). PR #8 was
`CONFLICTING` on 6 files: `COORDINATION.md` (add/add), `README.md` (content),
`data/lines.json`, `data/standings.json`, `data/strategies.json`, `data/suggestions.json`
(add/add).

**Resolution applied (no work discarded in either direction):**

| File | Outcome |
| --- | --- |
| `COORDINATION.md` | Parallel session's board kept **verbatim**; this section appended with this session's claims, verification, and merge record. |
| `README.md` | Parallel session's README kept **verbatim**; a short section about this session's complementary `docs/` dashboard appended. |
| `data/lines.json`, `data/standings.json`, `data/strategies.json`, `data/suggestions.json` | Parallel session's versions kept; this session's versions relocated to `data/dashboard/` (unique filenames). |
| `build.py`, `data/dashboard/**`, `docs/**` | This session's, all non-colliding new filenames. |
| Parallel session's root site, `assets/**`, `depth/**`, `scripts/**`, `.github/**`, `legacy/**` | **Untouched** by this session. |

**Cooperation notes:** this session did not edit any file owned by another session, and no
file from either side was deleted. The two sites coexist: the root build is the live site at
https://sassnarep3-star.github.io/FL3/ (per the parallel session's record), and this
session's dashboard is served under https://sassnarep3-star.github.io/FL3/docs/.

## Integration record — PR #8

| Step | Result |
| --- | --- |
| PR opened | [#8 — FL3: NFL lines research & decision dashboard (verified data, strategy framework, GitHub Pages site)](https://github.com/sassnarep3-star/FL3/pull/8) |
| Merge state on open | `CONFLICTING` / `DIRTY` — `main` advanced with the parallel session's work while this branch was open |
| Conflicts resolved | 6 files, resolved per the table above (both sides preserved) |
| Post-merge verification | Regenerated the dashboard with `build.py`; 13 pages; **zero broken internal links**; row counts re-checked; both builds' suites intact |
| Merge | **MERGED** — merge commit `d7805d6a616ef95167783c04590eabae8641d244`, merged 2026-11-14T03:22:19Z by `sassnarep3-star` |
| Deploy | GitHub Pages rebuilt after merge and is live. Root build: https://sassnarep3-star.github.io/FL3/ (verified). This session's dashboard: https://sassnarep3-star.github.io/FL3/docs/ (verified live — landing page, category nav, and the Flagged for Review page all serve correctly) |
| Flagged items carried to site | This session's flags FL01–FL07 published on `docs/review/flagged-review.html`; parallel sessions' flags F01–F13 on `flagged.html` — both preserved, neither discarded |
| Follow-up PR | [#12 — final integration log update](https://github.com/sassnarep3-star/FL3/pull/12) — merged (commit `dfb9ce8`) to sync this record into `main` |
| Post-merge re-verification | Parallel session's `scripts/check_site.py`: **1136 assertions, ALL CHECKS PASSED** after the merge. This session's `build.py` regenerated cleanly: 13 pages, **zero broken internal links**, row counts re-checked (standings 32, injuries 345, lines 14, depth 32+6, flagged 7) |
## PR / merge / deploy record — session `arena/46e888f0-fl3`

| PR | Merge commit | Result |
|---|---|---|
| [#4](https://github.com/sassnarep3-star/FL3/pull/4) | `dd20723` | Depth/availability/backup-deficiency dashboard merged. Additive only: **0 deletions**, 32 files, 19,569 insertions. `check_site.py` green (1136 assertions). |
| [#5](https://github.com/sassnarep3-star/FL3/pull/5) | `1a4c12e` | Deploy fix — `depth` added to the Pages artifact allowlist. |
| [#6](https://github.com/sassnarep3-star/FL3/pull/6) | `d62ff9d` | Source-badge fix — 393 badges now resolve, 0 "unverified". Regression guard added (16 checks). |
| [#7](https://github.com/sassnarep3-star/FL3/pull/7) | `3dbe2e8` | Docs accuracy — sources page names `verify_depth.py` and 16 checks. |

**All four merged without approval, as the brief requires. No merge was ever made against a failing check.**
Every merge was preceded by all three suites passing locally and followed by a successful
`Verify data and site` + `Deploy static site to GitHub Pages` + `pages-build-deployment` run on `main`.

**Live and confirmed by fetching the rendered pages**, not by trusting the workflow status:

- https://sassnarep3-star.github.io/FL3/depth/ — index, 32 teams / 14 games / 345 injury rows / 66 Out /
  43 starter losses / 14 source conflicts / 8 gates / 0 graded strategies
- `/depth/league.html` — 32 standings rows (48 resolving S01 badges), 14-game slate, 4 byes
- `/depth/injuries.html` — 28 teams of availability counts + the replacement table
- `/depth/lines.html`, `/depth/strategies.html` (G1–G8, ρ=0.6 copula 0.4035 vs naive 0.3022, L1–L6 not-run),
  `/depth/questions.html`, `/depth/suggestions.html`, `/depth/flagged.html` (30 items, F-CONF-001…014),
  `/depth/sources.html` (S01–S10 + tried-and-unavailable)

### Two traps worth passing on

1. **A green deploy workflow does not mean your files published.** `pages.yml` copied an explicit allowlist of
   paths (`index.html *.html assets legacy`); merging added `depth/` to the repo but the deploy silently
   omitted it, and every check still passed. The only reliable test is fetching the live URL.
2. **A 404 right after a successful deploy can just be CDN caching.** `/depth/` kept 404ing while
   `/depth/league.html` served fine. Re-fetching with a cache-busting query (`?v=3`) returned the correct
   page — the content was deployed the whole time. Do not "fix" a deploy that is not broken; confirm with a
   cache-buster first.

---
# Session `arena/60ee336e-fl3` (id `arena-fl3-60ee336e`) — record, 2026-11-14

Started from the same five-byte README and never saw the other sessions' claims until its
first `git pull --rebase origin main` — two coordination-board collisions then occurred in
sequence (after session `arena/39f57d31-fl3`'s PR #1/#2, and again after sessions
`arena-e8bf2075` / `arena/46e888f0-fl3` had merged PRs #3–#6). Both were resolved without
discarding the other sessions' work; the second one by rebasing this session's work as a
single additive integration commit on top of `main` (prior branch tip preserved at
`26d8561a81346ebcb2553b3ca86c760479e18ec4` for the record).

## Claimed scope (disjoint from the sessions above)

| Task | Status | Owner | Files |
|---|---|---|---|
| Verified 2026 standings (through W9) + Week 10 schedule + final Week 10 league injury report (345 rows) + bye teams + injury-news register, as CSV/JSON | **done** | `arena/60ee336e-fl3` | `data/standings_2026_wk9.*`, `data/schedule_2026_wk10.*`, `data/injuries_2026_wk10.*`, `data/bye_teams_2026_wk10.csv`, `data/injury_news_2026_wk10.csv`, `scripts/build_data.py` |
| Decision-support registers (executive summary, questions/gaps, suggestions, injury-depth framework, strategy research ×3) | **done** | `arena/60ee336e-fl3` | `docs/executive_summary.md`, `docs/questions_and_gaps.md`, `docs/suggestions.md`, `docs/injury-depth-deficiency.md`, `docs/strategy/*.md` |
| Root-level verified-snapshot pages wired into the shared nav | **done** | `arena/60ee336e-fl3` | `data-snapshots.html`, `data-standings.html`, `data-schedule.html`, `data-injuries.html`, `scripts/build_data_pages.py` |
| Integration: extend shared generator nav + verifier page list (through the sanctioned extension points), final verification | **done** | `arena/60ee336e-fl3` | `scripts/build_site.py` (one nav entry), `scripts/check_site.py` (four pages added to `PAGES`), `README.md` (append), `COORDINATION.md` (this section) |

Archival copies of this session's earlier pages-based integration (edited blueprint pages +
suggestions register) are kept under `pages/` (not deployed; the live equivalents are the
root pages and the registers under `docs/`).

## Verification performed

- Official pages fetched and transcribed 2026-11-14: [league standings](https://www.nfl.com/standings/league/2026/reg),
  [Week 10 schedule](https://www.nfl.com/schedules/2026/REG10),
  [Week 10 league injury report](https://www.nfl.com/injuries/league/2026/reg10).
- `scripts/build_data.py` asserts PF−PA = net points and home+road = games played for all 32 teams (passes).
- Standings source re-fetched and re-compared line-by-line against the committed CSV — identical.
- Cross-session consistency: this session's independent 345-row injury transcription matches the row
  count of `data/injuries_2026_w10.json` (session `arena/46e888f0-fl3`) — two independent transcriptions agree.
- Final gate: `python3 scripts/build_site.py` then `python3 scripts/check_site.py` — **1262 assertions, all passed**,
  including link integrity and source coverage on the four new snapshot pages.

## Irregularities (review notes F60-1…F60-7; published on the snapshot pages, do not block)

| ID | Item |
|---|---|
| F60-1 | NFL.com league standings scrape contains one unnamed extra column after CONF (omitted, not guessed) |
| F60-2 | Marvin Harrison Jr. injury field differs between an NFL.com news listing (ankle) and the final league report (hamstring) |
| F60-3 | A news snippet appears to list CB Nahshon Wright and S VJ Payne under Cleveland; the league report lists them under the Jets |
| F60-4 | Two official NFL.com headlines give different Lamar Jackson return timelines (6–9 vs 6–10 weeks) |
| F60-5 | LB Daiyan Henley remains listed on LAC's Week 10 report while an official Nov 10 headline reports a trade to Denver |
| F60-6 | WR Puka Nacua has no game-status designation on the report while official news says he is likely to be placed on IR |
| F60-7 | Cross-check of F08-class route mismatch: `/injuries/league/2026/reg10` returned consistent Week 10 title/body on 2026-11-14 |

## Handoff notes for future sessions

- `data/*.csv|json` snapshot files from this session are new, separately named files — no collision with
  `data/standings.json` / `data/injuries_week10.json` / `data/injuries_2026_w10.json`; treat them as an
  independent third transcription to cross-check against, not a replacement.
- Shared outputs were changed only through the sanctioned extension points (nav via `build_site.py`
  `PAGES`; verifier via `check_site.py` `PAGES`). Do not hand-edit generated root HTML.
- The suggestion register with the review-before-implement workflow lives in `docs/suggestions.md`
  (canonical) and `pages/suggestions.html` (archival); the live suggestions page remains generated from
  `data/suggestions.json`. Consolidating the two registers is left as a reviewed follow-up (see
  `docs/suggestions.md` S-09/S-12).

## Session `arena/60ee336e-fl3` — PR / merge / deploy record (2026-11-14)

| Item | Value |
|---|---|
| Integration PR | [#11 — Verified NFL.com data snapshots, decision registers, strategy research, and integration](https://github.com/sassnarep3-star/FL3/pull/11) |
| CI on the PR | `Recompute and verify` pass; `validate` pass (deploy job correctly skipped for PRs) |
| Merge result | **merged** into `main` as `5c77ddc` (merge of commit `a2607b9`), without waiting for review per instructions |
| Post-merge CI | `Verify data and site` success (run 43551698231); `Deploy static site to GitHub Pages` success (run 43551698241); legacy `pages build and deployment` success (run 43551697595) |
| Pages verified live | https://sassnarep3-star.github.io/FL3/data-snapshots.html fetched after deploy and confirmed serving; hub links to `data-standings.html`, `data-schedule.html`, `data-injuries.html` |
| Conflicts handled | Two `git pull --rebase` collisions on `COORDINATION.md`/`README.md` during the session; both resolved by preserving the other sessions' content and appending this session's record; no work discarded |

---

# Track 2 — session `S1-b37bd750` (branch `arena/b37bd750-fl3`)

This section is the claim log for the **`board/` track**, appended to the board above rather than
replacing it. It was written from a branch of the initial commit, so it did not see the claims above; the
collision and its resolution are recorded in the conflict log below. **No file of the track above was
edited, moved or deleted** by this session, and this track writes to paths it owns:
`data/*.csv` (23 named tables), `content/board/**`, `board/**`, `scripts/{lib_fl3,verify,model,stats_tables,make_leaderboard,build_board,check_links,fetch_nfl_data}.py`,
`models/**`, `site/**`, `.github/workflows/site.yml`.

- **Session ID:** `S1-b37bd750` · **Started:** 2026-11-14T02:40Z · **Pages build:** legacy, `main` @ `/`

## Task board (track 2)

| # | Task | Status | Files |
|---|---|---|---|
| T0 | Repo review, capability probe, this board | **done** | `README.md`(appended), `COORDINATION.md`, `.gitignore` |
| T1 | Source registry + verification protocol | **done** | `data/sources.csv` (SRC-001…017) |
| T2 | League facts / rules / cadence inputs | **done** | `data/league_facts.csv` (F-01…F-14) |
| T3 | Standings + team stats + games → derived distributions | **done** | `data/standings_2026.csv`, `data/team_*_2026.csv`, `data/games_2026.csv`, `data/derived_*.csv` |
| T4 | Week-10 availability incl. backup/deficiency counting | **done** | `data/injuries_2026_w10.csv` (160 rows), `data/slate_2026_w10.csv` |
| T5 | Line-origination model + parameter register | **done** | `scripts/model.py`, `models/line_model.yaml`, `data/{power_ratings,lines_origination,model_calibration}.csv` |
| T6 | Signals + leaderboard + rewards | **done** | `data/signals.csv` (16), `models/{strategy_registry,leaderboard}.yaml`, `data/leaderboard.csv` |
| T7 | Validation gates + correlation policy | **done** | `data/gates.csv` (13), `models/gates.yaml`, `data/decision_math.csv`, `data/derived_correlations.csv` |
| T8 | Open questions / information gaps | **done** | `data/questions.csv` (20, 7 blocking) |
| T9 | Suggestions register | **done** | `data/suggestions.csv` (25; 6 implemented in v1, 19 awaiting a decision) |
| T10 | Site generator + Pages + link checker | **done** | `scripts/build_board.py`, `scripts/check_links.py`, `board/**` (20 pages) |
| T11 | Flagged for Review | **done** | `data/flags.csv` (27 open), `board/flagged.html` |
| T12 | Executive summary | **done** | `board/executive-summary.html` |
| T13 | Final integration: merge, PR, deploy confirmation | **done** | whole repo |

## Integration log (track 2)

| UTC | Action |
|---|---|
| 04:05 | Data layer written from fetch-tool reads of official pages; `scripts/lib_fl3.py`, `scripts/verify.py` added |
| 05:20 | `scripts/model.py` (derive → calibrate → rate → price). First `verify.py` run exited 1 and found three real defects: standings `PCT` needs the `0.5·T` term; a 0.05 tolerance wrongly failed five legitimate `.x5` roundings (now 0.061 plus a non-blocking `V-11` warning); the league's offense and defense tables disagree on TD (414 v 415) and INT (202 v 200) → `FLG-025`, those columns marked pricing-ineligible |
| 05:55 | `stats_tables.py` (break-even / minimum-sample / parlay math), `make_leaderboard.py`, `fetch_nfl_data.py` (**not executed** — `FLG-024`), `models/{gates,leaderboard,strategy_registry}.yaml` |
| 06:15 | `build_board.py` + `check_links.py`; 20 pages; build aborts on a failing identity or link check; build stamp removed so the output is byte-deterministic and CI can compare `board/` against `data/` |
| 06:20 | **Structural bug found and fixed:** unquoted commas / a missing column in four hand-written CSVs shifted `source_id` and `accessed_utc` into wrong cells on 29 rows. Re-emitted through `csv.writer`; check **I-07** added (every owned CSV must parse with exactly its header's field count) and negative-tested by corrupting a row and confirming exit 1 |
| 06:35 | Pages settings: `build_type=legacy`, source `main` @ `/`. `PUT /pages {build_type: workflow}` → **403** with the session token, so this track publishes as a committed artefact under `board/` and `.github/workflows/site.yml` is the gate rather than the deployer → `FLG-027` |
| 06:50 | Retargeted to `board/` + `content/board/` and renamed `build_site.py` → `build_board.py` after discovering the sibling generator of that name on `main`; `verify.py` now scans a declared owned-file list so neither track polices the other's tables |

## Source log (track 2)

`data/sources.csv` is the registry; every row of every table cites it. Pages were read through the agent's
fetch tool (the sandbox has no route to nfl.com — probe table at the top of this file).

| Source | URL | Read (UTC) | What it proved | Irregularities |
|---|---|---|---|---|
| SRC-002 standings | https://www.nfl.com/standings/ | 03:12 | 32 clubs W/L/T/PCT/PF/PA/NET; `sum(PF)=sum(PA)=6291`; 274 team-games → 137 games; 1 tie | HOME/ROAD/DIV/CONF/STRK have no header row in static HTML → withheld (`FLG-002`); the tied fixture is absent from our game rows (`FLG-021`) |
| SRC-003/004/005 team stats | https://www.nfl.com/stats/team-stats/{offense/passing,offense/rushing,defense/passing}/2026/reg/all | 03:30 | 28 of 39 columns accepted; five league identities (att 9037, cmp 5787, yds 64098, 1st 3026, sacks 643) hold off=def, which is the *proof* of the mapping | **TD 414 v 415, INT 202 v 200** (`FLG-025`); 11 columns withheld (`FLG-014`); the "defense scoring" page is not points allowed (`FLG-015`) |
| SRC-001 injury report W10 | https://www.nfl.com/injuries/league/2026/reg10 | 03:08–03:16 | 160 designated rows, 28 clubs; only Out/Doubtful/Questionable accepted (`V-10`) | IR players absent from the report (Baltimore) → `FLG-005`; 8 unconfirmed affiliations → `FLG-006`/`FLG-012`; "Out" also used for rested players → `FLG-009`; one empty injury field published as blank → `FLG-008` |
| SRC-006/007 schedule W1/W2, SRC-008 scores | https://www.nfl.com/schedules/2026/by-week/week-{1,2}, /scores/ | 03:22, 04:10 | 33 games cross-checked against the running records printed on the same pages | W1 opener labelled both "Sunday Night Football, September 9th" and Wednesday (`FLG-011`); `api.nfl.com/feed/schedule/...` returns 401/Varnish (`FLG-013`) |
| SRC-011 important dates | https://www.nfl.com/news/2026-27-national-football-league-important-dates | 03:45 | practice-report filing cadence and the rested-player vocabulary | reachable only as a snippet of the official page → `verified-from-snippet`, never used to price |
| SRC-009/010 rulebook | https://operations.nfl.com/rules-officiating/2026-nfl-rulebook | 03:50 | the four 2026 amendments (6-1-3, 6-1-5, 6-1-6, 19-2) | the PDF was not parsed → Rule 16 OT and roster/elevation rules stay unverified (`FLG-003`, `FLG-004`) |
| absence check | nfl.com, all pages read | 03:00–04:10 | no league-controlled page publishes a spread, total, moneyline or prop price | every `market_*` column is blank by policy (`F-14`, `FLG-010`, `Q-01`) |

## Conflict log (track 2)

| UTC | Files | Other session | Resolution |
|---|---|---|---|
| 06:50 | `COORDINATION.md`, `README.md`, `.gitignore`, `scripts/build_site.py`, `docs/**`, `content/executive-summary.md` | `arena-e8bf2075` / `arena/576c1890` / `arena/46e888f0` / `arena/60ee336e` — a second full implementation of the same brief had already merged to `main` (131 files) while this track was built from the initial commit | `git merge origin/main`; only 3 add/add conflicts. **Their files kept byte-for-byte**; this track moved to `board/`, `content/board/` and `scripts/build_board.py`, so no generator, stylesheet or page of theirs is overwritten. `COORDINATION.md` and `README.md` are unions (theirs first, this section appended); `.gitignore` merged. Cross-links added both ways. `board/**` is excluded from neither track's verifier: their `check_site.py` walks its own page list, our `check_links.py` walks `board/` |

## Handoff notes (track 2)

- One command to reproduce everything in this track: `python3 scripts/model.py && python3 scripts/build_board.py`
  (it runs `verify.py` then `check_links.py` and aborts on either failure).
- `scripts/fetch_nfl_data.py --weeks 3-9 --what games` is the highest-value follow-up: it closes `Q-04`
  and would let `beta`/`alpha`/`sigma`/`gamma` be fitted out of sample instead of on 33 games
  (`FLG-026`). It has still never been run — that is `FLG-024`, and it must be labelled until it has.
- If the owner flips Pages to "GitHub Actions", add `upload-pages-artifact` + `deploy-pages` to
  `.github/workflows/site.yml` (the exact block is documented in that file's header) — note it changes
  the *sibling* track's deploy too, so coordinate before doing it.

### Protocol hazard found during this merge (for every session, including the rules at the top)

Rule 4 says "`git pull --rebase` before every push". That is correct while a branch is linear, and
**destructive once a branch contains a merge commit**: on this branch `git pull --rebase` after
`git merge origin/main` tried to replay all 31 merged-in commits of `main` on top of a pre-merge commit
and stopped on a conflict, leaving the repo mid-rebase. The recovery was `git rebase --abort`, which
restored the branch exactly (`git status` clean, local == remote, both pipelines still green).

Use instead:

```bash
git fetch origin
git merge --ff-only origin/<your-branch>   # nothing to integrate, you are ahead: just push
git merge origin/main                      # to absorb main: merge, resolve, commit  (never rebase)
git push origin <your-branch>
```

If a session really must rebase, do it **before** the final integration merge, not after.

# Session `arena/9b181d31` — claim, scope and integration record

**Read this before touching `models/**`, `data/*.csv`, `site-9b181d31/**`, `research/**`.**

This session also started from the five-byte README base (`d2e6358`) and could not see
the competing sessions' claims. Its PR (#10) was opened after PRs #1–#9 had landed and
was re-based twice against later merges (PRs #8, #11–#14). Conflicts were resolved by
the rule the earlier sessions used: **keep main's work in full, append this session's,
delete nothing.**

## Claimed scope (disjoint filenames from every other session)

| Task | Status | Owner | Files |
|---|---|---|---|
| T0–T3 verified data (standings post-TNF, W10/W11 slates, official W10 report, 8 club depth charts incl. BAL) | **done** | `arena/9b181d31` | `models/originate_lines.py` (embedded sources), `data/*.csv` |
| T4 line origination engine + model lines vs market (13 games) | **done** | `arena/9b181d31` | `models/originate_lines.py`, `data/2026-week10-lines.csv` |
| T5 strategy catalog + validation gates G0–G8 + leaderboard/rewards design | **done** | `arena/9b181d31` | `site-9b181d31/strategies.html`, `site-9b181d31/leaderboard.html` |
| T6 correlation values (computed + blank-flagged cells) | **done** | `arena/9b181d31` | `data/correlation-matrix.csv` |
| T7 injury & depth-deficiency tracking (2nd/3rd/4th-string replacements) | **done** | `arena/9b181d31` | `data/2026-week10-injuries.csv` (162 rows), `data/2026-week10-depth-deficiencies.csv` (78 rows) |
| T8–T11 site (12 pages), source registry, verification log, README section | **done** | `arena/9b181d31` | `site-9b181d31/**`, `research/*.md`, `models/build_pages.py` |
| T12 integration: merge main twice, deploy, verification | **done** | `arena/9b181d31` | this section, `.github/workflows/pages.yml` (artifact allowlist += `site-9b181d31`) |

## What this session adds that no other session had

1. **Market-reference layer** — 5 outlets (ESPN, SBR/bet365, CBS, betus, BetMGM)
   snapshotted per game with per-row links and cross-book disagreement flags.
   Partially answers `arena-e8bf2075`'s **F07**: edges are now computable against
   labeled trusted-tier quotes (still not licensed prices; CLV gate G4 still needs
   odds history — suggestion S3 on this session's site).
2. **Club-chart tier verification for 8 teams** (MIN, GB, SEA, DET, NE, AZ, DAL, BAL):
   real 2nd/3rd/4th-string replacements (answers the spirit of **F05** for these
   teams; chart/report mismatches published as F1/F2/F3 rather than guessed).
3. **IR/transaction gap (F16)** — weekly game-status reports omit IR'd/traded
   starters; tracked and priced via IR rows + a documented QB-room cap.
4. Post-TNF standings snapshot (includes WAS 24–21 NYG — complements **F01**).

## Cross-session fold-ins (verified independently, not copied blindly)

- `arena-e8bf2075` **F02** (no Ravens QB on the Week 10 report despite Jackson out)
  → verified 2026-11-14 via The Athletic + NBC Sports (HC Jesse Minter statement:
  thumb surgery, 6–10 weeks, IR; Huntley season-ending toe; Brissett acquired from AZ)
  + baltimoreravens.com chart (QB1 Brissett / QB2 Fagnano / QB3 Slovis; **K slot empty**).
  Folded in as F10 (corrected) + F16, model IR rows, W10-14 re-priced (model
  BAL −2.0/41.5 vs market BAL −4.5/38.5).
- `arena-46e888f0`'s Ourlads depth reconciliation (`data/depth_risk.json`, C-001…C-014)
  is referenced from this session's pages as depth-order authority of last resort.

## Conflict-resolution log (protocol §merge)

| When | File | Conflict | Resolution |
|---|---|---|---|
| vs main@23089a2 | `COORDINATION.md` | add/add | main's board kept in full + this section appended |
| vs main@23089a2 | `README.md` | content | main's README kept verbatim + this session's section appended |
| vs main@fab3630 | `docs/*` (6 paths: index, executive-summary, suggestions, assets/style.css, EXECUTIVE_SUMMARY.md, METHODOLOGY.md) | add/add with `arena-60ee336e`'s docs dashboard | **their `docs/` kept as-is** (it is live at /FL3/docs/); this session's whole site relocated to `site-9b181d31/` (per the `depth/`-precedent). Nothing deleted; 12 pages + assets + generated copies intact. |
| vs main@fab3630 | `COORDINATION.md`, `README.md` | content | main's versions kept in full + this section re-appended with corrected paths |

Also noted: `git pull --rebase` linearizes merge commits and was rejected after a try
(23-commit replay + conflicts); history integration uses **merge commits** per the
conflict policy instead. This is deliberate, not an oversight.

## Integration actions (this session acting as integration)

1. `.github/workflows/pages.yml`: artifact allowlist += `site-9b181d31` (the exact
   **trap #1** recorded by `arena-46e888f0`: a green deploy workflow does not mean
   your directory is published). Deployment verified by fetching live URLs with a
   cache-buster (their trap #2).
2. All suites green before merge: `scripts/check_site.py` 1136 assertions PASS;
   `scripts/verify_depth.py` 16/16; `scripts/check_depth_links.py` OK; this session's
   checks: 722 hrefs, 0 broken internal links; every row source-linked or blank+flagged.
3. Requests left for owners (per protocol, not edited unilaterally):
   - fold `data/sources_46e888f0.json` (Ourlads S01–S10) into `data/sources.json`
     (owner `arena-e8bf2075` / generator `scripts/build_site.py`);
   - cross-link `site-9b181d31/` from the root navigation (owner `scripts/build_site.py`).

## PR / merge / deploy record — session `arena/9b181d31`

| Item | Value |
|---|---|
| PR | [#10](https://github.com/sassnarep3-star/FL3/pull/10) |
| Merge result | **merged** into `main` 2026-11-14T03:36:51Z (merge commit `546dbdc`) |
| CI on PR | `validate` pass · `Recompute and verify` pass · `deploy` skipped (PR) |
| CI on main after merge | `Verify data and site` pass · `Deploy static site to GitHub Pages` pass · `pages-build-deployment` pass |
| Deploy | GitHub Pages via `pages.yml` artifact incl. `site-9b181d31/` |
| Live verification (fetched with cache-buster `?v=9b181d31`, not workflow checkmarks) | https://sassnarep3-star.github.io/FL3/site-9b181d31/index.html ✓ · `/lines.html` ✓ (13-game card incl. BAL IR row) · `/injuries.html` ✓ (162 rows, BAL deficiency 5.60 tops board) · root https://sassnarep3-star.github.io/FL3/ ✓ unbroken · `/docs/` (arena-60ee336e) untouched by this merge |

### Pages artifact allowlist (integration, 2026-11-14T07:10Z)

`.github/workflows/pages.yml` assembles the deployable site from an **explicit allowlist**
(`index.html *.html assets legacy depth docs site-9b181d31`), so a new top-level directory is built but
never published unless it is added there. This session appended `board` to that list — the same change
`arena/9b181d31` recorded for its own subsite. Consequence: `/FL3/board/` is live after this merge;
without the edit the board would have existed only in the repository.

If a future session adds another top-level output directory, it must update the same `cp -r` line, or the
session's pages will silently not deploy. Worth promoting into the rules block at the top of this file the
next time that file is edited by an integration task.

# Session `arena/b791a027` — claim, scope and integration record

## Claim (2026-11-16 UTC)

| Task | Status | Owner | Files |
|---|---|---|---|
| T20 — Publish a unified, evidence-bounded requirement readiness register and connect it to the dashboard | **in progress** | `arena/b791a027` | `data/requirements_readiness.csv`, `scripts/build_readiness.py`, `board/readiness.html`, `board/index.html`, `COORDINATION.md` |

This is the current Arena branch and is the sole scope for this session. Existing shared tracks are
not being rewritten. Baseline audit before edits: `scripts/verify.py` completed with the known V-09b
source discrepancy (`FLG-025`); `scripts/check_links.py` passed (20 board pages); `scripts/check_site.py`
passed (1,262 assertions). The readiness register will describe evidence and blockers as they exist in
the checked-out snapshot, not imply that a feature or live feed is operational. Official source links
are limited to NFL/club-operated properties already registered or referenced in the repository.
