# Model parameter register

`models/line_model.yaml`, rendered. This page exists so that the **unset** parameters are as visible as
the set ones: the register is the contract that stops a guessed constant from entering a price, and a
contract nobody can read is not a control.

Rules the register enforces:

- a parameter holds a value only when its `evidence` names a row in `data/` that passed
  [verification](verification.html);
- `null` + `blocked_by` is a legitimate, expected state - it means "we refuse to assume this";
- a parameter marked `provisional-in-sample` may appear in a published table but may not set a stake
  (`may_set_stake: false`).

## Blocked parameters and what unblocks them

| Parameter | Why it is null | Unblock |
|---|---|---|
| `strength.blending`, `strength.schedule_adjustment` | needs per-game opponents for Weeks 3-9 | [Q-04](questions.html) |
| `conversion.shrinkage_prior` | regression-to-the-mean prior needs multiple seasons | [Q-04](questions.html) |
| `availability.replacement_identification` | the report publishes designations, not lineups; no league-wide depth chart exists | [Q-02](questions.html), [FLG-017](flagged.html) |
| `availability.positional_weights` (QB, line, edge, CB, WR1, RB1) | must be *measured* from verified games, never assumed | [Q-02](questions.html), [Q-08](questions.html) |
| `markets.vig_model`, `markets.opening_close_sources` | no official source publishes odds; a licence decision is pending | [Q-01](questions.html), [FLG-010](flagged.html) |
| `availability.designation_semantics` conversions | the league publishes no Out/Doubtful/Questionable → probability table | [Q-09 / FLG-018](flagged.html) |

Every number that *is* set here is set by `scripts/model.py` from verified rows - none of them was typed
in. The fitted ones (`beta`, `alpha`, `sigma_margin`, `gamma`, `pyth_exponent`) carry `n` and standard
errors in [data/model_calibration.csv](data/model_calibration.csv), and their known weaknesses are on
[Model](model.html) and [FLG-026](flagged.html).
