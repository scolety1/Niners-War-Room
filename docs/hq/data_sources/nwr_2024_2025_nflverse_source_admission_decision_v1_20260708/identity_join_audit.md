# Identity Join Audit

Known join evidence preserved for human review:

- Scoped V0 weekly rows joined: 11,247 / 11,247
- Weekly stats joined: 11,247 / 11,247
- Snap counts joined: 11,219 / 11,247
- Safe actual opportunity joined: 10,563 / 11,247
- Static roster metadata joined: 1,167 / 1,167
- Static roster metadata conflict-flagged joins: 70

Policy decisions:

- Do not approve name-only joins.
- GSIS/player-id joins are acceptable as review-only evidence where prior packets show clean joins.
- Snap-count joins remain review-only where name/team/week caveats are involved.
- Static metadata is review-only because 70 conflict-flagged joins must remain visible to humans.
- PFR and ESPN identity bridges remain unsafe for admission because current evidence does not provide canonical historical NWR binding.
