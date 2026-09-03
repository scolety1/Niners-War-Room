# Player-Universe Saturday Renewal Packet

Prepared so the owner's morning decision takes minutes, not another
investigation. All facts below were read directly off the real installed
artifacts on this machine (`%LOCALAPPDATA%\com.ninerswarroom.redraft\state\redraft\projections\2026\`)
at **2026-09-03T11:17:54Z** — nothing here is inferred, extended, or
self-approved. No file in that directory was modified to produce this
packet.

## 1. Exact current artifact

| Field | Value |
|---|---|
| Installed snapshot | `current.csv` (608 rows), source file `GOVERNED_COMBINED_608_PROJECTION_SNAPSHOT.csv` |
| Artifact SHA-256 | `e483caaedc236140bcdfeccdd759bf8726a4b231bbaf3e9fdc461873d3921c25` |
| Manifest | `current.manifest.json` |
| Approval receipt | `current.approval.json` |
| Row-level freshness bypass | `DRAFT_DAY_AUTHORIZATION.json` (78 rookie `player_id`s only) |
| Rollback baseline | The three files above (untouched, already on disk) — an even earlier snapshot also exists at `state/recovery/20260814T145000Z__pre_owner_league_recovery_v1/redraft/projections/2026/` |

## 2. Prior approval, exactly as recorded

- **Authority**: `NWR_DATA_GOVERNANCE`, `approval_status: APPROVED_FOR_REDRAFT_V1`.
- **Approved by**: "NWR Owner (original 2026-08-09 admission) + Conversation
  user (2026-09-01 draft-day renewal, narrowly scoped per above)".
- **Approved at**: `2026-09-02T04:28:56Z`. **Installed at**: `2026-09-02T04:34:42Z`.
- **Composition**: 530 veteran rows (`source_as_of: 2026-08-08`) + 78
  rookie rows (`source_as_of: 2026-07-30`), merged with veteran bytes
  preserved byte-for-byte as the combined-output prefix (per
  `finalization_contract.veteran_bytes_preserved_as_combined_prefix: true`
  in the approval receipt) — the veteran layer's *values* were never
  touched by the rookie finalization step.
- **`valid_until`** (both manifest and approval receipt): **2026-09-03**
  — the receipt's own governance-set expiration, not a bare
  `source_as_of + 30 days` formula (that would land 2026-08-29 for the
  rookie cohort; governance deliberately extended a few extra days for
  the 2026-09-02 draft-day window).
- **`draft_day_authorization` (the 78-rookie row-level freshness
  bypass)**: `expires_at_utc: 2026-09-03T18:00:00Z`, and its own
  `effective_scope` field states it is authorized for **"2026 KHA High
  Stakes League draft only (2026-09-02, ESPN, 16-team, full PPR)"** —
  i.e. explicitly bound to a single draft that has already happened, not
  a general-purpose freshness extension.

## 3. Exact reason this is expiring / already scope-expired

Two independent gates, both real, both governance-authored (not derived
by this session):

1. **Row-level freshness** (`_source_as_of_reason`,
   `redraft_engine_v1_service.py:850`): any row is rejected once
   `today - source_as_of > 30 days` (`MAX_PROJECTION_AGE_DAYS = 30`).
   Veteran rows (`source_as_of 2026-08-08`) remain fresh through
   **2026-09-07**. Rookie rows (`source_as_of 2026-07-30`) crossed 30
   days on **2026-08-29** and have needed the `DRAFT_DAY_AUTHORIZATION`
   bypass ever since.
2. **Receipt-level `valid_until`** (`_validate_approval_receipt`): the
   whole install is rejected once `valid_until < today`. At the time
   this packet was written (`2026-09-03T11:17:54Z`), `valid_until
   (2026-09-03) < today (2026-09-03)` is **false** — the receipt has not
   yet crossed its own line, but it will at the 2026-09-04 rollover.

Even setting the clock aside: the `DRAFT_DAY_AUTHORIZATION`'s own
`effective_scope` limits it to the 2026-09-02 draft specifically. That
draft is over. **Reusing this authorization for any further use —
tonight's testing, a future mock, or a next real draft — is a scope
violation of the authorization's own stated terms, independent of
whether its timestamp has technically lapsed.** This is why the honest
answer is "blocked," not "technically still has hours left."

## 4. Governing service/contract

`src/services/redraft_engine_v1_service.py`:
`install_projection_snapshot` → `_validate_approval_receipt` (hard gate,
no code-level override) and `load_projection_snapshot` →
`_source_as_of_reason` per row, with `_load_draft_day_authorization` as
the only bypass mechanism, itself gated on artifact-SHA binding + label +
expiry (all three already verified above). Authority constant:
`NWR_DATA_GOVERNANCE` (`APPROVAL_AUTHORITY`).

## 5. Existing deterministic refresh path — and why it cannot run unattended

`scripts/finalize_redraft_2026_rookie_owner_approval.py` is the script
that produced today's installed artifact. It is **not** a general
"regenerate projections" pipeline: it is a one-time finalizer hard-bound
to the exact SHA-256 hashes of three already-computed, already-reviewed
input files (`EXPECTED_ROOKIE_SHA`, `EXPECTED_COMBINED_REVIEW_SHA`,
`EXPECTED_VETERAN_SHA`), and it refuses to run against anything else. No
script in this repository fetches fresh veteran stats, injury/depth-chart
status, or a re-dated rookie cohort — those are external data inputs
this environment has no live-provider access to (and is explicitly not
authorized to fetch even if it did). **There is no code-only "regenerate
and produce a candidate for review" path** — the finalize script needs
new externally-sourced input files that do not exist in this repo, so
there is nothing this session can safely run in an isolated candidate
right now. Per this directive's own instruction ("if owner authorization
is required before the refresh itself: stop that step and document the
exact authorization language needed"), this step stops here.

**`PLAYER_UNIVERSE_SATURDAY_DIFF.csv` is not produced** — there is no
candidate artifact to diff against the installed one.

## 6. The two real options for the owner, and exactly what each needs

**Option A — Re-approve the existing, unchanged data.** The 608-row
artifact itself does not need to change; only its governance window does.
This is honest only if the owner accepts that veteran rows are dated
2026-08-08 and rookie rows 2026-07-30 (increasingly stale for
injury/depth-chart/role-change purposes as the season progresses, but not
*false* for players whose situation has not materially changed). Requires
a new `current.approval.json`-shaped document with:
```json
{
  "schema_version": 1,
  "authority": "NWR_DATA_GOVERNANCE",
  "approval_status": "APPROVED_FOR_REDRAFT_V1",
  "season": 2026,
  "source_sha256": "e483caaedc236140bcdfeccdd759bf8726a4b231bbaf3e9fdc461873d3921c25",
  "source_id": "NWR_REDRAFT_2026_VETERAN_PLUS_ROOKIE_COMBINED_V1",
  "approved_by": "<real NWR Owner identity>",
  "approved_at_utc": "<real timestamp, not in the future>",
  "valid_until": "<real new expiration date the owner actually intends>"
}
```
signed off by the real owner (this session cannot self-issue
`approved_by`), then installed via `install_projection_snapshot(root,
2026, current_source_path, new_receipt_path)` — the same, already-tested,
unmodified installer used today. If a rookie-row freshness bypass is
still needed past 2026-09-03, a new `DRAFT_DAY_AUTHORIZATION.json` bound
to the same `source_sha256` with a real new `expires_at_utc` and an
honest `effective_scope` (not falsely re-scoped to the finished
2026-09-02 draft) is also needed.

**Option B — Refresh the underlying data.** Requires real, current
veteran stat/injury/depth-chart inputs and a re-dated rookie cohort from
outside this repo, run through the same governed
build-then-finalize pipeline that produced today's artifact (not
identified in full in this repo — only the final-merge step,
`finalize_redraft_2026_rookie_owner_approval.py`, is present; the
upstream veteran/rookie generation steps live outside what this session
has visibility into). This is the correct option if the owner wants
current-week accuracy rather than late-July/August priors, but it is not
something this session can do unattended tonight.

Neither option was executed by this session. No approval receipt was
authored on the owner's behalf, per this directive's explicit
instruction.
