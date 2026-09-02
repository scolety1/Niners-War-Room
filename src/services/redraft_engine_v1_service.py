from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import re
import shutil
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass, field, replace
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

REDRAFT_AUTHORITY_LABEL = "REDRAFT V1 - REVIEW"
DYNASTY_AUTHORITY_LABEL = "DYNASTY - LONG TERM"
MODEL_FAMILY = "R2_FLEX_AWARE_REPLACEMENT"
SCHEMA_VERSION = 1
SUPPORTED_POSITIONS = ("QB", "RB", "WR", "TE", "K", "DST")
FLEX_POSITIONS = ("RB", "WR", "TE")
SUPERFLEX_POSITIONS = ("QB", "RB", "WR", "TE")
PROJECTION_REQUIRED_COLUMNS = (
    "player_id",
    "player_name",
    "position",
    "team",
    "season",
    "source_status",
    "evidence_status",
)
PROJECTION_NUMERIC_COLUMNS = (
    "games",
    "passing_yards",
    "passing_tds",
    "interceptions",
    "rushing_yards",
    "rushing_tds",
    "receiving_yards",
    "receptions",
    "receiving_tds",
    "passing_first_downs",
    "rushing_first_downs",
    "receiving_first_downs",
    "return_yards",
    "return_tds",
    "fumbles_lost",
    "passing_300_games",
    "rushing_100_games",
    "receiving_100_games",
    "projected_points_override",
    "projection_low",
    "projection_high",
    "availability_probability",
)
BONUS_FIELDS = {
    "passing_300_game": "passing_300_games",
    "rushing_100_game": "rushing_100_games",
    "receiving_100_game": "receiving_100_games",
}
ADMITTED_SOURCE_STATUSES = {"GOVERNED"}
ADMITTED_EVIDENCE_STATUSES = {"AVAILABLE", "ADMITTED_CURRENT_SEASON"}
MINIMUM_POSITION_DEPTHS = {"QB": 20, "RB": 40, "WR": 50, "TE": 20}
MAX_PROJECTION_AGE_DAYS = 30
APPROVAL_AUTHORITY = "NWR_DATA_GOVERNANCE"
APPROVAL_STATUS = "APPROVED_FOR_REDRAFT_V1"


class RedraftValidationError(ValueError):
    pass


class RedraftPersistenceError(RuntimeError):
    pass


@dataclass(frozen=True)
class RosterSettings:
    qb: int = 1
    rb: int = 2
    wr: int = 2
    te: int = 1
    flex: int = 1
    superflex: int = 0
    k: int = 0
    dst: int = 0
    bench_size: int = 6


@dataclass(frozen=True)
class ScoringSettings:
    passing_yards: float = 0.04
    passing_td: float = 4.0
    interception: float = -2.0
    rushing_yards: float = 0.1
    rushing_td: float = 6.0
    receiving_yards: float = 0.1
    reception: float = 0.0
    receiving_td: float = 6.0
    passing_first_down: float = 0.0
    rushing_first_down: float = 0.0
    receiving_first_down: float = 0.0
    return_yards: float = 0.0
    return_td: float = 6.0
    fumble_lost: float = -2.0
    te_premium: float = 0.0
    bonuses: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class DraftContext:
    draft_type: str = "snake"
    draft_slot: int | None = None
    rounds: int = 16
    keeper_count: int = 0
    auction_budget: int | None = None
    roster_limits: dict[str, int] = field(default_factory=dict)
    adp_context_enabled: bool = False
    replacement_method: str = "expected_available"


@dataclass(frozen=True)
class LeagueProfile:
    profile_id: str
    league_name: str
    season: int
    team_count: int
    roster: RosterSettings
    scoring: ScoringSettings
    draft: DraftContext
    preset_key: str | None = None
    archived: bool = False
    created_at_utc: str = ""
    updated_at_utc: str = ""
    practical_mode: bool = False
    # Profile ids scope local Redraft state. External identity distinguishes
    # same-named league workspaces without changing any scoring model.
    provider: str = "local"
    provider_league_id: str | None = None
    schema_version: int = SCHEMA_VERSION


@dataclass(frozen=True)
class ProjectionPlayer:
    player_id: str
    player_name: str
    position: str
    team: str
    season: int
    source_status: str
    evidence_status: str
    source_as_of: str = ""
    rookie: bool = False
    stats: dict[str, float | None] = field(default_factory=dict)
    # True only when this row's normal 30-day source_as_of freshness gate was
    # bypassed under an explicit, narrowly-scoped, SHA-bound, time-limited
    # owner draft-day authorization (see _load_draft_day_authorization). The
    # projection VALUE and source_as_of date are never altered -- this is a
    # display/authority label, not a freshness claim.
    draft_day_prior_override: bool = False


@dataclass(frozen=True)
class ProjectionSnapshot:
    season: int
    source_path: Path
    source_sha256: str
    players: tuple[ProjectionPlayer, ...]
    blocked_rows: tuple[dict[str, str], ...]
    errors: tuple[str, ...]
    source_as_of: str


@dataclass(frozen=True)
class ReplacementLevel:
    position: str
    starter_count: int
    rostered_count: int
    starter_cutoff_points: float
    replacement_points: float


@dataclass(frozen=True)
class RedraftRankingRow:
    overall_rank: int
    position_rank: int
    player_id: str
    player_name: str
    position: str
    team: str
    projected_points: float
    replacement_points: float
    replacement_adjusted_value: float
    starter_gap: float
    confidence: str
    tier: int
    profile_id: str
    profile_name: str
    source_status: str
    evidence_status: str
    source_as_of: str
    rookie: bool
    authority_label: str = REDRAFT_AUTHORITY_LABEL
    model_family: str = MODEL_FAMILY
    position_tier: int = 1
    overall_tier_label: str = "Tier 1 · Elite"
    position_tier_label: str = "Position Tier 1"


@dataclass(frozen=True)
class RankingResult:
    profile: LeagueProfile
    rows: tuple[RedraftRankingRow, ...]
    replacement_levels: tuple[ReplacementLevel, ...]
    blocked_rows: tuple[dict[str, str], ...]
    generated_at_utc: str
    projection_sha256: str
    errors: tuple[str, ...] = ()

    @property
    def ready(self) -> bool:
        return bool(self.rows) and not self.errors


@dataclass(frozen=True)
class RedraftHealthReport:
    status: str
    player_universe_available: bool
    current_season_forecast_available: bool
    scoring_profile_valid: bool
    replacement_calculation_valid: bool
    ranked_players: int
    blocked_players: int
    last_generated_timestamp: str
    messages: tuple[str, ...]


def utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def redraft_store_root(repo_root: str | Path | None = None) -> Path:
    configured = os.environ.get("NWR_REDRAFT_HOME", "").strip()
    if configured:
        return Path(configured).expanduser().resolve()
    base = Path(repo_root).resolve() if repo_root else Path(__file__).resolve().parents[2]
    return base / "local_exports" / "redraft_v1"


