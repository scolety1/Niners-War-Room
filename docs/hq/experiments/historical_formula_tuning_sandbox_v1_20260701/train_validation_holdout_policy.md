# Train Validation Holdout Policy

Rows:

- Feature seasons: 2018-2024.
- Target seasons: 2019-2025.
- Evaluation seasons: 2021;2022;2023;2024;2025.

Candidate evaluation:

- Candidate formulas are fixed before metric review.
- For each target season and position, one-dimensional calibration uses only prior target seasons.
- Validation seasons: 2023;2024.
- Holdout season: 2025.
- Holdout is not used to choose weights or variants.

No production model training, production formula tuning, ranking changes, hidden sort, app wiring, or recommendations are created.
