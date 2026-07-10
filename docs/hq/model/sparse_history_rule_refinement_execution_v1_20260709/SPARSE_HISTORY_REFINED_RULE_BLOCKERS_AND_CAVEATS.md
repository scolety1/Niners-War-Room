# Sparse-History Refined Rule Blockers and Caveats

- Production/model-use remains blocked.
- Rankings integration remains blocked.
- App/runtime behavior is unchanged.
- Source promotion remains blocked.
- Push/merge was not performed.
- Current-only ADP, market data without as-of proof, SportsDataIO, paid/API/free-trial sources, PFF Elusive Rating, `nwr_elusive_proxy_review_only`, CFBD/prospect model input, and inferred UDFA truth were not used.
- Partial-window results remain partial-window only and cannot be compared as full-history plateau breaks.
- The primary metric is net miss reduction; Spearman is secondary.
