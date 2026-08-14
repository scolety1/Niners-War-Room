"""Build the deterministic NWR Rookie Intelligence V2 review packet.

The packet is research-only.  It preserves every frozen 2026 Rookie Review
formula output and reconstructs the seven formerly blocked rookies under a
separate, proposed identity contract.  It never writes runtime/model assets.
"""

# Long governed labels and Markdown templates are intentionally preserved verbatim.
# ruff: noqa: E402, E501

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import sys
import tempfile
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

REPO_IMPORT_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_IMPORT_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_IMPORT_ROOT))

from src.services import model_v4_2026_rookie_board_review_service as frozen_service
from src.services.model_v4_confidence_missingness_service import (
    CONFIDENCE_REVIEW_HEADER,
    build_confidence_missingness_layer,
)
from src.services.model_v4_sprint12_13_review_service import (
    PROSPECT_REVIEW_HEADER,
    build_sprint12_13_review_outputs,
)
from src.services.model_v4_sprint14e_rookie_draft_review_service import (
    POSITION_FORMAT_FACTORS,
    build_rookie_draft_review_outputs,
)

PACKET = Path("docs/hq/model/nwr_rookie_intelligence_v2_20260814")
FACTUAL_OVERLAY = Path(
    "docs/hq/product/nwr_rookie_intelligence_v2_factual_overlay_v1_20260814/"
    "MANUAL_REVIEW_FACTUAL_COMPONENT_OVERLAY.csv"
)
VERDICT = "GREEN_NWR_ROOKIE_REVIEW_REFRESH_CANDIDATE_READY_FOR_OWNER_APPROVAL"
CANDIDATE_AUTHORITY = "ROOKIE_REVIEW_REFRESH_CANDIDATE_REVIEW_ONLY"
STRICT_BLOCK = "STILL_BLOCKED_REQUIRED_EVIDENCE"
BRIDGE_PENDING = "READY_WITH_GOVERNED_MISSINGNESS_PENDING_IDENTITY_BRIDGE_APPROVAL"
MANUAL_NAMES = {
    "De'Zhaun Stribling",
    "Carson Beck",
    "Oscar Delp",
    "Colbie Young",
    "Nicholas Singleton",
    "Joe Royer",
    "Deion Burks",
}
REQUIRED_FILES = (
    "EXECUTIVE_VERDICT.md",
    "CURRENT_CLASS_COMPLETENESS.csv",
    "SEVEN_MANUAL_REVIEW_AUDIT.csv",
    "RANK_VS_SCORE_AUDIT.csv",
    "ROOKIE_TIER_ANALYSIS.md",
    "HISTORICAL_ROOKIE_FRAME.md",
    "MODEL_GAUNTLET.csv",
    "TEMPORAL_VALIDATION.csv",
    "POSITION_RESULTS.csv",
    "CONFIDENCE_GATE_RESULTS.csv",
    "CURRENT_2026_BOARD.csv",
    "CURRENT_CLASS_EXPLANATIONS.md",
    "ROOKIE_DATA_GAPS.md",
    "DESKTOP_INTEGRATION.md",
    "DRAFT_READINESS.md",
    "AUTHORITY_PRESERVATION.md",
    "VALIDATION_RESULTS.md",
    "NEXT_ACTION.md",
    "MANIFEST.json",
)

FROZEN_BOARD = Path(
    "docs/hq/master/nwr_model_v4_2026_rookie_board_review_v1_20260730/"
    "MODEL_V4_2026_ROOKIE_BOARD_REVIEW.csv"
)
FROZEN_BLOCKERS = FROZEN_BOARD.with_name("2026_ROOKIE_IDENTITY_BLOCKERS.csv")
FORMULA_RECONCILIATION = FROZEN_BOARD.with_name("FORMULA_RECONCILIATION_RESULTS.csv")
LIVE_IDENTITY = Path(
    "docs/hq/model/nwr_redraft_2026_rookie_projection_candidate_v1_20260809/"
    "CURRENT_2026_IDENTITY_AND_ROLE.csv"
)
REDRAFT = LIVE_IDENTITY.with_name("GOVERNED_ROOKIE_PROJECTION_SNAPSHOT.csv")
REDRAFT_BLOCKED = LIVE_IDENTITY.with_name("BLOCKED_2026_ROOKIES.csv")
RECONCILIATION = Path(
    "docs/hq/product/nwr_rookie_draft_eligibility_recovery_v1_20260813/"
    "FULL_DRAFT_CLASS_RECONCILIATION.csv"
)
RESEARCH = Path(
    "docs/hq/model/nwr_unified_research_preview_v1_20260808/"
    "UNIFIED_DYNASTY_RESEARCH_PREVIEW.csv"
)
NEIGHBORHOODS = RESEARCH.with_name("ROOKIE_VETERAN_NEIGHBORHOODS.csv")
CONFIG = Path("config/model_v4_2026_compatible_input_pack_v1.json")

SOURCE_HASHES = {
    CONFIG: "6ae6ee6d7284230cd2b9b181e8a241ae5fc00226a845b784b482aea1d6d06253",
    FROZEN_BOARD: "06853164a41cd9715accfc3c4f3e54d0cc915be6c55ebab040de6fc0abd96c2f",
    FROZEN_BLOCKERS: "361011524dfbabc62cecaf4286d201b219e275a5fa8b43b57c93017eca56d19a",
    FORMULA_RECONCILIATION: "55daca4ee45c82ad76c278471f9003f0940c750beec834170b1f288b2e0add23",
    LIVE_IDENTITY: "f4ae6106f5302c59f23d83a27c006a894c5660b3058a011e5b2f16c6a2c79ff9",
    RECONCILIATION: "49f6eeba806dfb31cf56fb627c6e1be0c554dad29fa012bfa1fa228a4a15bc15",
    RESEARCH: "8ab1bf7e1d33736d7609c7f8373cc7031dc24afed026278b8754a659a4af5dc0",
    NEIGHBORHOODS: "5ff806c997d385fcc85911b419fad53a9bf6af4f1f8c9da6b7cdc6a6bf7bcb82",
    REDRAFT: "e1636eb729441aed91187cf8170c05279090213ef0c2426269a63d95ec59c4d7",
    REDRAFT_BLOCKED: "5df49e6d63f6425d3eaa65d99a65b69c59243848e2950b25c35eed08247d3720",
}


@dataclass(frozen=True)
class BuildState:
    repo: Path
    frozen: list[dict[str, str]]
    candidate: list[dict[str, Any]]
    candidate_sources: list[dict[str, Any]]
    matrix: list[dict[str, Any]]
    profiles: dict[str, dict[str, Any]]
    live: dict[int, dict[str, str]]
    reconciliation: dict[int, dict[str, str]]
    research: dict[str, dict[str, str]]
    neighborhoods: dict[str, dict[str, str]]
    redraft: dict[str, dict[str, str]]
    redraft_blocked: dict[str, dict[str, str]]


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def _csv(rows: Iterable[dict[str, Any]], fields: Iterable[str]) -> str:
    out = io.StringIO(newline="")
    writer = csv.DictWriter(
        out, fieldnames=tuple(fields), extrasaction="ignore", lineterminator="\n"
    )
    writer.writeheader()
    writer.writerows(rows)
    return out.getvalue()


