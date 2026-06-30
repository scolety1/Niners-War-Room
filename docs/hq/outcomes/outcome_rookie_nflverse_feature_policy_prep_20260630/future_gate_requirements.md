# Future Gate Requirements

## Gates Required Before Any Model / Training Use

Every candidate feature family must pass:

1. source-policy gate;
2. identity binding gate;
3. schema and field semantics gate;
4. as-of/leakage gate;
5. missingness policy gate;
6. historical replay gate;
7. label parity gate where labels or player_stats sidecars are involved;
8. validation/calibration gate;
9. explicit user approval for model/training/source-truth promotion.

## Review-Only Candidates

Candidates that may be reviewed later:

- roster status;
- weekly roster status;
- injury report status;
- practice status;
- schedule context;
- depth chart role;
- snap recency;
- last active season/week;
- draft capital;
- combine;
- player_stats sidecar;
- identity bridge health;
- availability denominator fields.

## Not Model Eligible In This Packet

- contract context;
- games_missed_while_rostered;
- CFBD joins;
- UDFA status;
- `ff_rankings`.

## Suggested Next Lanes

1. `Outcome / Rookie NFLVerse Feature Policy Gate`
2. `NFLVerse Availability Denominator Definition Gate`
3. `Player Stats Sidecar Label Parity Gate`
4. `Rookie Drafted-Only Historical Replay Feasibility Gate`
5. `Depth Chart / Snap Recency Leakage Review`

No model build should start until a later lane explicitly approves model and
training flags.
