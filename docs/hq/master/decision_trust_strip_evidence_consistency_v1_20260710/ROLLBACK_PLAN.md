# Rollback Plan

Rollback is presentation-only:

1. Remove the three `render_decision_trust_strips` calls and their imports.
2. Remove `app/components/decision_trust_strip.py`.
3. Remove `src/services/decision_trust_strip_service.py`.
4. Remove the three focused trust-strip tests and synthetic fixture.
5. Leave all pre-existing pages, services, data, scores, ranks, filters, sorting, eligibility, receipts, sources, and identity systems unchanged.

No migration, data repair, cache invalidation, or source rollback is required.
