# League facts, rules and cadence

Structural facts the model is allowed to depend on, each with the official page it came from. These are
the ones that decide *when* data exists, *what a designation means*, and *what the league's own rules do
to a price* - the categories an analytics project normally hard-codes from memory.

:::table league_facts.csv | 14 facts; each row carries its verification class and the source id | id,topic,fact,value,as_of,verification_status,source_id,note

## Why these are on a site about betting lines

| Fact | Consequence for the system |
|---|---|
| **F-01** 18 regular-season weeks | sets the season denominator for every "N bets per year" calculation behind gate G-01 |
| **F-02** two 2026 internationals (East Melbourne W1, Munich NE-DET W10) | rest/travel and venue features must treat these separately - a "days of rest" model that ignores a 15,000 km trip is wrong by construction; W10's Munich game kicks off **9:30 a.m. ET**, which is why kickoff time is a stored field and not an assumption |
| **F-03** opener printed as Wednesday 2026-09-09 | the schedule page's own section header says "Sunday Night Football, September 9th" while the game line says Wednesday - published as read, flagged ([FLG-011](flagged.html)) |
| **F-04 … F-07** the 2026 rule changes (6-1-3 alignment, 6-1-5 dead-ball, 6-1-6 kicking-team encroachment, 19-2 personnel review) | each one changes a countable event; a totals model that ignores a dead-ball change is silently mis-specified, so rule changes are on the annual review calendar |
| **F-08** filing cadence (Wed/Thu/Fri 4 p.m. ET for a Sunday game; Mon/Tue/Wed for Thursday; Thu/Fri/Sat for Monday) | the fetcher is scheduled to *these* deadlines; and the three-filing "trajectory" feature only exists for Sunday games, which is the whole of [SIG-02](signals.html) |
| **F-09** rested players appear on the report | `Out` is not always medical: 5 rows this week are "Not injury related", three of them still `Out` - so a naive "count the Outs" feature counts coaches' rotation decisions as injuries |
| **F-10** standings column definitions | the only label set we accepted without a machine-readable header, because `PCT` and `NET PTS` reconcile arithmetically (`V-01`, `V-02`) |
| **F-11/F-13** 137 games played, 45.92 combined points | the denominator and the anchor: our Week-10 totals average 47.1 against this, which is how we know the *level* is right and the *dispersion* is wrong |
| **F-12** exactly 1 tied game in the standings | tie/push handling is a real pricing term; the fixture itself is not in our 33-row game table ([FLG-021](flagged.html)) |
| **F-14** the league publishes no odds | the reason every `market_*` column on [Lines](lines.html) is blank, and the reason [Q-01](questions.html) is the top blocking question |

## Verified how, exactly

`verified` = read directly from the cited official page this session. `verified-from-snippet` = the text
was seen in a search snippet *of the official page* and the page itself could not be opened here; that is
good enough to build a scheduler around and not good enough to price with. `verified-with-exception` and
`derived-verified-flagged` = read from the official source, with a conflict or gap recorded on
[Flagged for review](flagged.html).

## Rules we could NOT verify, and therefore did not encode

- **Overtime (Rule 16) mechanics for 2026.** The 2026 amendments listed above are named on the
  operations page, but the rulebook PDF itself was not parsed in this session, so the playoff-OT
  procedure that would change end-of-game pricing is recorded as [Q-09](questions.html) rather than
  modelled ([FLG-003](flagged.html)).
- **Roster rules** (53-man, practice-squad elevations, IR return windows). The practice-squad elevation
  number is *disputed between sources we are not allowed to treat as official* - 2 or 3 per week
  ([FLG-004](flagged.html)). It matters: it is the difference between "the starting RB is gone for four
  weeks" and "he comes back next Sunday". No elevation-dependent feature exists in this repo.
- **Injury-report obligation text.** The cadence above is official; the *penalty/review* machinery around
  non-compliance is only in secondary sources, so it is a question, not a fact.
