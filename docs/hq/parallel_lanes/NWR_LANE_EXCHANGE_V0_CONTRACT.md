# NWR Lane Exchange V0 Contract

Date: 2026-06-19

Owner: Master/Main HQ

Status: Phase 0 contract only. No lane is wired into this exchange yet.

## Purpose

The NWR Lane Exchange is a shared local-only hub for approved cross-lane data
snapshots. It exists so lanes can share approved outputs without inspecting
another lane's worktree, repo internals, or `local_exports` folders.

Producer lanes publish approved snapshot packages to the exchange. Consumer lanes
read packages only by manifest validation, including `sha256` and `row_count`
checks. No lane may scrape another lane's local repo or local exports as a
runtime dependency.

## Official Root

```text
C:\NWR_SHARED_DATA\lane_exchange\
```

This root is local-only and must remain outside all Git repositories. Data
snapshots, manifests, generated files, archives, and exchange state under this
root must not be committed to Git.

The local hub may also include a Master-owned local-only registry outside Git:

```text
C:\NWR_SHARED_DATA\lane_exchange_registry\lane_exchange_v0_registry.json
```

This is the only official Lane Exchange V0 registry path. A registry nested
under `C:\NWR_SHARED_DATA\lane_exchange\` is not official.

The registry is an operational index of lane/package ownership. The Master
contract remains the source of truth; the registry must not override this
document.

## Producer And Consumer Model

- Master/Main HQ owns this contract and approves changes to the exchange rules.
- Producer lanes own data creation, source quality, approval status, schema, and
  allowed-use labeling for the packages they publish.
- Consumer lanes validate manifests and file hashes before accepting any package.
- Mock Draft is a consumer for draft-day inputs.
- Drop Decision remains frozen. Any Drop Decision data used by the exchange must
  come only from already-approved or frozen outputs. This contract does not
  reopen Drop Decision work.

Consumers may use the exchange for read-only validation and approved downstream
workflows. They must not infer approval from file presence alone.

## Snapshot Concepts

- `latest_candidate`: the newest export from a producer lane. It is not trusted
  downstream and must not be used for draft decisions.
- `latest_approved`: an approved snapshot whose manifest, hash, row count, and
  allowed-use labels have passed the owning lane's approval gate.
- `pinned_live_snapshot`: a fixed manifest set for live draft mode. It freezes
  exact approved package versions so draft-day behavior is reproducible.

## Required Source Packages For Mock Draft Readiness

Mock Draft's minimum draft-ready input package uses these exchange package names:

```text
rookie_hq/frozen_rookie_mock_input
drop_decision/dropped_veterans
drop_decision/unavailable_players
league_state/pick_order
league_state/nwr_picks
model_value/veteran_private_values
market_behavior/display_only_market_context
```

`market_behavior/display_only_market_context` is optional for minimum manual
draft mode. If supplied, it may be used only for opponent behavior, availability,
and likely pick timing. It must never become NWR private value.

## Directory Structure

Each package has a source lane folder, package folder, immutable snapshot folders,
and pointer manifests:

```text
C:\NWR_SHARED_DATA\lane_exchange\<source_lane>\<package_name>\<timestamp_or_label>\
C:\NWR_SHARED_DATA\lane_exchange\<source_lane>\<package_name>\latest_candidate.json
C:\NWR_SHARED_DATA\lane_exchange\<source_lane>\<package_name>\latest_approved.json
```

Example:

```text
C:\NWR_SHARED_DATA\lane_exchange\rookie_hq\frozen_rookie_mock_input\20260619_approved\
C:\NWR_SHARED_DATA\lane_exchange\rookie_hq\frozen_rookie_mock_input\20260619_approved\manifest.json
C:\NWR_SHARED_DATA\lane_exchange\rookie_hq\frozen_rookie_mock_input\20260619_approved\rookie_2026_mock_draft_input.csv
C:\NWR_SHARED_DATA\lane_exchange\rookie_hq\frozen_rookie_mock_input\latest_candidate.json
C:\NWR_SHARED_DATA\lane_exchange\rookie_hq\frozen_rookie_mock_input\latest_approved.json
```

Pointer manifests should reference immutable snapshot folders. Consumers should
resolve a pointer, load the target manifest, validate it, and then validate the
referenced data file.

## Manifest Schema

Every snapshot manifest must include these fields:

```json
{
  "source_lane": "Rookie HQ",
  "source_repo": "C:\\NWR\\Niners-War-Room-rookies",
  "source_branch": "work/rookie-framework-path",
  "source_head": "7884d67...",
  "package_name": "rookie_hq/frozen_rookie_mock_input",
  "schema_version": "mock_draft_rookie_input_v1",
  "data_file": "rookie_2026_mock_draft_input.csv",
  "row_count": 55,
  "sha256": "<hex sha256>",
  "created_at": "2026-06-19T00:00:00-06:00",
  "approval_status": "approved",
  "approved_for": ["mock_draft_read_only_validation"],
  "allowed_use": ["draft_day_manual_review", "mock_draft_read_only_validation"],
  "forbidden_use": ["private_value_from_market", "simulation_without_live_pin"],
  "contains_private_value": true,
  "contains_market_data": false,
  "contains_adp": false,
  "notes": "Frozen rookie board approved by Rookie HQ."
}
```

Required field meanings:

- `source_lane`: human-readable owner lane name.
- `source_repo`: repo path that produced or approved the snapshot, if any.
- `source_branch`: branch used by the producing or approving lane.
- `source_head`: full or short commit hash used by the producing or approving
  lane.
- `package_name`: stable exchange package identifier.
- `schema_version`: versioned contract for expected columns and semantics.
- `data_file`: file name relative to the immutable snapshot folder.
- `row_count`: expected row count, including or excluding header as defined by
  the package schema.
- `sha256`: SHA256 hash of the data file.
- `created_at`: timestamp of snapshot creation.
- `approval_status`: `candidate`, `approved`, `rejected`, or `superseded`.
- `approved_for`: downstream workflows that may consume the package.
- `allowed_use`: explicit allowed uses.
- `forbidden_use`: explicit blocked uses.
- `contains_private_value`: whether the package carries NWR private value.
- `contains_market_data`: whether the package carries market context.
- `contains_adp`: whether the package carries ADP context.
- `notes`: human-readable source and approval notes.

## Safety Rules

- Consumers must not use `latest_candidate` for draft decisions.
- Live draft mode must use `pinned_live_snapshot` approved manifests.
- Every consumer must verify `sha256` and `row_count` before accepting a package.
- A manifest with `approval_status` other than `approved` must not be used for
  live draft decisions.
- Private value files must not include ADP, market rank, probability bands,
  hidden sort fields, external model leakage, promoted artifacts, or generated
  ranking/probability artifacts unless explicitly approved by Master.
- Market and ADP context must be display-only and clearly labeled in
  `allowed_use`, `forbidden_use`, `contains_market_data`, and `contains_adp`.
- ADP/market context may be used only for opponent behavior, availability, and
  likely pick timing. It must never become NWR private value or NWR ranking.
- No generated artifacts, data exchange snapshots, local exports, archives,
  `.env` files, caches, or real data files are committed to Git.
- Consumer lanes must fail closed if the manifest is missing, stale, malformed,
  unapproved, hash-mismatched, row-count-mismatched, or outside allowed use.
- Consumers must not inspect another lane's worktree or `local_exports` folder as
  a substitute for exchange manifests.

## Initial Implementation Roadmap

Phase 0: Master contract only.

- Create and review this contract.
- Do not create exchange data, producer scripts, consumer validators, or app
  wiring in this phase.

Phase 1: Mock Draft read-only validator for required packages.

- Add a Mock Draft validator that reads exchange manifests only.
- Validate required packages, hashes, row counts, approval status, allowed use,
  and market/private-value separation.
- Do not run simulations from exchange inputs in Phase 1.

Phase 2: Producer publish scripts per lane.

- Add producer-owned publish scripts only in the owning lanes.
- Scripts write local-only snapshots to `C:\NWR_SHARED_DATA\lane_exchange\`.
- Scripts produce immutable snapshot folders and pointer manifests.
- Producer lanes remain responsible for approval status.

Phase 3: Pinned live draft snapshot creation.

- Master creates or approves a pinned manifest set for live draft mode.
- Mock Draft consumes the pinned set rather than moving `latest_approved`
  pointers during the live draft.

Phase 4: Optional freshness/status dashboard.

- Add read-only status reporting for package freshness, approval, and validation
  failures.
- Dashboard must not mutate exchange state or produce draft decisions.

## Open Questions And Gates

- Who has final approval authority for the first `pinned_live_snapshot`: Tim,
  Master HQ, or both?
- Should row counts include the CSV header for every package, or should each
  schema define this explicitly?
- What is the first stable schema version for each Mock Draft package?
- Should `latest_approved.json` point to a snapshot manifest path or duplicate
  the full manifest contents?
- Should Drop Decision package publication be performed only from preserved
  approved outputs, since the lane remains frozen?
- What is the minimum manual fallback schema for dropped veterans and unavailable
  players if final producer exports are not ready before draft day?
- Should market behavior remain omitted from the first pinned live snapshot
  unless Tim explicitly provides a behavior-only source?
- What freshness warning should apply when a package was approved from archived
  laptop material rather than a current lane export?
- Should exchange writes require a Master approval note before a pointer can move
  from `latest_candidate` to `latest_approved`?

## Current Status

This V0 contract creates no data, no exchange directories, no publish scripts,
no validators, no app wiring, and no lane changes outside Master/Main docs.
