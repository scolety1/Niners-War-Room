# NWR Canonical Baseline Health V1

Verdict: `GREEN_NWR_GOLDEN_LANE_PHASE_1B_COMPLETE_AND_PHASE_2_READY`.

This packet pins and validates the exact 14 Phase 1A raw snapshots without
modifying them. Every file is hash-, size-, schema-, width-, row-, grain-,
identity-, rights-, temporal-, and safe-path checked. No source becomes model
eligible here.

The weekly player-stat snapshot's second horizontal column block is proven to
be a byte-for-byte logical duplicate for all 76,804 rows. The deterministic
derived representation keeps the first 146 columns, including
`summary_level`, and drops only the repeated 145-column block. Its complete
rebuild receipt is recorded; the raw source remains immutable.

The seasonal player-stat snapshot is a mixed horizontal join of unrelated
seasonal and weekly schemas and is quarantined in full. Depth-chart exact
duplicates, missing identities, ambiguous crosswalk values, unknown rights,
and unsafe temporal uses are also quarantined fail-closed. These truthful
quarantines are non-production baseline exceptions, not model admission.

Outcome V3 is restored deterministically in fresh Windows worktrees by the
scoped `text eol=lf` rule in `.gitattributes`; its governed semantic rows and
authoritative SHA-256 remain unchanged. Existing worktrees created from the
pre-repair parent use the validator's bounded `--restore-outcome-checkout`
mode, which refuses every input except the authoritative hash or the single
known CRLF mismatch hash.
