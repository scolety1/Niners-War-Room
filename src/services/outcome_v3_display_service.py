"""Read-only product adapter for the governed Outcome Columns V3 release."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from src.services.outcome_v3_calibration_service import (
    HORIZONS,
    NOT_APPLICABLE,
    NOT_ENOUGH_INFORMATION,
    POSITION_THRESHOLDS,
    RANKINGS_HORIZONS,
    RELEASE_IDENTIFIER,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
PACKET_ROOT = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "master"
    / "nwr_outcome_columns_v3_rc1_v1_20260729"
)
INTEGRATION_PACK_PATH = PACKET_ROOT / "OUTCOME_V3_INTEGRATION_PACK.csv"
MANIFEST_PATH = PACKET_ROOT / "MANIFEST.json"

REQUIRED_COLUMNS = {
    "player_id",
    "player_name",
    "position",
    "finished_v1_rank",
    "field_id",
    "threshold",
    "horizon",
    "horizon_label",
    "probability",
    "probability_display",
    "calibration_status",
    "effective_calibrator",
    "historical_labeled_rows",
    "historical_positive_events",
    "historical_negative_events",
    "confidence",
    "evidence_state",
    "missing_reason",
    "projection_adjustment",
    "reason_code",
    "applicable",
    "release_identifier",
    "display_only",
    "rank_use_allowed",
}


@dataclass(frozen=True)
class OutcomeV3DisplayBundle:
    frame: pd.DataFrame
    loaded: bool
    row_count: int
    player_count: int
    source_path: Path | None
    source_hash: str
    release_identifier: str
    errors: tuple[str, ...]


@dataclass(frozen=True)
class OutcomeCoverageAudit:
    numeric: int
    applicable: int
    percent: float
    classifications: tuple[tuple[str, int], ...]


def load_outcome_v3_display(
    *,
    integration_path: str | Path = INTEGRATION_PACK_PATH,
    manifest_path: str | Path = MANIFEST_PATH,
) -> OutcomeV3DisplayBundle:
    integration = Path(integration_path)
    manifest = Path(manifest_path)
    errors: list[str] = []
    if not integration.exists():
        errors.append(f"Outcome V3 integration pack is missing: {integration}")
    if not manifest.exists():
        errors.append(f"Outcome V3 manifest is missing: {manifest}")
    if errors:
        return _empty_bundle(errors)

    try:
        metadata = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return _empty_bundle([f"Outcome V3 manifest is invalid: {exc}"])
    if metadata.get("release_identifier") != RELEASE_IDENTIFIER:
        errors.append("Outcome V3 manifest release identifier mismatch")
    manifest_entries = {
        str(entry.get("path", "")): entry
        for entry in metadata.get("artifacts", [])
        if isinstance(entry, dict)
    }
    try:
        relative_path = integration.relative_to(manifest.parent).as_posix()
    except ValueError:
        relative_path = integration.name
    entry = manifest_entries.get(relative_path)
    if entry is None:
        errors.append("Outcome V3 integration pack is absent from the manifest")
    actual_hash = _sha256(integration)
    if entry is not None and str(entry.get("sha256", "")).lower() != actual_hash:
        errors.append("Outcome V3 integration pack hash mismatch")

    try:
        frame = pd.read_csv(integration, dtype=str, keep_default_na=False)
    except (OSError, pd.errors.ParserError) as exc:
        return _empty_bundle([*errors, f"Outcome V3 integration pack is invalid: {exc}"])
    missing = sorted(REQUIRED_COLUMNS - set(frame.columns))
    if missing:
        errors.append(f"Outcome V3 integration pack is missing columns: {missing}")
    if not errors:
        errors.extend(_validate_frame(frame))
    if errors:
        return OutcomeV3DisplayBundle(
            frame=pd.DataFrame(),
            loaded=False,
            row_count=0,
            player_count=0,
            source_path=integration,
            source_hash=actual_hash,
            release_identifier=RELEASE_IDENTIFIER,
            errors=tuple(errors),
        )
    return OutcomeV3DisplayBundle(
        frame=frame,
        loaded=True,
        row_count=len(frame),
        player_count=int(frame["player_id"].nunique()),
        source_path=integration,
        source_hash=actual_hash,
        release_identifier=RELEASE_IDENTIFIER,
        errors=(),
    )


def rankings_outcome_v3_rows(
    board: pd.DataFrame,
    outcome_frame: pd.DataFrame,
    *,
    position: str,
    threshold: int,
) -> pd.DataFrame:
    """Return five long-form horizon rows per selected exact-ID board player."""

    normalized_position = str(position).upper()
    if normalized_position not in POSITION_THRESHOLDS:
        raise ValueError(f"unsupported Outcome V3 position: {position}")
    if threshold not in POSITION_THRESHOLDS[normalized_position]:
        raise ValueError(
            f"unsupported Outcome V3 threshold: {normalized_position} T{threshold}"
        )
    required = {"player_id", "player_name", "position"}
    if missing := sorted(required - set(board.columns)):
        raise AssertionError(f"rankings Outcome V3 board missing columns: {missing}")

    filtered = board.loc[
        board["position"].astype(str).str.upper().eq(normalized_position)
    ].copy()
    lookup = _outcome_lookup(outcome_frame)
    rows: list[dict[str, str]] = []
    for player in filtered.to_dict("records"):
        player_id = _text(player.get("player_id"))
        for horizon in RANKINGS_HORIZONS:
            source = lookup.get((player_id, normalized_position, threshold, horizon))
            rows.append(
                _display_row(
                    player_id=player_id,
                    player_name=_text(player.get("player_name")),
                    position=normalized_position,
                    finished_v1_rank=_text(player.get("nwr_rank")),
                    threshold=threshold,
                    horizon=horizon,
                    source=source,
                )
            )
    return pd.DataFrame(rows)


def player_compare_outcome_v3_rows(
    compare_frame: pd.DataFrame,
    outcome_frame: pd.DataFrame,
) -> pd.DataFrame:
    """Return all applicable thresholds and six horizons without a name fallback."""

    required = {"player", "position"}
    if missing := sorted(required - set(compare_frame.columns)):
        raise AssertionError(f"Player Compare Outcome V3 input missing columns: {missing}")
    lookup = _outcome_lookup(outcome_frame)
    rows: list[dict[str, str]] = []
    for player in compare_frame.to_dict("records"):
        player_id = _text(player.get("player_id"))
        player_name = _text(player.get("player"))
        position = _text(player.get("position")).upper()
        thresholds = POSITION_THRESHOLDS.get(position, ())
        if not thresholds:
            rows.append(
                {
                    "Finished V1 Rank": _text(player.get("final_board_rank")),
                    "Player": player_name,
                    "Pos": position,
                    "Threshold": NOT_APPLICABLE,
                    "Horizon": NOT_APPLICABLE,
                    "Probability": NOT_APPLICABLE,
                    "Calibration status": NOT_APPLICABLE,
                    "Evidence": "wrong_position_not_applicable",
                    "Historical sample": NOT_APPLICABLE,
                    "Confidence": NOT_APPLICABLE,
                    "Missing-state explanation": NOT_APPLICABLE,
                    "Release": RELEASE_IDENTIFIER,
                }
            )
            continue
        for threshold in thresholds:
            for horizon in HORIZONS:
                source = lookup.get((player_id, position, threshold, horizon))
                rows.append(
                    _display_row(
                        player_id=player_id,
                        player_name=player_name,
                        position=position,
                        finished_v1_rank=_text(player.get("final_board_rank")),
                        threshold=threshold,
                        horizon=horizon,
                        source=source,
                    )
                )
    return pd.DataFrame(rows)


def outcome_v3_player_matrix(
    board: pd.DataFrame,
    outcome_frame: pd.DataFrame,
    *,
    position: str,
) -> tuple[pd.DataFrame, OutcomeCoverageAudit, pd.DataFrame]:
    """Pivot governed V3 values to one player per row with quiet missing markers."""

    normalized_position = str(position).upper()
    if normalized_position not in POSITION_THRESHOLDS:
        raise ValueError(f"unsupported Outcome V3 position: {position}")
    required = {"player_id", "player_name", "position"}
    if missing := sorted(required - set(board.columns)):
        raise AssertionError(f"Outcome V3 matrix board missing columns: {missing}")
    players = board.loc[
        board["position"].astype(str).str.upper().eq(normalized_position)
    ].copy()
    lookup = _outcome_lookup(outcome_frame)
    matrix_rows: list[dict[str, str]] = []
    detail_rows: list[dict[str, str]] = []
    numeric = 0
    applicable = 0
    classifications: dict[str, int] = {}
    for player in players.to_dict("records"):
        player_id = _text(player.get("player_id"))
        player_name = _text(player.get("player_name"))
        output: dict[str, str] = {
            "NWR Rank": _text(player.get("nwr_rank")) or NOT_ENOUGH_INFORMATION,
            "Player": player_name,
            "Pos": normalized_position,
        }
        for horizon in HORIZONS:
            for threshold in POSITION_THRESHOLDS[normalized_position]:
                source = lookup.get(
                    (player_id, normalized_position, int(threshold), horizon)
                )
                label = f"{_compact_horizon_label(horizon)} T{threshold}"
                applicable += 1
                probability = _text((source or {}).get("probability_display"))
                evidence = _text((source or {}).get("evidence_state"))
                if probability and probability not in {
                    NOT_ENOUGH_INFORMATION,
                    NOT_APPLICABLE,
                }:
                    output[label] = probability
                    numeric += 1
                    classification = "numeric evidence"
                else:
                    output[label] = "—"
                    classification = _missing_classification(source, player_id)
                    classifications[classification] = (
                        classifications.get(classification, 0) + 1
                    )
                detail_rows.append(
                    {
                        "Player": player_name,
                        "Pos": normalized_position,
                        "Outcome": label,
                        "Value": output[label],
                        "Classification": classification,
                        "Why unavailable": (
                            "Available"
                            if classification == "numeric evidence"
                            else _text((source or {}).get("missing_reason"))
                            or _text((source or {}).get("reason_code"))
                            or "No governed Outcome V3 row for the exact player ID"
                        ),
                        "Evidence": evidence or NOT_ENOUGH_INFORMATION,
                    }
                )
        matrix_rows.append(output)
    audit = OutcomeCoverageAudit(
        numeric=numeric,
        applicable=applicable,
        percent=round((numeric / applicable * 100) if applicable else 0.0, 1),
        classifications=tuple(sorted(classifications.items())),
    )
    return pd.DataFrame(matrix_rows), audit, pd.DataFrame(detail_rows)


def _compact_horizon_label(horizon: str) -> str:
    return {
        "THIS_YEAR": "2026",
        "NEXT_YEAR": "2027",
        "T_PLUS_2": "2028",
        "WITHIN_3Y": "Within 3Y",
        "WITHIN_5Y": "Within 5Y",
        "TWO_OF_NEXT_3Y": "2 of 3Y",
    }.get(horizon, horizon.replace("_", " ").title())


def _missing_classification(source: dict[str, Any] | None, player_id: str) -> str:
    if source is None or not player_id:
        return "loader/join issue"
    evidence = _text(source.get("evidence_state")).casefold()
    reasons = " ".join(
        (_text(source.get("missing_reason")), _text(source.get("reason_code")))
    ).casefold()
    if "stale" in reasons or "legacy" in reasons:
        return "stale/legacy artifact issue"
    if "blocked" in evidence or "blocked" in reasons:
        return "intentionally blocked"
    if "unsupported" in evidence or "unsupported" in reasons:
        return "model unsupported"
    return "true evidence gap"


def _outcome_lookup(
    frame: pd.DataFrame,
) -> dict[tuple[str, str, int, str], dict[str, Any]]:
    if frame.empty:
        return {}
    required = {"player_id", "field_id", "position", "threshold", "horizon"}
    if missing := sorted(required - set(frame.columns)):
        raise AssertionError(f"Outcome V3 display frame missing columns: {missing}")
    lookup: dict[tuple[str, str, int, str], dict[str, Any]] = {}
    for row in frame.to_dict("records"):
        key = (
            _text(row.get("player_id")),
            _text(row.get("field_id")).split("_", maxsplit=1)[0].upper(),
            int(row["threshold"]),
            _text(row.get("horizon")).upper(),
        )
        if key in lookup:
            raise AssertionError(f"duplicate Outcome V3 display key: {key}")
        lookup[key] = row
    return lookup


def _display_row(
    *,
    player_id: str,
    player_name: str,
    position: str,
    finished_v1_rank: str,
    threshold: int,
    horizon: str,
    source: dict[str, Any] | None,
) -> dict[str, str]:
    if source is None:
        probability = NOT_ENOUGH_INFORMATION
        calibration = NOT_ENOUGH_INFORMATION
        evidence = "insufficient_current_evidence"
        sample = NOT_ENOUGH_INFORMATION
        confidence = NOT_ENOUGH_INFORMATION
        reason = (
            "missing exact player_id Outcome evidence"
            if not player_id
            else "no governed Outcome V3 row for exact player_id"
        )
        horizon_label = _fallback_horizon_label(horizon)
    else:
        probability = _text(source.get("probability_display")) or NOT_ENOUGH_INFORMATION
        calibration = _text(source.get("calibration_status")) or NOT_ENOUGH_INFORMATION
        evidence = _text(source.get("evidence_state")) or NOT_ENOUGH_INFORMATION
        labeled = _text(source.get("historical_labeled_rows"))
        positives = _text(source.get("historical_positive_events"))
        negatives = _text(source.get("historical_negative_events"))
        sample = (
            f"{labeled} labeled ({positives} positive / {negatives} negative)"
            if labeled
            else NOT_ENOUGH_INFORMATION
        )
        confidence = _text(source.get("confidence")) or NOT_ENOUGH_INFORMATION
        reason = _text(source.get("missing_reason")) or _text(source.get("reason_code"))
        horizon_label = _text(source.get("horizon_label")) or _fallback_horizon_label(
            horizon
        )
    return {
        "Finished V1 Rank": finished_v1_rank or NOT_ENOUGH_INFORMATION,
        "Player": player_name or NOT_ENOUGH_INFORMATION,
        "Pos": position,
        "Threshold": f"{position} T{threshold}",
        "Horizon": horizon_label,
        "Probability": probability,
        "Calibration status": calibration,
        "Evidence": evidence,
        "Historical sample": sample,
        "Confidence": confidence,
        "Missing-state explanation": reason or "Complete admitted evidence",
        "Release": RELEASE_IDENTIFIER,
    }


def _fallback_horizon_label(horizon: str) -> str:
    return {
        "THIS_YEAR": "2026",
        "NEXT_YEAR": "2027",
        "T_PLUS_2": "2028",
        "WITHIN_3Y": "Within 3 Years",
        "WITHIN_5Y": "Within 5 Years",
        "TWO_OF_NEXT_3Y": "Two Qualifying Seasons Within 3 Years",
    }.get(horizon, NOT_ENOUGH_INFORMATION)


def _validate_frame(frame: pd.DataFrame) -> list[str]:
    errors: list[str] = []
    if len(frame) != 240 * 72:
        errors.append(f"Outcome V3 integration row count mismatch: {len(frame)}")
    if frame["player_id"].nunique() != 240:
        errors.append("Outcome V3 integration player count mismatch")
    if frame["field_id"].nunique() != 72:
        errors.append("Outcome V3 governed field count mismatch")
    if not frame["release_identifier"].eq(RELEASE_IDENTIFIER).all():
        errors.append("Outcome V3 row release identifier mismatch")
    if not frame["display_only"].str.lower().eq("true").all():
        errors.append("Outcome V3 contains a non-display-only row")
    if not frame["rank_use_allowed"].str.lower().eq("false").all():
        errors.append("Outcome V3 contains a rank-use row")
    numeric = pd.to_numeric(frame["probability"], errors="coerce")
    supplied = frame["probability"].str.strip().ne("")
    if numeric.loc[supplied].isna().any() or not numeric.loc[supplied].between(0, 1).all():
        errors.append("Outcome V3 contains an invalid numeric probability")
    blocked = frame["evidence_state"].isin(
        {"insufficient_current_evidence", "blocked_or_unsupported"}
    )
    if frame.loc[blocked, "probability"].str.strip().ne("").any():
        errors.append("Outcome V3 blocked or insufficient row is numeric")
    wrong = frame["evidence_state"].eq("wrong_position_not_applicable")
    if not frame.loc[wrong, "probability_display"].eq(NOT_APPLICABLE).all():
        errors.append("Outcome V3 wrong-position state is not N/A")
    return errors


def _empty_bundle(errors: list[str]) -> OutcomeV3DisplayBundle:
    return OutcomeV3DisplayBundle(
        frame=pd.DataFrame(),
        loaded=False,
        row_count=0,
        player_count=0,
        source_path=None,
        source_hash="",
        release_identifier=RELEASE_IDENTIFIER,
        errors=tuple(errors),
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _text(value: object) -> str:
    text = str(value if value is not None else "").strip()
    return "" if text.lower() in {"nan", "none", "null", "<na>"} else text
