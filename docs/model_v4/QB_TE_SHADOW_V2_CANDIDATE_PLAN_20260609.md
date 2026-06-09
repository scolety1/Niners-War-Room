# QB/TE Shadow v2 Candidate Plan - 2026-06-09

All variants are proposal-only and human-review-only. No active output is changed.

## Distribution Context
- QB median score: 15.1316
- TE median score: 14.3814
- RB/WR p80: 38.9005
- RB/WR p85: 44.9537
- RB/WR p90: 50.9317
- RB/WR p92: 54.0656
- RB/WR p95: 61.3322

## Variants
- `qb_context_balance_te_soft_exception_v2`: keeps v1 QB discipline and gives source-safe elite TE rows a softer no-premium adjustment.
- `qb_context_balance_te_receipt_gate_v2`: keeps v1 QB discipline and requires stricter private receipts before a TE escapes the no-premium compression band.
- `qb_context_balance_te_upper_band_guard_v2`: prevents automatic TE #1 behavior but allows a higher upper band for exceptional private evidence.
- `qb_context_balance_te_age_status_sensitive_v2`: similar to soft exception, but veteran/status-risk TEs get more cautious treatment.

## Blocked Inputs
No variant uses market rank, league rank, ADP, startup, consensus, public ranks, projections, trade calculators, RotoWire rankings/projections, or legacy active-pack scores as score inputs or targets.
