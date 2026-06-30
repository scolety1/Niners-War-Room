# Rankings Preset Rendered Column Snapshots / HTML Notes

Screenshots were not captured for this packet to avoid bulky binaries. These snapshots are generated from the current `display_unified_player_board_frame` output and list rendered columns plus current row counts.

## Clean Board

- Intended job: Default full dynasty scan sorted by Dynasty Rank with market basics visible as display-only context.
- Rendered column count: 19
- Columns: Dynasty Rank | Player | Pos | NFL Team | Age | NWR Dynasty Score | DP 1QB Value (Market Baseline / Display-Only) | DP 1QB Market Rank (Market Baseline / Display-Only) | DP ECR Pos (Market Baseline / Display-Only) | DP Age (Market Baseline / Display-Only) | NWR vs Market Gap (Market Baseline / Display-Only) | Market Sanity Flag (Market Baseline / Display-Only) | Age Source | Market Baseline Label | Position Rank | Value Band (Review-Only) | Data Trust | Confidence | Main Caveat
- Row count before UI filters: 294
- First three row preview, first visible columns only:
```json
[
  {
    "Dynasty Rank": "1",
    "Player": "Puka Nacua",
    "Pos": "WR",
    "NFL Team": "LAR",
    "Age": "25.1",
    "NWR Dynasty Score": "83.0486",
    "DP 1QB Value (Market Baseline / Display-Only)": "9034",
    "DP 1QB Market Rank (Market Baseline / Display-Only)": "6.4"
  },
  {
    "Dynasty Rank": "2",
    "Player": "Jaxon Smith-Njigba",
    "Pos": "WR",
    "NFL Team": "SEA",
    "Age": "24.4",
    "NWR Dynasty Score": "82.5714",
    "DP 1QB Value (Market Baseline / Display-Only)": "9831",
    "DP 1QB Market Rank (Market Baseline / Display-Only)": "2.8"
  },
  {
    "Dynasty Rank": "3",
    "Player": "Bijan Robinson",
    "Pos": "RB",
    "NFL Team": "ATL",
    "Age": "24.4",
    "NWR Dynasty Score": "78.4618",
    "DP 1QB Value (Market Baseline / Display-Only)": "9536",
    "DP 1QB Market Rank (Market Baseline / Display-Only)": "4.1"
  }
]
```

## Market Analyzer

- Intended job: Evaluate DynastyProcess market context beside NWR dynasty board without changing sort or rank logic.
- Rendered column count: 19
- Columns: Dynasty Rank | Player | Pos | NFL Team | Age | NWR Dynasty Score | DP 1QB Value (Market Baseline / Display-Only) | DP 1QB Market Rank (Market Baseline / Display-Only) | DP ECR Pos (Market Baseline / Display-Only) | DP Age (Market Baseline / Display-Only) | NWR vs Market Gap (Market Baseline / Display-Only) | Market Sanity Flag (Market Baseline / Display-Only) | Age Source | Market Baseline Label | Position Rank | Value Band (Review-Only) | Data Trust | Confidence | Main Caveat
- Row count before UI filters: 294
- First three row preview, first visible columns only:
```json
[
  {
    "Dynasty Rank": "1",
    "Player": "Puka Nacua",
    "Pos": "WR",
    "NFL Team": "LAR",
    "Age": "25.1",
    "NWR Dynasty Score": "83.0486",
    "DP 1QB Value (Market Baseline / Display-Only)": "9034",
    "DP 1QB Market Rank (Market Baseline / Display-Only)": "6.4"
  },
  {
    "Dynasty Rank": "2",
    "Player": "Jaxon Smith-Njigba",
    "Pos": "WR",
    "NFL Team": "SEA",
    "Age": "24.4",
    "NWR Dynasty Score": "82.5714",
    "DP 1QB Value (Market Baseline / Display-Only)": "9831",
    "DP 1QB Market Rank (Market Baseline / Display-Only)": "2.8"
  },
  {
    "Dynasty Rank": "3",
    "Player": "Bijan Robinson",
    "Pos": "RB",
    "NFL Team": "ATL",
    "Age": "24.4",
    "NWR Dynasty Score": "78.4618",
    "DP 1QB Value (Market Baseline / Display-Only)": "9536",
    "DP 1QB Market Rank (Market Baseline / Display-Only)": "4.1"
  }
]
```

## Outcome Lens