def _fmt(value: Any) -> Any:
    if value in (None, ""):
        return ""
    if isinstance(value, float):
        return f"{value:.6f}".rstrip("0").rstrip(".")
    return value


def _verify_sources(repo: Path) -> None:
    for relative, expected in SOURCE_HASHES.items():
        actual = _sha(repo / relative)
        if actual != expected:
            raise RuntimeError(f"source hash drift: {relative}: {actual}")


def _candidate_records(
    repo: Path,
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[int, dict[str, str]]]:
    config = json.loads((repo / CONFIG).read_text(encoding="utf-8"))
    sources = frozen_service._load_sources(repo, config)
    live = {int(row["draft_pick"]): row for row in _rows(repo / LIVE_IDENTITY)}
    players = pd.read_parquet(
        Path(config["nflverse"]["players_root"]) / "raw" / "players.parquet"
    )
    combine = pd.read_parquet(
        Path(config["nflverse"]["combine_root"]) / "raw" / "combine.parquet"
    )
    by_pfr_player = {
        frozen_service._text(row.get("pfr_id")): row
        for _, row in players.iterrows()
        if frozen_service._text(row.get("pfr_id"))
    }
    by_gsis_player = {
        frozen_service._text(row.get("gsis_id")): row
        for _, row in players.iterrows()
        if frozen_service._text(row.get("gsis_id"))
    }
    by_pfr_combine = {
        frozen_service._text(row.get("pfr_id")): row
        for _, row in combine.loc[combine["season"].eq(2026)].iterrows()
        if frozen_service._text(row.get("pfr_id"))
    }
    candidates = [dict(row) for row in sources["exact"]]
    for blocked in sources["blocked"]:
        pick = int(blocked["overall_pick"])
        current = live[pick]
        if current["draft_name"] != blocked["player_name"]:
            raise RuntimeError(f"official-pick/live-name mismatch at {pick}")
        player = by_pfr_player.get(blocked["pfr_player_id"])
        if player is None:
            player = by_gsis_player.get(current["player_id"])
        if player is None or not frozen_service._text(player.get("birth_date")):
            raise RuntimeError(f"birth authority missing at pick {pick}")
        candidates.append(
            {
                **blocked,
                "player_id": current["player_id"],
                "birth_date": frozen_service._text(player.get("birth_date")),
                "combine": by_pfr_combine.get(blocked["pfr_player_id"]),
                "identity_method": "PROPOSED_OFFICIAL_PICK_PLUS_PINNED_LIVE_ID_BRIDGE",
                "name_used_as_identity": False,
            }
        )
    candidates.sort(key=lambda row: int(row["overall_pick"]))
    if len(candidates) != 80 or len({row["player_id"] for row in candidates}) != 80:
        raise RuntimeError("candidate identity set is not 80 unique IDs")
    return sources, candidates, live


def _run_candidate(repo: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, dict[str, Any]]]:
    sources, candidates, _ = _candidate_records(repo)
    config = sources["config"]
    candidate_sources = {**sources, "exact": candidates, "blocked": []}
    profiles = frozen_service._build_college_profiles(candidates, sources["cfbd_root"])
    matrix, coverage, warnings = frozen_service._build_prospect_inputs(
        candidate_sources, profiles, config
    )
    with tempfile.TemporaryDirectory(prefix="nwr_rookie_v2_") as raw:
        root = Path(raw)
        paths = frozen_service._write_input_pack(
            root / "inputs", matrix, coverage, warnings, candidate_sources, config
        )
        confidence = build_confidence_missingness_layer(
            nfl_matrix_path=paths["nfl_matrix"],
            admitted_prospect_matrix_path=paths["prospect_matrix"],
            historical_backtest_matrix_path=paths["historical_matrix"],
            source_coverage_matrix_path=paths["coverage"],
            warning_matrix_path=paths["warnings"],
        )
        confidence_path = root / "confidence.csv"
        frozen_service._write_csv(
            confidence_path, CONFIDENCE_REVIEW_HEADER, confidence.review_rows
        )
        sprint = build_sprint12_13_review_outputs(
            admitted_prospect_matrix_path=paths["prospect_matrix"],
            confidence_rows_path=confidence_path,
            rookie_age_rows_path=paths["age"],
            draft_capital_rows_path=paths["draft_capital"],
            current_value_rows_path=paths["empty_current"],
            current_component_rows_path=paths["empty_components"],
            current_receipt_rows_path=paths["empty_receipts"],
            current_warning_rows_path=paths["empty_warnings"],
        )
        prospect_path = root / "prospects.csv"
        frozen_service._write_csv(
            prospect_path, PROSPECT_REVIEW_HEADER, sprint.prospect_rows
        )
        sprint14 = build_rookie_draft_review_outputs(
            prospect_rows_path=prospect_path,
            pick_inventory_path=paths["empty_picks"],
            roster_state_path=paths["empty_roster"],
        )
        board = frozen_service._build_complete_board(
            sources=candidate_sources,
            prospect_rows=sprint.prospect_rows,
            component_rows=sprint.prospect_component_rows,
            sprint14e_rows=sprint14.rookie_board_rows,
        )
    return board, matrix, profiles


def load_state(repo: Path) -> BuildState:
    _verify_sources(repo)
    frozen = _rows(repo / FROZEN_BOARD)
    candidate, matrix, profiles = _run_candidate(repo)
    _, candidate_sources, live = _candidate_records(repo)
    reconciliation = {
        int(row["overall_pick"]): row for row in _rows(repo / RECONCILIATION)
    }
    research_rows = [
        row for row in _rows(repo / RESEARCH) if row["asset_type"] == "ROOKIE"
    ]
    research = {row["source_asset_id"].split(":", 1)[-1]: row for row in research_rows}
    neighborhoods = {
        row["rookie_governed_id"]: row for row in _rows(repo / NEIGHBORHOODS)
    }
    redraft = {row["player_id"]: row for row in _rows(repo / REDRAFT)}
    redraft_blocked = {
        row["player_id"]: row for row in _rows(repo / REDRAFT_BLOCKED)
    }
    state = BuildState(
        repo=repo,
        frozen=frozen,
        candidate=candidate,
        candidate_sources=candidate_sources,
        matrix=matrix,
        profiles=profiles,
        live=live,
        reconciliation=reconciliation,
        research=research,
        neighborhoods=neighborhoods,
        redraft=redraft,
        redraft_blocked=redraft_blocked,
    )
    _validate_state(state)
    return state


PARITY_FIELDS = (
    "production_component",
    "market_share_component",
    "draft_capital_component",
    "athletic_component",
    "recruiting_component",
    "age_component",
    "weighted_component_sum",
    "raw_model_v4_score",
    "confidence_cap",
    "final_review_score",
    "sprint14e_format_score",
    "missing_components",
    "warning_codes",
    "evidence_confidence",
    "source_limit_state",
)


