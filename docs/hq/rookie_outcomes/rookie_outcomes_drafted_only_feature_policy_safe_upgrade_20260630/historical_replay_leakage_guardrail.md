# Historical Replay Leakage Guardrail

The existing historical replay service must preserve its leakage controls:

- ranking inputs are pre-NFL/as-of-draft only;
- outcome joins happen after ranking;
- changing an outcome file must not change ranking order;
- `future_nfl_stats_used=false`;
- top-5/top-10/top-20 hit rates are review/evaluation only;
- no current rookie probabilities are produced.

Existing tests already exercise these controls in `tests/test_historical_rookie_replay_service.py`, including ranking-order invariance when outcome rows change and feature receipts excluding outcome fields.

This lane adds policy tests to ensure the new Gate E feature manifest keeps Outcome V2 labels, player_stats, snap counts, injuries, roster status, and depth-chart rank out of model/training use.
