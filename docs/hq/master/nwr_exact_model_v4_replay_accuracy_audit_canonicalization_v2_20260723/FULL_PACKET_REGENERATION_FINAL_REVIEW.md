# Full-packet regeneration final review

Authoritative command:

```powershell
python scripts/build_exact_model_v4_replay_accuracy_audit_v1.py --source-commit 0929ce6ec058a698efeee10fe5770f56047bab21 --repo-root <ROOT> --output-dir <OUT>
```

Verification can additionally use `--verify-against <PACKET>`,
`--comparison-report <CSV>`, and governed `--input-order` perturbations.

Canonical outputs are anchored to the fixed source commit and fixed tracked
input hashes. They omit wall-clock timestamps, absolute worktree paths, user
names, active branch names, mutable remote state, and unbounded Git branch
enumeration. Git evidence uses only fixed reachable history.

Text is UTF-8 without BOM, LF-only, and newline-terminated. CSV field order and
sort keys are explicit; floats use six decimal places in generated packet
tables; JSON keys and governed arrays are sorted. Null, season, position, and
rank tie-breaking are explicit. The manifest hashes the ordered nonmanifest
inventory and excludes itself.

All governed comparisons passed with `28/28` identical files and zero
mismatches:

- same-checkout repeat;
- two independent detached clean checkouts;
- original/reverse/fixed-seed-random input order;
- committed packet reproduction;
- mutable local Git metadata probe; and
- UTC versus America/Denver environment isolation.

No generated packet file was manually corrected after validation.