def _validate_state(state: BuildState) -> None:
    frozen_scored = [row for row in state.frozen if row["final_review_score"]]
    frozen_blocked = [row for row in state.frozen if not row["final_review_score"]]
    if (len(state.frozen), len(frozen_scored), len(frozen_blocked)) != (80, 73, 7):
        raise RuntimeError("frozen 80/73/7 reconciliation failed")
    if len(state.candidate) != 80 or any(not row["final_review_score"] for row in state.candidate):
        raise RuntimeError("candidate board is not 80 scored review-only rows")
    if Counter(row["position"] for row in state.candidate) != Counter(
        {"QB": 10, "RB": 12, "WR": 36, "TE": 22}
    ):
        raise RuntimeError("official class position counts drifted")
    candidate_by_pick = {int(row["overall_pick"]): row for row in state.candidate}
    for frozen in frozen_scored:
        candidate = candidate_by_pick[int(frozen["overall_pick"])]
        for field in PARITY_FIELDS:
            if str(candidate[field]) != str(frozen[field]):
                raise RuntimeError(
                    f"73-row formula preservation failed: {frozen['player_name']} {field}"
                )
    manual = [row for row in state.candidate if row["player_name"] in MANUAL_NAMES]
    if len(manual) != 7:
        raise RuntimeError("manual-review identity set drift")
    if any(row["recruiting_component"] not in ("", None) for row in state.candidate):
        raise RuntimeError("missing recruiting was converted to numeric evidence")
    for field in (
        "production_component", "market_share_component", "draft_capital_component",
        "age_component", "age_at_draft",
    ):
        if any(row[field] in ("", None) for row in state.candidate):
            raise RuntimeError(f"candidate required field incomplete: {field}")
    if Counter(str(row["confidence_cap"]) for row in state.candidate) != Counter(
        {"0.88": 60, "0.84": 20}
    ):
        raise RuntimeError("candidate confidence-cap distribution drift")
    if sum(row["athletic_component"] not in ("", None) for row in state.candidate) != 18:
        raise RuntimeError("formula athletic support count drift")
    if len(state.live) != 80 or len(state.research) != 80 or len(state.neighborhoods) != 73:
        raise RuntimeError("live/research authority count drift")
    if (len(state.redraft), len(state.redraft_blocked)) != (78, 2):
        raise RuntimeError("redraft 78/2 authority partition drift")


def _candidate_index(state: BuildState) -> dict[int, dict[str, Any]]:
    return {int(row["overall_pick"]): row for row in state.candidate}


def _frozen_index(state: BuildState) -> dict[int, dict[str, str]]:
    return {int(row["overall_pick"]): row for row in state.frozen}


def _matrix_index(state: BuildState) -> dict[str, dict[str, Any]]:
    return {str(row["canonical_prospect_key"]): row for row in state.matrix}


def _profile_context(profile: dict[str, Any], lane: str) -> str:
    if not profile:
        return "missing_not_zero"
    if lane == "production":
        payload = {
            "latest_season": profile.get("latest_season"),
            "latest": profile.get("latest", {}).get("values", {}),
            "career_yards": profile.get("career", {}),
        }
    else:
        payload = {
            "latest_season": profile.get("latest_season"),
            "latest_shares": profile.get("latest", {}).get("shares", {}),
            "max_shares": profile.get("max_share", {}),
        }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def _explanation(row: dict[str, Any], frozen: dict[str, str] | None) -> str:
    components = {
        "production": row["production_component"],
        "market share": row["market_share_component"],
        "draft capital": row["draft_capital_component"],
        "athletic": row["athletic_component"],
        "age": row["age_component"],
    }
    numeric = [(name, float(value)) for name, value in components.items() if value not in ("", None)]
    numeric.sort(key=lambda item: item[1], reverse=True)
    strengths = ", ".join(f"{name} {value:.1f}" for name, value in numeric[:2])
    missing = str(row["missing_components"]).replace("_prior", "").replace("|", ", ")
    if frozen is None or not frozen.get("final_review_score"):
        prefix = "Candidate reconstruction only; strict frozen replay remains identity-blocked."
    else:
        prefix = "Frozen score is preserved exactly; candidate placement only reflects insertion of seven rows."
    return f"{prefix} Strongest admitted signals: {strengths}. Missing: {missing or 'none'}."


BOARD_FIELDS = (
    "official_draft_asset_id",
    "stable_asset_id",
    "overall_pick",
    "draft_round",
    "live_player_id",
    "frozen_model_player_id",
    "player",
    "position",
    "draft_team",
    "current_team",
    "current_status",
    "age_at_draft",
    "production_component",
    "production_context",
    "market_share_component",
    "market_share_context",
    "draft_capital_component",
    "athletic_component",
    "athletic_context",
    "recruiting_component",
    "recruiting_context",
    "age_component",
    "missing_components",
    "warning_codes",
    "frozen_score",
    "frozen_rank",
    "frozen_position_rank",
    "frozen_evidence_band",
    "refresh_candidate_score",
    "refresh_candidate_rank",
    "refresh_candidate_position_rank",
    "refresh_candidate_format_score",
    "draft_range_band",
    "manual_review_status",
    "strict_frozen_replay_status",
    "identity_contract_status",
    "research_rank",
    "research_band",
    "veteran_neighborhood_above",
    "veteran_neighborhood_below",
    "redraft_projection_status",
    "redraft_projection_low",
    "redraft_projection_high",
    "current_role_freshness",
    "explanation",
    "candidate_authority",
    "allowed_use",
    "blocked_use",
)

FACTUAL_OVERLAY_FIELDS = (
    "official_draft_asset_id",
    "stable_asset_id",
    "overall_pick",
    "live_player_id",
    "player",
    "position",
    "age_at_draft",
    "production_component",
    "market_share_component",
    "draft_capital_component",
    "athletic_component",
    "recruiting_component",
    "age_component",
    "missing_components",
    "factual_overlay_authority",
    "allowed_use",
    "blocked_use",
)


