# Source Trace

- Formula Data Mart: `docs/hq/data_hygiene/formula_data_mart_feature_availability_audit_v1_20260709/FORMULA_DATA_MART_REVIEW_ONLY.csv`; 5,518 rows; LF-canonical SHA-256 `705ce26c9b3649405efe42af135204e98bcad91ae718b43d55b5415fcef6159f`.
- Age/lifecycle sidecar: `docs/hq/data_hygiene/age_lifecycle_sidecar_freeze_validation_v1_20260709/MODEL_V4_AGE_LIFECYCLE_SIDECAR_REVIEW_ONLY.csv`; LF-canonical SHA-256 `623de1acd6fc1d885cf4b645be62d4bd4f9032b33de723e6547a3c8070c4573a`; exact `player_id|season|position` join only.
- Scoring contract: `config/nwr_scoring_rules_nwr_1qb_nonppr_fd_v1.json`; LF-canonical SHA-256 `59e7a65f61fd95cd83e82ba0fb631e4977faf120d7692f3aa3ebc690000af3a7`.
- Replacement ranks and chronological rules: Phase 2 packet `docs/hq/master/nwr_outcome_baseline_contract_v1_20260801/`.

All fields are lagged feature-season facts. Missing values remain missing. Current market, provider calls, diagnosis, route data, current-board rank, and target-season context are excluded.

