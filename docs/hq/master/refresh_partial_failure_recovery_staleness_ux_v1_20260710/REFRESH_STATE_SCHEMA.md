# Refresh State Schema

Canonical field order: `refresh_state`, `last_success_or_as_of`, `retained_data_status`, `reason_summary`, `safe_next_action`, `action_availability`, `diagnostic_path`.

State precedence is gated, skipped, unavailable, failed, stale retained, explicit partial, success, then not enough information. It resolves conflicting fields for display without changing input. Run-level `PARTIAL_SUCCESS` requires at least one success and one non-success; per-source detail remains visible.

Action values are `AVAILABLE_ACTION`, `REVIEW_LINK`, `INFORMATION_ONLY`, and `UNAVAILABLE_ACTION`. They are labels, never commands.
