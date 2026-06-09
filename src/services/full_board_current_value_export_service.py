from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from src.config.constants import DEFAULT_DATA_PACK
from src.services.model_v4_confidence_missingness_service import (
    build_confidence_missingness_layer,
    write_confidence_missingness_outputs,
)
from src.services.model_v4_current_value_checkpoint_service import (
    CurrentValueCheckpointPaths,
    build_current_value_checkpoint,
    write_current_value_checkpoint_outputs,
)
from src.services.model_v4_evidence_matrix_service import (
    MatrixPaths,
    build_evidence_matrices,
    write_evidence_matrix_outputs,
)
from src.services.model_v4_lifecycle_archetype_service import (
    build_lifecycle_archetype_layer,
    write_lifecycle_archetype_outputs,
)
from src.services.model_v4_qb_te_current_value_service import (
    build_qb_te_current_value,
    write_qb_te_current_value_outputs,
)
from src.services.model_v4_rb_wr_current_value_service import (
    build_rb_wr_current_value,
    write_rb_wr_current_value_outputs,
)
from src.services.model_v4_replacement_vorp_core_service import (
    ReplacementVorpPaths,
    build_replacement_vorp_core,
    write_replacement_vorp_core_outputs,
)

FULL_BOARD_CURRENT_VALUE_VERSION = "model_v4_full_board_current_value_export_0.1.0"

DEFAULT_OUTPUT_ROOT = Path("local_exports/model_v4/current_value/latest")
DEFAULT_SUPPORT_ROOT = DEFAULT_OUTPUT_ROOT / "full_board_active_support"
DEFAULT_FULL_BOARD_CURRENT_VALUE_ROWS = (
    DEFAULT_OUTPUT_ROOT / "current_player_value_full_board_review_rows.csv"
)

SUPPORTED_RANKINGS_POSITIONS = {"QB", "RB", "WR", "TE"}

ACTIVE_BOARD_TRUTH_SET_HEADER = (
    "player_name",
    "position",
    "nfl_team",
    "truth_set_group",
    "reason_included",
    "lifecycle_expected",
    "roster_context",
    "source_priority",
)


@dataclass(frozen=True)
class FullBoardCurrentValueExportResult:
    truth_set_path: Path
    evidence_paths: MatrixPaths
    vorp_paths: ReplacementVorpPaths
    checkpoint_paths: CurrentValueCheckpointPaths
    summary: dict[str, object]


