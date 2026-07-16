# Mutation Sensitivity Proof

All mutations use immutable `NavigationPageSpec` copies or in-memory source
overrides. Production source is never edited and reverted.

| Mutation | Expected failure | Observed | Restored state | Artifact/command |
|---|---|---|---|---|
| Wrong `/player-board` target | canonical target assertion | detected | route tuple discarded | `test_player_board_negative_control_rejects_wrong_player_board_route` |
| Wrong `/rankings` target | canonical target assertion | detected | route tuple discarded | `test_player_board_negative_control_rejects_wrong_rankings_route` |
| Comment-only trust call | exact AST call count zero | detected | source override discarded | `test_trust_negative_control_rejects_comment_only_call_reference` |
| Bannerless routed wrapper | exact AST call count zero on wrapper | detected | route tuple discarded | `test_trust_negative_control_rejects_routed_wrapper_without_banner` |
| All other required mutations | owning structural assertion | detected | override/copy discarded | `NEGATIVE_CONTROL_MATRIX.csv` |

Command:

`python -m pytest -q tests/test_player_board_ux_smoke_checklist.py tests/test_trust_banner_ui.py -k negative_control`

Observed result: `16 passed, 10 deselected`. Git diff inspection after the run
shows no application-source mutation. The three violations missed by the prior
review are explicitly covered by the first, third, and fourth rows above.
