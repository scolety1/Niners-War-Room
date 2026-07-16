# Route Authority Review

## Authority

`app/navigation.py` defines `ALL_NAVIGATION_PAGES`. `app/main.py` consumes the
same `NavigationPageSpec` objects and resolves their files with
`app_page_path`. The harness imports those production objects directly; it
does not maintain a second route table.

The live registry independently proves:

- `/rankings` targets `pages/20_final_board_v1.py`;
- `/player-board` targets `pages/20_final_board_v1.py`; and
- both aliases resolve inside `app/` to an existing file.

The resolver normalizes route names, rejects duplicate declarations, rejects
missing routes, resolves with the production helper, rejects targets escaping
`app/`, and requires an existing routed file before reading it.

## Negative revalidation

Wrong `/player-board`, wrong `/rankings`, missing `/player-board`, and missing
`/rankings` mutations all raised the expected assertions. Removing the routed
title or placing `Dynasty Rankings` only in unrelated source also failed.

Result: `PASS_LIVE_PRODUCTION_ROUTE_CONTRACT`.
