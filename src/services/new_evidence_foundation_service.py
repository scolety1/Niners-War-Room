"""Pure contracts for NWR rookie, opportunity, and availability foundations."""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import numpy as np
import pandas as pd

CORE_POSITIONS = ("QB", "RB", "WR", "TE")
NFLREADPY_VERSION = "0.1.5"
ALLOWED_INITIAL_HOST = "github.com"
ALLOWED_FINAL_HOSTS = {
    "codeload.github.com",
    "github.com",
    "release-assets.githubusercontent.com",
    "objects.githubusercontent.com",
}
SOURCE_STATUSES = {
    "ADMITTED_PRIMARY_SOURCE",
    "ADMITTED_WITH_COVERAGE_LIMIT",
    "REVIEW_ONLY_SOURCE",
    "BLOCKED_LICENSE_OR_TERMS",
    "BLOCKED_IDENTITY",
    "BLOCKED_TEMPORAL_AVAILABILITY",
    "BLOCKED_SCHEMA",
    "NOT_ENOUGH_INFORMATION",
}
IDENTITY_STATUSES = {
    "EXACT_SHARED_GSIS_ID",
    "EXACT_SHARED_PROVIDER_ID",
    "EXACT_DRAFT_SLOT_WITH_AUTHORITATIVE_CROSSWALK",
    "REVIEW_ONLY_UNIQUE_DRAFT_SLOT_CANDIDATE",
    "HUMAN_REVIEW_REQUIRED",
    "UNRESOLVED",
}
FEATURE_DECISIONS = {
    "ADMIT_SOURCE_AND_FEATURE",
    "ADMIT_SOURCE_FEATURE_REVIEW_ONLY",
    "ADMIT_SOURCE_FEATURE_NOT_INCREMENTAL",
    "BLOCK_SOURCE",
    "BLOCK_FEATURE",
    "NOT_ENOUGH_INFORMATION",
}
IDENTITY_COLUMNS = (
    "source_dataset",
    "source_row",
    "gsis_id",
    "identity_classification",
    "provider_authority",
    "provider_id",
    "player_name",
    "position",
    "draft_year",
    "draft_round",
    "draft_pick",
    "name_used_as_identity",
)

REPLACEMENT_RANK = {"QB": 12, "RB": 36, "WR": 48, "TE": 18}
TOP_RANK = {"QB": 12, "RB": 24, "WR": 24, "TE": 12}


class FoundationContractError(RuntimeError):
    """Base fail-closed foundation error."""


class SourceAdmissionError(FoundationContractError):
    """Source provenance, schema, immutable-byte, or terms failure."""


class IdentityAdmissionError(FoundationContractError):
    """Identity authority failure."""


class TemporalLeakageError(FoundationContractError):
    """Feature availability is later than its prediction boundary."""


class PanelContractError(FoundationContractError):
    """Rookie/opportunity/availability panel contract failure."""


class SecretExposureError(FoundationContractError):
    """A credential-like value reached a governed artifact."""


class RequestLimitError(FoundationContractError):
    """A source call budget would be exceeded."""


@dataclass(frozen=True)
class IdentityTables:
    exact: pd.DataFrame
    review: pd.DataFrame
    unresolved: pd.DataFrame


@dataclass(frozen=True)
class EvaluationResult:
    predictions: pd.DataFrame
    metrics: pd.DataFrame


