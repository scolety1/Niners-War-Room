# Human and External Recovery Package

## Controlling conclusion

All locally available, directly attributable NWR Git, worktree, shared-data, and
archive surfaces were exhausted without an admissible historical Model v4 receipt
chain. Do not substitute current-only files, proxy panels, name joins, market/ADP,
or reconstructed lifecycle/discipline values.

## 1. Historical checkpoint and final-score receipts

- Search patterns: `*checkpoint*review*score*.csv`, `*current_value_receipts*.csv`,
  `*model_v4*historical*score*.{csv,parquet,jsonl}`, and manifests containing both
  `position_specific_review_score` and `checkpoint_review_score`.
- Required fields: governed model identifier, code commit, player ID, target season,
  source/input as-of dates, position score, lifecycle modifier, confidence cap,
  discipline/safety output, checkpoint score, final score, schema version, input and
  output hashes.
- Likely context: the originating workstation or immutable backup used when Phase
  11G/current-value outputs were first generated; pre-June-2026 ranking export
  archives; deleted CI/artifact retention if it existed.
- Expected coverage: player-season rows across 2013-2025 and QB/RB/WR/TE; row count
  should reconcile to the 5,518-row historical panel or carry a signed completeness
  manifest explaining a strict subset.
- Human action: search external backup catalogs and artifact retention by filename
  and schema, then copy nothing into HQ until SHA-256, original timestamp, generating
  commit/command, and chain-of-custody are recorded.
- Prohibited substitute: current 2026 board/rebuild receipts or Formula Data Mart
  proxy scores.

## 2. Exact rank-assignment receipts

- Search patterns: `*rank_assignment*receipt*`, `*final_rank*historical*`,
  `*nwr_rank*asof*`, and exports pairing score, rank, tie key, and model version.
- Required fields: exact score input hash, assigned rank, scope (position/flex/overall),
  deterministic tie key, missing-score behavior, row count, season, and output hash.
- Human action: retrieve the exact exported bytes from the ranking run archive; do
  not reconstruct ranks unless the complete score population and ordering contract
  for that run are also authenticated.
- Prohibited substitute: ranks recalculated from the near-equivalent replay.

## 3. Component, lifecycle, confidence, discipline, and safety receipts

- Search patterns: `*position*component*receipt*`, `*lifecycle*receipt*`,
  `*confidence_missingness_receipts*`, `*discipline*multiplier*receipt*`,
  `*safety*overlay*receipt*`.
- Required fields: per-row inputs and outputs, component versions/weights, caps,
  missingness flags, source as-of dates, identity namespace, model/checkpoint stage,
  and immutable hash manifest.
- Known lead: current-only freezes in the formula-gauntlet context archive prove
  schemas but not historical application. Use them only to recognize expected
  structure.
- Prohibited substitute: the 5,518-row review-only cap/lifecycle panels.

## 4. Exact source/as-of manifests

- Search patterns: `*as_of_manifest*`, `*input_hash_manifest*`,
  `*point_in_time_snapshot*`, `*source_version*manifest*`.
- Required authority: all source families/versions, source and decision dates,
  hashes, schemas, identity namespace, missing-data policy, and generation command.
- Provider/source permission need: retrieve only from archives whose historical-use
  rights are already admitted; paid/current/provider payloads are not an automatic
  substitute.

## 5. Shadow Model v2, route, return, inactivity, and outcome-state receipts

- Search patterns: `*shadow_model_v2*metrics*`, `*route*yprr*tprr*asof*`,
  `*return*scoring*receipt*`, `*injury*inactivity*asof*`, and
  `*outcome_state*receipt*`.
- Known blocker: no admitted immutable historical chain appeared locally.
- External need: originating archive or source-specific historical snapshot with
  permission and exact identity/as-of metadata.
- Prohibited substitute: current depth chart, injury, roster, ADP, or name-matched data.

## Permanent-impossibility decision

If the originating machine, external backup catalogs, CI/artifact retention, and
approved source archives cannot supply these bytes, record
`PERMANENT_EXACT_CURRENT_MODEL_V4_HISTORICAL_REPLAY_IMPOSSIBLE_FOR_PRECAPTURE_YEARS`.
Then preserve the zero-exact frontier and begin only a separately governed,
prospective receipt-capture design. Do not backfill an exact label onto reconstructed
evidence.
