"""Live factual rookie eligibility without mutating the frozen Rookie Review.

The official 2026 draft pick is the reconciliation key.  Names and positions are
validated as receipts; they are never used as a fuzzy runtime identity join.
"""

from __future__ import annotations

import csv
import hashlib
import re
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
ROOKIE_PACKET_RELATIVE = Path(
    "docs/hq/master/nwr_model_v4_2026_rookie_board_review_v1_20260730"
)
ROOKIE_BOARD_RELATIVE = ROOKIE_PACKET_RELATIVE / "MODEL_V4_2026_ROOKIE_BOARD_REVIEW.csv"
BLOCKED_ROOKIES_RELATIVE = ROOKIE_PACKET_RELATIVE / "2026_ROOKIE_IDENTITY_BLOCKERS.csv"
LIVE_IDENTITY_RELATIVE = Path(
    "docs/hq/model/nwr_redraft_2026_rookie_projection_candidate_v1_20260809/"
    "CURRENT_2026_IDENTITY_AND_ROLE.csv"
)

ROOKIE_BOARD_SHA256 = "06853164a41cd9715accfc3c4f3e54d0cc915be6c55ebab040de6fc0abd96c2f"
BLOCKED_ROOKIES_SHA256 = "361011524dfbabc62cecaf4286d201b219e275a5fa8b43b57c93017eca56d19a"
LIVE_IDENTITY_SHA256 = "f4ae6106f5302c59f23d83a27c006a894c5660b3058a011e5b2f16c6a2c79ff9"

SUPPORTED_POSITIONS = ("QB", "RB", "WR", "TE")
EXPECTED_POSITION_COUNTS = {"QB": 10, "RB": 12, "WR": 36, "TE": 22}
EXPECTED_OFFICIAL_COUNT = 80
EXPECTED_SCORED_COUNT = 73
EXPECTED_MANUAL_REVIEW_COUNT = 7

GREEN_COMPLETE_MANUAL = "GREEN_NWR_ROOKIE_DRAFT_CLASS_COMPLETE_WITH_MANUAL_REVIEW_ASSETS"
YELLOW_IDENTITY_GAPS = "YELLOW_NWR_ROOKIE_DRAFT_ELIGIBILITY_PARTIAL_IDENTITY_GAPS_REMAIN"
BLOCKED_SOURCE = "BLOCKED_NWR_ROOKIE_DRAFT_CLASS_SOURCE_INCOMPLETE"
RED_UNSAFE = "RED_NWR_ROOKIE_DRAFT_SAFETY_STILL_UNACCEPTABLE"


@dataclass(frozen=True)
class RookieDraftEligibilityOverlay:
    rows: tuple[dict[str, Any], ...]
    errors: tuple[str, ...]
    summary: dict[str, Any]
    source_hashes: dict[str, str]

    @property
    def by_asset_id(self) -> dict[str, dict[str, Any]]:
        return {str(row["asset_id"]): row for row in self.rows}