def _board_rows(state: BuildState) -> list[dict[str, Any]]:
    frozen_by_pick = _frozen_index(state)
    matrix_by_id = _matrix_index(state)
    rows: list[dict[str, Any]] = []
    for candidate in sorted(state.candidate, key=lambda row: int(row["overall_review_rank"])):
        pick = int(candidate["overall_pick"])
        frozen = frozen_by_pick[pick]
        live = state.live[pick]
        recon = state.reconciliation[pick]
        matrix = matrix_by_id[str(candidate["player_id"])]
        prior = json.loads(str(matrix["prospect_prior_evidence_json"]))
        workout = prior.get("workout_profile") or {}
        frozen_id = recon["frozen_model_player_id"]
        research = state.research.get(frozen_id, {})
        neighborhood = state.neighborhoods.get(frozen_id, {})
        redraft = state.redraft.get(live["player_id"])
        redraft_blocked = state.redraft_blocked.get(live["player_id"])
        is_manual = candidate["player_name"] in MANUAL_NAMES
        evidence_band = (
            f"FROZEN_{str(frozen.get('evidence_confidence') or 'BLOCKED').upper()}"
            if frozen.get("final_review_score")
            else "FROZEN_IDENTITY_BLOCKED"
        )
        rows.append(
            {
                "official_draft_asset_id": recon["official_draft_asset_id"],
                "stable_asset_id": recon["asset_id"],
                "overall_pick": pick,
                "draft_round": candidate["draft_round"],
                "live_player_id": live["player_id"],
                "frozen_model_player_id": frozen_id,
                "player": candidate["player_name"],
                "position": candidate["position"],
                "draft_team": candidate["nfl_team"],
                "current_team": live["current_team"],
                "current_status": live["current_status"],
                "age_at_draft": _fmt(candidate["age_at_draft"]),
                "production_component": _fmt(candidate["production_component"]),
                "production_context": _profile_context(state.profiles[str(candidate["player_id"])], "production"),
                "market_share_component": _fmt(candidate["market_share_component"]),
                "market_share_context": _profile_context(state.profiles[str(candidate["player_id"])], "market"),
                "draft_capital_component": _fmt(candidate["draft_capital_component"]),
                "athletic_component": _fmt(candidate["athletic_component"]),
                "athletic_context": (
                    json.dumps(workout, sort_keys=True, separators=(",", ":"))
                    if workout
                    else "missing_not_zero"
                ),
                "recruiting_component": "",
                "recruiting_context": "governed_source_absent:missing_not_zero",
                "age_component": _fmt(candidate["age_component"]),
                "missing_components": candidate["missing_components"],
                "warning_codes": candidate["warning_codes"],
                "frozen_score": frozen.get("final_review_score", ""),
                "frozen_rank": frozen.get("overall_review_rank", ""),
                "frozen_position_rank": frozen.get("position_rank", ""),
                "frozen_evidence_band": evidence_band,
                "refresh_candidate_score": _fmt(candidate["final_review_score"]),
                "refresh_candidate_rank": candidate["overall_review_rank"],
                "refresh_candidate_position_rank": candidate["position_rank"],
                "refresh_candidate_format_score": _fmt(candidate["sprint14e_format_score"]),
                "draft_range_band": candidate["tier"],
                "manual_review_status": "SEVEN_MANUAL_REVIEW" if is_manual else "FROZEN_ROW_PRESERVED",
                "strict_frozen_replay_status": STRICT_BLOCK if is_manual else "FROZEN_CANONICAL_ROW_PRESERVED",
                "identity_contract_status": (
                    "OWNER_APPROVAL_REQUIRED_FOR_NEW_IDENTITY_BRIDGE" if is_manual else "FROZEN_CONTRACT_UNCHANGED"
                ),
                "research_rank": research.get("research_rank", ""),
                "research_band": research.get("research_tier", ""),
                "veteran_neighborhood_above": neighborhood.get("veterans_above", ""),
                "veteran_neighborhood_below": neighborhood.get("veterans_below", ""),
                "redraft_projection_status": (
                    "ADMITTED_CURRENT_SEASON" if redraft else redraft_blocked.get("projection_status", "MISSING") if redraft_blocked else "MISSING"
                ),
                "redraft_projection_low": redraft.get("projection_low", "") if redraft else "",
                "redraft_projection_high": redraft.get("projection_high", "") if redraft else "",
                "current_role_freshness": "2026-07-30_TEAM_STATUS_ONLY_NO_DEPTH_COMPETITION_OR_INJURY",
                "explanation": _explanation(candidate, frozen),
                "candidate_authority": CANDIDATE_AUTHORITY,
                "allowed_use": "research_review_and_owner_approval_only",
                "blocked_use": "no_runtime_no_canonical_rank_no_draft_recommendation_no_score_overlay",
            }
        )
    return rows


def render_factual_overlay(state: BuildState) -> bytes:
    """Render the seven-row Desktop evidence source with all score/rank fields excluded."""

    rows: list[dict[str, Any]] = []
    for row in _board_rows(state):
        if row["manual_review_status"] != "SEVEN_MANUAL_REVIEW":
            continue
        rows.append(
            {
                "official_draft_asset_id": row["official_draft_asset_id"],
                "stable_asset_id": row["stable_asset_id"],
                "overall_pick": row["overall_pick"],
                "live_player_id": row["live_player_id"],
                "player": row["player"],
                "position": row["position"],
                "age_at_draft": row["age_at_draft"],
                "production_component": row["production_component"],
                "market_share_component": row["market_share_component"],
                "draft_capital_component": row["draft_capital_component"],
                "athletic_component": row["athletic_component"],
                "recruiting_component": row["recruiting_component"],
                "age_component": row["age_component"],
                "missing_components": row["missing_components"],
                "factual_overlay_authority": (
                    "ROOKIE_INTELLIGENCE_V2_REVIEW_ONLY_FACTUAL_COMPONENTS"
                ),
                "allowed_use": "manual_review_owner_context_only",
                "blocked_use": "no_score_no_rank_no_model_no_trade_value",
            }
        )
    if len(rows) != 7:
        raise RuntimeError(f"factual overlay must contain seven manual rows; found {len(rows)}")
    return _csv(rows, FACTUAL_OVERLAY_FIELDS).encode("utf-8")


