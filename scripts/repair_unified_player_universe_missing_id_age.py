from __future__ import annotations

# ruff: noqa: E402
import sys
from datetime import date
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

OUTPUT_DIR = REPO_ROOT / "docs" / "hq" / "model" / "unified_player_universe_v0"
CONSOLIDATED_REVIEW_PATH = OUTPUT_DIR / "unified_player_universe_v1_consolidated_review.csv"
REMAINING_BLOCKERS_PATH = OUTPUT_DIR / "unified_player_universe_v1_remaining_blockers.csv"
REPAIR_PATH = OUTPUT_DIR / "unified_player_universe_v1_missing_id_age_repair.csv"
INSPECTION_PATH = OUTPUT_DIR / "unified_player_universe_v1_missing_id_age_blocker_inspection.csv"
SOURCE_SUMMARY_PATH = OUTPUT_DIR / "unified_player_universe_v1_source_summary.csv"
VALIDATION_REPORT_PATH = OUTPUT_DIR / "unified_player_universe_v1_validation_report.csv"

IDENTITY_AUDIT_PATH = (
    REPO_ROOT / "docs" / "hq" / "data_sources" / "identity" / "player_id_coverage_audit_v1.csv"
)
ROOKIE_AGE_PATH = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "parallel_lanes"
    / "age_source_audit_20260622"
    / "rookie_verified_age_display_20260622.csv"
)
DP_MARKET_PATH = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "parallel_lanes"
    / "dynastyprocess_market_baseline_20260622"
    / "dp_market_baseline_context.csv"
)
ROSTER_DISPLAY_CONTEXT_PATH = Path(
    r"C:\NWR_SHARED_DATA\lane_exchange\stats_context\player_roster_display_context"
    r"\20260621_011500_timing_metadata_v1\player_roster_display_context.csv"
)

NOT_ENOUGH_INFORMATION = "Not enough information"
REPAIR_COLUMNS = [
    "player_name",
    "position",
    "source_layer",
    "player_type",
    "blocker_type",
    "original_player_id",
    "repaired_player_id",
    "original_age",
    "repaired_age",
    "age_source",
    "repair_status",
    "repair_source",
    "confidence",
    "notes",
]
INSPECTION_COLUMNS = [
    "player_name",
    "position",
    "source_layer",
    "player_type",
    "current_player_id",
    "current_age",
    "blocker_type",
    "current_review_status",
    "candidate_repair_source",
    "repair_possible",
    "reason",
]
BLOCKER_COLUMNS = [
    "blocker_id",
    "blocker_type",
    "player_name",
    "position",
    "source_layer",
    "detail",
    "prevents_app_wiring",
    "recommended_action",
    "notes",
]


