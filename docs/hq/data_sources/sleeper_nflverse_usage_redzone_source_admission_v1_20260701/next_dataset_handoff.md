# Next Dataset Handoff

Recommended next lane: `Core Usage Review Dataset V1`.

The next lane may build a compact review-only season N to season N+1 lagged factual usage dataset only if it preserves these rules:

1. Use completed prior-season data only for any lagged feature candidate.
2. Keep `review_only=true` and all production approval flags false.
3. Do not use missing Sleeper sparse keys as zero.
4. Compare Sleeper `rec_tgt`, `rush_att`, `rec`, `off_snp`, and `tm_off_snp` against NFLVerse/NFL Usage overlap before trusting field semantics.
5. Treat `rz_att` as blocked until source semantics are documented.
6. Treat red-zone opportunities as opportunities, not touches or scoring expectations.
7. Defer routes/TPRR/YPRR unless a rights-cleared upload or already approved compact route source is available.
8. Do not read raw `C:\NWR_SHARED_DATA` from app pages.
9. Do not approve model, training, source-truth, ranking, hidden-sort, recommendation, probability, trade-value, or pick-value use.
10. Do not block this builder on full fantasy scoring parity or return touchdown subtype gaps.
11. Do not create fake route proxies from participation data.

Build-ready review families for the next checkpoint:

- Targets: `rec_tgt` from Sleeper, `targets` from NFLVerse/NFL Usage.
- Carries: `rush_att` from Sleeper, `carries` from NFLVerse/NFL Usage.
- Receptions: `rec` from Sleeper, `receptions` from NFLVerse/NFL Usage.
- Yardage context: rushing yards, receiving yards, receiving air yards, receiving yards after catch where already admitted.
- First downs: passing/rushing/receiving first downs where already admitted in NFLVerse player_stats.
- Snaps: `off_snp`, `tm_off_snp`, NFLVerse `offense_snaps`, `offense_pct`, and derived snap share only after denominator checks.
- Derived usage: touches and opportunities from approved factual components only.
- Red-zone: `rec_rz_tgt`, `rush_rz_att`, and `pass_rz_att` as source-admit candidates after coverage and semantics checks; PBP-derived `yardline_100 <= 20` counts may be review-only validation/fallback artifacts.

Suggested join/coverage checks:

- Season/week coverage completeness by source.
- Player identity join coverage and ambiguity review.
- Cross-source row count and non-null count comparison.
- Explicit-zero versus missing/sparse-key audit.
- As-of/leakage gate before any experiment consideration.
- Field-level source precedence and fallback policy, especially Sleeper versus NFLVerse/PBP-derived red-zone counts.
- Null preservation check proving missing remains `Not enough information`.