def reconcile_rookie_draft_readiness(
    official_rows: Sequence[Mapping[str, Any]],
    *,
    surface_asset_ids: Mapping[str, Sequence[str]],
    source_errors: Sequence[str] = (),
) -> dict[str, Any]:
    """Reconcile official assets against independently composed workflow surfaces.

    The eligibility overlay establishes the official 80-row class.  This gate does
    not trust the overlay's own visibility booleans: callers must supply the asset
    IDs that survived each real registry/API/workflow composition step.
    """

    official_ids = [str(row.get("asset_id") or "").strip() for row in official_rows]
    official_set = {asset_id for asset_id in official_ids if asset_id}
    surface_sequences = {
        str(surface): [str(asset_id).strip() for asset_id in asset_ids if str(asset_id).strip()]
        for surface, asset_ids in surface_asset_ids.items()
    }
    surface_sets = {
        surface: set(asset_ids) for surface, asset_ids in surface_sequences.items()
    }
    missing_by_surface = {
        surface: [asset_id for asset_id in official_ids if asset_id not in asset_ids]
        for surface, asset_ids in surface_sets.items()
    }
    duplicate_by_surface = {
        surface: [
            asset_id
            for asset_id, count in Counter(asset_ids).items()
            if asset_id in official_set and count > 1
        ]
        for surface, asset_ids in surface_sequences.items()
    }
    surface_gap_asset_ids = sorted(
        set().union(
            *(set(asset_ids) for asset_ids in missing_by_surface.values()),
            *(set(asset_ids) for asset_ids in duplicate_by_surface.values()),
        )
        if missing_by_surface or duplicate_by_surface
        else set()
    )
    position_counts = {
        position: sum(str(row.get("position") or "").strip() == position for row in official_rows)
        for position in SUPPORTED_POSITIONS
    }
    scored = sum(bool(row.get("model_score_eligible")) for row in official_rows)
    manual = sum(
        str(row.get("authority_status") or "") == "UNSCORED_MANUAL_REVIEW"
        for row in official_rows
    )
    unresolved = sum(
        str(row.get("authority_status") or "") == "BLOCKED_IDENTITY"
        for row in official_rows
    )
    exact = sum(
        str(row.get("identity_status") or "") == "EXACT_GOVERNED_IDENTITY"
        for row in official_rows
    )
    duplicate_asset_ids = len(official_ids) - len(official_set)
    source_invalid = bool(source_errors) or any(
        (
            len(official_rows) != EXPECTED_OFFICIAL_COUNT,
            position_counts != EXPECTED_POSITION_COUNTS,
            duplicate_asset_ids != 0,
            scored != EXPECTED_SCORED_COUNT,
            manual + unresolved != EXPECTED_MANUAL_REVIEW_COUNT,
        )
    )
    if source_invalid:
        verdict = BLOCKED_SOURCE
    elif surface_gap_asset_ids:
        verdict = RED_UNSAFE
    elif unresolved:
        verdict = YELLOW_IDENTITY_GAPS
    else:
        verdict = GREEN_COMPLETE_MANUAL
    ready = verdict == GREEN_COMPLETE_MANUAL
    registry_missing = missing_by_surface.get("registry", [])
    selectable_missing = missing_by_surface.get("selectable", [])
    draft_cockpit_missing = missing_by_surface.get("draft_cockpit", [])
    draft_pool_ids = surface_sets.get("draft_cockpit", surface_sets.get("draftable", set()))
    return {
        "verdict": verdict,
        "ready": ready,
        "readiness_scope": "POST_COMPOSITION_WORKFLOW_RECONCILIATION",
        "official_drafted": len(official_rows),
        "position_counts": position_counts,
        "exact_identity": exact,
        "scored": scored,
        "manual_review": manual,
        "unresolved": unresolved,
        "missing_from_registry": len(registry_missing),
        "missing_from_draftable_pool": len(draft_cockpit_missing),
        "duplicate_asset_ids": duplicate_asset_ids,
        "refresh_available": sum(bool(row.get("refresh_available")) for row in official_rows),
        "review_asset_ids": [
            str(row.get("asset_id") or "")
            for row in official_rows
            if not bool(row.get("model_score_eligible"))
        ],
        "missing_asset_ids": surface_gap_asset_ids,
        "surface_gap_asset_ids": surface_gap_asset_ids,
        "nonselectable_asset_ids": selectable_missing,
        "draftable_asset_ids": sorted(official_set & draft_pool_ids),
        "missing_by_surface": missing_by_surface,
        "duplicate_by_surface": duplicate_by_surface,
        "validated_surfaces": sorted(surface_sets),
        "source_errors": list(dict.fromkeys(str(error) for error in source_errors if error)),
        "alert_code": "ROOKIE_DRAFT_CLASS_COMPLETE" if ready else "ROOKIE_DRAFT_READINESS_REVIEW",
        "alert_title": (
            "Rookie Draft Class Complete"
            if ready
            else (
                "Rookie Draft Readiness: "
                f"{len(surface_gap_asset_ids) + unresolved} assets need review"
            )
        ),
        "alert_message": (
            f"{len(official_rows)} official QB/RB/WR/TE assets survived every validated "
            f"workflow surface: {scored} scored, {manual} manual review, "
            f"{len(surface_gap_asset_ids)} missing or duplicated."
        ),
    }


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return [
            {str(key): str(value or "").strip() for key, value in row.items()}
            for row in csv.DictReader(handle)
        ]


def _slug(value: str) -> str:
    return "-".join(value.lower().replace("'", "").split())


def _truth(value: object) -> bool:
    return str(value if value is not None else "").strip().casefold() in {
        "1",
        "true",
        "yes",
        "y",
    }


def _governed_namespace(player_id: str) -> str:
    return "GSIS" if re.fullmatch(r"00-\d{7}", player_id) else "GOVERNED_REGISTRY"


