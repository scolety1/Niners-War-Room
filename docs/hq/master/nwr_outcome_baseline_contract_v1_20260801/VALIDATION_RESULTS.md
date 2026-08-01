# Validation Results

- Contract validator: PASS with 69 governed rows.
- Exact scoring configuration and source hashes: PASS.
- Target separation and label-availability dates: PASS.
- Expanding, nested, horizon-aware chronological folds: PASS.
- Review-only replacement references and deterministic competition ties: PASS.
- Support and fail-closed missingness controls: PASS.
- Synthetic persistence fixture: PASS with 94 rows and four baseline outputs.
- Two-disposable-root persistence comparison: PASS; canonical output SHA-256 `c71bff8b924bd1e02f0c65fabe51d368c595d1effa0702c7ddf7ce833dcd0979`.
- Protected-root refusal and negative mutation controls: PASS.
- Focused tests: PASS, 8/8.
- Applicable regression slice: PASS, 70/70.
- Static validation: PASS.
- Protected authorities and production state: unchanged.
- Independent adoption review: PASS in a fresh worktree from the exact canonical parent; adopted tree matched the implementation tree byte-for-byte, validators and the persistence harness passed, regression slice passed 70/70, and static checks passed.
