# 5-21 UI Safety Checkpoint

Status: review-only app cleanup complete.

## Completed

- Created the 5-21 worksheet in Markdown and CSV form.
- Kept normalized league rank and ADP as review-only market context.
- Added a partial-market label so missing league rank or ADP cannot look like a normal edge.
- Reduced the Decision Board to fewer decision sections.
- Moved the top-five rule above the Decision Board tabs.
- Added visible Veteran Risk cards on the Decision Board.
- Added Player Board manual review notes, audit watchlist, TE no-premium review, and veteran/rushing-age review.
- Removed the draft-pool workflow from Player Board. Draft Room owns draft pool and mock-draft workflows.
- Combined Market Gap and Edge Finder into Trade Lab's Market Signals tab.
- Added a Command Center quick path.
- Documented remaining real data needs for route/snap, DOB, and injury history.

## Preserved Safety

- No formula changes.
- No active rankings changes.
- No My Team mutation.
- No War Board mutation.
- No readiness unlock.
- No app promotion.
- No fake route, age, injury, or snap evidence.

## Verification

- Focused navigation and market-gap tests passed.
- Ruff passed on touched files.
- Local app routes responded for Player Board, Draft Room, Decision Board, and Trade Lab.

## What The User Should Review First

1. Decision Board: confirm the top-five rule and roster pressure sections are understandable.
2. Player Board: inspect the big formula table and Manual Review Notes.
3. Player Board audit sections: review TE no-premium rows and aging/rushing-age rows.
4. Trade Lab: inspect Market Signals for disagreement context, remembering it is not private value.
5. Draft Room: use this for draft pool and mock-draft work, not Player Board.
