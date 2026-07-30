# Player Source Authority

The sole current-player authority for Trading Lab is the existing Finished V1
production artifact loaded by `load_dynasty_rankings()`.

- Required release identifier: `NWR_FINISHED_VERSION_1`
- Required rows: 240
- Required SHA-256: `263cc8aa050c4670bf5ed22701d7b04801d143480c5630b98e00dd08d2968ce4`
- Identity: nonblank, unique `player_id`
- Required player fields: `player_id`, `player_name`, `position`, `nwr_rank`,
  and `pool_status`
- Approved ownership values: `MY TEAM`, `OTHER TEAM`

The 240-row contract is checked before lookup construction. An invalid bundle,
hash mismatch, missing schema, duplicate or blank identity, or unauthorized
ownership state stops player selection. No lower-authority fallback is allowed.
