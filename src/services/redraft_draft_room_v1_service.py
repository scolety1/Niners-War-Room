"""Deterministic Redraft Draft Room, owner ADP boundary, and mock behavior.

NWR rankings remain the player-value authority. ADP is optional market-timing
context. CPU selections use admitted ADP when present and otherwise disclose a
deterministic NWR-order fallback. Sleeper events are accepted read-only; this
module contains no platform write client.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import re
import unicodedata
import urllib.error
import urllib.request
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

from src.services.redraft_engine_v1_service import (
    LeagueProfile,
    RankingResult,
    RedraftPersistenceError,
    RedraftValidationError,
    load_draft_board,
    utc_now,
)

ROOM_SCHEMA_VERSION = 1
ADP_SCHEMA_VERSION = 2
FFC_PROVIDER_VERSION = "NWR_FFC_ADP_PROVIDER_V1"
FFC_SOURCE = "Fantasy Football Calculator ADP"
FFC_AUTHORITY = "EXTERNAL ADP / MARKET TIMING"
FFC_ATTRIBUTION_URL = "https://fantasyfootballcalculator.com/adp"
FFC_API_BASE = "https://fantasyfootballcalculator.com/api/v1/adp"
DEFAULT_SEED = 20260817
SUPPORTED_SPEEDS = frozenset({"FAST", "NORMAL", "STEP"})
SUPPORTED_MODES = frozenset({"MOCK", "LIVE_READ_ONLY"})
ADP_REQUIRED_COLUMNS = frozenset(
    {"player", "position", "source", "scoring_format", "team_count", "date"}
)
ADP_OPTIONAL_COLUMNS = frozenset(
    {
        "player_id",
        "team",
        "overall_adp",
        "expected_pick",
        "min_pick",
        "max_pick",
        "std_dev",
    }
)
ADP_COLUMN_ALIASES = {
    "adp": "overall_adp",
    "rank": "overall_adp",
    "format": "scoring_format",
    "player_name": "player",
    "nfl_team": "team",
}
PASTE_PLATFORM_COLUMNS = frozenset({"CONSENSUS", "SLEEPER", "ESPN", "FANTASYPROS"})
OWNER_PLATFORM_SELECTIONS = frozenset({"AUTO", "CONSENSUS", "SLEEPER", "ESPN", "FANTASYPROS", "DISABLED"})
PASTE_COLUMN_ALIASES = {
    "cons": "CONSENSUS", "consensus": "CONSENSUS",
    "sleeper": "SLEEPER", "espn": "ESPN",
    "fpros": "FANTASYPROS", "fantasypros": "FANTASYPROS", "fantasy pros": "FANTASYPROS",
}


@dataclass(frozen=True)
class AdpEntry:
    player_id: str
    player: str
    team: str
    position: str
    overall_adp: float
    expected_pick: float
    min_pick: float | None
    max_pick: float | None
    std_dev: float | None
    source_player_id: str = ""
    expected_round: int | None = None
    match_status: str = "MATCHED"
    match_confidence: str = "HIGH"
    unmatched_reason: str = ""


@dataclass(frozen=True)
class AdpSnapshot:
    profile_id: str
    source: str
    scoring_format: str
    team_count: int
    source_date: str
    imported_at_utc: str
    source_sha256: str
    entries: tuple[AdpEntry, ...]
    unmatched: tuple[str, ...]
    errors: tuple[str, ...] = ()
    provider: str = "OWNER_IMPORT"
    authority: str = "EXTERNAL ADP / MARKET TIMING"
    position_filter: str = "ALL"
    sample_size: int | None = None
    date_window: str = ""
    retrieved_at_utc: str = ""
    provider_version: str = ""
    endpoint: str = ""
    freshness: str = "UNAVAILABLE"
    last_refresh_error: str = ""
    match_report: tuple[dict[str, Any], ...] = ()
    paste_rows: tuple[dict[str, Any], ...] = ()

    @property
    def available(self) -> bool:
        return bool(self.entries) and not self.errors

    @property
    def by_player_id(self) -> dict[str, AdpEntry]:
        return {entry.player_id: entry for entry in self.entries}


def adp_import_template() -> str:
    columns = [
        "player_id",
        "player",
        "team",
        "position",
        "overall_adp",
        "expected_pick",
        "min_pick",
        "max_pick",
        "std_dev",
        "source",
        "scoring_format",
        "team_count",
        "date",
    ]
    return ",".join(columns) + "\n"


def import_owner_adp_csv(
    root: str | Path,
    profile: LeagueProfile,
    ranking: RankingResult,
    csv_text: str,
    manual_assets: Sequence[Mapping[str, Any]] = (),
) -> AdpSnapshot:
    if not csv_text.strip() or len(csv_text.encode("utf-8")) > 2_000_000:
        raise RedraftValidationError("ADP CSV must be non-empty and no larger than 2 MB.")
    try:
        reader = csv.DictReader(io.StringIO(csv_text.lstrip("\ufeff")))
    except csv.Error as exc:
        raise RedraftValidationError("ADP CSV could not be parsed.") from exc
    original_fields = [str(value or "").strip() for value in (reader.fieldnames or [])]
    normalized_fields = [
        ADP_COLUMN_ALIASES.get(value.lower(), value.lower()) for value in original_fields
    ]
    if len(normalized_fields) != len(set(normalized_fields)):
        raise RedraftValidationError("ADP CSV has duplicate or conflicting columns.")
    fields = set(normalized_fields)
    missing = sorted(ADP_REQUIRED_COLUMNS - fields)
    unknown = sorted(fields - ADP_REQUIRED_COLUMNS - ADP_OPTIONAL_COLUMNS)
    if missing:
        raise RedraftValidationError("ADP CSV is missing columns: " + ", ".join(missing))
    if unknown:
        raise RedraftValidationError("ADP CSV has unsupported columns: " + ", ".join(unknown))
    if "overall_adp" not in fields and "expected_pick" not in fields:
        raise RedraftValidationError("ADP CSV requires adp, rank, overall_adp, or expected_pick.")

    assets = _matching_assets(ranking, manual_assets)
    assets_by_id = {str(row["player_id"]): row for row in assets}

    entries: list[AdpEntry] = []
    unmatched: list[str] = []
    sources: set[str] = set()
    scoring_formats: set[str] = set()
    source_dates: set[str] = set()
    seen_ids: set[str] = set()
    match_report: list[dict[str, Any]] = []
    for line_number, source_row in enumerate(reader, start=2):
        row = {
            ADP_COLUMN_ALIASES.get(str(key).strip().lower(), str(key).strip().lower()):
            str(value or "").strip()
            for key, value in source_row.items()
        }
        player = row["player"]
        position = _normalized_position(row["position"])
        if not player or position not in {"QB", "RB", "WR", "TE", "K", "DST"}:
            unmatched.append(f"line {line_number}: {player or 'missing player'}")
            continue
        try:
            team_count = int(row["team_count"])
        except ValueError as exc:
            raise RedraftValidationError(f"ADP line {line_number} team_count is invalid.") from exc
        if team_count != profile.team_count:
            raise RedraftValidationError(
                f"ADP line {line_number} is for {team_count} teams; active league uses "
                f"{profile.team_count}."
            )
        scoring = _normalized_scoring(row["scoring_format"])
        if scoring != _profile_scoring(profile):
            raise RedraftValidationError(
                f"ADP line {line_number} scoring format does not match the active league."
            )
        try:
            source_date = date.fromisoformat(row["date"])
        except ValueError as exc:
            raise RedraftValidationError(
                f"ADP line {line_number} date must be YYYY-MM-DD."
            ) from exc
        if source_date > datetime.now(UTC).date():
            raise RedraftValidationError(f"ADP line {line_number} date is in the future.")
        source_name = row["source"]
        if not source_name:
            raise RedraftValidationError(f"ADP line {line_number} source is required.")
        overall_value = row.get("overall_adp") or row.get("expected_pick") or ""
        overall = _positive_float(overall_value, line_number, "overall_adp")
        expected = (
            _positive_float(row["expected_pick"], line_number, "expected_pick")
            if row.get("expected_pick")
            else overall
        )
        minimum = _optional_positive_float(row.get("min_pick", ""), line_number, "min_pick")
        maximum = _optional_positive_float(row.get("max_pick", ""), line_number, "max_pick")
        std_dev = _optional_positive_float(row.get("std_dev", ""), line_number, "std_dev")
        if minimum is not None and maximum is not None and minimum > maximum:
            raise RedraftValidationError(f"ADP line {line_number} min_pick exceeds max_pick.")
        if minimum is not None and expected < minimum:
            raise RedraftValidationError(f"ADP line {line_number} expected_pick is below min_pick.")
        if maximum is not None and expected > maximum:
            raise RedraftValidationError(f"ADP line {line_number} expected_pick exceeds max_pick.")

        requested_id = row.get("player_id", "")
        matched = assets_by_id.get(requested_id) if requested_id else None
        match_method = "EXACT_NWR_ID" if matched is not None else ""
        confidence = "HIGH" if matched is not None else ""
        reason = ""
        if matched is None:
            matched, match_method, confidence, reason = _match_adp_player(
                player, position, row.get("team", ""), assets
            )
        if matched is None:
            unmatched.append(f"line {line_number}: {player} ({position})")
            match_report.append(_match_report_row(
                requested_id, player, position, row.get("team", ""), None,
                "UNMATCHED", "", reason or "NO_SAFE_IDENTITY_MATCH",
            ))
            continue
        matched_id = str(matched["player_id"])
        if matched_id in seen_ids:
            raise RedraftValidationError(
                f"ADP line {line_number} duplicates {matched['player_name']}."
            )
        seen_ids.add(matched_id)
        sources.add(source_name)
        scoring_formats.add(scoring)
        source_dates.add(source_date.isoformat())
        entries.append(
            AdpEntry(
                player_id=matched_id,
                player=str(matched["player_name"]),
                team=str(matched["team"]),
                position=str(matched["position"]),
                overall_adp=round(overall, 2),
                expected_pick=round(expected, 2),
                min_pick=round(minimum, 2) if minimum is not None else None,
                max_pick=round(maximum, 2) if maximum is not None else None,
                std_dev=round(std_dev, 2) if std_dev is not None else None,
                source_player_id=requested_id,
                expected_round=max(1, math.ceil(expected / profile.team_count)),
                match_status="MATCHED",
                match_confidence=confidence,
            )
        )
        match_report.append(_match_report_row(
            requested_id, player, position, row.get("team", ""), matched,
            match_method, confidence, "",
        ))
    if not entries:
        raise RedraftValidationError("ADP CSV did not match any governed Redraft player IDs.")
    if len(sources) != 1 or len(scoring_formats) != 1 or len(source_dates) != 1:
        raise RedraftValidationError(
            "ADP CSV must contain one source, scoring format, and source date per snapshot."
        )
    entries.sort(key=lambda entry: (entry.expected_pick, entry.player_id))
    raw_source = next(iter(sources))
    sleeper_owner_import = "sleeper" in raw_source.lower()
    snapshot = AdpSnapshot(
        profile_id=profile.profile_id,
        source="Owner-imported Sleeper ADP" if sleeper_owner_import else raw_source,
        scoring_format=next(iter(scoring_formats)),
        team_count=profile.team_count,
        source_date=next(iter(source_dates)),
        imported_at_utc=utc_now(),
        source_sha256=hashlib.sha256(csv_text.encode("utf-8")).hexdigest(),
        entries=tuple(entries),
        unmatched=tuple(unmatched),
        provider="OWNER_SLEEPER_CSV" if sleeper_owner_import else "OWNER_IMPORT",
        authority=FFC_AUTHORITY,
        retrieved_at_utc=utc_now(),
        provider_version="OWNER_ADP_CSV_V1",
        freshness="FRESH",
        match_report=tuple(match_report),
    )
    _atomic_json(_adp_path(root, profile.profile_id), _adp_document(snapshot))
    return snapshot


def preview_owner_paste_adp(
    profile: LeagueProfile,
    ranking: RankingResult,
    paste_text: str,
    selected_source: str,
    manual_assets: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    """Parse a stable owner-supplied markdown table without changing any state."""
    if not paste_text.strip() or len(paste_text.encode("utf-8")) > 2_000_000:
        raise RedraftValidationError("Pasted rankings must be non-empty and no larger than 2 MB.")
    selected = _paste_selected_source(selected_source)
    rows, parser_mode, parser_warnings = _owner_platform_rows(paste_text)
    if not rows:
        raise RedraftValidationError(
            "Paste a markdown pipe table, or plain-text blocks such as `WR13`, player name, "
            "then `Consensus Sleeper ESPN FantasyPros` numbers. No local state was changed."
        )
    assets = _matching_assets(ranking, manual_assets)
    parsed_rows: list[dict[str, Any]] = []
    entries: list[AdpEntry] = []
    unmatched: list[str] = []
    warnings: list[str] = list(parser_warnings)
    report: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for source_index, row in enumerate(rows, start=1):
        position_rank, position = _paste_position(row.get("position", ""))
        player = str(row.get("player") or "").strip()
        selected_value = _paste_number(row.get(selected.lower(), ""))
        raw_row = "|".join(str(row.get(key, "")) for key in ("position", "player", "consensus", "sleeper", "espn", "fantasypros"))
        receipt = {
            "source_row_index": source_index,
            "position_rank": position_rank,
            "position": position,
            "positional_adp_rank": position_rank,
            "player_name": player,
            "consensus_adp": _paste_number(row.get("consensus", "")),
            "sleeper_adp": _paste_number(row.get("sleeper", "")),
            "espn_adp": _paste_number(row.get("espn", "")),
            "fantasypros_adp": _paste_number(row.get("fantasypros", "")),
            "selected_adp": selected_value,
            "selected_source": selected,
            "imported_at": "",
            "import_source_label": "",
            "raw_row_hash": hashlib.sha256(raw_row.encode("utf-8")).hexdigest(),
        }
        if not player or position not in {"QB", "RB", "WR", "TE", "K", "DST"}:
            warnings.append(f"row {source_index}: missing or unsupported player identity")
            unmatched.append(f"row {source_index}: {player or 'missing player'}")
            receipt["match_status"] = "INVALID"
            parsed_rows.append(receipt)
            continue
        match_value = selected_value
        if match_value is None:
            for fallback in ("consensus", "sleeper", "espn", "fantasypros"):
                match_value = _paste_number(row.get(fallback, ""))
                if match_value is not None:
                    warnings.append(
                        f"row {source_index}: {player} has no usable {selected.title()} ADP; "
                        "it remains available through its populated platform column."
                    )
                    break
        if match_value is None:
            warnings.append(f"row {source_index}: {player} has no usable platform ADP")
            receipt["match_status"] = "SKIPPED_NO_PLATFORM_ADP"
            parsed_rows.append(receipt)
            continue
        matched, method, confidence, reason = _match_adp_player(player, position, "", assets)
        if matched is None:
            unmatched.append(f"row {source_index}: {player} ({position})")
            warnings.append(f"row {source_index}: {player} not safely matched ({reason})")
            receipt["match_status"] = "UNMATCHED"
            receipt["unmatched_reason"] = reason or "NO_SAFE_IDENTITY_MATCH"
            parsed_rows.append(receipt)
            report.append(_match_report_row("", player, position, "", None, "UNMATCHED", "", reason or "NO_SAFE_IDENTITY_MATCH"))
            continue
        matched_id = str(matched["player_id"])
        if matched_id in seen_ids:
            warnings.append(f"row {source_index}: duplicate safe match for {matched['player_name']}")
            receipt["match_status"] = "DUPLICATE_MATCH"
            parsed_rows.append(receipt)
            continue
        seen_ids.add(matched_id)
        receipt.update({"match_status": "MATCHED", "matched_nwr_player_id": matched_id, "matched_nwr_player_name": str(matched["player_name"]), "matched_nwr_team": str(matched["team"]), "match_method": method, "match_confidence": confidence})
        parsed_rows.append(receipt)
        entries.append(AdpEntry(player_id=matched_id, player=str(matched["player_name"]), team=str(matched["team"]), position=str(matched["position"]), overall_adp=match_value, expected_pick=match_value, min_pick=None, max_pick=None, std_dev=None, source_player_id=f"paste:{source_index}", expected_round=max(1, math.ceil(match_value / profile.team_count)), match_status="MATCHED", match_confidence=confidence))
        report.append(_match_report_row("", player, position, "", matched, method, confidence, ""))
    if not entries:
        raise RedraftValidationError("The pasted table did not safely match any NWR Draft Room players.")
    return {"selectedSource": selected, "parserMode": parser_mode, "platformCoverage": _platform_coverage(parsed_rows), "parsedRows": parsed_rows, "entries": entries, "unmatched": unmatched, "warnings": warnings, "matchReport": report, "sourceRows": len(rows), "matchedRows": len(entries), "skippedRows": len(rows) - len(entries)}


def save_owner_paste_adp(
    root: str | Path,
    profile: LeagueProfile,
    ranking: RankingResult,
    paste_text: str,
    selected_source: str,
    source_label: str,
    manual_assets: Sequence[Mapping[str, Any]] = (),
    *,
    activate: bool = False,
) -> AdpSnapshot:
    preview = preview_owner_paste_adp(profile, ranking, paste_text, selected_source, manual_assets)
    selected = str(preview["selectedSource"])
    imported = utc_now()
    label = source_label.strip()
    canonical_source = f"Owner-imported {selected.title()} ADP"
    source = canonical_source if not label else f"{canonical_source} — {label}"
    rows = [{**row, "imported_at": imported, "import_source_label": source} for row in preview["parsedRows"]]
    snapshot = AdpSnapshot(profile_id=profile.profile_id, source=source, scoring_format=_profile_scoring(profile), team_count=profile.team_count, source_date=datetime.now(UTC).date().isoformat(), imported_at_utc=imported, source_sha256=hashlib.sha256(paste_text.encode("utf-8")).hexdigest(), entries=tuple(sorted(preview["entries"], key=lambda entry: (entry.expected_pick, entry.player_id))), unmatched=tuple(preview["unmatched"]), provider=f"OWNER_PASTE_{selected}", authority="OWNER-IMPORTED PLATFORM ADP / MARKET TIMING", retrieved_at_utc=imported, provider_version="NWR_OWNER_PASTE_ADP_V1", freshness="FRESH", match_report=tuple(preview["matchReport"]), paste_rows=tuple(rows))
    _save_owner_platform_snapshot(
        root, profile, snapshot, rows, paste_text,
        source_label=label or "Owner platform rankings",
        parser_mode=str(preview["parserMode"]),
        platform_coverage=dict(preview["platformCoverage"]),
        active=True,
    )
    return snapshot


def set_owner_paste_adp_active(root: str | Path, profile: LeagueProfile, *, active: bool) -> None:
    if _owner_platform_snapshot_path(root).is_file():
        selection = _owner_platform_selection(root, profile)[0]
        _atomic_json(_owner_platform_selection_path(root, profile.profile_id), {
            "profile_id": profile.profile_id,
            "selection": selection if active else "DISABLED",
            "updated_at_utc": utc_now(),
        })
        return
    path = _owner_paste_adp_path(root, profile.profile_id)
    if not path.is_file():
        raise RedraftValidationError("Save a pasted platform ADP snapshot before activating it.")
    document = json.loads(path.read_text(encoding="utf-8"))
    document["active"] = active
    _atomic_json(path, document)


def load_adp_snapshot(root: str | Path, profile: LeagueProfile) -> AdpSnapshot:
    has_global_snapshot = _owner_platform_snapshot_path(root).is_file()
    global_snapshot = _load_owner_platform_snapshot(root, profile)
    if global_snapshot is not None:
        ffc_path = _ffc_adp_path(root, profile.profile_id)
        if ffc_path.is_file():
            try:
                return _merge_owner_platform_fallback(global_snapshot, _read_adp_snapshot(ffc_path, profile))
            except RedraftPersistenceError:
                pass
        return global_snapshot
    owner_path = _adp_path(root, profile.profile_id)
    ffc_path = _ffc_adp_path(root, profile.profile_id)
    paste_path = _owner_paste_adp_path(root, profile.profile_id)
    paste_active = False
    if paste_path.is_file():
        try:
            paste_active = bool(json.loads(paste_path.read_text(encoding="utf-8")).get("active"))
        except (OSError, ValueError, json.JSONDecodeError):
            paste_active = False
    # Once a global snapshot exists, Disabled/use FFC must not be shadowed by an
    # older profile-scoped owner paste cache from the pre-snapshot implementation.
    path = (
        ffc_path if has_global_snapshot and ffc_path.is_file()
        else owner_path if has_global_snapshot
        else paste_path if paste_active
        else ffc_path if ffc_path.is_file()
        else owner_path
    )
    if not path.is_file():
        return AdpSnapshot(
            profile_id=profile.profile_id,
            source="",
            scoring_format=_profile_scoring(profile),
            team_count=profile.team_count,
            source_date="",
            imported_at_utc="",
            source_sha256="",
            entries=(),
            unmatched=(),
        )
    return _read_adp_snapshot(path, profile)


def refresh_fantasy_football_calculator_adp(
    root: str | Path,
    profile: LeagueProfile,
    ranking: RankingResult,
    manual_assets: Sequence[Mapping[str, Any]] = (),
    *,
    fetcher: Any | None = None,
) -> AdpSnapshot:
    """Fetch one documented FFC snapshot and atomically preserve the last known good cache."""

    scoring_slug = {"PPR": "ppr", "HALF_PPR": "half-ppr", "STANDARD": "standard"}.get(
        _profile_scoring(profile)
    )
    if not scoring_slug:
        raise RedraftValidationError("FFC ADP does not support the active scoring format.")
    endpoint = f"{FFC_API_BASE}/{scoring_slug}?teams={profile.team_count}&year={profile.season}"
    try:
        raw = fetcher(endpoint) if fetcher is not None else _fetch_ffc_json(endpoint)
        document = raw if isinstance(raw, Mapping) else json.loads(
            raw.decode("utf-8") if isinstance(raw, bytes) else str(raw)
        )
        snapshot = _parse_ffc_snapshot(
            profile, ranking, manual_assets, document, endpoint=endpoint
        )
        _atomic_json(_ffc_adp_path(root, profile.profile_id), _adp_document(snapshot))
        return snapshot
    except (
        OSError,
        ValueError,
        TypeError,
        KeyError,
        json.JSONDecodeError,
        urllib.error.URLError,
    ) as exc:
        cached_path = _ffc_adp_path(root, profile.profile_id)
        if cached_path.is_file():
            cached = _read_adp_snapshot(cached_path, profile)
            failed = _snapshot_with_refresh_error(cached, str(exc))
            _atomic_json(cached_path, _adp_document(failed))
            return failed
        raise RedraftPersistenceError(
            "Fantasy Football Calculator ADP refresh failed and no cache is available."
        ) from exc


def _read_adp_snapshot(path: Path, profile: LeagueProfile) -> AdpSnapshot:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
        if (
            int(document.get("schema_version") or 1) not in {1, ADP_SCHEMA_VERSION}
            or document.get("profile_id") != profile.profile_id
            or document.get("team_count") != profile.team_count
            or document.get("scoring_format") != _profile_scoring(profile)
        ):
            raise RedraftValidationError("ADP snapshot does not match the active league.")
        entries = tuple(AdpEntry(**row) for row in document.get("entries", []))
        return AdpSnapshot(
            profile_id=profile.profile_id,
            source=str(document.get("source") or ""),
            scoring_format=str(document.get("scoring_format") or ""),
            team_count=int(document.get("team_count") or 0),
            source_date=str(document.get("source_date") or ""),
            imported_at_utc=str(document.get("imported_at_utc") or ""),
            source_sha256=str(document.get("source_sha256") or ""),
            entries=entries,
            unmatched=tuple(str(value) for value in document.get("unmatched", [])),
            errors=tuple(str(value) for value in document.get("errors", [])),
            provider=str(document.get("provider") or "OWNER_IMPORT"),
            authority=str(document.get("authority") or FFC_AUTHORITY),
            position_filter=str(document.get("position_filter") or "ALL"),
            sample_size=_optional_int(document.get("sample_size")),
            date_window=str(document.get("date_window") or ""),
            retrieved_at_utc=str(
                document.get("retrieved_at_utc") or document.get("imported_at_utc") or ""
            ),
            provider_version=str(document.get("provider_version") or ""),
            endpoint=str(document.get("endpoint") or ""),
            freshness=_freshness_label(
                str(document.get("retrieved_at_utc") or document.get("imported_at_utc") or "")
            ),
            last_refresh_error=str(document.get("last_refresh_error") or ""),
            match_report=tuple(
                dict(value)
                for value in document.get("match_report", [])
                if isinstance(value, Mapping)
            ),
            paste_rows=tuple(
                dict(value)
                for value in document.get("paste_rows", [])
                if isinstance(value, Mapping)
            ),
        )
    except (OSError, ValueError, TypeError, json.JSONDecodeError, RedraftValidationError) as exc:
        raise RedraftPersistenceError("ADP snapshot is unreadable or incompatible.") from exc


def _fetch_ffc_json(endpoint: str) -> bytes:
    request = urllib.request.Request(
        endpoint,
        headers={
            "Accept": "application/json",
            "User-Agent": "Niners-War-Room/1.0 (local owner ADP refresh)",
        },
        method="GET",
    )
    with urllib.request.urlopen(request, timeout=20) as response:  # noqa: S310 - admitted HTTPS API
        if getattr(response, "status", 200) != 200:
            raise OSError(f"FFC returned HTTP {getattr(response, 'status', 'unknown')}.")
        return response.read(4_000_001)


def _parse_ffc_snapshot(
    profile: LeagueProfile,
    ranking: RankingResult,
    manual_assets: Sequence[Mapping[str, Any]],
    document: Mapping[str, Any],
    *,
    endpoint: str,
) -> AdpSnapshot:
    if str(document.get("status") or "").lower() != "success":
        raise ValueError("FFC response status was not Success.")
    meta = document.get("meta")
    players = document.get("players")
    if not isinstance(meta, Mapping) or not isinstance(players, list):
        raise ValueError("FFC response is missing meta or players.")
    if int(meta.get("teams") or 0) != profile.team_count:
        raise ValueError("FFC response team count does not match the active profile.")
    response_scoring = _normalized_scoring(str(meta.get("type") or ""))
    if response_scoring != _profile_scoring(profile):
        raise ValueError("FFC response scoring format does not match the active profile.")

    assets = _matching_assets(ranking, manual_assets)
    entries: list[AdpEntry] = []
    unmatched: list[str] = []
    report: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for source in players:
        if not isinstance(source, Mapping):
            continue
        source_id = str(source.get("player_id") or "")
        player = str(source.get("name") or "").strip()
        position = _normalized_position(str(source.get("position") or ""))
        team = _normalized_team(str(source.get("team") or ""))
        try:
            expected = float(source.get("adp"))
        except (TypeError, ValueError):
            expected = 0.0
        if not player or position not in {"QB", "RB", "WR", "TE", "K", "DST"} or expected <= 0:
            reason = "INVALID_SOURCE_IDENTITY_OR_ADP"
            unmatched.append(f"{source_id or 'unknown'}: {player or 'missing player'} ({position})")
            report.append(_match_report_row(
                source_id, player, position, team, None, "UNMATCHED", "", reason,
                sample_size=_optional_int(source.get("times_drafted")),
            ))
            continue
        matched, method, confidence, reason = _match_adp_player(player, position, team, assets)
        if matched is None:
            unmatched.append(f"{source_id}: {player} ({position}, {team})")
            report.append(_match_report_row(
                source_id, player, position, team, None, "UNMATCHED", "", reason,
                sample_size=_optional_int(source.get("times_drafted")),
            ))
            continue
        matched_id = str(matched["player_id"])
        if matched_id in seen_ids:
            unmatched.append(f"{source_id}: {player} duplicates matched NWR ID {matched_id}")
            report.append(_match_report_row(
                source_id, player, position, team, matched, "UNMATCHED", "",
                "DUPLICATE_MATCHED_NWR_ID", sample_size=_optional_int(source.get("times_drafted")),
            ))
            continue
        seen_ids.add(matched_id)
        minimum = _source_float(source.get("high"))
        maximum = _source_float(source.get("low"))
        std_dev = _source_float(source.get("stdev"))
        entries.append(
            AdpEntry(
                player_id=matched_id,
                player=str(matched["player_name"]),
                team=str(matched["team"]),
                position=str(matched["position"]),
                overall_adp=round(expected, 2),
                expected_pick=round(expected, 2),
                min_pick=round(minimum, 2) if minimum is not None else None,
                max_pick=round(maximum, 2) if maximum is not None else None,
                std_dev=round(std_dev, 2) if std_dev is not None else None,
                source_player_id=source_id,
                expected_round=max(1, math.ceil(expected / profile.team_count)),
                match_status="MATCHED",
                match_confidence=confidence,
            )
        )
        report.append(_match_report_row(
            source_id, player, position, team, matched, method, confidence, "",
            sample_size=_optional_int(source.get("times_drafted")),
        ))
    if not entries:
        raise ValueError("FFC response did not safely match any NWR Draft Room assets.")

    entries.sort(key=lambda entry: (entry.expected_pick, entry.player_id))
    retrieved = utc_now()
    start_date = str(meta.get("start_date") or "")
    end_date = str(meta.get("end_date") or "")
    canonical_source = json.dumps(document, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return AdpSnapshot(
        profile_id=profile.profile_id,
        source=FFC_SOURCE,
        scoring_format=_profile_scoring(profile),
        team_count=profile.team_count,
        source_date=end_date,
        imported_at_utc=retrieved,
        source_sha256=hashlib.sha256(canonical_source).hexdigest(),
        entries=tuple(entries),
        unmatched=tuple(unmatched),
        provider="FFC",
        authority=FFC_AUTHORITY,
        position_filter="ALL",
        sample_size=_optional_int(meta.get("total_drafts")),
        date_window=f"{start_date} to {end_date}" if start_date and end_date else end_date,
        retrieved_at_utc=retrieved,
        provider_version=FFC_PROVIDER_VERSION,
        endpoint=endpoint,
        freshness="FRESH",
        match_report=tuple(report),
    )


def _matching_assets(
    ranking: RankingResult,
    manual_assets: Sequence[Mapping[str, Any]],
) -> list[dict[str, str]]:
    assets = [
        {
            "player_id": str(row.player_id),
            "player_name": str(row.player_name),
            "position": _normalized_position(str(row.position)),
            "team": _normalized_team(str(row.team)),
        }
        for row in ranking.rows
    ]
    assets.extend(
        {
            "player_id": _manual_id(row),
            "player_name": str(row.get("player_name") or row.get("playerName") or ""),
            "position": _normalized_position(str(row.get("position") or "")),
            "team": _normalized_team(str(row.get("team") or "")),
        }
        for row in manual_assets
        if _manual_id(row)
    )
    return assets


def _match_adp_player(
    player: str,
    position: str,
    team: str,
    assets: Sequence[Mapping[str, str]],
) -> tuple[Mapping[str, str] | None, str, str, str]:
    normalized_position = _normalized_position(position)
    normalized_team = _normalized_team(team)
    position_assets = [row for row in assets if row["position"] == normalized_position]
    if normalized_position == "DST" and normalized_team:
        team_matches = [row for row in position_assets if row["team"] == normalized_team]
        if len(team_matches) == 1:
            return team_matches[0], "DST_TEAM_POSITION", "HIGH", ""
        return None, "", "", "DST_TEAM_NOT_UNIQUE"

    exact_name = _normalized_name(player)
    exact_matches = [
        row for row in position_assets if _normalized_name(row["player_name"]) == exact_name
    ]
    if normalized_team:
        exact_team = [row for row in exact_matches if row["team"] == normalized_team]
        if len(exact_team) == 1:
            return exact_team[0], "EXACT_NAME_POSITION_TEAM", "HIGH", ""
        if len(exact_matches) == 1:
            return exact_matches[0], "EXACT_NAME_POSITION_TEAM_MISMATCH", "MEDIUM", ""
    elif len(exact_matches) == 1:
        return exact_matches[0], "EXACT_NAME_POSITION", "HIGH", ""
    if exact_matches:
        return None, "", "", "EXACT_NAME_TEAM_COLLISION_OR_MISMATCH"

    core_name = _normalized_name_without_suffix(player)
    core_matches = [
        row
        for row in position_assets
        if _normalized_name_without_suffix(row["player_name"]) == core_name
    ]
    if normalized_team:
        core_team_matches = [row for row in core_matches if row["team"] == normalized_team]
        if len(core_team_matches) == 1:
            return core_team_matches[0], "SUFFIX_TOLERANT_NAME_POSITION_TEAM", "MEDIUM", ""
        if len(core_matches) == 1:
            return core_matches[0], "SUFFIX_TOLERANT_TEAM_MISMATCH", "MEDIUM", ""
    elif len(core_matches) == 1:
        return core_matches[0], "SUFFIX_TOLERANT_NAME_POSITION", "MEDIUM", ""
    return None, "", "", "NO_SAFE_IDENTITY_MATCH" if not core_matches else "NAME_COLLISION"


def _match_report_row(
    source_id: str,
    player: str,
    position: str,
    team: str,
    matched: Mapping[str, str] | None,
    method: str,
    confidence: str,
    reason: str,
    *,
    sample_size: int | None = None,
) -> dict[str, Any]:
    return {
        "source_player_id": source_id,
        "source_player_name": player,
        "source_position": position,
        "source_team": _normalized_team(team),
        "matched_nwr_player_id": str((matched or {}).get("player_id") or ""),
        "matched_nwr_player_name": str((matched or {}).get("player_name") or ""),
        "match_status": "MATCHED" if matched is not None and method != "UNMATCHED" else "UNMATCHED",
        "match_method": method,
        "match_confidence": confidence,
        "unmatched_reason": reason,
        "times_drafted": sample_size,
    }


def _snapshot_with_refresh_error(snapshot: AdpSnapshot, error: str) -> AdpSnapshot:
    return replace(
        snapshot,
        freshness=_freshness_label(snapshot.retrieved_at_utc or snapshot.imported_at_utc),
        last_refresh_error=(error.strip() or "Provider refresh failed.")[:300],
    )


def _freshness_label(value: str, *, now: datetime | None = None) -> str:
    if not value:
        return "UNAVAILABLE"
    try:
        retrieved = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return "UNAVAILABLE"
    reference = now or datetime.now(UTC)
    age = reference - retrieved.astimezone(UTC)
    if age <= timedelta(hours=24):
        return "FRESH"
    if age <= timedelta(hours=72):
        return "RECENT"
    return "STALE"


def _source_float(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) and number > 0 else None


def _optional_int(value: Any) -> int | None:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None
    return number if number >= 0 else None


def draft_order(profile: LeagueProfile) -> tuple[int, ...]:
    order: list[int] = []
    for round_number in range(1, profile.draft.rounds + 1):
        slots = range(1, profile.team_count + 1)
        order.extend(slots if round_number % 2 else reversed(tuple(slots)))
    return tuple(order)


def load_room_state(
    root: str | Path,
    profile: LeagueProfile,
    ranking: RankingResult,
    manual_assets: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    document = load_draft_board(root, profile.profile_id)
    return _coerce_room_state(profile, ranking, manual_assets, document)


def start_draft_room(
    root: str | Path,
    profile: LeagueProfile,
    ranking: RankingResult,
    manual_assets: Sequence[Mapping[str, Any]],
    adp: AdpSnapshot,
    *,
    owner_slot: int,
    seed: int = DEFAULT_SEED,
    speed: str = "NORMAL",
    mode: str = "MOCK",
) -> dict[str, Any]:
    if profile.draft.draft_type != "snake" or not 1 <= owner_slot <= profile.team_count:
        raise RedraftValidationError("Draft Room requires a valid snake-draft owner slot.")
    normalized_speed = speed.strip().upper()
    normalized_mode = mode.strip().upper()
    if normalized_speed not in SUPPORTED_SPEEDS or normalized_mode not in SUPPORTED_MODES:
        raise RedraftValidationError("Draft Room speed or mode is unsupported.")
    state = {
        "schema_version": ROOM_SCHEMA_VERSION,
        "profile_id": profile.profile_id,
        "owner_slot": owner_slot,
        "seed": int(seed),
        "speed": normalized_speed,
        "mode": normalized_mode,
        "drafted": [],
        "picks": [],
        "updated_at_utc": utc_now(),
    }
    if normalized_mode == "MOCK":
        state = _advance_cpu(
            profile,
            ranking,
            manual_assets,
            adp,
            state,
            stop_at_owner=True,
        )
    _save_room_state(root, state)
    return state


def owner_pick_and_advance(
    root: str | Path,
    profile: LeagueProfile,
    ranking: RankingResult,
    manual_assets: Sequence[Mapping[str, Any]],
    adp: AdpSnapshot,
    *,
    player_id: str,
) -> dict[str, Any]:
    state = load_room_state(root, profile, ranking, manual_assets)
    owner_slot = state.get("owner_slot")
    if not isinstance(owner_slot, int):
        raise RedraftValidationError("Start the Draft Room and choose an owner slot first.")
    if _current_team(profile, state) != owner_slot:
        raise RedraftValidationError("The Draft Room is not currently on the owner pick.")
    asset = _asset_pool(ranking, manual_assets).get(player_id)
    if asset is None or player_id in state["drafted"]:
        raise RedraftValidationError("The selected Draft Room player is unavailable.")
    state = _record_pick(profile, state, asset, actor="OWNER", behavior="OWNER_SELECTION")
    if state.get("mode") == "MOCK" and not _complete(profile, state):
        step = state.get("speed") == "STEP"
        state = _advance_cpu(
            profile,
            ranking,
            manual_assets,
            adp,
            state,
            stop_at_owner=not step,
            max_picks=1 if step else None,
        )
    _save_room_state(root, state)
    return state


def advance_cpu_to_owner(
    root: str | Path,
    profile: LeagueProfile,
    ranking: RankingResult,
    manual_assets: Sequence[Mapping[str, Any]],
    adp: AdpSnapshot,
    *,
    one_pick: bool = False,
) -> dict[str, Any]:
    state = load_room_state(root, profile, ranking, manual_assets)
    state = _advance_cpu(
        profile,
        ranking,
        manual_assets,
        adp,
        state,
        stop_at_owner=not one_pick,
        max_picks=1 if one_pick else None,
    )
    _save_room_state(root, state)
    return state


def undo_room_pick(
    root: str | Path,
    profile: LeagueProfile,
    ranking: RankingResult,
    manual_assets: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    state = load_room_state(root, profile, ranking, manual_assets)
    if not state["picks"]:
        raise RedraftValidationError("No Draft Room pick is available to undo.")
    state["picks"] = state["picks"][:-1]
    state["drafted"] = [pick["player_id"] for pick in state["picks"]]
    state["updated_at_utc"] = utc_now()
    _save_room_state(root, state)
    return state


def ingest_read_only_sleeper_pick(
    root: str | Path,
    profile: LeagueProfile,
    ranking: RankingResult,
    manual_assets: Sequence[Mapping[str, Any]],
    *,
    player_id: str,
    pick_number: int,
) -> dict[str, Any]:
    state = load_room_state(root, profile, ranking, manual_assets)
    if state.get("mode") != "LIVE_READ_ONLY":
        raise RedraftValidationError("Sleeper pick ingestion requires Live Read-Only mode.")
    expected = len(state["picks"]) + 1
    if pick_number != expected:
        raise RedraftValidationError(
            f"Sleeper pick {pick_number} does not match next pick {expected}."
        )
    asset = _asset_pool(ranking, manual_assets).get(player_id)
    if asset is None or player_id in state["drafted"]:
        raise RedraftValidationError("Sleeper pick player is unavailable locally.")
    state = _record_pick(
        profile,
        state,
        asset,
        actor="SLEEPER_READ_ONLY",
        behavior="READ_ONLY_PICK_EVENT",
    )
    _save_room_state(root, state)
    return state


def run_complete_mock(
    profile: LeagueProfile,
    ranking: RankingResult,
    manual_assets: Sequence[Mapping[str, Any]],
    adp: AdpSnapshot,
    *,
    owner_slot: int,
    seed: int = DEFAULT_SEED,
) -> dict[str, Any]:
    state: dict[str, Any] = {
        "schema_version": ROOM_SCHEMA_VERSION,
        "profile_id": profile.profile_id,
        "owner_slot": owner_slot,
        "seed": seed,
        "speed": "FAST",
        "mode": "MOCK",
        "drafted": [],
        "picks": [],
        "updated_at_utc": utc_now(),
    }
    pool = _asset_pool(ranking, manual_assets)
    while not _complete(profile, state):
        team_slot = _current_team(profile, state)
        actor = "OWNER_AUTO_TEST" if team_slot == owner_slot else "CPU"
        asset, behavior = _select_asset(profile, ranking, adp, state, pool, team_slot, actor)
        state = _record_pick(profile, state, asset, actor=actor, behavior=behavior)
    return state


def build_draft_room_payload(
    profile: LeagueProfile,
    ranking: RankingResult,
    manual_assets: Sequence[Mapping[str, Any]],
    adp: AdpSnapshot,
    state: Mapping[str, Any],
) -> dict[str, Any]:
    normalized = _coerce_room_state(profile, ranking, manual_assets, state)
    order = draft_order(profile)
    picks = list(normalized["picks"])
    picks_by_number = {int(pick["pick_number"]): pick for pick in picks}
    owner_slot = normalized.get("owner_slot")
    current_pick = len(picks) + 1
    complete = current_pick > len(order)
    current_team = None if complete else order[current_pick - 1]
    next_owner = _next_owner_pick(profile, current_pick, owner_slot)
    roster_by_team = _rosters(profile, picks)
    board_cells = []
    for pick_number, team_slot in enumerate(order, start=1):
        round_number = ((pick_number - 1) // profile.team_count) + 1
        pick = picks_by_number.get(pick_number)
        board_cells.append(
            {
                "pickNumber": pick_number,
                "round": round_number,
                "teamSlot": team_slot,
                "ownerPick": team_slot == owner_slot,
                "current": pick_number == current_pick and not complete,
                "playerId": str((pick or {}).get("player_id") or ""),
                "playerName": str((pick or {}).get("player_name") or ""),
                "position": str((pick or {}).get("position") or ""),
                "team": str((pick or {}).get("team") or ""),
                "actor": str((pick or {}).get("actor") or ""),
                "selectionBehavior": str((pick or {}).get("selection_behavior") or ""),
            }
        )
    teams = [
        {
            "teamSlot": slot,
            "name": "My Team" if slot == owner_slot else f"Team {slot}",
            "owner": slot == owner_slot,
            "roster": roster_by_team[slot],
            "picks": [pick for pick in picks if pick["team_slot"] == slot],
        }
        for slot in range(1, profile.team_count + 1)
    ]
    available = _available_ranked(ranking, normalized)
    recommendations = _recommendations(
        profile,
        ranking,
        adp,
        normalized,
        current_pick=current_pick,
        next_owner_pick=next_owner,
    )
    return {
        "schemaVersion": ROOM_SCHEMA_VERSION,
        "profileId": profile.profile_id,
        "configured": isinstance(owner_slot, int),
        "ownerSlot": owner_slot,
        "seed": normalized.get("seed", DEFAULT_SEED),
        "speed": normalized.get("speed", "NORMAL"),
        "mode": normalized.get("mode", "MOCK"),
        "drafted": list(normalized["drafted"]),
        "picks": [_pick_payload(pick) for pick in picks],
        "boardCells": board_cells,
        "teams": teams,
        "recentPicks": [_pick_payload(pick) for pick in picks[-8:]],
        "draftLog": [_pick_payload(pick) for pick in picks],
        "myRoster": roster_by_team.get(owner_slot, []) if isinstance(owner_slot, int) else [],
        "currentPick": None if complete else current_pick,
        "currentTeamSlot": current_team,
        "nextOwnerPick": next_owner,
        "isOwnerTurn": current_team == owner_slot and not complete,
        "complete": complete,
        "availableCount": len(available)
        + len([row for row in manual_assets if _manual_id(row) not in normalized["drafted"]]),
        "canUndo": bool(picks),
        "updatedAtUtc": str(normalized.get("updated_at_utc") or ""),
        "recoveredFromBackup": bool(normalized.get("recovered_from_backup")),
        "adp": _adp_status(adp, len(ranking.rows)),
        "beatAdpPool": recommendations["beatAdpPool"],
        "decisionRows": recommendations["allRows"],
        "recommendations": recommendations["cards"],
        "positionRun": recommendations["positionRun"],
        "fallbackDisclosure": (
            "CPU uses Fantasy Football Calculator market ADP plus seeded variation and "
            "roster construction; NWR rank remains separate."
            if adp.available and adp.provider == "FFC"
            else "CPU uses owner-imported ADP plus seeded variation and roster construction."
            if adp.available
            else "ADP unavailable. CPU uses disclosed deterministic NWR order fallback; "
            "this is not market realism."
        ),
        "sleeperCompatibility": {
            "mode": "READ_ONLY_PICK_EVENTS",
            "pollingDefault": "OFF",
            "writes": "NONE",
        },
    }


def validate_complete_mock(profile: LeagueProfile, state: Mapping[str, Any]) -> tuple[str, ...]:
    picks = list(state.get("picks", []))
    errors: list[str] = []
    expected = profile.team_count * profile.draft.rounds
    if len(picks) != expected:
        errors.append(f"Draft contains {len(picks)} picks; expected {expected}.")
    player_ids = [str(pick.get("player_id") or "") for pick in picks]
    if len(player_ids) != len(set(player_ids)):
        errors.append("Draft contains duplicate player IDs.")
    rosters = _rosters(profile, picks)
    required = {
        "QB": profile.roster.qb,
        "RB": profile.roster.rb,
        "WR": profile.roster.wr,
        "TE": profile.roster.te,
        "K": profile.roster.k,
        "DST": profile.roster.dst,
    }
    for slot, roster in rosters.items():
        counts = Counter(str(player["position"]) for player in roster)
        for position, count in required.items():
            if counts[position] < count:
                errors.append(f"Team {slot} is missing required {position}.")
        flex_total = sum(counts[position] for position in ("RB", "WR", "TE"))
        flex_required = (
            profile.roster.rb + profile.roster.wr + profile.roster.te + profile.roster.flex
        )
        if flex_total < flex_required:
            errors.append(f"Team {slot} is missing a legal FLEX asset.")
    return tuple(errors)


def _advance_cpu(
    profile: LeagueProfile,
    ranking: RankingResult,
    manual_assets: Sequence[Mapping[str, Any]],
    adp: AdpSnapshot,
    state: dict[str, Any],
    *,
    stop_at_owner: bool,
    max_picks: int | None = None,
) -> dict[str, Any]:
    owner_slot = state.get("owner_slot")
    if not isinstance(owner_slot, int):
        raise RedraftValidationError("Draft Room owner slot is not configured.")
    pool = _asset_pool(ranking, manual_assets)
    added = 0
    while not _complete(profile, state):
        team_slot = _current_team(profile, state)
        if team_slot == owner_slot and stop_at_owner:
            break
        if team_slot == owner_slot:
            break
        asset, behavior = _select_asset(profile, ranking, adp, state, pool, team_slot, "CPU")
        state = _record_pick(profile, state, asset, actor="CPU", behavior=behavior)
        added += 1
        if max_picks is not None and added >= max_picks:
            break
    return state


def _select_asset(
    profile: LeagueProfile,
    ranking: RankingResult,
    adp: AdpSnapshot,
    state: Mapping[str, Any],
    pool: Mapping[str, dict[str, Any]],
    team_slot: int,
    actor: str,
) -> tuple[dict[str, Any], str]:
    available = [asset for key, asset in pool.items() if key not in state.get("drafted", [])]
    if not available:
        raise RedraftValidationError("No Draft Room asset remains available.")
    roster = Counter(
        str(pick["position"])
        for pick in state.get("picks", [])
        if int(pick["team_slot"]) == team_slot
    )
    current_pick = len(state.get("picks", [])) + 1
    round_number = ((current_pick - 1) // profile.team_count) + 1
    forced = _forced_position(profile, roster, round_number)
    candidates = [asset for asset in available if forced is None or asset["position"] == forced]
    if not candidates:
        candidates = available
    candidates = [
        asset for asset in candidates if _roster_candidate_allowed(profile, roster, asset)
    ]
    if not candidates:
        candidates = available
    if actor == "OWNER_AUTO_TEST":
        candidates.sort(
            key=lambda asset: (
                _owner_auto_score(profile, roster, round_number, asset),
                str(asset["player_id"]),
            )
        )
        behavior = (
            "MANUAL_UNMODELED"
            if candidates[0]["position"] in {"K", "DST"}
            else "OWNER_TEST_NWR_RECOMMENDATION"
        )
        return candidates[0], behavior

    adp_by_id = adp.by_player_id if adp.available else {}
    seed = int(state.get("seed") or DEFAULT_SEED)
    scored: list[tuple[float, str, dict[str, Any]]] = []
    for asset in candidates:
        entry = adp_by_id.get(str(asset["player_id"]))
        base = entry.expected_pick if entry is not None else float(asset.get("nwr_rank") or 9999)
        spread = _adp_spread(entry) if entry is not None else 5.0
        jitter = _seeded_unit(seed, current_pick, str(asset["player_id"])) * spread
        need_adjustment = _roster_need_adjustment(profile, roster, round_number, asset["position"])
        missing_adp_penalty = 25.0 if adp.available and entry is None else 0.0
        scored.append(
            (base + jitter + need_adjustment + missing_adp_penalty, str(asset["player_id"]), asset)
        )
    scored.sort(key=lambda row: (row[0], row[1]))
    if adp.available and adp.provider == "FFC":
        behavior = "CPU_MARKET_ADP_FFC"
    elif adp.available and adp.provider == "OWNER_PLATFORM_AUTO_SLEEPER":
        behavior = "CPU_MARKET_ADP_OWNER_AUTO_SLEEPER"
    elif adp.available and adp.provider == "OWNER_PLATFORM_AUTO_ESPN":
        behavior = "CPU_MARKET_ADP_OWNER_AUTO_ESPN"
    elif adp.available and adp.provider == "OWNER_PLATFORM_AUTO_CONSENSUS":
        behavior = "CPU_MARKET_ADP_OWNER_AUTO_CONSENSUS"
    elif adp.available and adp.provider == "OWNER_PLATFORM_AUTO_FANTASYPROS":
        behavior = "CPU_MARKET_ADP_OWNER_AUTO_FANTASYPROS"
    elif adp.available and adp.provider == "OWNER_PLATFORM_SLEEPER":
        behavior = "CPU_MARKET_ADP_OWNER_SLEEPER"
    elif adp.available and adp.provider == "OWNER_PLATFORM_ESPN":
        behavior = "CPU_MARKET_ADP_OWNER_ESPN"
    elif adp.available and adp.provider == "OWNER_PLATFORM_CONSENSUS":
        behavior = "CPU_MARKET_ADP_OWNER_CONSENSUS"
    elif adp.available and adp.provider == "OWNER_PLATFORM_FANTASYPROS":
        behavior = "CPU_MARKET_ADP_OWNER_FANTASYPROS"
    elif adp.available and adp.provider == "OWNER_PASTE_SLEEPER":
        behavior = "CPU_MARKET_ADP_OWNER_SLEEPER"
    elif adp.available and adp.provider == "OWNER_PASTE_CONSENSUS":
        behavior = "CPU_MARKET_ADP_OWNER_CONSENSUS"
    elif adp.available and adp.provider == "OWNER_PASTE_ESPN":
        behavior = "CPU_MARKET_ADP_OWNER_ESPN"
    elif adp.available and adp.provider == "OWNER_PASTE_FANTASYPROS":
        behavior = "CPU_MARKET_ADP_OWNER_FANTASYPROS"
    elif adp.available and adp.provider == "OWNER_SLEEPER_CSV":
        behavior = "CPU_MARKET_ADP_OWNER_SLEEPER"
    elif adp.available:
        behavior = "CPU_MARKET_ADP_OWNER_IMPORT"
    else:
        behavior = "DISCLOSED_NWR_ORDER_FALLBACK"
    if scored[0][2]["position"] in {"K", "DST"}:
        behavior = "MANUAL_UNMODELED"
    return scored[0][2], behavior


def _record_pick(
    profile: LeagueProfile,
    state: Mapping[str, Any],
    asset: Mapping[str, Any],
    *,
    actor: str,
    behavior: str,
) -> dict[str, Any]:
    updated = {**state, "picks": list(state.get("picks", []))}
    pick_number = len(updated["picks"]) + 1
    order = draft_order(profile)
    if pick_number > len(order):
        raise RedraftValidationError("The Draft Room is already complete.")
    player_id = str(asset["player_id"])
    if player_id in state.get("drafted", []):
        raise RedraftValidationError("The Draft Room player is already drafted.")
    round_number = ((pick_number - 1) // profile.team_count) + 1
    team_slot = order[pick_number - 1]
    updated["picks"].append(
        {
            "pick_number": pick_number,
            "round": round_number,
            "team_slot": team_slot,
            "player_id": player_id,
            "player_name": str(asset["player_name"]),
            "position": str(asset["position"]),
            "team": str(asset.get("team") or ""),
            "actor": actor,
            "selection_behavior": behavior,
            "nwr_rank": asset.get("nwr_rank"),
            "picked_at_utc": utc_now(),
        }
    )
    updated["drafted"] = [pick["player_id"] for pick in updated["picks"]]
    updated["updated_at_utc"] = utc_now()
    return updated


def _recommendations(
    profile: LeagueProfile,
    ranking: RankingResult,
    adp: AdpSnapshot,
    state: Mapping[str, Any],
    *,
    current_pick: int,
    next_owner_pick: int | None,
) -> dict[str, Any]:
    available = _available_ranked(ranking, state)
    owner_slot = state.get("owner_slot")
    roster = Counter(
        str(pick["position"])
        for pick in state.get("picks", [])
        if pick.get("team_slot") == owner_slot
    )
    enriched = [
        _decision_row(profile, row, adp, current_pick, next_owner_pick, roster)
        for row in available[:100]
    ]
    beat_pool = sorted(
        [row for row in enriched if row["nwrView"] in {"STRONG VALUE", "VALUE"}],
        key=lambda row: (-float(row.get("nwrEdge") or 0), int(row["nwrRank"])),
    )[:30]
    cards: list[dict[str, Any]] = []
    if enriched:
        cards.append(_card("Best Available", enriched[0], "Highest available NWR Redraft rank."))
        fit = min(
            enriched[:30],
            key=lambda row: (
                _fit_penalty(profile, roster, str(row["position"])),
                int(row["nwrRank"]),
            ),
        )
        cards.append(_card("Best Fit", fit, "Best open-starter and FLEX fit among top options."))
        value_rows = [row for row in enriched if row.get("expectedPick") is not None]
        if value_rows:
            value = max(value_rows, key=lambda row: float(row.get("nwrEdge") or -9999))
            cards.append(_card("Value vs ADP", value, "Largest admitted ADP edge near this pick."))
        else:
            cards.append(
                _card(
                    "Value vs ADP",
                    enriched[0],
                    "ADP unavailable; this card preserves NWR order and makes no market claim.",
                )
            )
        upside = max(enriched[:20], key=lambda row: float(row["replacementAdjustedValue"]))
        cards.append(
            _card("Upside", upside, "Highest replacement-adjusted ceiling proxy available.")
        )
        safe_rows = [row for row in enriched[:30] if str(row["confidence"]).upper() == "HIGH"]
        safer = safe_rows[0] if safe_rows else enriched[0]
        cards.append(
            _card("Safer", safer, "Best high-evidence option; falls back visibly if none.")
        )
    recent_positions = [str(pick["position"]) for pick in state.get("picks", [])[-6:]]
    counts = Counter(recent_positions)
    position_run = [
        {"position": position, "count": count}
        for position, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
        if count >= 2
    ]
    return {
        "cards": cards[:5],
        "beatAdpPool": beat_pool,
        "allRows": enriched,
        "positionRun": position_run,
    }


def _decision_row(
    profile: LeagueProfile,
    row: Any,
    adp: AdpSnapshot,
    current_pick: int,
    next_owner_pick: int | None,
    roster: Counter[str],
) -> dict[str, Any]:
    entry = adp.by_player_id.get(row.player_id) if adp.available else None
    edge = round(entry.expected_pick - row.overall_rank, 1) if entry else None
    nwr_view = _nwr_view(edge)
    timing, survival, probability, method = _draft_timing(
        row.overall_rank,
        entry,
        current_pick,
        next_owner_pick,
    )
    return {
        "playerId": row.player_id,
        "playerName": row.player_name,
        "team": row.team,
        "position": row.position,
        "nwrRank": row.overall_rank,
        "positionRank": row.position_rank,
        "overallTier": row.tier,
        "overallTierLabel": getattr(row, "overall_tier_label", f"Tier {row.tier}"),
        "positionTier": getattr(row, "position_tier", row.tier),
        "positionTierLabel": getattr(row, "position_tier_label", f"{row.position} Tier {row.tier}"),
        "replacementAdjustedValue": row.replacement_adjusted_value,
        "confidence": row.confidence,
        "expectedPick": entry.expected_pick if entry else None,
        "expectedRound": entry.expected_round if entry else None,
        "overallAdp": entry.overall_adp if entry else None,
        "nwrEdge": edge,
        "nwrView": nwr_view,
        "draftTiming": timing,
        "makeItBack": survival,
        "makeItBackProbability": probability,
        "makeItBackMethod": method,
        "rosterFit": _roster_fit(profile, roster, row.position),
        "adpSource": adp.source if entry else "",
        "adpSourceDate": adp.source_date if entry else "",
    }


def _draft_timing(
    nwr_rank: int,
    entry: AdpEntry | None,
    current_pick: int,
    next_owner_pick: int | None,
) -> tuple[str, str, float | None, str]:
    if entry is None:
        return "ADP UNAVAILABLE", "MAKE-IT-BACK: UNAVAILABLE", None, "NO_ADP_DISTRIBUTION"
    if nwr_rank > current_pick + 35 and entry.expected_pick > current_pick + 20:
        timing = "REACH"
    elif entry.expected_pick <= current_pick + 3:
        timing = "TAKE NOW"
    elif next_owner_pick is not None and entry.expected_pick >= next_owner_pick + 5:
        timing = "WAIT"
    else:
        timing = "VALID"
    if next_owner_pick is None:
        return timing, "MAKE-IT-BACK: UNAVAILABLE", None, "NO_NEXT_OWNER_PICK"
    spread = _adp_distribution_spread(entry)
    if spread is None:
        return timing, "HEURISTIC — LOW CONFIDENCE", None, "EXPECTED_PICK_ONLY_NO_PROBABILITY"
    z = (next_owner_pick - entry.expected_pick) / spread
    probability = 0.5 * math.erfc(z / math.sqrt(2.0))
    probability = round(max(0.0, min(1.0, probability)), 2)
    if probability >= 0.65:
        survival = "LIKELY TO MAKE IT BACK"
    elif probability <= 0.35:
        survival = "UNLIKELY TO MAKE IT BACK"
    else:
        survival = "HEURISTIC — LOW CONFIDENCE"
    return timing, survival, probability, "HEURISTIC_NORMAL_FROM_OWNER_ADP_RANGE"


def _coerce_room_state(
    profile: LeagueProfile,
    ranking: RankingResult,
    manual_assets: Sequence[Mapping[str, Any]],
    document: Mapping[str, Any],
) -> dict[str, Any]:
    pool = _asset_pool(ranking, manual_assets)
    drafted = [str(value) for value in document.get("drafted", [])]
    raw_picks = document.get("picks", [])
    picks: list[dict[str, Any]] = []
    if isinstance(raw_picks, list) and raw_picks:
        for expected, raw in enumerate(raw_picks, start=1):
            if not isinstance(raw, Mapping) or int(raw.get("pick_number") or 0) != expected:
                raise RedraftValidationError("Draft Room event sequence is invalid.")
            picks.append(dict(raw))
    elif drafted:
        order = draft_order(profile)
        for index, player_id in enumerate(drafted, start=1):
            asset = pool.get(player_id, _unknown_asset(player_id))
            picks.append(
                {
                    "pick_number": index,
                    "round": ((index - 1) // profile.team_count) + 1,
                    "team_slot": order[index - 1],
                    "player_id": player_id,
                    "player_name": asset["player_name"],
                    "position": asset["position"],
                    "team": asset["team"],
                    "actor": "LEGACY",
                    "selection_behavior": "LEGACY_ORDER_ONLY",
                    "nwr_rank": asset.get("nwr_rank"),
                    "picked_at_utc": str(document.get("updated_at_utc") or ""),
                }
            )
    if [str(pick["player_id"]) for pick in picks] != drafted:
        drafted = [str(pick["player_id"]) for pick in picks]
    if len(drafted) != len(set(drafted)):
        raise RedraftValidationError("Draft Room contains duplicate player IDs.")
    return {
        "schema_version": ROOM_SCHEMA_VERSION,
        "profile_id": profile.profile_id,
        "owner_slot": document.get("owner_slot"),
        "seed": int(document.get("seed") or DEFAULT_SEED),
        "speed": str(document.get("speed") or "NORMAL"),
        "mode": str(document.get("mode") or "MOCK"),
        "drafted": drafted,
        "picks": picks,
        "updated_at_utc": str(document.get("updated_at_utc") or ""),
        "recovered_from_backup": bool(document.get("recovered_from_backup")),
    }


def _save_room_state(root: str | Path, state: Mapping[str, Any]) -> None:
    profile_id = str(state["profile_id"])
    path = Path(root) / "draft_boards" / f"{profile_id}.json"
    document = {
        "schema_version": ROOM_SCHEMA_VERSION,
        "profile_id": profile_id,
        "owner_slot": state.get("owner_slot"),
        "seed": int(state.get("seed") or DEFAULT_SEED),
        "speed": str(state.get("speed") or "NORMAL"),
        "mode": str(state.get("mode") or "MOCK"),
        "drafted": [str(value) for value in state.get("drafted", [])],
        "picks": list(state.get("picks", [])),
        "updated_at_utc": str(state.get("updated_at_utc") or utc_now()),
    }
    _atomic_json(path, document)
    _atomic_json(path.with_suffix(".backup.json"), document)


def _atomic_json(path: Path, document: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(document, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _asset_pool(
    ranking: RankingResult,
    manual_assets: Sequence[Mapping[str, Any]],
) -> dict[str, dict[str, Any]]:
    pool = {
        row.player_id: {
            "player_id": row.player_id,
            "player_name": row.player_name,
            "position": row.position,
            "team": row.team,
            "nwr_rank": row.overall_rank,
            "replacement_adjusted_value": row.replacement_adjusted_value,
            "confidence": row.confidence,
        }
        for row in ranking.rows
        if row.position in {"QB", "RB", "WR", "TE"}
    }
    for raw in manual_assets:
        player_id = _manual_id(raw)
        position = str(raw.get("position") or "").upper()
        if player_id and position in {"K", "DST"}:
            pool[player_id] = {
                "player_id": player_id,
                "player_name": str(raw.get("player_name") or raw.get("playerName") or ""),
                "position": position,
                "team": str(raw.get("team") or ""),
                "nwr_rank": None,
                "replacement_adjusted_value": None,
                "confidence": "NOT MODELED",
            }
    return pool


def _forced_position(profile: LeagueProfile, roster: Counter[str], round_number: int) -> str | None:
    if round_number >= max(1, profile.draft.rounds - 1):
        if roster["K"] < profile.roster.k:
            return "K"
        if roster["DST"] < profile.roster.dst:
            return "DST"
    deadlines = (("QB", 8), ("TE", 10), ("RB", 12), ("WR", 12))
    for position, deadline in deadlines:
        required = int(getattr(profile.roster, position.lower()))
        if round_number >= deadline and roster[position] < required:
            return position
    return None


def _roster_candidate_allowed(
    profile: LeagueProfile,
    roster: Counter[str],
    asset: Mapping[str, Any],
) -> bool:
    position = str(asset["position"])
    if position in {"K", "DST"}:
        return roster[position] < int(getattr(profile.roster, position.lower()))
    if position == "QB":
        return roster[position] < max(profile.roster.qb + 1, 2)
    if position == "TE":
        return roster[position] < max(profile.roster.te + 1, 2)
    return roster[position] < profile.draft.rounds


def _roster_need_adjustment(
    profile: LeagueProfile,
    roster: Counter[str],
    round_number: int,
    position: str,
) -> float:
    required = int(getattr(profile.roster, position.lower(), 0))
    if position in {"QB", "RB", "WR", "TE"} and roster[position] < required:
        return -10.0 - round_number
    if position in {"RB", "WR", "TE"}:
        flex_have = sum(roster[value] for value in ("RB", "WR", "TE"))
        flex_need = profile.roster.rb + profile.roster.wr + profile.roster.te + profile.roster.flex
        if flex_have < flex_need:
            return -6.0
    if position in {"QB", "TE"} and roster[position] > required:
        return 18.0
    return float(roster[position]) * 1.5


def _owner_auto_score(
    profile: LeagueProfile,
    roster: Counter[str],
    round_number: int,
    asset: Mapping[str, Any],
) -> float:
    rank = float(asset.get("nwr_rank") or 10_000)
    return rank + _roster_need_adjustment(profile, roster, round_number, str(asset["position"]))


def _fit_penalty(profile: LeagueProfile, roster: Counter[str], position: str) -> float:
    return _roster_need_adjustment(profile, roster, 1, position)


def _roster_fit(profile: LeagueProfile, roster: Counter[str], position: str) -> str:
    required = int(getattr(profile.roster, position.lower(), 0))
    if roster[position] < required:
        return "OPEN STARTER"
    if position in {"RB", "WR", "TE"}:
        flex_have = sum(roster[value] for value in ("RB", "WR", "TE"))
        flex_need = profile.roster.rb + profile.roster.wr + profile.roster.te + profile.roster.flex
        if flex_have < flex_need:
            return "OPEN FLEX"
    return "DEPTH"


def _available_ranked(ranking: RankingResult, state: Mapping[str, Any]) -> list[Any]:
    drafted = {str(value) for value in state.get("drafted", [])}
    return [row for row in ranking.rows if row.player_id not in drafted]


def _rosters(
    profile: LeagueProfile, picks: Sequence[Mapping[str, Any]]
) -> dict[int, list[dict[str, Any]]]:
    rosters: dict[int, list[dict[str, Any]]] = {
        slot: [] for slot in range(1, profile.team_count + 1)
    }
    for pick in picks:
        slot = int(pick["team_slot"])
        rosters[slot].append(
            {
                "pickNumber": int(pick["pick_number"]),
                "playerId": str(pick["player_id"]),
                "playerName": str(pick["player_name"]),
                "position": str(pick["position"]),
                "team": str(pick.get("team") or ""),
            }
        )
    return rosters


def _current_team(profile: LeagueProfile, state: Mapping[str, Any]) -> int | None:
    pick_number = len(state.get("picks", [])) + 1
    order = draft_order(profile)
    return order[pick_number - 1] if pick_number <= len(order) else None


def _next_owner_pick(
    profile: LeagueProfile,
    current_pick: int,
    owner_slot: Any,
) -> int | None:
    if not isinstance(owner_slot, int):
        return None
    order = draft_order(profile)
    return next(
        (
            pick_number
            for pick_number in range(current_pick + 1, len(order) + 1)
            if order[pick_number - 1] == owner_slot
        ),
        None,
    )


def _complete(profile: LeagueProfile, state: Mapping[str, Any]) -> bool:
    return len(state.get("picks", [])) >= profile.team_count * profile.draft.rounds


def _pick_payload(pick: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "pickNumber": int(pick["pick_number"]),
        "round": int(pick["round"]),
        "teamSlot": int(pick["team_slot"]),
        "playerId": str(pick["player_id"]),
        "playerName": str(pick["player_name"]),
        "position": str(pick["position"]),
        "team": str(pick.get("team") or ""),
        "actor": str(pick.get("actor") or ""),
        "selectionBehavior": str(pick.get("selection_behavior") or ""),
        "nwrRank": pick.get("nwr_rank"),
        "pickedAtUtc": str(pick.get("picked_at_utc") or ""),
    }


def _card(label: str, row: Mapping[str, Any], note: str) -> dict[str, Any]:
    return {
        "label": label,
        "playerId": row["playerId"],
        "playerName": row["playerName"],
        "position": row["position"],
        "team": row["team"],
        "nwrRank": row["nwrRank"],
        "nwrView": row["nwrView"],
        "draftTiming": row["draftTiming"],
        "makeItBack": row["makeItBack"],
        "overallTierLabel": row["overallTierLabel"],
        "positionTierLabel": row["positionTierLabel"],
        "rosterFit": row["rosterFit"],
        "note": note,
    }


def _nwr_view(edge: float | None) -> str:
    if edge is None:
        return "ADP UNAVAILABLE"
    if edge >= 24:
        return "STRONG VALUE"
    if edge >= 10:
        return "VALUE"
    if edge <= -24:
        return "STRONG FADE"
    if edge <= -10:
        return "FADE"
    return "ALIGNED"


def _adp_spread(entry: AdpEntry | None) -> float:
    if entry is None:
        return 5.0
    spread = _adp_distribution_spread(entry)
    return max(3.0, min(spread or 6.0, 18.0))


def _adp_distribution_spread(entry: AdpEntry) -> float | None:
    if entry.std_dev is not None:
        return max(entry.std_dev, 1.0)
    if entry.min_pick is not None and entry.max_pick is not None:
        return max((entry.max_pick - entry.min_pick) / 4.0, 1.0)
    return None


def _seeded_unit(seed: int, pick_number: int, player_id: str) -> float:
    digest = hashlib.sha256(f"{seed}:{pick_number}:{player_id}".encode()).digest()
    integer = int.from_bytes(digest[:8], "big")
    return (integer / ((1 << 64) - 1)) * 2.0 - 1.0


def _adp_status(snapshot: AdpSnapshot, ranking_count: int) -> dict[str, Any]:
    source_players = len(snapshot.match_report) or len(snapshot.entries) + len(snapshot.unmatched)
    return {
        "available": snapshot.available,
        "authority": snapshot.authority,
        "provider": snapshot.provider,
        "source": snapshot.source,
        "sourceDate": snapshot.source_date,
        "dateWindow": snapshot.date_window,
        "importedAtUtc": snapshot.imported_at_utc,
        "retrievedAtUtc": snapshot.retrieved_at_utc,
        "sourceSha256": snapshot.source_sha256,
        "endpoint": snapshot.endpoint,
        "providerVersion": snapshot.provider_version,
        "positionFilter": snapshot.position_filter,
        "sampleSize": snapshot.sample_size,
        "freshness": snapshot.freshness,
        "lastRefreshError": snapshot.last_refresh_error,
        "attributionUrl": FFC_ATTRIBUTION_URL if snapshot.provider == "FFC" else "",
        "matchedPlayers": len(snapshot.entries),
        "sourcePlayers": source_players,
        "sourceCoverage": (
            round(len(snapshot.entries) / source_players, 3) if source_players else 0.0
        ),
        "rankingPlayers": ranking_count,
        "coverage": round(len(snapshot.entries) / ranking_count, 3) if ranking_count else 0.0,
        "unmatched": list(snapshot.unmatched),
        "message": (
            "Fantasy Football Calculator ADP is active for market timing; it does not "
            "change NWR rank. Data updates daily at the source."
            if snapshot.available and snapshot.provider == "FFC"
            else "Owner-imported platform ADP is active for market timing; it does not change NWR rank."
            if snapshot.available
            else "ADP unavailable. Import an owner-authorized CSV; NWR does not invent ADP."
        ),
    }


def _adp_document(snapshot: AdpSnapshot) -> dict[str, Any]:
    return {
        "schema_version": ADP_SCHEMA_VERSION,
        "profile_id": snapshot.profile_id,
        "source": snapshot.source,
        "scoring_format": snapshot.scoring_format,
        "team_count": snapshot.team_count,
        "source_date": snapshot.source_date,
        "imported_at_utc": snapshot.imported_at_utc,
        "source_sha256": snapshot.source_sha256,
        "errors": list(snapshot.errors),
        "provider": snapshot.provider,
        "authority": snapshot.authority,
        "position_filter": snapshot.position_filter,
        "sample_size": snapshot.sample_size,
        "date_window": snapshot.date_window,
        "retrieved_at_utc": snapshot.retrieved_at_utc,
        "provider_version": snapshot.provider_version,
        "endpoint": snapshot.endpoint,
        "freshness": snapshot.freshness,
        "last_refresh_error": snapshot.last_refresh_error,
        "entries": [entry.__dict__ for entry in snapshot.entries],
        "unmatched": list(snapshot.unmatched),
        "match_report": list(snapshot.match_report),
        "paste_rows": list(snapshot.paste_rows),
    }


def _adp_path(root: str | Path, profile_id: str) -> Path:
    return Path(root) / "adp_snapshots" / f"{profile_id}.json"


def _ffc_adp_path(root: str | Path, profile_id: str) -> Path:
    return Path(root) / "adp_provider_cache" / "ffc" / f"{profile_id}.json"


def _owner_paste_adp_path(root: str | Path, profile_id: str) -> Path:
    return Path(root) / "adp_provider_cache" / "owner_paste" / f"{profile_id}.json"


def _owner_paste_raw_path(root: str | Path, profile_id: str) -> Path:
    return Path(root) / "adp_provider_cache" / "owner_paste" / f"{profile_id}.md"


def _owner_platform_snapshot_path(root: str | Path) -> Path:
    return Path(root) / "adp_provider_cache" / "owner_platform_snapshot" / "snapshot.json"


def _owner_platform_raw_path(root: str | Path) -> Path:
    return Path(root) / "adp_provider_cache" / "owner_platform_snapshot" / "snapshot.txt"


def _owner_platform_selection_path(root: str | Path, profile_id: str) -> Path:
    return Path(root) / "adp_provider_cache" / "owner_platform_snapshot" / "leagues" / f"{profile_id}.json"


def _detected_platform(profile: LeagueProfile) -> str:
    provider = str(profile.provider or "").strip().lower()
    if provider == "sleeper":
        return "SLEEPER"
    if provider == "espn":
        return "ESPN"
    if provider in {"fantasypros", "fantasy_pros"}:
        return "FANTASYPROS"
    return "CONSENSUS"


def _owner_platform_selection(root: str | Path, profile: LeagueProfile) -> tuple[str, bool]:
    selection = "AUTO"
    path = _owner_platform_selection_path(root, profile.profile_id)
    if path.is_file():
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
            candidate = str(document.get("selection") or "AUTO").upper()
            if candidate in OWNER_PLATFORM_SELECTIONS:
                selection = candidate
        except (OSError, ValueError, json.JSONDecodeError):
            selection = "AUTO"
    return (_detected_platform(profile) if selection == "AUTO" else selection, selection == "AUTO")


def set_owner_platform_selection(root: str | Path, profile: LeagueProfile, selection: str) -> None:
    normalized = str(selection or "").strip().upper()
    if normalized not in OWNER_PLATFORM_SELECTIONS:
        raise RedraftValidationError("Select Auto, Consensus, Sleeper, ESPN, FantasyPros, or Disabled/use FFC.")
    if not _owner_platform_snapshot_path(root).is_file():
        raise RedraftValidationError("Save one global owner platform snapshot before selecting a league column.")
    _atomic_json(_owner_platform_selection_path(root, profile.profile_id), {
        "profile_id": profile.profile_id,
        "selection": normalized,
        "updated_at_utc": utc_now(),
    })


def clear_owner_platform_selection(root: str | Path, profile: LeagueProfile) -> None:
    path = _owner_platform_selection_path(root, profile.profile_id)
    if path.is_file():
        path.unlink()


def _save_owner_platform_snapshot(
    root: str | Path,
    profile: LeagueProfile,
    snapshot: AdpSnapshot,
    rows: Sequence[Mapping[str, Any]],
    paste_text: str,
    *,
    source_label: str,
    parser_mode: str,
    platform_coverage: Mapping[str, Any],
    active: bool,
) -> None:
    path = _owner_platform_snapshot_path(root)
    document = {
        "schema_version": 1,
        "active": active,
        "source_label": source_label,
        "parser_mode": parser_mode,
        "rows": [dict(row) for row in rows],
        "scoring_format": snapshot.scoring_format,
        "year": profile.season,
        "team_count": profile.team_count,
        "imported_at_utc": snapshot.imported_at_utc,
        "source_date": snapshot.source_date,
        "raw_hash": snapshot.source_sha256,
        "row_count": len(rows),
        "match_report": list(snapshot.match_report),
        "unmatched": list(snapshot.unmatched),
        "platform_coverage": dict(platform_coverage),
    }
    _atomic_json(path, document)
    raw_path = _owner_platform_raw_path(root)
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_text(paste_text, encoding="utf-8", newline="")


def _load_owner_platform_snapshot(root: str | Path, profile: LeagueProfile) -> AdpSnapshot | None:
    path = _owner_platform_snapshot_path(root)
    if not path.is_file():
        return None
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
        if not bool(document.get("active")):
            return None
        selected, automatic = _owner_platform_selection(root, profile)
        if selected == "DISABLED":
            return None
        rows = [dict(row) for row in document.get("rows", []) if isinstance(row, Mapping)]
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return None
    entries: list[AdpEntry] = []
    unmatched: list[str] = [str(value) for value in document.get("unmatched", [])]
    report = [dict(value) for value in document.get("match_report", []) if isinstance(value, Mapping)]
    seen: set[str] = set()
    for row in rows:
        player_id = str(row.get("matched_nwr_player_id") or "")
        if not player_id or str(row.get("match_status") or "") != "MATCHED" or player_id in seen:
            continue
        selected_value = _paste_number(row.get(f"{selected.lower()}_adp"))
        origin = selected
        if selected_value is None and selected != "CONSENSUS":
            selected_value = _paste_number(row.get("consensus_adp"))
            origin = "CONSENSUS"
        if selected_value is None:
            unmatched.append(f"{row.get('player_name') or player_id}: missing {selected.title()} and Consensus ADP")
            continue
        seen.add(player_id)
        row["active_selected_source"] = origin
        entries.append(AdpEntry(
            player_id=player_id,
            player=str(row.get("matched_nwr_player_name") or row.get("player_name") or ""),
            team=str(row.get("matched_nwr_team") or ""),
            position=str(row.get("position") or ""),
            overall_adp=selected_value,
            expected_pick=selected_value,
            min_pick=None,
            max_pick=None,
            std_dev=None,
            source_player_id=f"owner-platform:{row.get('source_row_index') or player_id}",
            expected_round=max(1, math.ceil(selected_value / profile.team_count)),
            match_status="MATCHED",
            match_confidence=str(row.get("match_confidence") or "HIGH"),
        ))
    if not entries:
        return None
    entries.sort(key=lambda entry: (entry.expected_pick, entry.player_id))
    source_label = str(document.get("source_label") or "Owner platform rankings")
    display = f"Owner-imported {selected.title()} ADP"
    provider = f"OWNER_PLATFORM_{'AUTO_' if automatic else ''}{selected}"
    return AdpSnapshot(
        profile_id=profile.profile_id,
        source=f"{display} — {source_label}",
        scoring_format=str(document.get("scoring_format") or _profile_scoring(profile)),
        team_count=profile.team_count,
        source_date=str(document.get("source_date") or ""),
        imported_at_utc=str(document.get("imported_at_utc") or ""),
        source_sha256=str(document.get("raw_hash") or ""),
        entries=tuple(entries),
        unmatched=tuple(dict.fromkeys(unmatched)),
        provider=provider,
        authority="OWNER-IMPORTED PLATFORM ADP / MARKET TIMING",
        retrieved_at_utc=str(document.get("imported_at_utc") or ""),
        provider_version="NWR_OWNER_PLATFORM_SNAPSHOT_V1",
        freshness="FRESH",
        match_report=tuple(report),
        paste_rows=tuple(rows),
    )


def _merge_owner_platform_fallback(owner: AdpSnapshot, ffc: AdpSnapshot) -> AdpSnapshot:
    existing = owner.by_player_id
    entries = list(owner.entries)
    entries.extend(entry for entry in ffc.entries if entry.player_id not in existing)
    return replace(owner, entries=tuple(sorted(entries, key=lambda entry: (entry.expected_pick, entry.player_id))))


def owner_platform_snapshot_status(root: str | Path, profile: LeagueProfile | None = None) -> dict[str, Any]:
    path = _owner_platform_snapshot_path(root)
    if not path.is_file():
        return {"available": False, "active": False, "parserMode": "", "rowCount": 0, "platformCoverage": {}, "sourceLabel": "", "rawHash": "", "importedAtUtc": "", "leagueSelection": "", "detectedPlatform": ""}
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError):
        return {"available": False, "active": False, "parserMode": "", "rowCount": 0, "platformCoverage": {}, "sourceLabel": "", "rawHash": "", "importedAtUtc": "", "leagueSelection": "", "detectedPlatform": ""}
    selected, automatic = _owner_platform_selection(root, profile) if profile else ("", False)
    return {
        "available": bool(document.get("rows")), "active": bool(document.get("active")),
        "parserMode": str(document.get("parser_mode") or ""), "rowCount": int(document.get("row_count") or 0),
        "matchedRows": sum(1 for row in document.get("rows", []) if isinstance(row, Mapping) and row.get("match_status") == "MATCHED"),
        "platformCoverage": _normalized_platform_coverage(document.get("platform_coverage")), "sourceLabel": str(document.get("source_label") or ""),
        "rawHash": str(document.get("raw_hash") or ""), "importedAtUtc": str(document.get("imported_at_utc") or ""),
        "leagueSelection": ("AUTO" if automatic else selected), "detectedPlatform": _detected_platform(profile) if profile else "",
        "activeColumn": selected,
    }


def _paste_selected_source(value: str) -> str:
    selected = str(value or "").strip().upper().replace(" ", "")
    if selected not in PASTE_PLATFORM_COLUMNS:
        raise RedraftValidationError("Select Consensus, Sleeper, ESPN, or FantasyPros ADP.")
    return selected


def _paste_table_rows(paste_text: str) -> list[dict[str, str]]:
    lines = [line.strip() for line in paste_text.replace("\r\n", "\n").split("\n") if "|" in line]
    if len(lines) < 2:
        return []
    header = _paste_cells(lines[0])
    canonical = [_paste_header(value) for value in header]
    if "position" not in canonical or "player" not in canonical:
        return []
    rows: list[dict[str, str]] = []
    for line in lines[1:]:
        cells = _paste_cells(line)
        if not cells or all(re.fullmatch(r"[:\- ]+", value or "") for value in cells):
            continue
        if len(cells) != len(canonical):
            continue
        row = {key: value for key, value in zip(canonical, cells) if key}
        if row:
            rows.append(row)
    return rows


def _owner_platform_rows(paste_text: str) -> tuple[list[dict[str, str]], str, list[str]]:
    markdown_rows = _paste_table_rows(paste_text)
    if markdown_rows:
        return markdown_rows, "MARKDOWN_TABLE", []
    plain_rows, warnings = _plain_text_platform_rows(paste_text)
    return plain_rows, "PLAIN_TEXT_BLOCK", warnings


def _plain_text_platform_rows(paste_text: str) -> tuple[list[dict[str, str]], list[str]]:
    lines = [re.sub(r"\*+", "", value).strip() for value in paste_text.replace("\r\n", "\n").split("\n")]
    lines = [value for value in lines if value]
    rows: list[dict[str, str]] = []
    warnings: list[str] = []
    index = 0
    while index < len(lines):
        combined = _plain_position(lines[index])
        consumed = 1
        if combined is None and index + 1 < len(lines):
            maybe_position = _normalized_position(lines[index])
            if maybe_position in {"QB", "RB", "WR", "TE", "K", "DST"} and re.fullmatch(r"\d+", lines[index + 1]):
                combined = f"{maybe_position}{lines[index + 1]}"
                consumed = 2
        if combined is None:
            index += 1
            continue
        player_index = index + consumed
        values_index = player_index + 1
        if values_index >= len(lines):
            warnings.append(f"plain-text row near line {index + 1}: missing player or ADP values")
            break
        values = lines[values_index].replace(",", "").split()
        if len(values) < 1 or len(values) > 4:
            warnings.append(f"plain-text row near line {index + 1}: expected 1–4 ADP values after player name")
            index += consumed
            continue
        rows.append({
            "position": combined,
            "player": lines[player_index],
            "consensus": values[0] if len(values) > 0 else "",
            "sleeper": values[1] if len(values) > 1 else "",
            "espn": values[2] if len(values) > 2 else "",
            "fantasypros": values[3] if len(values) > 3 else "",
        })
        index = values_index + 1
    return rows, warnings


def _plain_position(value: str) -> str | None:
    match = re.fullmatch(r"\s*(QB|RB|WR|TE|K|DST|D/ST)\s*(\d+)\s*", value, re.I)
    return f"{_normalized_position(match.group(1))}{match.group(2)}" if match else None


def _platform_coverage(rows: Sequence[Mapping[str, Any]]) -> dict[str, dict[str, int]]:
    total = len(rows)
    return {
        source: {"available": sum(1 for row in rows if _paste_number(row.get(f"{source}_adp")) is not None), "total": total}
        for source in ("consensus", "sleeper", "espn", "fantasypros")
    }


def _normalized_platform_coverage(value: object) -> dict[str, dict[str, int]]:
    raw = value if isinstance(value, Mapping) else {}
    coverage: dict[str, dict[str, int]] = {}
    for source in ("consensus", "sleeper", "espn", "fantasypros"):
        candidate = raw.get(source) or raw.get(source.upper()) or raw.get(source.title()) or {}
        if isinstance(candidate, Mapping):
            coverage[source] = {
                "available": int(candidate.get("available") or 0),
                "total": int(candidate.get("total") or 0),
            }
        else:
            coverage[source] = {"available": 0, "total": 0}
    return coverage


def _paste_cells(line: str) -> list[str]:
    stripped = line.strip().strip("|")
    return [re.sub(r"\*+", "", value).strip() for value in stripped.split("|")]


def _paste_header(value: str) -> str:
    compact = re.sub(r"[^a-z0-9]", "", value.lower())
    if compact in {"position", "pos", "rank"}:
        return "position"
    if compact in {"player", "name", "playername"}:
        return "player"
    return PASTE_COLUMN_ALIASES.get(
        compact, PASTE_COLUMN_ALIASES.get(value.strip().lower(), "")
    ).lower()


def _paste_position(value: str) -> tuple[int | None, str]:
    match = re.fullmatch(r"\s*(QB|RB|WR|TE|K|DST|D/ST)\s*(\d+)?\s*", str(value or ""), re.I)
    if not match:
        return None, ""
    return (int(match.group(2)) if match.group(2) else None, _normalized_position(match.group(1)))


def _paste_number(value: object) -> float | None:
    raw = str(value or "").strip().replace(",", "")
    if raw in {"", "-", "—", "–", "N/A", "NA"}:
        return None
    try:
        parsed = float(raw)
    except ValueError:
        return None
    return round(parsed, 2) if math.isfinite(parsed) and parsed > 0 else None


def _profile_scoring(profile: LeagueProfile) -> str:
    if profile.scoring.reception == 1:
        return "PPR"
    if profile.scoring.reception == 0.5:
        return "HALF_PPR"
    return "STANDARD"


def _normalized_scoring(value: str) -> str:
    normalized = re.sub(r"[^A-Z0-9]+", "_", value.strip().upper()).strip("_")
    aliases = {"HALF": "HALF_PPR", "HALF_POINT_PPR": "HALF_PPR", "STD": "STANDARD"}
    return aliases.get(normalized, normalized)


def _normalized_name(value: str) -> str:
    ascii_value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]", "", ascii_value.lower())


def _normalized_name_without_suffix(value: str) -> str:
    words = re.sub(r"[^a-z0-9 ]+", " ", unicodedata.normalize("NFKD", value)
                   .encode("ascii", "ignore").decode("ascii").lower()).split()
    while words and words[-1] in {"jr", "sr", "ii", "iii", "iv", "v"}:
        words.pop()
    return "".join(words)


def _normalized_position(value: str) -> str:
    normalized = value.strip().upper()
    return {"PK": "K", "DEF": "DST", "D/ST": "DST", "D": "DST"}.get(normalized, normalized)


def _normalized_team(value: str) -> str:
    normalized = re.sub(r"[^A-Z0-9]", "", value.strip().upper())
    aliases = {
        "ARZ": "ARI",
        "JAC": "JAX",
        "KAN": "KC",
        "LVR": "LV",
        "NOR": "NO",
        "NWE": "NE",
        "SFO": "SF",
        "TAM": "TB",
        "WSH": "WAS",
        "LA": "LAR",
    }
    return aliases.get(normalized, normalized)


def _positive_float(value: str, line_number: int, field: str) -> float:
    try:
        number = float(value)
    except ValueError as exc:
        raise RedraftValidationError(f"ADP line {line_number} {field} is invalid.") from exc
    if not math.isfinite(number) or number <= 0:
        raise RedraftValidationError(f"ADP line {line_number} {field} must be positive.")
    return number


def _optional_positive_float(value: str, line_number: int, field: str) -> float | None:
    return _positive_float(value, line_number, field) if value else None


def _manual_id(row: Mapping[str, Any]) -> str:
    return str(row.get("player_id") or row.get("playerId") or "")


def _unknown_asset(player_id: str) -> dict[str, Any]:
    return {
        "player_id": player_id,
        "player_name": "Unknown legacy player",
        "position": "",
        "team": "",
        "nwr_rank": None,
    }
