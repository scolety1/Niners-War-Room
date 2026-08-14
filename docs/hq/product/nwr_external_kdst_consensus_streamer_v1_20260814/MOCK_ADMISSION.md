# Real Sleeper mock admission

Fantasy Gamers (`1312983576827920384`) remains a 10-team, 15-round, 1 K / 1 DEF league. Its owner `scolety` has no assigned Sleeper draft slot in the imported receipt.

No real mock was rerun: no authorized FantasyPros K/DST ECR data exists locally, and the offensive materiality gate remains blocked. The existing Redraft board still contains zero K/DST rows, so claiming K/DST search/select/draft, CPU completion, manual fallback, or a complete 15-round roster would be false.

When both gates are open, the next narrow implementation is to keep external K/DST rows in a separate ECR-only draft namespace, deplete them with the existing board state, and preserve NWR-only recommendations for QB/RB/WR/TE. It must not merge numerical scales.
