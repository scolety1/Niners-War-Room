# Display-Only NGS HQ Merge Report

Verdict: GREEN_DISPLAY_ONLY_NGS_HQ_MERGED

Target branch reviewed: work/hq-parallel-control

Pre-merge HQ HEAD: a2e81615f202a3c1ab00c4b176c810f80ca98555

Source branch reviewed: work/lane-player-compare-display-only-ngs-v1-20260707

Source HEAD: 44f75fe6d61606c9046d85988151356d83053f90

Merge mode: clean detached HQ merge-review worktree from origin/work/hq-parallel-control, with a no-fast-forward merge commit prepared locally. The dirty stale local checkout of work/hq-parallel-control was not disturbed.

Conflict result: none.

Runtime surfaces added:

- Development Lab: Review-only NGS Context.
- Settings/Data Health: Review-only NGS Context.
- Player Compare: Review-only NGS Context.

Gate preserved: REVIEW_ONLY_NGS_CONTEXT.

Scope confirmation:

- NGS context is display-only/review-only.
- NGS is not model-approved.
- NGS is not source truth.
- NGS is not used in rankings, default sorting, hidden sorting, recommendations, trade logic, draft logic, or player decisions.
- Missing or thresholded NGS values remain unavailable/thresholded and are not converted to zero.

Allowed NGS display metrics:

- QB: CPOE, expected completion percentage, average time to throw, aggressiveness, air yards to sticks, intended air yards, completed air yards.
- RB: RYOE, RYOE per attempt, rush percentage over expected, efficiency, 8+ box rate, time to line of scrimmage.
- WR/TE: separation, cushion, expected YAC, YAC over expected, share of intended air yards, average intended air yards.

Blocked families preserved:

- PFR, ESPN QBR, FTN, PFF, ffopportunity UI use, routes, route participation, TPRR, YPRR, rz_att, exact PFF Elusive Rating, nwr_elusive_proxy_review_only.
- Trading Lab, Live Draft / Mock Draft, and Rankings preset remain untouched.

Push status: not pushed; explicit push approval still required.
