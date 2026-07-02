# Review-Only Shadow Config Spec

This is a static artifact contract, not a runtime configuration file.

Candidate id: `wr_boundary_breakout_sensitivity_guard`

Permitted output surface:

- Static CSV/HTML/Markdown review bundles outside the repo.
- Review-only experiment docs under `docs/hq/experiments`.

Blocked surfaces:

- Streamlit pages.
- App routes or live preview.
- Ranking services.
- Model services.
- Source-truth registries.
- Hidden sort or recommendation code.
- Production config files.

Current-board shadow bundle status:

- `SAFE_YELLOW_BLOCKED_CURRENT_BOARD_INPUT_NOT_APPROVED_IN_CLEAN_WORKTREE`
- Required before a real static current-board side-by-side: approved current-board baseline export, safe 2025 completed feature context, deterministic identity join, and no forbidden inputs.