def main() -> None:
    consolidated = pd.read_csv(CONSOLIDATED_REVIEW_PATH, keep_default_na=False, dtype=str)
    starting_blockers = pd.read_csv(REMAINING_BLOCKERS_PATH, keep_default_na=False, dtype=str)
    identity = _read_optional_csv(IDENTITY_AUDIT_PATH)
    rookie_age = _read_optional_csv(ROOKIE_AGE_PATH)
    dp_market = _read_optional_csv(DP_MARKET_PATH)
    roster_context = _read_optional_csv(ROSTER_DISPLAY_CONTEXT_PATH)

    target_blockers = starting_blockers.loc[
        starting_blockers["blocker_type"].isin(["MISSING_PLAYER_ID", "MISSING_AGE"])
    ].copy()
    repair_rows: list[dict[str, str]] = []
    inspection_rows: list[dict[str, str]] = []

    for _, blocker in target_blockers.iterrows():
        row_index = _match_consolidated_row(consolidated, blocker)
        row = consolidated.loc[row_index] if row_index is not None else pd.Series(dtype=object)
        inspection, repair = _inspect_and_repair(
            row,
            blocker,
            identity,
            rookie_age,
            dp_market,
            roster_context,
        )
        inspection_rows.append(inspection)
        repair_rows.append(repair)
        if row_index is not None and repair["repair_status"] == "REPAIRED":
            _apply_repair(consolidated, row_index, repair)
        elif row_index is not None and repair["repair_status"] == "CONFLICT_REVIEW_NEEDED":
            _apply_conflict(consolidated, row_index, repair)

    repair_frame = pd.DataFrame(repair_rows, columns=REPAIR_COLUMNS)
    inspection_frame = pd.DataFrame(inspection_rows, columns=INSPECTION_COLUMNS)
    blockers = _build_remaining_blockers(consolidated)
    source_summary = _update_source_summary(consolidated, blockers)
    validation_report = _update_validation_report(consolidated, blockers, repair_frame)

    consolidated.to_csv(CONSOLIDATED_REVIEW_PATH, index=False)
    blockers.to_csv(REMAINING_BLOCKERS_PATH, index=False)
    repair_frame.to_csv(REPAIR_PATH, index=False)
    inspection_frame.to_csv(INSPECTION_PATH, index=False)
    source_summary.to_csv(SOURCE_SUMMARY_PATH, index=False)
    validation_report.to_csv(VALIDATION_REPORT_PATH, index=False)

    print(f"starting_missing_player_id={int(starting_blockers['blocker_type'].eq('MISSING_PLAYER_ID').sum())}")
    print(f"ending_missing_player_id={int(blockers['blocker_type'].eq('MISSING_PLAYER_ID').sum())}")
    print(f"starting_missing_age={int(starting_blockers['blocker_type'].eq('MISSING_AGE').sum())}")
    print(f"ending_missing_age={int(blockers['blocker_type'].eq('MISSING_AGE').sum())}")
    print(f"repairs={int(repair_frame['repair_status'].eq('REPAIRED').sum())}")
    print(f"conflicts={int(repair_frame['repair_status'].eq('CONFLICT_REVIEW_NEEDED').sum())}")
    print(f"remaining_blockers={len(blockers)}")


