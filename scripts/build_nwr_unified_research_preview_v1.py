# ruff: noqa: E501
"""Materialize the frozen unified-dynasty research preview without model refitting."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "docs/hq/model/nwr_unified_research_preview_v1_20260808"
INPUTS = PACKET / "frozen_inputs"
FOUNDATION_COMMIT = "61b8ffd091de46b7d8cc46d322b8c19e70450298"
FRESH_EVIDENCE_COMMIT = "4d137c63b264db1e07f4a46812ea7779cb2d18ae"
FOUNDATION_PREFIX = "docs/hq/model/nwr_unified_dynasty_training_panel_and_current_frame_v1_20260808"
FRESH_MANIFEST_PATH = "docs/hq/model/nwr_unified_dynasty_fresh_rookie_calibration_validation_v1_20260808/MANIFEST.json"
SOURCE_FILES = {
    "eligible_predictions.csv": (
        FOUNDATION_COMMIT,
        f"{FOUNDATION_PREFIX}/CURRENT_ELIGIBLE_PREDICTIONS_RESEARCH_ONLY.csv",
        "0b45e61b3b565d1ffae0ed81e930b1788edfb47cc7cda0bc95fe4f01706c3420",
    ),
    "current_veteran_frame.csv": (
        FOUNDATION_COMMIT,
        f"{FOUNDATION_PREFIX}/CURRENT_VETERAN_FEATURE_FRAME.csv",
        "cbff65ec9e8397709724b3fbfea474c72c5fd5fe0835d4a533c334ebbd0a0d9e",
    ),
    "current_rookie_frame.csv": (
        FOUNDATION_COMMIT,
        f"{FOUNDATION_PREFIX}/CURRENT_ROOKIE_FEATURE_FRAME.csv",
        "6a0f6dc58416b2a87ac4454ab8b8e6ddfc8b070ff534f756e990e7633c136afd",
    ),
    "fresh_cohort_manifest.json": (
        FRESH_EVIDENCE_COMMIT,
        FRESH_MANIFEST_PATH,
        "3b6b290dcc89b405d2188beb2e7854a8a0b4793f6425dec3a1ca2f2dc8ee66c2",
    ),
}
BOARD_COLUMNS = [
    "research_rank",
    "research_asset_id",
    "source_asset_id",
    "governed_player_id",
    "player",
    "position",
    "asset_type",
    "research_tier",
    "outlook_3y",
    "outlook_5y",
    "ceiling_signal",
    "downside_signal",
    "confidence",
    "uncertainty_low",
    "uncertainty_high",
    "evidence_coverage",
    "existing_finished_v1_rank",
    "existing_rookie_review_rank",
    "status",
    "blocking_reason",
    "authority",
]


def sha256(path: Path) -> str:
    """Hash canonical text bytes so Windows checkout newlines do not create drift."""
    digest = hashlib.sha256()
    digest.update(path.read_bytes().replace(b"\r\n", b"\n"))
    return digest.hexdigest()


def materialize_frozen_inputs() -> None:
    INPUTS.mkdir(parents=True, exist_ok=True)
    for filename, (commit, source_path, expected) in SOURCE_FILES.items():
        destination = INPUTS / filename
        if not destination.exists():
            data = subprocess.check_output(["git", "show", f"{commit}:{source_path}"], cwd=ROOT)
            destination.write_bytes(data)
        actual = sha256(destination)
        if actual != expected:
            raise AssertionError(
                f"frozen input hash mismatch for {filename}: {actual} != {expected}"
            )


def _slug(value: str) -> str:
    return "-".join(value.lower().replace("'", "").split())


def _float(value: Any) -> float | None:
    parsed = pd.to_numeric(value, errors="coerce")
    return None if pd.isna(parsed) else float(parsed)


def _rank_text(value: Any) -> str:
    parsed = _float(value)
    return "" if parsed is None else str(int(parsed))


def _tier(value: float, quantiles: list[float]) -> str:
    if value >= quantiles[3]:
        return "RESEARCH_TIER_1"
    if value >= quantiles[2]:
        return "RESEARCH_TIER_2"
    if value >= quantiles[1]:
        return "RESEARCH_TIER_3"
    if value >= quantiles[0]:
        return "RESEARCH_TIER_4"
    return "RESEARCH_TIER_5"


def build_board() -> pd.DataFrame:
    eligible = pd.read_csv(INPUTS / "eligible_predictions.csv", low_memory=False)
    eligible = eligible.sort_values(
        ["predicted_utility", "governed_player_id"], ascending=[False, True], kind="stable"
    ).reset_index(drop=True)
    eligible["research_rank"] = range(1, len(eligible) + 1)
    quantiles = eligible["predicted_utility"].quantile([0.2, 0.4, 0.6, 0.8]).tolist()
    rows: list[dict[str, Any]] = []
    for row in eligible.to_dict("records"):
        rookie = int(row["rookie_entry"]) == 1
        source_asset_id = (
            f"rookie:{row['governed_player_id']}"
            if rookie
            else f"current:{_rank_text(row.get('finished_v1_player_id'))}"
        )
        asset_type = "ROOKIE" if rookie else "VETERAN"
        rows.append(
            {
                "research_rank": int(row["research_rank"]),
                "research_asset_id": f"unified-research:{row['governed_player_id']}",
                "source_asset_id": source_asset_id,
                "governed_player_id": row["governed_player_id"],
                "player": row["player_name"],
                "position": row["position"],
                "asset_type": asset_type,
                "research_tier": _tier(float(row["predicted_utility"]), quantiles),
                "outlook_3y": row["predicted_3y_outlook"],
                "outlook_5y": row["predicted_5y_outlook"],
                "ceiling_signal": row["ceiling_probability"],
                "downside_signal": row["downside_probability"],
                "confidence": row["confidence"],
                "uncertainty_low": row["utility_p10"],
                "uncertainty_high": row["utility_p90"],
                "evidence_coverage": row["evidence_coverage"],
                "existing_finished_v1_rank": _rank_text(row.get("finished_v1_rank")),
                "existing_rookie_review_rank": _rank_text(row.get("rookie_review_rank")),
                "status": "RESEARCH_ONLY_NOT_ADMITTED",
                "blocking_reason": "",
                "authority": "RESEARCH_ONLY_NOT_PRODUCTION",
            }
        )

    veteran = pd.read_csv(INPUTS / "current_veteran_frame.csv", low_memory=False)
    rookie = pd.read_csv(INPUTS / "current_rookie_frame.csv", low_memory=False)
    blocked_veterans = veteran.loc[
        ~veteran["prediction_eligibility"].astype(str).str.startswith("ELIGIBLE")
    ]
    blocked_rookies = rookie.loc[
        rookie["prediction_eligibility"].astype(str).str.startswith("BLOCKED")
    ]
    for row in blocked_veterans.to_dict("records"):
        source_id = f"current:{_rank_text(row.get('finished_v1_player_id'))}"
        rows.append(
            {
                "research_rank": "",
                "research_asset_id": f"unified-research-blocked:{row['governed_player_id']}",
                "source_asset_id": source_id,
                "governed_player_id": row["governed_player_id"],
                "player": row["player_name"],
                "position": row["position"],
                "asset_type": "VETERAN",
                "research_tier": "",
                "outlook_3y": "",
                "outlook_5y": "",
                "ceiling_signal": "",
                "downside_signal": "",
                "confidence": "",
                "uncertainty_low": "",
                "uncertainty_high": "",
                "evidence_coverage": row.get("evidence_coverage", ""),
                "existing_finished_v1_rank": _rank_text(row.get("finished_v1_rank")),
                "existing_rookie_review_rank": "",
                "status": "INSUFFICIENT / OUTSIDE MODEL SUPPORT",
                "blocking_reason": row["prediction_eligibility"],
                "authority": "RESEARCH_ONLY_NOT_PRODUCTION",
            }
        )
    for row in blocked_rookies.to_dict("records"):
        source_id = f"blocked-rookie:{_slug(str(row['player_name']))}"
        governed_id = str(row.get("governed_player_id") or "").strip()
        rows.append(
            {
                "research_rank": "",
                "research_asset_id": f"unified-research-blocked:{governed_id or _slug(str(row['player_name']))}",
                "source_asset_id": source_id,
                "governed_player_id": governed_id,
                "player": row["player_name"],
                "position": row["position"],
                "asset_type": "ROOKIE",
                "research_tier": "",
                "outlook_3y": "",
                "outlook_5y": "",
                "ceiling_signal": "",
                "downside_signal": "",
                "confidence": "",
                "uncertainty_low": "",
                "uncertainty_high": "",
                "evidence_coverage": row.get("evidence_coverage", ""),
                "existing_finished_v1_rank": "",
                "existing_rookie_review_rank": _rank_text(row.get("rookie_review_rank")),
                "status": "INSUFFICIENT / OUTSIDE MODEL SUPPORT",
                "blocking_reason": row["prediction_eligibility"],
                "authority": "RESEARCH_ONLY_NOT_PRODUCTION",
            }
        )
    board = pd.DataFrame(rows, columns=BOARD_COLUMNS)
    if len(board) != 320:
        raise AssertionError(f"preview must contain 320 visible assets, found {len(board)}")
    ranked = board.loc[board["status"].eq("RESEARCH_ONLY_NOT_ADMITTED")]
    if len(ranked) != 304 or list(pd.to_numeric(ranked["research_rank"])) != list(range(1, 305)):
        raise AssertionError("preview ranked rows must be exactly 1..304")
    if int(ranked["asset_type"].eq("VETERAN").sum()) != 231:
        raise AssertionError("preview must contain 231 ranked veterans")
    if int(ranked["asset_type"].eq("ROOKIE").sum()) != 73:
        raise AssertionError("preview must contain 73 ranked rookies")
    blocked = board.loc[~board["status"].eq("RESEARCH_ONLY_NOT_ADMITTED")]
    if len(blocked) != 16 or blocked["research_rank"].astype(str).str.strip().any():
        raise AssertionError("all 16 blocked assets must remain unranked")
    return board


def build_neighborhoods(board: pd.DataFrame) -> pd.DataFrame:
    ranked = board.loc[board["status"].eq("RESEARCH_ONLY_NOT_ADMITTED")].copy()
    ranked["research_rank"] = pd.to_numeric(ranked["research_rank"]).astype(int)
    veterans = ranked.loc[ranked["asset_type"].eq("VETERAN")].copy()
    rows: list[dict[str, Any]] = []
    for rookie in ranked.loc[ranked["asset_type"].eq("ROOKIE")].to_dict("records"):
        rank = int(rookie["research_rank"])
        above = veterans.loc[veterans["research_rank"].lt(rank)].tail(3)
        below = veterans.loc[veterans["research_rank"].gt(rank)].head(3)
        def format_rows(frame: pd.DataFrame) -> str:
            return " | ".join(
                f"{int(row['research_rank'])}. {row['player']} ({row['position']})"
                for row in frame.to_dict("records")
            )
        rows.append(
            {
                "rookie_governed_id": rookie["governed_player_id"],
                "rookie": rookie["player"],
                "position": rookie["position"],
                "research_rank": rank,
                "research_tier": rookie["research_tier"],
                "veterans_above": format_rows(above),
                "veterans_below": format_rows(below),
                "confidence": rookie["confidence"],
                "evidence_coverage": rookie["evidence_coverage"],
                "reason_evidence_summary": (
                    f"Frozen shared-target signals: 3Y={float(rookie['outlook_3y']):.3f}; "
                    f"5Y={float(rookie['outlook_5y']):.3f}; "
                    f"ceiling={float(rookie['ceiling_signal']):.3f}; "
                    f"downside={float(rookie['downside_signal']):.3f}. "
                    "Research context only; no production rank or recommendation."
                ),
                "status": "RESEARCH_ONLY_NOT_ADMITTED",
                "authority": "RESEARCH_ONLY_NOT_PRODUCTION",
            }
        )
    result = pd.DataFrame(rows).sort_values("research_rank").reset_index(drop=True)
    if len(result) != 73:
        raise AssertionError("every eligible rookie requires one research neighborhood")
    return result


def output_hashes() -> dict[str, str]:
    return {
        path.name: sha256(path)
        for path in sorted(PACKET.iterdir())
        if path.is_file() and path.name != "MANIFEST.json"
    }


def build() -> dict[str, Any]:
    materialize_frozen_inputs()
    fresh = json.loads((INPUTS / "fresh_cohort_manifest.json").read_text(encoding="utf-8"))
    if fresh["verdict"] != "BLOCKED_NWR_UNIFIED_DYNASTY_NO_UNTOUCHED_MATURE_ROOKIE_COHORT":
        raise AssertionError("fresh-cohort controlling verdict drift")
    board = build_board()
    neighborhoods = build_neighborhoods(board)
    PACKET.mkdir(parents=True, exist_ok=True)
    board.to_csv(
        PACKET / "UNIFIED_DYNASTY_RESEARCH_PREVIEW.csv",
        index=False,
        lineterminator="\n",
        float_format="%.6f",
    )
    neighborhoods.to_csv(
        PACKET / "ROOKIE_VETERAN_NEIGHBORHOODS.csv",
        index=False,
        lineterminator="\n",
        float_format="%.6f",
    )
    board.loc[pd.to_numeric(board["research_rank"], errors="coerce").le(25)].to_csv(
        PACKET / "TOP_25_RESEARCH_PREVIEW.csv",
        index=False,
        lineterminator="\n",
        float_format="%.6f",
    )
    receipt = {
        "authority": "RESEARCH_ONLY_NOT_PRODUCTION",
        "foundation_commit": FOUNDATION_COMMIT,
        "fresh_evidence_commit": FRESH_EVIDENCE_COMMIT,
        "controlling_verdict": fresh["verdict"],
        "selected_research_learner": "M5_BOUNDED_QUADRATIC",
        "target_architecture": "MULTI_HORIZON_VECTOR_5Y",
        "calibration_state": "G3_FAILED_NO_FRESH_UNTOUCHED_MATURE_5Y_COHORT",
        "model_refits": 0,
        "coefficient_changes": 0,
        "manual_reorders": 0,
        "source_files": {
            filename: {"commit": commit, "path": path, "sha256": expected}
            for filename, (commit, path, expected) in SOURCE_FILES.items()
        },
    }
    (PACKET / "FROZEN_RESEARCH_RECEIPT.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    (PACKET / "README.md").write_text(
        """# Unified Dynasty Preview V1

