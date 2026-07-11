# Pytest Teardown Differential

## Command and environment

Both isolated worktrees used the same bundled workspace Python, environment, arguments, and 120-second observation timeout:

`python -m pytest -q tests/test_rookie_evidence_registry_scaffold_v1.py tests/test_rookie_evidence_registry_linkage_gap_closure_v1.py tests/test_rookie_evidence_registry_metadata_review_queue_v1.py`

No test file, marker, skip, xfail, assertion, or runtime code differs between baseline and source; the source commit is documentation-only.

## Results

| Revision | Tests/assertions | Assertion result | Teardown | Timeout | Process state | Diagnostic output |
| --- | ---: | --- | --- | --- | --- | --- |
| Clean HQ `b6d16e64d4c182f4a9a5cce558a4b389d0d48bc1` | 68 | PASS | completed | 120s not reached; 1.82s elapsed | exited normally, code 0 | `68 passed in 1.82s`; no stack diagnostic required |
| Source `497e5f0b5dd1020b47f53cf862aa63571cd735eb` | 68 | PASS | completed | 120s not reached; 1.70s elapsed | exited normally, code 0 | `68 passed in 1.70s`; no stack diagnostic required |

Baseline/source equivalence: `PASS_EQUIVALENT_NORMAL_TEARDOWN`. The previously reported post-assertion hang did not reproduce on either revision. Because both revisions completed normally, the source commit changes no test/runtime code, and no test was modified or weakened, there is no source-specific teardown regression and no test-environment hold is required for this lane.
