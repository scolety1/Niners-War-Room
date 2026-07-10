# Validation Results

## Verdict

`PASS_PACKET_VALIDATION_FOR_RED_REGULARIZED_CHALLENGER_FAILED_TEMPORAL_VALIDATION`

| Validation | Result | Evidence |
|---|---|---|
| Required files | PASS | 26 unconditional required artifacts present; conditional challenger correctly absent |
| Preregistration hash | PASS | `1b8cfac3807613c453588a60b24b6303e8bcaac35d03639c1927ec8d81735e28` unchanged and recorded before scoring |
| Standard-library CSV parse | PASS | 15 CSV files; consistent headers and row widths |
| Spreadsheet-engine CSV parse | PASS | all 15 CSV files parsed with `@oai/artifact-tool` and nonempty used ranges |
| Origin registry | PASS | 132 unique candidate-season-position origins (3×11×4) |
| OOF prediction identity/hash | PASS | 14193 unique candidate-season-position-player rows; hashes match origin registry; outcomes joined after hashes |
| Balanced headline reconciliation | PASS | ridge `0.682359958` vs PYF `0.674558848`; delta `+0.007801111` for both balanced summaries |
| Severe-FP reconciliation | PASS | ridge 79 vs PYF 73 on paired shared rows |
| 2026 baseline freeze | PASS | SHA-256 `b3270d9782cf53de745e966c318dd61aa7f482db17da7c4ceb51ef8baa8e1179`; PYF and exact legacy 231 valid rows each; current-board comparator preserved as 240 rows / 232 valid scores |
| Challenger absence | PASS | no fake/empty challenger CSV; freeze manifest records gate-failure absence |
| Freeze manifest | PASS | baseline file hash, row counts, conditional absence, input hashes, and review-only restrictions validated |
| Internal links/paths | PASS | 8 Markdown files; no broken relative links |
| Contradictory-language scan | PASS | no forbidden `untouched` phrase and no affirmative claim that historical results prove production superiority |
| Protected-path scan | PASS | every changed path is inside this isolated packet |
| `git diff --check` | PASS | no whitespace errors |
| `git diff --cached --check` | PASS | no staged whitespace errors at validation time |
| Production/rankings/app/source restrictions | PASS | all remain explicitly blocked; snapshots are review-only |

`PROSPECTIVE_2026_CHALLENGER_FREEZE.csv` is intentionally absent because the ridge failed non-compensable historical gates. A clean-worktree check is performed again after the local commit as the final closeout step; it cannot be truthfully represented as post-commit before that commit exists.
