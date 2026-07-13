# Validation Results

## Repository, remote, and ancestry

- Fetch all remotes with prune: PASS.
- Expected live HQ: `00fc89ed95f0b2b06c43d0acd28b4c0181647a30`.
- Actual starting live HQ: `00fc89ed95f0b2b06c43d0acd28b4c0181647a30`.
- Remote advance: PASS; zero commits and no intervening diff.
- Source parent and merge base equal verified HQ: PASS.
- Blocked-review parent is the source commit; merge base is verified HQ: PASS.
- Remote containment for source commit: PASS; zero remote branches.
- Remote containment for blocked-review commit: PASS; zero remote branches.
- Stable-ID revision worktree: PASS; clean and no correction commit.
- New isolated closeout worktree from verified HQ: PASS.

## Unsafe source exclusion

- Unsafe source commit inventory: PASS; 11 paths reconciled.
- Live-HQ Trading Lab page blob equals source parent: PASS.
- Saved-scenario service in HQ: absent.
- Saved-scenario tests and fixtures in HQ: absent.
- Saved-scenario session/runtime namespace in HQ: absent.
- Saved-scenario import/export behavior in HQ: absent.
- Unsafe source packet in HQ: absent.
- Blocked-review packet in HQ: absent.
- Tracked runtime store/backup/corrupt files: zero.
- Default external runtime root on validating host: absent.
- Runtime-root environment override: unset.
- Production migration/rollback required: no.

## Stable identifier and prohibited-field reconciliation

| Asset type | Selectable | Direct stable admitted IDs | Result |
|---|---:|---:|---|
| Rookie players | 54 | 0 | `0/54` |
| Dropped veterans | 12 | 0 | `0/12` |
| Pick-context assets | 54 | 0 | `0/54` |
| Total | 120 | 0 | `0/120` |

The 66 player-board rows reconcile to 54 rookies and 12 dropped veterans. The pick-context input
contains 54 rows. Direct stable admitted identifier columns are absent. Existing key-like values
are composite presentation keys and do not count.

Prohibited composite fields reconcile exactly to final-board rank, player name, position, and NFL
team. The schema-prefix review confirms version `1` accepts `player:` and `pick_context:` tokens.
Import/export therefore fails the privacy and persistence allowlist.

## Packet and scope validation

- Required file names and count: PASS; 13 of 13.
- Documentation-only changed paths: PASS.
- CSV parsing: PASS.
- Duplicate CSV primary keys: PASS; zero duplicates.
- Manifest JSON parsing: PASS.
- Duplicate manifest JSON keys: PASS; zero duplicates.
- Manifest path/file-count/hash/byte validation excluding self: PASS.
- Reentry status and all 15 triggers: PASS.
- No-recreate rules: PASS.
- Privacy and rights scan: PASS; no credentials, private locators, provider payloads, rights
  grants, or new persistence authority.
- Protected application/source/ranking/formula/plugin/rookie/production/draft changes: zero.
- Starting-HQ frozen inventory: 122 paths.
- Frozen-artifact byte/object mismatches: zero.
- Application behavior changes: zero.
- `git diff --check`: PASS.
- `git diff --cached --check`: PASS after staging.

## Post-commit gate

A commit cannot canonically contain its own SHA or attest a later remote readback. Final
non-force push, remote-HQ readback, `0 ahead / 0 behind`, and clean-worktree results are reported
with the final handoff after they execute.
