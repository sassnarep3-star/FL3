# research/sources.md — source & fetch log (session 9b181d31, 2026-11-14)

Every factual value in `data/` and `docs/` traces to one of the fetches below.
Tool note: pages were retrieved with the session's page-fetch tool; values were
transcribed row-by-row and cross-checked (see verification-log.md).

## Tier policy (provisional, pending Q3 sign-off)
- **Official league:** nfl.com
- **Official club:** team-operated sites (vikings.com, packers.com, seahawks.com,
  detroitlions.com, patriots.com, azcardinals.com, dallascowboys.com, …)
- **Trusted market/media (never called "official"):** ESPN, CBS Sports,
  SportsbookReview (bet365), betus, USA TODAY sportsdata (BetMGM)
- **Model output:** our own computations — always badged as model output.

## Fetch log

| # | URL | Tier | Content taken | Access |
|---|-----|------|---------------|--------|
| 1 | https://www.nfl.com/standings/league/2026/REG | official league | all 32 teams: W-L-T, PF/PA, net, home/road/div/conf, streak, last-5 | 2026-11-14 |
| 2 | https://www.nfl.com/schedules/2026/by-week/week-10 | official league | 14 games + byes (CHI/DEN/PHI/TB) + TNF final WAS 24-NYG 21 + Munich note | 2026-11-14 |
| 3 | https://www.nfl.com/schedules/2026/by-week/week-11 | official league | 13 games + byes (ATL/CLE/GB/LAR/NE/SEA) + Mexico City SNF | 2026-11-14 |
| 4 | https://www.nfl.com/news/nfl-week-10-injury-report-2026-season | official league | official game-status report, all 14 games, every OUT/DOUBTFUL/QUESTIONABLE row | 2026-11-14 |
| 5 | https://www.nfl.com/news/nfl-news-roundup-latest-league-updates-from-wednesday-nov-11 | official league | depth-chart news (Beck first start, Watson start, Cousins trade, Butker kicker, Patterson BAL signing), Wednesday practice levels, transactions | 2026-11-14 |
| 6 | https://www.nfl.com/games/commanders-at-giants-2026-reg-10 | official league | TNF final score | 2026-11-14 |
| 7 | https://www.vikings.com/team/depth-chart | official club | complete tiers (QB/RB/WR/TE/OL/DL/LB/CB/S/ST) | 2026-11-14 |
| 8 | https://www.packers.com/team/depth-chart | official club | complete tiers (chart dated "Unofficial, Nov. 10, 2026") | 2026-11-14 |
| 9 | https://www.seahawks.com/team/depth-chart/ | official club | complete tiers | 2026-11-14 |
| 10 | https://www.detroitlions.com/team/depth-chart | official club | complete tiers | 2026-11-14 |
| 11 | https://www.patriots.com/team/depth-chart/ | official club | complete tiers (offense + defense) | 2026-11-14 |
| 12 | https://www.azcardinals.com/team/depth-chart | official club | complete tiers ("Official Depth Chart") | 2026-11-14 |
| 13 | https://www.dallascowboys.com/team/depth-chart | official club | complete tiers | 2026-11-14 |
| 14 | https://www.houstontexans.com/team/depth-chart | official club | **chart published as image — no table extracted** (F7) | 2026-11-14 |
| 15 | https://www.sf49ers.com/team/depth-chart | official club | **HTTP 500 on two attempts — nothing taken** (F8) | 2026-11-14 |
| 16 | https://www.espn.com/espn/betting/story/_/id/50414742/2026-nfl-week-10-schedule-odds-point-spreads-totals | trusted market | Week 10 spreads/totals/ML/FPI + opened values (one anomaly flagged F6) | 2026-11-14 |
| 17 | https://www.sportsbookreview.com/picks/nfl/week-10-odds-betting-lines-2026/ | trusted market | complete bet365 14-game table (spread/ML/total) | 2026-11-14 |
| 18 | https://cbssports.com/betting/news/week-10-nfl-betting-odds-lines-totals-spreads | trusted market | Week 10 spreads/totals (partial) | 2026-11-14 |
| 19 | https://www.betus.com.pa/sportsbook/nfl/nfl-odds-week-10/ | trusted market | Week 10 spreads/totals/ML (partial) | 2026-11-14 |
| 20 | https://sportsdata.usatoday.com/football/nfl/odds | trusted market | BetMGM spread/total snapshots | 2026-11-14 |

## Search-derived leads (web search, 2026-11-14)
- "NFL injuries Week 11 2026 official injury report" → surfaced the current NFL.com
  roundup (fetch #5) and two **stale** pages (ESPN 2001 injury report; CBS Week 11
  **2025** article). Stale pages were discarded; only fetches above were used.
- "NFL Week 10 2026 point spreads odds totals" → sources #16–#20.

## Known data gaps (recorded, not filled)
- Game-level results Weeks 1–9 (needed for SRS + outcome correlations) — suggestion S1.
- Player-level stats (prop models) — S2.
- Odds history / closing lines (CLV gate) — S3.
- Depth charts for teams other than the seven fetched (esp. HOU image, SF 500) — S5.
- Thursday/Friday practice reports + final inactives (only Wednesday snapshot taken) — F15.
