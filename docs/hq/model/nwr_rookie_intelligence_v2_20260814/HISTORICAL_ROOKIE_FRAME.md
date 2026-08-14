# Historical rookie frame

- Governed redraft outcome frame: 1,105 unique drafted QB/RB/WR/TE rows, classes 2012–2025, QB 161 / RB 298 / WR 448 / TE 198; SHA-256 `a02d77684bd0313ff59ed74665e5f87f76a5a1714799ed13aaaad4f1dd37a791`.
- Per-class counts for 2012–2025: 77, 79, 75, 78, 77, 83, 83, 80, 77, 75, 79, 80, 77, 85.
- 896 rows have a rookie stat row; 209 are genuine no-row zeros under that redraft contract; age is missing on 3 rows.
- Review-only dynasty labels: 919 rows, classes 2012–2024, QB 123 / RB 246 / WR 383 / TE 167; SHA-256 `6db401e1cbaf9a611d53061046006d40600fae335dac512e23539391f2aabeac`.
- All 919 labels join 1:1 to the outcome frame with age and draft capital complete. Every label is `review_only=true`, `model_use_allowed=false`, `training_allowed=false`.
- The expected 395-row 2021–2025 frozen Champion historical matrix is absent. The compatible-pack copy is header-only, SHA-256 `d7486d344d29ff5ae6b038a381f41ab034eef4932a2653a444858b66cd9424b2`.

Therefore exact Champion historical score, rank, confidence, tier separation, and promotion comparisons are `NOT_ENOUGH_INFORMATION`. Existing model_rd_v1 results are retrospective class holdouts, not outcome-maturity-safe rolling origin. Five-year results are descriptive only.