def _pick_index(
    rows: Sequence[Mapping[str, object]],
    field: str,
    *,
    label: str,
    errors: list[str],
) -> dict[str, Mapping[str, object]]:
    indexed: dict[str, Mapping[str, object]] = {}
    for row in rows:
        pick = str(row.get(field) or "").strip()
        if not pick:
            errors.append(f"{label} contains a row without an official overall pick")
            continue
        if pick in indexed:
            errors.append(f"{label} contains duplicate official pick {pick}")
            continue
        indexed[pick] = row
    return indexed


def build_rookie_draft_eligibility_overlay(
    rookie_rows: Sequence[Mapping[str, object]],
    live_identity_rows: Sequence[Mapping[str, object]],
    blocker_rows: Sequence[Mapping[str, object]],
    *,
    source_hashes: Mapping[str, str] | None = None,
) -> RookieDraftEligibilityOverlay:
    """Compose the full official class using exact official-pick reconciliation."""

    errors: list[str] = []
    official = [
        row
        for row in rookie_rows
        if str(row.get("position") or "").strip().upper() in SUPPORTED_POSITIONS
    ]
    live = [
        row
        for row in live_identity_rows
        if str(row.get("draft_position") or "").strip().upper() in SUPPORTED_POSITIONS
    ]
    official_by_pick = _pick_index(
        official, "overall_pick", label="Frozen Rookie Review", errors=errors
    )
    live_by_pick = _pick_index(
        live, "draft_pick", label="Live rookie identity authority", errors=errors
    )
    blocker_by_pick = _pick_index(
        blocker_rows, "overall_pick", label="Frozen blocker inventory", errors=errors
    )

    if len(official) != EXPECTED_OFFICIAL_COUNT:
        errors.append(
            f"Official supported-position class must contain {EXPECTED_OFFICIAL_COUNT} rows; "
            f"found {len(official)}"
        )
    if len(live) != EXPECTED_OFFICIAL_COUNT:
        errors.append(
            "Live identity authority must contain "
            f"{EXPECTED_OFFICIAL_COUNT} rows; found {len(live)}"
        )
    position_counts = {
        position: sum(
            str(row.get("position") or "").strip().upper() == position for row in official
        )
        for position in SUPPORTED_POSITIONS
    }
    if position_counts != EXPECTED_POSITION_COUNTS:
        errors.append(f"Official class position counts do not match: {position_counts}")
    if set(official_by_pick) != set(live_by_pick):
        missing_live = sorted(
            set(official_by_pick) - set(live_by_pick), key=lambda value: int(value)
        )
        extra_live = sorted(set(live_by_pick) - set(official_by_pick), key=lambda value: int(value))
        errors.append(
            "Official/live pick universes differ; "
            f"missing live={missing_live or 'none'}, extra live={extra_live or 'none'}"
        )

    output: list[dict[str, Any]] = []
    seen_live_ids: set[str] = set()
    for frozen in official:
        pick = str(frozen.get("overall_pick") or "").strip()
        current = live_by_pick.get(pick, {})
        frozen_name = str(frozen.get("player_name") or "").strip()
        frozen_position = str(frozen.get("position") or "").strip().upper()
        frozen_round = str(frozen.get("draft_round") or "").strip()
        current_name = str(current.get("draft_name") or "").strip()
        current_position = str(current.get("draft_position") or "").strip().upper()
        current_round = str(current.get("draft_round") or "").strip()
        if current and (
            current_name != frozen_name
            or current_position != frozen_position
            or current_round != frozen_round
        ):
            errors.append(
                f"Official pick {pick} identity receipt mismatch: "
                f"{frozen_name}/{frozen_position}/R{frozen_round} vs "
                f"{current_name}/{current_position}/R{current_round}"
            )

        frozen_player_id = str(frozen.get("player_id") or "").strip()
        live_player_id = str(current.get("player_id") or "").strip()
        identity_conflict = _truth(current.get("identity_conflict"))
        exact_identity = bool(live_player_id) and not identity_conflict
        if exact_identity:
            if live_player_id in seen_live_ids:
                errors.append(f"Live governed player ID is duplicated: {live_player_id}")
            seen_live_ids.add(live_player_id)

        score = str(frozen.get("final_review_score") or "").strip()
        rank = str(frozen.get("overall_review_rank") or "").strip()
        model_score_eligible = bool(score and rank)
        if bool(score) != bool(rank):
            errors.append(f"Frozen score/rank completeness differs for official pick {pick}")

        official_draft_asset_id = f"nflverse-draft:2026:{pick}"
        asset_id = (
            f"rookie:{frozen_player_id}"
            if frozen_player_id
            else f"blocked-rookie:{_slug(frozen_name)}"
        )
        governed_draft_identity = bool(pick and frozen_name and frozen_position and frozen_round)
        draft_eligible = governed_draft_identity
        selectable = governed_draft_identity
        blocker = blocker_by_pick.get(pick, {})
        refresh_available = bool(live_player_id and not frozen_player_id and blocker)
        previous_block_reason = str(blocker.get("blocking_reason") or "").strip()

        if model_score_eligible:
            authority_status = "SCORED_REVIEW_ONLY"
            score_status = "Rookie Review score available"
            score_block_reason = ""
        elif exact_identity:
            authority_status = "UNSCORED_MANUAL_REVIEW"
            score_status = "No admitted Rookie Review score — manual review required"
            score_block_reason = (
                "The frozen Rookie Review did not admit a score. Current exact identity and "
                "draft facts update eligibility only; no replacement score or rank was invented."
            )
        else:
            authority_status = "BLOCKED_IDENTITY"
            score_status = "No admitted Rookie Review score — identity review required"
            score_block_reason = (
                "The official draft asset is uniquely selectable, but an exact governed player "
                "identity is not yet available for model scoring."
            )

        current_team = str(current.get("current_team") or "").strip()
        output.append(
            {
                "official_draft_asset_id": official_draft_asset_id,
                "asset_id": asset_id,
                "season": 2026,
                "overall_pick": int(pick) if pick.isdigit() else None,
                "draft_round": int(frozen_round) if frozen_round.isdigit() else None,
                "player_name": frozen_name,
                "position": frozen_position,
                "team": current_team or str(frozen.get("nfl_team") or "").strip(),
                "frozen_team": str(frozen.get("nfl_team") or "").strip(),
                "frozen_model_player_id": frozen_player_id,
                "live_governed_player_id": live_player_id,
                "live_player_id_namespace": (
                    _governed_namespace(live_player_id) if exact_identity else "UNRESOLVED"
                ),
                "identity_status": (
                    "EXACT_GOVERNED_IDENTITY" if exact_identity else "BLOCKED_IDENTITY"
                ),
                "identity_method": str(current.get("identity_method") or "").strip(),
                "identity_conflict": identity_conflict,
                "asset_exists": True,
                "draft_eligible": draft_eligible,
                "draft_eligibility_basis": (
                    "EXACT_GOVERNED_PLAYER_ID"
                    if exact_identity
                    else "UNIQUE_GOVERNED_OFFICIAL_DRAFT_ASSET"
                ),
                "model_score_eligible": model_score_eligible,
                "authority_status": authority_status,
                "score_status": score_status,
                "frozen_rank": int(rank) if rank.isdigit() else None,
                "frozen_score": float(score) if score else None,
                "searchable": True,
                "selectable": selectable,
                "draftable": draft_eligible,
                "asset_explorer_visible": True,
                "detail_available": True,
                "compare_selectable": selectable,
                "trade_selectable": selectable,
                "draft_cockpit_selectable": selectable,
                "refresh_available": refresh_available,
                "rebuild_needed": not model_score_eligible,
                "rebuild_status": (
                    "NO_REBUILD_NEEDED"
                    if model_score_eligible
                    else "YES_SEPARATE_GOVERNED_REBUILD"
                ),
                "previous_identity_status": str(frozen.get("identity_status") or "").strip(),
                "previous_block_reason": previous_block_reason,
                "score_block_reason": score_block_reason,
                "owner_reason": (
                    score_block_reason or "Frozen Rookie Review score remains admitted."
                ),
                "source_rank_label": str(frozen.get("rank_label") or "").strip(),
                "source_score_label": str(frozen.get("score_label") or "").strip(),
                "source_tier": str(frozen.get("tier") or "").strip(),
                "source_confidence": str(frozen.get("evidence_confidence") or "").strip(),
                "source_warnings": str(frozen.get("warning_codes") or "").strip(),
                "age_at_draft": str(frozen.get("age_at_draft") or "").strip(),
            }
        )

    output.sort(
        key=lambda row: (
            0 if row["model_score_eligible"] else 1,
            row["frozen_rank"] if row["frozen_rank"] is not None else 999,
            row["overall_pick"] if row["overall_pick"] is not None else 999,
            row["player_name"],
        )
    )
    if len({str(row["asset_id"]) for row in output}) != len(output):
        errors.append("Rookie eligibility overlay contains duplicate stable asset IDs")

    scored = sum(bool(row["model_score_eligible"]) for row in output)
    manual = sum(row["authority_status"] == "UNSCORED_MANUAL_REVIEW" for row in output)
    unresolved = sum(row["authority_status"] == "BLOCKED_IDENTITY" for row in output)
    exact = sum(row["identity_status"] == "EXACT_GOVERNED_IDENTITY" for row in output)
    missing_registry = sum(not str(row.get("asset_id") or "") for row in output)
    missing_draftable = sum(not bool(row["draftable"]) for row in output)
    if not errors and scored != EXPECTED_SCORED_COUNT:
        errors.append(f"Frozen scored count must remain {EXPECTED_SCORED_COUNT}; found {scored}")
    if not errors and manual + unresolved != EXPECTED_MANUAL_REVIEW_COUNT:
        errors.append(
            "Frozen unscored count must remain "
            f"{EXPECTED_MANUAL_REVIEW_COUNT}; found {manual + unresolved}"
        )

    if errors:
        verdict = BLOCKED_SOURCE
    elif missing_registry or missing_draftable:
        verdict = RED_UNSAFE
    elif unresolved:
        verdict = YELLOW_IDENTITY_GAPS
    else:
        verdict = GREEN_COMPLETE_MANUAL
    ready = verdict == GREEN_COMPLETE_MANUAL
    summary = {
        "verdict": verdict,
        "ready": ready,
        "official_drafted": len(output),
        "position_counts": position_counts,
        "exact_identity": exact,
        "scored": scored,
        "manual_review": manual,
        "unresolved": unresolved,
        "missing_from_registry": missing_registry,
        "missing_from_draftable_pool": missing_draftable,
        "duplicate_asset_ids": len(output) - len({str(row["asset_id"]) for row in output}),
        "refresh_available": sum(bool(row["refresh_available"]) for row in output),
        "review_asset_ids": [
            str(row["asset_id"]) for row in output if not row["model_score_eligible"]
        ],
        "alert_code": (
            "ROOKIE_DRAFT_CLASS_COMPLETE" if ready else "ROOKIE_DRAFT_READINESS_REVIEW"
        ),
        "alert_title": (
            "Rookie Draft Class Complete"
            if ready
            else f"Rookie Draft Readiness: {unresolved + missing_draftable} players need review"
        ),
        "alert_message": (
            f"{len(output)} official QB/RB/WR/TE assets are searchable and draftable: "
            f"{scored} scored, {manual} manual review, {missing_draftable} missing."
        ),
    }
    return RookieDraftEligibilityOverlay(
        rows=tuple(output),
        errors=tuple(dict.fromkeys(errors)),
        summary=summary,
        source_hashes=dict(source_hashes or {}),
    )


