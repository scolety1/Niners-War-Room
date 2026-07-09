# Missingness and Coverage Audit

Coverage evidence:

- Weekly stats joined: 11,247 / 11,247.
- Snap counts joined: 11,219 / 11,247.
- Safe actual opportunity joined: 10,563 / 11,247.
- Static roster metadata joined: 1,167 / 1,167, with 70 conflict flags.

Missingness policy:

- Missing remains `Not enough information`.
- Missing snap count is not zero snaps or no-role.
- Missing weekly roster status is not inactive/off-roster unless separately proven.
- Missing opportunity component is not zero opportunity unless explicit source zero exists.
- Useful dashboard/display context is not proven accurate model input.

`weekly_rosters.csv` decision: valid season-week context, not current-only, when joined by approved season/week/player/team evidence. It is still review-only and not production/model approved.
