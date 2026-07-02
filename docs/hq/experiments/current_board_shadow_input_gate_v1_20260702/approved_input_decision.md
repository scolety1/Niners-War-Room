# Approved Input Decision

Decision: `SAFE_EXPORT_GENERATED_REVIEW_ONLY`

Rationale:

- The raw app current-board export under `local_exports/` is not tracked in the clean worktree and must not be copied into git.
- A tracked review artifact exists at `docs\hq\model\unified_player_universe_v0\unified_player_universe_v1_review.csv` with stable player identifiers, player names, positions, teams, display ranks, data-quality fields, and explicit `app_wiring_allowed=no` / `model_input_allowed=no` guardrails.
- This gate generated a stripped review-only baseline input from that artifact and excluded market values, ADP/vendor/projection fields, candidate outputs, production approval flags, and score components that are not present in the tracked source.

Approved use:

- Static side-by-side shadow review input only.

Blocked use:

- Production rank source.
- App ranking replacement.
- Hidden sort.
- Recommendation.
- Model input.
- Source truth.
