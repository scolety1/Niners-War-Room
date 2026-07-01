# Return / Special TD Blocker Report

Direct `return_touchdowns` and direct `special_touchdowns` remain blocked. NFLVerse `special_teams_tds` cannot safely feed both return TD and special TD scoring buckets without double counting or subtype ambiguity.

Compact V1 uses only `return_or_special_touchdowns` as a single 4-point composite review component. That is useful for observed-row review but not enough for return-vs-special subtype parity.

Current status: `return_special_td_parity_ready=false` for every matrix row.
