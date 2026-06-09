from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass
from pathlib import Path

DEFAULT_CLEAN_ROWS = Path(
    "local_exports/model_v4/historical_fantasypros_advanced/latest/"
    "fantasypros_advanced_clean_rows.csv"
)
DEFAULT_IDENTITY_MAP = Path(
    "local_exports/nflverse/preview/sprint2_phase7_public_20260514/raw/"
    "nflverse_identity_map.csv"
)
DEFAULT_ACTIVE_BRIDGE = Path(
    "local_exports/active_veteran_model_public_sources/sleeper_nflverse_identity_bridge.csv"
)
DEFAULT_TRUTH_SET = Path("docs/model_v4/TRUTH_SET_PLAYER_UNIVERSE.csv")
DEFAULT_OUTPUT_ROOT = Path("local_exports/model_v4/historical_fantasypros_advanced/latest")

FANTASYPROS_IDENTITY_MAPPING_HEADER = (
    "fantasypros_player_name",
    "normalized_player_name",
    "season",
    "position",
    "fantasypros_team",
    "matched_model_player",
    "sleeper_id",
    "gsis_id",
    "match_method",
    "match_confidence",
    "warning",
    "candidate_count",
    "candidate_players",
    "source_file",
    "source_hash",
)

FANTASYPROS_IDENTITY_UNRESOLVED_HEADER = FANTASYPROS_IDENTITY_MAPPING_HEADER + (
    "unresolved_reason",
)

FANTASYPROS_IDENTITY_SUMMARY_HEADER = ("metric", "value")

SUPPORTED_POSITIONS = {"QB", "RB", "WR", "TE"}

TEAM_ALIASES = {
    "JAC": "JAX",
    "LA": "LAR",
    "STL": "LAR",
    "SD": "LAC",
    "OAK": "LV",
    "WSH": "WAS",
}

CLEAR_NAME_ALIASES = {
    "hollywoodbrown": "marquisebrown",
    "robbieanderson": "robbyanderson",
    "mitchelltrubisky": "mitchtrubisky",
}


@dataclass(frozen=True)
class FantasyProsIdentityMappingResult:
    mapping_rows: tuple[dict[str, object], ...]
    unresolved_rows: tuple[dict[str, object], ...]
    summary: dict[str, object]


@dataclass
class ModelIdentityCandidate:
    model_player_name: str
    position: str
    team: str
    sleeper_id: str
    gsis_id: str
    names: set[str]
    source: set[str]


def build_fantasypros_identity_mapping(
    *,
    clean_rows_path: str | Path = DEFAULT_CLEAN_ROWS,
    identity_map_path: str | Path = DEFAULT_IDENTITY_MAP,
    active_bridge_path: str | Path = DEFAULT_ACTIVE_BRIDGE,
    truth_set_path: str | Path = DEFAULT_TRUTH_SET,
) -> FantasyProsIdentityMappingResult:
    clean_rows = _read_rows(Path(clean_rows_path))
    candidates = build_model_identity_candidates(
        identity_map_path=identity_map_path,
        active_bridge_path=active_bridge_path,
        truth_set_path=truth_set_path,
    )
    resolver = _IdentityResolver(candidates)
    mapping_rows = [resolver.resolve(row) for row in clean_rows]
    unresolved_rows = [
        {**row, "unresolved_reason": row["warning"]}
        for row in mapping_rows
        if row["warning"] in {"unmatched_player", "ambiguous_name_position"}
    ]
    return FantasyProsIdentityMappingResult(
        mapping_rows=tuple(mapping_rows),
        unresolved_rows=tuple(unresolved_rows),
        summary=_summary(mapping_rows, unresolved_rows, candidates, clean_rows_path),
    )


def build_model_identity_candidates(
    *,
    identity_map_path: str | Path = DEFAULT_IDENTITY_MAP,
    active_bridge_path: str | Path = DEFAULT_ACTIVE_BRIDGE,
    truth_set_path: str | Path = DEFAULT_TRUTH_SET,
) -> tuple[ModelIdentityCandidate, ...]:
    by_key: dict[str, ModelIdentityCandidate] = {}
    for row in _read_rows_if_exists(Path(identity_map_path)):
        if str(row.get("position") or "") not in SUPPORTED_POSITIONS:
            continue
        candidate = ModelIdentityCandidate(
            model_player_name=str(row.get("player_name") or "").strip(),
            position=str(row.get("position") or "").strip(),
            team=_team_key(row.get("team")),
            sleeper_id=str(row.get("sleeper_id") or row.get("player_id") or "").strip(),
            gsis_id=str(row.get("gsis_id") or "").strip(),
            names={
                str(row.get("player_name") or "").strip(),
                str(row.get("normalized_name") or "").strip(),
            },
            source={"nflverse_identity_map"},
        )
        _merge_candidate(by_key, candidate)

    for row in _read_rows_if_exists(Path(active_bridge_path)):
        if str(row.get("position") or "") not in SUPPORTED_POSITIONS:
            continue
        names = {
            str(row.get("player_name") or "").strip(),
            str(row.get("bridge_name") or "").strip(),
            str(row.get("stat_player_name") or "").strip(),
        }
        display_name = _best_display_name(names)
        candidate = ModelIdentityCandidate(
            model_player_name=display_name,
            position=str(row.get("position") or "").strip(),
            team="",
            sleeper_id=str(row.get("sleeper_id") or "").strip(),
            gsis_id=str(row.get("matched_gsis_id") or row.get("bridge_gsis_id") or "").strip(),
            names=names,
            source={"active_sleeper_bridge"},
        )
        _merge_candidate(by_key, candidate)

    for row in _read_rows_if_exists(Path(truth_set_path)):
        if str(row.get("position") or "") not in SUPPORTED_POSITIONS:
            continue
        candidate = ModelIdentityCandidate(
            model_player_name=str(row.get("player_name") or "").strip(),
            position=str(row.get("position") or "").strip(),
            team=_team_key(row.get("nfl_team")),
            sleeper_id="",
            gsis_id="",
            names={str(row.get("player_name") or "").strip()},
            source={"model_v4_truth_set"},
        )
        _merge_truth_set_candidate(by_key, candidate)

    return tuple(by_key.values())


