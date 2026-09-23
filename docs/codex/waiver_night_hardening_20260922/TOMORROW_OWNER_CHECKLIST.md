# NWR — The One Remaining Step for Real ESPN Data (KHA and 403 N 18th)

Everything downstream of the actual Flaim fetch is built, tested, and verified tonight. This is the only remaining step, and it requires an authenticated session (you, or a future Claude/ChatGPT session with a completed Flaim login) — no more architecture work is needed after this.

## What's needed

For **each** of your two ESPN leagues (KHA and 403 N 18th, done separately, one at a time):

1. **Call exactly these 3 Flaim tools** (no others — `get_standings` and `get_transactions` are deliberately not authorized yet, per the existing capability governance):
   - `get_league_info` for the league
   - `get_roster` for your own team
   - `get_free_agents` (bounded, e.g. count=100 — do not claim it's the complete pool)

   League IDs and your team info:
   | League | ESPN League ID | Your Team ID | Your Team Name |
   |---|---|---|---|
   | 2026 KHA High Stakes League | `1298250946` | `4` | Colety Crusaders |
   | 403 N 18th and friends | `1009373442` | `5` | Spencer's Smart Team |

2. **Save the 3 raw responses into one JSON file**, shaped exactly like this (real field values, not placeholders):

```json
{
  "capture_schema": "nwr_espn_flaim_raw_capture_v1",
  "profile_id": "<the existing NWR profile id for this league>",
  "retrieved_at_utc": "<real UTC timestamp of the fetch>",
  "get_league_info": {
    "league_id": "1298250946", "league_name": "2026 KHA High Stakes League",
    "season": 2026, "team_count": 16, "owner_team_id": "4", "owner_team_name": "Colety Crusaders",
    "scoring_settings": [ /* whatever real scoring fields Flaim returns, mapped to an nwr_setting name where known */ ],
    "provider_as_of_utc": null
  },
  "get_roster": {
    "team_id": "4", "team_name": "Colety Crusaders",
    "players": [ /* real roster rows, with a real "slot": "STARTER"|"BENCH"|"RESERVE" */ ]
  },
  "get_free_agents": {
    "coverage": "BOUNDED",
    "bound_description": "First 100 rows returned by Flaim get_free_agents",
    "players": [ /* real free-agent rows */ ]
  }
}
```

   The `profile_id` for KHA is the existing local profile starting `fb1c4940...`; for 403 N 18th it's the one starting `4b4a990f...` — check `local_exports/redraft_v1/profiles/` in the worktree for the exact full IDs.

   **Important**: the exact field names above (`league_id`, `owner_team_id`, `slot`, etc.) are NWR's own capture contract, not a documented Flaim wire format — the importer only accepts this exact shape on purpose, so a real identity mistake can't slip through silently. You may need to rename fields from whatever Flaim's raw tool responses actually call them.

3. **Run the deterministic importer** (does zero network calls, zero provider writes):

```
python scripts/refresh_espn_flaim_snapshot.py \
  --profile-id fb1c4940... \
  --input path/to/kha_capture.json \
  --input-kind raw \
  --expected-provider-league-id 1298250946 \
  --expected-owner-team-id 4 \
  --expected-owner-team-name "Colety Crusaders"
```

   This runs in **preview mode by default** — it validates and shows you what would be written, without touching anything. Add `--activate` to actually write it (atomically, never overwriting the profile's other data, with a real backup of anything it replaces).

4. **Verify KHA live**: restart the Redraft dev backend, activate the KHA profile in the app, and confirm Start/Sit, Waivers, and K/DST Streamer now show real data instead of the "Verified league data required" message. If your league's exact scoring modifiers weren't fully captured by `get_league_info`, the app will correctly show scoring as PARTIAL/UNKNOWN rather than guessing — that's expected and honest, not a bug.

5. **Repeat exactly the same 4 steps for 403 N 18th.**

## What NOT to do

- Don't call `get_standings` or `get_transactions` yet — not authorized in the current governance scope.
- Don't hand-edit any existing profile JSON file directly.
- Don't commit the raw capture file or the resulting snapshot to git (both contain real private league data).
- Don't assume standard/PPR scoring for any field `get_league_info` didn't actually return.

No further code changes should be required for either league once a real snapshot is imported — this was verified end-to-end tonight using synthetic test fixtures with the exact same schema.
