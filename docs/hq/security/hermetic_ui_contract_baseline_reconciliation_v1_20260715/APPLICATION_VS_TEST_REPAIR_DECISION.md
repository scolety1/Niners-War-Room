# Application vs Test Repair Decision

## Decision

No application repair is authorized or necessary. Current application behavior already matches later canonical product, navigation, and Decision Trust Strip acceptance evidence.

| Failure | Decision | Changed layer |
|---|---|---|
| Phase-5 grouped warnings | `STALE_TEST_EXPECTATION` | Test only |
| Phase-5 filter language | `STALE_TEST_EXPECTATION` | Test only |
| Phase-5 score disclosure | `STALE_TEST_EXPECTATION` | Test only |
| Player Board labels | `STALE_TEST_EXPECTATION` | Test only |
| Primary trust banner | `FIXTURE_OR_HARNESS_DEFECT` | Test harness only |
| Main model banner | `FIXTURE_OR_HARNESS_DEFECT` | Test harness only |

## Non-weakening proof

- The warning-group test still asserts grouped and detailed warnings plus both raw warning sources on the owning legacy Decision Board.
- The Phase-5 filter test now asserts five current controls and two forbidden deprecated labels.
- The score-disclosure test asserts raw score metadata and all six canonical Decision Trust Strip labels.
- The Player Board test asserts eleven labels on the actual routed implementation.
- The trust tests retain legacy banner checks, add current routed trust-strip checks, and preserve Draft Prep gating.
- The representative Streamlit trust render test remains unchanged and passing.

No assertion was skipped, xfailed, replaced with `True`, or reduced to existence-only coverage of an unrelated file.
