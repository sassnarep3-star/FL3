# Executive summary

**Read:** 2026-11-14. **Season state:** Week 10, Thursday game played, 13 Sunday games and one Monday
game still to come. **Repo state at start:** one 5-byte `README.md`, one commit, no code, no data
([FLG-001](flagged.html)).

## 1. What this project now is

A data-to-price pipeline with a review discipline attached:

`ingest → verify → derive → rate → price → signal → gate → board`, where *nothing* enters the site
that does not carry a source id, and *nothing* is priced off an unverified input.

- **19 sources registered** in [sources.csv](sources.html); 9 read this session from the league's own
  pages (standings, injury report, three team-stat pages, two schedule pages, scores page, the 2026
  rulebook page).
- **13 automated identity checks** in [verification log](verification.html); the build fails on a
  transcription error and passes with warnings on source-level noise.
- **9 data tables**, 4 model/spec files, 4 scripts, GitHub Pages deploy - all reproducible with one
  command (`python3 scripts/build_site.py`).

## 2. What the verified data already tells us

| Finding | Number | Where | So what |
|---|---|---|---|
| League scoring through Week 9 | 22.96 pts per club per game (45.92 combined) | [league facts](league-facts.html) F-13 | the total-anchoring constant, from 137 games, official |
| Games played | 137, of which 1 tie | F-11, F-12 | a **0.7% tie rate** is a real pricing term for spreads and moneylines, not a rounding error |
| Home margin, ingested sample (n=33) | **+0.09 pts**, SD 14.71 | [derived league stats](model.html) | home-field advantage is currently indistinguishable from zero on our sample - a 2-point "standard" HFA would be a fabricated input |
| Spread vs total volatility | margin SD 14.71 vs total SD 16.32 | derived | the two markets need different widths; one "sigma" for everything is wrong |
| Pass yards/game vs net points | r = 0.46 (95% CI 0.14 to 0.70) | [correlation](correlation.html) | passing volume separates good teams from bad ones - usable |
| Rush yards/game vs net points | r = 0.17 (CI -0.19 to 0.49) | correlation | rushing offence is *not* separating teams this year; that kills a family of "run game" signals |
| Same-game home pts vs away pts | r = 0.12 (CI -0.23 to 0.44) | correlation | the correlation that parlay prices depend on is **not yet measured** - sample too small |
| Availability load, Week 10 | 160 designated players; 2 clubs with a QB "Out"; 5 with 2+ OL out | [injuries](injuries.html) | the slate's biggest pricing events are visible 1 day out - which is exactly the window a model can exploit |

## 3. The uncomfortable findings (these are the useful ones)

1. **The injury report alone cannot do the job you asked for.** It lists designations, not lineups.
   It omits players on IR entirely: the Week 10 Baltimore report contains 8 rows and no game status,
   while the league's own news feed on the same page says the franchise QB is out 6-10 weeks
   ([FLG-005](flagged.html)). Any "defence is down to its 4th-string CB" logic must merge the report
   with transactions, inactive lists and club depth charts - and no league-wide depth chart exists
   ([FLG-017](flagged.html)).
2. **Stat pages on nfl.com publish numbers with no machine-readable column labels.** We could only
   publish 28 of 39 columns; the rest stayed blank because a magnitude is not a label
   ([FLG-014](flagged.html)). The columns we did publish are pinned by identities (league pass
   attempts on offense = league pass attempts on defense = 9,037, etc.), which is why the mapping is
   provable rather than plausible.
3. **The two official tables disagree with each other** about scoring events:
   `offense pass TD = 414` vs `defense TD allowed = 415`, `INT thrown = 202` vs `INT forced = 200`
   ([FLG-025](flagged.html)). Those four columns are published but marked *pricing-ineligible*.
   A model that silently used them would inherit a bug it could never see.
4. **There is no official source for odds.** No NFL-controlled page publishes a spread, total,
   moneyline or prop price ([FLG-010](flagged.html)). So every "market" column on this site is blank.
   Originating lines is now possible; *scoring* them against the market is a purchase decision.
5. **The first model we built is a good example of a bad line.** Unshrunk net-points ratings produce
   things like "JAX -24 at TEN", which is nonsense. Fitting the conversion on our 33 verified games
   even returns `beta = 1.14` - i.e. *anti*-shrinkage, and a total-model exponent pinned on the edge of
   its search grid ([FLG-026](flagged.html)). Those two facts are the clearest available evidence that
   the sample is too small to calibrate anything, which is exactly what the gates are for.
6. **A handful of Week 10 rows list players on clubs they have not been associated with before 2026**
   (Garrett on LA, Evans on SF, Marvin Harrison Jr. on HOU, Nelson on SEA, McCarthy on NYG…). Each is
   either a real 2026 transaction or a feed error; we did not assume either way and put them all in a
   queue for an affiliation audit ([FLG-006](flagged.html)).

## 4. What has to be answered before a decision

20 questions in [Questions & gaps](questions.html); **7 are blocking**: market prices (Q-01),
lineups (Q-02), IR/transactions (Q-03), game-level history (Q-04), the calibration constants
(Q-05/Q-06) and the correlation inputs (Q-07). Each one names what we have, what we lack, exactly how to obtain it, and which
decision it unblocks.

## 5. Recommended path (nothing is implemented without your approval)

| Step | Do this | Cost / risk | Buys |
|---|---|---|---|
| 1 | Approve **S-11 + S-08 + S-09**: game-level history, availability merge, affiliation audit | engineering only | turns every provisional constant into a real one |
| 2 | Approve **S-01/S-02/S-06** (site discipline already in v1) | done | auditability |
| 3 | Buy one odds feed (**Q-01/SRC-016**) | money; the only real spend | CLV, gate G-03, and therefore an honest leaderboard |
| 4 | Run the **paper tier** for 4-6 weeks under gates G-01…G-13, with **S-15/S-16/S-17/S-24** (prediction-quality scoring, sealed parameters, FDR control, anti-gaming rewards) | a season of patience | the only version of this where "skill" means something |
| 5 | Only then decide the bankroll (**Q-17, S-19, S-20**) | exposure | - |

**Do not** start by picking a signal. On this data set, no signal has yet passed a single gate, and
the first thing the pipeline is good for is killing the ideas that look best.

## 6. What is deliberately *not* here

No bet results, no ROI, no "record" of any strategy, no odds values, no weather numbers, no snap
counts, no player-level prop rates. Each of those absences is a row on
[Flagged for review](flagged.html) or a question in [Questions & gaps](questions.html), because
inventing them is the failure mode this whole repo is organised to prevent.