def builtin_presets() -> tuple[LeagueProfile, ...]:
    definitions = (
        ("10_TEAM_1QB_STANDARD", "10-team 1QB Standard", 10, 0.0, 0),
        ("12_TEAM_1QB_HALF_PPR", "12-team 1QB Half-PPR", 12, 0.5, 0),
        ("12_TEAM_PPR", "12-team PPR", 12, 1.0, 0),
        ("12_TEAM_SUPERFLEX_PPR", "12-team Superflex PPR", 12, 1.0, 1),
    )
    rows: list[LeagueProfile] = []
    for key, name, teams, reception, superflex in definitions:
        rows.append(
            LeagueProfile(
                profile_id=f"preset:{key}",
                league_name=name,
                season=2026,
                team_count=teams,
                roster=RosterSettings(superflex=superflex),
                scoring=ScoringSettings(reception=reception),
                draft=DraftContext(rounds=16),
                preset_key=key,
            )
        )
    return tuple(rows)


def validate_profile(profile: LeagueProfile) -> None:
    if profile.schema_version != SCHEMA_VERSION:
        raise RedraftValidationError("Unsupported redraft profile schema version.")
    if not profile.profile_id or not re.fullmatch(r"[A-Za-z0-9._:-]+", profile.profile_id):
        raise RedraftValidationError("Profile id contains unsupported characters.")
    if not profile.league_name.strip():
        raise RedraftValidationError("League name is required.")
    if profile.provider not in {"local", "sleeper", "espn", "fantasypros"}:
        raise RedraftValidationError(
            "League provider must be local, sleeper, espn, or fantasypros."
        )
    if profile.provider == "sleeper":
        if not profile.provider_league_id or not re.fullmatch(
            r"[A-Za-z0-9_-]+", profile.provider_league_id
        ):
            raise RedraftValidationError("Sleeper profiles require a valid Sleeper league id.")
    elif profile.provider_league_id is not None:
        raise RedraftValidationError("Only Sleeper profiles may include a provider league id.")
    if not 2000 <= profile.season <= 2100:
        raise RedraftValidationError("Season must be between 2000 and 2100.")
    if not 2 <= profile.team_count <= 32:
        raise RedraftValidationError("Team count must be between 2 and 32.")
    roster_values = asdict(profile.roster)
    for name, value in roster_values.items():
        if not isinstance(value, int) or value < 0:
            raise RedraftValidationError(f"Roster field {name} must be a non-negative integer.")
    if sum(value for key, value in roster_values.items() if key != "bench_size") <= 0:
        raise RedraftValidationError("At least one starting roster slot is required.")
    if profile.roster.bench_size > 40:
        raise RedraftValidationError("Bench size cannot exceed 40.")
    if profile.draft.draft_type not in {"snake", "auction"}:
        raise RedraftValidationError("Draft type must be snake or auction.")
    if profile.draft.replacement_method not in {"starter_cutoff", "expected_available"}:
        raise RedraftValidationError("Unsupported replacement method.")
    if not 1 <= profile.draft.rounds <= 40:
        raise RedraftValidationError("Draft rounds must be between 1 and 40.")
    if (
        profile.draft.draft_slot is not None
        and not 1 <= profile.draft.draft_slot <= profile.team_count
    ):
        raise RedraftValidationError("Draft slot must be within the league team count.")
    if profile.draft.keeper_count < 0:
        raise RedraftValidationError("Keeper count cannot be negative.")
    if profile.draft.auction_budget is not None and profile.draft.auction_budget <= 0:
        raise RedraftValidationError("Auction budget must be positive when configured.")
    for position, limit in profile.draft.roster_limits.items():
        if position.upper() not in SUPPORTED_POSITIONS or int(limit) < 0:
            raise RedraftValidationError(
                "Roster limits must use supported positions and non-negative values."
            )
    for name, value in asdict(profile.scoring).items():
        if name == "bonuses":
            continue
        if not isinstance(value, (int, float)) or not math.isfinite(float(value)):
            raise RedraftValidationError(f"Scoring field {name} must be finite.")
    unsupported_bonuses = set(profile.scoring.bonuses) - set(BONUS_FIELDS)
    if unsupported_bonuses:
        raise RedraftValidationError(
            "Unsupported bonuses: " + ", ".join(sorted(unsupported_bonuses))
        )


def _profile_path(root: Path, profile_id: str) -> Path:
    safe = re.sub(r"[^A-Za-z0-9._-]", "_", profile_id)
    return root / "profiles" / f"{safe}.json"


def _profile_document(profile: LeagueProfile) -> dict[str, Any]:
    return asdict(profile)


def _normalized_profile(profile: LeagueProfile) -> LeagueProfile:
    normalized_limits = {
        str(position).strip().upper(): int(limit)
        for position, limit in profile.draft.roster_limits.items()
    }
    return replace(
        profile,
        draft=replace(profile.draft, roster_limits=normalized_limits),
    )


