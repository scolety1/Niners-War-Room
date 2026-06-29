# Historical Rookie Label Availability Audit - 2026-06-29

## Verdict

Historical rookie labels are not ready for an active rookie outcome build.

Primary blocker: existing historical rookie outcome work is prototype/review context, not an approved production label dataset.

## Questions Answered

### Do we have historical rookie classes?

Partially.

The repo contains historical rookie replay services, sample data, templates, and prior Model v4 docs covering 2021-2025 style replay work. However, the real production input paths used by the older services point to `local_exports`.

### Do we have player IDs bridging college/prospect to NFL player records?

Not in an approved way.

CFBD identity links are draft review-only. The registry has 213 candidates, all with `approved_by_human=false`.

### Do we have fantasy scoring by season?

Prototype yes, approved active source no.

The older rookie outcome label service uses RotoWire-derived player stats under `local_exports/model_v4/rotowire_intake/latest/rotowire_player_stats_clean_rows.csv`. That is not acceptable as source truth or active model/training input in this lane.

### Can we compute position finishes?

Not safely for active rookie outcomes from current approved artifacts.

Existing prototype labels use PPG-style outcome buckets and starter thresholds, not the requested T6/T12/T24/T36 seasonal position-finish targets.

### Can we compute rookie-year, year-2, first-3-year, first-5-year labels?

Not safely now.

Prior docs mention three-year replay maturity and partial 2024/2025 windows. A first-five-year label system is not present as an approved, censoring-safe artifact.

### Are recent classes censored for five-year outcomes?

Yes. Any recent class is immature for first-five-year labels. Censored classes must not be treated as misses.

### Can we avoid leakage?

A future design can avoid leakage, but no active build should proceed until source, identity, and label windows are explicit.

Prior services do join outcomes after scoring for review, but they are not enough to approve a new rookie outcome probability system.

### Can first-down scoring be included?

Not proven for the historical rookie label set.

If exact first-down-adjusted historical labels are unavailable, future labels must be marked as scoring approximation.

### Is there enough sample size by position?

Not established for the requested horizons.

Prior docs mention 395 historical rookie rows and 338 loaded outcome labels in prototype context, plus mature 2021-2023 subsets. That is useful R&D context, but it is not an approved sample-size analysis for T6/T12/T24/T36 rookie horizons.

## Existing Prototype Context

Prior research documents are useful:

- historical replay separated broad, strict starter, and difference-maker outcomes
- outcome maturity distinguishes mature 2021-2023 from partial 2024 and rookie-year-only 2025
- draft-capital-only and simple-hybrid baselines were compared
- outcomes were intended as display-only after scoring

Those are good design clues. They are not active approval.

## Required Before Label Generation

Future label work needs:

1. Approved historical rookie universe.
2. Approved college/prospect-to-NFL identity bridge.
3. Approved draft capital / NFL entry table.
4. Approved seasonal scoring data.
5. Position-finish label builder for T6/T12/T24/T36.
6. Censoring-safe first-3-year and first-5-year logic.
7. Missingness policy that preserves `Not enough information`.
8. Validation report before app display.

## Safe Conclusion

Do not build active rookie labels from the current sources.

The current evidence supports target design and blocker mapping only.