def load_rookie_draft_eligibility_overlay(
    *, repo_root: str | Path = REPO_ROOT
) -> RookieDraftEligibilityOverlay:
    root = Path(repo_root)
    paths = {
        "Rookie Review": root / ROOKIE_BOARD_RELATIVE,
        "Blocked Rookie Inventory": root / BLOCKED_ROOKIES_RELATIVE,
        "Live Rookie Identity": root / LIVE_IDENTITY_RELATIVE,
    }
    expected = {
        "Rookie Review": ROOKIE_BOARD_SHA256,
        "Blocked Rookie Inventory": BLOCKED_ROOKIES_SHA256,
        "Live Rookie Identity": LIVE_IDENTITY_SHA256,
    }
    errors: list[str] = []
    hashes: dict[str, str] = {}
    for label, path in paths.items():
        if not path.is_file():
            errors.append(f"{label} source is missing")
            continue
        hashes[label] = file_sha256(path)
        if hashes[label] != expected[label]:
            errors.append(f"{label} hash mismatch")
    if errors:
        return RookieDraftEligibilityOverlay(
            rows=(),
            errors=tuple(errors),
            summary={
                "verdict": BLOCKED_SOURCE,
                "ready": False,
                "official_drafted": 0,
                "position_counts": {},
                "exact_identity": 0,
                "scored": 0,
                "manual_review": 0,
                "unresolved": 0,
                "missing_from_registry": 0,
                "missing_from_draftable_pool": 0,
                "duplicate_asset_ids": 0,
                "refresh_available": 0,
                "review_asset_ids": [],
                "alert_code": "ROOKIE_DRAFT_READINESS_REVIEW",
                "alert_title": "Rookie Draft Readiness unavailable",
                "alert_message": "The governed official rookie class could not be verified.",
            },
            source_hashes=hashes,
        )

    return build_rookie_draft_eligibility_overlay(
        _read_rows(paths["Rookie Review"]),
        _read_rows(paths["Live Rookie Identity"]),
        _read_rows(paths["Blocked Rookie Inventory"]),
        source_hashes=hashes,
    )
