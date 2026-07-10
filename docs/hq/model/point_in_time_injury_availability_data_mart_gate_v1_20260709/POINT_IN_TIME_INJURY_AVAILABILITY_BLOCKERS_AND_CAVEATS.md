# Blockers And Caveats

- This is review-only evidence, not production/model-use.
- This is not injury prediction.
- Same-season/future context was not used; all tests use feature season N to target season N+1.
- Injury reports include rest and non-injury rows; derived features try to avoid treating non-injury rest as injury signal, but status semantics remain caveated.
- Absence from injury reports is treated as zero only when the player has a weekly roster record for that feature season.
- Combo tests using prior ffopportunity or NGS inherit partial-window V2 sidecar caveats.
- Partial-window results cannot be used to claim the full-history `.755` plateau was broken.
- Review-only ranking simulation remains blocked.
