# Post Display-Only NGS Next Step Recommendation

Recommendation: safe to start a separate PFR identity hardening lane from a fresh clean worktree, if Tim explicitly opens that lane.

Conditions:

- Do not start PFR work from the dirty primary checkout.
- Do not treat PFR as identity-safe or model-approved yet.
- Keep PFR out of UI/runtime until a dedicated source/identity gate passes.
- Keep NGS as REVIEW_ONLY_NGS_CONTEXT.
- Do not use PFR, ESPN QBR, FTN, PFF, ffopportunity, routes, TPRR, YPRR, rz_att, exact PFF Elusive Rating, or nwr_elusive_proxy_review_only in production rankings.

Current best next action:

Open PFR identity hardening only as a guarded source/identity review lane. Do not expand model/rank/UI behavior from this health check.
