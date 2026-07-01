# Blocked Sidecar Build Report

Decision: `BLOCKED_NO_ROW_LEVEL_SOURCE`

## Why the Sidecar Was Not Built

The requested row-level sidecar requires real tracked NFLVerse player_stats source rows. The current repo contains:

- a zero-row weekly player_stats template;
- dataset registry and coverage metadata;
- count-level overlap and label-parity packets;
- no tracked row-level weekly or seasonal player_stats source artifact.

Building `player_stats_sidecar_artifact.csv` anyway would create fake sidecar rows.

## Why Raw Shared Data Was Not Used

The allowed-source contract marks raw/shared exports as not allowed for this planning packet. This lane also does not have an approved runner/gate to read raw `C:\NWR_SHARED_DATA` directly.

## What Remains Needed

An approved runner or tracked source artifact must provide row-level NFLVerse player_stats rows with:

- player identity;
- season;
- week or seasonal grain;
- position;
- team;
- stat names and values;
- source artifact or snapshot metadata;
- source/as-of metadata;
- identity status.

## Current Blocker Status

- Sidecar artifact built: no.
- Sidecar rows created: 0.
- Unmatched rows computed: no.
- Scoring parity computed: no.
- Label truth promoted: no.
- Model/training/source-truth approval: no.
