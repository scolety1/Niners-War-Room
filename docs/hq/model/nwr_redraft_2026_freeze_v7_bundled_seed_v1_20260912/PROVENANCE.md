# Freeze V7 bundled-seed packet -- provenance (2026-09-12)

This directory is the new canonical home for this worktree's default
bundled Redraft 2026 projection seed, referenced by
`src/application/desktop_facade.py`'s `REDRAFT_SEED_*` constants. It
replaces the prior default target (`docs/hq/model/
nwr_redraft_2026_rookie_projection_candidate_v1_20260809/`, 608 rows,
`source_sha256` `e483caae...`, `valid_until` 2026-09-09 -- independently
verified EXPIRED as of 2026-09-12, the date of this migration, with no
newer approval for that same 608-row artifact found anywhere in the repo).
That prior packet is left untouched (not deleted) -- still used directly
by `tests/test_redraft_profile_practical_mode_toggle.py`'s own hermetic
fixture, unrelated to this default.

## What this is

The real, owner-approved "Freeze V7" combined 2026 veteran+rookie
projection admission (491 veteran + 73 rookie = 564 total rows),
documented at `docs/codex/NWR_PROSPECTIVE_2026_FREEZE_V7_20260908.md` and
`docs/codex/NWR_NEXT_DRAFT_FINAL_BLOCKER_CLOSURE_LEDGER.md` (both already
present in this worktree's history -- commit `0ae4b039` and the Freeze V7
doc's own HEAD `b2555f095cd1e4e2b6b9b08754dba5cf2b1fdce9` are verified
ancestors of this branch's start HEAD via `git merge-base --is-ancestor`).

## Exact source of these 3 files

Copied byte-for-byte (only CRLF -> LF line-ending normalization applied --
see below) from the existing, untouched staging directory
`docs/codex/nwr_redraft_2026_rookie_projection_admission_CANDIDATE_v2_20260908/`:

| This directory | Copied from | Note |
|---|---|---|
| `GOVERNED_COMBINED_564_PROJECTION_SNAPSHOT.csv` | `MERGED_CURRENT_CANDIDATE.csv` | 564 data rows + header |
| `NWR_DATA_GOVERNANCE.json` | `MERGED_CURRENT_CANDIDATE.approval.json` | **verbatim content, unmodified** -- renamed only to match the filename `REDRAFT_SEED_APPROVAL_RELATIVE` expects |
| `BLOCKED_2026_ROOKIES.csv` | `BLOCKED_2026_ROOKIES.csv` | verbatim content, unmodified; 7 rows with `projection_status=BLOCKED` |

**No new approval was created or altered.** `NWR_DATA_GOVERNANCE.json`
here is an exact copy of the existing, already owner-issued receipt:
`approved_by: "Spencer Colety (owner, explicit chat authorization,
2026-09-08, 'NWR NEXT-DRAFT ROOKIE / INSUFFICIENT-HISTORY CLOSURE'
directive)"`, `approval_status: "APPROVED_FOR_REDRAFT_V1"`, `valid_until:
"2026-10-08"` (not expired as of this 2026-09-12 migration).

## Line-ending normalization (why the hash still matches)

This worktree's git config has `core.autocrlf=true`, and the source
staging directory (`docs/codex/.../CANDIDATE_v2_20260908/`) carries no
`.gitattributes` override, so Windows checkouts convert its `.csv`/`.json`
files' LF line endings to CRLF on disk. `install_projection_snapshot()`
hashes raw bytes on disk (`hashlib.sha256(source_path.read_bytes())`), so
a CRLF checkout would NOT match the receipt's own recorded
`source_sha256` (`b87c7296647b83a6103209a2995827766b7957a35270edb1624d7a
61102929f4`) -- verified directly: the as-checked-out CRLF bytes hash to
`6fc0b9a05db1ac7164ede1a33f2c780c13d945a852ae9d7c16a25ca9b7252712`, while
normalizing CRLF->LF reproduces the receipt's exact recorded hash. This is
a benign git-checkout artifact (identical byte CONTENT, only the
line-ending representation differs), not tampering or a modified
artifact -- the same pattern the existing bundled-seed directory already
solves via its own `.gitattributes` `text eol=lf` rule (line 18). This
packet's own `.gitattributes` entry applies the identical fix so the
checked-out file matches the approved hash on any machine, not just this
one.

Verified after normalization: `sha256(GOVERNED_COMBINED_564_PROJECTION_
SNAPSHOT.csv) == b87c7296647b83a6103209a2995827766b7957a35270edb1624d7a
61102929f4 == NWR_DATA_GOVERNANCE.json's own "source_sha256" field`.

## What did NOT change

No projection value, formula, model weight, scoring, roster-legality, or
`marginal_roster_utility` logic. This is a pure default-data-source swap
(`REDRAFT_SEED_*` constants in `desktop_facade.py`) from an expired
bundled seed to an already-owner-approved, still-valid one.
