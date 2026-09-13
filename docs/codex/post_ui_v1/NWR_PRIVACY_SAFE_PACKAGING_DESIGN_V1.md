# NWR Privacy-Safe Packaging Design V1

Worker B, `upgrade/nwr-post-ui-product-v1-20260912`, worktree
`C:\NWR\post-ui-product-v1`. Design for unblocking `npm run check:resources`
for the `redraft` desktop app without weakening the privacy guard, tampering
with governance history, or removing the human audit identity from the
canonical record.

## 1. The actual conflict (verified, not assumed)

`desktop/scripts/check-resource-allowlists.mjs` scans every file the Windows
Tauri bundle (`desktop/apps/redraft/src-tauri/tauri.windows.conf.json`)
declares as a packaged resource for a small set of real owner-identity
markers (`ownerMarkers`, includes `"Spencer Colety"`). The `redraft`
allowlist includes the bundled Freeze V7 governance receipt,
`docs/hq/model/nwr_redraft_2026_freeze_v7_bundled_seed_v1_20260912/
NWR_DATA_GOVERNANCE.json`. That receipt's own `approved_by` field legitimately
reads `"Spencer Colety (owner, explicit chat authorization, 2026-09-08,
...)"` -- a real, correct, already-approved audit-trail entry, not a defect.
The guard correctly refuses to let a file containing that string ship inside
a distributable installer. This is the guard doing its job; the fix is
architectural, not a guard change.

**Why the receipt is bundled at all (verified by reading the runtime, not
assumed):** `src/application/desktop_facade.py`'s
`_ensure_redraft_projection_seed()` performs a one-time, first-run install of
the bundled 2026 projection seed into the user's local Redraft store. It
reads two files relative to `self.repo_root`: the projection CSV and
`NWR_DATA_GOVERNANCE.json` (`REDRAFT_SEED_APPROVAL_RELATIVE`), and passes
both to `redraft_engine_v1_service.install_projection_snapshot(...)`, which
calls `_validate_approval_receipt(...)` -- a strict validator requiring
`schema_version`, `authority`, `approval_status`, `season`, `source_sha256`,
`source_id`, `approved_by`, `approved_at_utc`, `valid_until`, all non-empty/
well-formed, `approval_status`/`authority` matching the expected constants,
`source_sha256` binding the receipt to the exact projection artifact, and
`valid_until` not expired. In a **packaged** build,
`desktop/crates/nwr-desktop-runtime/src/lib.rs`'s `resolve_repo_root()`
resolves `self.repo_root` to Tauri's `resource_dir()` -- i.e. the bundled
resource tree is the *only* place this file can come from once installed on
a machine with no prior local Redraft store. That is why the full receipt
was ever a packaging candidate: the runtime genuinely needs *some* file at
that location to complete a fresh install.

