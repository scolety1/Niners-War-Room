# Stribling Incident

The frozen Rookie Review correctly refused an unsafe model-data identity join. The
product then converted that model-score block into the registry type `Blocked Rookie`,
and Desktop converted the type or any evidence reason into `AssetOption.blocked=true`.
Compare, Trade, Player Detail actions, and Draft Cockpit used that overloaded boolean
as selectability. Draft Cockpit also required a non-null rank and kept only twelve rows.

The result was the defect:

`official asset + no admitted score -> effectively unavailable during the draft`

Current governed evidence resolves De'Zhaun Stribling to `00-0041035`, SF, WR,
round 2, pick 33. The recovery retains stable asset ID
`blocked-rookie:dezhaun-stribling`, attaches the live ID as an alias, and leaves rank
and score null.
