# Sleeper integration recovery

Classification: **EXISTS_BUT_STALE**.

`src/services/sleeper_import_service.py` already supplied `SleeperHttpClient` and read-only league, users, rosters, drafts, scoring, roster-position and player snapshot handling. It had no user-to-roster owner flow, exact Redraft-profile mapper, field reconciliation, draft-candidate ambiguity protection, or active-draft pick reader.

`src/services/sleeper_redraft_owner_service.py` reuses that client only. It makes GET requests to league, user, roster, draft and draft-pick endpoints; it has no POST, PUT, PATCH, DELETE, browser automation, token use, or Sleeper mutation capability.
