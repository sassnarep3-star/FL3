# Executive summary — 2026-11-16

**Written:** 2026-11-16T01:50Z. **Data snapshot on the site:** 2026-11-14. **Current season state:**
Week 10 is 12 of 14 games complete. PIT at CIN (Sunday Night Football) kicked off at 8:20 PM ET on
2026-11-15, which is **2026-11-16T01:20Z**, and was in progress at the time of writing. LAC at BAL
(Monday Night Football) is scheduled for 8:15 PM ET on 2026-11-16, which is **2026-11-17T01:15Z**.

This summary supersedes the 2026-11-14 one, which was accurate for its moment. Where they differ,
the difference is a fact that changed, not a fact that was wrong.

---

## The one-paragraph version

The repository holds a real, source-linked NFL dataset and a working origination engine, and as of
today it can be **scored for the first time**. The score is: **not established**. Over 11
pre-kickoff forecasts the model beat a coin flip on the Brier score (+0.194) with an interval that
includes zero ([-0.018, +0.385]), **lost to the far stronger benchmark of always quoting the sample's
own base rate** (-0.016), and won 1.4 more games than its own probabilities said it should. Its
opinions are also **four times too narrow** to beat a market. Separately, and more seriously, the
repository was publishing **three different numbers called "our line"** for the same fixtures, on two
opposite sign conventions, and the site's data snapshot **predated the results of the games it
prices**. Both of those are now measured and published rather than inherited.

---

## 1. What was done this session, and how it was verified

| # | Work | Verification |
|---|---|---|
| 1 | **Official re-capture, 2026-11-16.** Injury report (347 rows / 28 clubs), Week 10 results (14 fixtures, 12 settled), league standings (32 clubs). | Every figure transcribed directly off the NFL page and stored with its UTC clock time, per-row source URL and a hash. See the provenance caveat below. |
| 2 | **Verified results feed** (`board/results.html`). | 12 settled scores, each row linking its own nfl.com game page. 2 games declared *not final* and left blank. |
| 3 | **First prospective scoring** (`board/luck.html`). | Frozen forecast (`model_run_date 2026-11-14`), Thursday game excluded as final-before-forecast, n=11, both benchmarks, bootstrap interval, dispersion, luck gap. |
| 4 | **Line provenance reconciliation** (`board/line-provenance.html`). | Three files, one axis, 14 fixtures, per-game and aggregate error against settled results. |
| 5 | **Depth evidence** (`board/depth-evidence.html`). | 3 clubs transcribed with cell structure intact, 176 player cells, 6 structural failure modes, 8 starter-out joins. |
| 6 | **Staleness measurement** (`board/data-freshness.html`). | 22/32 clubs changed in 2 days; injury rows 160→347; a row-by-row diff of two independent transcriptions of the same URL. |
| 7 | **Registers updated.** 73 requirements, 24 flags (F01–F24), 42 flag rows (FLG-001–FLG-042), 20 sources. | `verify.py` and `check_site.py` (1,668 assertions) and `check_links.py` (26 pages) all pass. |

**A provenance caveat that must be repeated wherever these captures are cited.** The hash in
`data/captures/manifest.json` covers the *transcription*, not NFL.com's raw HTTP bytes, because the
agent's fetch tool returns extracted text rather than bytes. It makes the capture tamper-evident
and re-checkable row by row; it is not a hash of the source document and must not be described as
one.

---

## 2. The four findings that change decisions

### 2.1 The model is not yet distinguishable from luck, and it is worse than a trivial benchmark

| Test | Result | Reading |
|---|---|---|
| Brier skill vs coin flip | **+0.194**, 95% CI **[-0.018, +0.385]** | interval includes zero |
| Brier skill vs sample base rate | **-0.016** | **worse** than always quoting "27% home" |
| Picks won vs expected | 8 / 11 vs **6.61** expected | **+1.39 wins of luck** |
| Dispersion ratio (model sd ÷ realised sd) | **0.24** | opinions ~4× too narrow |

This is not a verdict that the model is bad. It is a verdict that **11 games cannot say**, and the
honest presentation of "we cannot say" is the interval, not a headline. What *is* actionable is the
dispersion ratio: a forecast that barely varies across games cannot produce an edge over a market
no matter how good its average is, and no amount of re-centring fixes that.

### 2.2 Three files publish different numbers called "our line"

`data/lines_week10.json` (rendered on the public root site), `data/lines_origination.csv` (rendered
on the board) and `data/2026-week10-lines.csv` (which no generator writes) each publish a Week 10
line. They use **two opposite sign conventions** and disagree by **6.72 points on average on the
same fixtures** — more than either disagrees with reality. On WAS-NYG, decided by 3 points, one file
was ~7 points wrong one way and another ~6.5 points wrong the other way.

Nothing was rewritten. Choosing a canonical series is a decision with gate consequences and belongs
to the owner, not to a session that also wrote the comparison. The reconciliation is published so
the decision can be made on evidence.

### 2.3 The snapshot predates the results it prices