def write_fantasypros_identity_mapping_outputs(
    output_root: str | Path,
    result: FantasyProsIdentityMappingResult,
) -> dict[str, Path]:
    root = Path(output_root)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "mapping": root / "fantasypros_advanced_identity_mapping.csv",
        "unresolved": root / "fantasypros_advanced_identity_unresolved.csv",
        "summary_csv": root / "fantasypros_advanced_identity_summary.csv",
        "summary_json": root / "fantasypros_advanced_identity_summary.json",
    }
    _write_csv(paths["mapping"], FANTASYPROS_IDENTITY_MAPPING_HEADER, result.mapping_rows)
    _write_csv(
        paths["unresolved"],
        FANTASYPROS_IDENTITY_UNRESOLVED_HEADER,
        result.unresolved_rows,
    )
    _write_csv(
        paths["summary_csv"],
        FANTASYPROS_IDENTITY_SUMMARY_HEADER,
        [{"metric": key, "value": value} for key, value in result.summary.items()],
    )
    paths["summary_json"].write_text(
        json.dumps(result.summary, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return paths


class _IdentityResolver:
    def __init__(self, candidates: tuple[ModelIdentityCandidate, ...]) -> None:
        self.by_name_position_team: dict[
            tuple[str, str, str],
            list[ModelIdentityCandidate],
        ] = {}
        self.by_name_position: dict[tuple[str, str], list[ModelIdentityCandidate]] = {}
        for candidate in candidates:
            for name in candidate.names:
                name_key = normalize_player_name(name)
                if not name_key:
                    continue
                self.by_name_position.setdefault(
                    (name_key, candidate.position),
                    [],
                ).append(candidate)
                if candidate.team:
                    self.by_name_position_team.setdefault(
                        (name_key, candidate.position, candidate.team),
                        [],
                    ).append(candidate)

    def resolve(self, fantasypros_row: dict[str, str]) -> dict[str, object]:
        player_name = str(fantasypros_row.get("player_name") or "").strip()
        normalized = normalize_player_name(player_name)
        aliased = CLEAR_NAME_ALIASES.get(normalized, normalized)
        position = str(fantasypros_row.get("position") or "").strip()
        fantasypros_team = _team_key(fantasypros_row.get("nfl_team"))

        match, method, confidence, warning = self._resolve_candidate(
            normalized=normalized,
            aliased=aliased,
            position=position,
            fantasypros_team=fantasypros_team,
        )
        candidates = self.by_name_position.get((aliased, position), [])
        candidate_players = "|".join(
            sorted({candidate.model_player_name for candidate in candidates})
        )
        return {
            "fantasypros_player_name": player_name,
            "normalized_player_name": normalized,
            "season": fantasypros_row.get("season", ""),
            "position": position,
            "fantasypros_team": fantasypros_team,
            "matched_model_player": match.model_player_name if match else "",
            "sleeper_id": match.sleeper_id if match else "",
            "gsis_id": match.gsis_id if match else "",
            "match_method": method,
            "match_confidence": confidence,
            "warning": warning,
            "candidate_count": len(_unique_candidates(candidates)),
            "candidate_players": candidate_players,
            "source_file": fantasypros_row.get("source_file", ""),
            "source_hash": fantasypros_row.get("source_hash", ""),
        }

    def _resolve_candidate(
        self,
        *,
        normalized: str,
        aliased: str,
        position: str,
        fantasypros_team: str,
    ) -> tuple[ModelIdentityCandidate | None, str, int, str]:
        team_candidates = _unique_candidates(
            self.by_name_position_team.get((aliased, position, fantasypros_team), [])
        )
        if len(team_candidates) == 1:
            method = "alias_name_team_position" if aliased != normalized else "name_team_position"
            return team_candidates[0], method, 98, ""
        if len(team_candidates) > 1:
            return None, "ambiguous_name_team_position", 0, "ambiguous_name_position"

        name_candidates = _unique_candidates(self.by_name_position.get((aliased, position), []))
        if len(name_candidates) == 1:
            warning = ""
            confidence = 94
            method = "alias_name_position" if aliased != normalized else "exact_normalized_name"
            if fantasypros_team and name_candidates[0].team:
                warning = "team_mismatch_or_historical_team"
                confidence = 88
            return name_candidates[0], method, confidence, warning
        if len(name_candidates) > 1:
            return None, "ambiguous_name_position", 0, "ambiguous_name_position"
        return None, "unmatched", 0, "unmatched_player"


def normalize_player_name(value: object) -> str:
    normalized = str(value or "").lower()
    normalized = normalized.replace("&", "and")
    normalized = re.sub(r"['’`.\-]", "", normalized)
    normalized = re.sub(r"\b(jr|sr|ii|iii|iv|v)\b", "", normalized)
    normalized = re.sub(r"[^a-z0-9]+", "", normalized)
    return normalized.strip()


def _merge_candidate(
    by_key: dict[str, ModelIdentityCandidate],
    candidate: ModelIdentityCandidate,
) -> None:
    key = _candidate_key(candidate)
    if not key:
        return
    existing = by_key.get(key)
    if not existing:
        by_key[key] = candidate
        return
    existing.names.update(name for name in candidate.names if name)
    existing.source.update(candidate.source)
    existing.model_player_name = _preferred_name(
        existing.model_player_name,
        candidate.model_player_name,
    )
    existing.team = existing.team or candidate.team
    existing.sleeper_id = existing.sleeper_id or candidate.sleeper_id
    existing.gsis_id = existing.gsis_id or candidate.gsis_id


def _merge_truth_set_candidate(
    by_key: dict[str, ModelIdentityCandidate],
    candidate: ModelIdentityCandidate,
) -> None:
    name_key = normalize_player_name(candidate.model_player_name)
    matching_existing = [
        existing
        for existing in by_key.values()
        if existing.position == candidate.position
        and any(normalize_player_name(name) == name_key for name in existing.names)
    ]
    if len(matching_existing) == 1:
        existing = matching_existing[0]
        existing.names.update(name for name in candidate.names if name)
        existing.source.update(candidate.source)
        existing.team = existing.team or candidate.team
        return
    if len(matching_existing) > 1:
        return
    _merge_candidate(by_key, candidate)


def _candidate_key(candidate: ModelIdentityCandidate) -> str:
    if candidate.sleeper_id:
        return f"sleeper:{candidate.sleeper_id}"
    if candidate.gsis_id:
        return f"gsis:{candidate.gsis_id}"
    name_key = normalize_player_name(candidate.model_player_name)
    if name_key and candidate.position:
        return f"name:{name_key}:{candidate.position}"
    return ""


def _preferred_name(existing: str, incoming: str) -> str:
    if not existing:
        return incoming
    if not incoming:
        return existing
    if normalize_player_name(existing) == normalize_player_name(incoming):
        return incoming if len(incoming) > len(existing) else existing
    return existing


def _best_display_name(names: set[str]) -> str:
    clean_names = [name for name in names if name]
    if not clean_names:
        return ""
    return sorted(clean_names, key=lambda value: (normalize_player_name(value), len(value)))[-1]


def _unique_candidates(
    candidates: list[ModelIdentityCandidate],
) -> list[ModelIdentityCandidate]:
    by_key = {
        _candidate_key(candidate): candidate
        for candidate in candidates
        if _candidate_key(candidate)
    }
    return list(by_key.values())


def _team_key(value: object) -> str:
    team = str(value or "").strip().upper()
    return TEAM_ALIASES.get(team, team)


def _summary(
    mapping_rows: list[dict[str, object]],
    unresolved_rows: list[dict[str, object]],
    candidates: tuple[ModelIdentityCandidate, ...],
    clean_rows_path: str | Path,
) -> dict[str, object]:
    warning_counts: dict[str, int] = {}
    method_counts: dict[str, int] = {}
    for row in mapping_rows:
        warning = str(row.get("warning") or "none")
        method = str(row.get("match_method") or "unknown")
        warning_counts[warning] = warning_counts.get(warning, 0) + 1
        method_counts[method] = method_counts.get(method, 0) + 1
    matched = [row for row in mapping_rows if row.get("matched_model_player")]
    return {
        "status": "ready",
        "review_status": "review_only",
        "clean_rows_path": str(clean_rows_path),
        "fantasypros_rows": len(mapping_rows),
        "matched_rows": len(matched),
        "unresolved_rows": len(unresolved_rows),
        "model_identity_candidates": len(candidates),
        "match_methods": json.dumps(method_counts, sort_keys=True),
        "warnings": json.dumps(warning_counts, sort_keys=True),
        "ambiguous_rows_silently_merged": False,
        "active_rankings_overwritten": False,
        "model_scores_changed": False,
    }


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def _read_rows_if_exists(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    return _read_rows(path)


def _write_csv(
    path: Path,
    fieldnames: tuple[str, ...],
    rows: tuple[dict[str, object], ...] | list[dict[str, object]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
