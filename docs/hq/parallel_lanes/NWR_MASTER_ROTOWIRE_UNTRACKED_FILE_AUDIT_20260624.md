# NWR Master RotoWire Untracked File Audit

Date: 2026-06-24

## Summary

Master was synced with origin at `80ab3b93da8e8dfaa6883a4d13a67ec1f720bb56`, but the working tree contained pre-existing untracked RotoWire-related files. These files were audited by path, extension, size, and filename/header secret-pattern scan only. No sensitive contents were printed.

All untracked RotoWire files were preserved outside the repository at:

`C:\NWR_LOCAL_ARCHIVE\rotowire_untracked_quarantine_20260624\`

No raw RotoWire/vendor files were committed. No app code, model logic, rank files, frozen board files, latest files, pinned files, runtime state, `local_exports`, or `C:\NWR_SHARED_DATA` files were changed or tracked.

## Files Found

| Path | Size bytes | Type | Likely purpose | Risk classification | Action |
|---|---:|---|---|---|---|
| `docs/hq/data_sources/rotowire_usage/NWR_ROTOWIRE_USAGE_FIELD_ALLOWLIST_V0_20260624.csv` | 3,078 | `.csv` | Candidate allowlist/schema research | Safe research artifact, not raw vendor dump by filename/header scan | Moved to quarantine |
| `docs/hq/data_sources/rotowire_usage/NWR_ROTOWIRE_USAGE_FIELD_BLOCKLIST_V0_20260624.csv` | 1,945 | `.csv` | Candidate blocklist/schema research | Safe research artifact, not raw vendor dump by filename/header scan | Moved to quarantine |
| `docs/hq/data_sources/rotowire_usage/NWR_ROTOWIRE_USAGE_LIVE_PULL_BLOCKED_SUMMARY_20260624.csv` | 711 | `.csv` | Blocked live-pull summary | Safe research artifact; indicates blocked/manual posture | Moved to quarantine |
| `docs/hq/data_sources/rotowire_usage/NWR_ROTOWIRE_USAGE_SCRAPER_README_V0_20260624.md` | 1,886 | `.md` | Candidate scraper/readme notes | Safe docs by filename/header scan | Moved to quarantine |
| `docs/hq/data_sources/rotowire_usage/NWR_ROTOWIRE_USAGE_SOURCE_CONTRACT_V0_20260624.md` | 3,400 | `.md` | Candidate source contract | Safe docs by filename/header scan | Moved to quarantine |
| `scripts/rotowire_usage_pull_research.py` | 3,103 | `.py` | Candidate research pull script | Code artifact; not raw vendor dump by filename/header scan | Moved to quarantine |
| `src/services/rotowire_usage_schema_service.py` | 5,879 | `.py` | Candidate schema service | Code artifact; not app-wired while untracked | Moved to quarantine |
| `src/services/rotowire_usage_validation_service.py` | 5,821 | `.py` | Candidate validation service | Code artifact; not app-wired while untracked | Moved to quarantine |
| `tests/test_rotowire_usage_validation_service.py` | 6,131 | `.py` | Candidate validation tests | Test artifact | Moved to quarantine |

## Safe Docs Worth Preserving

The following docs appear useful as local research context and were preserved in quarantine instead of being committed to Master:

- `NWR_ROTOWIRE_USAGE_SCRAPER_README_V0_20260624.md`
- `NWR_ROTOWIRE_USAGE_SOURCE_CONTRACT_V0_20260624.md`
- `NWR_ROTOWIRE_USAGE_FIELD_ALLOWLIST_V0_20260624.csv`
- `NWR_ROTOWIRE_USAGE_FIELD_BLOCKLIST_V0_20260624.csv`
- `NWR_ROTOWIRE_USAGE_LIVE_PULL_BLOCKED_SUMMARY_20260624.csv`

They should be reintroduced only through the dedicated RotoWire source-repair lane after validation and guardrail review.

## Secrets and Raw Vendor Scan

- Filename/header secret marker scan: no hits.
- API keys, tokens, credentials, or authorization markers detected by filename/header scan: no.
- Raw vendor dumps detected by filename/header scan: no.
- Full content was not printed or exposed.

## Ignore Policy

No new `.gitignore` patterns were added in this audit. The quarantined files now live outside the repository, and broad ignores for `scripts/`, `src/services/`, `tests/`, or `docs/hq/data_sources/` would hide legitimate future review work. Existing ignore rules already cover `local_exports/`, runtime state folders, temporary files, and local data directories.

If the RotoWire lane later produces raw/vendor outputs, those outputs must be kept outside the repo or placed under an already ignored local output path. Candidate docs/code must return through a reviewed branch and must not be hidden by broad ignore rules.

## Action Taken

1. Ran `git status --short`.
2. Identified every untracked RotoWire-related file.
3. Recorded file path, size, type, likely purpose, and risk classification.
4. Performed filename/header secret marker scan without printing sensitive contents.
5. Moved all untracked RotoWire-related files to:
   `C:\NWR_LOCAL_ARCHIVE\rotowire_untracked_quarantine_20260624\`
6. Left Master free of untracked RotoWire files.
7. Created this audit report as the only intended repository change.

## Final Status

- Anything committed by this audit: this report only.
- Raw/vendor files tracked: no.
- `C:\NWR_SHARED_DATA` tracked: no.
- `local_exports` tracked: no.
- Runtime JSON tracked: no.
- Secrets/API keys detected by filename/header scan: no.
- Master expected final status after report commit: clean and synced with origin.