def write_full_board_current_value_export(
    *,
    data_pack_path: str | Path = DEFAULT_DATA_PACK,
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
    support_root: str | Path = DEFAULT_SUPPORT_ROOT,
) -> FullBoardCurrentValueExportResult:
    """Run the admitted Model v4 current-value chain over active QB/RB/WR/TE rows.

    The active data pack supplies only the identity universe, roster context, and team
    mapping. Private scores still come from the existing Model v4 evidence/VORP/current-
    value formula chain. Market, league, and legacy active-pack score fields are never
    read into private value.
    """

    output = Path(output_root)
    support = Path(support_root)
    output.mkdir(parents=True, exist_ok=True)
    support.mkdir(parents=True, exist_ok=True)

    truth_set_path = support / "active_board_qb_rb_wr_te_truth_set.csv"
    truth_rows = _active_board_truth_rows(Path(data_pack_path))
    _write_csv(truth_set_path, ACTIVE_BOARD_TRUTH_SET_HEADER, truth_rows)

    evidence_root = support / "evidence_matrices"
    evidence_result = build_evidence_matrices(truth_set_path=truth_set_path)
    evidence_paths = write_evidence_matrix_outputs(
        output_root=evidence_root,
        doc_path=support / "evidence_matrices.md",
        result=evidence_result,
    )

    vorp_root = support / "replacement_vorp"
    vorp_result = build_replacement_vorp_core(nfl_matrix_path=evidence_paths.nfl)
    vorp_paths = write_replacement_vorp_core_outputs(
        output_root=vorp_root,
        doc_path=support / "replacement_vorp.md",
        result=vorp_result,
    )

    current_root = support / "current_value_layers"
    rb_wr_result = build_rb_wr_current_value(
        nfl_matrix_path=evidence_paths.nfl,
        vorp_rows_path=vorp_paths.player_rows,
    )
    write_rb_wr_current_value_outputs(
        output_root=current_root,
        doc_path=support / "rb_wr_current_value.md",
        result=rb_wr_result,
    )
    qb_te_result = build_qb_te_current_value(
        nfl_matrix_path=evidence_paths.nfl,
        vorp_rows_path=vorp_paths.player_rows,
        rb_wr_reference_rows=rb_wr_result.value_rows,
    )
    write_qb_te_current_value_outputs(
        output_root=current_root,
        doc_path=support / "qb_te_current_value.md",
        result=qb_te_result,
    )
    lifecycle_result = build_lifecycle_archetype_layer(nfl_matrix_path=evidence_paths.nfl)
    write_lifecycle_archetype_outputs(
        output_root=current_root,
        doc_path=support / "lifecycle_archetype.md",
        result=lifecycle_result,
    )
    confidence_result = build_confidence_missingness_layer(nfl_matrix_path=evidence_paths.nfl)
    write_confidence_missingness_outputs(
        output_root=current_root,
        doc_path=support / "confidence_missingness.md",
        result=confidence_result,
    )

    checkpoint_result = build_current_value_checkpoint(input_root=current_root)
    checkpoint_paths = write_current_value_checkpoint_outputs(
        output_root=current_root,
        doc_path=support / "current_value_checkpoint.md",
        result=checkpoint_result,
    )
    _copy_csv(
        checkpoint_paths.review_rows,
        DEFAULT_FULL_BOARD_CURRENT_VALUE_ROWS
        if output == DEFAULT_OUTPUT_ROOT
        else output / DEFAULT_FULL_BOARD_CURRENT_VALUE_ROWS.name,
    )

    summary = {
        "full_board_current_value_version": FULL_BOARD_CURRENT_VALUE_VERSION,
        "active_truth_set_rows": len(truth_rows),
        "evidence_nfl_player_rows": evidence_result.summary["nfl_player_rows"],
        "vorp_player_rows": vorp_result.summary["player_rows"],
        "rb_wr_value_rows": rb_wr_result.summary["player_rows"],
        "qb_te_value_rows": qb_te_result.summary["player_rows"],
        "lifecycle_rows": lifecycle_result.summary["player_rows"],
        "confidence_nfl_player_rows": confidence_result.summary["nfl_player_rows"],
        "checkpoint_review_rows": checkpoint_result.summary["review_rows"],
        "checkpoint_scored_rows": sum(
            1
            for row in checkpoint_result.review_rows
            if str(row.get("checkpoint_review_score") or "").strip()
        ),
        "market_rows_used": 0,
        "league_rank_rows_used": 0,
        "legacy_active_pack_scores_used": 0,
        "active_rankings_changed": False,
        "readiness_unlocked": False,
    }
    _write_csv(
        output / "current_player_value_full_board_summary.csv",
        ("metric", "value"),
        ({"metric": key, "value": value} for key, value in summary.items()),
    )
    return FullBoardCurrentValueExportResult(
        truth_set_path=truth_set_path,
        evidence_paths=evidence_paths,
        vorp_paths=vorp_paths,
        checkpoint_paths=checkpoint_paths,
        summary=summary,
    )


def _active_board_truth_rows(data_pack_path: Path) -> tuple[dict[str, object], ...]:
    model_rows = _read_rows(data_pack_path / "model_outputs.csv")
    official_by_player_id = _by_player_id(_read_rows(data_pack_path / "fact_official_rankings.csv"))
    roster_by_player_id = _by_player_id(_read_rows(data_pack_path / "fact_rosters.csv"))
    truth_rows: list[dict[str, object]] = []
    seen: set[tuple[str, str]] = set()
    for row in model_rows:
        position = str(row.get("position") or "").upper()
        if position not in SUPPORTED_RANKINGS_POSITIONS:
            continue
        player_id = str(row.get("player_id") or "")
        official = official_by_player_id.get(player_id, {})
        roster = roster_by_player_id.get(player_id, {})
        player = str(row.get("player_name") or official.get("player_name") or "")
        key = (player.lower(), position)
        if not player or key in seen:
            continue
        seen.add(key)
        truth_rows.append(
            {
                "player_name": player,
                "position": position,
                "nfl_team": official.get("nfl_team") or roster.get("nfl_team") or "",
                "truth_set_group": "active_board_qb_rb_wr_te",
                "reason_included": "active_board_identity_universe_for_full_board_coverage",
                "lifecycle_expected": "",
                "roster_context": "active_board_player",
                "source_priority": "full_board_coverage_review",
            }
        )
    return tuple(truth_rows)


def _read_rows(path: Path) -> tuple[dict[str, str], ...]:
    if not path.exists():
        return ()
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return tuple(csv.DictReader(handle))


def _by_player_id(rows: tuple[dict[str, str], ...]) -> dict[str, dict[str, str]]:
    return {str(row.get("player_id") or ""): row for row in rows if row.get("player_id")}


def _write_csv(path: Path, header: tuple[str, ...], rows: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=header, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _copy_csv(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
