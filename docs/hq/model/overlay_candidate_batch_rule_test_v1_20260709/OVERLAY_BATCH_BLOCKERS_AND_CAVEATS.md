# Overlay Batch Blockers And Caveats

- This is review-only testing, not production/model-use.
- Partial-window results must not be treated as full-history comparable.
- Primary overlay policy is non-stacking; secondary eligibility is only recorded.
- Inputs are inherited from accepted review-only packets and sidecars.
- Some accepted prior packets are still local-only in their source worktrees; those source packet paths were verified and recorded in the source trace.
- Current-only ADP, market without as-of proof, same-season/future context, SportsDataIO, paid/API/free-trial sources, PFF Elusive Rating, `nwr_elusive_proxy_review_only`, ungated CFBD/prospect production, and inferred UDFA truth remain blocked.
- Review-only ranking simulation remains blocked unless a future readiness gate is explicitly authorized and justified.
