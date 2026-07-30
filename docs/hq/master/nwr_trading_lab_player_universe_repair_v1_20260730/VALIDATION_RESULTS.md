# Validation Results

## Committed implementation

- Focused Trading Lab suite: 57 passed.
- Earlier selected regression suite: 103 passed.
- Changed-file Ruff: passed.
- Git whitespace: passed (line-ending notices only in the CRLF materialized clone).
- Python/Streamlit AppTest: 240 players, 240 unique IDs, veteran, rookie, picks,
  source disclosure, no recommendation, and no page-open mutation all passed.
- Real production parity: Finished V1 = dimension = roster ID sets, 240 each.
- Mutation sensitivity: 15/15 killed through service, loader, lookup, or render paths.
- Browser render: 375x812, 768x1024, and 1440x1000 passed with no traceback or root overflow.

## Repository harness

The first independent implementation clone Hermetic run completed bootstrap
13/13 and existing focused security controls 20/20, then reported 2,946 passed
and 14 failed. Ten failures were launcher-port environment failures while port
8520 was occupied; four were Outcome V3 byte-hash failures caused by CRLF checkout
materialization in that disposable clone. The unchanged stable checkout,
retested through the same offline runtime, passed Outcome V3 4/4 and launcher
42/42. The implementation commit contains neither surface.

The adoption clone must use `core.autocrlf=false` and rerun the full Hermetic
gate. LocalData is expected to report `BLOCKED_MISSING_LOCAL_TEST_PACK` with exit
4. No provider call, security scan, skip, xfail, xpass, or scheduled-task
execution is part of this repair.