- Intended job: Inspect approved/display-only Outcome V1/V2 and injury-context status for veterans where artifacts support it.
- Rendered column count: 70
- Columns: Dynasty Rank | Player | Pos | NFL Team | Age | NWR Dynasty Score | DP 1QB Value (Market Baseline / Display-Only) | DP 1QB Market Rank (Market Baseline / Display-Only) | DP ECR Pos (Market Baseline / Display-Only) | DP Age (Market Baseline / Display-Only) | NWR vs Market Gap (Market Baseline / Display-Only) | Market Sanity Flag (Market Baseline / Display-Only) | Age Source | Market Baseline Label | Position Rank | Outcome Availability (Display-Only) | QB T12 (Display-Only) | RB T12 (Display-Only) | RB T24 (Display-Only) | WR T12 (Display-Only) | WR T24 (Display-Only) | WR T36 (Display-Only) | TE T12 (Display-Only) | Outcome V2 Status (Display-Only) | Outcome V2 Availability Caveat | Outcome V2 Caveat | Injury Context Available | Availability Caveat | Limited Recent Sample | Last Materially Active Season | Seasons Since Material Activity | Not Enough Information Reason | QB T6 This Year (Outcome V2 / Display-Only) | QB T12 This Year (Outcome V2 / Display-Only) | RB T6 This Year (Outcome V2 / Display-Only) | RB T12 This Year (Outcome V2 / Display-Only) | RB T24 This Year (Outcome V2 / Display-Only) | RB T36 This Year (Outcome V2 / Display-Only) | WR T6 This Year (Outcome V2 / Display-Only) | WR T12 This Year (Outcome V2 / Display-Only) | WR T24 This Year (Outcome V2 / Display-Only) | WR T36 This Year (Outcome V2 / Display-Only) | TE T6 This Year (Outcome V2 / Display-Only) | TE T12 This Year (Outcome V2 / Display-Only) | QB T6 Next Year (Outcome V2 / Display-Only) | QB T12 Next Year (Outcome V2 / Display-Only) | RB T6 Next Year (Outcome V2 / Display-Only) | RB T12 Next Year (Outcome V2 / Display-Only) | RB T24 Next Year (Outcome V2 / Display-Only) | RB T36 Next Year (Outcome V2 / Display-Only) | WR T6 Next Year (Outcome V2 / Display-Only) | WR T12 Next Year (Outcome V2 / Display-Only) | WR T24 Next Year (Outcome V2 / Display-Only) | WR T36 Next Year (Outcome V2 / Display-Only) | TE T6 Next Year (Outcome V2 / Display-Only) | TE T12 Next Year (Outcome V2 / Display-Only) | QB T6 Within 5Y (Outcome V2 / Display-Only) | QB T12 Within 5Y (Outcome V2 / Display-Only) | RB T24 Within 5Y (Outcome V2 / Display-Only) | RB T36 Within 5Y (Outcome V2 / Display-Only) | WR T6 Within 5Y (Outcome V2 / Display-Only) | WR T12 Within 5Y (Outcome V2 / Display-Only) | WR T24 Within 5Y (Outcome V2 / Display-Only) | WR T36 Within 5Y (Outcome V2 / Display-Only) | TE T6 Within 5Y (Outcome V2 / Display-Only) | TE T12 Within 5Y (Outcome V2 / Display-Only) | Value Band (Review-Only) | Data Trust | Confidence | Main Caveat
- Row count before UI filters: 294
- First three row preview, first visible columns only:
```json
[
  {
    "Dynasty Rank": "1",
    "Player": "Puka Nacua",
    "Pos": "WR",
    "NFL Team": "LAR",
    "Age": "25.1",
    "NWR Dynasty Score": "83.0486",
    "DP 1QB Value (Market Baseline / Display-Only)": "9034",
    "DP 1QB Market Rank (Market Baseline / Display-Only)": "6.4"
  },
  {
    "Dynasty Rank": "2",
    "Player": "Jaxon Smith-Njigba",
    "Pos": "WR",
    "NFL Team": "SEA",
    "Age": "24.4",
    "NWR Dynasty Score": "82.5714",
    "DP 1QB Value (Market Baseline / Display-Only)": "9831",
    "DP 1QB Market Rank (Market Baseline / Display-Only)": "2.8"
  },
  {
    "Dynasty Rank": "3",
    "Player": "Bijan Robinson",
    "Pos": "RB",
    "NFL Team": "ATL",
    "Age": "24.4",
    "NWR Dynasty Score": "78.4618",
    "DP 1QB Value (Market Baseline / Display-Only)": "9536",
    "DP 1QB Market Rank (Market Baseline / Display-Only)": "4.1"
  }
]
```

## Data Review

