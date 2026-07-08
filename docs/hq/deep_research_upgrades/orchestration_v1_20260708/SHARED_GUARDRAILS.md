# Shared Guardrails

These rules apply to HQ 1, HQ 2, and all future Deep Research upgrade lanes.

## Hard Rules

- No production rankings change.
- No model formula change.
- No model weight change.
- No default sort change.
- No hidden sort.
- No UI integration.
- No app/runtime behavior change.
- No player recommendations, player verdicts, boosts, winners, trade logic, draft logic, or decision logic.
- No source-truth promotion.
- No blocked source use.
- No exact PFF Elusive Rating calculation or display.
- No `nwr_elusive_proxy_review_only` calculation or display.
- No current/future leakage.
- No name-only joins.
- No dirty primary checkout disturbance.
- No merge unless explicitly instructed.
- No push unless explicitly instructed.

## Source Rules

- Read source gates before using a field in any review-only plan.
- Treat display-only, review-only, blocked, and identity-unsafe signals as non-production.
- Do not imply source admission from research interest.
- Do not use paid/proprietary stats as if NWR already has access.
- Do not use future-season information for identity matching or historical features.

## Output Rules

- Review artifacts must live in lane-owned docs paths.
- Every packet must include source trace and guardrail status.
- Every CSV must parse.
- Every lane must report changed paths and protected-path scan results.
- Any future script must be review-output-only and scoped to its lane folder unless separately approved.
