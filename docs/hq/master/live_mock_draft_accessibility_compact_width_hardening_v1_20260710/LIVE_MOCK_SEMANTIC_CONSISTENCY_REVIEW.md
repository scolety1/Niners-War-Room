# Live / Mock Semantic Consistency Review

Equivalent actions are rendered only by the shared workflow component and now use the same labels on both routes:

- `Assign selected player to pick`
- `Undo last assigned pick`
- `Remove player from assigned pick`
- `Show drafted players`
- `Filter and sort players`

Both routes expose the same selected-player, selected-pick, current-pick, current-team, draft-status, empty-table, and unavailable-action wording. Existing genuine differences remain: Live warns about real local live state; Mock identifies practice isolation and retains saved-session management. No behavior divergence was introduced.
