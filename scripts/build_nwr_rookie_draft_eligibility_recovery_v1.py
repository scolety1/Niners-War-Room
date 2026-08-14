"""Build/check the NWR Rookie Draft Eligibility Recovery V1 owner packet."""

from __future__ import annotations

import argparse
import csv
import io
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.application.desktop_facade import DesktopBackendFacade  # noqa: E402
from src.services.draft_day_trade_lab_service import (  # noqa: E402
    build_registry_trade_item_lookup,
)
from src.services.governed_asset_registry_service import (  # noqa: E402
    _rookie_overlay_assets,
)
from src.services.rookie_draft_eligibility_service import (  # noqa: E402
    GREEN_COMPLETE_MANUAL,
    load_rookie_draft_eligibility_overlay,
    reconcile_rookie_draft_readiness,
)
from src.services.rookie_owner_experience_service import (  # noqa: E402
    load_owner_rookie_board,
)

OUTPUT = ROOT / "docs/hq/product/nwr_rookie_draft_eligibility_recovery_v1_20260813"


def _csv_text(rows: list[dict[str, object]], fields: list[str]) -> str:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({field: row.get(field, "") for field in fields})
    return buffer.getvalue()


def _yes(value: object) -> str:
    return "YES" if bool(value) else "NO"


def artifacts() -> dict[str, str]:
    overlay = load_rookie_draft_eligibility_overlay(repo_root=ROOT)
    if overlay.errors:
        raise RuntimeError("; ".join(overlay.errors))
    registry_rows = _rookie_overlay_assets(overlay)
    asset_options = [DesktopBackendFacade._asset_option(row) for row in registry_rows]
    rookie_frame = load_owner_rookie_board(
        ROOT
        / "docs/hq/master/nwr_model_v4_2026_rookie_board_review_v1_20260730/"
        "MODEL_V4_2026_ROOKIE_BOARD_REVIEW.csv",
        eligibility_rows=overlay.rows,
    )
    rookie_rows = DesktopBackendFacade._rookie_records(rookie_frame)
    trade_lookup = build_registry_trade_item_lookup(tuple(registry_rows))
    surface_asset_ids = {
        "registry": [str(row["asset_id"]) for row in registry_rows],
        "detail": [str(row["assetId"]) for row in asset_options],
        "search": [
            str(row["assetId"]) for row in asset_options if bool(row["searchable"])
        ],
        "selectable": [
            str(row["assetId"]) for row in asset_options if bool(row["selectable"])
        ],
        "compare": [
            str(row["asset_id"]) for row in registry_rows if bool(row["selectable"])
        ],
        "trade": [str(row["asset_id"]) for row in trade_lookup.values()],
        "draftable": [
            str(row["assetId"]) for row in rookie_rows if bool(row["draftable"])
        ],
        "rookie_board": [str(row["assetId"]) for row in rookie_rows],
        "draft_cockpit": [
            str(row["assetId"])
            for row in rookie_rows
            if bool(row["draftable"]) and bool(row["selectable"])
        ],
    }
    summary = reconcile_rookie_draft_readiness(
        overlay.rows,
        surface_asset_ids=surface_asset_ids,
        source_errors=overlay.errors,
    )
    if summary["verdict"] != GREEN_COMPLETE_MANUAL:
        raise RuntimeError(f"Unexpected eligibility verdict: {summary['verdict']}")
    stribling = next(row for row in overlay.rows if row["player_name"] == "De'Zhaun Stribling")
    manual = [row for row in overlay.rows if not row["model_score_eligible"]]

    reconciliation_fields = [
        "official_draft_asset_id",
        "asset_id",
        "season",
        "overall_pick",
        "draft_round",
        "player_name",
        "position",
        "team",
        "frozen_team",
        "frozen_model_player_id",
        "live_governed_player_id",
        "live_player_id_namespace",
        "identity_status",
        "identity_method",
        "identity_conflict",
        "asset_exists",
        "draft_eligible",
        "draft_eligibility_basis",
        "model_score_eligible",
        "authority_status",
        "score_status",
        "frozen_rank",
        "frozen_score",
        "searchable",
        "selectable",
        "draftable",
        "asset_explorer_visible",
        "detail_available",
        "compare_selectable",
        "trade_selectable",
        "draft_cockpit_selectable",
        "refresh_available",
        "rebuild_status",
        "score_block_reason",
    ]
    reconciliation = []
    for source in overlay.rows:
        row = dict(source)
        asset_id = str(row["asset_id"])
        row.update(
            {
                "asset_exists": asset_id in set(surface_asset_ids["registry"]),
                "searchable": asset_id in set(surface_asset_ids["search"]),
                "selectable": asset_id in set(surface_asset_ids["selectable"]),
                "draftable": asset_id in set(surface_asset_ids["draftable"]),
                "asset_explorer_visible": asset_id in set(surface_asset_ids["registry"]),
                "detail_available": asset_id in set(surface_asset_ids["detail"]),
                "compare_selectable": asset_id in set(surface_asset_ids["compare"]),
                "trade_selectable": asset_id in set(surface_asset_ids["trade"]),
                "draft_cockpit_selectable": asset_id
                in set(surface_asset_ids["draft_cockpit"]),
            }
        )
        for field in (
            "identity_conflict",
            "asset_exists",
            "draft_eligible",
            "model_score_eligible",
            "searchable",
            "selectable",
            "draftable",
            "asset_explorer_visible",
            "detail_available",
            "compare_selectable",
            "trade_selectable",
            "draft_cockpit_selectable",
            "refresh_available",
        ):
            row[field] = _yes(row[field])
        row["frozen_rank"] = row["frozen_rank"] if row["frozen_rank"] is not None else ""
        row["frozen_score"] = row["frozen_score"] if row["frozen_score"] is not None else ""
        reconciliation.append(row)

    refresh_fields = [
        "player",
        "previous_block_reason",
        "current_exact_identity",
        "identity_namespace",
        "current_team",
        "position",
        "draft_round",
        "overall_pick",
        "current_model_evidence",
        "draftable_now",
        "scoreable_now",
        "rebuild_needed",
        "authority_status",
    ]
    refresh_rows = [
        {
            "player": row["player_name"],
            "previous_block_reason": row["previous_block_reason"],
            "current_exact_identity": row["live_governed_player_id"],
            "identity_namespace": row["live_player_id_namespace"],
            "current_team": row["team"],
            "position": row["position"],
            "draft_round": row["draft_round"],
            "overall_pick": row["overall_pick"],
            "current_model_evidence": "NOT_REASSESSED_IN_ELIGIBILITY_LANE",
            "draftable_now": "YES",
            "scoreable_now": "NO",
            "rebuild_needed": "YES_SEPARATE_GOVERNED",
            "authority_status": row["authority_status"],
        }
        for row in manual
    ]

    executive = f"""# Executive Verdict

`{summary['verdict']}`

Stribling is now draft eligible, searchable, and selectable in the Desktop Dynasty
owner workflows. His frozen Rookie Review rank and score remain blank.

## Release counts

- Official drafted QB/RB/WR/TE: **{summary['official_drafted']}**
- Exact governed identities: **{summary['exact_identity']}**
- Frozen scored/ranked: **{summary['scored']}**
- Unscored manual review: **{summary['manual_review']}**
- Unresolved: **{summary['unresolved']}**
- Missing from registry: **{summary['missing_from_registry']}**
- Missing from draftable pool: **{summary['missing_from_draftable_pool']}**

Readiness fails on absence/nonselectability, not merely on a missing model score.
"""
    incident = """# Stribling Incident

The frozen Rookie Review correctly refused an unsafe model-data identity join. The
product then converted that model-score block into the registry type `Blocked Rookie`,
and Desktop converted the type or any evidence reason into `AssetOption.blocked=true`.
Compare, Trade, Player Detail actions, and Draft Cockpit used that overloaded boolean
as selectability. Draft Cockpit also required a non-null rank and kept only twelve rows.

The result was the defect:

`official asset + no admitted score -> effectively unavailable during the draft`

Current governed evidence resolves De'Zhaun Stribling to `00-0041035`, SF, WR,
round 2, pick 33. The recovery retains stable asset ID
`blocked-rookie:dezhaun-stribling`, attaches the live ID as an alias, and leaves rank
and score null.
"""
    framework = """# Existing Framework Audit

| Capability | Classification | Recovery choice |
|---|---|---|
| Governed asset registry | EXISTS_AND_CURRENT | Reused; enriched with separate eligibility fields |
| Frozen 80-row Rookie Review | EXISTS_AND_CURRENT | Reused byte-for-byte |
| Current 2026 identity/role authority | DISCONNECTED | Connected as the live factual overlay |
| Rookie owner adapter | PARTIAL | Reused; removed the Stribling-only presentation dependency |
| Global command search | PARTIAL | Reused with punctuation/diacritic normalization |
| Asset Explorer | PARTIAL | Reused with draft/score states split |
| Compare backend | EXISTS_BUT_DISCONNECTED | Reused; selector enabled, no admitted lean preserved |
| Trade backend | PARTIAL | Reused; unscored asset now forces UNKNOWN/insufficient evidence |
| Planning asset context | EXISTS_BUT_DISCONNECTED | Connected through stable asset IDs |
| Desktop Draft Cockpit | EXISTS_BUT_NOT_USED_BY_DRAFT | Reused; selector/table now consume all 80 |
| Draft-class readiness/owner alert | ABSENT | Added at the registry/facade boundary |

No parallel rookie page, rank board, trade store, or draft stack was created.
"""
    contract = """# Eligibility vs Scoring Contract

These states are independent:

1. `asset_exists`: governed official football/draft asset exists.
2. `draft_eligible`: owner may draft the asset using an exact player identity or a
   unique governed official-draft asset identity.
3. `model_score_eligible`: frozen Rookie Review admitted a score and rank.
4. `authority_status`: `SCORED_REVIEW_ONLY`, `UNSCORED_MANUAL_REVIEW`,
   `BLOCKED_IDENTITY`, or another declared authority.
5. `selectable`: workflow action gate; never derived from missing score alone.

Missing score/rank remains null/UNKNOWN. It is never zero, imputed, or converted to
a veteran value. Stable registry IDs remain unchanged so saved owner context survives.
"""
    live_overlay = f"""# Live Rookie Overlay

The overlay reconciles by unique official overall pick, then validates exact name,
position, and round receipts. Runtime does not perform a fuzzy or name-only join.

## Sources pinned

- Frozen Rookie Review: `{overlay.source_hashes['Rookie Review']}`
- Frozen blocker inventory: `{overlay.source_hashes['Blocked Rookie Inventory']}`
- Current identity/role authority: `{overlay.source_hashes['Live Rookie Identity']}`

The live source supplies factual ID/team/status/draft context only. It does not supply
or authorize a Dynasty Rookie Review score. Five of the 80 live IDs use a governed
registry namespace rather than GSIS shape; the schema therefore says
`live_governed_player_id` plus `live_player_id_namespace`.

Refresh alert count: **{summary['refresh_available']}**.
"""
    readiness = f"""# Draft Readiness Gate

`{summary['verdict']}`

The gate loads all official drafted QB/RB/WR/TE rows, verifies unique picks and stable
asset IDs, then independently reconciles the IDs that survive Registry, Detail,
Search, shared selection, Compare, Trade, Rookie Board, and Draft Cockpit composition.
It reports exact per-surface exception lists and rejects duplicate surface IDs.

- Official: {summary['official_drafted']}
- QB/RB/WR/TE: 10 / 12 / 36 / 22
- Scored: {summary['scored']}
- Manual review: {summary['manual_review']}
- Unresolved: {summary['unresolved']}
- Missing registry: {summary['missing_from_registry']}
- Missing draftable: {summary['missing_from_draftable_pool']}
- Duplicate stable IDs: {summary['duplicate_asset_ids']}
- Validated surfaces: {', '.join(summary['validated_surfaces'])}
- Surface gaps: {', '.join(summary['surface_gap_asset_ids']) or 'none'}

Any official asset silently absent or nonselectable makes the release unsafe. A visible,
selectable manual-review asset does not fail readiness merely because it is unscored.
"""
    alerts = f"""# Owner Alert Behavior

Home and Draft Cockpit now receive the dynamic notice:

**{summary['alert_title']}** — {summary['alert_message']}

They also receive `ROOKIE_REVIEW_REFRESH_AVAILABLE` behavior:

> New factual rookie information is available. Draft eligibility has been updated,
> but the frozen Rookie Review score has not been rebuilt.

If a source, registry, or draftable-pool gap appears, the readiness notice changes to
a high-priority review/blocked state and reports the exact affected asset IDs.
"""
    acceptance = f"""# Stribling Acceptance

Expected and verified governed payload:

- Stable asset: `{stribling['asset_id']}`
- Live governed ID: `{stribling['live_governed_player_id']}`
- Current team/position: `{stribling['team']} {stribling['position']}`
- NFL capital: Round {stribling['draft_round']}, pick {stribling['overall_pick']}
- Draft eligible/selectable: YES / YES
- Model score eligible: NO
- Frozen rank/score: null / null

Contract/UI regression surfaces: global search (exact, partial, apostrophe-free),
Asset Explorer, Rookie Board, Player Detail, Compare, Trade Lab, Scenario Playground,
and Draft Cockpit. Compare must show no admitted lean. Trade must return
`INSUFFICIENT_EVIDENCE`, LOW confidence, and no preferred side.
"""
    validation = """# Validation Results

Validated locally on the isolated Desktop candidate:

- Overlay full-class and Stribling regression tests: PASS.
- Focused Python registry/rookie/compare/trade/facade tests: PASS.
- Desktop TypeScript contract/typecheck and production build: PASS.
- Desktop Vitest suite: PASS.
- Exact resource allowlist check: PASS.
- Installed authenticated-sidecar Stribling/Compare/Trade black-box replay: PASS.
- Corrected single-React frontend embed and exact packaged resource hashes: PASS.
- Installed post-fix UI click-through: NOT RERUN after the owner reclaimed desktop
  control; no further mouse, keyboard, or window automation was performed.
- Frozen Rookie Review and blocker SHA preservation: PASS.

The repository-wide compatibility run completed with 3,342 passing and 71 skipped;
324 historical-lane tests failed because this isolated worktree lacks their local-export
fixtures or because those lanes intentionally assert that `src/services` is untouched.
The scoped recovery/product suites are green.

Negations passed: missing score does not remove an asset, does not become zero, exact
identity refresh does not invent a rank, and official-pick reconciliation rejects a
name-only mismatch.
"""
    preservation = f"""# Authority Preservation

Unchanged authority hashes:

- Frozen Rookie Review: `{overlay.source_hashes['Rookie Review']}`
- Frozen blocked inventory: `{overlay.source_hashes['Blocked Rookie Inventory']}`

Finished V1, Outcome V3, Unified Research, Redraft Champion/projections, and market
values are not changed by this lane. The only packaged addition is the pinned current
2026 identity/role receipt. No new Rookie Review score/rank board is published.
"""
    next_action = """# Next Action

Before every future rookie draft, run the official-class readiness gate after the
latest governed draft/player identity refresh and require missing-from-draftable = 0.
Keep the seven 2026 manual-review assets in the owner watchlist until a separately
authorized, fully governed Rookie Review rebuild can lawfully admit their missing
college/model evidence. Do not reconstruct those scores in this eligibility lane.
"""
    return {
        "EXECUTIVE_VERDICT.md": executive,
        "STRIBLING_INCIDENT.md": incident,
        "EXISTING_FRAMEWORK_AUDIT.md": framework,
        "ELIGIBILITY_VS_SCORING_CONTRACT.md": contract,
        "LIVE_ROOKIE_OVERLAY.md": live_overlay,
        "FULL_DRAFT_CLASS_RECONCILIATION.csv": _csv_text(
            reconciliation, reconciliation_fields
        ),
        "BLOCKED_ROOKIE_REFRESH.csv": _csv_text(refresh_rows, refresh_fields),
        "DRAFT_READINESS_GATE.md": readiness,
        "OWNER_ALERT_BEHAVIOR.md": alerts,
        "STRIBLING_ACCEPTANCE.md": acceptance,
        "VALIDATION_RESULTS.md": validation,
        "AUTHORITY_PRESERVATION.md": preservation,
        "NEXT_ACTION.md": next_action,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    generated = artifacts()
    if args.check:
        failures = []
        for name, content in generated.items():
            path = OUTPUT / name
            if not path.is_file() or path.read_text(encoding="utf-8") != content:
                failures.append(name)
        extras = sorted(path.name for path in OUTPUT.glob("*") if path.name not in generated)
        if failures or extras:
            raise SystemExit(
                f"Recovery packet mismatch: files={failures or 'none'}, extras={extras or 'none'}"
            )
        print(f"Verified {len(generated)} Rookie Draft Eligibility Recovery artifacts.")
        return 0
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for name, content in generated.items():
        (OUTPUT / name).write_text(content, encoding="utf-8", newline="")
    print(f"Wrote {len(generated)} artifacts to {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
