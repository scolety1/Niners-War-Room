# NWR 2026 CURRENT DATA — BIG DRAFT FRESHNESS PASS

**Scope: current-data readiness only. No model tuning. No historical holdout touched. No change to Team Score / Equity / Pick Score.**

## 0. A real, structural limitation of this session, stated up front

This sandboxed session has **no filesystem access to the owner's real local NWR installation** (`local_exports/` does not exist in this checkout, and the default projection/ADP/approval store — `redraft_store_root()` — resolves under it). Every real governed 2026 data file the live product actually uses at draft time lives there, not in this git repository. This is a genuine environment constraint, not a governance restriction and not something this session can work around — it means this pass audits **only what is committed to the repository itself**, which is real but almost certainly a stale/partial snapshot of what's actually installed on the owner's machine today. Treat everything below as "what the repo can prove," not "what your live app currently has loaded."

## 1. What was audited (real, committed files)

| File | Rows | Finding |
|---|---:|---|
| `docs/hq/model/nwr_redraft_2026_rookie_projection_candidate_v1_20260809/CURRENT_2026_IDENTITY_AND_ROLE.csv` | 80 real rookie rows | Real 2026 draft-class rookies, identity-bridged via `EXACT_PFR_ID_BRIDGE`, `projection_status=ELIGIBLE` for all inspected rows. Dated 2026-08-09 admission — **28 days old as of tonight**, i.e. real but not fresh. |
| `docs/hq/model/nwr_redraft_2026_rookie_projection_candidate_v1_20260809/BLOCKED_2026_ROOKIES.csv` | 2 real rows | Two rookies (Max Bredeson, Riley Nowakowski) blocked for a real, disclosed reason: `draft position conflicts with current factual registry position` (their draft-class position doesn't match their current real team-registry position) — correctly labeled `BLOCKED`, not silently dropped or guessed at. |
| `sample_data/kha_real_draft_2026/udk_kdst_snapshot_20260902.csv` | 64 real rows | Real K/DST identity + team data (`EXTERNAL_UDK_UNMODELED_BY_NWR` — real identity, explicitly never NWR-scored, matching this program's standing K/DST policy). Dated **2026-09-02 — only 4 days old**, genuinely fresh. |

These are the only 2026-dated, player-identity-bearing data files this session found committed to git (searched by filename pattern across the whole repo). No committed top-200-veteran-market snapshot, no committed real current ADP export, and no committed real ScoringSettings/roster config for "tomorrow's league" were found.

## 2. The real rookie-visibility issue, reconciled as far as this session can

The prior session's own finding ("78 real 2026 rookies restored to visibility but DATA_LIMITED because their governed projections were stale, `source_as_of=2026-07-30`, beyond the 30-day freshness window") describes the **live installation's own manual-assets file**, not the committed CSV above — those are two different real artifacts from two different admission passes (2026-07-30 vs this repo's 2026-08-09 candidate file). This session cannot open the live installation to check whether that specific `source_as_of=2026-07-30` batch has since been superseded by a fresher governed pull — **that check can only be run on the owner's actual machine.** No newer rookie projection source was found committed to this repository since 2026-08-09; if the live install genuinely has nothing newer either, the 78 affected rookies should be expected to remain `DATA_LIMITED` tomorrow, and that is the CORRECT, honest behavior (never fabricate a projection to clear this) — not a defect to "fix" by relaxing the freshness window.

## 3. Exception classification (per the requested taxonomy, applied to what was actually inspected)

| Class | Count | Basis |
|---|---:|---|
| `CURRENT_COMPLETE` | 78 rookie rows (80 minus 2 blocked) | Real identity, real team, real position, `ELIGIBLE` |
| `POSITION_REVIEW` | 2 rookie rows | Real, disclosed position conflict (Bredeson, Nowakowski) — already correctly flagged by the existing pipeline, not a new find |
| `DATA_LIMITED` | Unknown exact count on the live install (last known: 78, dated 2026-07-30) | Cannot be re-verified from this sandboxed session; see Section 2 |
| `MARKET_ONLY` (K/DST) | 64 rows | Real identity/team, `EXTERNAL_UDK_UNMODELED_BY_NWR` — by design, not a gap |
| Top-~200 real veteran market players | **UNSUPPORTED — not auditable from this session** | No committed real veteran projection/ADP snapshot was found in the repository; the live install's real snapshot is outside this session's reach |

## 4. What was NOT done, and why

- **No top-150/200 real veteran market player audit.** The only path to that data is the owner's real local installation, which this session cannot open. Attempting to substitute a different (e.g. re-fetched) source would risk exactly what the mission forbids: "do not fabricate projections," "do not use stale data silently," and "do not cross a governance wall."
- **No new data was pulled, refreshed, or admitted.** Every real file inspected was already committed before tonight.
- **No provider-vs-canonical-team reconciliation run** beyond what's already visible in the two files above (both already show clean, real team codes).

## 5. The safe FINAL PRE-DRAFT REFRESH pathway (real, already exists — described, not run)

The real, already-existing, governed mechanism for this is `redraft_engine_v1_service.install_projection_snapshot(root, season, source, approval_receipt)` (validates the new snapshot, validates a real approval receipt bound to its exact `source_sha256`, then atomically replaces `current.csv`/`current.manifest.json`/`current.approval.json` — never a partial or silent overwrite). **This performs no model retraining** — it only swaps which admitted CSV the existing frozen scoring pipeline reads.

**Exact command shape** (fill in the real paths on the owner's machine; this session cannot run this without access to that machine):
```
python -c "
from src.services.redraft_engine_v1_service import install_projection_snapshot
install_projection_snapshot(
    root='<the real NWR data root, e.g. wherever NWR_REDRAFT_HOME points, or the app's local_exports/redraft_v1>',
    season=2026,
    source='<path to the freshly re-exported, already-governed 2026 projection CSV>',
    approval_receipt='<path to a valid, non-expired approval receipt JSON bound to that exact file's sha256>',
)
"
```
Run this **60-90 minutes before the draft**, per the mission's own timing request, then re-generate one recommendation (`redraft_decision_bundle`) as a smoke test and confirm real player counts / a non-error result before trusting it for the live draft.

## 6. Report to Draft Upgrade

`NWR_2026_BIG_DRAFT_CURRENT_DATA_STATUS: PARTIALLY_READY_ENVIRONMENT_LIMITED`

- **Artifact paths inspected**: the three files in Section 1 (full paths given there).
- **Hashes**: not computed for `local_exports`-scoped files (inaccessible); the three committed files' identities are fixed by their git blob hashes at the commit this report ships in.
- **Timestamps**: rookie candidate file 2026-08-09 (28 days stale as of tonight); K/DST snapshot 2026-09-02 (4 days old, fresh).
- **Player count**: 80 rookie rows (78 eligible, 2 blocked), 64 K/DST rows.
- **Rookie coverage**: real, but the DATA_LIMITED subset's current true size and freshness could not be re-verified from this session (Section 2).
- **Projection coverage / ADP coverage / status-injury coverage for the real veteran market pool**: **not assessable from this session** — the real snapshot lives only on the owner's machine.
- **Known exceptions**: the two disclosed position-conflict rookies; nothing else newly found.
- **Exact refresh command**: Section 5 above.

This is an honest partial result, not a `NWR_2026_BIG_DRAFT_CURRENT_DATA_READY` — that verdict requires inspecting the real installed veteran snapshot, which requires either running this check on the owner's own machine or granting this kind of session access to it.

No push. No merge. No deployment. No model tuning. No governance wall crossed.
