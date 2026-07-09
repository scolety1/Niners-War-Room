# Diverse Champion Refinement Blockers And Caveats

- This run used only review-only Formula Data Mart fields.
- No route/YPRR/TPRR, return scoring, broad PFR, PFR QB passing, PFF Elusive Rating, `nwr_elusive_proxy_review_only`, exact Model v4 replay fields, or current/future context were used.
- Age/lifecycle and role-archetype effects are review-only context. They are not production boosts, penalties, formula approvals, ranking inputs, hidden sorts, or recommendation logic.
- The refinement grid was fixed before scoring and no dynamic optimization was run.
- Exact Model v4 replay remains blocked.
- Production/model-use and rankings integration remain blocked.
