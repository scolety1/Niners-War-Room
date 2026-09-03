# One-command historical calibration readiness (sections 33-34)

## The command

```
python scripts/run_historical_calibration_readiness_v1.py --dataset-dir "C:\path\to\dataset"
```

Expects `<dataset-dir>/historical_replay_rows.csv` (columns =
`historical_replay_data_adapter_service.REQUIRED_PRE_DRAFT_FIELDS` +
`OUTCOME_ONLY_FIELDS` — the field contract
`HISTORICAL_REPLAY_DATA_CONTRACT_20260903.md` already specifies; this
script only adds the concrete file shape, since that doc names required
fields, not a format) and optionally `historical_picks.csv` for the
identity-completeness check. Without `--dataset-dir`, or if that file
isn't found there, the exact same pipeline runs against a deterministic
**SYNTHETIC_PIPELINE_TEST_ONLY** dataset instead — every output is
labeled, and every run (real or synthetic) writes
`docs/codex/HISTORICAL_CALIBRATION_READINESS_REPORT.json` plus a short
console summary.

## What one real run just proved (synthetic mode, this session)

`DATASET_READINESS_REPORT` reached **PASS_READY_FOR_REPLAY**, and every
downstream stage ran for real against the synthetic fixture: schema/
leakage validation, chronological split (train=[2023], test=[2024]), the
real `historical_draft_replay_engine_service` running two full snake
drafts per season (PLATFORM_ADP and GREEDY_NWR, the owner seat running
each strategy under test while every opponent seat used the market
model), `outcome_evaluation_framework_service`-style realized-production
totals per strategy, and a genuine `CHALLENGER_COMPARISON` between them.
Full output: `docs/codex/HISTORICAL_CALIBRATION_READINESS_REPORT.json`.

This is a **mechanics proof only** — the synthetic fixture was
constructed so ADP order exactly matches realized-production order by
construction (a disclosed simplification to make the pipeline
deterministic to test), so PLATFORM_ADP "beating" GREEDY_NWR in that run
is an artifact of the fixture, not a finding about anything real.

## What a real dataset gets, mechanically verified

Also exercised directly (a dedicated test, not just the synthetic path):
a real conformant 12-row CSV dataset reaches `PASS_READY_FOR_REPLAY` and
runs `PLATFORM_ADP` (real historical rows only carry `platform_adp`, no
`nwr_overall_rank` column, so `GREEDY_NWR`/`STANDARD_VBD` are correctly
omitted rather than faked). A deliberately leakage-violating row (a
projection dated after its own draft date) is correctly caught and
reported as `BLOCKED_LEAKAGE` with the run otherwise completing cleanly
(exit code 0 — a validation block is a normal, well-formed result, not a
crash).

## What is not yet wired, and exactly why

`CHAMPIONSHIP_EQUITY_CALIBRATION`, `PICK_SCORE_EVALUATION`, and
`COST_OF_WAITING_CALIBRATION` are present in every report with an
explicit `blocked_reason`: `shadow_numeric_authorities_service`'s
`team_score`/`championship_equity`/`pick_score`/`cost_of_waiting` are
real, tested functions, but they consume a `RankingResult`/`AdpSnapshot`
pool (`redraft_engine_v1_service`'s shape), not raw
`historical_replay_rows.csv` rows. Building that adapter — turning a
season's historical rows into a `RankingResult` the existing Monte Carlo
machinery can consume — is the single next task that unlocks all three
sections at once; not attempted this pass to avoid a rushed, undertested
bridge between two real but differently-shaped data models.

## Verification

5/5 new tests (`tests/test_run_historical_calibration_readiness_v1.py`):
synthetic dataset self-validates, a full synthetic run reaches
`PASS_READY_FOR_REPLAY` with every section populated, a missing dataset
directory returns an explicit `BLOCKED_NO_DATASET_FOUND`, a real
conformant CSV reaches `PASS_READY_FOR_REPLAY`, and a real CSV with a
genuine leakage violation is correctly blocked. Ruff clean.
