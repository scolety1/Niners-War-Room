# Mock Draft Blank Input Template Packet

These are header-only templates for manually creating future local-only CSV
inputs. They contain no real player data and must not be treated as draft
outputs.

## Templates

`rookie_input`

```csv
asset_id,asset_type,nwr_private_value,player,position,source_status
```

`veteran_pool`

```csv
asset_id,availability_source,nfl_team,player,position,review_status
```

`pick_order`

```csv
current_owner,overall_pick,original_owner,pick_label,round,round_pick
```

`my_picks`

```csv
is_nwr_pick,overall_pick,owner,pick_label
```

`rosters_keepers`

```csv
keeper_status,player,position,team_id,team_name
```

`team_needs`

```csv
need_weight,position,team_id,team_name,tendency_note
```

`nwr_private_values`

```csv
asset_id,nwr_private_value,player,position,separation_note,value_source
```

`market_context`

```csv
allowed_use,asset_id,market_adp_pick,market_source,opponent_likelihood_signal,player,position,separation_note
```

## Manual Use

Create real files only in ignored local-only paths. Do not commit real inputs,
manifests, generated exports, or rows copied from local files. Keep market
context separate from NWR private values. No simulation may run from templates.
