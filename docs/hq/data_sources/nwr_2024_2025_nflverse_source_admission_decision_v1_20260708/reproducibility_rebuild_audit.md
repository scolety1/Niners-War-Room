# Reproducibility / Rebuild Audit

Raw local snapshot files are not tracked. Rebuild must use the approved nflverse safe refresh/scheduled ingest pattern already documented in prior HQ packets.

Known local snapshot root:

`C:\NWR_SHARED_DATA\scheduled_ingest\nflverse\player_context_display_final_20260630\`

Known advanced metrics cache root:

`C:\NWR_REVIEW\advanced_metrics_source_cache_20260707\`

Rules:

- Do not copy raw shared/cache files into the repo.
- Regenerate compact review artifacts only from approved runners/receipts.
- Preserve checksums in receipt audits where possible.
- Any future rebuild that changes rows or hashes requires a new human review packet.
