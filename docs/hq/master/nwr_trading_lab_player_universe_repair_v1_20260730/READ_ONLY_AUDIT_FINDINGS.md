# Read-Only Audit Findings

The reported observation was correct. The prior `/trading-lab` page passed
`load_frozen_board().frame` into `build_trade_item_lookup`, so the current-player
selectors could expose only the 66 records in the frozen draft board.

The complete production authority already existed in the stable checkout:
`local_exports/model_v4/current_value/latest/full_player_board_value_review_rows.csv`.
Its manifest-governed SHA-256 is
`263cc8aa050c4670bf5ed22701d7b04801d143480c5630b98e00dd08d2968ce4`.

The smallest safe repair is source wiring plus contract enforcement and truthful
labeling: load the existing dynasty artifact for player selectors, keep the
frozen board for pick/draft context, enforce the 240-player identity/ownership
contract, and fail closed. No model or dataset change is required.
