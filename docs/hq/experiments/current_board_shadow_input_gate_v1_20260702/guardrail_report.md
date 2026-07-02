# Guardrail Report

Verdict: `GREEN_GUARDRAILS_INPUT_GATE_REVIEW_ONLY`

- No production formula changes.
- No model training or tuning.
- No formula promotion.
- No app wiring or live preview page.
- No production rankings behavior changes.
- No hidden sort or recommendations.
- No source-truth promotion.
- No runtime behavior or production config changes.
- No candidate output wired into NWR.
- No raw/shared/cache/local export/secrets files tracked.
- Market/ADP/vendor/projection fields are blocked as source truth.
- Routes, TPRR, YPRR, route proxies, red-zone sidecars, ambiguous `rz_att`, and current-only context remain blocked as model features.

Generated export is local-only and review-only: `C:\NWR_REVIEW\current_board_shadow_input_gate_v1_20260702\current_board_baseline_shadow_input_review_only.csv`.
