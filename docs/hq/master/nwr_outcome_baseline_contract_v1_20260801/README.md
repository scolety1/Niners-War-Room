# NWR Outcome and Baseline Contract V1

Verdict: `GREEN_NWR_GOLDEN_LANE_PHASE_2_COMPLETE_AND_PHASE_3_READY`.

This Phase 2 packet freezes evaluation contracts before any Phase 3 feature test. It does
not create a new formula, scalar dynasty value, rookie-veteran common scale, calibration,
rank, product behavior, or production default.

The scored historical population is exact-ID QB/RB/WR/TE player-season evidence under the
existing NWR 10-team, 1QB, non-PPR, first-down scoring rules. Win Now, two-year, and
three-year football outcomes remain separate position-specific targets. Availability,
evidence confidence, and market retention remain separate concepts and cannot silently
alter a football target.

Replacement references are review-only comparators at QB12, RB30, WR40, and TE12. They
are calculated from complete, admitted position-season scoring rows available to the fold;
they are not production ranks or a cross-position value. Missing reference support fails
closed.

All folds are expanding and chronological. A training row is usable only when its label was
available by the decision cutoff. Right-censored, missing, identity-blocked, unsupported,
and source-blocked rows remain visible in coverage reporting and never become zeroes.

The persistence harness builds a synthetic baseline in a disposable root, writes it
atomically, rereads and verifies it, and proves deterministic bytes. It refuses protected,
existing, symlink, and non-empty roots and never writes production or user state.