- Intended job: Human-review lens for source coverage, confidence, caveats, risk notes, candidate status, and review flags.
- Rendered column count: 78
- Columns: Dynasty Rank | Tuned V2 Candidate Rank (Review-Only) | Tuned V2 Candidate Value (Review-Only) | Player | Pos | NFL Team | Age | Asset Type | Source Coverage | Final Board Rank | Final Tier | Position Rank | Value Band (Review-Only) | Confidence | Available-Pool ADP Range (Display-Only) | Current Pick Value (Display-Only) | Main Caveat | NWR Dynasty Score | DP 1QB Value (Market Baseline / Display-Only) | DP 1QB Market Rank (Market Baseline / Display-Only) | DP ECR Pos (Market Baseline / Display-Only) | DP Age (Market Baseline / Display-Only) | NWR vs Market Gap (Market Baseline / Display-Only) | Market Sanity Flag (Market Baseline / Display-Only) | Age Source | Market Baseline Label | Data Trust | Warnings | Status | Data Needed | Model Posture Used | Candidate Status | Risk Notes | Review Needed | QB T12 (Display-Only) | RB T12 (Display-Only) | RB T24 (Display-Only) | WR T12 (Display-Only) | WR T24 (Display-Only) | WR T36 (Display-Only) | TE T12 (Display-Only) | Outcome V2 Status (Display-Only) | Outcome V2 Availability Caveat | Outcome V2 Caveat | QB T6 This Year (Outcome V2 / Display-Only) | QB T12 This Year (Outcome V2 / Display-Only) | RB T6 This Year (Outcome V2 / Display-Only) | RB T12 This Year (Outcome V2 / Display-Only) | RB T24 This Year (Outcome V2 / Display-Only) | RB T36 This Year (Outcome V2 / Display-Only) | WR T6 This Year (Outcome V2 / Display-Only) | WR T12 This Year (Outcome V2 / Display-Only) | WR T24 This Year (Outcome V2 / Display-Only) | WR T36 This Year (Outcome V2 / Display-Only) | TE T6 This Year (Outcome V2 / Display-Only) | TE T12 This Year (Outcome V2 / Display-Only) | QB T6 Next Year (Outcome V2 / Display-Only) | QB T12 Next Year (Outcome V2 / Display-Only) | RB T6 Next Year (Outcome V2 / Display-Only) | RB T12 Next Year (Outcome V2 / Display-Only) | RB T24 Next Year (Outcome V2 / Display-Only) | RB T36 Next Year (Outcome V2 / Display-Only) | WR T6 Next Year (Outcome V2 / Display-Only) | WR T12 Next Year (Outcome V2 / Display-Only) | WR T24 Next Year (Outcome V2 / Display-Only) | WR T36 Next Year (Outcome V2 / Display-Only) | TE T6 Next Year (Outcome V2 / Display-Only) | TE T12 Next Year (Outcome V2 / Display-Only) | QB T6 Within 5Y (Outcome V2 / Display-Only) | QB T12 Within 5Y (Outcome V2 / Display-Only) | RB T24 Within 5Y (Outcome V2 / Display-Only) | RB T36 Within 5Y (Outcome V2 / Display-Only) | WR T6 Within 5Y (Outcome V2 / Display-Only) | WR T12 Within 5Y (Outcome V2 / Display-Only) | WR T24 Within 5Y (Outcome V2 / Display-Only) | WR T36 Within 5Y (Outcome V2 / Display-Only) | TE T6 Within 5Y (Outcome V2 / Display-Only) | TE T12 Within 5Y (Outcome V2 / Display-Only)
- Row count before UI filters: 294
- First three row preview, first visible columns only:
```json
[
  {
    "Dynasty Rank": "1",
    "Tuned V2 Candidate Rank (Review-Only)": "2",
    "Tuned V2 Candidate Value (Review-Only)": "83.55",
    "Player": "Puka Nacua",
    "Pos": "WR",
    "NFL Team": "LAR",
    "Age": "25.1",
    "Asset Type": "veteran"
  },
  {
    "Dynasty Rank": "2",
    "Tuned V2 Candidate Rank (Review-Only)": "1",
    "Tuned V2 Candidate Value (Review-Only)": "84.57",
    "Player": "Jaxon Smith-Njigba",
    "Pos": "WR",
    "NFL Team": "SEA",
    "Age": "24.4",
    "Asset Type": "veteran"
  },
  {
    "Dynasty Rank": "3",
    "Tuned V2 Candidate Rank (Review-Only)": "3",
    "Tuned V2 Candidate Value (Review-Only)": "79.96",
    "Player": "Bijan Robinson",
    "Pos": "RB",
    "NFL Team": "ATL",
    "Age": "24.4",
    "Asset Type": "veteran"
  }
]
```

## Compact Draft View

- Intended job: Fast-scan full dynasty board with review context pushed back and Dynasty Rank as default sort.
- Rendered column count: 11
- Columns: Dynasty Rank | Player | Pos | NFL Team | Age | NWR Dynasty Score | Position Rank | Value Band (Review-Only) | Data Trust | Confidence | Main Caveat
- Row count before UI filters: 294
- First three row preview, first visible columns only:
```json
[
  {
    "Dynasty Rank": "1",
    "Player": "Puka Nacua",
    "Pos": "WR",
    "NFL Team": "LAR",
    "Age": "25.1",
    "NWR Dynasty Score": "83.0486",
    "Position Rank": "WR1",
    "Value Band (Review-Only)": "Priority candidate"
  },
  {
    "Dynasty Rank": "2",
    "Player": "Jaxon Smith-Njigba",
    "Pos": "WR",
    "NFL Team": "SEA",
    "Age": "24.4",
    "NWR Dynasty Score": "82.5714",
    "Position Rank": "WR2",
    "Value Band (Review-Only)": "Priority candidate"
  },
  {
    "Dynasty Rank": "3",
    "Player": "Bijan Robinson",
    "Pos": "RB",
    "NFL Team": "ATL",
    "Age": "24.4",
    "NWR Dynasty Score": "78.4618",
    "Position Rank": "RB1",
    "Value Band (Review-Only)": "Priority candidate"
  }
]
```

