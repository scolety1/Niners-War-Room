# Recovery Action Safety Review

Result: PASS.

Guidance is a deterministic lookup from an already-classified display state. It may tell the user to review an existing partial breakdown or diagnostic, keep stale labeling visible, wait for availability, request source-admission review, choose an existing approved refresh control separately, or take no action for an intentional skip.

The implementation does not auto-retry, bypass a gate, navigate and execute, rewrite state on disclosure, create a diagnostic link, or enable an unavailable action. The panel contains no executable recovery control. `AVAILABLE_ACTION`, `REVIEW_LINK`, `INFORMATION_ONLY`, and `UNAVAILABLE_ACTION` are plain-language status tokens explained in the panel caption. Unavailable states include the reason and a safe wait/review instruction.

Refresh Data command selection, source list/order, timeouts, retries, orchestration, persistence, and confirmations are untouched. Settings / Data Health calculations, freshness, source status/admission, diagnostics, retained production data, and page-open behavior are untouched.
