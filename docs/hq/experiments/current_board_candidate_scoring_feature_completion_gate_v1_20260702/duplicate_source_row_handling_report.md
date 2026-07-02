# Duplicate Source Row Handling Report

Raw 2025 REG rows before exact dedup: `37078`

Rows participating in exact duplicate groups: `37078`

Rows after exact dedup: `18539`

Duplicate player/season/week keys after exact dedup: `0`

Policy:

- Exact duplicate raw rows are collapsed before scoring.
- Non-exact duplicates would stop the gate.
- This gate does not infer or fill missing player-week rows.
