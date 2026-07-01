# Quarantined Fields Report

The compact derivation excludes every quarantined field from the admitted source receipt.

## Excluded Fields

`air_yards_share, fantasy_points, fantasy_points_ppr, headshot_url, pacr, passing_cpoe, passing_epa, racr, receiving_epa, rushing_epa, target_share, wopr`

## Included Fields

`passing_first_downs, rushing_first_downs, receiving_first_downs`

The included fields are review-allowed in the source-admission schema manifest.
Quarantined fields remain blocked from review sidecar rows, private value,
hidden sort, model, training, source truth, recommendations, trade value,
and pick value.
