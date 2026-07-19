# Persistent data root contract

The per-user root is `%LOCALAPPDATA%\NinersWarRoom`; `NWR_DATA_HOME` is accepted only as an explicit test/maintenance override. Children are `data`, `backups`, `logs`, `run`, `browser-profile`, and `config`.

Existing approved stable roots are reused when present: `C:\NWR_SHARED_DATA\draft_runtime_state` and `C:\NWR_SHARED_DATA\development_lab_state`. The launcher sets their existing environment variables. Repository-relative `local_exports\refresh_data` and `local_exports\mock_drafts` have no accepted path override, so the launcher creates and validates exact directory junctions to the per-user `data` children. A populated non-junction or wrong-target junction stops with a migration conflict. No LocalData, credentials, provider tokens, licensed exports, CSV inputs, or fixtures enter this root.
