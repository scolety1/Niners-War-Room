"""Deterministic Redraft Draft Room, owner ADP boundary, and mock behavior.

NWR rankings remain the player-value authority. ADP is optional market-timing
context. CPU selections use admitted ADP when present and otherwise disclose a
deterministic NWR-order fallback. Sleeper events are accepted read-only; this
module contains no platform write client.
"""

from __future__ import annotations

import csv
import difflib
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
    *,
    root: str | Path | None = None,
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
    aliases = _load_owner_platform_manual_matches(root) if root is not None else {}
    parsed_rows: list[dict[str, Any]] = []
    entries: list[AdpEntry] = []
    unmatched: list[str] = []
    warnings: list[str] = list(parser_warnings)
    report: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for source_index, row in enumerate(rows, start=1):
        position_rank, position = _paste_position(row.get("position", ""))
        player = str(row.get("player") or "").strip()
        source_team = _normalized_team(str(row.get("team") or ""))
        selected_value = _paste_number(row.get(selected.lower(), ""))
        raw_row = "|".join(str(row.get(key, "")) for key in ("position", "player", "consensus", "sleeper", "espn", "fantasypros"))
        receipt = {
            "source_row_index": source_index,
            "position_rank": position_rank,
            "position": position,
            "positional_adp_rank": position_rank,
            "player_name": player,
            "source_team": source_team,
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
        alias = aliases.get(_manual_match_key(player, position))
        matched = next((asset for asset in assets if alias and asset["player_id"] == alias.get("selected_nwr_player_id") and asset["position"] == position), None)
        if matched is not None:
            method, confidence, reason = "OWNER_APPROVED", "OWNER", ""
        else:
            matched, method, confidence, reason = _match_adp_player(player, position, source_team, assets)
        if matched is None:
            unmatched.append(f"row {source_index}: {player} ({position})")
            warnings.append(f"row {source_index}: {player} not safely matched ({reason})")
            receipt["match_status"] = "UNMATCHED"
            receipt["unmatched_reason"] = _classify_owner_platform_gap(player, position, reason, assets)
            receipt["candidate_suggestions"] = _owner_platform_candidates(player, position, assets)
            parsed_rows.append(receipt)
            report.append(_match_report_row("", player, position, "", None, "UNMATCHED", "", receipt["unmatched_reason"]))
            continue
        matched_id = str(matched["player_id"])
        if matched_id in seen_ids:
            warnings.append(f"row {source_index}: duplicate safe match for {matched['player_name']}")
            receipt["match_status"] = "DUPLICATE_MATCH"
            parsed_rows.append(receipt)
            continue
        seen_ids.add(matched_id)
        receipt.update({"match_status": "MATCHED", "matched_nwr_player_id": matched_id, "matched_nwr_player_name": str(matched["player_name"]), "matched_nwr_team": str(matched["team"]), "match_method": method, "match_confidence": confidence, "match_source": "OWNER_APPROVED" if method == "OWNER_APPROVED" else "AUTOMATIC"})
        parsed_rows.append(receipt)
        entries.append(AdpEntry(player_id=matched_id, player=str(matched["player_name"]), team=str(matched["team"]), position=str(matched["position"]), overall_adp=match_value, expected_pick=match_value, min_pick=None, max_pick=None, std_dev=None, source_player_id=f"paste:{source_index}", expected_round=max(1, math.ceil(match_value / profile.team_count)), match_status="MATCHED", match_confidence=confidence))
        report.append(_match_report_row("", player, position, "", matched, method, confidence, ""))
    # A zero-match preview is still useful: it is the owner’s safe review queue.
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
    preview = preview_owner_paste_adp(profile, ranking, paste_text, selected_source, manual_assets, root=root)
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

    name_any_position = [
        row for row in assets if _normalized_name(row["player_name"]) == exact_name
    ]
    if name_any_position:
        return None, "", "", "POSITION_MISMATCH"

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
    core_any_position = [
        row for row in assets
        if _normalized_name_without_suffix(row["player_name"]) == core_name
    ]
    if core_any_position:
        return None, "", "", "POSITION_MISMATCH" if not core_matches else "AMBIGUOUS_NAME"
    return None, "", "", "NO_SAFE_IDENTITY_MATCH" if not core_matches else "AMBIGUOUS_NAME"


_UDK_REQUIRED_COLUMNS = (
    "Name", "Position", "Team", "Bye Week", "Rank", "Points", "Risk", "Upside",
    "ADP", "Tier", "Outlook", "Dynasty", "Markers",
)
_UDK_SUPPORTED_POSITIONS = frozenset({"QB", "RB", "WR", "TE", "K", "DST"})


def _udk_number(value: str) -> float | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _udk_dynasty_locked(value: str) -> bool:
    text = str(value or "")
    return "unlock" in text.lower() or "udk+" in text.lower()


def parse_udk_position_csv(
    profile: LeagueProfile,
    ranking: RankingResult,
    csv_text: str,
    manual_assets: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    """Parse the owner's real UDK ("Position Rankings — Fantasy Footballers
    Podcast") CSV export -- a genuine, documented schema (Name, Position,
    Team, Bye Week, Rank, Points, Risk, Upside, ADP, Tier, Outlook,
    Dynasty, Markers), NOT a full-position provider: a single export may
    legitimately cover only one position (the owner's own file is 36
    rows, all QB). Positions actually present are read from each row's
    own Position column, never assumed or invented for positions the
    file does not contain.

    Reuses the exact existing owner-paste matching machinery
    (_matching_assets / _match_adp_player) to attach real canonical NWR
    player IDs so Draft/Queue works directly from a UDK row -- never a
    second, disconnected identity space.

    ADP is preserved as an OPAQUE STRING, never parsed as a number or
    reinterpreted as this league's own round.pick: the source file
    discloses no team count, and values like "2.06" are UDK's own
    round.pick-style notation from an unknown/unverified source league
    size (never our own conversion, never sorted numerically).

    `Dynasty` is detected as locked upsell text ("Unlock with the 2026
    UDK+...") and stored as dynasty_locked=True with no numeric rating
    invented from it. `Markers` (Mark Drafted / Mark Keeper / Mark
    Favorite / Mark Watchlist / Mark Avoid) is UI action text, not player
    state -- it is discarded entirely, never ingested as a boolean flag.
    """
    if not csv_text.strip() or len(csv_text.encode("utf-8")) > 4_000_000:
        raise RedraftValidationError("UDK CSV must be non-empty and no larger than 4 MB.")
    try:
        reader = csv.DictReader(io.StringIO(csv_text))
        rows = list(reader)
    except csv.Error as exc:
        raise RedraftValidationError("UDK CSV could not be parsed.") from exc
    if reader.fieldnames is None or set(_UDK_REQUIRED_COLUMNS) - set(reader.fieldnames):
        raise RedraftValidationError(
            "UDK CSV is missing required columns "
            f"({', '.join(_UDK_REQUIRED_COLUMNS)})."
        )
    assets = _matching_assets(ranking, manual_assets)
    by_position: dict[str, list[dict[str, Any]]] = {}
    unmatched: list[str] = []
    warnings: list[str] = []
    matched_count = 0
    for source_index, row in enumerate(rows, start=1):
        player = str(row.get("Name") or "").strip()
        position = _normalized_position(str(row.get("Position") or ""))
        team = _normalized_team(str(row.get("Team") or ""))
        if not player or position not in _UDK_SUPPORTED_POSITIONS:
            warnings.append(f"row {source_index}: missing or unsupported position ({row.get('Position')!r})")
            continue
        matched, method, confidence, reason = _match_adp_player(player, position, team, assets)
        entry = {
            "playerId": str(matched["player_id"]) if matched else None,
            "playerName": str(matched["player_name"]) if matched else player,
            "team": str(matched["team"]) if matched else team,
            "position": position,
            "byeWeek": str(row.get("Bye Week") or ""),
            "rank": int(_udk_number(row.get("Rank", "")) or 0) or None,
            "points": _udk_number(row.get("Points", "")),
            "risk": _udk_number(row.get("Risk", "")),
            "upside": _udk_number(row.get("Upside", "")),
            "adpRaw": str(row.get("ADP") or ""),
            "tier": int(_udk_number(row.get("Tier", "")) or 0) or None,
            "outlook": str(row.get("Outlook") or ""),
            "dynastyLocked": _udk_dynasty_locked(str(row.get("Dynasty") or "")),
            "matchStatus": "MATCHED" if matched else "UNMATCHED",
            "matchMethod": method if matched else "",
            "matchConfidence": confidence if matched else "",
        }
        by_position.setdefault(position, []).append(entry)
        if matched:
            matched_count += 1
        else:
            unmatched.append(f"row {source_index}: {player} ({position}) — {reason}")
            warnings.append(f"row {source_index}: {player} not safely matched to an NWR player ({reason})")
    if not by_position:
        raise RedraftValidationError(
            "No UDK rows matched a supported position. Check the CSV's Position column."
        )
    # NWR class-time hardening, section 7: the directive's own required preview
    # fields (per-position counts, duplicate detection) alongside the pre-
    # existing matched/unmatched/warnings -- a duplicate is two source rows in
    # THIS SAME import resolving to the same real NWR playerId (a real, owner-
    # visible data-quality signal the prior preview never surfaced).
    per_position_counts = {position: len(entries) for position, entries in by_position.items()}
    duplicate_rows: list[str] = []
    for position, entries in by_position.items():
        first_name_by_id: dict[str, str] = {}
        occurrences: dict[str, int] = {}
        for entry in entries:
            player_id = entry.get("playerId")
            if not player_id:
                continue
            occurrences[player_id] = occurrences.get(player_id, 0) + 1
            first_name_by_id.setdefault(player_id, entry["playerName"])
        for player_id, count in occurrences.items():
            if count > 1:
                duplicate_rows.append(
                    f"{position}: {first_name_by_id[player_id]} (playerId={player_id}) "
                    f"appears {count} times in this import"
                )
    return {
        "positions": by_position,
        "sourceRows": len(rows),
        "matchedRows": matched_count,
        "unmatched": unmatched,
        "warnings": warnings,
        "sourceSha256": hashlib.sha256(csv_text.encode("utf-8")).hexdigest(),
        "perPositionCounts": per_position_counts,
        "duplicateRows": duplicate_rows,
    }


def parse_udk_position_pdf(
    profile: LeagueProfile,
    ranking: RankingResult,
    pdf_bytes: bytes,
    manual_assets: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    """Parse a PDF export of the owner's UDK ("Position Rankings — Fantasy
    Footballers Podcast") product -- the Fantasy Footballers sell the same
    Ultimate Draft Kit data in both CSV and PDF form; only the CSV path
    has ever been exercised against a real owner file (`parse_udk_position_csv`,
    the owner's real 36-row QB file). NWR post-draft overnight, section 14.

    NO REAL BALLERS/UDK PDF SAMPLE HAS EVER BEEN SEEN BY THIS PIPELINE.
    This function's PDF-table-extraction step is built and tested against
    a representative FIXTURE PDF this session generated (same documented
    column schema as the real CSV: Name, Position, Team, Bye Week, Rank,
    Points, Risk, Upside, ADP, Tier, Outlook, Dynasty, Markers) -- a
    reasonable assumption given it is the same underlying UDK dataset in
    a different export format, but NOT a verified match to the real
    product's actual PDF layout (column order, page breaks, header/footer
    noise, multi-table-per-page splits are all real unknowns until an
    actual owner PDF is seen). See
    `test_parse_udk_position_pdf_against_a_real_owner_sample` in the
    paired test file for the one test explicitly marked
    BLOCKED_PENDING_OWNER_SAMPLE -- that gap is in the SAMPLE, not in
    this function, which is otherwise fully built and tested.

    Design: extracts each page's table(s) via pdfplumber, re-serializes
    them as CSV text using the exact same header contract
    `parse_udk_position_csv` already requires, and delegates every real
    parsing/matching/validation rule (position support, ADP-as-opaque-
    string, Dynasty-locked detection, Markers-discarded, owner-identity
    matching) to that already-tested function -- this file adds ONLY the
    PDF-to-table-text extraction step, never a second, parallel matching
    implementation that could silently drift from the CSV path's rules.
    """
    if not pdf_bytes:
        raise RedraftValidationError("UDK PDF must be non-empty.")
    if len(pdf_bytes) > 20_000_000:
        raise RedraftValidationError("UDK PDF must be no larger than 20 MB.")
    try:
        import pdfplumber
    except ImportError as exc:  # pragma: no cover -- pdfplumber is a real, pinned dependency
        raise RedraftValidationError(
            "UDK PDF import requires the pdfplumber dependency, which is not installed."
        ) from exc
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            tables: list[list[list[str | None]]] = []
            for page in pdf.pages:
                tables.extend(page.extract_tables())
    except Exception as exc:
        raise RedraftValidationError(f"UDK PDF could not be read: {exc}") from exc
    if not tables:
        raise RedraftValidationError(
            "No table was found in the UDK PDF. This parser expects a real, "
            "extractable table (the same rows a real Fantasy Footballers UDK PDF "
            "export carries) -- an image-only/scanned PDF is not supported."
        )
    header: list[str] | None = None
    body_rows: list[list[str]] = []
    for table in tables:
        if not table:
            continue
        candidate_header = [str(cell or "").strip() for cell in table[0]]
        if set(_UDK_REQUIRED_COLUMNS) <= set(candidate_header):
            if header is None:
                header = candidate_header
            elif header != candidate_header:
                # A later page repeats the header row (common in multi-page
                # PDF exports) -- reuse the first header, skip the repeat.
                pass
            body_rows.extend([str(cell or "") for cell in row] for row in table[1:])
        elif header is not None:
            # A continuation table on a later page with no repeated header
            # row -- assume it's more body rows in the same column order.
            body_rows.extend([str(cell or "") for cell in row] for row in table)
    if header is None:
        raise RedraftValidationError(
            "UDK PDF is missing required columns "
            f"({', '.join(_UDK_REQUIRED_COLUMNS)}) -- no table header matched the "
            "known UDK schema."
        )
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(header)
    writer.writerows(body_rows)
    csv_text = buffer.getvalue()
    result = parse_udk_position_csv(profile, ranking, csv_text, manual_assets)
    # Real provenance: hash the actual PDF bytes the owner uploaded, not
    # the intermediate CSV text this function derived from them.
    result["sourceSha256"] = hashlib.sha256(pdf_bytes).hexdigest()
    result["sourceFormat"] = "PDF"
    return result


UDK_MAX_HISTORY_VERSIONS = 5


def _persist_udk_preview(
    root: str | Path, profile: LeagueProfile, preview: dict[str, Any]
) -> dict[str, Any]:
    """Shared persistence for a UDK preview, however it was parsed (CSV or
    PDF) -- merges additively into any prior import for this profile so
    importing a QB-only file does not erase a previously-imported RB
    file. Provenance (provider, imported_at, source hash, source format)
    travels with every position bucket so the UI can always disclose
    "UDK, imported <time>" distinct from NWR's own rankings.

    NWR class-time hardening, section 7: activation now keeps a real,
    bounded version history PER POSITION (the directive's own "versioned
    local/private artifact... allow rollback" requirement) -- before a
    position's active snapshot is overwritten, it is pushed onto that
    position's own `history` list (newest first, capped at
    `UDK_MAX_HISTORY_VERSIONS`), so `rollback_udk_position_rankings` can
    restore it. A position with no prior import has no history to push;
    the first real activation for a position never has anything to roll
    back to, which is the correct, honest behavior."""
    path = _udk_rankings_path(root, profile.profile_id)
    existing: dict[str, Any] = {}
    try:
        if path.exists():
            existing = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError):
        existing = {}
    positions = dict(existing.get("positions") or {})
    imported_at = datetime.now(UTC).isoformat()
    for position, entries in preview["positions"].items():
        previous = positions.get(position)
        history = list(previous.get("history") or []) if previous else []
        if previous is not None:
            previous_without_history = {k: v for k, v in previous.items() if k != "history"}
            history = ([previous_without_history] + history)[:UDK_MAX_HISTORY_VERSIONS]
        positions[position] = {
            "entries": entries,
            "provider": "Fantasy Footballers Podcast UDK",
            "importedAtUtc": imported_at,
            "sourceSha256": preview["sourceSha256"],
            "sourceFormat": preview.get("sourceFormat", "CSV"),
            "sourceRows": len(entries),
            "history": history,
        }
    document = {"profileId": profile.profile_id, "positions": positions}
    try:
        _atomic_json(path, document)
    except OSError as exc:
        raise RedraftPersistenceError("UDK rankings could not be saved.") from exc
    return {
        "positions": sorted(preview["positions"].keys()),
        "sourceRows": preview["sourceRows"],
        "matchedRows": preview["matchedRows"],
        "unmatched": preview["unmatched"],
        "warnings": preview["warnings"],
        "importedAtUtc": imported_at,
        "perPositionCounts": preview.get("perPositionCounts", {}),
        "duplicateRows": preview.get("duplicateRows", []),
    }


def rollback_udk_position_rankings(
    root: str | Path, profile_id: str, position: str
) -> dict[str, Any]:
    """Restores the most recent prior version of ONE position's UDK
    import, per the directive's real "allow rollback to previous
    version" requirement. Raises `RedraftValidationError` (never
    silently no-ops) if that position has no import at all, or has no
    history to roll back to (e.g. its only real import so far)."""
    normalized_position = _normalized_position(position)
    path = _udk_rankings_path(root, profile_id)
    try:
        document = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise RedraftPersistenceError("UDK rankings could not be read.") from exc
    positions = dict(document.get("positions") or {})
    current = positions.get(normalized_position)
    if current is None:
        raise RedraftValidationError(f"No UDK import exists for position {normalized_position!r}.")
    history = list(current.get("history") or [])
    if not history:
        raise RedraftValidationError(
            f"No earlier UDK version exists for position {normalized_position!r} to roll back to."
        )
    restored, remaining_history = history[0], history[1:]
    positions[normalized_position] = {**restored, "history": remaining_history}
    document = {"profileId": profile_id, "positions": positions}
    try:
        _atomic_json(path, document)
    except OSError as exc:
        raise RedraftPersistenceError("UDK rankings could not be saved.") from exc
    return {
        "position": normalized_position,
        "restoredImportedAtUtc": restored.get("importedAtUtc", ""),
        "restoredSourceSha256": restored.get("sourceSha256", ""),
        "remainingHistoryCount": len(remaining_history),
    }


def save_udk_position_rankings(
    root: str | Path,
    profile: LeagueProfile,
    ranking: RankingResult,
    csv_text: str,
    manual_assets: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    """Parse + persist a UDK CSV import -- see `_persist_udk_preview`."""
    preview = parse_udk_position_csv(profile, ranking, csv_text, manual_assets)
    return _persist_udk_preview(root, profile, preview)


def save_udk_position_pdf_rankings(
    root: str | Path,
    profile: LeagueProfile,
    ranking: RankingResult,
    pdf_bytes: bytes,
    manual_assets: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    """Parse + persist a UDK PDF import -- see `parse_udk_position_pdf`'s
    docstring for the real, disclosed BLOCKED_PENDING_OWNER_SAMPLE
    limitation, and `_persist_udk_preview` for the shared persistence
    this shares with the CSV path (same storage, same merge behavior,
    same UI-facing shape)."""
    preview = parse_udk_position_pdf(profile, ranking, pdf_bytes, manual_assets)
    return _persist_udk_preview(root, profile, preview)


def load_udk_rankings(root: str | Path, profile_id: str) -> dict[str, Any]:
    """Returns `positions` as a LIST of `{position, entries, ...}` objects
    -- never a dict keyed by position string. A dict keyed by real
    position codes ("QB", "RB") would be silently mangled by the shared
    camelCase JSON key transform every facade payload passes through
    (public_json_value(), which camelCases every dict key it sees,
    turning "QB" into "qB") -- a real, verified bug caught by rendering
    this against the live desktop API, not merely unit-tested. The
    on-disk cache file itself is still stored keyed by position (an
    internal convenience for additive merge-on-import in
    save_udk_position_rankings); this function is the one conversion
    point to the list shape every consumer actually reads.

    NWR class-time hardening, section 7: each position's real, on-disk
    `history` (full prior snapshots, each with its own `entries`) is
    deliberately NOT included in this payload -- every live consumer
    (Suggestions/Rankings/Cheat Sheets/Compare/Player Drawer/K-DST
    fallback) only ever needs the CURRENT active version, and shipping
    every prior version's full entry list on every load would bloat the
    payload for no consumer that reads it. Only a real `historyCount`
    (how many versions are available to roll back to) is exposed."""
    path = _udk_rankings_path(root, profile_id)
    positions_by_key: dict[str, Any] = {}
    if path.exists():
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
            positions_by_key = dict(document.get("positions") or {})
        except (OSError, ValueError, json.JSONDecodeError):
            positions_by_key = {}
    positions = [
        {
            "position": position,
            **{k: v for k, v in snapshot.items() if k != "history"},
            "historyCount": len(snapshot.get("history") or ()),
        }
        for position, snapshot in sorted(positions_by_key.items())
    ]
    return {"positions": positions}


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
    violation = _roster_limit_violation(profile, state, owner_slot, asset)
    if violation is not None:
        raise RedraftValidationError(violation)
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


def _pick_slot_or_raise(state: Mapping[str, Any], pick_number: int) -> dict[str, Any]:
    picks = state.get("picks", [])
    if not isinstance(pick_number, int) or not (1 <= pick_number <= len(picks)):
        raise RedraftValidationError(f"Pick {pick_number} does not exist in this draft room.")
    return dict(picks[pick_number - 1])


def _apply_pick_correction(
    state: Mapping[str, Any],
    *,
    pick_number: int,
    asset: Mapping[str, Any] | None,
    action: str,
) -> dict[str, Any]:
    """Shared mechanism for REPLACE PICK / CLEAR PICK / FILL GAP: mutate
    exactly one existing pick slot in place. pick_number, round, and
    team_slot never change, and every other slot's record is untouched --
    no later pick is renumbered or displaced. The prior snapshot of the
    slot is kept in state["last_correction"] so undo_pick_correction can
    reverse only this one action, independent of undo_room_pick's
    separate global-LIFO "undo the latest recorded pick" semantics."""
    picks = list(state.get("picks", []))
    index = pick_number - 1
    previous_snapshot = dict(picks[index])
    if asset is not None:
        player_id = str(asset["player_id"])
        collision = next(
            (
                pick
                for i, pick in enumerate(picks)
                if i != index and str(pick.get("player_id") or "") == player_id
            ),
            None,
        )
        if collision is not None:
            raise RedraftValidationError(
                f"{asset.get('player_name', player_id)} is already drafted at pick "
                f"{collision['pick_number']}."
            )
        new_entry = {
            **previous_snapshot,
            "player_id": player_id,
            "player_name": str(asset["player_name"]),
            "position": str(asset["position"]),
            "team": str(asset.get("team") or ""),
            "nwr_rank": asset.get("nwr_rank"),
            "status": "RESOLVED",
            "actor": "OWNER_CORRECTION",
            "selection_behavior": action,
            "picked_at_utc": utc_now(),
        }
    else:
        new_entry = {
            **previous_snapshot,
            "player_id": "",
            "player_name": "",
            "position": "",
            "team": "",
            "nwr_rank": None,
            "status": "UNRESOLVED",
            "actor": "OWNER_CORRECTION",
            "selection_behavior": action,
            "picked_at_utc": utc_now(),
        }
    picks[index] = new_entry
    updated = {**state, "picks": picks}
    updated["drafted"] = [str(pick["player_id"]) for pick in picks if pick.get("player_id")]
    updated["last_correction"] = {
        "pick_number": pick_number,
        "action": action,
        "previous": previous_snapshot,
        "corrected_at_utc": utc_now(),
    }
    updated["updated_at_utc"] = utc_now()
    return updated


def replace_pick(
    root: str | Path,
    profile: LeagueProfile,
    ranking: RankingResult,
    manual_assets: Sequence[Mapping[str, Any]],
    *,
    pick_number: int,
    player_id: str,
) -> dict[str, Any]:
    """Change the player assigned to an exact historical pick. Every
    later pick's pick_number/round/team_slot/player is untouched; the
    old player returns to the available pool and the new one leaves it."""
    state = load_room_state(root, profile, ranking, manual_assets)
    target = _pick_slot_or_raise(state, pick_number)
    if not target.get("player_id"):
        raise RedraftValidationError(f"Pick {pick_number} is unresolved; use Fill Gap instead.")
    asset = _asset_pool(ranking, manual_assets).get(player_id)
    if asset is None:
        raise RedraftValidationError("The selected replacement player is unavailable.")
    state = _apply_pick_correction(
        state, pick_number=pick_number, asset=asset, action="REPLACE_PICK"
    )
    _save_room_state(root, state)
    return state


def clear_pick(
    root: str | Path,
    profile: LeagueProfile,
    ranking: RankingResult,
    manual_assets: Sequence[Mapping[str, Any]],
    *,
    pick_number: int,
) -> dict[str, Any]:
    """Set a pick to UNRESOLVED. pick_number/round/team_slot are
    preserved; every later pick is untouched. The previously-assigned
    player returns to the available pool."""
    state = load_room_state(root, profile, ranking, manual_assets)
    target = _pick_slot_or_raise(state, pick_number)
    if not target.get("player_id"):
        raise RedraftValidationError(f"Pick {pick_number} is already unresolved.")
    state = _apply_pick_correction(state, pick_number=pick_number, asset=None, action="CLEAR_PICK")
    _save_room_state(root, state)
    return state


def fill_gap_pick(
    root: str | Path,
    profile: LeagueProfile,
    ranking: RankingResult,
    manual_assets: Sequence[Mapping[str, Any]],
    *,
    pick_number: int,
    player_id: str,
) -> dict[str, Any]:
    """Assign a player to an exact UNRESOLVED slot. Identical mechanism to
    replace_pick, gated to only apply when the slot starts UNRESOLVED."""
    state = load_room_state(root, profile, ranking, manual_assets)
    target = _pick_slot_or_raise(state, pick_number)
    if target.get("player_id"):
        raise RedraftValidationError(
            f"Pick {pick_number} is already resolved; use Replace instead."
        )
    asset = _asset_pool(ranking, manual_assets).get(player_id)
    if asset is None:
        raise RedraftValidationError("The selected player is unavailable.")
    state = _apply_pick_correction(state, pick_number=pick_number, asset=asset, action="FILL_GAP")
    _save_room_state(root, state)
    return state


def undo_pick_correction(
    root: str | Path,
    profile: LeagueProfile,
    ranking: RankingResult,
    manual_assets: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Reverse only the single most recent REPLACE/CLEAR/FILL GAP action.
    Independent of undo_room_pick (which undoes the latest *recorded*
    pick globally, LIFO) -- correcting pick 12 and then undoing that
    correction never touches picks 13+ or the draft's live tail."""
    state = load_room_state(root, profile, ranking, manual_assets)
    last = state.get("last_correction")
    if not last:
        raise RedraftValidationError("No pick correction is available to undo.")
    picks = list(state.get("picks", []))
    index = int(last["pick_number"]) - 1
    if not (0 <= index < len(picks)):
        raise RedraftValidationError("The corrected pick no longer exists.")
    picks[index] = dict(last["previous"])
    updated = {**state, "picks": picks}
    updated["drafted"] = [str(pick["player_id"]) for pick in picks if pick.get("player_id")]
    updated["last_correction"] = None
    updated["updated_at_utc"] = utc_now()
    _save_room_state(root, updated)
    return updated


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


# Bounded per call: a single sync never silently applies an entire draft.
# The caller (facade) re-invokes the sync on its own polling cadence, so a
# stuck draft or a bad connection surfaces as "no new picks" rather than one
# call hanging on hundreds of Sleeper picks.
MAX_SLEEPER_AUTO_SYNC_BATCH = 25


def sync_read_only_sleeper_picks(
    root: str | Path,
    profile: LeagueProfile,
    ranking: RankingResult,
    manual_assets: Sequence[Mapping[str, Any]],
    *,
    sleeper_picks: Sequence[Mapping[str, Any]],
    sleeper_players: Mapping[str, Mapping[str, Any]],
    max_picks: int = MAX_SLEEPER_AUTO_SYNC_BATCH,
) -> dict[str, Any]:
    """Bounded, read-only sync of a live Sleeper draft into LIVE_READ_ONLY
    room state. Never issues a Sleeper write. Applies at most `max_picks`
    new picks per call, in strict pick-number order; a pick that cannot be
    safely applied -- out of order relative to the next local pick, an
    unresolvable Sleeper player identity, or a local player already marked
    drafted -- is reported as a conflict and stops the sync at that point,
    so nothing is ever applied out of order past an unresolved gap. Player
    identity is resolved via the same normalized name+position key already
    used for owner-platform manual matches (_manual_match_key), not a new
    matching scheme."""
    state = load_room_state(root, profile, ranking, manual_assets)
    if state.get("mode") != "LIVE_READ_ONLY":
        raise RedraftValidationError("Sleeper auto-sync requires Live Read-Only mode.")
    pool = _asset_pool(ranking, manual_assets)
    identity_index: dict[str, str] = {}
    for asset in pool.values():
        key = _manual_match_key(asset["player_name"], asset["position"])
        identity_index.setdefault(key, asset["player_id"])

    ordered = sorted(
        (dict(raw) for raw in sleeper_picks if isinstance(raw.get("pick_no"), int)),
        key=lambda raw: raw["pick_no"],
    )
    applied: list[dict[str, Any]] = []
    conflicts: list[dict[str, Any]] = []
    next_expected = len(state["picks"]) + 1
    for raw_pick in ordered:
        pick_no = raw_pick["pick_no"]
        if pick_no < next_expected:
            continue  # already applied in an earlier sync call
        if len(applied) >= max_picks:
            break
        if pick_no != next_expected:
            conflicts.append(
                {
                    "pickNumber": pick_no,
                    "reason": "OUT_OF_ORDER",
                    "detail": (
                        f"Sleeper reports pick {pick_no} but the next local pick is "
                        f"{next_expected}."
                    ),
                }
            )
            break
        sleeper_player_id = str(raw_pick.get("player_id") or "").strip()
        sleeper_player = sleeper_players.get(sleeper_player_id)
        if not isinstance(sleeper_player, Mapping):
            conflicts.append(
                {
                    "pickNumber": pick_no,
                    "reason": "UNKNOWN_SLEEPER_PLAYER",
                    "detail": (
                        f"Sleeper player id {sleeper_player_id or '<missing>'} was not found "
                        "in the Sleeper player catalog."
                    ),
                }
            )
            break
        name = str(sleeper_player.get("full_name") or sleeper_player.get("search_full_name") or "")
        position = str(sleeper_player.get("position") or "").upper()
        position = "DST" if position == "DEF" else position
        local_player_id = identity_index.get(_manual_match_key(name, position))
        if local_player_id is None or local_player_id in state["drafted"]:
            conflicts.append(
                {
                    "pickNumber": pick_no,
                    "reason": "UNRESOLVED_LOCAL_IDENTITY",
                    "detail": (
                        f"Sleeper pick {pick_no} ({name or '<unnamed>'} — {position or '?'}) "
                        "has no available local match."
                    ),
                }
            )
            break
        asset = pool[local_player_id]
        state = _record_pick(
            profile, state, asset, actor="SLEEPER_READ_ONLY", behavior="AUTO_SYNC_PICK_EVENT"
        )
        applied.append(
            {"pickNumber": pick_no, "playerId": local_player_id, "playerName": asset["player_name"]}
        )
        next_expected += 1
    if applied:
        _save_room_state(root, state)
    return {
        "applied": applied,
        "conflicts": conflicts,
        "nextExpectedPick": next_expected,
        "sleeperPickCount": len(ordered),
        "boundedBatchHit": len(applied) >= max_picks,
    }


# --- Catch-up mode (section 10) ---------------------------------------
# See docs/codex/CATCH_UP_MODE_CONTRACT_20260903.md. A multi-line paste of
# player names, one per line, resolved sequentially against the next N
# slots that still need a player (an existing UNRESOLVED slot or a
# brand-new upcoming one), previewed before anything is written, and
# applied only when every line resolved unambiguously -- "AI cannot
# silently admit ambiguous identity" (section 15) applied to this surface.


def record_catch_up_pick(
    root: str | Path,
    profile: LeagueProfile,
    ranking: RankingResult,
    manual_assets: Sequence[Mapping[str, Any]],
    *,
    player_id: str,
    pick_number: int,
) -> dict[str, Any]:
    """Append one new tail pick from a confirmed catch-up-mode paste line.
    Same strict-next-pick-number append mechanism as
    ingest_read_only_sleeper_pick, but under its own actor/behavior label
    -- this pick did not come from Sleeper, it is an owner-confirmed match
    against a pasted recap, and the ledger must not misattribute its
    source."""
    state = load_room_state(root, profile, ranking, manual_assets)
    if state.get("mode") != "LIVE_READ_ONLY":
        raise RedraftValidationError("Catch-up mode requires Live Read-Only mode.")
    expected = len(state["picks"]) + 1
    if pick_number != expected:
        raise RedraftValidationError(
            f"Catch-up pick {pick_number} does not match next pick {expected}."
        )
    asset = _asset_pool(ranking, manual_assets).get(player_id)
    if asset is None or player_id in state["drafted"]:
        raise RedraftValidationError("Catch-up pick player is unavailable locally.")
    state = _record_pick(
        profile, state, asset, actor="OWNER_CATCH_UP", behavior="CATCH_UP_PASTE_EVENT"
    )
    _save_room_state(root, state)
    return state


def _catch_up_line_names(paste: str) -> list[str]:
    return [line.strip() for line in paste.splitlines() if line.strip()]


def _catch_up_target_slots(
    profile: LeagueProfile, state: Mapping[str, Any], count: int
) -> list[int]:
    total = profile.team_count * profile.draft.rounds
    resolved_by_number = {pick["pick_number"]: pick for pick in state["picks"]}
    targets: list[int] = []
    pick_number = 1
    while len(targets) < count and pick_number <= total:
        existing = resolved_by_number.get(pick_number)
        if existing is None or not existing.get("player_id"):
            targets.append(pick_number)
        pick_number += 1
    return targets


def _catch_up_candidate_row(asset: Mapping[str, Any]) -> dict[str, str]:
    return {
        "playerId": str(asset["player_id"]),
        "playerName": str(asset["player_name"]),
        "position": str(asset["position"]),
        "team": str(asset.get("team") or ""),
    }


def _catch_up_resolve(
    name: str, pool: Mapping[str, dict[str, Any]], unavailable: set[str]
) -> dict[str, Any]:
    core = _normalized_name_without_suffix(name)
    exact = [
        asset
        for asset in pool.values()
        if _normalized_name_without_suffix(asset["player_name"]) == core
        and asset["player_id"] not in unavailable
    ]
    if len(exact) == 1:
        match = exact[0]
        return {
            "pastedName": name,
            "status": "MATCHED",
            "playerId": match["player_id"],
            "playerName": match["player_name"],
            "position": match["position"],
            "team": match.get("team") or "",
            "candidates": [],
        }
    if len(exact) > 1:
        return {
            "pastedName": name,
            "status": "AMBIGUOUS",
            "playerId": None,
            "playerName": None,
            "position": None,
            "team": None,
            "candidates": [_catch_up_candidate_row(asset) for asset in exact],
        }
    scored = sorted(
        (
            (
                difflib.SequenceMatcher(
                    None, core, _normalized_name_without_suffix(asset["player_name"])
                ).ratio(),
                asset,
            )
            for asset in pool.values()
            if asset["player_id"] not in unavailable
        ),
        key=lambda pair: pair[0],
        reverse=True,
    )
    suggestions = [asset for score, asset in scored[:3] if score >= 0.6]
    return {
        "pastedName": name,
        "status": "NO_MATCH",
        "playerId": None,
        "playerName": None,
        "position": None,
        "team": None,
        "candidates": [_catch_up_candidate_row(asset) for asset in suggestions],
    }


def preview_catch_up_paste(
    root: str | Path,
    profile: LeagueProfile,
    ranking: RankingResult,
    manual_assets: Sequence[Mapping[str, Any]],
    *,
    paste: str,
) -> dict[str, Any]:
    """Pure preview -- never writes. Resolves each pasted name against the
    next N slots needing a player; a name that is ambiguous or has no
    confident match blocks readyToApply for the whole batch rather than
    silently skipping or guessing."""
    state = load_room_state(root, profile, ranking, manual_assets)
    names = _catch_up_line_names(paste)
    targets = _catch_up_target_slots(profile, state, len(names))
    pool = _asset_pool(ranking, manual_assets)
    unavailable = set(state["drafted"])
    rows: list[dict[str, Any]] = []
    for pick_number, name in zip(targets, names, strict=False):
        row = _catch_up_resolve(name, pool, unavailable)
        row["pickNumber"] = pick_number
        if row["status"] == "MATCHED":
            unavailable.add(row["playerId"])
        rows.append(row)
    overflow_names = names[len(targets) :]
    ready = bool(rows) and not overflow_names and all(row["status"] == "MATCHED" for row in rows)
    return {
        "rows": rows,
        "overflowNames": overflow_names,
        "readyToApply": ready,
    }


def apply_catch_up_paste(
    root: str | Path,
    profile: LeagueProfile,
    ranking: RankingResult,
    manual_assets: Sequence[Mapping[str, Any]],
    *,
    paste: str,
) -> dict[str, Any]:
    """Apply a catch-up paste. Re-resolves from scratch (never trusts a
    stale client-side preview) and refuses to apply anything if any line is
    unresolved, ambiguous, or there are more names than open slots. Reuses
    the event ledger verbatim: an existing UNRESOLVED slot goes through
    fill_gap_pick; a brand-new tail slot goes through record_catch_up_pick,
    applied in ascending pick order so each append satisfies its own
    strict next-pick-number check. (preview_catch_up_paste never selects an
    already-RESOLVED slot as a target, so there is no third case here --
    correcting an already-resolved pick is the separate Replace action on
    the event ledger, not a catch-up-paste concern.)"""
    preview = preview_catch_up_paste(root, profile, ranking, manual_assets, paste=paste)
    if not preview["readyToApply"]:
        raise RedraftValidationError(
            "Catch-up paste has unresolved, ambiguous, or unassigned lines; nothing was applied."
        )
    state = load_room_state(root, profile, ranking, manual_assets)
    existing_numbers = {pick["pick_number"] for pick in state["picks"]}
    applied: list[dict[str, Any]] = []
    for row in sorted(preview["rows"], key=lambda item: item["pickNumber"]):
        pick_number = row["pickNumber"]
        player_id = row["playerId"]
        if pick_number in existing_numbers:
            state = fill_gap_pick(
                root, profile, ranking, manual_assets,
                pick_number=pick_number, player_id=player_id,
            )
        else:
            state = record_catch_up_pick(
                root, profile, ranking, manual_assets,
                pick_number=pick_number, player_id=player_id,
            )
        applied.append(
            {"pickNumber": pick_number, "playerId": player_id, "playerName": row["playerName"]}
        )
    return {"applied": applied, "state": state}


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
                "status": "OPEN" if pick is None else str(pick.get("status") or "RESOLVED"),
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
    # NWR post-draft overnight, DecisionBundle latency repair: real
    # cProfile evidence pinned this exact line as the dominant cost
    # (`_select_asset`: 10,056 calls, 9.2s of its own time in a single
    # real DecisionBundle FAST call) -- `state["drafted"]` is a plain
    # list (rebuilt by `_record_pick` after every real pick), so
    # `key not in state.get("drafted", [])` was an O(len(drafted)) scan
    # run once per pool entry, making this one line O(pool_size x
    # drafted_size) -- with a real ~530-row pool and drafted growing to
    # ~190 deep in a draft, that is real, quadratic-shaped cost repeated
    # on every one of the thousands of `_select_asset` calls a single
    # Raw Action Value Monte Carlo evaluation makes. A set has the exact
    # same membership answer as the list in O(1) -- pure speed, zero
    # behavior change (verified: full regression suite unchanged).
    drafted_ids = set(state.get("drafted", ()))
    available = [asset for key, asset in pool.items() if key not in drafted_ids]
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
    # NWR post-draft overnight, DecisionBundle latency repair (real
    # cProfile evidence: `_roster_candidate_allowed`/`_roster_need_
    # adjustment` were called once PER CANDIDATE -- ~5M times combined
    # in a single real DecisionBundle FAST call -- but both are PURE
    # functions of `position` alone given `profile`/`roster`/
    # `round_number`, which are all fixed for the duration of this one
    # `_select_asset` call. A real ~530-row pool has at most 6 distinct
    # real positions (QB/RB/WR/TE/K/DST), so memoizing by position here
    # turns ~500+ redundant recomputations of the same value into at
    # most 6 real ones per call -- pure speed, zero behavior change
    # (the memoized value is byte-identical to what the direct call
    # would have returned; verified via the full regression suite).
    allowed_cache: dict[str, bool] = {}
    need_adjustment_cache: dict[str, float] = {}

    def _cached_roster_candidate_allowed(asset: Mapping[str, Any]) -> bool:
        position = str(asset["position"])
        cached = allowed_cache.get(position)
        if cached is None:
            cached = _roster_candidate_allowed(profile, roster, asset)
            allowed_cache[position] = cached
        return cached

    def _cached_roster_need_adjustment(position: str) -> float:
        cached = need_adjustment_cache.get(position)
        if cached is None:
            cached = _roster_need_adjustment(profile, roster, round_number, position)
            need_adjustment_cache[position] = cached
        return cached

    candidates = [asset for asset in candidates if _cached_roster_candidate_allowed(asset)]
    if not candidates:
        candidates = available
    if actor == "OWNER_AUTO_TEST":
        candidates.sort(
            key=lambda asset: (
                float(asset.get("nwr_rank") or 10_000) + _cached_roster_need_adjustment(str(asset["position"])),
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
        need_adjustment = _cached_roster_need_adjustment(str(asset["position"]))
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
    round_number = ((current_pick - 1) // profile.team_count) + 1 if profile.team_count else 1
    enriched = [
        _decision_row(profile, row, adp, current_pick, next_owner_pick, roster)
        for row in available[:100]
    ]
    beat_pool = sorted(
        [row for row in enriched if row["nwrView"] in {"STRONG VALUE", "VALUE"}],
        key=lambda row: (-float(row.get("nwrEdge") or 0), int(row["nwrRank"])),
    )[:30]
    # Suggestions eligibility is a legality rule, not a ranking calibration:
    # a position already at this league's configured maximum (roster_limits,
    # or the same heuristic cap _roster_candidate_allowed enforces at pick
    # time) is dropped from the actionable candidate set below. The player
    # stays fully visible/searchable elsewhere (PLAYERS panel, beat_pool,
    # allRows) -- this only narrows what gets *recommended*.
    eligible = [row for row in enriched if _roster_candidate_allowed(profile, roster, row)]
    cards: list[dict[str, Any]] = []
    used_player_ids: set[str] = set()

    def pick_distinct(candidates: list[dict[str, Any]]) -> dict[str, Any] | None:
        """Return the first candidate not already used by an earlier card,
        falling back to the top candidate (materially the best option) if the
        whole ranked pool is already exhausted of distinct alternatives."""
        for candidate in candidates:
            if candidate["playerId"] not in used_player_ids:
                return candidate
        return candidates[0] if candidates else None

    if eligible:
        best_available = eligible[0]
        cards.append(_card("Best Available", best_available, "Highest available NWR Redraft rank."))
        used_player_ids.add(best_available["playerId"])

        fit_ranked = sorted(
            eligible[:30],
            key=lambda row: (
                _fit_penalty(profile, roster, str(row["position"]), round_number),
                -float(row["replacementAdjustedValue"]),
            ),
        )
        fit = pick_distinct(fit_ranked)
        if fit is not None:
            cards.append(_card("Best Fit", fit, "Best roster-construction fit by scarcity and starter/FLEX need."))
            used_player_ids.add(fit["playerId"])

        # Value vs ESPN: bounded to actionable players near this pick / next
        # owner pick, not a raw ADP-minus-rank edge over the whole available
        # pool (which lets an irrelevant deep-bench player with a huge ADP
        # dwarf any real near-term value signal).
        reach_buffer = 12
        window_end = (next_owner_pick + reach_buffer) if next_owner_pick is not None else (current_pick + 40)
        actionable_value_rows = [
            row for row in eligible
            if row.get("expectedPick") is not None
            and current_pick - 8 <= float(row["expectedPick"]) <= window_end
            and row["draftTiming"] in {"TAKE NOW", "VALID"}
        ]
        actionable_value_rows.sort(key=lambda row: -float(row.get("nwrEdge") or -9999))
        value = pick_distinct(actionable_value_rows)
        if value is not None:
            cards.append(_card("Value vs ESPN", value, "Largest ESPN-ADP edge among players actually relevant to this pick window."))
            used_player_ids.add(value["playerId"])
        else:
            fallback = pick_distinct(eligible[:30]) or best_available
            cards.append(
                _card(
                    "Value vs ESPN",
                    fallback,
                    "No actionable ADP edge in the current pick window; showing NWR order instead.",
                )
            )
            used_player_ids.add(fallback["playerId"])

        upside_ranked = sorted(eligible[:20], key=lambda row: -float(row["replacementAdjustedValue"]))
        upside = pick_distinct(upside_ranked)
        if upside is not None:
            cards.append(_card("Upside", upside, "Highest replacement-adjusted ceiling proxy available."))
            used_player_ids.add(upside["playerId"])

        safe_ranked = [row for row in eligible[:30] if str(row["confidence"]).upper() == "HIGH"]
        safer = pick_distinct(safe_ranked) if safe_ranked else pick_distinct(eligible[:30])
        if safer is not None:
            cards.append(_card("Safer", safer, "Best high-evidence option; falls back visibly if none."))
            used_player_ids.add(safer["playerId"])
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
    adp_explanation = _adp_explanation(adp, row.player_id, entry)
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
        "adpSource": adp_explanation["source"],
        "adpExplanation": adp_explanation["label"],
        "adpUnavailableReason": adp_explanation["unavailableReason"],
        "adpSourceDate": adp.source_date if entry else "",
    }


def _adp_explanation(adp: AdpSnapshot, player_id: str, entry: AdpEntry | None) -> dict[str, str]:
    if entry is None:
        return {
            "source": "",
            "label": "ADP unavailable · no selected platform, Consensus, or FFC match",
            "unavailableReason": "NO_ACTIVE_ADP_FOR_PLAYER",
        }
    if not adp.provider.startswith("OWNER_PLATFORM_"):
        return {"source": adp.source, "label": f"ADP: {entry.overall_adp:.1f} · {adp.source}", "unavailableReason": ""}
    selected = adp.provider.removeprefix("OWNER_PLATFORM_AUTO_").removeprefix("OWNER_PLATFORM_")
    owner_row = next((row for row in adp.paste_rows if str(row.get("matched_nwr_player_id") or "") == player_id), None)
    if owner_row is None:
        return {"source": "FFC fallback", "label": f"ADP: {entry.overall_adp:.1f} · FFC fallback", "unavailableReason": ""}
    origin = str(owner_row.get("active_selected_source") or selected)
    if origin != selected:
        return {"source": "Consensus fallback", "label": f"ADP: {entry.overall_adp:.1f} · Consensus fallback", "unavailableReason": ""}
    return {"source": f"Owner {selected.title()}", "label": f"ADP: {entry.overall_adp:.1f} · Owner {selected.title()}", "unavailableReason": ""}


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
    # UNRESOLVED picks (CLEAR PICK) carry an empty player_id -- exclude
    # them from `drafted` so multiple cleared slots don't collide with
    # each other or block re-selecting the same real player elsewhere.
    recomputed_drafted = [str(pick["player_id"]) for pick in picks if pick.get("player_id")]
    if recomputed_drafted != drafted:
        drafted = recomputed_drafted
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
        "last_correction": document.get("last_correction"),
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
        "last_correction": state.get("last_correction"),
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
    # K/DST are always manual (NWR has no model for them). Skill positions
    # (QB/RB/WR/TE) are admitted from the manual pool only when NWR's own
    # ranked universe has no entry for that player_id -- these are real,
    # externally-known players NWR's projection universe is missing (see
    # src/services/udk_unmodeled_skill_asset_service.py), not a second,
    # conflicting entry for a player who is already ranked.
    for raw in manual_assets:
        player_id = _manual_id(raw)
        position = str(raw.get("position") or "").upper()
        if not player_id:
            continue
        is_unranked_skill = position in {"QB", "RB", "WR", "TE"} and player_id not in pool
        if position in {"K", "DST"} or is_unranked_skill:
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
    # NWR OVERNIGHT (K/DST completion, Section 3): a general feasibility
    # check, not a second hardcoded round number -- when the picks actually
    # remaining in this draft for this team are down to (or below) the
    # count of still-required-but-unfilled positions, force one now,
    # regardless of which position or how many rounds that is from the
    # end. Reuses roster/profile.roster the exact same way every other
    # branch here already does; derives urgency from the real remaining
    # choices, not a fixed "round 15" assumption that a shorter or
    # differently-sized bench could invalidate.
    picks_remaining = max(0, profile.draft.rounds - round_number + 1)
    still_required = [
        position
        for position in ("QB", "RB", "WR", "TE", "K", "DST")
        if roster[position]
        < int(getattr(profile.roster, position.lower(), 0))
        + (profile.roster.superflex if position == "QB" else 0)
    ]
    if still_required and picks_remaining <= len(still_required):
        return still_required[0]
    if round_number >= max(1, profile.draft.rounds - 1):
        if roster["K"] < profile.roster.k:
            return "K"
        if roster["DST"] < profile.roster.dst:
            return "DST"
    deadlines = (("QB", 8), ("TE", 10), ("RB", 12), ("WR", 12))
    for position, deadline in deadlines:
        required = int(getattr(profile.roster, position.lower()))
        # Owner feedback closure (Superflex disposition): a Superflex slot
        # is real, real QB demand -- a team with one configured needs a
        # deadline-forced QB just as much as one filling its starter QB1,
        # never treated as if the slot doesn't exist. Zero-blast-radius
        # for every 1QB league (profile.roster.superflex defaults to 0,
        # so `required` is unchanged from the frozen behavior above).
        if position == "QB":
            required += profile.roster.superflex
        if round_number >= deadline and roster[position] < required:
            return position
    return None


def _roster_candidate_allowed(
    profile: LeagueProfile,
    roster: Counter[str],
    asset: Mapping[str, Any],
) -> bool:
    position = str(asset["position"])
    explicit_limit = profile.draft.roster_limits.get(position)
    if explicit_limit is not None:
        return roster[position] < int(explicit_limit)
    if position in {"K", "DST"}:
        return roster[position] < int(getattr(profile.roster, position.lower()))
    if position == "QB":
        # Owner feedback closure (Superflex disposition): a Superflex
        # slot is a second real starter-eligible QB use, not just "QB1 +
        # one legal backup" -- the same +1-backup allowance the 1QB case
        # already gets is preserved on top of the real Superflex count.
        # Zero-blast-radius for every 1QB league (superflex defaults to
        # 0, reproducing max(profile.roster.qb + 1, 2) exactly).
        return roster[position] < max(profile.roster.qb + profile.roster.superflex + 1, 2)
    if position == "TE":
        return roster[position] < max(profile.roster.te + 1, 2)
    return roster[position] < profile.draft.rounds


def _roster_limit_violation(
    profile: LeagueProfile,
    state: Mapping[str, Any],
    team_slot: int,
    asset: Mapping[str, Any],
) -> str | None:
    """Return a human-readable message if drafting `asset` for `team_slot` would
    exceed a configured position maximum, else None. Applies to every actor
    (owner and CPU alike) so a human owner cannot violate the same league
    position caps that constrain the bots."""
    roster = Counter(
        str(pick["position"])
        for pick in state.get("picks", [])
        if int(pick["team_slot"]) == team_slot
    )
    if _roster_candidate_allowed(profile, roster, asset):
        return None
    position = str(asset["position"])
    explicit_limit = profile.draft.roster_limits.get(position)
    limit = (
        int(explicit_limit)
        if explicit_limit is not None
        else roster[position]  # heuristic cap already reached; report the count as the limit
    )
    return f"Drafting this {position} would exceed the league position maximum of {limit}."


def _roster_need_adjustment(
    profile: LeagueProfile,
    roster: Counter[str],
    round_number: int,
    position: str,
) -> float:
    required = int(getattr(profile.roster, position.lower(), 0))
    # NWR OVERNIGHT (K/DST completion): K/DST get the exact same real
    # under-required urgency signal QB/RB/WR/TE already had -- previously
    # excluded from this branch, K/DST could never outrank a low-value
    # skill-position depth pick even with zero rostered and one required,
    # the precisely-traced root cause of K/DST finishing 0/1 in a real
    # top-suggestion mock. K/DST have no FLEX-slot slack, so this is their
    # only need signal (no second branch below applies to them).
    if position in {"QB", "RB", "WR", "TE", "K", "DST"} and roster[position] < required:
        return -10.0 - round_number
    if position in {"RB", "WR", "TE"}:
        flex_have = sum(roster[value] for value in ("RB", "WR", "TE"))
        flex_need = profile.roster.rb + profile.roster.wr + profile.roster.te + profile.roster.flex
        if flex_have < flex_need:
            return -6.0
    # Owner feedback closure (Superflex disposition): the exact same
    # real-slack pattern immediately above (RB/WR/TE counting toward the
    # shared FLEX slot) applied to QB counting toward a real Superflex
    # slot -- reused, not reinvented. Zero-blast-radius for every 1QB
    # league: profile.roster.superflex defaults to 0, so this branch
    # never fires when QB1 is already satisfied (roster[QB] >= required
    # == profile.roster.qb == qb_need).
    if position == "QB" and profile.roster.superflex > 0:
        qb_need = profile.roster.qb + profile.roster.superflex
        if roster["QB"] < qb_need:
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


def _fit_penalty(profile: LeagueProfile, roster: Counter[str], position: str, round_number: int = 1) -> float:
    return _roster_need_adjustment(profile, roster, round_number, position)


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
        if not pick.get("player_id"):
            continue  # UNRESOLVED (cleared) slot -- not a roster entry
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
        "status": str(pick.get("status") or "RESOLVED"),
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
        "overallAdp": row["overallAdp"],
        "adpSource": row["adpSource"],
        "adpExplanation": row["adpExplanation"],
        "adpUnavailableReason": row["adpUnavailableReason"],
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
        # NWR DRAFT-DAY (round.pick for ADP): the source's OWN team count,
        # never assumed to match the active room's team_count -- a
        # round.pick conversion is only safe when they match (see
        # formatAdpRoundPick in draft-room-v2.tsx); this is what lets the
        # frontend refuse to "silently convert source context" instead of
        # guessing.
        "teamCount": snapshot.team_count,
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


def _udk_rankings_path(root: str | Path, profile_id: str) -> Path:
    return Path(root) / "udk_provider_cache" / f"{profile_id}.json"


def _owner_platform_snapshot_path(root: str | Path) -> Path:
    return Path(root) / "adp_provider_cache" / "owner_platform_snapshot" / "snapshot.json"


def _owner_platform_manual_matches_path(root: str | Path) -> Path:
    return Path(root) / "adp_provider_cache" / "owner_platform_snapshot" / "manual_matches.json"


def _manual_match_key(player: str, position: str) -> str:
    return f"{_normalized_position(position)}:{_normalized_name_without_suffix(player)}"


def _load_owner_platform_manual_matches(root: str | Path | None) -> dict[str, dict[str, Any]]:
    if root is None:
        return {}
    path = _owner_platform_manual_matches_path(root)
    try:
        rows = json.loads(path.read_text(encoding="utf-8")).get("matches", [])
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return {}
    return {_manual_match_key(str(row.get("pasted_name") or ""), str(row.get("pasted_position") or "")): dict(row) for row in rows if isinstance(row, Mapping)}


def approve_owner_platform_manual_match(
    root: str | Path, ranking: RankingResult, manual_assets: Sequence[Mapping[str, Any]], *,
    pasted_name: str, pasted_position: str, pasted_position_rank: str, selected_nwr_player_id: str,
    source_snapshot_hash: str = "",
) -> None:
    """Persist an owner decision scoped solely to Redraft pasted ADP identity."""
    assets = _matching_assets(ranking, manual_assets)
    position = _normalized_position(pasted_position)
    candidate = next((row for row in assets if row["player_id"] == selected_nwr_player_id and row["position"] == position), None)
    if candidate is None:
        raise RedraftValidationError("Choose an existing NWR player with the same position for this local ADP alias.")
    path = _owner_platform_manual_matches_path(root)
    existing = _load_owner_platform_manual_matches(root)
    existing[_manual_match_key(pasted_name, position)] = {
        "pasted_name": pasted_name.strip(), "pasted_position": position, "pasted_position_rank": pasted_position_rank,
        "selected_nwr_player_id": selected_nwr_player_id, "selected_nwr_player_name": candidate["player_name"],
        "selected_nwr_position": candidate["position"], "selected_nwr_team": candidate["team"],
        "approved_at": utc_now(), "approved_by": "owner", "source_snapshot_hash": source_snapshot_hash,
        "scope": "REDRAFT_ADP_IMPORT_ONLY",
    }
    _atomic_json(path, {"schema_version": 1, "matches": list(existing.values())})


def clear_owner_platform_manual_match(root: str | Path, *, pasted_name: str, pasted_position: str) -> None:
    existing = _load_owner_platform_manual_matches(root)
    existing.pop(_manual_match_key(pasted_name, pasted_position), None)
    _atomic_json(_owner_platform_manual_matches_path(root), {"schema_version": 1, "matches": list(existing.values())})


def _owner_platform_candidates(player: str, position: str, assets: Sequence[Mapping[str, str]]) -> list[dict[str, str]]:
    target = _normalized_name_without_suffix(player)
    candidates: list[tuple[float, Mapping[str, str]]] = []
    for asset in assets:
        score = difflib.SequenceMatcher(None, target, _normalized_name_without_suffix(asset["player_name"])).ratio()
        if asset["position"] == position:
            score += 0.2
        if score >= 0.58:
            candidates.append((score, asset))
    candidates.sort(key=lambda item: (-item[0], item[1]["player_name"]))
    return [{"player_id": str(row["player_id"]), "player_name": str(row["player_name"]), "position": str(row["position"]), "team": str(row["team"]), "active_redraft_board": True, "confidence": "HIGH" if score >= 1.0 else "REVIEW", "reason": "normalized name and position candidate" if row["position"] == position else "name candidate; position differs"} for score, row in candidates[:5]]


def _classify_owner_platform_gap(player: str, position: str, reason: str, assets: Sequence[Mapping[str, str]]) -> str:
    if reason in {"POSITION_MISMATCH", "AMBIGUOUS_NAME"}:
        return reason
    if _owner_platform_candidates(player, position, assets):
        return "POSSIBLE_ALIAS_REVIEW"
    return "NOT_IN_ACTIVE_REDRAFT_BOARD"


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
        freshness=_freshness_label(str(document.get("imported_at_utc") or "")),
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
    if not lines:
        return []
    # Responsive clipboard copies can contain data rows without a header.
    compact_rows = []
    for line in lines:
        cells = _paste_cells(line)
        if len(cells) == 6 and _plain_position(cells[0]):
            compact_rows.append({"position": cells[0], "player": cells[1], "consensus": cells[2], "sleeper": cells[3], "espn": cells[4], "fantasypros": cells[5]})
    if compact_rows:
        return compact_rows
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
    return plain_rows, "RESPONSIVE_PLATFORM_CLIPBOARD", warnings


def _plain_text_platform_rows(paste_text: str) -> tuple[list[dict[str, str]], list[str]]:
    lines = [re.sub(r"\*+", "", value).strip() for value in paste_text.replace("\r\n", "\n").split("\n")]
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
        cursor = index + consumed
        player = ""
        team = ""
        values: list[str] = []
        while cursor < len(lines):
            value = lines[cursor]
            if re.fullmatch(r"(?:QB|RB|WR|TE|K|DST|D/ST)\d+", value, re.I) or (_normalized_position(value) in {"QB", "RB", "WR", "TE", "K", "DST"} and cursor + 1 < len(lines) and re.fullmatch(r"\d+", lines[cursor + 1] or "")):
                break
            tokens = value.replace(",", "").split()
            if value and 1 <= len(tokens) <= 4 and all(re.fullmatch(r"(?:\d+(?:\.\d+)?|—|-)", token) for token in tokens):
                values = tokens
                break
            if value and not _clipboard_noise(value) and value not in {"●", "•", "-", "—"}:
                if re.fullmatch(r"[A-Z]{2,4}", value):
                    team = value
                elif not player:
                    player = value
            cursor += 1
        if not player or not values:
            warnings.append(f"plain-text row near line {index + 1}: missing player or ADP values")
            index += consumed
            continue
        rows.append({
            "position": combined,
            "player": player,
            "team": team,
            "consensus": values[0] if len(values) > 0 else "",
            "sleeper": values[1] if len(values) > 1 else "",
            "espn": values[2] if len(values) > 2 else "",
            "fantasypros": values[3] if len(values) > 3 else "",
        })
        index = cursor + 1
    return rows, warnings


def _clipboard_noise(value: str) -> bool:
    return re.sub(r"[^a-z]", "", value.lower()) in {"position", "player", "consensus", "sleeper", "espn", "fantasypros", "fpros", "ppr", "halfppr", "std", "qbrbwrte", "tagsfilters"}


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
