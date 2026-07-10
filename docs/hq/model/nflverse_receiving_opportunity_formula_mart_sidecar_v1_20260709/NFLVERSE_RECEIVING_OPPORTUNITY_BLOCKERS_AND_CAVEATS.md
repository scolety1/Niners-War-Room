# Blockers And Caveats

- This is review-only evidence, not production/model-use.
- Same-season/future context was not used; all tests use feature season N to target season N+1.
- Receiving opportunity fields are not true route/YPRR/TPRR receipts and do not reopen route source recovery.
- RACR/PACR are denominator-sensitive and are null when prior air yards are not positive.
- Combo tests using prior ffopportunity or NGS inherit partial-window V2 sidecar caveats.
- Partial-window results cannot be used to claim the full-history `.755` plateau was broken.
- Review-only ranking simulation remains blocked.
