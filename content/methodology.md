# Verification methodology

How a number gets to be on this site - stated so it can be argued with, and short enough to be read.

## The rule

> Every table row carries a source. A value that cannot be confirmed from an official source is left
> blank and flagged. Nothing is inferred to fill a gap.

Three classes, and only three:

| Class | Meaning | Who may use it |
|---|---|---|
| `verified` | read directly from a source in the [registry](sources.html), with a UTC read timestamp | anything, including prices |
| `derived` / `derived-verified` | computed from verified rows by a script in this repo | anything; the computation is published with it |
| `blank` + flag | the source does not exist, is not licensed, or contradicts itself | nothing - a row that would consume it is marked not-actionable |

A fourth state exists in practice and is always labelled: `provisional` - a real value computed on a real
but too-small sample (the 33-game table). Provisional values may set a *direction of travel* in a
document; they may not set a stake.

## What "official" means here

`nfl.com` (league office pages: standings, schedule, scores, injury report, team stats, news),
`operations.nfl.com` (rulebook, including the 2026 PDF), and government sources for anything external
(e.g. NOAA/NWS for weather). Club-owned pages count as official for their own roster/depth facts.
Media, aggregators and other betting sites are recorded as `secondary` or `commercial-market` and
**never** used as the basis of a published value - they can justify a *question*, not a number.

## The identity checks (run at build time, `scripts/verify.py`)

| Check | What it proves |
|---|---|
| V-01 / V-02 | standings rows are internally consistent, including `PCT = (W+0.5T)/(W+L+T)` |
| V-03 | league-wide `sum(PF) = sum(PA)` and `sum(W) = sum(L)` - a transcription error in any of 32 rows breaks it |
| V-04 | team-games is even, and ties come in pairs |
| V-05 | every game row names two of the 32 clubs |
| V-06/07/08 | each published rate (cmp%, yds/att, 1st%) equals the recomputed rate |
| V-09a | offense totals = defense totals league-wide, which is what *proves* the column mapping on pages that publish no labels |
| V-09b | scoring/turnover totals must match too - **they currently do not** ([FLG-025](flagged.html)), so those columns are pricing-ineligible |
| V-10 | injury rows use only legal designations and known clubs |
| V-11 | rounding-boundary warnings are surfaced rather than silently tolerated |

Plus three integrity checks over the repo itself:

| Check | What it proves |
|---|---|
| I-05 | no row cites a `source_id` that is missing from `data/sources.csv` |
| I-06 / I-06b | our numbers are all present, and **no market value was invented** anywhere |
| I-07 | every `data/*.csv` row parses with exactly its header's field count |

I-07 exists because it found a real bug: four hand-written CSVs had unquoted commas (and one missing
column), which silently shifted `source_id` and `accessed_utc` into the wrong cells on 29 rows. It is
negative-tested by corrupting a row and confirming the build exits 1.

A separate link check (`scripts/check_links.py`) fails on a broken internal link, an anchor that does not
exist, or a page unreachable from `index.html`; external links are reported, never fatal - a league page
that moves is a finding for the review queue, not a reason to break a deploy.

## How the site gets published

Pages for this repo is a **legacy branch build from `main` / `docs`** - the agent token could not change
that setting (HTTP 403, [FLG-027](flagged.html)), so the committed `docs/` is what publishes.
`.github/workflows/site.yml` is therefore the *gate*: on every push and PR it re-runs `model.py`,
`stats_tables.py`, `make_leaderboard.py`, `verify.py`, `build_site.py --check` and `check_links.py`, then
fails if the regenerated `docs/`/`data/` differs from what was committed. Combined with a deterministic
build (no timestamp embedded in any page), that means **a hand-edited or stale page cannot survive on the
live site**: it fails CI at the PR stage.

## Worked example of the discipline paying for itself

The team-stat pages publish 39 numeric columns with no header row. Rather than guess from magnitudes - the
normal way a scraper "just knows" that column 6 is touchdowns - the mapping was accepted only where an
identity pins it, and then confirmed by a *league-wide* identity that only a correct mapping can satisfy:

```
sum over 32 offenses of pass attempts  =  9037  =  sum over 32 defenses of opponent pass attempts
```

Five such identities hold exactly. Two do not (TD 414 vs 415; INT 202 vs 200) and eleven columns are
withheld. That single page of the site now knows which of its numbers are load-bearing, which is more than
most dashboards of this kind can say.

## Reproducing everything

```bash
python3 scripts/verify.py        # identity checks; exit 1 blocks the publish (gate G-10)
python3 scripts/model.py         # derived metrics, calibration, ratings, priced slate
python3 scripts/stats_tables.py  # closed-form thresholds (break-even, N_min, parlay EV)
python3 scripts/make_leaderboard.py
python3 scripts/build_site.py    # renders docs/ from data/ + content/
python3 scripts/check_links.py   # internal links + registry integrity
```

No third-party packages: standard library only, so the same build runs in GitHub Actions and on a laptop.
`docs/` is generated - edit `data/` or `content/`, never the HTML.

## What is *not* verified, listed rather than hidden

- The fetchers have never been executed here: this sandbox blocks nfl.com and GitHub release assets, so
  `scripts/fetch_nfl_data.py` ships as **untested code, labelled as such**
  ([FLG-024](flagged.html)) - it is not cited as a verification step anywhere.
- 104 of 137 verified 2026 games are not in the repo ([FLG-016](flagged.html)).
- Odds, lineups, snap counts, weather, player-level rates, prior seasons: absent by design until sourced
  ([questions](questions.html)).
- Headline context (Jackson/Darnold/Willis/Nacua/Jacobs) is read from link text on the official page, not
  from the article bodies ([FLG-022](flagged.html)).
