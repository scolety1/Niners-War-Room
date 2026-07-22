# Hermetic, LocalData, and security regression results

- Hermetic bootstrap: 13 passed, 0 failed.
- Security automation controls: 20 passed, 0 failed.
- Python collection: 2,736 passed; no skip, xfail, or xpass added.
- Hermetic verdict: HERMETIC_TIER_PASS, exit 0.
- LocalData: BLOCKED_MISSING_LOCAL_TEST_PACK, native exit 4.
- LocalData was not passed, skipped, synthesized, copied, or imported.
- All five previously closed security-finding regressions remained green inside
  the accepted suite. No new security scan was run.
- CSV security, trust classification, Data Health, page-open no-mutation,
  launcher ownership, route, ranking, compare, trading, draft, persistence, and
  tracked UI contracts passed in Hermetic.

A pre-commit Hermetic attempt had 2,726 passes and ten expected self-audit
failures because those lane tests reject uncommitted app paths. After the green
website repair commit, the authoritative clean-tree rerun passed all 2,736.
