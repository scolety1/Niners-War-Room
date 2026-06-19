# Trading Lab Integration Field Parity Audit - 2026-06-18

| Area | Current fixture field | Future real source candidate | Ready? | Gap | Approval before wiring |
|---|---|---|---|---|---|
| NWR private value | `nwr_value` | Approved NWR value output | Yes | Real source not wired | Required |
| Public fantasy market value | `public_market_value` | Approved public fantasy display source | Yes | Source freshness not wired | Required |
| Player asset | `asset_id`, `display_name`, `position`, `team_name`, `asset_type` | NWR/player identity source | Yes | Real identity mapping not wired | Required |
| Pick asset | `asset_id`, `display_name`, `rookie_pick_context`, `asset_type` | Rookie/Mock context source | Yes | Real pick mapping not wired | Required |
| Roster context | `roster_needs`, `surplus_tags`, `trade_style` | Approved roster context | Partial | Real roster state missing | Required |
| Keeper/drop | `keeper_status`, `drop_pressure_tag` | Keeper and Drop Decision context | Yes | Real keeper/drop feed not wired | Required |
| Rookie/mock context | `rookie_pick_context`, mock placeholder text | Rookie and Mock Draft context | Partial | Mock draft fields placeholder | Required |
| Opponent/team fit | `TeamContext`, `opponent_fit` score | Manual or approved opponent context | Yes | Private/manual context not wired | Required |
| Negotiation ladder | opening, fair, max, walk-away, counter notes | Fixture-generated review helper | Yes | Human calibration needed | Required |
| Warning/explanation | warning labels, risk labels, explanation fields | Fixture-generated review helper | Yes | Real provenance needed | Required |

## Current Status

All fields are fixture-only or placeholder. No real integration is approved by this audit.
