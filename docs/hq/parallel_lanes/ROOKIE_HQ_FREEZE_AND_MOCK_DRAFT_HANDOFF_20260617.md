# Rookie HQ Freeze And Mock Draft Handoff

## Scope

This is a Master/Main HQ record of Rookie HQ paused/frozen status and approval
to proceed in a separate Mock Draft HQ/lane. It does not modify Rookie files,
app behavior, production rankings, Outcome behavior, veteran logic, promoted
artifacts, probabilities, bands, hidden sort keys, `data/`, or `local_exports/`.

## Rookie HQ Status

Rookie HQ is paused/frozen after the final manual draft kit post-fill runway.

Rookie repo:

```text
C:\Users\smcol\Documents\Vacation\Niners-War-Room-rookies
```

Rookie branch:

```text
work/rookie-framework-path
```

Final Rookie commit recorded:

```text
07d27b70aaa30f2e637733c5f19d3ac6ca0c7777
```

Expected Rookie git status:

```text
?? data/
```

Do not stage or commit `data/`.

## Final Rookie Quality Status

- Final kit quality: GREEN
- Mock Draft rookie input readiness: GREEN
- Preview/readability: GREEN
- Data integrity: GREEN
- Anti-cheat/leakage: GREEN
- Manual draft trust: YELLOW

Manual draft trust remains YELLOW because some display-only fields still have
`needs_data`.

## Final Rookie Artifacts

Preview:

```text
local_exports/rookie_framework/final_post_fill_runway_20260616/preview/index.html
```

Final rookie board:

```text
local_exports/rookie_framework/final_post_fill_runway_20260616/rookie_2026_final_manual_draft_board_post_fill_runway_20260616.csv
```

Mock Draft rookie input:

```text
local_exports/rookie_framework/final_post_fill_runway_20260616/rookie_2026_mock_draft_input_20260616.csv
```

Missing-data templates:

```text
local_exports/rookie_framework/final_post_fill_runway_20260616/missing_data_templates/
```

## Final Display/Data-Fill Commits After Final Kit Freeze

- `19a117a5ec4a32ab647c0e1ef4809cbdd00bcf97` - stat enrichment
- `0aadbe3ba83d6dadfb103bec4f3eb96d2e326186` - display cleanup
- `ac84f7fc71d379a658cbbd287f48734afa7a1fd2` - local display data fill
- `6fba96d9a08f635e19aeee2fe38599691a52dc99` - final post-fill runway / Mock Draft input handoff
- `07d27b70aaa30f2e637733c5f19d3ac6ca0c7777` - Rookie pause and Mock Draft handoff prompts

## Display Field Coverage

- ADP / Market: 46/54 populated, 8 `needs_data`
- NFL Team: 46/54 populated, 8 `needs_data`
- Age: 27/54 populated, 27 `needs_data`
- Depth Chart / Role: 11/54 populated, 43 `needs_data`
- NFL Draft Capital: 54/54 populated

## Rookie Guardrails

- Formula unchanged: `cfbd_enriched_baseline_v1_1`
- Board order unchanged
- Rookie artifacts are manual-use inputs only
- Rookie artifacts are not production/app rankings
- ADP/market is display-only and must not affect NWR private/model quality
- No production/app/outcome/veteran contamination occurred
- No probabilities, bands, hidden sort keys, or promoted artifacts were created

## Reopen Conditions

Reopen Rookie HQ only if explicitly requested for:

- factual correction
- player update
- broken export
- push/backup request
- later explicit production integration request

## Mock Draft HQ / Lane Approval

Approved: open a separate Mock Draft HQ/lane.

Mock Draft HQ should use:

```text
local_exports/rookie_framework/final_post_fill_runway_20260616/rookie_2026_mock_draft_input_20260616.csv
```

Mock Draft HQ must treat that file as:

- manual-use rookie input only
- not production rankings
- not app rankings
- not a new Rookie model
- not a hidden sort key source
- not a source of probabilities/bands unless separately approved later

## Master HQ Confirmation

Rookie outputs are manual-use only and not production rankings. Mock Draft work
must remain separate from Rookie HQ unless HQ explicitly approves reopening
Rookie for one of the listed reopen conditions.