**A second, previously-undiscovered instance of the same conflict, found
while reading this path:** `nwr-desktop-runtime`'s own release-build startup
gate (`validate_bundled_resource_root`, `REDRAFT_RESOURCE_FILES`) *also*
hard-requires `NWR_DATA_GOVERNANCE.json` to exist at a bundled path -- and
that constant was additionally stale, still pointing at the retired
`nwr_redraft_2026_rookie_projection_candidate_v1_20260809` / 608-row packet
(pre-dating Worker 2's P0-2 migration to Freeze V7), not just the human-name
conflict Worker 3 found in the npm-side allowlist. A packaged app built
before this pass, even if `check:resources` had somehow been bypassed, would
have failed to start (`bundled redraft resources are incomplete: missing ...
GOVERNED_COMBINED_608_PROJECTION_SNAPSHOT.csv`) because the Rust-side
constant and the npm-side allowlist/`tauri.windows.conf.json` had drifted
apart. Fixed as part of this pass (see Section 4) -- both must always name
the exact same file set, and now do.

**Nothing about this validation is a security check on the human name
itself.** `_validate_approval_receipt` only requires `approved_by` to be a
non-empty string -- it never inspects, compares, or authenticates the name's
*value* against anything. The runtime-relevant facts it actually enforces
are: artifact-hash binding (`source_sha256` match), admission state
(`authority`/`approval_status`), and temporal validity (`approved_at_utc`
sane, `valid_until` not expired). None of those require the approver's name
to be present at runtime -- the name is audit-trail content, valuable for
provenance, irrelevant to runtime admission logic.

## 2. The two-artifact architecture

### A. Private canonical governance receipt (already exists, untouched)

`docs/hq/model/nwr_redraft_2026_freeze_v7_bundled_seed_v1_20260912/
NWR_DATA_GOVERNANCE.json` remains exactly as approved: immutable, complete
audit trail (including the real `approved_by` identity), the actual source
of truth for what was approved, when, by whom, and under what directive. It
stays in the repository for provenance and continues to be usable for any
**non-packaged** workflow that already reads the full receipt (e.g. the
manual admission page, `app/pages/52_redraft_v1.py`, and
`redraft_engine_v1_service.install_projection_snapshot`/
`_validate_approval_receipt`, both entirely unmodified by this pass). It is
now explicitly **excluded** from every Tauri bundle resource map. Nothing
about its content, filename, or location changed.

### B. Release-safe runtime admission summary (new)

A new file, deterministically **derived** from the private receipt:

`docs/hq/model/nwr_redraft_2026_freeze_v7_bundled_seed_v1_20260912/
NWR_DATA_GOVERNANCE_RELEASE_SUMMARY.json`

Produced by `src/services/governance_release_summary_service.py`'s
`derive_release_admission_summary(canonical_receipt, canonical_receipt_bytes)`
-- a pure function with an explicit allowlist of output fields:

```json
{
  "summary_schema_version": 1,
  "kind": "NWR_GOVERNANCE_RELEASE_ADMISSION_SUMMARY",
  "derived_from_canonical_receipt_sha256": "<sha256 of the exact private receipt bytes>",
  "authority": "NWR_DATA_GOVERNANCE",
  "approval_status": "APPROVED_FOR_REDRAFT_V1",
  "admission_scope": "NWR_REDRAFT_2026_LIVE",
  "season": 2026,
  "source_id": "NWR_REDRAFT_2026_VETERAN_PLUS_ROOKIE_COMBINED_V2",
  "source_sha256": "b87c7296...29f4",
  "source_as_of": {"veterans": "...", "rookies": "..."},
  "valid_until": "2026-10-08"
}
```

Explicitly **excluded**: `approved_by`, `approved_at_utc`, `requested_by`,
`reason`, `limitations`, and any local filesystem path. These fields are
never copied, never abbreviated, never hashed-in-place-of -- they simply do
not exist anywhere in this file's schema. `derive_release_admission_summary`
enforces this by construction (it builds the output dict field-by-field from
an explicit allowlist; it does not start from a copy of the input and
subtract) and a dedicated test additionally scans the generated summary and
the checked-in file for every one of `check-resource-allowlists.mjs`'s own
`ownerMarkers` strings.

**This is a projection of an already-approved admission, not a new
approval.** Concretely:

- It carries no `approved_by`/`approved_at_utc` fields at all -- there is
  nothing in its own schema that could be mistaken for an independent
  approval signature. Anyone reading it sees admission *facts* (what/when
  valid/what season/what hash), never a claim of *who approved it* --
  because it is not the record of that decision, only a distributable
  restatement of its outcome.
- It is **hash-bound to the exact canonical receipt it was derived from**
  via `derived_from_canonical_receipt_sha256`. It cannot be repointed at a
  different canonical receipt without changing that field, and the
  regeneration test (Section 3) fails the build if the checked-in summary
  ever stops matching a fresh derivation from the checked-in canonical
  receipt.
- It is separately **hash-bound to the exact projection artifact it
  admits** via `source_sha256`, exactly like the canonical receipt is --
  runtime verification (Section 3) still refuses to install a projection
  snapshot whose hash doesn't match this field, so the summary cannot be
  swapped to cover different data than what it was generated for.
- `kind: "NWR_GOVERNANCE_RELEASE_ADMISSION_SUMMARY"` is a distinct,
  unambiguous type tag -- it can never be confused with (or accidentally
  accepted in place of) a full receipt in code that branches on shape.

## 3. Runtime wiring

`desktop_facade.py`'s `_ensure_redraft_projection_seed()` now reads
`NWR_DATA_GOVERNANCE_RELEASE_SUMMARY.json` (a new
`REDRAFT_SEED_RELEASE_SUMMARY_RELATIVE` constant) instead of
`NWR_DATA_GOVERNANCE.json`, and calls a new
`redraft_engine_v1_service.install_projection_snapshot_from_release_summary(...)`
instead of `install_projection_snapshot(...)`. This is a **separate,
additive function** -- `install_projection_snapshot`/
`_validate_approval_receipt` are byte-for-byte unmodified and remain the
correct path for any full-receipt admission flow (the manual admission page,
the existing `install_projection_snapshot` test suite). The new function:

1. Loads and validates the projection CSV exactly as before
   (`load_projection_snapshot`, unchanged).
2. Validates the release summary via a new
   `governance_release_summary_service.validate_release_admission_summary(...)`,
   which independently checks: required-field completeness, `kind`/
   `summary_schema_version` match, `authority`/`approval_status` match the
   same expected constants `_validate_approval_receipt` already enforces
   (passed in by the caller, not duplicated), `season`/`source_sha256`
   binding to the actual projection artifact being installed, `valid_until`
   not expired, `derived_from_canonical_receipt_sha256` well-formed, and --
   defense in depth -- a recursive scan of every string value in the summary
   for the same owner-identity markers `check-resource-allowlists.mjs`
   checks, so a hand-tampered summary that tried to smuggle a name back in
   is rejected even before packaging-time scanning would catch it.
3. Installs the projection CSV and a **copy of the summary** (not the
   private receipt -- the packaged runtime never has access to the private
   receipt at all) as the local `.approval.json`, and writes a manifest
   whose approval-related fields (`approval_receipt_sha256`,
   `approval_source_id`, `valid_until`, `canonical_receipt_sha256`,
   `admission_kind: "RELEASE_SUMMARY"`) are all summary-shaped -- no
   `approved_by`/`approved_at_utc` key is written at all, matching the
   installed source file.

`redraft_engine_v1_service._projection_manifest_errors` (the function that
re-validates the *installed local copy* on every subsequent load with
`require_manifest=True` -- i.e. every mutating Redraft operation) now
detects, by inspecting the installed `.approval.json`'s own shape (`"kind"
== "NWR_GOVERNANCE_RELEASE_ADMISSION_SUMMARY"` vs. the pre-existing
`approved_by`-carrying shape), which validator to re-run. **The full-receipt
branch is completely unmodified** -- same code, same behavior, same
expectations -- so every existing full-receipt install (dev/test
environments, the manual admission page, every pre-existing on-disk
installation anywhere) is unaffected. Only the new summary-shaped branch is
added.

Both environments (a `cargo tauri dev` debug run against the full git
checkout, and a packaged release build) now go through the **same**
summary-based seed-install code path, uniformly -- there is no
dev-vs-packaged divergence left in this logic. That is a deliberate choice:
Worker 3's stale-Rust-constant finding above happened *because* the
dev-tested path and the packaged path silently used different assumptions
about what resource files existed. Using one code path for both closes that
class of bug, not just this one instance of it.

## 4. Files updated to point at the release-safe summary

- `desktop/apps/redraft/src-tauri/tauri.windows.conf.json`: the bundled
  Windows resource map's third `redraft` entry now points at
  `NWR_DATA_GOVERNANCE_RELEASE_SUMMARY.json` instead of
  `NWR_DATA_GOVERNANCE.json`.
- `desktop/scripts/check-resource-allowlists.mjs`: the `redraft` allowlist
  mirrors the same change. The guard's own logic (`ownerMarkers`,
  `assertNoOwnerMarkers`, the exact-match assertion between the allowlist and
  the actual Tauri resource map) is **completely unmodified** -- no
  exception, no whitelist-for-this-file, nothing. It now simply scans a
  different (PII-free) file and passes on its own merits.
- `desktop/crates/nwr-desktop-runtime/src/lib.rs`: `REDRAFT_RESOURCE_FILES`
  (the release-build startup gate) is corrected to the real Freeze V7 paths
  and now names the release summary instead of the private receipt --
  closing both the human-name conflict and the separately-discovered stale
  608-row/legacy-path bug in the same edit, since both were the same
  constant.

## 5. What is explicitly NOT done

- The privacy guard (`check-resource-allowlists.mjs`) gained no exception,
  override, or per-file allowlist bypass. It still scans every bundled
  resource file's actual bytes for the same owner markers it always has.
- The canonical `NWR_DATA_GOVERNANCE.json` was not edited, redacted, moved,
  or stripped. `git diff` against it is empty; a test asserts its on-disk
  bytes are unchanged from the derivation input used to produce the summary.
- No "safe names" allowlist of any kind was created. The summary schema
  simply never has a name-shaped field to allowlist in the first place.
- Runtime verification was not weakened: the summary path still enforces
  artifact-hash binding, admission-state matching, and expiry -- the exact
  same categories of fact the full-receipt path enforces, and a test proves
  a tampered/mismatched summary is still rejected end to end through the
  real install function (Section "Tests" below).

## 6. Tests (see the actual test files for full detail)

1. `tests/test_privacy_safe_packaging_bundle.py` -- a **real packaging-scan**
   test, not "should be excluded" logic: runs the actual
   `node desktop/scripts/check-resource-allowlists.mjs` as a subprocess and
   asserts it exits 0; loads the actual
   `tauri.windows.conf.json` resource map and asserts the private receipt's
   destination path is absent and the release summary's destination path is
   present; reads every real bundled `redraft` resource file's bytes off
   disk and asserts none contain any owner-identity marker; cross-checks the
   Rust `REDRAFT_RESOURCE_FILES` constant (via `lib.rs`'s own source text) is
   the exact same file set as the npm allowlist, so the two can never drift
   apart silently again.
2. `tests/test_governance_release_summary_service.py` -- regenerates the
   summary directly from the checked-in canonical receipt and asserts it is
   byte-for-byte identical to the checked-in summary file (drift-detection);
   asserts the derivation output never contains any forbidden field or
   owner-marker string; unit-tests `validate_release_admission_summary`
   accepting a valid summary and rejecting: a wrong `source_sha256`, an
   expired `valid_until`, a wrong `approval_status`/`kind`, a missing
   required field, and a summary with a name-marker string hand-inserted
   into an otherwise-valid field.
3. `tests/test_redraft_engine_v1_service.py` (extended) --
   `install_projection_snapshot_from_release_summary` end-to-end: a real
   install succeeds and is loadable via `load_projection_snapshot(...,
   require_manifest=True)`; a tampered summary (edited `source_sha256` or
   expired `valid_until`) is rejected and installs nothing; the pre-existing
   full-receipt `install_projection_snapshot` test suite is re-run unchanged
   to confirm zero regression in that path.

## 7. Verdict

This is the **PACKAGE PASS** case, not the "requires full receipt at
runtime" blocked case: the runtime's actual verification needs (artifact
identity, admission state, expiry) are fully satisfiable by a derived,
hash-bound, PII-free summary, without weakening what gets checked. See
`NWR_POST_UI_WORKDAY_LEDGER.md`'s Worker B entry and this session's final
handoff message for the actual native-build/packaging-scan result.
