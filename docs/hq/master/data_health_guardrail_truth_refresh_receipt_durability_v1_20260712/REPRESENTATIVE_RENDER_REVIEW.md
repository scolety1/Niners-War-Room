# Representative Render Review

All render data is controlled synthetic metadata. Labels begin with `Synthetic fixture -` and do not represent live source health. Render evidence supplements, but does not replace, the automated tests.

## Desktop matrix

`rendered_evidence/synthetic_matrix_refresh_data_1440x1000_viewport.png`

The expanded canonical recovery table shows current success, partial success, failed latest with last-known-good, failed latest with no usable data, stale retained data, gated, unavailable, skipped, and not-enough-information together. The run is explicitly RED/partial rather than upgraded because one source succeeded. Latest receipt validation is shown separately from outcome truth.

## Compact expanded details

`rendered_evidence/synthetic_matrix_refresh_data_375x812_expanded.png`

At 375 by 812 pixels the validation text, latest-attempt role, opaque receipt ID, expanded passive recovery disclosure, and synthetic failure/stale/gated rows remain visible. The table can scroll horizontally without hiding the state classification from the data.

## Settings / Data Health guardrail

`rendered_evidence/synthetic_matrix_settings_data_health_1440x1000.png`

The representative Data Health surface shows an explicit overall blocked state and Review status for Refresh Data while preserving Ready statuses for unrelated areas. The durable receipt section is visibly subordinate to the existing Safe Data Loader controls and does not imply an automatic refresh.

## Invalid-state review

Controlled browser reload inspections also verified exact visible messages for missing (`No current outcome is inferred`), unsupported schema (`not trusted`), and corrupt latest (`not used as current truth`, followed by bounded quarantine). These states are mechanically covered by component/store tests; the retained image set is limited to the three non-duplicative representative renders above.
