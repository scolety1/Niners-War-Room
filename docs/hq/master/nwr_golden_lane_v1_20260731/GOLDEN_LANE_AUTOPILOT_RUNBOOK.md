# Golden Lane Autopilot Runbook

For every controller turn:

1. Fetch/prune once; resolve canonical HQ/tree and remote divergence.
2. Validate both checkouts are clean, the scheduler is disabled or absent, no
   overlapping lane is active, and protected-state hashes match.
3. Validate `GOLDEN_LANE_AUTOPILOT_STATE.json`, status, matrix, manifest, and the
   exact next-prompt hash with `scripts/validate_golden_lane_autopilot.py`.
4. If a hard stop is active, emit one decision packet and stop.
5. Create a fresh implementation worktree from the verified canonical HQ and
   execute only the named phase.
6. Run focused and applicable full validation; commit the phase packet.
7. Create a fresh independent review/adoption worktree from the same canonical
   parent, adopt the implementation commit, rebuild evidence, and review scope.
8. Permit at most one bounded correction cycle. A second required correction is
   a hard stop.
9. After Green or an accepted truthful null result, conditionally push normally,
   reread remote at 0/0, fast-forward stable, and prove stable is clean.
10. Update the canonical phase packet and generate exactly one next prompt.
11. Recompute its SHA-256, write the phase identity/hash to autopilot state, run
    validation from two roots, and dispatch automatically only if all gates pass.

Never reuse a dirty worktree, update the operational checkout, enable refresh,
force-push, rewrite history, mutate owner state, or combine major phases.

## Prompt generation contract

The generated prompt must name exactly one `next_phase`, declare its allowed and
prohibited scope, identify canonical/stable/operational locations, require fresh
implementation and review worktrees, preserve scheduler and protected state,
state push rules, and describe phase pass/null/failure closeout. The UTF-8 file
bytes are hashed with SHA-256 and recorded as `next_prompt_sha256`. Dispatch must
re-read the file and verify both hash and phase identity immediately before worktree creation.

