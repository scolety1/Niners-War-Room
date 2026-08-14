# Sleeper → NWR profile mapping

| Sleeper | NWR | Status |
|---|---|---|
| 10 teams | `team_count=10` | exact |
| QB, 2 RB, 2 WR, TE, FLEX, K, DEF | `qb=1, rb=2, wr=2, te=1, flex=1, k=1, dst=1` | exact roster shape |
| six BN | `bench_size=6` | exact |
| no SUPER_FLEX, IR, taxi | `superflex=0`; no IR/taxi field | transformed/unsupported metadata |
| 15-round snake | `draft_type=snake, rounds=15` | exact |
| no draft order | `draft_slot=null` | exact unknown, not invented |
| no keepers on roster; max keepers 1 | `keeper_count=0` | exact current state |
| core offensive scoring | Redraft `ScoringSettings` | exact; see CSV |
| K/DST/defense/special teams scoring | no admissible current Redraft scorer | unsupported and blocking |

The imported local profile is isolated under `local_exports/redraft_v1`; it does not change any Dynasty artifact or model.
