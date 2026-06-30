# Rookie Outcome Handoff Contract

`historical_rookie_entry_status_v1.csv` is review-only.

- `model_use_allowed=false`
- `training_allowed=false`
- Rookie Outcome may use it only to evaluate coverage and propose gates.
- Rookie Outcome may not train on UDFAs until a confirmed-UDFA source policy is approved.
- Drafted-only models must remain explicitly drafted-only.
- `unknown`, `name_collision`, and `wrong_universe` rows must be blocked from training.
- `likely_udfa_needs_review` and `free_agent_rookie_needs_review` rows may not be treated as clean
  UDFAs.
- Outcome V2 labels, fantasy outcomes, games, starts, AV, career length, and awards may not be used
  to prove entry status.

This contract does not authorize app wiring, ranking changes, source-truth promotion, or model
tuning.
