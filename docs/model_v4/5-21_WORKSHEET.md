# 5-21 Worksheet

Purpose: turn the May 21 formula-safety and app-UX audits into concrete prompts and implementation tasks. This sheet is intentionally review-only: it should improve clarity, safety, and workflow without changing formulas, active rankings, My Team, War Board, or readiness gates.

Implementation status:
- Prompts 1-7 have safe app/documentation upgrades in place.
- Remaining true data upgrades require new admitted sources for route/snap detail, DOB, and injury history.
- Player Board now stays focused on the formula table; draft-pool work belongs in Draft Room.
- Trade Lab now groups normalized market gap and model-vs-market edges under Market Signals.

## Prompt 1: Market-Gap Safety Cleanup

Use the May 21 safety audit to harden the normalized league-rank and ADP review layer.

Tasks:
- Keep league-rank and ADP normalization as context only.
- Ensure partial market context does not create normal buy/sell watch labels.
- Add short display labels for long market-gap codes.
- Keep formal machine-readable labels in data outputs.
- Make missing ADP/rank warnings prominent.
- Run market-gap tests and navigation compile tests.

Constraints:
- Do not let market, ADP, ranking, projection, mock, or consensus fields drive private football value.
- Do not mutate active rankings, My Team, War Board, or readiness gates.

## Prompt 2: Decision Board UX Cleanup

Use the app audit to make the June 15 Decision Board easier to understand.

Tasks:
- Keep the top-five rule visible as the first section.
- Reduce the internal tab count into fewer decision sections.
- Rename vague labels into plain English.
- Keep warnings and receipts under Advanced.
- Add a compact audit-notes explainer for route gaps, aging-risk gaps, TE no-premium context, and market context.

Constraints:
- No final cut/keep/trade/draft recommendations.
- Review-only outputs only.

## Prompt 3: Player Board Human-Readable Formula Table

Make the Player Board the main readable player table.

Tasks:
- Keep search, position, and owner visible.
- Move low-use filters into Advanced Filters.
- Add plain-English manual-review notes for warning codes.
- Add an audit watchlist for route/snap gaps, age guardrails, TE no-premium checks, first-down gaps, and missingness.
- Keep market columns visibly labeled as context only.

Constraints:
- Do not hide receipts permanently; keep them in advanced sections.
- Do not change formula outputs.

## Prompt 4: TE No-Premium Interpretation Pass

Make TE values harder to misread in the app.

Tasks:
- Add visible notes that TE scores are no-premium VORP values.
- Flag TE rows with no-premium caps or route/target missingness for manual review.
- Keep Brock Bowers, Travis Kelce, and George Kittle as named sanity examples in documentation or review notes.

Constraints:
- Do not manually tune TE scores to match preference.
- Do not add TE premium logic.

## Prompt 5: Aging And Rushing-Age Manual Review Pass

Make aging-risk warnings visible where decisions happen.

Tasks:
- Surface RB age-cliff and QB rushing-age guardrail warnings in Player Board and Decision Board.
- Ensure players such as Christian McCaffrey, Travis Kelce, George Kittle, and Lamar Jackson remain easy to inspect.
- Create or update a veteran risk review surface if needed.

Constraints:
- Do not fabricate DOB, injury, route, or athletic evidence.
- Missing age/injury evidence should remain a confidence/manual-review warning.

## Prompt 6: Route/Target/Snap Data Gap Plan

Plan the route/target/snap improvement without fake data.

Tasks:
- Inventory which current outputs carry `licensed_route_metrics_not_available` or `missing_or_review_route_target_snap_evidence`.
- Document which positions are most affected.
- Create a source plan for admitted route participation, routes run, target share, TPRR, or snap evidence if licensed exports become available.

Constraints:
- Do not estimate route metrics and label them as real.
- Do not allow review-only route context to drive private value.

## Prompt 7: Final Human Review Readiness Check

After the UI and safety cleanup, run a final local check.

Tasks:
- Run focused tests.
- Run Ruff on touched files.
- Open the app and inspect Decision Board, Player Board, Trade Lab, Draft Room, and Settings.
- Confirm review-only status and no active-data mutation.

Expected output:
- Short checkpoint doc with what changed, what remains manual, and what the user should review first.
