# Current Board Recovery Rebuild Source Trace

Generated at UTC: `2026-07-09T02:30:00.828057+00:00`

## Canonical HQ

Current remote HQ head verified before lane start:

`4aced300c917d952ae08afcaf927268402423834`

New commits since the prior validation lane were inspected and were docs-only/non-runtime.

## Prior Evidence

- Original Current Board Deterministic Rebuild Fix V1: `609e830e4d4c7f9b0d6082217847fe505dc2764b`
- Current Board Rebuild Input Recovery V1: `2a8086083e0ff867735a35c6804ca7fbc63e56a5`
- Current Board Missing File Manual Recovery V1: `43758e3cf2c30a4792bb0bcd33a4c8fd8e7468f7`
- Human Manual Recovery Packet V1: `0df59e9cf26b8d74232904b8452f623d55e50eb5`
- Recovery ZIP Ingest + Dropzone Validation V1: `d9d862be39e81a02412b14e8bfb5b2a18d8909ca`

## Recovered Input Root

`C:\NWR\_manual_recovery_dropzone\current_board_rebuild_inputs_v1\z1`

Primary recovered source group used:

`recovered_from_vacation_repo`

## Logic Reused

Existing row logic from:

`src/services/model_v4_wr_qb_v2_candidate_service.py`

Functions reused:

- `_candidate_rows`
- `_component_lookup`
- `_age_lookup`
- `_write_csv`

No production formula file was edited. No model weight was changed.

## Key Hashes

- Rebuilt board hash: `263cc8aa050c4670bf5ed22701d7b04801d143480c5630b98e00dd08d2968ce4`
- Pinned final board hash: `263cc8aa050c4670bf5ed22701d7b04801d143480c5630b98e00dd08d2968ce4`
- Recovered final board hash: `263cc8aa050c4670bf5ed22701d7b04801d143480c5630b98e00dd08d2968ce4`
- Detailed field diff count: `0`
- QB age adapter rows: `28`

## Caveat

The exact original age sidecar was not recovered. The adapter was derived from recovered lifecycle receipt rows and used only inside this review artifact lane. `shadow_model_v2_metrics.csv` remains absent and is not required for this exact board-row hash rebuild.