Pages are stamped 2026-11-14; the Sunday slate was played 2026-11-15. Re-capture shows **22 of 32
clubs changed** and the injury report going from **160 rows / 26 clubs to 347 rows / 28 clubs**.

The sharpest form of this is a controlled comparison the repository accidentally made possible: two
independent transcriptions of the *same official URL*, 48 hours apart. They disagree substantively
on 16 rows. **LAC carried a game status on 0 of 19 rows on 2026-11-14 and 9 of 19 on 2026-11-16** —
correct both times, because a Monday club has not had its final practice yet. The brief's demand to
*treat the injury report as a timestamped series, not a weekly snapshot* is therefore not
housekeeping. Pricing from a frozen read uses **less** information than was available and presents it
as the state of the world.

### 2.4 Depth charts cannot be read as "column 1 = the starter"

Confirmed against the live club pages: Houston publishes its chart as a raster image; Green Bay
prepends jersey numbers; Seattle puts **two players in one cell**; Baltimore publishes **no kicker**;
Green Bay has **one player at rank 1 of both safety spots**; Baltimore has **one backup listed at
rank 2 of two positions**. Three of these produce a fabricated starter, a doubled player, or a
dropped player under a naive parse.

What the data *does* support is the feature the brief actually asked for: **8 rank-1 players were
also Out or Doubtful on the official report, each with the club's named replacement and that
replacement's own designation** — replacement *depth*, not merely replacement *presence*.

---

## 3. Three claims in the brief that the official pages do not support

Checked against the live pages on 2026-11-16, and recorded as **refuted** rather than "fixed":

| Claim | Reality |
|---|---|
| Three Lions game statuses are blank | Kerby Joseph, Cade Mays and D.J. Reed all read **Out** — in the checked-in file *and* on the live page. |
| Seattle and Cincinnati shown injury-free while listing 15 and 4 players | The live page has **SEA 15 rows / CIN 9 rows**; the checked-in file has SEA 4 / CIN 4. Neither shows them injury-free; the *counts* differ by read. |
| Baltimore still lists Lamar Jackson and Tyler Huntley at QB | The chart reads **Brissett / Fagnano / Slovis**. Neither appears. |

This matters because acting on any of them would have introduced an error into data that was
already right. It is also why the standing rule is *verify, then record the refutation* — a review
queue that only ever confirms is not a review queue.

---

## 4. What is still missing, in the order it blocks things

| Blocker | Blocks | Why it cannot be worked around |
|---|---|---|
| **No licensed market price** (Q-01 / FLG-010) | ROI, closing-line value, any "edge" figure, the top two reward tiers | Every one of those is a *comparison against a price*. The two market quotes in the repo are attributed to ESPN and Sportsbook Review — third-party media, not a licensed feed. Inventing one is the single failure mode this project exists to prevent. |
| **One scored week** (238 games short of a corpus) | Strategy promotion, demotion, rewards, ablations | 11 games with an interval spanning zero clears no gate, and cannot distinguish skill from variance at any honest confidence. |
| **No dated depth archive** | Point-in-time replacement features, the deficiency matrix | 2 of 3 sampled club charts publish **no effective date at all**, so they cannot be proved pre-kickoff. |
| **No inactive list or snap counts** | Confirming a replacement rather than suspecting one; starter/backup split | The injury report publishes *designations*, not participation. A backup's entry is inferred from depth alone today. |
| **No automated capture cadence** | Everything in section 2.3 | The fix is scheduled capture with retained hashes, not a bigger one-off read. |

---

## 5. What to decide first

1. **Name a canonical line series** and a single sign convention. Until then two pages of this site
   give different answers to "what did we think".
2. **Set the price-data policy.** Either license a feed or accept, in writing, that no ROI, CLV or
   edge number will be published. Both are defensible; publishing an unlicensed comparison is not.
3. **Decide the depth-source route** for Houston (and any other image-only club): authorised feed, or
   publish the field as unknown. Never transcribe by eye.
4. **Accept or reject the dispersion finding** as the top modelling priority. It is the only finding
   here that no amount of additional data collection fixes by itself.

---

## 6. Where everything lives

| Page | What it answers |
|---|---|
| [Results feed](results.html) | What actually happened, with a link per game |
| [Removal of luck](luck.html) | Is the model skilled, or lucky? |
| [Line provenance](line-provenance.html) | Which number is "our line"? |
| [Depth evidence](depth-evidence.html) | Who replaced whom, and what the charts really publish |
| [Data freshness](data-freshness.html) | How stale is everything, measured |
| [Requirement readiness](readiness.html) | 73 requirements, one row each, with the gate and the clearing number |
| [Flagged for review](flagged.html) | Every unverified item and every conflict, with its source |

**Verification state:** `scripts/verify.py` passes with one known non-blocking source discrepancy
(V-09b: pass TD 414 vs 415 allowed — see FLG-042); `scripts/check_site.py` passes 1,668 assertions;
`scripts/check_links.py` passes 26 pages with no orphans. All five new dataset generators are
deterministic and re-runnable.