Authority: **RESEARCH_ONLY_NOT_PRODUCTION**.

This additive preview reproduces the frozen current research ordering from commit
61b8ffd091de46b7d8cc46d322b8c19e70450298. It does not refit the model,
change coefficients, reorder players manually, replace Finished V1, or admit a
production common scale. Rookie calibration remains unvalidated because no fresh
untouched mature five-year cohort exists.
""",
        encoding="utf-8",
        newline="\n",
    )
    ranked = board.loc[board["status"].eq("RESEARCH_ONLY_NOT_ADMITTED")]
    blocked = board.loc[~board["status"].eq("RESEARCH_ONLY_NOT_ADMITTED")]
    manifest = {
        "schema_version": 1,
        "authority": "RESEARCH_ONLY_NOT_PRODUCTION",
        "controlling_verdict": fresh["verdict"],
        "foundation_commit": FOUNDATION_COMMIT,
        "fresh_evidence_commit": FRESH_EVIDENCE_COMMIT,
        "preview_rows": len(board),
        "ranked_rows": len(ranked),
        "eligible_veterans": int(ranked["asset_type"].eq("VETERAN").sum()),
        "eligible_rookies": int(ranked["asset_type"].eq("ROOKIE").sum()),
        "blocked_assets": len(blocked),
        "blocked_kickers": int(blocked["position"].eq("K").sum()),
        "blocked_outside_support_veterans": int(
            blocked["blocking_reason"]
            .eq("BLOCKED_OUTSIDE_HISTORICAL_VETERAN_SUPPORT_NO_PRIOR_SEASON")
            .sum()
        ),
        "blocked_rookies": int(blocked["asset_type"].eq("ROOKIE").sum()),
        "rookie_neighborhoods": len(neighborhoods),
        "production_common_rank_admitted": False,
        "model_refits": 0,
        "coefficient_changes": 0,
        "manual_reorders": 0,
        "provider_calls": 0,
        "dynastyprocess_files_opened": 0,
        "source_hashes": {name: expected for name, (_, _, expected) in SOURCE_FILES.items()},
        "output_hashes": output_hashes(),
    }
    (PACKET / "MANIFEST.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify-existing", action="store_true")
    args = parser.parse_args()
    before = output_hashes() if args.verify_existing and PACKET.exists() else None
    manifest = build()
    if args.verify_existing:
        after = output_hashes()
        if before != after:
            changed = sorted(set(before or {}) | set(after))
            drift = [name for name in changed if (before or {}).get(name) != after.get(name)]
            raise AssertionError(f"deterministic preview drift: {drift}")
        print("deterministic research preview: PASS")
    print(
        json.dumps(
            {
                key: manifest[key]
                for key in (
                    "preview_rows",
                    "ranked_rows",
                    "eligible_veterans",
                    "eligible_rookies",
                    "blocked_assets",
                )
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
