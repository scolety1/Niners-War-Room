"""Pure CFBD snapshot, identity, feature, and temporal-admission contracts."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from src.services import new_evidence_foundation_service as foundation

POSITION_MAP = {
    "Quarterback": "QB",
    "Running Back": "RB",
    "Wide Receiver": "WR",
    "Tight End": "TE",
}
CORE_POSITIONS = set(POSITION_MAP.values())
EXACT_CLASSIFICATION = "EXACT_DRAFT_SLOT_WITH_AUTHORITATIVE_CROSSWALK"
UNRESOLVED_CLASSIFICATION = "UNRESOLVED"
SELECTED_STATS = {
    ("passing", "ATT"): "college_pass_attempts",
    ("passing", "COMPLETIONS"): "college_pass_completions",
    ("passing", "YDS"): "college_pass_yards",
    ("passing", "TD"): "college_pass_tds",
    ("passing", "INT"): "college_interceptions",
    ("rushing", "CAR"): "college_rush_attempts",
    ("rushing", "YDS"): "college_rush_yards",
    ("rushing", "TD"): "college_rush_tds",
    ("receiving", "REC"): "college_receptions",
    ("receiving", "YDS"): "college_receiving_yards",
    ("receiving", "TD"): "college_receiving_tds",
}
COUNTING_FEATURES = tuple(SELECTED_STATS.values())
DERIVED_FEATURES = (
    "college_scrimmage_yards",
    "college_scrimmage_tds",
    "college_total_opportunities",
    "college_pass_yards_per_attempt",
    "college_rush_yards_per_attempt",
    "college_receiving_yards_per_reception",
)
USAGE_FEATURES = (
    "college_usage_overall",
    "college_usage_pass",
    "college_usage_rush",
    "college_usage_standard_downs",
    "college_usage_passing_downs",
)
PPA_FEATURES = (
    "college_average_ppa_all",
    "college_average_ppa_pass",
    "college_average_ppa_rush",
    "college_total_ppa_all",
    "college_total_ppa_pass",
    "college_total_ppa_rush",
)
MODEL_FEATURES = COUNTING_FEATURES + DERIVED_FEATURES + USAGE_FEATURES + PPA_FEATURES


class CfbdEvidenceError(RuntimeError):
    """Base error for fail-closed CFBD college evidence."""


class CfbdSnapshotIntegrityError(CfbdEvidenceError):
    """Raised when immutable source bytes do not match their governed receipt."""


class CfbdIdentityError(CfbdEvidenceError):
    """Raised when a college-to-NFL identity contract is ambiguous or violated."""


class CfbdTemporalError(CfbdEvidenceError):
    """Raised when college evidence crosses its governed prediction boundary."""


@dataclass(frozen=True)
class Snapshot:
    catalog: dict[str, Any]
    manifest: dict[str, Any]
    root: Path


@dataclass(frozen=True)
class IdentityCrosswalk:
    exact: pd.DataFrame
    review: pd.DataFrame
    unresolved: pd.DataFrame


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_snapshot(catalog_path: Path, snapshot_root: Path) -> Snapshot:
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    required_catalog = {
        "foundation_id",
        "admission_id",
        "snapshot_id",
        "manifest_relative_path",
        "aggregate_sha256",
        "raw_payloads_committed",
    }
    missing = sorted(required_catalog - set(catalog))
    if missing:
        raise CfbdSnapshotIntegrityError(f"catalog fields missing: {missing}")
    if catalog["foundation_id"] != "NWR_NEW_EVIDENCE_FOUNDATION_V1":
        raise CfbdSnapshotIntegrityError("foundation authority drift")
    if catalog["admission_id"] != "NWR_CFBD_COLLEGE_EVIDENCE_ADMISSION_V1":
        raise CfbdSnapshotIntegrityError("CFBD admission authority drift")
    if bool(catalog["raw_payloads_committed"]):
        raise CfbdSnapshotIntegrityError("raw CFBD payload was marked for Git")

    manifest_path = snapshot_root / str(catalog["manifest_relative_path"])
    if not manifest_path.is_file():
        raise CfbdSnapshotIntegrityError("completion manifest is missing")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    root = manifest_path.parent.resolve()
    if manifest.get("snapshot_id") != catalog["snapshot_id"]:
        raise CfbdSnapshotIntegrityError("snapshot ID mismatch")
    if manifest.get("aggregate_sha256") != catalog["aggregate_sha256"]:
        raise CfbdSnapshotIntegrityError("catalog and manifest aggregate mismatch")
    if (
        manifest.get("provider") != "CollegeFootballData"
        or manifest.get("api_family") != "official REST API v2"
        or not bool(manifest.get("immutable"))
        or not bool(manifest.get("complete"))
    ):
        raise CfbdSnapshotIntegrityError("provider or completion contract drift")

    hashes: list[str] = []
    for asset in manifest.get("assets", []):
        relative = Path(str(asset.get("relative_path", "")))
        if relative.is_absolute() or ".." in relative.parts:
            raise CfbdSnapshotIntegrityError("unsafe asset path")
        path = root / relative
        if not path.is_file():
            raise CfbdSnapshotIntegrityError(f"asset missing: {relative.as_posix()}")
        if path.stat().st_size != int(asset.get("bytes", -1)):
            raise CfbdSnapshotIntegrityError(f"asset size drift: {relative.as_posix()}")
        actual = sha256_file(path)
        if actual != str(asset.get("sha256", "")):
            raise CfbdSnapshotIntegrityError(f"asset hash drift: {relative.as_posix()}")
        hashes.append(actual)
    aggregate = foundation.sha256_bytes("".join(hashes).encode("ascii"))
    if aggregate != manifest["aggregate_sha256"]:
        raise CfbdSnapshotIntegrityError("recomputed aggregate drift")
    pending = list(root.parent.glob(".pending-*"))
    if pending:
        raise CfbdSnapshotIntegrityError("pending CFBD snapshot exists")
    return Snapshot(catalog=catalog, manifest=manifest, root=root)


def load_family(snapshot: Snapshot, family: str) -> list[dict[str, Any]]:
    family_root = snapshot.root / "raw" / family
    if not family_root.is_dir():
        raise CfbdSnapshotIntegrityError(f"snapshot family missing: {family}")
    rows: list[dict[str, Any]] = []
    for path in sorted(family_root.glob("*.json"), key=lambda item: item.name):
        document = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(document, list) or not all(
            isinstance(row, dict) for row in document
        ):
            raise CfbdSnapshotIntegrityError(f"invalid family document: {path.name}")
        rows.extend(document)
    return rows


def _number(value: Any) -> float:
    try:
        number = float(value)
        return number if math.isfinite(number) else math.nan
    except (TypeError, ValueError):
        return math.nan


def _id(value: Any) -> str:
    if value is None:
        return ""
    try:
        number = float(value)
        if math.isfinite(number) and number.is_integer():
            return str(int(number))
    except (TypeError, ValueError):
        pass
    return foundation.normalized_id(value)


def build_identity_crosswalk(
    rookie: pd.DataFrame,
    draft_rows: list[dict[str, Any]],
) -> IdentityCrosswalk:
    required_rookie = {
        "gsis_id",
        "player_name",
        "position",
        "draft_year",
        "draft_round",
        "draft_pick",
        "drafted_status",
    }
    if not required_rookie.issubset(rookie.columns):
        raise CfbdIdentityError(
            f"rookie identity fields missing: {sorted(required_rookie - set(rookie))}"
        )
    provider = pd.DataFrame(draft_rows).copy()
    required_provider = {
        "year",
        "round",
        "overall",
        "collegeAthleteId",
        "nflAthleteId",
        "collegeTeam",
        "name",
        "position",
    }
    if not required_provider.issubset(provider.columns):
        raise CfbdIdentityError(
            f"CFBD draft fields missing: {sorted(required_provider - set(provider))}"
        )
    provider["position_code"] = provider["position"].map(POSITION_MAP).fillna("")
    for column in ("year", "round", "overall"):
        provider[column] = pd.to_numeric(provider[column], errors="coerce")
    duplicate_slots = provider.duplicated(["year", "round", "overall"], keep=False)
    if duplicate_slots.any():
        raise CfbdIdentityError("CFBD authoritative draft slot is not unique")

    base = rookie.copy()
    for column in ("draft_year", "draft_round", "draft_pick"):
        base[column] = pd.to_numeric(base[column], errors="coerce")
    if base["gsis_id"].map(_id).eq("").any() or base["gsis_id"].duplicated().any():
        raise CfbdIdentityError("rookie GSIS authority is blank or duplicated")
    merged = base.merge(
        provider[
            [
                "year",
                "round",
                "overall",
                "collegeAthleteId",
                "nflAthleteId",
                "collegeTeam",
                "name",
                "position_code",
            ]
        ],
        left_on=["draft_year", "draft_round", "draft_pick"],
        right_on=["year", "round", "overall"],
        how="left",
        indicator=True,
        validate="many_to_one",
    )
    slot_found = merged["_merge"].eq("both")
    college_id_present = merged["collegeAthleteId"].map(_id).ne("")
    exact_mask = (
        merged["drafted_status"].eq("DRAFTED") & slot_found & college_id_present
    )
    exact = merged.loc[exact_mask].copy()
    exact["cfbd_college_athlete_id"] = exact["collegeAthleteId"].map(_id)
    exact["cfbd_nfl_athlete_id"] = exact["nflAthleteId"].map(_id)
    exact["identity_classification"] = EXACT_CLASSIFICATION
    exact["identity_authority"] = "CFBD_AND_NFLVERSE_UNIQUE_YEAR_ROUND_OVERALL"
    exact["identity_join_keys"] = "draft_year|draft_round|draft_pick"
    exact["name_used_as_identity"] = False
    exact["name_agreement_diagnostic"] = (
        exact["player_name"].astype(str).str.casefold()
        == exact["name"].astype(str).str.casefold()
    )
    exact["position_agreement_diagnostic"] = (
        exact["position"].astype(str) == exact["position_code"].astype(str)
    )
    exact = exact.rename(
        columns={
            "name": "cfbd_player_name",
            "collegeTeam": "cfbd_college_team",
            "position_code": "cfbd_position",
        }
    )
    exact_columns = [
        "gsis_id",
        "cfbd_college_athlete_id",
        "cfbd_nfl_athlete_id",
        "player_name",
        "cfbd_player_name",
        "position",
        "cfbd_position",
        "draft_year",
        "draft_round",
        "draft_pick",
        "cfbd_college_team",
        "identity_classification",
        "identity_authority",
        "identity_join_keys",
        "name_used_as_identity",
        "name_agreement_diagnostic",
        "position_agreement_diagnostic",
    ]
    exact = exact[exact_columns].sort_values(
        ["draft_year", "draft_pick", "gsis_id"], kind="stable"
    )
    if exact["cfbd_college_athlete_id"].duplicated().any():
        raise CfbdIdentityError("CFBD college athlete maps to multiple NFL identities")

    unresolved = merged.loc[~exact_mask].copy()
    unresolved["cfbd_college_athlete_id"] = unresolved["collegeAthleteId"].map(_id)
    unresolved["identity_classification"] = UNRESOLVED_CLASSIFICATION
    unresolved["unresolved_reason"] = np.select(
        [
            unresolved["drafted_status"].eq("UNDRAFTED"),
            unresolved["_merge"].ne("both"),
            unresolved["collegeAthleteId"].map(_id).eq(""),
        ],
        [
            "UNDRAFTED_NO_CFBD_DRAFT_IDENTITY",
            "CFBD_DRAFT_SLOT_NOT_FOUND",
            "CFBD_COLLEGE_ATHLETE_ID_MISSING",
        ],
        default="UNRESOLVED_IDENTITY_CONTRACT",
    )
    unresolved["name_used_as_identity"] = False
    unresolved = unresolved[
        [
            "gsis_id",
            "player_name",
            "position",
            "draft_year",
            "draft_round",
            "draft_pick",
            "drafted_status",
            "cfbd_college_athlete_id",
            "identity_classification",
            "unresolved_reason",
            "name_used_as_identity",
        ]
    ].sort_values(["draft_year", "position", "gsis_id"], kind="stable")
    if len(exact) + len(unresolved) != len(rookie):
        raise CfbdIdentityError("identity partition dropped or duplicated rookie rows")
    review = pd.DataFrame(
        columns=[
            "gsis_id",
            "player_name",
            "position",
            "draft_year",
            "candidate_cfbd_college_athlete_id",
            "review_reason",
            "name_used_as_identity",
        ]
    )
    return IdentityCrosswalk(
        exact=exact.reset_index(drop=True),
        review=review,
        unresolved=unresolved.reset_index(drop=True),
    )


def _terminal_seasons(
    exact: pd.DataFrame,
    stats: pd.DataFrame,
) -> pd.DataFrame:
    authority = exact[
        ["gsis_id", "cfbd_college_athlete_id", "draft_year"]
    ].copy()
    authority["draft_year"] = pd.to_numeric(authority["draft_year"], errors="coerce")
    candidates = stats.merge(
        authority, left_on="playerId", right_on="cfbd_college_athlete_id", how="inner"
    )
    candidates["season"] = pd.to_numeric(candidates["season"], errors="coerce")
    candidates = candidates[candidates["season"] < candidates["draft_year"]].copy()
    terminal = (
        candidates.groupby(
            ["gsis_id", "cfbd_college_athlete_id", "draft_year"], as_index=False
        )["season"]
        .max()
        .rename(columns={"season": "college_terminal_season"})
    )
    return terminal


def _safe_divide(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    top = pd.to_numeric(numerator, errors="coerce")
    bottom = pd.to_numeric(denominator, errors="coerce")
    return top.div(bottom.where(bottom.ne(0)))


def _primary_nested_row(
    frame: pd.DataFrame,
    *,
    nested_column: str,
    ranking_key: str,
) -> pd.DataFrame:
    if frame.empty:
        return frame
    data = frame.copy()
    data["_rank"] = data[nested_column].map(
        lambda value: abs(_number(value.get(ranking_key))) if isinstance(value, dict) else -1
    )
    data["_team_sort"] = (
        data["team"].astype(str)
        if "team" in data
        else pd.Series("", index=data.index, dtype=str)
    )
    return (
        data.sort_values(
            ["cfbd_college_athlete_id", "season", "_rank", "_team_sort"],
            ascending=[True, True, False, True],
            kind="stable",
        )
        .drop_duplicates(["cfbd_college_athlete_id", "season"], keep="first")
        .drop(columns=["_rank", "_team_sort"])
    )


def build_college_features(
    exact: pd.DataFrame,
    *,
    stat_rows: list[dict[str, Any]],
    usage_rows: list[dict[str, Any]],
    ppa_rows: list[dict[str, Any]],
) -> pd.DataFrame:
    if exact.empty:
        return pd.DataFrame()
    exact_ids = set(exact["cfbd_college_athlete_id"].map(_id))
    stats = pd.DataFrame(
        [
            row
            for row in stat_rows
            if _id(row.get("playerId")) in exact_ids
            and (row.get("category"), row.get("statType")) in SELECTED_STATS
        ]
    )
    if stats.empty:
        raise CfbdEvidenceError("no selected college statistics matched exact identities")
    stats["playerId"] = stats["playerId"].map(_id)
    terminal = _terminal_seasons(exact, stats)
    if terminal.empty:
        raise CfbdEvidenceError("no pre-draft terminal college seasons were found")
    selected = stats.merge(
        terminal,
        left_on=["playerId", "season"],
        right_on=["cfbd_college_athlete_id", "college_terminal_season"],
        how="inner",
    )
    selected["feature"] = [
        SELECTED_STATS[(category, stat_type)]
        for category, stat_type in zip(
            selected["category"], selected["statType"], strict=True
        )
    ]
    selected["numeric_stat"] = selected["stat"].map(_number)
    counting = (
        selected.groupby(
            [
                "gsis_id",
                "cfbd_college_athlete_id",
                "draft_year",
                "college_terminal_season",
                "feature",
            ],
            as_index=False,
        )["numeric_stat"]
        .sum(min_count=1)
        .pivot(
            index=[
                "gsis_id",
                "cfbd_college_athlete_id",
                "draft_year",
                "college_terminal_season",
            ],
            columns="feature",
            values="numeric_stat",
        )
        .reset_index()
    )
    counting.columns.name = None
    for feature in COUNTING_FEATURES:
        if feature not in counting:
            counting[feature] = np.nan

    usage = pd.DataFrame(
        [row for row in usage_rows if _id(row.get("id")) in exact_ids]
    )
    if not usage.empty:
        usage["cfbd_college_athlete_id"] = usage["id"].map(_id)
        usage["season"] = pd.to_numeric(usage["season"], errors="coerce")
        usage = _primary_nested_row(
            usage, nested_column="usage", ranking_key="overall"
        )
        usage_values = usage[
            ["cfbd_college_athlete_id", "season", "team", "usage"]
        ].copy()
        for source, target in (
            ("overall", "college_usage_overall"),
            ("pass", "college_usage_pass"),
            ("rush", "college_usage_rush"),
            ("standardDowns", "college_usage_standard_downs"),
            ("passingDowns", "college_usage_passing_downs"),
        ):
            usage_values[target] = usage_values["usage"].map(
                lambda value, key=source: (
                    _number(value.get(key)) if isinstance(value, dict) else math.nan
                )
            )
        usage_values = usage_values.rename(
            columns={"season": "college_terminal_season", "team": "cfbd_usage_team"}
        ).drop(columns="usage")
    else:
        usage_values = pd.DataFrame(
            columns=[
                "cfbd_college_athlete_id",
                "college_terminal_season",
                "cfbd_usage_team",
                *USAGE_FEATURES,
            ]
        )

    ppa = pd.DataFrame([row for row in ppa_rows if _id(row.get("id")) in exact_ids])
    if not ppa.empty:
        ppa["cfbd_college_athlete_id"] = ppa["id"].map(_id)
        ppa["season"] = pd.to_numeric(ppa["season"], errors="coerce")
        ppa = _primary_nested_row(
            ppa, nested_column="totalPPA", ranking_key="all"
        )
        ppa_values = ppa[
            [
                "cfbd_college_athlete_id",
                "season",
                "team",
                "averagePPA",
                "totalPPA",
            ]
        ].copy()
        for container, prefix in (
            ("averagePPA", "college_average_ppa"),
            ("totalPPA", "college_total_ppa"),
        ):
            for source in ("all", "pass", "rush"):
                ppa_values[f"{prefix}_{source}"] = ppa_values[container].map(
                    lambda value, key=source: (
                        _number(value.get(key)) if isinstance(value, dict) else math.nan
                    )
                )
        ppa_values = ppa_values.rename(
            columns={"season": "college_terminal_season", "team": "cfbd_ppa_team"}
        ).drop(columns=["averagePPA", "totalPPA"])
    else:
        ppa_values = pd.DataFrame(
            columns=[
                "cfbd_college_athlete_id",
                "college_terminal_season",
                "cfbd_ppa_team",
                *PPA_FEATURES,
            ]
        )

    features = counting.merge(
        usage_values,
        on=["cfbd_college_athlete_id", "college_terminal_season"],
        how="left",
        validate="one_to_one",
    ).merge(
        ppa_values,
        on=["cfbd_college_athlete_id", "college_terminal_season"],
        how="left",
        validate="one_to_one",
    )
    features["college_scrimmage_yards"] = features[
        ["college_rush_yards", "college_receiving_yards"]
    ].sum(axis=1, min_count=1)
    features["college_scrimmage_tds"] = features[
        ["college_rush_tds", "college_receiving_tds"]
    ].sum(axis=1, min_count=1)
    features["college_total_opportunities"] = features[
        ["college_pass_attempts", "college_rush_attempts", "college_receptions"]
    ].sum(axis=1, min_count=1)
    features["college_pass_yards_per_attempt"] = _safe_divide(
        features["college_pass_yards"], features["college_pass_attempts"]
    )
    features["college_rush_yards_per_attempt"] = _safe_divide(
        features["college_rush_yards"], features["college_rush_attempts"]
    )
    features["college_receiving_yards_per_reception"] = _safe_divide(
        features["college_receiving_yards"], features["college_receptions"]
    )
    features["college_season_gap"] = (
        pd.to_numeric(features["draft_year"], errors="coerce")
        - pd.to_numeric(features["college_terminal_season"], errors="coerce")
    )
    features["college_stats_present"] = features[list(COUNTING_FEATURES)].notna().any(
        axis=1
    )
    features["college_usage_present"] = features[list(USAGE_FEATURES)].notna().any(
        axis=1
    )
    features["college_ppa_present"] = features[list(PPA_FEATURES)].notna().any(axis=1)
    features["identity_classification"] = EXACT_CLASSIFICATION
    features["temporal_availability"] = (
        "PASS_FINAL_COLLEGE_SEASON_PRECEDES_DRAFT_"
        "WITH_RETROSPECTIVE_REVISION_LIMIT"
    )
    features["source_snapshot_class"] = "IMMUTABLE_RETRIEVAL_2026-07-30"
    features = features.merge(
        exact[
            [
                "gsis_id",
                "player_name",
                "position",
                "cfbd_player_name",
                "cfbd_position",
                "cfbd_college_team",
            ]
        ],
        on="gsis_id",
        how="left",
        validate="one_to_one",
    )
    validate_college_features(features, exact)
    leading = [
        "gsis_id",
        "cfbd_college_athlete_id",
        "player_name",
        "cfbd_player_name",
        "position",
        "cfbd_position",
        "draft_year",
        "college_terminal_season",
        "college_season_gap",
        "cfbd_college_team",
        "cfbd_usage_team",
        "cfbd_ppa_team",
        "identity_classification",
        "temporal_availability",
        "source_snapshot_class",
        "college_stats_present",
        "college_usage_present",
        "college_ppa_present",
    ]
    return features[
        leading + list(COUNTING_FEATURES + DERIVED_FEATURES + USAGE_FEATURES + PPA_FEATURES)
    ].sort_values(["draft_year", "position", "gsis_id"], kind="stable").reset_index(
        drop=True
    )


def validate_college_features(features: pd.DataFrame, exact: pd.DataFrame) -> None:
    if features["gsis_id"].duplicated().any():
        raise CfbdIdentityError("college feature panel duplicated an NFL identity")
    exact_ids = set(exact["gsis_id"].map(_id))
    if not set(features["gsis_id"].map(_id)).issubset(exact_ids):
        raise CfbdIdentityError("unresolved identity entered college feature panel")
    if features["identity_classification"].ne(EXACT_CLASSIFICATION).any():
        raise CfbdIdentityError("non-exact identity entered college feature panel")
    terminal = pd.to_numeric(features["college_terminal_season"], errors="coerce")
    draft = pd.to_numeric(features["draft_year"], errors="coerce")
    if terminal.isna().any() or draft.isna().any() or (terminal >= draft).any():
        raise CfbdTemporalError("college season is not strictly before NFL draft year")
    if any("adp" in column.lower() for column in features.columns):
        raise CfbdTemporalError("current ADP entered college evidence")
    if "name_used_as_identity" in features and features[
        "name_used_as_identity"
    ].astype(bool).any():
        raise CfbdIdentityError("name-only identity entered college evidence")


def coverage_rows(
    rookie: pd.DataFrame,
    identities: IdentityCrosswalk,
    features: pd.DataFrame,
) -> pd.DataFrame:
    exact_ids = set(identities.exact["gsis_id"])
    feature_ids = set(features["gsis_id"])
    rows: list[dict[str, Any]] = []
    base = rookie.copy()
    base["draft_year"] = pd.to_numeric(base["draft_year"], errors="coerce")
    for keys, group in base.groupby(["draft_year", "position"], dropna=False):
        year, position = keys
        drafted = group["drafted_status"].eq("DRAFTED")
        rows.append(
            {
                "draft_year": int(year),
                "position": str(position),
                "rookie_rows": len(group),
                "drafted_rows": int(drafted.sum()),
                "exact_identity_rows": int(group["gsis_id"].isin(exact_ids).sum()),
                "terminal_feature_rows": int(group["gsis_id"].isin(feature_ids).sum()),
                "exact_identity_pct_of_drafted": round(
                    group.loc[drafted, "gsis_id"].isin(exact_ids).mean()
                    if drafted.any()
                    else 0.0,
                    6,
                ),
                "terminal_feature_pct_of_drafted": round(
                    group.loc[drafted, "gsis_id"].isin(feature_ids).mean()
                    if drafted.any()
                    else 0.0,
                    6,
                ),
            }
        )
    return pd.DataFrame(rows).sort_values(
        ["draft_year", "position"], kind="stable"
    ).reset_index(drop=True)