def sha256_bytes(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def schema_fingerprint(frame: pd.DataFrame) -> str:
    fields = [
        {"name": str(column), "dtype": str(frame[column].dtype)}
        for column in frame.columns
    ]
    body = json.dumps(fields, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return sha256_bytes(body)


def require_official_url(url: str, *, final: bool = False) -> None:
    parsed = urlparse(url)
    allowed = ALLOWED_FINAL_HOSTS if final else {ALLOWED_INITIAL_HOST}
    if parsed.scheme != "https" or parsed.hostname not in allowed:
        raise SourceAdmissionError(f"unauthorized nflverse source URL: {url}")
    if parsed.hostname == "github.com" and not parsed.path.startswith("/nflverse/"):
        raise SourceAdmissionError(f"non-nflverse GitHub source URL: {url}")


def require_no_secret(text: str, known_tokens: Iterable[str] = ()) -> None:
    lowered = text.lower()
    if re.search(r"(?i)authorization\s*[:=]\s*bearer\s+\S+", text):
        raise SecretExposureError("authorization bearer value reached governed output")
    if re.search(r"(?i)\b(?:cfbd_bearer_token|bearer_token)\s*[:=]\s*\S+", text):
        raise SecretExposureError("CFBD environment assignment reached governed output")
    for token in known_tokens:
        if token and token in text:
            raise SecretExposureError("known credential reached governed output")
    if "sk-" in lowered and re.search(r"sk-[a-z0-9_-]{12,}", lowered):
        raise SecretExposureError("credential-like token reached governed output")


def enforce_request_limit(request_count: int, limit: int) -> None:
    if request_count < 0 or limit < 0 or request_count > limit:
        raise RequestLimitError(
            f"request plan exceeds governed limit {limit}: {request_count}"
        )


def validate_expected_digest(actual: str, expected: str, *, label: str) -> None:
    if not actual or not expected or actual != expected:
        raise SourceAdmissionError(f"{label} hash drift")


def validate_schema_record(
    *,
    actual_schema: Sequence[Mapping[str, Any]],
    expected_schema: Sequence[Mapping[str, Any]],
    actual_rows: int,
    expected_rows: int,
) -> None:
    actual = [
        {"name": str(field["name"]), "dtype": str(field["dtype"])}
        for field in actual_schema
    ]
    expected = [
        {"name": str(field["name"]), "dtype": str(field["dtype"])}
        for field in expected_schema
    ]
    if actual != expected or int(actual_rows) != int(expected_rows):
        raise SourceAdmissionError("schema or row-count drift")


def validate_snapshot_metadata(manifest: Mapping[str, Any]) -> None:
    required = {
        "schema_version",
        "provider",
        "dataset",
        "snapshot_id",
        "retrieved_at_utc",
        "package_name",
        "package_version",
        "source_release",
        "license_spdx",
        "license_url",
        "immutable",
        "complete",
        "aggregate_sha256",
        "assets",
    }
    missing = sorted(required - set(manifest))
    if missing:
        raise SourceAdmissionError(f"snapshot manifest missing fields: {missing}")
    if manifest["provider"] != "nflverse":
        raise SourceAdmissionError("snapshot provider must be nflverse")
    if manifest["package_name"] != "nflreadpy":
        raise SourceAdmissionError("snapshot client must be nflreadpy")
    if manifest["package_version"] != NFLREADPY_VERSION:
        raise SourceAdmissionError("nflreadpy version drift")
    if not manifest["license_spdx"] or not manifest["license_url"]:
        raise SourceAdmissionError("missing license receipt")
    if not bool(manifest["immutable"]) or not bool(manifest["complete"]):
        raise SourceAdmissionError("snapshot is mutable or incomplete")

    downloaded_hashes: list[str] = []
    for asset in manifest["assets"]:
        if asset.get("status") != "downloaded":
            continue
        source_url = str(asset.get("source_url", ""))
        final_url = str(asset.get("final_url", source_url))
        if not source_url:
            raise SourceAdmissionError("missing source URL")
        require_official_url(source_url)
        require_official_url(final_url, final=True)
        asset_hash = str(asset.get("sha256", ""))
        if not asset_hash:
            raise SourceAdmissionError("missing snapshot asset hash")
        downloaded_hashes.append(asset_hash)
    aggregate = (
        downloaded_hashes[0]
        if manifest["dataset"] == "nflreadpy_client" and len(downloaded_hashes) == 1
        else sha256_bytes("".join(downloaded_hashes).encode("ascii"))
    )
    validate_expected_digest(
        aggregate,
        str(manifest["aggregate_sha256"]),
        label="snapshot aggregate",
    )


def validate_snapshot_manifest(
    manifest: Mapping[str, Any],
    *,
    snapshot_root: Path,
) -> None:
    validate_snapshot_metadata(manifest)

    snapshot_id = str(manifest["snapshot_id"])
    dataset = str(manifest["dataset"])
    base = (snapshot_root / "nflverse" / dataset / snapshot_id).resolve()
    root = snapshot_root.resolve()
    if root not in base.parents:
        raise SourceAdmissionError("snapshot path escapes governed root")
    terms_receipt = base / "LICENSE_TERMS_RECEIPT.json"
    if not terms_receipt.is_file():
        raise SourceAdmissionError("missing license receipt")
    for asset in manifest["assets"]:
        if asset.get("status") != "downloaded":
            continue
        relative = Path(str(asset.get("relative_path", "")))
        if relative.is_absolute() or ".." in relative.parts:
            raise SourceAdmissionError("unsafe snapshot asset path")
        path = base / relative
        if not path.is_file():
            raise SourceAdmissionError(f"snapshot asset is missing: {relative}")
        if path.stat().st_size != int(asset.get("bytes", -1)):
            raise SourceAdmissionError(f"snapshot asset size drift: {relative}")
        validate_expected_digest(
            sha256_file(path),
            str(asset.get("sha256", "")),
            label=f"snapshot asset {relative}",
        )


def normalized_id(value: Any) -> str:
    text = str(value if value is not None else "").strip()
    if text.lower() in {"", "nan", "none", "null", "na", "n/a"}:
        return ""
    return text


def first_column(frame: pd.DataFrame, names: Sequence[str]) -> str:
    for name in names:
        if name in frame.columns:
            return name
    return ""


def _value(row: Mapping[str, Any], names: Sequence[str]) -> str:
    for name in names:
        if name in row:
            value = normalized_id(row.get(name))
            if value:
                return value
    return ""


def _numeric(value: Any) -> float:
    try:
        number = float(value)
        return number if math.isfinite(number) else math.nan
    except (TypeError, ValueError):
        return math.nan


def validate_gsis_ids(frame: pd.DataFrame, column: str = "gsis_id") -> None:
    if column not in frame:
        raise IdentityAdmissionError(f"missing GSIS column: {column}")
    values = frame[column].map(normalized_id)
    if values.eq("").any():
        raise IdentityAdmissionError("blank GSIS ID")
    nonblank = values[values.ne("")]
    if nonblank.duplicated().any():
        duplicated = sorted(nonblank[nonblank.duplicated(keep=False)].unique())
        raise IdentityAdmissionError(f"duplicate GSIS IDs: {duplicated[:5]}")


def validate_identity_admission_rows(
    exact: pd.DataFrame,
    review: pd.DataFrame,
    unresolved: pd.DataFrame,
) -> None:
    expected = set(IDENTITY_COLUMNS)
    for label, frame in (
        ("exact", exact),
        ("review", review),
        ("unresolved", unresolved),
    ):
        if not expected.issubset(frame.columns):
            raise IdentityAdmissionError(
                f"{label} identity output missing fields: "
                f"{sorted(expected - set(frame.columns))}"
            )
        if frame["name_used_as_identity"].astype(str).str.lower().eq("true").any():
            raise IdentityAdmissionError("name-only join attempted")

    exact_statuses = {
        "EXACT_SHARED_GSIS_ID",
        "EXACT_SHARED_PROVIDER_ID",
        "EXACT_DRAFT_SLOT_WITH_AUTHORITATIVE_CROSSWALK",
    }
    if not exact["identity_classification"].isin(exact_statuses).all():
        raise IdentityAdmissionError("non-exact row admitted to exact crosswalk")
    if exact["gsis_id"].map(normalized_id).eq("").any():
        raise IdentityAdmissionError("blank GSIS ID admitted to exact crosswalk")
    if review["gsis_id"].map(normalized_id).ne("").any():
        raise IdentityAdmissionError("review-only identity admitted as exact")
    if unresolved["gsis_id"].map(normalized_id).ne("").any():
        raise IdentityAdmissionError("unresolved identity admitted as exact")

    authoritative = exact[
        exact["provider_authority"].map(normalized_id).ne("")
        & exact["provider_id"].map(normalized_id).ne("")
    ].copy()
    if not authoritative.empty:
        conflicts = authoritative.groupby(
            ["provider_authority", "provider_id"], dropna=False
        )["gsis_id"].nunique()
        if conflicts.gt(1).any():
            raise IdentityAdmissionError(
                "provider or draft-slot authority maps to multiple GSIS IDs"
            )


def build_identity_tables(
    players: pd.DataFrame,
    draft_picks: pd.DataFrame,
    combine: pd.DataFrame,
) -> IdentityTables:
    """Build exact, review-only, and unresolved NFL identity tables.

    Exact joins use GSIS, a shared provider identifier, or an authoritative
    unique draft slot. Names are carried as display evidence only.
    """

    players = players.copy().reset_index(drop=True)
    draft_picks = draft_picks.copy().reset_index(drop=True)
    combine = combine.copy().reset_index(drop=True)
    gsis_col = first_column(players, ("gsis_id", "player_id"))
    if not gsis_col:
        raise IdentityAdmissionError("players source has no GSIS identity")
    validate_gsis_ids(players.rename(columns={gsis_col: "gsis_id"}), "gsis_id")

    provider_columns = {
        "pfr_id": ("pfr_id", "pfr_player_id"),
        "espn_id": ("espn_id",),
        "sportradar_id": ("sportradar_id",),
    }
    provider_maps: dict[str, dict[str, str]] = {}
    for authority, aliases in provider_columns.items():
        column = first_column(players, aliases)
        mapping: dict[str, str] = {}
        if column:
            for _, row in players.iterrows():
                provider_id = normalized_id(row[column])
                gsis_id = normalized_id(row[gsis_col])
                if not provider_id or not gsis_id:
                    continue
                if provider_id in mapping and mapping[provider_id] != gsis_id:
                    raise IdentityAdmissionError(f"ambiguous shared provider ID: {provider_id}")
                mapping[provider_id] = gsis_id
        provider_maps[authority] = mapping

    exact_rows: list[dict[str, Any]] = []
    review_rows: list[dict[str, Any]] = []
    unresolved_rows: list[dict[str, Any]] = []

    for index, row in players.iterrows():
        gsis_id = normalized_id(row[gsis_col])
        target = exact_rows if gsis_id else unresolved_rows
        target.append(
            _identity_row(
                "players",
                index,
                gsis_id,
                "EXACT_SHARED_GSIS_ID" if gsis_id else "UNRESOLVED",
                row,
                provider_authority="gsis_id" if gsis_id else "",
                provider_id=gsis_id,
            )
        )

    draft_exact_by_index: dict[int, str] = {}
    draft_slots: dict[tuple[str, str, str], list[tuple[int, str]]] = {}
    for index, row in draft_picks.iterrows():
        direct = _value(row, ("gsis_id", "player_id"))
        matched = direct
        classification = "EXACT_SHARED_GSIS_ID" if direct else ""
        authority = "gsis_id" if direct else ""
        provider_id = direct
        if not matched:
            for provider, aliases in provider_columns.items():
                candidate = _value(row, aliases)
                if candidate and candidate in provider_maps[provider]:
                    matched = provider_maps[provider][candidate]
                    classification = "EXACT_SHARED_PROVIDER_ID"
                    authority = provider
                    provider_id = candidate
                    break
        slot = _draft_slot(row)
        if slot:
            draft_slots.setdefault(slot, []).append((index, matched))
        if matched:
            draft_exact_by_index[index] = matched
            exact_rows.append(
                _identity_row(
                    "draft_picks",
                    index,
                    matched,
                    classification,
                    row,
                    provider_authority=authority,
                    provider_id=provider_id,
                )
            )
        else:
            unresolved_rows.append(
                _identity_row("draft_picks", index, "", "UNRESOLVED", row)
            )

    for index, row in combine.iterrows():
        matched = ""
        classification = ""
        authority = ""
        provider_id = ""
        direct = _value(row, ("gsis_id", "player_id"))
        if direct:
            matched = direct
            classification = "EXACT_SHARED_GSIS_ID"
            authority = "gsis_id"
            provider_id = direct
        else:
            for provider, aliases in provider_columns.items():
                candidate = _value(row, aliases)
                if candidate and candidate in provider_maps[provider]:
                    matched = provider_maps[provider][candidate]
                    classification = "EXACT_SHARED_PROVIDER_ID"
                    authority = provider
                    provider_id = candidate
                    break
        slot = _draft_slot(row)
        slot_candidates = draft_slots.get(slot, []) if slot else []
        exact_slot_ids = sorted({gsis for _, gsis in slot_candidates if gsis})
        if not matched and len(slot_candidates) == 1 and len(exact_slot_ids) == 1:
            matched = exact_slot_ids[0]
            classification = "EXACT_DRAFT_SLOT_WITH_AUTHORITATIVE_CROSSWALK"
            authority = "draft_year_round_pick"
            provider_id = "|".join(slot)

        if matched:
            exact_rows.append(
                _identity_row(
                    "combine",
                    index,
                    matched,
                    classification,
                    row,
                    provider_authority=authority,
                    provider_id=provider_id,
                )
            )
        elif len(slot_candidates) == 1:
            review_rows.append(
                _identity_row(
                    "combine",
                    index,
                    "",
                    "REVIEW_ONLY_UNIQUE_DRAFT_SLOT_CANDIDATE",
                    row,
                    provider_authority="draft_year_round_pick",
                    provider_id="|".join(slot),
                )
            )
        elif len(slot_candidates) > 1:
            review_rows.append(
                _identity_row(
                    "combine",
                    index,
                    "",
                    "HUMAN_REVIEW_REQUIRED",
                    row,
                    provider_authority="ambiguous_draft_slot",
                    provider_id="|".join(slot),
                )
            )
        else:
            unresolved_rows.append(
                _identity_row("combine", index, "", "UNRESOLVED", row)
            )

    tables = IdentityTables(
        exact=_sorted_frame(
            exact_rows,
            ["source_dataset", "source_row"],
            empty_columns=IDENTITY_COLUMNS,
        ),
        review=_sorted_frame(
            review_rows,
            ["source_dataset", "source_row"],
            empty_columns=IDENTITY_COLUMNS,
        ),
        unresolved=_sorted_frame(
            unresolved_rows,
            ["source_dataset", "source_row"],
            empty_columns=IDENTITY_COLUMNS,
        ),
    )
    validate_identity_admission_rows(
        tables.exact,
        tables.review,
        tables.unresolved,
    )
    return tables


def _draft_slot(row: Mapping[str, Any]) -> tuple[str, str, str] | None:
    season = _value(row, ("season", "draft_year", "year"))
    round_value = _value(row, ("round", "draft_round"))
    pick = _value(row, ("pick", "draft_pick", "overall_pick"))
    if not season or not round_value or not pick:
        return None
    return season, round_value, pick


def _identity_row(
    source: str,
    index: int,
    gsis_id: str,
    classification: str,
    row: Mapping[str, Any],
    *,
    provider_authority: str = "",
    provider_id: str = "",
) -> dict[str, Any]:
    if classification not in IDENTITY_STATUSES:
        raise IdentityAdmissionError(f"unknown identity status: {classification}")
    return {
        "source_dataset": source,
        "source_row": int(index),
        "gsis_id": gsis_id,
        "identity_classification": classification,
        "provider_authority": provider_authority,
        "provider_id": provider_id,
        "player_name": _value(
            row,
            ("display_name", "player_name", "full_name", "pfr_player_name", "player"),
        ),
        "position": _value(row, ("position", "pos")),
        "draft_year": _value(row, ("draft_year", "season", "year")),
        "draft_round": _value(row, ("draft_round", "round")),
        "draft_pick": _value(row, ("draft_pick", "pick", "overall_pick")),
        "name_used_as_identity": "false",
    }


def validate_temporal_rows(rows: pd.DataFrame) -> None:
    required = {"feature_name", "available_after", "prediction_boundary"}
    if not required.issubset(rows.columns):
        raise TemporalLeakageError(f"temporal rows missing fields: {sorted(required - set(rows))}")
    for _, row in rows.iterrows():
        available = str(row["available_after"])
        boundary = str(row["prediction_boundary"])
        if not available or not boundary:
            raise TemporalLeakageError("blank temporal availability boundary")
        if available > boundary:
            raise TemporalLeakageError(
                f"future feature used: {row['feature_name']} {available}>{boundary}"
            )
        if str(row.get("present_day_snapshot_as_historical", "false")).lower() == "true":
            raise TemporalLeakageError("present-day field treated as historical")


def derive_nwr_points(frame: pd.DataFrame) -> pd.Series:
    def num(column: str) -> pd.Series:
        if column not in frame:
            return pd.Series(0.0, index=frame.index)
        return pd.to_numeric(frame[column], errors="coerce").fillna(0.0)

    points = (
        num("passing_yards") / 30.0
        + num("passing_tds") * 3.0
        - num("passing_interceptions")
        + num("rushing_yards") / 10.0
        + num("rushing_tds") * 4.0
        + num("receiving_yards") / 10.0
        + num("receiving_tds") * 4.0
        + (num("rushing_first_downs") + num("receiving_first_downs")) * 0.4
        + (num("punt_return_yards") + num("kickoff_return_yards")) / 30.0
        + num("special_teams_tds") * 4.0
        + (
            num("passing_2pt_conversions")
            + num("rushing_2pt_conversions")
            + num("receiving_2pt_conversions")
        )
        * 2.0
        - (
            num("sack_fumbles_lost")
            + num("rushing_fumbles_lost")
            + num("receiving_fumbles_lost")
        )
    )
    return points.round(6)


def add_realized_outcomes(stats: pd.DataFrame) -> pd.DataFrame:
    output = stats.copy()
    output["season"] = pd.to_numeric(output["season"], errors="coerce").astype("Int64")
    output["position"] = output["position"].astype(str).str.upper()
    output = output[output["position"].isin(CORE_POSITIONS)].copy()
    output["nwr_points"] = derive_nwr_points(output)
    output["games"] = pd.to_numeric(output.get("games", 0), errors="coerce").fillna(0)
    output["position_rank"] = output.groupby(["season", "position"])["nwr_points"].rank(
        method="min", ascending=False
    )
    replacement = []
    for (_season, position), group in output.groupby(["season", "position"]):
        rank = REPLACEMENT_RANK[position]
        ordered = group["nwr_points"].sort_values(ascending=False, kind="stable")
        value = float(ordered.iloc[min(rank - 1, len(ordered) - 1)]) if len(ordered) else 0.0
        replacement.extend((index, value) for index in group.index)
    replacement_series = pd.Series(
        {index: value for index, value in replacement}, dtype=float
    )
    output["replacement_points"] = replacement_series.reindex(output.index).fillna(0.0)
    output["nwr_value_over_replacement"] = (
        output["nwr_points"] - output["replacement_points"]
    ).round(6)
    output["top_position_outcome"] = [
        int(rank <= TOP_RANK[position])
        for rank, position in zip(output["position_rank"], output["position"], strict=True)
    ]
    output["above_replacement_outcome"] = (
        output["nwr_value_over_replacement"] > 0
    ).astype(int)
    return output


def validate_rookie_panel(
    frame: pd.DataFrame,
    *,
    expected_rookie_ids: Iterable[str] | None = None,
) -> None:
    required = {
        "gsis_id",
        "drafted_status",
        "combine_missing_indicator",
        "evidence_completeness",
    }
    if not required.issubset(frame.columns):
        raise PanelContractError(f"rookie panel missing fields: {sorted(required - set(frame))}")
    if frame["gsis_id"].map(normalized_id).eq("").any():
        raise IdentityAdmissionError("rookie panel admitted a blank GSIS ID")
    if expected_rookie_ids is not None:
        expected = {normalized_id(value) for value in expected_rookie_ids}
        actual = set(frame["gsis_id"].map(normalized_id))
        missing = sorted((expected - {""}) - actual)
        if missing:
            raise PanelContractError(
                f"rookie panel silently dropped governed players: {missing[:5]}"
            )
    if not frame["drafted_status"].isin({"DRAFTED", "UNDRAFTED"}).all():
        raise PanelContractError("rookie panel silently dropped/invalidated undrafted players")
    combine_columns = [
        column
        for column in ("forty", "vertical", "broad_jump", "cone", "shuttle", "bench")
        if column in frame
    ]
    for column in combine_columns:
        missing = frame["combine_missing_indicator"].astype(bool)
        coerced_zero = missing & pd.to_numeric(frame[column], errors="coerce").eq(0)
        if coerced_zero.any():
            raise PanelContractError("missing combine values converted to zero")
    if (frame["evidence_completeness"] == "FULL").any():
        full = frame["evidence_completeness"].eq("FULL")
        if frame.loc[full, "combine_missing_indicator"].astype(bool).any():
            raise PanelContractError("incomplete rookie treated as full evidence")
    forbidden = [column for column in frame if "adp" in column.lower()]
    if forbidden:
        raise PanelContractError(f"current ADP introduced: {forbidden}")


def validate_availability_panel(frame: pd.DataFrame) -> None:
    required = {
        "injury_record_state",
        "inactive_state",
        "games_played",
        "return_history_adequate",
        "injury_return_row",
    }
    if not required.issubset(frame.columns):
        raise PanelContractError(
            f"availability panel missing fields: {sorted(required - set(frame))}"
        )
    valid_injury_states = {
        "INJURY_RECORD_PRESENT",
        "NOT_ON_REPORT",
        "NO_INJURY_RECORD",
        "SOURCE_UNAVAILABLE",
    }
    if not frame["injury_record_state"].isin(valid_injury_states).all():
        raise PanelContractError("missing injury report treated as healthy")
    if (
        frame["injury_record_state"].eq("SOURCE_UNAVAILABLE")
        & frame["inactive_state"].eq("ACTIVE")
    ).any():
        raise PanelContractError("source-missing and active/healthy were conflated")
    games = pd.to_numeric(frame["games_played"], errors="coerce")
    if ((games > 0) & (games < 1)).any():
        raise PanelContractError("games fraction treated as binary probability")
    invalid_return = frame["injury_return_row"].astype(bool) & ~frame[
        "return_history_adequate"
    ].astype(bool)
    if invalid_return.any():
        raise PanelContractError("return-from-injury row created without history")


def walk_forward_evaluate(
    frame: pd.DataFrame,
    *,
    model_features: Mapping[str, Sequence[str]],
    season_column: str,
    continuous_target: str,
    binary_target: str,
    position_column: str = "position",
    slice_column: str | None = None,
) -> EvaluationResult:
    """Deterministic chronological ridge/logistic evaluation."""

    data = frame.copy()
    data[season_column] = pd.to_numeric(data[season_column], errors="coerce")
    data = data.dropna(subset=[season_column, continuous_target, binary_target]).copy()
    data[season_column] = data[season_column].astype(int)
    seasons = sorted(data[season_column].unique())
    prediction_rows: list[pd.DataFrame] = []
    metric_rows: list[dict[str, Any]] = []
    for model, features in model_features.items():
        if model.endswith("_BLOCKED"):
            metric_rows.append(
                {
                    "model": model.removesuffix("_BLOCKED"),
                    "slice": "ALL",
                    "folds": 0,
                    "rows": 0,
                    "spearman": "",
                    "rank_mae": "",
                    "brier": "",
                    "log_loss": "",
                    "ece": "",
                    "top_n_precision": "",
                    "top_n_recall": "",
                    "coverage": 0.0,
                    "status": "BLOCKED_MISSING_ADMITTED_FEATURE_FAMILY",
                }
            )
            continue
        fold_frames: list[pd.DataFrame] = []
        for test_season in seasons:
            prior = [season for season in seasons if season < test_season]
            if len(prior) < 3:
                continue
            train = data[data[season_column].isin(prior)].copy()
            test = data[data[season_column].eq(test_season)].copy()
            if train.empty or test.empty:
                continue
            x_train, x_test = _design_matrices(
                train,
                test,
                features=features,
                position_column=position_column,
            )
            y_train = pd.to_numeric(train[continuous_target], errors="coerce").to_numpy()
            y_binary = pd.to_numeric(train[binary_target], errors="coerce").to_numpy()
            regression = _ridge_predict(x_train, y_train, x_test)
            probability = _logistic_predict(x_train, y_binary, x_test)
            fold = test[
                [season_column, position_column, continuous_target, binary_target]
                + ([slice_column] if slice_column and slice_column in test else [])
            ].copy()
            fold["model"] = model
            fold["prediction"] = regression
            fold["probability"] = probability
            fold["test_season"] = test_season
            fold_frames.append(fold)
        if fold_frames:
            predictions = pd.concat(fold_frames, ignore_index=True)
            prediction_rows.append(predictions)
            metric_rows.extend(
                _metric_rows(
                    predictions,
                    model=model,
                    continuous_target=continuous_target,
                    binary_target=binary_target,
                    season_column=season_column,
                    position_column=position_column,
                    slice_column=slice_column,
                    eligible_rows=len(data),
                )
            )
        else:
            metric_rows.append(
                {
                    "model": model,
                    "slice": "ALL",
                    "folds": 0,
                    "rows": 0,
                    "spearman": "",
                    "rank_mae": "",
                    "brier": "",
                    "log_loss": "",
                    "ece": "",
                    "top_n_precision": "",
                    "top_n_recall": "",
                    "coverage": 0.0,
                    "status": "NOT_ENOUGH_INFORMATION",
                }
            )
    predictions = (
        pd.concat(prediction_rows, ignore_index=True)
        if prediction_rows
        else pd.DataFrame()
    )
    return EvaluationResult(
        predictions=predictions,
        metrics=_sorted_frame(metric_rows, ["model", "slice"]),
    )


def _design_matrices(
    train: pd.DataFrame,
    test: pd.DataFrame,
    *,
    features: Sequence[str],
    position_column: str,
) -> tuple[np.ndarray, np.ndarray]:
    numeric_features = [feature for feature in features if feature != position_column]
    train_columns: list[np.ndarray] = [np.ones(len(train))]
    test_columns: list[np.ndarray] = [np.ones(len(test))]
    for feature in numeric_features:
        train_values = pd.to_numeric(train.get(feature, np.nan), errors="coerce")
        test_values = pd.to_numeric(test.get(feature, np.nan), errors="coerce")
        median = float(train_values.median()) if train_values.notna().any() else 0.0
        train_missing = train_values.isna().astype(float).to_numpy()
        test_missing = test_values.isna().astype(float).to_numpy()
        train_filled = train_values.fillna(median).to_numpy(dtype=float)
        test_filled = test_values.fillna(median).to_numpy(dtype=float)
        mean = float(np.mean(train_filled))
        std = float(np.std(train_filled))
        if std <= 1e-12:
            std = 1.0
        train_columns.extend(((train_filled - mean) / std, train_missing))
        test_columns.extend(((test_filled - mean) / std, test_missing))
    if position_column in features:
        train_position = train[position_column].astype(str)
        test_position = test[position_column].astype(str)
        for position in CORE_POSITIONS:
            train_columns.append(train_position.eq(position).astype(float).to_numpy())
            test_columns.append(test_position.eq(position).astype(float).to_numpy())
    return np.column_stack(train_columns), np.column_stack(test_columns)


def _ridge_predict(
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_test: np.ndarray,
) -> np.ndarray:
    penalty = np.eye(x_train.shape[1]) * 1.0
    penalty[0, 0] = 0.0
    beta = np.linalg.pinv(x_train.T @ x_train + penalty) @ x_train.T @ y_train
    return x_test @ beta


def _logistic_predict(
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_test: np.ndarray,
) -> np.ndarray:
    if len(np.unique(y_train)) < 2:
        return np.full(len(x_test), float(np.mean(y_train)))
    beta = np.zeros(x_train.shape[1], dtype=float)
    for _ in range(400):
        probabilities = 1.0 / (1.0 + np.exp(-np.clip(x_train @ beta, -30, 30)))
        gradient = x_train.T @ (probabilities - y_train) / len(y_train)
        gradient[1:] += 0.01 * beta[1:]
        beta -= 0.1 * gradient
    return 1.0 / (1.0 + np.exp(-np.clip(x_test @ beta, -30, 30)))


def _metric_rows(
    predictions: pd.DataFrame,
    *,
    model: str,
    continuous_target: str,
    binary_target: str,
    season_column: str,
    position_column: str,
    slice_column: str | None,
    eligible_rows: int,
) -> list[dict[str, Any]]:
    slices: list[tuple[str, pd.DataFrame]] = [("ALL", predictions)]
    for value, group in predictions.groupby(position_column, dropna=False):
        slices.append((f"{position_column}={value}", group))
    for value, group in predictions.groupby(season_column, dropna=False):
        slices.append((f"{season_column}={value}", group))
    if slice_column and slice_column in predictions:
        for value, group in predictions.groupby(slice_column, dropna=False):
            slices.append((f"{slice_column}={value}", group))
    rows: list[dict[str, Any]] = []
    for slice_name, frame in slices:
        actual = pd.to_numeric(frame[continuous_target], errors="coerce")
        pred = pd.to_numeric(frame["prediction"], errors="coerce")
        binary = pd.to_numeric(frame[binary_target], errors="coerce").astype(int)
        probability = pd.to_numeric(frame["probability"], errors="coerce").clip(1e-6, 1 - 1e-6)
        spearman = actual.rank().corr(pred.rank(), method="pearson")
        actual_rank = frame.groupby([season_column, position_column])[continuous_target].rank(
            method="average", ascending=False
        )
        predicted_rank = frame.groupby([season_column, position_column])["prediction"].rank(
            method="average", ascending=False
        )
        predicted_binary = probability.ge(0.5).astype(int)
        true_positive = int(((predicted_binary == 1) & (binary == 1)).sum())
        predicted_positive = int((predicted_binary == 1).sum())
        actual_positive = int((binary == 1).sum())
        rows.append(
            {
                "model": model,
                "slice": slice_name,
                "folds": int(frame["test_season"].nunique()),
                "rows": int(len(frame)),
                "spearman": _round(spearman),
                "rank_mae": _round((actual_rank - predicted_rank).abs().mean()),
                "brier": _round(np.mean((probability - binary) ** 2)),
                "log_loss": _round(
                    -np.mean(
                        binary * np.log(probability)
                        + (1 - binary) * np.log(1 - probability)
                    )
                ),
                "ece": _round(_ece(binary.to_numpy(), probability.to_numpy())),
                "top_n_precision": _round(
                    true_positive / predicted_positive if predicted_positive else 0.0
                ),
                "top_n_recall": _round(
                    true_positive / actual_positive if actual_positive else 0.0
                ),
                "coverage": _round(len(frame) / eligible_rows if eligible_rows else 0.0),
                "status": "EVALUATED_CHRONOLOGICAL_WALK_FORWARD",
            }
        )
    return rows


def _ece(actual: np.ndarray, probability: np.ndarray) -> float:
    total = len(actual)
    if not total:
        return math.nan
    value = 0.0
    for lower in np.linspace(0.0, 0.9, 10):
        upper = lower + 0.1
        mask = (probability >= lower) & (
            probability <= upper if upper >= 1.0 else probability < upper
        )
        if mask.any():
            value += float(mask.mean()) * abs(
                float(actual[mask].mean()) - float(probability[mask].mean())
            )
    return value


def _round(value: Any) -> float | str:
    try:
        number = float(value)
        return round(number, 6) if math.isfinite(number) else ""
    except (TypeError, ValueError):
        return ""


MUTATION_CASES = (
    "wrong_release_asset",
    "modified_raw_bytes",
    "changed_schema",
    "missing_license_receipt",
    "missing_source_url",
    "mutable_snapshot",
    "secret_written_to_logs",
    "request_limit_exceeded",
    "name_only_join",
    "duplicate_gsis_id",
    "blank_gsis_id",
    "ambiguous_draft_slot_mapping",
    "swapped_same_position_players",
    "unresolved_cfbd_player_admitted",
    "post_draft_data_used_before_draft",
    "season_end_college_data_used_early",
    "future_nfl_snaps",
    "future_depth_chart",
    "future_injury_report",
    "present_day_field_treated_as_historical",
    "undrafted_player_dropped",
    "missing_combine_values_converted_to_zero",
    "current_adp_introduced",
    "incomplete_rookie_treated_as_full_evidence",
    "missing_injury_report_treated_as_healthy",
    "games_fraction_treated_as_binary_probability",
    "inactive_and_source_missing_conflated",
    "return_from_injury_without_history",
)


def exercise_mutation(case: str) -> str:
    """Exercise each required mutation through its owning contract path."""

    if case not in MUTATION_CASES:
        raise ValueError(f"unknown mutation: {case}")
    try:
        if case in {
            "wrong_release_asset",
            "modified_raw_bytes",
            "changed_schema",
            "missing_license_receipt",
            "missing_source_url",
            "mutable_snapshot",
        }:
            _exercise_source_mutation(case)
        elif case == "secret_written_to_logs":
            require_no_secret("Authorization: Bearer synthetic-secret-value")
        elif case == "request_limit_exceeded":
            enforce_request_limit(161, 160)
        elif case in {
            "name_only_join",
            "duplicate_gsis_id",
            "blank_gsis_id",
            "ambiguous_draft_slot_mapping",
            "swapped_same_position_players",
            "unresolved_cfbd_player_admitted",
        }:
            _exercise_identity_mutation(case)
        elif case in {
            "post_draft_data_used_before_draft",
            "season_end_college_data_used_early",
            "future_nfl_snaps",
            "future_depth_chart",
            "future_injury_report",
            "present_day_field_treated_as_historical",
        }:
            available = "2024-09-10"
            boundary = "2024-09-01"
            present = case == "present_day_field_treated_as_historical"
            validate_temporal_rows(
                pd.DataFrame(
                    [
                        {
                            "feature_name": case,
                            "available_after": available,
                            "prediction_boundary": boundary,
                            "present_day_snapshot_as_historical": str(present).lower(),
                        }
                    ]
                )
            )
        elif case in {
            "undrafted_player_dropped",
            "missing_combine_values_converted_to_zero",
            "current_adp_introduced",
            "incomplete_rookie_treated_as_full_evidence",
        }:
            _exercise_rookie_mutation(case)
        else:
            _exercise_availability_mutation(case)
    except FoundationContractError as exc:
        return type(exc).__name__
    raise AssertionError(f"mutation did not fail closed: {case}")


def _exercise_source_mutation(case: str) -> None:
    if case == "wrong_release_asset":
        require_official_url("https://github.com/not-nflverse/data/releases/download/x.csv")
        return
    if case == "modified_raw_bytes":
        validate_expected_digest("mutated", "admitted", label="snapshot asset")
        return
    if case == "changed_schema":
        validate_schema_record(
            actual_schema=[{"name": "gsis_id", "dtype": "Int64"}],
            expected_schema=[{"name": "gsis_id", "dtype": "String"}],
            actual_rows=1,
            expected_rows=1,
        )
        return

    asset = {
        "status": "downloaded",
        "source_url": (
            "https://github.com/nflverse/nflverse-data/releases/download/"
            "players/players.parquet"
        ),
        "final_url": (
            "https://release-assets.githubusercontent.com/"
            "official-nflverse-asset"
        ),
        "sha256": "a" * 64,
    }
    manifest: dict[str, Any] = {
        "schema_version": 1,
        "provider": "nflverse",
        "dataset": "players",
        "snapshot_id": "synthetic",
        "retrieved_at_utc": "2026-07-30T00:00:00Z",
        "package_name": "nflreadpy",
        "package_version": NFLREADPY_VERSION,
        "source_release": "players",
        "license_spdx": "CC-BY-4.0",
        "license_url": "https://github.com/nflverse/nflverse-data/blob/master/LICENSE.md",
        "immutable": True,
        "complete": True,
        "aggregate_sha256": sha256_bytes(("a" * 64).encode("ascii")),
        "assets": [asset],
    }
    if case == "missing_license_receipt":
        manifest["license_url"] = ""
    elif case == "missing_source_url":
        asset["source_url"] = ""
    elif case == "mutable_snapshot":
        manifest["immutable"] = False
    validate_snapshot_metadata(manifest)


def _exercise_identity_mutation(case: str) -> None:
    if case == "duplicate_gsis_id":
        validate_gsis_ids(pd.DataFrame({"gsis_id": ["00-1", "00-1"]}))
        return

    exact = pd.DataFrame(
        [
            _identity_row(
                "players",
                0,
                "00-1",
                "EXACT_SHARED_GSIS_ID",
                {"display_name": "Synthetic A", "position": "WR"},
                provider_authority="gsis_id",
                provider_id="00-1",
            )
        ],
        columns=IDENTITY_COLUMNS,
    )
    review = pd.DataFrame(columns=IDENTITY_COLUMNS)
    unresolved = pd.DataFrame(columns=IDENTITY_COLUMNS)
    if case == "blank_gsis_id":
        exact.loc[0, "gsis_id"] = ""
    elif case == "name_only_join":
        exact.loc[0, "name_used_as_identity"] = "true"
    elif case in {"ambiguous_draft_slot_mapping", "swapped_same_position_players"}:
        exact = pd.concat(
            [
                exact,
                pd.DataFrame(
                    [
                        _identity_row(
                            "combine",
                            1,
                            "00-2",
                            "EXACT_SHARED_PROVIDER_ID",
                            {"display_name": "Synthetic B", "position": "WR"},
                            provider_authority=(
                                "draft_year_round_pick"
                                if case == "ambiguous_draft_slot_mapping"
                                else "pfr_id"
                            ),
                            provider_id=(
                                "2024|1|10"
                                if case == "ambiguous_draft_slot_mapping"
                                else "Shared00"
                            ),
                        )
                    ],
                    columns=IDENTITY_COLUMNS,
                ),
            ],
            ignore_index=True,
        )
        exact.loc[0, "provider_authority"] = exact.loc[1, "provider_authority"]
        exact.loc[0, "provider_id"] = exact.loc[1, "provider_id"]
    elif case == "unresolved_cfbd_player_admitted":
        exact.loc[0, "source_dataset"] = "cfbd_player_season"
        exact.loc[0, "identity_classification"] = "UNRESOLVED"
        exact.loc[0, "gsis_id"] = ""
    validate_identity_admission_rows(exact, review, unresolved)


def _exercise_rookie_mutation(case: str) -> None:
    frame = pd.DataFrame(
        [
            {
                "gsis_id": "00-1",
                "drafted_status": "DRAFTED",
                "combine_missing_indicator": False,
                "evidence_completeness": "PARTIAL",
                "forty": 4.5,
            }
        ]
    )
    if case == "undrafted_player_dropped":
        validate_rookie_panel(
            frame,
            expected_rookie_ids={"00-1", "00-2"},
        )
        return
    elif case == "missing_combine_values_converted_to_zero":
        frame.loc[0, "combine_missing_indicator"] = True
        frame.loc[0, "forty"] = 0
    elif case == "current_adp_introduced":
        frame["current_adp"] = 1
    elif case == "incomplete_rookie_treated_as_full_evidence":
        frame.loc[0, "combine_missing_indicator"] = True
        frame.loc[0, "forty"] = np.nan
        frame.loc[0, "evidence_completeness"] = "FULL"
    validate_rookie_panel(frame, expected_rookie_ids={"00-1"})


def _exercise_availability_mutation(case: str) -> None:
    frame = pd.DataFrame(
        [
            {
                "injury_record_state": "NO_INJURY_RECORD",
                "inactive_state": "NOT_INACTIVE",
                "games_played": 8.0,
                "return_history_adequate": True,
                "injury_return_row": False,
            }
        ]
    )
    if case == "missing_injury_report_treated_as_healthy":
        frame.loc[0, "injury_record_state"] = "HEALTHY"
    elif case == "games_fraction_treated_as_binary_probability":
        frame.loc[0, "games_played"] = 0.5
    elif case == "inactive_and_source_missing_conflated":
        frame.loc[0, "injury_record_state"] = "SOURCE_UNAVAILABLE"
        frame.loc[0, "inactive_state"] = "ACTIVE"
    elif case == "return_from_injury_without_history":
        frame.loc[0, "return_history_adequate"] = False
        frame.loc[0, "injury_return_row"] = True
    validate_availability_panel(frame)


def _sorted_frame(
    rows: list[dict[str, Any]],
    columns: Sequence[str],
    *,
    empty_columns: Sequence[str] = (),
) -> pd.DataFrame:
    frame = pd.DataFrame(rows)
    if frame.empty:
        return pd.DataFrame(columns=list(empty_columns))
    available = [column for column in columns if column in frame]
    return frame.sort_values(available, kind="stable").reset_index(drop=True)
