# Known Hermetic Baseline Comparison

- Canonical before: `FAIL: bootstrap 13/13; security 20/20; pytest 2950 passed, 3 failed, 15 errors; EXIT 1`
- Candidate after: `FAIL: bootstrap 13/13; security 20/20; pytest 2965 passed, 3 failed, 15 errors; EXIT 1; exact baseline signature`
- Failing tests: `test_input_order_is_canonicalized`; `test_no_current_board_or_frozen_comparator_change`; `test_full_packet_repeats_and_input_order_environment_do_not_change_bytes`
- Setup errors: 15 cases in `tests/test_exact_model_v4_replay_accuracy_audit_v1.py`
- Classification: `BASELINE_HERMETIC_BLOCKER_NOT_CANDIDATE_REGRESSION`
- Protected historical replay artifact was not modified.
