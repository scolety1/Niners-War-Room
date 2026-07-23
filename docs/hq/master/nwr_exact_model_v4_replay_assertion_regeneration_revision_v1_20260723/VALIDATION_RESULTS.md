# Validation results

Local verdict:
`GREEN_NWR_EXACT_REPLAY_ASSERTION_AND_REGENERATION_REVISION_READY_FOR_ADOPTION`.

- Original blocker reproduction: 8/8 survived before hardening.
- Original blocker closure: 8/8 detected after hardening.
- Expanded mutation sensitivity: 33/33 detected.
- Exact replay suite: 32 passed.
- Same-checkout full builds: 28/28 files identical.
- Independent clean checkouts: 28/28 files identical.
- Input-order and environment isolation: 28/28 files identical.
- Committed packet reproduction: 28/28 files identical.
- Mutable Git-state isolation: 28/28 files identical.
- Changed-file Ruff: pass.
- Python compilation: pass.
- Git whitespace checks: pass.
- Metrics and challenger disposition: preserved.
- Current board and frozen comparator: exact.
- Primary, persistent, backup, recovery, protected, and frozen state: exact.

Hermetic, LocalData, five closed-finding security regressions, and passive Data
Health are rerun independently in adoption before conditional push.
