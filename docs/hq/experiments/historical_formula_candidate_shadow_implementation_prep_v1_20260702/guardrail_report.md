# Guardrail Report

Verdict: `GREEN_GUARDRAILS_WITH_SAFE_YELLOW_CURRENT_BOARD_BLOCKER`

- No production formula changes.
- No production model training or tuning.
- No app wiring or live preview page.
- No ranking, hidden sort, recommendation, source-truth, runtime, or production config change.
- No candidate output is wired into NWR.
- No market/ADP/vendor/projection fields are used as source truth.
- Routes, TPRR, YPRR, route proxies, red-zone sidecars, ambiguous `rz_att`, and current-only roster/status/injury/depth/schedule context remain blocked.
- Missing values are not forced to zero.
- Selected candidate remains review-only and not production-approved.
- Current-board static output is blocked until approved clean inputs exist: `SAFE_YELLOW_BLOCKED_CURRENT_BOARD_INPUT_NOT_APPROVED_IN_CLEAN_WORKTREE`.
