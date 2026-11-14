# Questions and information gaps

The brief asks for *a clear list of questions, information and answers that must be addressed before
any decision can reasonably be made, based on what we have and what we do not have*. This is that
list. It is a table rather than prose because it is a work queue: each row states what we already
have, exactly what is missing, how to get it, and which decision is waiting on it.

**How to read the `blocking` column:** `yes` = a decision that depends on this is currently
undecidable with integrity (we would be guessing). `no` = it improves the model but does not gate the
next step.

:::table questions.csv | 20 open questions - 7 blocking | id,blocking,area,question,what_we_have,what_we_need,how_to_obtain,decision_it_unblocks

## The seven that gate everything else

- **Q-01 market prices.** We can build a number; we cannot yet say whether it is better than the
  market's. Without opening *and* closing lines there is no CLV (gate G-03), no vig realism
  (G-06), and a leaderboard that ranks guesses. This is the only item on the list that is primarily a
  purchase.
- **Q-02 lineups.** "Which backup is playing" is the heart of your brief. The league publishes a
  *designation*, not a *lineup* ([FLG-017](flagged.html)), so every starter-quality adjustment in
  [models/line_model.yaml](model.html) is deliberately `value: null`.
- **Q-03 IR / transactions.** A club can be missing its best player and show a nearly empty report
  (Baltimore, Week 10 - [FLG-005](flagged.html)). Any deficiency count that reads only the report is
  systematically wrong in the direction of "everyone is healthy".
- **Q-04 game-level history.** 33 of 137 verified 2026 games are in the repo, and no prior season
  is. Every distribution (margin SD, home advantage, push rate, correlation) is therefore labelled
  provisional - see the fitted `beta = 1.14` anomaly in [FLG-026](flagged.html), which is what a
  too-small sample looks like when you refuse to hide it.
- **Q-05/Q-06 calibration.** The two constants that turn a rating gap into a spread, plus home-field
  value. Right now: `sigma_margin` 11.92 pts (in-sample), `alpha` −0.82 pts (in-sample, not
  distinguishable from 0), and no schedule adjustment at all.
- **Q-07 correlation inputs.** Every parlay and prop-combo price depends on a joint distribution, and
  the only correlation we can currently measure with an interval is same-game home-vs-away points at
  r = 0.12 (CI −0.23 to +0.44) — i.e. uninformative. Until this is settled, gate G-07 cannot be
  evaluated and no multi-leg strategy can be promoted ([Correlation](correlation.html)).

## Questions we should not ask yet

These look like questions but are actually *consequences* of the above, and asking them now invites a
made-up answer:

- "Which signal is best?" - no signal has a settled sample (G-01).
- "Is our model sharper than the market?" - undefined until Q-01.
- "How much should we bet?" - Kelly on an unmeasured edge is just a faster way to be wrong (Q-17).
- "Are parlays +EV here?" - needs the correlation measurements in [Correlation](correlation.html),
  which need Q-04 and Q-07.

## Suggested way to answer them without me

1. Approve the data tasks (S-08, S-09, S-11) and let `scripts/fetch_nfl_data.py` run on a host that
   can reach nfl.com - it closes Q-04 in one afternoon and needs no licence.
2. Decide the odds vendor (Q-01). Nothing else on this page unblocks G-03, and G-03 is the gate that
   separates "we have a model" from "we have an edge".
3. Answer Q-17 (mandate) in writing - unit size, slate cap, kill-switch owner. Two hours of your time
   that the entire staking/reward design depends on.
4. Everything else in this table is a research task with a named source; it can be worked in parallel
   by session, one row at a time, marking each row `answered` here with the link.
