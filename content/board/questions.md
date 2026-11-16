# Questions and information gaps

The brief asks for *a clear list of questions, information and answers that must be addressed before
any decision can reasonably be made, based on what we have and what we do not have*. This is that
list. It is a table rather than prose because it is a work queue: each row states what we already
have, exactly what is missing, how to get it, and which decision is waiting on it. The final two
columns are row-level provenance: `source_id` links to a registered official input where one applies;
`source_gap` states what that source does not establish, or why no official source applies. A link is a
place to verify an input, not proof that the question is answered. Open questions remain open until
the missing evidence is captured and reconciled.

**How to read the `blocking` column:** `yes` = a decision that depends on this is currently
undecidable with integrity (we would be guessing). `no` = it improves the model but does not gate the
next step.

:::table questions.csv | 20 open questions - 7 blocking; official input links or explicit source gaps | id,blocking,area,question,what_we_have,what_we_need,how_to_obtain,decision_it_unblocks,source_id,source_gap

## The seven that gate everything else

- **Q-01 market prices.** We can build a number; we cannot yet say whether it is better than the
  market's. Without opening *and* closing lines there is no CLV (gate G-03), no vig realism
  (G-06), and a leaderboard that ranks guesses. This is the only item on the list that is primarily a
  purchase.
- **Q-02 lineups.** "Which backup is playing" is the heart of your brief. The league publishes a
  *designation*, not a *lineup* ([FLG-017](flagged.html)), so every starter-quality adjustment in
  [models/line_model.yaml](model.html) is deliberately `value: null`.
- **Q-03 IR / transactions.** A weekly report does not establish reserve status or a dated roster
  history. The separate [verified-source track](../verified/injuries.html) has point-in-time report and
  roster checks, but this board still has no daily placement/activation series or general IR-duration
  rule. Treat individual examples as unresolved until their dated transaction chain is captured. Any
  absence from the report remains unknown, never "healthy".
- **Q-04 game-level history.** The board model still consumes 33 game rows, but a separate official-source
  verified corpus now contains 148 final games through Week 10 and reconciles 160 club W/L/T/PF/PA figures
  to standings. That corpus is not yet integrated into this board model, and no prior-season results corpus
  is present. Every fitted game distribution remains provisional; see the in-sample `beta = 1.14`
  anomaly in [FLG-026](flagged.html). Future 2026 games are not yet results and must not be backfilled.
- **Q-05/Q-06 calibration.** The legacy in-sample fit on `n = 33` gives `beta = 1.14`,
  `sigma_margin = 11.92` points and `alpha = −0.82` points (SE 2.09). Separately, the verified track's
  100-game walk-forward evaluation reports spread RMSE 12.58 versus 13.31 for a zero-margin baseline
  (gain +0.055, 95% CI −0.020 to +0.130) and Brier skill +0.069 versus a coin (95% CI −0.086 to +0.229).
  Both intervals include no improvement; the test is not a sportsbook comparison and does not validate
  the legacy fit parameters. A stable multi-season calibration and schedule adjustment remain open.
- **Q-07 correlation inputs.** The board's eight provisional coefficients use two game-level pairs
  (`n = 33`) and six team-level pairs (`n = 32`), each with an interval on the
  [Correlation](correlation.html) page. The separate 148-game corpus has not yet been used to recompute
  these outputs. Player-prop pairs and directly validated joint settlement probabilities remain
  unavailable, so G-07 still blocks combo ranking.

## Questions we should not ask yet

These look like questions but are actually *consequences* of the above, and asking them now invites a
made-up answer:

- "Which signal is best?" - no signal has a settled sample (G-01).
- "Is our model sharper than the market?" - undefined until Q-01.
- "How much should we bet?" - Kelly on an unmeasured edge is just a faster way to be wrong (Q-17).
- "Are parlays +EV here?" - needs the correlation measurements in [Correlation](correlation.html),
  which need Q-04 and Q-07.

## Recommended next steps and owner-dependent gates

1. Continue only with official, permitted schedule/results and availability capture. Keep each read
   timestamped and immutable; distinguish the separate 148-game verified corpus from the board model's
   33-row input, integrate through a checked change, and do not use unplayed games as outcomes.
2. Before any CLV/backtest publication, establish a licensed price-data source, permitted retention,
   and settlement keys. Until that exists, leave market values blank and keep the price gate blocked.
3. Keep all strategies in shadow/paper status. A 100-game walk-forward evaluation exists in the separate
   verified track, but its uncertainty includes no improvement and it is not a market comparison. No
   stake, reward or live-demotion policy is inferred from a model result.
4. Treat legal scope, price licensing, infrastructure credentials and bankroll authority as explicit
   owner-dependent questions. The site records the missing evidence and best next path; it cannot
   supply contracts, legal approval or account access on the owner's behalf.
5. Compare implementation options on the [Suggestions](suggestions.html) page before changing the
   system. Record a choice and rationale there; only then should a path that depends on that choice be
   implemented.