def _inspect_and_repair(
    row: pd.Series,
    blocker: pd.Series,
    identity: pd.DataFrame,
    rookie_age: pd.DataFrame,
    dp_market: pd.DataFrame,
    roster_context: pd.DataFrame,
) -> tuple[dict[str, str], dict[str, str]]:
    player_name = _text(blocker.get("player_name"))
    position = _text(blocker.get("position"))
    source_layer = _text(blocker.get("source_layer"))
    blocker_type = _text(blocker.get("blocker_type"))
    current_player_id = _text(row.get("player_id"))
    current_age = _text(row.get("age")) or NOT_ENOUGH_INFORMATION
    player_type = _text(row.get("player_type"))
    review_status = _text(row.get("review_status"))

    if blocker_type == "MISSING_PLAYER_ID":
        repaired_id, repair_source = _player_id_repair_candidate(
            player_name,
            position,
            identity,
        )
        repair_possible = "yes" if repaired_id else "no"
        reason = (
            "Approved high-confidence exact identity match found."
            if repaired_id
            else "No approved high-confidence exact player_id source found."
        )
        repair_status = "REPAIRED" if repaired_id else "NOT_ENOUGH_INFORMATION"
        repair = _repair_row(
            blocker,
            row,
            repaired_player_id=repaired_id,
            repaired_age="",
            age_source="",
            repair_status=repair_status,
            repair_source=repair_source,
            confidence="HIGH" if repaired_id else "LOW",
            notes=reason,
        )
    elif current_age != NOT_ENOUGH_INFORMATION:
        repair_possible = "yes"
        reason = "Stale blocker removed; consolidated canonical row already has age."
        repair = _repair_row(
            blocker,
            row,
            repaired_player_id=current_player_id,
            repaired_age=current_age,
            age_source=_text(row.get("age_source")),
            repair_status="REPAIRED",
            repair_source="Existing consolidated canonical row",
            confidence="HIGH",
            notes=reason,
        )
    else:
        candidates = _age_candidates(row, rookie_age, dp_market, roster_context)
        distinct_ages = sorted({candidate["age"] for candidate in candidates})
        if len(distinct_ages) == 1:
            candidate_sources = "; ".join(
                dict.fromkeys(candidate["source"] for candidate in candidates)
            )
            repair_possible = "yes"
            reason = "Approved display-age source matched exactly."
            repair = _repair_row(
                blocker,
                row,
                repaired_player_id=current_player_id,
                repaired_age=distinct_ages[0],
                age_source=candidate_sources,
                repair_status="REPAIRED",
                repair_source=candidate_sources,
                confidence="HIGH",
                notes=reason,
            )
        elif len(distinct_ages) > 1:
            candidate_sources = "; ".join(
                f"{candidate['source']}={candidate['age']}" for candidate in candidates
            )
            repair_possible = "no"
            reason = f"Age conflict across approved display sources: {candidate_sources}."
            repair = _repair_row(
                blocker,
                row,
                repaired_player_id=current_player_id,
                repaired_age="",
                age_source="",
                repair_status="CONFLICT_REVIEW_NEEDED",
                repair_source=candidate_sources,
                confidence="REVIEW",
                notes=reason,
            )
        else:
            repair_possible = "no"
            reason = "No approved local age source found; keep Not enough information."
            repair = _repair_row(
                blocker,
                row,
                repaired_player_id=current_player_id,
                repaired_age="",
                age_source="",
                repair_status="NOT_ENOUGH_INFORMATION",
                repair_source="",
                confidence="LOW",
                notes=reason,
            )

    inspection = {
        "player_name": player_name,
        "position": position,
        "source_layer": source_layer,
        "player_type": player_type,
        "current_player_id": current_player_id,
        "current_age": current_age,
        "blocker_type": blocker_type,
        "current_review_status": review_status,
        "candidate_repair_source": repair["repair_source"],
        "repair_possible": repair_possible,
        "reason": reason,
    }
    return inspection, repair


def _player_id_repair_candidate(
    player_name: str,
    position: str,
    identity: pd.DataFrame,
) -> tuple[str, str]:
    if identity.empty:
        return "", ""
    frame = identity.loc[
        identity["player_name"].map(_normalize).eq(_normalize(player_name))
        & identity["position"].astype(str).str.upper().eq(position.upper())
        & identity["match_confidence"].astype(str).str.upper().eq("HIGH")
        & identity["needs_manual_review"].astype(str).str.lower().eq("no")
        & identity["sleeper_id"].astype(str).str.strip().ne("")
    ]
    if frame.empty:
        return "", ""
    return _clean_id(frame.iloc[0]["sleeper_id"]), _rel(IDENTITY_AUDIT_PATH)


