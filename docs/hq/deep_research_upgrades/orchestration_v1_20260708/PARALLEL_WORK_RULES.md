# Parallel Work Rules

## Required Worktree Rules

- Use fresh worktrees only.
- Do not use, reset, clean, stash, or otherwise disturb the dirty primary checkout.
- Every lane must state the exact base HQ HEAD.
- No push or merge unless explicitly instructed.
- Every lane must produce a final guardrail scan.

## Packet Collision Rules

- Do not run two Codex lanes that touch the same review packet folder.
- Do not run two Codex lanes that touch the same artifact manifest.
- Do not run two Codex lanes that write the same scorecard, candidate registry, miss taxonomy, or source status file.
- Do not let HQ 1 edit HQ 2 tournament scorecards or miss taxonomy artifacts.
- Do not let HQ 2 edit HQ 1 broad source map, source status matrix, or future candidate registry.

## Protected File Rules

- Do not run two Codex lanes that touch the same model, ranking, runtime, or app files.
- Do not let any review lane edit production formula files.
- Do not let any review lane edit UI/app files.
- Do not let any review lane edit runtime service files.
- Do not let any review lane promote source status.
- Do not let any review lane change default sort or hidden sort logic.

## Script Rules

- Review-only scripts require an explicitly assigned lane.
- Do not run two script-writing lanes in parallel if either touches the same input/output folder.
- Tournament runner lanes must be serialized if they share labels, baselines, scorecards, or miss taxonomy outputs.
- Orchestration and prompt lanes should not add scripts.

## Final Scan Requirements

Each lane must confirm:

- Base HQ HEAD.
- Clean worktree before changes.
- Changed paths are scoped to the lane artifact folder.
- No production model files changed.
- No rankings files changed.
- No app/UI files changed.
- No runtime/source-truth files changed.
- No default sort or hidden sort changes.
- No recommendation, player verdict, boost, winner, trade, draft, or decision logic added.
- No exact PFF Elusive Rating calculation/display.
- No `nwr_elusive_proxy_review_only` calculation/display.
- No current/future leakage introduced.
- Dirty primary checkout untouched.
