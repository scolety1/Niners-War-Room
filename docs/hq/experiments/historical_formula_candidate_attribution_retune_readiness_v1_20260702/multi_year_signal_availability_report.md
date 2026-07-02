# Multi-Year Signal Availability Report

Current-board candidate feature input used here:
`C:\NWR_REVIEW\current_board_candidate_scoring_feature_completion_gate_v1_20260702\current_board_candidate_feature_input_completed_review_only.csv`

Available current-board feature input is a 2025 lagged factual snapshot for 2026 current-board review. It includes prior-season games, NWR scoring, PPG, opportunities, targets, receptions, receiving/rushing/passing production, and first downs.

It does not include admitted current-board multi-year rolling production, career peak, age, draft capital, or dynasty cornerstone/stability fields as formula inputs. Market/context data exists as display-only review context, but it is not source truth and must not become a model feature.

Merged historical substrate/source-contract artifacts provide a path to build multi-year features safely, but a future retune lane must explicitly admit those fields as review-only before candidate testing.

Readiness: `YELLOW_AVAILABLE_HISTORICALLY_NOT_ADMITTED_FOR_CURRENT_BOARD_FORMULA_INPUT`.
