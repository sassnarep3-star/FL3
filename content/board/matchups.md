# Week 10 matchup deficiency matrix

The full interactive matrix lives on the sibling dashboard:
**[Matchup matrix at the site root](../matchups.html)** — 168 rows (14 games × 2 directions ×
6 declared units), first through fourth strings on both sides, with replacement **depth** counted
only where the official Week 10 report rules a first-string player **Out**.

## Sources and authority

* Availability: the [official NFL Week 10 injury report](https://www.nfl.com/injuries/league/2026/reg10)
  (SRC-001), captured 2026-11-14. A player absent from the report is *no designation published*,
  never "healthy".
* Order: the targeted Ourlads capture `data/depth_charts_2026-11-16.json` (14 clubs, fetched
  2026-11-16) for those clubs, and the 2026-11-14 transcription `data/depth_risk.json` for the other
  14 playing clubs. Ourlads is a third-party scouting service; it supplies order only, never
  availability. Where a chart marker disagrees with the official report, the report wins and the
  disagreement is published on the root page.
* The declared slot map (LWR/RWR/SWR → WR, LDE/RDE/RUSH → DE, …) is a display convention printed on
  the root page. The league publishes no depth rank; nothing here invents one.

## State: PARTIAL (readiness R036)

* 102 of 168 rows have both sides' order evidence; the other 66 are explicit `n/a` rows naming the
  missing group, club and source.
* 25 rows carry a confirmed promotion (first-string ruled Out). Doubtful/Questionable first strings
  are shown but never counted as promotions.
* 8 chart-marker vs official-report conflicts are listed on the root page with both source links.
* Gate: official club-by-club depth order for all 32 clubs (R042) and the shared/empty-slot schema
  (R064/R069) are what clear the remaining `n/a` cells. Until then the matrix stays descriptive —
  it counts strings and computes no score, projection or edge.
