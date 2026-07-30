# Player/Pick Source Separation

Current players come from the 240-row Finished V1 authority and use keys of the
form `player:id:<player_id>`.

Draft and pick context remains sourced from the frozen draft-day lane and uses
keys of the form `pick_context:<source identity>`. Player and pick keyspaces are
tested as disjoint even when a player display name resembles a pick label.

The frozen board has 66 rows and SHA-256 `0c6652e2b756a891af95bc208679aa6e426fd91f3e548329d75e97bf7bddce7e`. It is retained as
draft/pick context and is explicitly rejected as current-player authority.
Pick context remains descriptive; no standalone pick price or automatic package
value is inferred.
