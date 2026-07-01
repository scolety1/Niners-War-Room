# Rescue Variant Selection Decision

Decision label: `NO_SAFE_RESCUE_HOLD`

Selection policy:

- Variant definitions and thresholds were fixed before evaluation.
- Validation evidence was used to identify the best partial rescue.
- Holdout was evaluated once after definitions were fixed.
- Holdout was not used to define guard thresholds.

Best partial rescue: `qb_guard_soft_blend`.

Why it is not a full rescue:

- It reduces elite-QB severe regressions from `14` to `1`.
- It preserves validation and holdout MAE improvement versus the frozen V3 baseline.
- It keeps aggregate startable precision flat versus baseline.
- It does not reduce actual cutline hits moved below cutline: `8` -> `8`.

Conclusion: no rescue variant clears the full safety question. Keep the candidate held for human review.
