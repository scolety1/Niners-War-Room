# Legacy `os.replace` Regression Proof

The exact legacy negative control failed the second of five `os.replace`
operations and observed a mixed set: one new file and four old files. This
confirms the original release blocker.

The transactional negative control monkeypatched `os.replace` to fail if any
individual output replacement was attempted. No output replacement occurred.
On Windows, both directory publication and pointer commit use handle-bound
native rename. Injecting failure at the pointer replacement retained the old
pointer and all five old payloads.

Results:

- legacy second replacement: partial publication reproduced;
- new individual-output replacement calls: 0;
- new pre-pointer failure: old generation complete and current;
- mixed generation visible through resolver: 0;
- set-level commit points: exactly 1 (`current_generation.json`).
