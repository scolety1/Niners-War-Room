# Source-to-Sink Revalidation

## Confirmed current-HQ path

1. `validate_frozen_board` requires 66 rows and visible fields but permits
   additional status aliases.
2. `normalize_board_frame` copies those additional columns into the selected
   Player Compare or Trading Lab row.
3. `build_decision_trust_strip` selects the aliases and calls
   `state_from_existing_status`.
4. Before the fix, affirmative substrings inside `not ready`, `not current`,
   `unmatched`, and `not scored` returned `VALID_CURRENT`.
5. `_summary_part` then replaced each contradictory source value with
   `Valid / current` in the collapsed operator-facing summary.

The safe prepatch PoC reproduced all four positive misclassifications. The
postpatch PoC maps them to fail-closed or identity-exception states and retains
all original values in the collapsed summary. `not valid`, which was already
nonpositive, remains nonpositive and visible.

## End-to-end regression

The security test constructs an otherwise valid fictional 66-row frozen board,
passes it through validation and normalization, selects the affected row,
builds its Decision Trust Strip, and checks the exact collapsed summary output.
No private, licensed, provider, or production data is used.

## Sink result

The component still hides detail only for a genuinely `VALID_CURRENT` state.
Every crafted negation now remains mechanically nonpositive, so source wording
is visible without expanding the disclosure.