def _profile_from_document(document: Mapping[str, Any]) -> LeagueProfile:
    try:
        profile = LeagueProfile(
            profile_id=str(document["profile_id"]),
            league_name=str(document["league_name"]),
            season=int(document["season"]),
            team_count=int(document["team_count"]),
            roster=RosterSettings(**dict(document["roster"])),
            scoring=ScoringSettings(**dict(document["scoring"])),
            draft=DraftContext(**dict(document["draft"])),
            preset_key=(str(document["preset_key"]) if document.get("preset_key") else None),
            archived=bool(document.get("archived", False)),
            created_at_utc=str(document.get("created_at_utc", "")),
            updated_at_utc=str(document.get("updated_at_utc", "")),
            practical_mode=bool(document.get("practical_mode", False)),
            provider=str(document.get("provider", "local")),
            provider_league_id=(
                str(document["provider_league_id"]) if document.get("provider_league_id") else None
            ),
            schema_version=int(document.get("schema_version", 0)),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise RedraftValidationError(f"Invalid league profile document: {exc}") from exc
    profile = _normalized_profile(profile)
    validate_profile(profile)
    return profile


def _atomic_json(path: Path, document: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    try:
        temporary.write_text(
            json.dumps(document, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        os.replace(temporary, path)
    except OSError as exc:
        temporary.unlink(missing_ok=True)
        raise RedraftPersistenceError(f"Could not persist redraft state: {exc}") from exc


def list_profiles(root: str | Path, *, include_archived: bool = False) -> tuple[LeagueProfile, ...]:
    profiles_dir = Path(root) / "profiles"
    if not profiles_dir.exists():
        return ()
    profiles: list[LeagueProfile] = []
    for path in sorted(profiles_dir.glob("*.json")):
        try:
            profile = _profile_from_document(json.loads(path.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError, TypeError, ValueError, KeyError):
            continue
        if include_archived or not profile.archived:
            profiles.append(profile)
    return tuple(sorted(profiles, key=lambda item: (item.league_name.casefold(), item.profile_id)))


def profile_store_errors(root: str | Path) -> tuple[str, ...]:
    profiles_dir = Path(root) / "profiles"
    errors: list[str] = []
    for path in sorted(profiles_dir.glob("*.json")):
        try:
            _profile_from_document(json.loads(path.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError, TypeError, ValueError, KeyError):
            errors.append(f"{path.name}: unreadable or invalid profile state")
    return tuple(errors)


def load_profile(root: str | Path, profile_id: str) -> LeagueProfile:
    path = _profile_path(Path(root), profile_id)
    if not path.is_file():
        raise RedraftPersistenceError(f"Redraft profile not found: {profile_id}")
    return _profile_from_document(json.loads(path.read_text(encoding="utf-8")))


def create_profile(
    root: str | Path,
    template: LeagueProfile,
    *,
    league_name: str | None = None,
) -> LeagueProfile:
    now = utc_now()
    profile = replace(
        template,
        profile_id=uuid4().hex,
        league_name=(league_name or template.league_name).strip(),
        archived=False,
        created_at_utc=now,
        updated_at_utc=now,
    )
    profile = _normalized_profile(profile)
    validate_profile(profile)
    path = _profile_path(Path(root), profile.profile_id)
    if path.exists():
        raise RedraftPersistenceError("Generated redraft profile id already exists.")
    _atomic_json(path, _profile_document(profile))
    return profile


def save_profile(root: str | Path, profile: LeagueProfile) -> LeagueProfile:
    path = _profile_path(Path(root), profile.profile_id)
    if not path.is_file():
        raise RedraftPersistenceError("Cannot edit a redraft profile that does not exist.")
    prior = load_profile(root, profile.profile_id)
    updated = _normalized_profile(
        replace(
            profile,
            created_at_utc=prior.created_at_utc,
            updated_at_utc=utc_now(),
        )
    )
    validate_profile(updated)
    _atomic_json(path, _profile_document(updated))
    return updated


def duplicate_profile(
    root: str | Path, profile_id: str, *, league_name: str | None = None
) -> LeagueProfile:
    source = load_profile(root, profile_id)
    return create_profile(
        root,
        replace(source, preset_key=source.preset_key, provider="local", provider_league_id=None),
        league_name=league_name or f"{source.league_name} Copy",
    )


def reconcile_sleeper_profile_identities(root: str | Path) -> tuple[LeagueProfile, ...]:
    """Attach stable Sleeper identity to legacy receipt-backed profiles.

    This is a local metadata migration only: scoring, roster settings, draft
    state, and the existing profile id are retained exactly as stored.
    """

    root_path = Path(root)
    reconciled: list[LeagueProfile] = []
    for profile in list_profiles(root_path, include_archived=True):
        receipt_path = root_path / "sleeper_imports" / f"{profile.profile_id}.json"
        if not receipt_path.is_file():
            reconciled.append(profile)
            continue
        try:
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            league = receipt["league"]
            league_id = str(league["league_id"])
            season = int(league["season"])
        except (OSError, ValueError, KeyError, TypeError):
            reconciled.append(profile)
            continue
        if not re.fullmatch(r"[A-Za-z0-9_-]+", league_id) or season != profile.season:
            reconciled.append(profile)
            continue
        if profile.provider == "sleeper" and profile.provider_league_id == league_id:
            reconciled.append(profile)
            continue
        reconciled.append(
            save_profile(
                root_path,
                replace(profile, provider="sleeper", provider_league_id=league_id),
            )
        )
    return tuple(reconciled)


def archive_profile(root: str | Path, profile_id: str) -> LeagueProfile:
    profile = load_profile(root, profile_id)
    archived = save_profile(root, replace(profile, archived=True))
    if active_profile_id(root) == profile_id:
        _atomic_json(Path(root) / "active_profile.json", {"profile_id": None})
    return archived


def restore_profile(root: str | Path, profile_id: str) -> LeagueProfile:
    profile = load_profile(root, profile_id)
    if not profile.archived:
        raise RedraftValidationError("Only an archived redraft profile can be restored.")
    return save_profile(root, replace(profile, archived=False))


def delete_profile(root: str | Path, profile_id: str, *, confirmed: bool) -> None:
    if not confirmed:
        raise RedraftValidationError("Permanent profile deletion requires confirmation.")
    path = _profile_path(Path(root), profile_id)
    if not path.is_file():
        raise RedraftPersistenceError(f"Redraft profile not found: {profile_id}")
    path.unlink()
    board = Path(root) / "draft_boards" / f"{profile_id}.json"
    board.unlink(missing_ok=True)
    board.with_suffix(".backup.json").unlink(missing_ok=True)
    if active_profile_id(root) == profile_id:
        _atomic_json(Path(root) / "active_profile.json", {"profile_id": None})


def set_active_profile(root: str | Path, profile_id: str) -> LeagueProfile:
    profile = load_profile(root, profile_id)
    if profile.archived:
        raise RedraftValidationError("An archived redraft profile cannot be active.")
    _atomic_json(Path(root) / "active_profile.json", {"profile_id": profile_id})
    return profile


def active_profile_id(root: str | Path) -> str | None:
    path = Path(root) / "active_profile.json"
    if not path.is_file():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8")).get("profile_id")
    except (OSError, json.JSONDecodeError):
        return None
    return str(value) if value else None


def active_profile(root: str | Path) -> LeagueProfile | None:
    profile_id = active_profile_id(root)
    if not profile_id:
        return None
    try:
        profile = load_profile(root, profile_id)
    except (RedraftPersistenceError, RedraftValidationError, OSError, json.JSONDecodeError):
        return None
    return None if profile.archived else profile


def projection_snapshot_path(root: str | Path, season: int) -> Path:
    return Path(root) / "projections" / str(season) / "current.csv"


def projection_manifest_path(root: str | Path, season: int) -> Path:
    return projection_snapshot_path(root, season).with_suffix(".manifest.json")


def projection_approval_path(root: str | Path, season: int) -> Path:
    return projection_snapshot_path(root, season).with_suffix(".approval.json")


def install_projection_snapshot(
    root: str | Path,
    season: int,
    source: str | Path,
    approval_receipt: str | Path,
) -> ProjectionSnapshot:
    source_path = Path(source).resolve()
    snapshot = load_projection_snapshot(source_path, season=season)
    if snapshot.errors:
        raise RedraftValidationError(
            "Projection snapshot failed validation: " + "; ".join(snapshot.errors)
        )
    receipt_path = Path(approval_receipt).resolve()
    receipt, receipt_digest = _validate_approval_receipt(
        receipt_path,
        season=season,
        source_sha256=snapshot.source_sha256,
    )
    destination = projection_snapshot_path(root, season)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f".{destination.name}.{uuid4().hex}.tmp")
    approval_destination = destination.with_suffix(".approval.json")
    approval_temporary = approval_destination.with_name(
        f".{approval_destination.name}.{uuid4().hex}.tmp"
    )
    try:
        shutil.copyfile(source_path, temporary)
        shutil.copyfile(receipt_path, approval_temporary)
        os.replace(temporary, destination)
        os.replace(approval_temporary, approval_destination)
    except OSError as exc:
        temporary.unlink(missing_ok=True)
        approval_temporary.unlink(missing_ok=True)
        raise RedraftPersistenceError(f"Could not install projection snapshot: {exc}") from exc
    _atomic_json(
        destination.with_suffix(".manifest.json"),
        {
            "schema_version": SCHEMA_VERSION,
            "season": season,
            "source_sha256": snapshot.source_sha256,
            "player_rows": len(snapshot.players),
            "blocked_rows": len(snapshot.blocked_rows),
            "source_filename": source_path.name,
            "admission_policy": "GOVERNED_CURRENT_SEASON_V1",
            "approval_receipt_sha256": receipt_digest,
            "approval_authority": receipt["authority"],
            "approval_status": receipt["approval_status"],
            "approval_source_id": receipt["source_id"],
            "approved_by": receipt["approved_by"],
            "approved_at_utc": receipt["approved_at_utc"],
            "valid_until": receipt["valid_until"],
            "installed_at_utc": utc_now(),
        },
    )
    return load_projection_snapshot(destination, season=season, require_manifest=True)


DRAFT_DAY_AUTHORIZATION_FILENAME = "DRAFT_DAY_AUTHORIZATION.json"
DRAFT_DAY_AUTHORIZATION_LABEL = "OWNER_DRAFT_DAY_APPROVAL_2026_KHA"


def _load_draft_day_authorization(snapshot_dir: Path, *, source_sha256: str) -> frozenset[str]:
    """Return the set of player_ids explicitly authorized, tonight, to bypass
    the normal source_as_of freshness gate -- ONLY if every safety condition
    holds. Any failure returns an empty set (i.e. the normal, safe, blocked
    behavior), never an exception -- this is a narrow, self-expiring, opt-in
    relaxation, not a new default.

    Conditions, all required:
      - the authorization file exists next to the projection snapshot;
      - its label is exactly DRAFT_DAY_AUTHORIZATION_LABEL;
      - its bound_source_sha256 matches the snapshot actually being loaded
        (if the projection artifact ever changes, this authorization goes
        inert automatically -- "if the artifact hash differs, STOP");
      - it has not passed its own expires_at_utc.
    """
    path = snapshot_dir / DRAFT_DAY_AUTHORIZATION_FILENAME
    if not path.is_file():
        return frozenset()
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError):
        return frozenset()
    if not isinstance(document, dict):
        return frozenset()
    if document.get("label") != DRAFT_DAY_AUTHORIZATION_LABEL:
        return frozenset()
    if str(document.get("bound_source_sha256") or "") != source_sha256:
        return frozenset()
    try:
        expires_at = datetime.fromisoformat(str(document.get("expires_at_utc") or "").replace("Z", "+00:00"))
    except ValueError:
        return frozenset()
    if expires_at.tzinfo is None or datetime.now(UTC) > expires_at.astimezone(UTC):
        return frozenset()
    player_ids = document.get("player_ids")
    if not isinstance(player_ids, list):
        return frozenset()
    return frozenset(str(value) for value in player_ids)


def load_projection_snapshot(
    path: str | Path,
    *,
    season: int,
    require_manifest: bool = False,
) -> ProjectionSnapshot:
    source_path = Path(path)
    if not source_path.is_file():
        return ProjectionSnapshot(
            season=season,
            source_path=source_path,
            source_sha256="",
            players=(),
            blocked_rows=(),
            errors=(f"Governed {season} projection snapshot is missing.",),
            source_as_of="",
        )
    source_bytes = source_path.read_bytes()
    digest = hashlib.sha256(source_bytes).hexdigest()
    stale_override_ids = _load_draft_day_authorization(source_path.parent, source_sha256=digest)
    errors: list[str] = []
    players: list[ProjectionPlayer] = []
    blocked: list[dict[str, str]] = []
    seen: set[str] = set()
    source_as_of_values: set[str] = set()
    with source_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        columns = tuple(reader.fieldnames or ())
        missing = [column for column in PROJECTION_REQUIRED_COLUMNS if column not in columns]
        if missing:
            errors.append("Projection snapshot is missing columns: " + ", ".join(missing))
        else:
            for line_number, row in enumerate(reader, start=2):
                player_id = str(row.get("player_id", "")).strip()
                name = str(row.get("player_name", "")).strip()
                position = str(row.get("position", "")).strip().upper()
                row_season = _optional_int(row.get("season"))
                source_status = str(row.get("source_status", "")).strip().upper()
                evidence_status = str(row.get("evidence_status", "")).strip().upper()
                source_as_of = str(row.get("source_as_of", "")).strip()
                reason = ""
                if not player_id or not name:
                    reason = "missing player identity"
                elif player_id in seen:
                    reason = "duplicate player_id"
                elif position not in SUPPORTED_POSITIONS:
                    reason = "unsupported position"
                elif row_season != season:
                    reason = "season mismatch"
                elif source_status not in ADMITTED_SOURCE_STATUSES:
                    reason = f"source status {source_status.lower() or 'missing'} is not admitted"
                elif evidence_status not in ADMITTED_EVIDENCE_STATUSES:
                    reason = (
                        f"evidence status {evidence_status.lower() or 'missing'} is not admitted"
                    )
                else:
                    reason = _source_as_of_reason(source_as_of, season)
                draft_day_override_applied = False
                if (
                    reason
                    and reason.endswith("freshness window")
                    and player_id in stale_override_ids
                ):
                    reason = ""
                    draft_day_override_applied = True
                stats: dict[str, float | None] = {
                    column: _optional_float(row.get(column))
                    for column in PROJECTION_NUMERIC_COLUMNS
                }
                if position in {"QB", "RB", "WR", "TE"} and not any(
                    stats.get(column) is not None
                    for column in (
                        "passing_yards",
                        "passing_tds",
                        "rushing_yards",
                        "rushing_tds",
                        "receiving_yards",
                        "receptions",
                        "receiving_tds",
                    )
                ):
                    reason = reason or "no scoreable projection components"
                if position in {"K", "DST"} and stats.get("projected_points_override") is None:
                    reason = reason or "K/DST requires governed projected_points_override"
                if reason:
                    blocked.append(
                        {
                            "line": str(line_number),
                            "player_id": player_id,
                            "player_name": name,
                            "position": position,
                            "reason": reason,
                        }
                    )
                    continue
                seen.add(player_id)
                if source_as_of:
                    source_as_of_values.add(source_as_of)
                players.append(
                    ProjectionPlayer(
                        player_id=player_id,
                        player_name=name,
                        position=position,
                        team=str(row.get("team", "")).strip().upper(),
                        season=season,
                        source_status=source_status,
                        evidence_status=evidence_status,
                        source_as_of=source_as_of,
                        rookie=_truthy(row.get("rookie")),
                        stats=stats,
                        draft_day_prior_override=draft_day_override_applied,
                    )
                )
    if players and not errors:
        counts = {
            position: sum(player.position == position for player in players)
            for position in MINIMUM_POSITION_DEPTHS
        }
        short = [
            f"{position} {counts[position]}/{minimum}"
            for position, minimum in MINIMUM_POSITION_DEPTHS.items()
            if counts[position] < minimum
        ]
        if short:
            errors.append(
                "Projection universe is below minimum admitted depth: " + ", ".join(short)
            )
    if not players and not errors:
        errors.append("Projection snapshot has no rankable player rows.")
    if require_manifest and not errors:
        errors.extend(
            _projection_manifest_errors(
                source_path,
                season=season,
                digest=digest,
                player_rows=len(players),
                blocked_rows=len(blocked),
            )
        )
    return ProjectionSnapshot(
        season=season,
        source_path=source_path,
        source_sha256=digest,
        players=tuple(players),
        blocked_rows=tuple(blocked),
        errors=tuple(errors),
        source_as_of=max(source_as_of_values) if source_as_of_values else "",
    )


def _source_as_of_reason(value: str, season: int) -> str:
    try:
        as_of = date.fromisoformat(value)
    except ValueError:
        return "source_as_of must be an ISO date"
    today = datetime.now(UTC).date()
    if as_of > today:
        return "source_as_of is in the future"
    earliest = date(season - 1, 12, 1)
    if as_of < earliest:
        return f"source_as_of is stale for the {season} season"
    if (today - as_of).days > MAX_PROJECTION_AGE_DAYS:
        return f"source_as_of exceeds the {MAX_PROJECTION_AGE_DAYS}-day freshness window"
    return ""


def _validate_approval_receipt(
    receipt_path: Path,
    *,
    season: int,
    source_sha256: str,
) -> tuple[dict[str, Any], str]:
    if not receipt_path.is_file():
        raise RedraftValidationError("Independent projection approval receipt is missing.")
    try:
        data = receipt_path.read_bytes()
    except OSError as exc:
        raise RedraftValidationError("Projection approval receipt is unreadable.") from exc
    try:
        receipt = json.loads(data.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RedraftValidationError("Projection approval receipt is unreadable.") from exc
    if not isinstance(receipt, dict):
        raise RedraftValidationError("Projection approval receipt must be a JSON object.")
    required = (
        "schema_version",
        "authority",
        "approval_status",
        "season",
        "source_sha256",
        "source_id",
        "approved_by",
        "approved_at_utc",
        "valid_until",
    )
    missing = [field for field in required if field not in receipt]
    if missing:
        raise RedraftValidationError(
            "Projection approval receipt is missing: " + ", ".join(missing)
        )
    if receipt["schema_version"] != SCHEMA_VERSION:
        raise RedraftValidationError("Projection approval receipt schema is unsupported.")
    if receipt["authority"] != APPROVAL_AUTHORITY or receipt["approval_status"] != APPROVAL_STATUS:
        raise RedraftValidationError("Projection approval receipt is not independently admitted.")
    try:
        receipt_season = int(receipt["season"])
    except (TypeError, ValueError) as exc:
        raise RedraftValidationError("Projection approval season is invalid.") from exc
    if receipt_season != season or receipt["source_sha256"] != source_sha256:
        raise RedraftValidationError("Projection approval receipt does not bind this snapshot.")
    if not str(receipt["source_id"]).strip() or not str(receipt["approved_by"]).strip():
        raise RedraftValidationError("Projection approval source and approver are required.")
    try:
        approved_at = datetime.fromisoformat(str(receipt["approved_at_utc"]).replace("Z", "+00:00"))
        valid_until = date.fromisoformat(str(receipt["valid_until"]))
    except ValueError as exc:
        raise RedraftValidationError("Projection approval dates are invalid.") from exc
    today = datetime.now(UTC).date()
    if approved_at.tzinfo is None or approved_at.astimezone(UTC).date() > today:
        raise RedraftValidationError("Projection approval timestamp is invalid or in the future.")
    if valid_until < today:
        raise RedraftValidationError("Projection approval receipt has expired.")
    return receipt, hashlib.sha256(data).hexdigest()


def _projection_manifest_errors(
    source_path: Path,
    *,
    season: int,
    digest: str,
    player_rows: int,
    blocked_rows: int,
) -> list[str]:
    manifest_path = source_path.with_suffix(".manifest.json")
    if not manifest_path.is_file():
        return ["Installed projection manifest is missing."]
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ["Installed projection manifest is unreadable."]
    if not isinstance(manifest, dict):
        return ["Installed projection manifest must be a JSON object."]
    expected = {
        "schema_version": SCHEMA_VERSION,
        "season": season,
        "source_sha256": digest,
        "player_rows": player_rows,
        "blocked_rows": blocked_rows,
        "admission_policy": "GOVERNED_CURRENT_SEASON_V1",
        "approval_authority": APPROVAL_AUTHORITY,
        "approval_status": APPROVAL_STATUS,
    }
    mismatches = [key for key, value in expected.items() if manifest.get(key) != value]
    approval_path = source_path.with_suffix(".approval.json")
    try:
        receipt, receipt_digest = _validate_approval_receipt(
            approval_path,
            season=season,
            source_sha256=digest,
        )
    except RedraftValidationError as exc:
        return [str(exc)]
    approval_expected = {
        "approval_receipt_sha256": receipt_digest,
        "approval_source_id": receipt["source_id"],
        "approved_by": receipt["approved_by"],
        "approved_at_utc": receipt["approved_at_utc"],
        "valid_until": receipt["valid_until"],
    }
    mismatches.extend(key for key, value in approval_expected.items() if manifest.get(key) != value)
    return (
        ["Installed projection manifest mismatch: " + ", ".join(mismatches)] if mismatches else []
    )


def score_projection(player: ProjectionPlayer, scoring: ScoringSettings) -> float:
    stats = player.stats
    if player.position in {"K", "DST"}:
        override = stats.get("projected_points_override")
        if override is None:
            raise RedraftValidationError("K/DST projection is missing governed point override.")
        return round(float(override), 4)
    value = 0.0
    value += _number(stats.get("passing_yards")) * scoring.passing_yards
    value += _number(stats.get("passing_tds")) * scoring.passing_td
    value += _number(stats.get("interceptions")) * scoring.interception
    value += _number(stats.get("rushing_yards")) * scoring.rushing_yards
    value += _number(stats.get("rushing_tds")) * scoring.rushing_td
    value += _number(stats.get("receiving_yards")) * scoring.receiving_yards
    value += _number(stats.get("receptions")) * scoring.reception
    value += _number(stats.get("receiving_tds")) * scoring.receiving_td
    value += _number(stats.get("passing_first_downs")) * scoring.passing_first_down
    value += _number(stats.get("rushing_first_downs")) * scoring.rushing_first_down
    value += _number(stats.get("receiving_first_downs")) * scoring.receiving_first_down
    value += _number(stats.get("return_yards")) * scoring.return_yards
    value += _number(stats.get("return_tds")) * scoring.return_td
    value += _number(stats.get("fumbles_lost")) * scoring.fumble_lost
    if player.position == "TE":
        value += _number(stats.get("receptions")) * scoring.te_premium
    for bonus_name, points in scoring.bonuses.items():
        value += _number(stats.get(BONUS_FIELDS[bonus_name])) * float(points)
    return round(value, 4)


def _required_position_counts(profile: LeagueProfile) -> dict[str, int]:
    return {
        "QB": profile.team_count * profile.roster.qb,
        "RB": profile.team_count * profile.roster.rb,
        "WR": profile.team_count * profile.roster.wr,
        "TE": profile.team_count * profile.roster.te,
        "K": profile.team_count * profile.roster.k,
        "DST": profile.team_count * profile.roster.dst,
    }


def calculate_replacement_levels(
    profile: LeagueProfile,
    scored_players: Sequence[tuple[ProjectionPlayer, float]],
) -> tuple[ReplacementLevel, ...]:
    validate_profile(profile)
    ordered = sorted(
        scored_players,
        key=lambda item: (-item[1], item[0].position, item[0].player_id),
    )
    by_position: dict[str, list[tuple[ProjectionPlayer, float]]] = {
        position: [] for position in SUPPORTED_POSITIONS
    }
    for item in ordered:
        by_position[item[0].position].append(item)
    required = _required_position_counts(profile)
    selected: set[str] = set()
    starter_counts = dict(required)
    for position, count in required.items():
        for player, _points in by_position[position][:count]:
            selected.add(player.player_id)

    def allocate_flexible(count: int, positions: Sequence[str]) -> None:
        candidates = [
            item
            for item in ordered
            if item[0].position in positions and item[0].player_id not in selected
        ]
        for player, _points in candidates[:count]:
            selected.add(player.player_id)
            starter_counts[player.position] += 1

    allocate_flexible(profile.team_count * profile.roster.flex, FLEX_POSITIONS)
    allocate_flexible(profile.team_count * profile.roster.superflex, SUPERFLEX_POSITIONS)
    starter_selected = set(selected)

    if profile.draft.replacement_method == "expected_available":
        limits = {
            position: _position_roster_limit(profile, position, starter_counts[position])
            for position in SUPPORTED_POSITIONS
        }
        rostered_counts = {position: starter_counts[position] for position in SUPPORTED_POSITIONS}
        remaining = [item for item in ordered if item[0].player_id not in selected]
        bench_slots = profile.team_count * profile.roster.bench_size
        for player, _points in remaining:
            if bench_slots <= 0:
                break
            if rostered_counts[player.position] >= limits[player.position]:
                continue
            selected.add(player.player_id)
            rostered_counts[player.position] += 1
            bench_slots -= 1
    else:
        rostered_counts = dict(starter_counts)

    results: list[ReplacementLevel] = []
    for position in SUPPORTED_POSITIONS:
        position_rows = by_position[position]
        starter_points = _cutoff_points(position_rows, starter_counts[position])
        if profile.draft.replacement_method == "starter_cutoff":
            replacement_points = starter_points
        else:
            replacement_points = _next_available_points(position_rows, selected)
        results.append(
            ReplacementLevel(
                position=position,
                starter_count=starter_counts[position],
                rostered_count=rostered_counts[position],
                starter_cutoff_points=round(starter_points, 4),
                replacement_points=round(replacement_points, 4),
            )
        )
    if not starter_selected:
        raise RedraftValidationError("Replacement calculation produced no starters.")
    return tuple(results)


def _position_roster_limit(profile: LeagueProfile, position: str, starter_count: int) -> int:
    configured = next(
        (
            limit
            for configured_position, limit in profile.draft.roster_limits.items()
            if configured_position.upper() == position
        ),
        None,
    )
    if configured is not None:
        return profile.team_count * int(configured)
    per_team_starters = math.ceil(starter_count / profile.team_count) if starter_count else 0
    if position in {"QB", "TE"}:
        return profile.team_count * max(2, per_team_starters + 1)
    if position in {"K", "DST"}:
        return profile.team_count * max(1, per_team_starters)
    return profile.team_count * (per_team_starters + profile.roster.bench_size)


def _cutoff_points(rows: Sequence[tuple[ProjectionPlayer, float]], count: int) -> float:
    if count <= 0 or not rows:
        return 0.0
    index = min(count, len(rows)) - 1
    return rows[index][1]


def _next_available_points(
    rows: Sequence[tuple[ProjectionPlayer, float]],
    selected: set[str],
) -> float:
    for player, points in rows:
        if player.player_id not in selected:
            return points
    return 0.0


def generate_rankings(profile: LeagueProfile, snapshot: ProjectionSnapshot) -> RankingResult:
    validate_profile(profile)
    generated = utc_now()
    if snapshot.errors:
        return RankingResult(
            profile=profile,
            rows=(),
            replacement_levels=(),
            blocked_rows=snapshot.blocked_rows,
            generated_at_utc=generated,
            projection_sha256=snapshot.source_sha256,
            errors=snapshot.errors,
        )
    counts = {
        position: sum(player.position == position for player in snapshot.players)
        for position in SUPPORTED_POSITIONS
    }
    required = _required_position_counts(profile)
    insufficient = [
        f"{position} {counts[position]}/{count + 1}"
        for position, count in required.items()
        if count > 0
        and counts[position] < count + 1
        and not (profile.practical_mode and position in {"K", "DST"})
    ]
    if insufficient:
        return RankingResult(
            profile=profile,
            rows=(),
            replacement_levels=(),
            blocked_rows=snapshot.blocked_rows,
            generated_at_utc=generated,
            projection_sha256=snapshot.source_sha256,
            errors=(
                "Projection universe cannot support profile replacement depth: "
                + ", ".join(insufficient),
            ),
        )
    scored = [(player, score_projection(player, profile.scoring)) for player in snapshot.players]
    replacements = calculate_replacement_levels(profile, scored)
    replacement_by_position = {row.position: row for row in replacements}
    allowed_positions = {
        position for position, count in _required_position_counts(profile).items() if count > 0
    }
    if profile.roster.flex:
        allowed_positions.update(FLEX_POSITIONS)
    if profile.roster.superflex:
        allowed_positions.update(SUPERFLEX_POSITIONS)
    preliminary: list[dict[str, Any]] = []
    for player, projected in scored:
        if player.position not in allowed_positions:
            continue
        baseline = replacement_by_position[player.position]
        preliminary.append(
            {
                "player": player,
                "projected": projected,
                "replacement": baseline.replacement_points,
                "value": round(projected - baseline.replacement_points, 4),
                "starter_gap": round(projected - baseline.starter_cutoff_points, 4),
                "confidence": _confidence(player, projected),
            }
        )
    preliminary.sort(
        key=lambda row: (
            -row["value"],
            -row["projected"],
            row["player"].position,
            row["player"].player_id,
        )
    )
    tier_by_index = _tier_assignments(
        [float(row["value"]) for row in preliminary],
        maximum_tiers=64,
    )
    position_tier_by_player: dict[str, int] = {}
    for position in SUPPORTED_POSITIONS:
        position_rows = [item for item in preliminary if item["player"].position == position]
        assignments = _tier_assignments(
            [float(item["value"]) for item in position_rows],
            minimum_size=3,
            maximum_size=14,
            maximum_tiers=32,
        )
        position_tier_by_player.update(
            {
                item["player"].player_id: assignments[index]
                for index, item in enumerate(position_rows)
            }
        )
    position_ranks: dict[str, int] = {position: 0 for position in SUPPORTED_POSITIONS}
    rows: list[RedraftRankingRow] = []
    for index, item in enumerate(preliminary, start=1):
        player = item["player"]
        position_ranks[player.position] += 1
        rows.append(
            RedraftRankingRow(
                overall_rank=index,
                position_rank=position_ranks[player.position],
                player_id=player.player_id,
                player_name=player.player_name,
                position=player.position,
                team=player.team,
                projected_points=round(float(item["projected"]), 2),
                replacement_points=round(float(item["replacement"]), 2),
                replacement_adjusted_value=round(float(item["value"]), 2),
                starter_gap=round(float(item["starter_gap"]), 2),
                confidence=str(item["confidence"]),
                tier=tier_by_index[index - 1],
                profile_id=profile.profile_id,
                profile_name=profile.league_name,
                source_status=player.source_status,
                evidence_status=player.evidence_status,
                source_as_of=player.source_as_of,
                rookie=player.rookie,
                position_tier=position_tier_by_player[player.player_id],
                overall_tier_label=_overall_tier_label(tier_by_index[index - 1]),
                position_tier_label=(
                    f"{player.position} Tier {position_tier_by_player[player.player_id]}"
                ),
            )
        )
    return RankingResult(
        profile=profile,
        rows=tuple(rows),
        replacement_levels=replacements,
        blocked_rows=snapshot.blocked_rows,
        generated_at_utc=generated,
        projection_sha256=snapshot.source_sha256,
    )


def _confidence(player: ProjectionPlayer, projected: float) -> str:
    low = player.stats.get("projection_low")
    high = player.stats.get("projection_high")
    availability = player.stats.get("availability_probability")
    if low is None or high is None or projected <= 0:
        return "LOW" if player.source_status == "REVIEW_ONLY" or player.rookie else "MEDIUM"
    width_ratio = max(0.0, float(high) - float(low)) / projected
    availability_value = 1.0 if availability is None else float(availability)
    if player.source_status == "GOVERNED" and width_ratio <= 0.20 and availability_value >= 0.90:
        return "HIGH"
    if width_ratio <= 0.40 and availability_value >= 0.75:
        return "MEDIUM"
    return "LOW"


def _tier_assignments(
    values: Sequence[float],
    *,
    minimum_size: int = 4,
    maximum_size: int = 24,
    maximum_tiers: int = 64,
) -> list[int]:
    """Create stable evidence-gap tiers with bounded draft-day presentation.

    Boundaries prefer statistically unusual adjacent value cliffs. A maximum
    segment size is only a readability guard and selects the strongest local
    gap; it never forces equal tier sizes. Tier count remains bounded while the
    size guard prevents a large catch-all deep tier.
    """

    if not values:
        return []
    if len(values) == 1:
        return [1]
    minimum_size = max(2, int(minimum_size))
    maximum_size = max(minimum_size + 1, int(maximum_size))
    maximum_tiers = max(2, int(maximum_tiers))
    gaps = [
        max(0.0, float(values[index]) - float(values[index + 1]))
        for index in range(len(values) - 1)
    ]
    positive = sorted(gap for gap in gaps if gap > 0)
    median = _percentile(positive, 0.50)
    deviations = sorted(abs(gap - median) for gap in positive)
    mad = _percentile(deviations, 0.50)
    evidence_threshold = max(1.0, median + (2.5 * max(mad, 0.25)))

    boundaries: list[int] = []
    start = 0
    while start + minimum_size < len(values) and len(boundaries) < maximum_tiers - 1:
        earliest = start + minimum_size - 1
        latest = min(start + maximum_size - 1, len(gaps) - 1)
        if earliest > latest:
            break
        window = list(range(earliest, latest + 1))
        supported = [index for index in window if gaps[index] >= evidence_threshold]
        if supported:
            boundary = max(supported, key=lambda index: (gaps[index], -index))
        elif len(values) - start <= maximum_size:
            break
        else:
            boundary = max(window, key=lambda index: (gaps[index], -index))
        cut = boundary + 1
        if len(values) - cut < minimum_size:
            break
        boundaries.append(cut)
        start = cut

    tiers: list[int] = []
    for index in range(len(values)):
        tiers.append(1 + sum(index >= boundary for boundary in boundaries))
    return tiers


def _overall_tier_label(tier: int) -> str:
    labels = {
        1: "Tier 1 · Elite",
        2: "Tier 2 · Foundation",
        3: "Tier 3 · Strong starters",
        4: "Tier 4 · Core starters",
        5: "Tier 5 · Flex value",
        6: "Tier 6 · Bench value",
        7: "Tier 7 · Late targets",
        8: "Tier 8 · Deep targets",
        9: "Tier 9 · Deep targets",
    }
    return labels.get(tier, f"Tier {tier} · Deep pool")


def _percentile(values: Sequence[float], percentile: float) -> float:
    if not values:
        return 0.0
    index = (len(values) - 1) * percentile
    lower = math.floor(index)
    upper = math.ceil(index)
    if lower == upper:
        return float(values[lower])
    fraction = index - lower
    return float(values[lower] * (1.0 - fraction) + values[upper] * fraction)


def ranking_rows(result: RankingResult) -> list[dict[str, Any]]:
    return [asdict(row) for row in result.rows]


def player_compare_rows(
    result: RankingResult,
    players: Iterable[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    by_id = {row.player_id: row for row in result.rows}
    output: list[dict[str, Any]] = []
    for player in players:
        player_id = str(player.get("player_id") or "").strip()
        position = str(player.get("position") or "").strip().upper()
        name = str(player.get("player") or player.get("player_name") or "").strip()
        row = by_id.get(player_id) if player_id else None
        if row is None:
            reason = (
                "No exact stable player_id match in the active profile ranking."
                if player_id
                else "Stable player_id is required for redraft comparison."
            )
            output.append(
                {
                    "Player": name,
                    "Pos": position,
                    "Redraft Status": "NOT_ENOUGH_INFORMATION",
                    "Blocking / Missing Evidence": reason,
                }
            )
            continue
        output.append(
            {
                "Player": row.player_name,
                "Pos": row.position,
                "Overall Redraft Rank": row.overall_rank,
                "Position Rank": f"{row.position}{row.position_rank}",
                "Projected Season Points": row.projected_points,
                "Replacement-Adjusted Value": row.replacement_adjusted_value,
                "Confidence": row.confidence,
                "Tier": row.tier,
                "League Profile": row.profile_name,
                "Redraft Status": row.authority_label,
                "Scoring Difference": _profile_scoring_summary(result.profile),
            }
        )
    return output


def redraft_compare_pool_rows(result: RankingResult) -> list[dict[str, str]]:
    """Build the exact-ID selector universe for Redraft Player Compare."""
    return [
        {
            "asset_id": row.player_id,
            "player_id": row.player_id,
            "player": row.player_name,
            "position": row.position,
            "compare_select_label": (
                f"{row.player_name} | {row.position} | {row.team or 'FA'} | Redraft"
            ),
        }
        for row in result.rows
    ]


def _profile_scoring_summary(profile: LeagueProfile) -> str:
    parts = [f"{profile.scoring.reception:g} PPR"]
    if profile.scoring.te_premium:
        parts.append(f"+{profile.scoring.te_premium:g} TE premium")
    if profile.roster.superflex:
        parts.append(f"{profile.roster.superflex} Superflex")
    return ", ".join(parts)


def load_draft_board(root: str | Path, profile_id: str) -> dict[str, Any]:
    path = Path(root) / "draft_boards" / f"{profile_id}.json"
    if not path.is_file():
        return {"schema_version": SCHEMA_VERSION, "profile_id": profile_id, "drafted": []}
    backup_path = path.with_suffix(".backup.json")

    def _validated_document(candidate: Path) -> dict[str, Any]:
        document = json.loads(candidate.read_text(encoding="utf-8"))
        if (
            document.get("schema_version") != SCHEMA_VERSION
            or document.get("profile_id") != profile_id
        ):
            raise RedraftValidationError("Redraft draft-board state does not match the profile.")
        drafted = document.get("drafted", [])
        if not isinstance(drafted, list) or len(drafted) != len(set(map(str, drafted))):
            raise RedraftValidationError("Redraft draft-board drafted-player state is invalid.")
        return document

    try:
        return _validated_document(path)
    except (OSError, json.JSONDecodeError, RedraftValidationError) as primary_error:
        if backup_path.is_file():
            try:
                recovered = _validated_document(backup_path)
            except (OSError, json.JSONDecodeError, RedraftValidationError):
                pass
            else:
                return {**recovered, "recovered_from_backup": True}
        raise RedraftPersistenceError(
            "Draft-board state is unreadable and no valid profile backup is available."
        ) from primary_error


def mark_player_drafted(
    root: str | Path,
    profile_id: str,
    player_id: str,
    *,
    drafted: bool,
) -> dict[str, Any]:
    load_profile(root, profile_id)
    state = load_draft_board(root, profile_id)
    drafted_ids = [str(value) for value in state.get("drafted", [])]
    if drafted:
        if str(player_id) not in drafted_ids:
            drafted_ids.append(str(player_id))
    else:
        drafted_ids = [value for value in drafted_ids if value != str(player_id)]
    updated = {
        "schema_version": SCHEMA_VERSION,
        "profile_id": profile_id,
        "drafted": drafted_ids,
        "updated_at_utc": utc_now(),
    }
    path = Path(root) / "draft_boards" / f"{profile_id}.json"
    _atomic_json(path, updated)
    _atomic_json(path.with_suffix(".backup.json"), updated)
    return updated


def undo_last_draft_pick(root: str | Path, profile_id: str) -> dict[str, Any]:
    load_profile(root, profile_id)
    state = load_draft_board(root, profile_id)
    drafted_ids = [str(value) for value in state.get("drafted", [])]
    if not drafted_ids:
        raise RedraftValidationError("No drafted player is available to undo.")
    drafted_ids.pop()
    updated = {
        "schema_version": SCHEMA_VERSION,
        "profile_id": profile_id,
        "drafted": drafted_ids,
        "updated_at_utc": utc_now(),
    }
    path = Path(root) / "draft_boards" / f"{profile_id}.json"
    _atomic_json(path, updated)
    _atomic_json(path.with_suffix(".backup.json"), updated)
    return updated


def build_health_report(
    profile: LeagueProfile | None,
    snapshot: ProjectionSnapshot | None,
    ranking: RankingResult | None,
) -> RedraftHealthReport:
    messages: list[str] = []
    profile_valid = False
    if profile is None:
        messages.append("No active redraft league profile.")
    else:
        try:
            validate_profile(profile)
            profile_valid = True
        except RedraftValidationError as exc:
            messages.append(str(exc))
    forecast_available = bool(snapshot and snapshot.players and not snapshot.errors)
    if not forecast_available:
        messages.append("Governed granular current-season projections are missing or blocked.")
    replacement_valid = bool(ranking and ranking.replacement_levels and not ranking.errors)
    if profile and (profile.roster.k or profile.roster.dst):
        messages.append(
            "K/DST are manual and unmodeled in Practical Mode."
            if profile.practical_mode
            else "K/DST require governed projected_points_override rows."
        )
    ranked = len(ranking.rows) if ranking else 0
    blocked = len(snapshot.blocked_rows) if snapshot else 0
    if not profile_valid:
        status = "BLOCKED_PROFILE"
    elif not forecast_available:
        status = "BLOCKED_CURRENT_SEASON_EVIDENCE"
    elif not replacement_valid:
        status = "BLOCKED_REPLACEMENT"
    elif blocked:
        status = "READY_WITH_BLOCKED_PLAYERS"
    else:
        status = "READY_REVIEW_ONLY"
    return RedraftHealthReport(
        status=status,
        player_universe_available=bool(snapshot and (snapshot.players or snapshot.blocked_rows)),
        current_season_forecast_available=forecast_available,
        scoring_profile_valid=profile_valid,
        replacement_calculation_valid=replacement_valid,
        ranked_players=ranked,
        blocked_players=blocked,
        last_generated_timestamp=ranking.generated_at_utc if ranking else "",
        messages=tuple(messages),
    )


def _optional_float(value: Any) -> float | None:
    text = str(value if value is not None else "").strip()
    if not text or text.casefold() in {"nan", "none", "null", "n/a", "not enough information"}:
        return None
    try:
        number = float(text)
    except ValueError:
        return None
    return number if math.isfinite(number) else None


def _optional_int(value: Any) -> int | None:
    number = _optional_float(value)
    return int(number) if number is not None and number.is_integer() else None


def _number(value: float | None) -> float:
    return 0.0 if value is None else float(value)


def _truthy(value: Any) -> bool:
    return str(value or "").strip().casefold() in {"1", "true", "yes", "y"}


def _name_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.casefold())
