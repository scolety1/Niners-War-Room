# CFBD Identity Matching V1 Method

## Source Inputs Used

- `docs/hq/data_sources/cfbd_review_artifacts_20260624/cfbd_player_identity_review_queue.csv`
- Unified player universe review/consolidated review artifacts
- Sleeper current-context status artifact
- Player ID coverage audit and manual identity review queue
- DynastyProcess display-only crosswalk audit
- Frozen Final Draft Board V1 as display-only identity context
- Sample 2026 pre-declaration `dim_players.csv` reference rows

## Candidate Source Counts

- dynastyprocess_display_crosswalk: 330 candidate rows
- frozen_final_board_v1: 66 candidate rows
- player_id_coverage_audit: 388 candidate rows
- player_identity_manual_review_queue: 18 candidate rows
- sample_2026_pre_declaration_dim_players: 24 candidate rows
- sleeper_current_context: 129 candidate rows
- unified_player_universe_consolidated: 347 candidate rows
- unified_player_universe_review: 347 candidate rows

## Normalization Rules

- Unicode text is converted to ASCII where possible.
- Ampersands are normalized to `and`.
- Suffixes `Jr.`, `Sr.`, `II`, `III`, `IV`, and `V` are removed for matching.
- Punctuation, apostrophes, hyphens, whitespace, and symbols are removed.
- Names are lowercased and compared as compact normalized strings.
- Existing aliases for `KC Concepcion` and `Nick Singleton` are preserved.

## Scoring Rules

- Exact normalized name and compatible position: name score `100`.
- Exact normalized name with position mismatch or missing position context: name score `95`.
- Fuzzy fallback uses Python `SequenceMatcher` among same-position, same-first-letter candidates.
- Fuzzy candidates below score `88` are treated as unmatched.

## Match Status And Confidence

- `exact_match` / `HIGH`: one identity candidate, exact normalized name, compatible position.
- `strong_candidate` / `MEDIUM`: one strong candidate requiring review.
- `possible_candidate` / `LOW`: fuzzy candidate requiring review.
- `ambiguous` / `MEDIUM` or `LOW`: multiple plausible identities require review.
- `unmatched_review_required` / `UNKNOWN`: no candidate reached threshold.

## Review-Only Guardrail

All outputs are review-only identity suggestions. They are not source truth, not model input,
not training truth, and not candidate/rank outputs. Even `HIGH` confidence rows require human
review before any future promotion.

## Known Limitations

- CFBD college team is not directly comparable to current NFL team for most candidates.
- Transfer history and draft-year context are not resolved in V1.
- Matching uses existing tracked artifacts only and does not repull CFBD or Sleeper.
- Ambiguous common names remain intentionally visible for human review.