def _age_candidates(
    row: pd.Series,
    rookie_age: pd.DataFrame,
    dp_market: pd.DataFrame,
    roster_context: pd.DataFrame,
) -> list[dict[str, str]]:
    candidates: list[dict[str, str]] = []
    player_name = _text(row.get("player_name"))
    position = _text(row.get("position"))
    player_id = _clean_id(row.get("player_id"))

    if not rookie_age.empty:
        rookie_matches = rookie_age.loc[
            rookie_age["player"].map(_normalize).eq(_normalize(player_name))
            & rookie_age["position"].astype(str).str.upper().eq(position.upper())
            & rookie_age["allowed_use"].astype(str).eq("display_age_only_not_model_or_rank_input")
            & ~rookie_age["verification_status"].astype(str).str.contains("conflict", case=False)
        ]
        for _, match in rookie_matches.iterrows():
            age = _age_text(match.get("age"))
            if age:
                candidates.append(
                    {
                        "age": age,
                        "source": f"{_rel(ROOKIE_AGE_PATH)} display_age_only",
                    }
                )

    if player_id and not dp_market.empty:
        dp_matches = dp_market.loc[
            dp_market["nwr_player_id"].astype(str).map(_clean_id).eq(player_id)
            & dp_market["nwr_pos"].astype(str).str.upper().eq(position.upper())
            & dp_market["join_confidence"].astype(str).str.lower().eq("high")
        ]
        for _, match in dp_matches.iterrows():
            age = _age_text(match.get("age"))
            if age:
                candidates.append(
                    {
                        "age": age,
                        "source": f"{_rel(DP_MARKET_PATH)} DynastyProcess display fallback",
                    }
                )

    if player_id and not roster_context.empty:
        roster_matches = roster_context.loc[
            roster_context["sleeper_id"].astype(str).map(_clean_id).eq(player_id)
            & roster_context["position"].astype(str).str.upper().eq(position.upper())
            & roster_context["live_use_allowed"].astype(str).str.lower().eq("true")
            & roster_context["allowed_use"].astype(str).eq("display_stat_context_only")
            & roster_context["birth_date"].astype(str).str.strip().ne("")
        ]
        for _, match in roster_matches.iterrows():
            age = _display_age_from_birth_date(_text(match.get("birth_date")))
            if age:
                candidates.append(
                    {
                        "age": age,
                        "source": "nflverse roster display context display_stat_context_only",
                    }
                )
    return _dedupe_candidates(candidates)


def _apply_repair(consolidated: pd.DataFrame, row_index: int, repair: dict[str, str]) -> None:
    if repair["repaired_player_id"] and not _text(consolidated.at[row_index, "player_id"]):
        consolidated.at[row_index, "player_id"] = repair["repaired_player_id"]
    if repair["repaired_age"]:
        consolidated.at[row_index, "age"] = repair["repaired_age"]
        consolidated.at[row_index, "age_source"] = repair["age_source"]
        consolidated.at[row_index, "caveats"] = _append_caveat(
            consolidated.at[row_index, "caveats"],
            f"Missing ID/age repair: age filled from {repair['repair_source']}.",
        )


def _apply_conflict(consolidated: pd.DataFrame, row_index: int, repair: dict[str, str]) -> None:
    consolidated.at[row_index, "review_status"] = "REVIEW_NEEDED"
    consolidated.at[row_index, "manual_review_flag"] = "true"
    consolidated.at[row_index, "data_quality_status"] = "MANUAL_REVIEW"
    consolidated.at[row_index, "conflict_flags"] = _append_token(
        consolidated.at[row_index, "conflict_flags"],
        "age_conflict_review_needed",
    )
    consolidated.at[row_index, "caveats"] = _append_caveat(
        consolidated.at[row_index, "caveats"],
        repair["notes"],
    )


def _build_remaining_blockers(consolidated: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, str]] = []
    missing_ids = consolidated.loc[
        consolidated["player_id"].astype(str).str.strip().eq("")
    ]
    for _, row in missing_ids.iterrows():
        rows.append(
            _blocker_row(
                len(rows) + 1,
                "MISSING_PLAYER_ID",
                row,
                "Missing stable approved player_id.",
                "Manual identity review; do not fabricate IDs.",
            )
        )
    age_missing = consolidated.loc[
        consolidated["age"].astype(str).eq(NOT_ENOUGH_INFORMATION)
        & ~consolidated["conflict_flags"].astype(str).str.contains("age_conflict_review_needed")
    ]
    for _, row in age_missing.iterrows():
        rows.append(
            _blocker_row(
                len(rows) + 1,
                "MISSING_AGE",
                row,
                "Missing approved age coverage.",
                "Add approved age source coverage or keep Not enough information.",
            )
        )
    age_conflicts = consolidated.loc[
        consolidated["conflict_flags"].astype(str).str.contains("age_conflict_review_needed")
    ]
    for _, row in age_conflicts.iterrows():
        rows.append(
            _blocker_row(
                len(rows) + 1,
                "AGE_CONFLICT_REVIEW_NEEDED",
                row,
                "Approved display-age sources conflict.",
                "Resolve age conflict before app wiring.",
            )
        )
    review_needed = consolidated.loc[consolidated["review_status"].astype(str).eq("REVIEW_NEEDED")]
    for _, row in review_needed.iterrows():
        rows.append(
            _blocker_row(
                len(rows) + 1,
                "REVIEW_NEEDED_ROW",
                row,
                "Row remains REVIEW_NEEDED in the review artifact.",
                "Clear manual review/source caveats before app wiring.",
            )
        )
    return pd.DataFrame(rows, columns=BLOCKER_COLUMNS)


