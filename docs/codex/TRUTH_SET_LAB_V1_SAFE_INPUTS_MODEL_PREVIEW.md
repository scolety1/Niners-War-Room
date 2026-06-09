# Truth Set Lab v1 Safe Inputs Model Preview

This preview applies only approved Truth Set Lab fields to the stats-first preview pipeline. It does not overwrite active rankings or unlock gates.

## Outputs

- Preview folder: `C:\Dev\niners-war-room\local_exports\nflverse_model_previews\truth_set_safe_inputs_20260515T042925`
- Model outputs: `C:\Dev\niners-war-room\local_exports\nflverse_model_previews\truth_set_safe_inputs_20260515T042925\stats_first_veteran_model_preview_outputs.csv`
- Contribution receipts: `C:\Dev\niners-war-room\local_exports\nflverse_model_previews\truth_set_safe_inputs_20260515T042925\stats_first_feature_contributions.csv`
- Normalized features: `C:\Dev\niners-war-room\local_exports\nflverse_model_previews\truth_set_safe_inputs_20260515T042925\stats_first_normalized_features.csv`
- Before/after comparison: `C:\Dev\niners-war-room\local_exports\nflverse_model_previews\truth_set_safe_inputs_20260515T042925\truth_set_safe_preview_comparison.csv`
- Source usage/rejection log: `C:\Dev\niners-war-room\local_exports\nflverse_model_previews\truth_set_safe_inputs_20260515T042925\truth_set_safe_preview_source_log.csv`

## Summary

- Truth-set players: 40
- Truth-set rows overlayed: 40
- Projection rows applied: 37
- Young bridge rows applied: 20
- Market context rows applied: 5
- Rejected production rows: 40
- Large value-change rows: 0

## Projection Quality Flags

Projection quality flags are retained in the safe preview source log and receipt inputs. They are review signals only and do not unlock decision-ready status.

- Missing first-down projection flags: 40
- Missing offensive projection flags: 3
- Team-mismatch flags: 3
- High-active-value missing-projection flags: 0

Known projection team mismatches:

- David Montgomery: projection `HOU`, active model `DET`
- Romeo Doubs: projection `NE`, active model `GB`
- Wan'Dale Robinson: projection `TEN`, active model `NYG`

## Young Bridge Gap Fill

The sixth-report gap-fill controls for Jahmyr Gibbs, Ashton Jeanty, and Brock Bowers are now present in the preview source. Only factual draft year, round, pick, team, and source URLs were added; college production and athletic testing remain blank/review-only for those gap-fill rows.

## Guardrails

- Rejected production fields are not imported.
- Unsafe RB role text is not imported as numeric workload data.
- Market rows are trade context only.
- Injury rows are confidence/context only.
- Active app rankings remain review-only.