def _completeness_rows(state: BuildState, board: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for row in sorted(board, key=lambda item: int(item["overall_pick"])):
        manual = row["manual_review_status"] == "SEVEN_MANUAL_REVIEW"
        rows.append(
            {
                "official_draft_asset_id": row["official_draft_asset_id"],
                "stable_asset_id": row["stable_asset_id"],
                "overall_pick": row["overall_pick"],
                "player": row["player"],
                "position": row["position"],
                "draft_authority": "EXACT_OFFICIAL_PICK",
                "live_identity": "EXACT_GOVERNED_IDENTITY",
                "frozen_identity_admission": "BLOCKED" if manual else "ADMITTED",
                "age": "PRESENT",
                "college_production": "PRESENT",
                "market_share": "PRESENT",
                "raw_combine": "PRESENT" if row["athletic_context"] != "missing_not_zero" else "MISSING_NOT_ZERO",
                "formula_athletic": "PRESENT" if row["athletic_component"] != "" else "MISSING_NOT_ZERO",
                "recruiting": "MISSING_NOT_ZERO",
                "frozen_rookie_review": "SCORED" if row["frozen_score"] != "" else "UNSCORED_IDENTITY_BLOCKED",
                "refresh_candidate": "SCORED_REVIEW_ONLY_PENDING_BRIDGE" if manual else "PRESERVED_EXACT",
                "unified_research": "PRESENT_RESEARCH_ONLY" if row["research_rank"] != "" else "MISSING_FOR_MANUAL_ROW",
                "redraft_projection": row["redraft_projection_status"],
                "current_role": row["current_role_freshness"],
                "missing_classification": "SOURCE_ABSENT_NOT_ZERO;IDENTITY_CONTRACT_PENDING" if manual else "SOURCE_ABSENT_NOT_ZERO",
            }
        )
    return rows


def _manual_rows(board: list[dict[str, Any]]) -> list[dict[str, Any]]:
    fields = (
        "official_draft_asset_id", "stable_asset_id", "overall_pick", "player", "position",
        "live_player_id", "draft_team", "current_team", "current_status", "age_at_draft",
        "production_component", "production_context", "market_share_component",
        "market_share_context", "draft_capital_component", "athletic_component",
        "athletic_context", "recruiting_component", "recruiting_context", "missing_components",
        "strict_frozen_replay_status", "candidate_reconstruction_status",
        "identity_bridge", "frozen_score", "frozen_rank", "refresh_candidate_score",
        "refresh_candidate_rank", "refresh_candidate_format_score", "draft_range_band",
        "redraft_projection_status", "current_role_freshness",
        "evidence_finding", "required_owner_action", "blocked_use",
    )
    rows = []
    for row in sorted(
        (item for item in board if item["manual_review_status"] == "SEVEN_MANUAL_REVIEW"),
        key=lambda item: int(item["overall_pick"]),
    ):
        rows.append(
            {
                **row,
                "candidate_reconstruction_status": BRIDGE_PENDING,
                "identity_bridge": "PROPOSED_OFFICIAL_PICK_PLUS_PINNED_LIVE_ID;NOT_IN_FROZEN_20260730_CONTRACT",
                "evidence_finding": "production+market_share+draft_capital+age reconstructed; athletic only when frozen consumer supports it; recruiting absent",
                "required_owner_action": "approve_or_reject_new_identity_contract_then_run_full_governed_rebuild",
            }
        )
    return [{field: row.get(field, "") for field in fields} for row in rows]


def _rank_audit_rows(state: BuildState, board: list[dict[str, Any]]) -> list[dict[str, Any]]:
    frozen = [row for row in state.frozen if row["final_review_score"]]
    ordered_final = sorted(
        frozen, key=lambda row: (float(row["final_review_score"]), row["player_name"]), reverse=True
    )
    final_rank = {int(row["overall_pick"]): index for index, row in enumerate(ordered_final, 1)}
    ordered_format = sorted(
        frozen, key=lambda row: (float(row["sprint14e_format_score"]), row["player_name"]), reverse=True
    )
    format_rank = {int(row["overall_pick"]): index for index, row in enumerate(ordered_format, 1)}
    formula = {
        row["player_id"]: row for row in _rows(state.repo / FORMULA_RECONCILIATION)
    }
    if len(formula) != 73 or any(row["reconciled"] != "True" for row in formula.values()):
        raise RuntimeError("frozen formula reconciliation receipt drift")
    board_by_pick = {int(row["overall_pick"]): row for row in board}
    rows = []
    for row in sorted(frozen, key=lambda item: int(item["overall_review_rank"])):
        pick = int(row["overall_pick"])
        candidate = board_by_pick[pick]
        receipt = formula[row["player_id"]]
        factor = POSITION_FORMAT_FACTORS[row["position"]]
        frozen_rank = int(row["overall_review_rank"])
        if receipt["sprint14e_evidence_state"] == "watchlist_data_incomplete":
            classification = "INTENTIONAL_AUTHORITY_GATE"
        elif final_rank[pick] != frozen_rank and factor != 1.0:
            classification = "POSITION_FORMAT_RULE"
        elif final_rank[pick] != frozen_rank:
            classification = "COMPONENT_WEIGHT_OR_EVIDENCE_GATE"
        else:
            classification = "SCORE_AND_RANK_ALIGNED"
        rows.append(
            {
                "overall_pick": pick,
                "player": row["player_name"],
                "position": row["position"],
                "raw_model_v4_score": row["raw_model_v4_score"],
                "confidence_cap": row["confidence_cap"],
                "final_review_score": row["final_review_score"],
                "component_weight_available": receipt["component_weight_available"],
                "guardrail_states": receipt["guardrail_states"],
                "position_format_factor": factor,
                "expected_uncapped_format_score": receipt["expected_uncapped_format_score"],
                "sprint14e_format_score": row["sprint14e_format_score"],
                "sprint14e_evidence_state": receipt["sprint14e_evidence_state"],
                "final_score_rank": final_rank[pick],
                "recomputed_sprint14e_rank": format_rank[pick],
                "frozen_rank": frozen_rank,
                "refresh_candidate_rank": candidate["refresh_candidate_rank"],
                "candidate_rank_shift": int(candidate["refresh_candidate_rank"]) - frozen_rank,
                "classification": classification,
                "finding": "NO_RANKING_DEFECT; Sprint14E format score, not final analyzer score, is the frozen rank key",
            }
        )
    if any(row["recomputed_sprint14e_rank"] != row["frozen_rank"] for row in rows):
        raise RuntimeError("frozen Sprint14E rank reproduction failed")
    return rows


def _gauntlet_rows() -> list[dict[str, Any]]:
    return [
        {"candidate": "Frozen Champion", "family": "exact Model V4 Rookie Review", "execution": "BLOCKED", "result": "NO_HISTORICAL_SCORE_ROWS", "promotion": "RETAINED_BY_DEFAULT", "reason": "expected 395-row historical Champion matrix absent; compatible copy header-only"},
        {"candidate": "H1", "family": "production+draft capital interaction", "execution": "UNTOUCHED_RESEARCH_FEASIBLE", "result": "NOT_EXECUTED", "promotion": "NO", "reason": "historical admission/coverage/parity absent; labels prohibit model/training use"},
        {"candidate": "H2", "family": "confidence-cap shadow", "execution": "DOCUMENTED_ONLY_UNREPRODUCIBLE", "result": "NO_ROW_LEVEL_MATRIX", "promotion": "NO", "reason": "published aggregate tied current strict rate; row evidence unavailable"},
        {"candidate": "H3", "family": "age/early-declare", "execution": "UNTOUCHED_AGE_ONLY_FEASIBLE", "result": "NOT_EXECUTED", "promotion": "NO", "reason": "age present on joined labels; early-declare absent"},
        {"candidate": "H4", "family": "production/team-share", "execution": "UNTOUCHED_RESEARCH_FEASIBLE", "result": "NOT_EXECUTED", "promotion": "NO", "reason": "no governed historical college feature admission"},
        {"candidate": "H5", "family": "normalized athletic", "execution": "UNTOUCHED_BLOCKED", "result": "NOT_EXECUTABLE", "promotion": "NO", "reason": "no historical/current percentile-normalization parity"},
        {"candidate": "H6", "family": "position-specific calibration/tiering", "execution": "CONTROL_ONLY_REQUIRES_RERUN", "result": "NOT_PROMOTABLE", "promotion": "NO", "reason": "existing draft-capital control split is not outcome-maturity-safe"},
    ]


def _temporal_rows() -> list[dict[str, Any]]:
    counts = {
        ("rookie", "T12"): (818, 41), ("rookie", "T24"): (579, 67), ("rookie", "T36"): (579, 107),
        ("year2", "T12"): (737, 79), ("year2", "T24"): (506, 92), ("year2", "T36"): (506, 120),
        ("first3y", "T12"): (492, 112), ("first3y", "T24"): (349, 131), ("first3y", "T36"): (355, 167),
        ("first5y", "T12"): (291, 116), ("first5y", "T24"): (210, 117), ("first5y", "T36"): (224, 157),
    }
    rules = {
        "rookie": ("train_label_year<=test_class-1", "2016-2024", "SECONDARY"),
        "year2": ("train_label_year<=test_class-2", "2017-2023", "SECONDARY"),
        "first3y": ("train_label_year<=test_class-3", "2018-2022", "PRIMARY"),
        "first5y": ("train_label_year<=test_class-5", "2018-2020", "DESCRIPTIVE_ONLY"),
    }
    rows = []
    for (window, target), (eligible, hits) in counts.items():
        rule, tests, use = rules[window]
        rows.append({
            "window": window, "target": target, "eligible_rows": eligible,
            "hits": hits, "censored_rows_policy": "EXCLUDE_NOT_MISS",
            "required_rolling_origin_rule": rule, "suggested_test_classes": tests,
            "promotion_use": use, "execution_status": "NOT_EXECUTED_IN_V2",
        })
    return rows


def _position_rows() -> list[dict[str, Any]]:
    counts = {
        "QB": (161, 123, 10),
        "RB": (298, 246, 12),
        "WR": (448, 383, 36),
        "TE": (198, 167, 22),
    }
    return [
        {
            "position": position,
            "historical_frame_rows": historical,
            "labeled_rows": labeled,
            "current_class_rows": current,
            "historical_authority": "REVIEW_ONLY_MODEL_AND_TRAINING_PROHIBITED",
            "champion_row_level_status": "ABSENT",
            "leakage_safe_position_evaluation": "NOT_EXECUTED",
            "spearman": "NOT_COMPUTABLE",
            "pairwise_accuracy": "NOT_COMPUTABLE",
            "top_n_utility": "NOT_COMPUTABLE",
            "finding": "NO_POSITION_CHALLENGER_OR_CALIBRATION_CLAIM",
        }
        for position, (historical, labeled, current) in counts.items()
    ]


def _confidence_rows() -> list[dict[str, Any]]:
    return [
        {"gate": "current_2026_confidence_contract", "rows": 80, "result": "60_AT_0.88;20_AT_0.84", "authority": "REFRESH_CANDIDATE_ONLY", "finding": "unchanged formula and governed missingness; not historical validation"},
        {"gate": "recruiting_missingness", "rows": 80, "result": "80_MISSING_NOT_ZERO", "authority": "EXACT_SOURCE_GAP", "finding": "no numeric substitution"},
        {"gate": "historical_confidence_cap_shadow", "rows": 128, "result": "broad=.567;strict=.317;draft_misses=14", "authority": "PUBLISHED_AGGREGATE_UNREPRODUCIBLE", "finding": "documented shadow tied current; not promotable"},
        {"gate": "historical_champion_confidence_join", "rows": 0, "result": "BLOCKED", "authority": "MISSING_ROW_LEVEL_CHAMPION", "finding": "cannot measure separation or calibration"},
    ]


def _draft_range_label(value: str) -> str:
    return {
        "first_round_board_context_review": "First-round draft range",
        "second_round_board_context_review": "Second-round draft range",
        "depth_board_context_review": "Depth-board range",
        "watchlist_context_review": "Watchlist range",
        "watchlist_or_data_incomplete_context_review": (
            "Watchlist or incomplete-evidence range"
        ),
        "blocked_unranked": "Manual review",
    }.get(value, "Not enough information")


def _evidence_band_label(value: str) -> str:
    return {
        "FROZEN_USABLE_WITH_CONFIDENCE_CAP": "Usable with confidence cap",
        "FROZEN_CAPPED_REVIEW_REQUIRED": "Capped; owner review required",
        "FROZEN_IDENTITY_BLOCKED": "Frozen identity blocked",
    }.get(value, "Not enough information")


def _selected_explanations(board: list[dict[str, Any]]) -> str:
    by_name = {row["player"]: row for row in board}
    selected = ["Jeremiyah Love", "Carnell Tate", "KC Concepcion", "De'Zhaun Stribling"]
    for position in ("QB", "RB", "WR", "TE"):
        top = next(row for row in board if row["position"] == position)
        selected.append(top["player"])
    selected.extend([board[len(board) // 2]["player"], board[-1]["player"]])
    lines = ["# Current class explanations", "", "These are evidence receipts, not final draft recommendations. Candidate-only ranks and scores are disconnected from runtime.", ""]
    for name in dict.fromkeys(selected):
        row = by_name[name]
        lines.extend([
            f"## {name} — {row['position']}", "",
            row["explanation"], "",
            f"Draft capital component: {row['draft_capital_component']}; production: {row['production_component']}; market share: {row['market_share_component']}; athletic: {row['athletic_component'] or 'missing-not-zero'}; age: {row['age_component']}. Draft Range Band: **{_draft_range_label(row['draft_range_band'])}**. Frozen Evidence Band: **{_evidence_band_label(row['frozen_evidence_band'])}**.", "",
        ])
    stribling = by_name["De'Zhaun Stribling"]
    bell = by_name["Chris Bell"]
    lines.extend([
        "## Stribling versus Chris Bell", "",
        f"The separate refresh candidate places Bell #{bell['refresh_candidate_rank']} ({bell['refresh_candidate_score']}) and Stribling #{stribling['refresh_candidate_rank']} ({stribling['refresh_candidate_score']}). Bell leads the admitted production ({bell['production_component']} vs {stribling['production_component']}), market-share ({bell['market_share_component']} vs {stribling['market_share_component']}), and age ({bell['age_component']} vs {stribling['age_component']}) components; Stribling leads draft capital ({stribling['draft_capital_component']} vs {bell['draft_capital_component']}). Both lack a formula athletic component and recruiting prior. This is an explainable candidate result, not a canonical rank or proof that either ordering is correct.", "",
        "## External plausibility checks", "",
        "Accessed 2026-08-14 and used only as display sanity, never as tuning or rank truth: [PFF](https://www.pff.com/news/2026-fantasy-football-dynasty-rookie-cheat-sheet-printable-superflex-rankings-for-drafts) calls Love the clear dynasty 1.01; [FantasyPros](https://www.fantasypros.com/nfl/rankings/dynasty-rookies-overall.php) lists Chris Bell #13 and Stribling #18; [NBC Sports](https://www.nbcsports.com/fantasy/football/news/2026-nfl-dynasty-rookie-rankings-dezhaun-stribling-and-kc-concepcion-rise-up-the-board) lists Stribling #12 and Bell #21; [Dynasty Dealer](https://www.dynastydealer.com/rookie-rankings/2026) consensus lists Mendoza #2 and Sadiq #8. Love's frozen #1 is broadly plausible. Tate and KC are explainable NWR disagreements requiring owner scrutiny. Public Stribling/Bell disagreement is a sanity flag, not authority to force a rank.", "",
    ])
    return "\n".join(lines)


def render_packet(state: BuildState) -> dict[str, bytes]:
    board = _board_rows(state)
    completeness = _completeness_rows(state, board)
    manual = _manual_rows(board)
    rank_audit = _rank_audit_rows(state, board)
    shifts = sum(int(row["candidate_rank_shift"]) != 0 for row in rank_audit)
    formula_athletic = sum(row["athletic_component"] != "" for row in board)
    redraft_present = sum(row["redraft_projection_status"] == "ADMITTED_CURRENT_SEASON" for row in board)
    files: dict[str, str] = {}
    files["CURRENT_2026_BOARD.csv"] = _csv(board, BOARD_FIELDS)
    files["CURRENT_CLASS_COMPLETENESS.csv"] = _csv(completeness, completeness[0].keys())
    files["SEVEN_MANUAL_REVIEW_AUDIT.csv"] = _csv(manual, manual[0].keys())
    files["RANK_VS_SCORE_AUDIT.csv"] = _csv(rank_audit, rank_audit[0].keys())
    files["MODEL_GAUNTLET.csv"] = _csv(_gauntlet_rows(), _gauntlet_rows()[0].keys())
    files["TEMPORAL_VALIDATION.csv"] = _csv(_temporal_rows(), _temporal_rows()[0].keys())
    files["POSITION_RESULTS.csv"] = _csv(_position_rows(), _position_rows()[0].keys())
    files["CONFIDENCE_GATE_RESULTS.csv"] = _csv(_confidence_rows(), _confidence_rows()[0].keys())
    files["EXECUTIVE_VERDICT.md"] = f"""# NWR Rookie Intelligence V2 — executive verdict

`{VERDICT}`

The official 2026 QB/RB/WR/TE class reconciles to **80 = 73 frozen scored + 7 frozen identity-blocked + 0 unresolved draft assets**. All 73 frozen formula outputs recompute exactly across {len(PARITY_FIELDS)} governed scored/component fields before presentation formatting. The seven now have lawful draft-slot, live-ID, age, college, draft-capital, and combine evidence sufficient to calculate a separate review-only candidate, but they are **not exact frozen replays**: the 2026-07-30 service requires draft-source GSIS equality and the draft rows remain blank. Owner approval of a new identity bridge is required.

The 80-row refresh candidate changes {shifts} of 73 retained ranks when the seven are inserted. That rank is not canonical and is disconnected from runtime. No validated rookie tier is claimed; `Draft Range Band` is descriptive and `Frozen Evidence Band` reports the frozen evidence state.

Historical Champion validation remains blocked because the row-level Champion feature/score matrix is absent and labels are review-only (`model_use_allowed=false`, `training_allowed=false`). No challenger was promoted. Champion production authority is unchanged.
"""
    files["ROOKIE_TIER_ANALYSIS.md"] = """# Rookie tier analysis

No validated rookie tiers are promoted. The frozen `draft_board_band` is rank/evidence rule output, not an outcome-validated tier. V2 exposes it only as **Draft Range Band** and translates frozen source confidence into **Frozen Evidence Band**.

Historical tier separation cannot be tested without row-level frozen Champion scores and as-of-date feature parity. Candidate rank buckets would be circular and are therefore prohibited. A future tier proposal must use leakage-safe rolling origin, censored-window exclusion, position-aware outcomes, paired class bootstrap, and beat both the frozen Champion and draft-capital control before owner review.
"""
    files["HISTORICAL_ROOKIE_FRAME.md"] = """# Historical rookie frame

- Governed redraft outcome frame: 1,105 unique drafted QB/RB/WR/TE rows, classes 2012–2025, QB 161 / RB 298 / WR 448 / TE 198; SHA-256 `a02d77684bd0313ff59ed74665e5f87f76a5a1714799ed13aaaad4f1dd37a791`.
- Per-class counts for 2012–2025: 77, 79, 75, 78, 77, 83, 83, 80, 77, 75, 79, 80, 77, 85.
- 896 rows have a rookie stat row; 209 are genuine no-row zeros under that redraft contract; age is missing on 3 rows.
- Review-only dynasty labels: 919 rows, classes 2012–2024, QB 123 / RB 246 / WR 383 / TE 167; SHA-256 `6db401e1cbaf9a611d53061046006d40600fae335dac512e23539391f2aabeac`.
- All 919 labels join 1:1 to the outcome frame with age and draft capital complete. Every label is `review_only=true`, `model_use_allowed=false`, `training_allowed=false`.
- The expected 395-row 2021–2025 frozen Champion historical matrix is absent. The compatible-pack copy is header-only, SHA-256 `d7486d344d29ff5ae6b038a381f41ab034eef4932a2653a444858b66cd9424b2`.

Therefore exact Champion historical score, rank, confidence, tier separation, and promotion comparisons are `NOT_ENOUGH_INFORMATION`. Existing model_rd_v1 results are retrospective class holdouts, not outcome-maturity-safe rolling origin. Five-year results are descriptive only.
"""
    files["CURRENT_CLASS_EXPLANATIONS.md"] = _selected_explanations(board)
    files["ROOKIE_DATA_GAPS.md"] = f"""# Rookie data gaps

- Frozen identity contract: seven rows still fail the source-draft GSIS equality gate. Their live IDs are exact in a later governed overlay, but that bridge is new authority.
- Recruiting: 80/80 missing-not-zero.
- Athletic formula support: {formula_athletic}/80; raw combine evidence exists more broadly but percentile normalization is not governed for most positions.
- Unified dynasty research: 73/80 only; the seven candidate rows have no frozen research rank or veteran neighborhood.
- Redraft projection: {redraft_present}/80. Max Bredeson and Riley Nowakowski are blocked by draft-position/current-position conflicts.
- Current role: 2026-07-30 team/status only; no depth chart, competition, injury, or camp evidence. Treat as stale for role claims.
- Historical Champion: row-level feature/score matrix absent; exact accuracy and tiers cannot be validated.
"""
    files["DESKTOP_INTEGRATION.md"] = """# Desktop integration

This packet does not integrate candidate scores or ranks. The local Desktop candidate packages a separate seven-row `MANUAL_REVIEW_FACTUAL_COMPONENT_OVERLAY.csv` containing no score or rank columns. The full `CURRENT_2026_BOARD.csv` remains research-only and is not packaged.

The seven stable asset IDs surface identity, draft capital, age, production/market-share receipts, governed athletic context where supported, governed missingness, current team/status, and manual-review state. They remain `MANUAL REVIEW — NOT YET SCORED` in canonical product semantics until the owner approves the new identity contract and a separately reviewed rebuild is promoted. The deterministic builder writes the 19-artifact research packet plus the separate factual-only Desktop overlay.
"""
    files["DRAFT_READINESS.md"] = """# Draft readiness

All 80 official draft assets are searchable/selectable/draftable by eligibility authority. Seventy-three retain frozen review-only scores. The seven recovered assets remain manual-review rows for canonical ranking; their candidate-only calculations are evidence that a governed rebuild is feasible, not draft recommendations.

Readiness is **green for an owner-approval refresh candidate, not for canonical promotion**: completeness is recovered and the candidate is deterministic, while identity-contract approval, fresh role context, and historical accuracy remain open. Stribling's omission mechanism is closed at the asset/eligibility layer; score/rank promotion is deliberately not automatic.
"""
    files["AUTHORITY_PRESERVATION.md"] = """# Authority preservation

1. Frozen Rookie Review remains canonical and unchanged (SHA-256 `06853164a41cd9715accfc3c4f3e54d0cc915be6c55ebab040de6fc0abd96c2f`).
2. The 73 admitted rows preserve every formula/component/confidence/format value exactly.
3. The seven retain `STILL_BLOCKED_REQUIRED_EVIDENCE` under the exact 2026-07-30 input contract because source draft GSIS is blank.
4. The proposed bridge uses official unique draft pick + pinned later governed live player ID, then exact PFR-to-players/combine and unique draft-slot-to-CFBD joins. This is a new identity contract requiring owner approval.
5. Candidate scores/ranks are labeled review-only, never canonical, never runtime-integrated, and never silently substituted for frozen blanks.
6. Missing evidence remains blank/null, never zero. Formula versions and weights are unchanged. Finished V1, Outcome V3, active model packs, and rank authorities are untouched; the only product artifact emitted is the bounded factual-only overlay.
"""
    files["VALIDATION_RESULTS.md"] = f"""# Validation results

- PASS — official class: 80 rows; QB 10 / RB 12 / WR 36 / TE 22.
- PASS — frozen reconciliation: 73 scored / 7 identity-blocked / 0 unresolved draft assets.
- PASS — all {len(PARITY_FIELDS)} preserved formula/output fields match for all 73 retained rows.
- PASS — seven candidate rows have exact live IDs, ages, production, market share, and draft capital; all have candidate-only scores/ranks.
- PASS — recruiting is blank for 80/80; no missing-to-zero substitution.
- PASS — frozen ranks reproduce the exact Sprint14E `(league_format_adjusted_score, prospect_name)` descending contract.
- PASS — {shifts}/73 retained ranks shift only in the separate 80-row candidate.
- PASS — no canonical/model/rank authority files are output; the packet contains exactly 19 artifacts and the separate product overlay contains no score/rank fields.
- BLOCKED — exact frozen replay for seven pending owner approval of new identity contract.
- BLOCKED — historical Champion accuracy, tier separation, and challenger promotion due missing row-level Champion matrix and non-training labels.

Overall: `{VERDICT}`.
"""
    files["NEXT_ACTION.md"] = """# Next action

Owner decision required: approve or reject the proposed `official unique draft pick + pinned governed live ID` identity contract for the seven manual-review rookies. If approved, implement it in a new versioned source adapter, regenerate a full governed 80-row review build, rerun mutations/parity checks, and review rank shifts before any promotion.

Separately, admit an as-of-date historical Champion feature/score matrix and obtain training/model-use authority for labels before running H1–H6 under maturity-safe rolling origin. Refresh current role evidence before using depth, competition, injury, or camp claims. Until those gates pass, retain the frozen Champion and keep candidate score/rank columns disconnected.
"""
    encoded = {name: text.encode("utf-8") for name, text in files.items()}
    if set(encoded) != set(REQUIRED_FILES) - {"MANIFEST.json"}:
        raise RuntimeError("renderer does not produce the required 18 pre-manifest files")
    manifest = {
        "packet": "NWR_ROOKIE_INTELLIGENCE_V2_20260814",
        "as_of": "2026-08-14",
        "verdict": VERDICT,
        "authority": "RESEARCH_ONLY_OWNER_APPROVAL_PACKET",
        "class_counts": {"total": 80, "QB": 10, "RB": 12, "WR": 36, "TE": 22, "frozen_scored": 73, "frozen_blocked": 7, "unresolved_draft_assets": 0},
        "candidate_contract": "PROPOSED_OFFICIAL_PICK_PLUS_PINNED_LIVE_ID_BRIDGE",
        "candidate_scores_ranks_runtime_integrated": False,
        "source_hashes": {str(path).replace("\\", "/"): expected for path, expected in SOURCE_HASHES.items()},
        "external_source_hashes": {
            "nflverse_draft_raw": "7b41d3437d8172ed619f4fb8de2536eaefb8aa09e901ae53f45e9605509abf0f",
            "nflverse_players_raw": "b10b2d1759c77c02c8c87ab23924a060a59c05e1d89dfc5f9f7ddaba1a2b175c",
            "nflverse_combine_raw": "1b6c48a0b56e515b043dd678ea38a2e6ae83cb9de488e6a0a89f8b2f980bf2cf",
            "cfbd_aggregate": "370ce01696c305f64792e45e1f8671cfb788b8419b257040206a6f14e5c2770a",
            "historical_redraft_frame": "a02d77684bd0313ff59ed74665e5f87f76a5a1714799ed13aaaad4f1dd37a791",
            "historical_review_only_labels": "6db401e1cbaf9a611d53061046006d40600fae335dac512e23539391f2aabeac",
            "finished_v1_protected": "263cc8aa050c4670bf5ed22701d7b04801d143480c5630b98e00dd08d2968ce4",
            "outcome_v3_protected": "e3b44047d36bd62d9573295db64d96f214922a20f0083cf49105f104970b3d20",
        },
        "files": {name: {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)} for name, data in sorted(encoded.items())},
    }
    encoded["MANIFEST.json"] = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
    return encoded


def write_packet(repo: Path) -> dict[str, bytes]:
    state = load_state(repo)
    rendered = render_packet(state)
    root = repo / PACKET
    root.mkdir(parents=True, exist_ok=True)
    extras = {path.name for path in root.iterdir() if path.is_file()} - set(REQUIRED_FILES)
    if extras:
        raise RuntimeError(f"unexpected packet artifacts: {sorted(extras)}")
    for name in REQUIRED_FILES:
        (root / name).write_bytes(rendered[name])
    factual_path = repo / FACTUAL_OVERLAY
    factual_path.parent.mkdir(parents=True, exist_ok=True)
    factual_path.write_bytes(render_factual_overlay(state))
    return rendered


def check_packet(repo: Path) -> None:
    state = load_state(repo)
    rendered = render_packet(state)
    root = repo / PACKET
    actual = {path.name for path in root.iterdir() if path.is_file()} if root.is_dir() else set()
    if actual != set(REQUIRED_FILES):
        raise RuntimeError(f"packet file set mismatch: {sorted(actual)}")
    for name, expected in rendered.items():
        if (root / name).read_bytes() != expected:
            raise RuntimeError(f"determinism check failed: {name}")
    factual_path = repo / FACTUAL_OVERLAY
    if not factual_path.is_file() or factual_path.read_bytes() != render_factual_overlay(state):
        raise RuntimeError("determinism check failed: factual-only Desktop overlay")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    repo = args.repo_root.resolve()
    if args.check:
        check_packet(repo)
        print(
            f"PASS: {len(REQUIRED_FILES)} deterministic packet artifacts + "
            "1 factual-only Desktop overlay"
        )
    else:
        rendered = write_packet(repo)
        print(
            f"WROTE: {len(rendered)} deterministic packet artifacts to {repo / PACKET} "
            f"and factual-only overlay to {repo / FACTUAL_OVERLAY}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
