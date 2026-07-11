# Refresh Partial-Failure Recovery and Staleness UX V1

Verdict: `GREEN_REFRESH_RECOVERY_STALENESS_UX_V1_READY_FOR_HQ_REVIEW`

This lane adds a passive presentation adapter and compact disclosure panel to Refresh Data and Settings / Data Health. It maps existing refresh records into eight mechanically distinct states and deterministic guidance. It does not execute recovery, alter refresh orchestration, calculate freshness, change source admission, or mutate records.

The verified base was remote `work/hq-parallel-control` at `250c28853a4bc175b2702e206e68f49560c4e6e0`; the remote had not advanced. The implementation is isolated on `work/refresh-recovery-staleness-ux-v1-20260710`.

The adapter is pure and I/O-free. The panel uses a keyboard-operable Streamlit expander, text labels, and a compact-width table. Existing refresh controls remain the only way to initiate refreshes, and existing health calculations remain controlling.

No production, ranking, formula, recommendation, sorting, filtering, source-registry, source-admission, frozen-artifact, orchestration, freshness-policy, or Decision Trust Strip code was changed.
