# Outcome Display Rules

- Outcome props are display-only evidence for the frozen final draft board.
- The frozen board remains the source of truth for rank, tier, score, and availability.
- Outcome fields must not create private value, sorting behavior, ranking behavior, or draft recommendations.
- Approved display columns only: QB T12, RB T12, RB T24, WR T12, WR T24, WR T36, TE T12.
- Join fallback used here is player name plus position because the frozen board does not include player_id.
- Rows with `match_status` other than `matched_name_position` require manual review.
- `final_board_rank_reference` is a board reference only and must not override `final_board_rank`.

