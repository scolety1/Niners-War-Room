# Player Board Route Contract Revision

## Live positive contract

`app.navigation.ALL_NAVIGATION_PAGES` is resolved with the repository-native
`app_page_path` helper. The live declarations prove:

- `/rankings` exists and targets `pages/20_final_board_v1.py`;
- `/player-board` exists and targets `pages/20_final_board_v1.py`; and
- both routed sources import `page_header` from
  `app.components.ui_framework` and call it once with `Dynasty Rankings` as the
  first literal argument.

The remaining current labels are exact AST string values in that routed owner.
Comments and unrelated files are excluded. The test no longer opens a fixed
implementation path independently of routing.

## Mutation controls

Disposable immutable route copies and source overrides prove failures for:

1. wrong `/player-board` target;
2. wrong `/rankings` target;
3. removed routed title;
4. title present only in an unrelated file;
5. missing `/rankings`; and
6. missing `/player-board`.

All six controls pass by observing the expected `AssertionError`. Production
navigation and page source remain untouched.