def _blocker_row(
    blocker_num: int,
    blocker_type: str,
    row: pd.Series,
    detail: str,
    recommended_action: str,
) -> dict[str, str]:
    return {
        "blocker_id": f"BLOCKER-{blocker_num:04d}",
        "blocker_type": blocker_type,
        "player_name": _text(row.get("player_name")),
        "position": _text(row.get("position")),
        "source_layer": _text(row.get("source_layers")),
        "detail": detail,
        "prevents_app_wiring": "yes",
        "recommended_action": recommended_action,
        "notes": _text(row.get("caveats")),
    }


def _update_source_summary(consolidated: pd.DataFrame, blockers: pd.DataFrame) -> pd.DataFrame:
    summary = pd.read_csv(SOURCE_SUMMARY_PATH, keep_default_na=False, dtype=str)
    consolidated_mask = summary["layer"].astype(str).eq("Consolidated review output")
    if consolidated_mask.any():
        summary.loc[consolidated_mask, "row_count"] = str(len(consolidated))
        summary.loc[consolidated_mask, "unique_player_count"] = str(consolidated[
            ["normalized_name", "position"]
        ].drop_duplicates().shape[0])
        summary.loc[consolidated_mask, "player_id_coverage"] = str(int(
            consolidated["player_id"].astype(str).str.strip().ne("").sum()
        ))
        summary.loc[consolidated_mask, "age_coverage"] = str(int(
            consolidated["age"].astype(str).ne(NOT_ENOUGH_INFORMATION).sum()
        ))
        summary.loc[consolidated_mask, "review_needed_count"] = str(int(
            consolidated["review_status"].astype(str).eq("REVIEW_NEEDED").sum()
        ))
    blockers_mask = summary["layer"].astype(str).eq("Remaining blockers output")
    if blockers_mask.any():
        summary.loc[blockers_mask, "row_count"] = str(len(blockers))
    return summary


def _update_validation_report(
    consolidated: pd.DataFrame,
    blockers: pd.DataFrame,
    repair_frame: pd.DataFrame,
) -> pd.DataFrame:
    report = pd.read_csv(VALIDATION_REPORT_PATH, keep_default_na=False, dtype=str)
    checks = [
        _check_row(
            "missing_id_age_repair_schema_valid",
            set(REPAIR_COLUMNS).issubset(repair_frame.columns),
            "repair CSV required columns present",
        ),
        _check_row(
            "repaired_age_source_present",
            repair_frame.loc[
                repair_frame["repair_status"].eq("REPAIRED")
                & repair_frame["repaired_age"].astype(str).str.strip().ne(""),
                "age_source",
            ]
            .astype(str)
            .str.strip()
            .ne("")
            .all(),
            "repaired age rows require age_source",
        ),
        _check_row(
            "no_player_id_repair_without_approved_source",
            repair_frame.loc[
                repair_frame["repaired_player_id"].astype(str).str.strip().ne("")
                & repair_frame["original_player_id"].astype(str).str.strip().eq(""),
                "repair_source",
            ]
            .astype(str)
            .str.strip()
            .ne("")
            .all(),
            "new player_id values must cite an approved source",
        ),
        _check_row(
            "repair_preserves_app_and_model_no",
            consolidated["app_wiring_allowed"].astype(str).str.lower().eq("no").all()
            and consolidated["model_input_allowed"].astype(str).str.lower().eq("no").all(),
            "repair artifact remains blocked from app/model usage",
        ),
        _check_row(
            "remaining_blockers_load_after_repair",
            not blockers.empty,
            f"remaining blockers rows={len(blockers)}",
        ),
    ]
    names = {row["check_name"] for row in checks}
    report = report.loc[~report["check_name"].isin(names)]
    return pd.concat([report, pd.DataFrame(checks)], ignore_index=True)


def _check_row(check_name: str, passed: bool, detail: str) -> dict[str, str]:
    return {"check_name": check_name, "status": "PASS" if passed else "FAIL", "detail": detail}


def _repair_row(
    blocker: pd.Series,
    row: pd.Series,
    *,
    repaired_player_id: str,
    repaired_age: str,
    age_source: str,
    repair_status: str,
    repair_source: str,
    confidence: str,
    notes: str,
) -> dict[str, str]:
    return {
        "player_name": _text(blocker.get("player_name")),
        "position": _text(blocker.get("position")),
        "source_layer": _text(blocker.get("source_layer")),
        "player_type": _text(row.get("player_type")),
        "blocker_type": _text(blocker.get("blocker_type")),
        "original_player_id": _text(row.get("player_id")),
        "repaired_player_id": repaired_player_id,
        "original_age": _text(row.get("age")) or NOT_ENOUGH_INFORMATION,
        "repaired_age": repaired_age,
        "age_source": age_source,
        "repair_status": repair_status,
        "repair_source": repair_source,
        "confidence": confidence,
        "notes": notes,
    }


def _match_consolidated_row(consolidated: pd.DataFrame, blocker: pd.Series) -> int | None:
    name = _normalize(blocker.get("player_name"))
    position = _text(blocker.get("position")).upper()
    source_layer = _text(blocker.get("source_layer"))
    matched = consolidated.loc[
        consolidated["normalized_name"].astype(str).eq(name)
        & consolidated["position"].astype(str).str.upper().eq(position)
        & consolidated["source_layers"].astype(str).str.contains(source_layer, regex=False)
    ]
    if matched.empty:
        matched = consolidated.loc[
            consolidated["normalized_name"].astype(str).eq(name)
            & consolidated["position"].astype(str).str.upper().eq(position)
        ]
    if matched.empty:
        return None
    return int(matched.index[0])


def _read_optional_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, keep_default_na=False, dtype=str)


def _display_age_from_birth_date(value: str) -> str:
    if not value:
        return ""
    try:
        year, month, day = (int(part) for part in value.split("-"))
        born = date(year, month, day)
    except ValueError:
        return ""
    as_of = date(2026, 6, 24)
    return f"{((as_of - born).days / 365.25):.1f}"


def _dedupe_candidates(candidates: list[dict[str, str]]) -> list[dict[str, str]]:
    seen = set()
    output = []
    for candidate in candidates:
        key = (candidate["age"], candidate["source"])
        if key not in seen:
            output.append(candidate)
            seen.add(key)
    return output


def _append_caveat(caveats: str, addition: str) -> str:
    caveats = _text(caveats)
    if not caveats:
        return addition
    if addition in caveats:
        return caveats
    return f"{caveats} | {addition}"


def _append_token(value: str, token: str) -> str:
    pieces = [piece.strip() for piece in _text(value).split(";") if piece.strip()]
    if token not in pieces:
        pieces.append(token)
    return ";".join(pieces)


def _age_text(value: object) -> str:
    text = _text(value)
    if not text or text.upper() == "NA" or text.lower() == "nan":
        return ""
    try:
        number = float(text)
    except ValueError:
        return ""
    return f"{number:.1f}"


def _clean_id(value: object) -> str:
    return _text(value).replace(".0", "")


def _normalize(value: object) -> str:
    return " ".join(_text(value).lower().replace(".", "").replace("'", "").split())


def _text(value: object) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    return str(value).strip()


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


if __name__ == "__main__":
    main()
