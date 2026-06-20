from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

DEFAULT_OUTPUT_ROOT = Path(r"C:\NWR_SHARED_DATA\lane_exchange")
PACKAGE_NAMES = (
    "sleeper_state/league_rosters_snapshot",
    "sleeper_state/draft_pick_ownership_snapshot",
    "sleeper_state/traded_picks_snapshot",
    "sleeper_state/transactions_snapshot",
    "league_state/pick_order",
    "league_state/nwr_picks",
)
FORBIDDEN_USE = [
    "latest_approved",
    "pinned_live_snapshot",
    "final_draft_day_decision",
    "simulation",
    "recommendation",
    "private_value",
    "hidden_sort",
    "production_deployment",
]
ALLOWED_USE = [
    "manifest_validation",
    "source_audit",
    "future_latest_candidate_review",
]


class NormalizationError(ValueError):
    pass


@dataclass(frozen=True)
class PackageDraft:
    package_name: str
    data_file: str
    rows: list[dict[str, Any]]
    allowed_use: list[str]
    forbidden_use: list[str]
    notes: str
    contains_private_value: bool = False
    contains_market_data: bool = False
    contains_adp: bool = False


@dataclass(frozen=True)
class NormalizeResult:
    snapshot_dir: Path
    report_path: Path
    packages: list[PackageDraft]
    warnings: list[str]
    wrote_candidates: bool
    candidate_paths: dict[str, Path]


def normalize_snapshot(
    *,
    snapshot_dir: Path,
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    write_candidates: bool = False,
    snapshot_label: str | None = None,
    expected_rounds: int = 5,
    expected_teams: int = 10,
    nwr_roster_id: int | None = None,
    nwr_team_name: str = "Niners",
) -> NormalizeResult:
    raw = _read_snapshot(snapshot_dir)
    source_metadata = _read_optional_json(snapshot_dir / "snapshot_metadata.json") or {}
    label = snapshot_label or _snapshot_label(snapshot_dir, source_metadata)
    warnings = _source_warnings(source_metadata)

    league = _as_dict(raw["league"], "league")
    users = _as_list(raw["users"], "users")
    rosters = _as_list(raw["rosters"], "rosters")
    traded_picks = _as_list(raw["traded_picks"], "traded_picks")
    draft_details = _as_dict(raw["draft_details"], "draft_details")
    draft_picks = _as_list(raw["draft_picks"], "draft_picks")
    transactions = _transaction_rows(raw["transactions"])

    users_by_id = {str(user.get("user_id")): user for user in users if user.get("user_id")}
    rosters_by_id = {int(roster["roster_id"]): roster for roster in rosters}
    teams_by_roster_id = _team_rows_by_roster(rosters, users_by_id)
    nwr_id = nwr_roster_id or _find_nwr_roster_id(teams_by_roster_id, nwr_team_name)
    if nwr_id is None:
        warnings.append(
            f"NWR roster not found from team name '{nwr_team_name}'. "
            "league_state/nwr_picks will be empty until explicitly provided."
        )

    league_id = str(league.get("league_id") or source_metadata.get("league_id") or "")
    draft_id = str(draft_details.get("draft_id") or source_metadata.get("draft_id") or "")
    season = str(
        draft_details.get("season")
        or league.get("season")
        or source_metadata.get("season")
        or ""
    )
    rounds = int((draft_details.get("settings") or {}).get("rounds") or expected_rounds)
    teams = int((draft_details.get("settings") or {}).get("teams") or expected_teams)

    if rounds != expected_rounds or teams != expected_teams:
        warnings.append(
            f"Draft settings are {rounds} rounds x {teams} teams; expected "
            f"{expected_rounds} x {expected_teams} for current NWR draft validation."
        )

    pick_rows = _build_pick_ownership_rows(
        league=league,
        draft_details=draft_details,
        draft_picks=draft_picks,
        traded_picks=traded_picks,
        rosters_by_id=rosters_by_id,
        teams_by_roster_id=teams_by_roster_id,
        expected_rounds=expected_rounds,
        expected_teams=expected_teams,
    )
    _validate_pick_rows(pick_rows, expected_rounds * expected_teams)

    packages = [
        PackageDraft(
            package_name="sleeper_state/league_rosters_snapshot",
            data_file="league_rosters_snapshot.csv",
            rows=_league_roster_rows(
                league_id=league_id,
                season=season,
                rosters=rosters,
                users_by_id=users_by_id,
                teams_by_roster_id=teams_by_roster_id,
            ),
            allowed_use=ALLOWED_USE + ["roster_identity_crosscheck"],
            forbidden_use=FORBIDDEN_USE,
            notes="Sleeper roster snapshot from raw local scheduled ingest.",
        ),
        PackageDraft(
            package_name="sleeper_state/draft_pick_ownership_snapshot",
            data_file="draft_pick_ownership_snapshot.csv",
            rows=pick_rows,
            allowed_use=ALLOWED_USE + ["pick_ownership_crosscheck"],
            forbidden_use=FORBIDDEN_USE,
            notes=(
                "Sleeper draft pick ownership reconstructed from draft_order plus "
                "traded_picks when draft_picks is empty/pre-draft."
            ),
        ),
        PackageDraft(
            package_name="sleeper_state/traded_picks_snapshot",
            data_file="traded_picks_snapshot.csv",
            rows=_traded_pick_rows(
                league_id=league_id,
                season=season,
                traded_picks=traded_picks,
                teams_by_roster_id=teams_by_roster_id,
            ),
            allowed_use=ALLOWED_USE + ["pick_ownership_crosscheck"],
            forbidden_use=FORBIDDEN_USE,
            notes="Sleeper traded_picks raw snapshot normalized for source audit.",
        ),
        PackageDraft(
            package_name="sleeper_state/transactions_snapshot",
            data_file="transactions_snapshot.csv",
            rows=_transactions_package_rows(league_id, season, transactions),
            allowed_use=ALLOWED_USE + ["transaction_evidence_review"],
            forbidden_use=FORBIDDEN_USE,
            notes=(
                "Sleeper transaction rows captured only for evidence review; "
                "not final dropped-player approval."
            ),
        ),
        PackageDraft(
            package_name="league_state/pick_order",
            data_file="pick_order.csv",
            rows=_pick_order_rows(pick_rows),
            allowed_use=ALLOWED_USE + ["mock_draft_pick_order_candidate"],
            forbidden_use=FORBIDDEN_USE,
            notes=(
                "Candidate pick_order built from Sleeper source-backed pick ownership. "
                "Not final draft-day approval."
            ),
        ),
        PackageDraft(
            package_name="league_state/nwr_picks",
            data_file="nwr_picks.csv",
            rows=_nwr_pick_rows(pick_rows, nwr_id),
            allowed_use=ALLOWED_USE + ["mock_draft_nwr_pick_candidate"],
            forbidden_use=FORBIDDEN_USE,
            notes=(
                "Candidate NWR picks from Sleeper current ownership. "
                f"NWR roster id: {nwr_id if nwr_id is not None else 'not_found'}."
            ),
        ),
    ]

    candidate_paths: dict[str, Path] = {}
    if write_candidates:
        for package in packages:
            candidate_paths[package.package_name] = _write_candidate_package(
                output_root=output_root,
                package=package,
                label=label,
                source_metadata=source_metadata,
                snapshot_dir=snapshot_dir,
                league_id=league_id,
                draft_id=draft_id,
                season=season,
                warnings=warnings,
            )

    report_path = snapshot_dir / "sleeper_normalizer_v0_report.md"
    report_path.write_text(
        _markdown_report(
            packages=packages,
            warnings=warnings,
            write_candidates=write_candidates,
            candidate_paths=candidate_paths,
            label=label,
            snapshot_dir=snapshot_dir,
        ),
        encoding="utf-8",
    )
    return NormalizeResult(
        snapshot_dir=snapshot_dir,
        report_path=report_path,
        packages=packages,
        warnings=warnings,
        wrote_candidates=write_candidates,
        candidate_paths=candidate_paths,
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Normalize a local Sleeper raw snapshot into dry-run reports or explicit "
            "Lane Exchange latest_candidate packages. Never writes latest_approved."
        )
    )
    parser.add_argument("--snapshot-dir", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--write-candidates", action="store_true")
    parser.add_argument("--snapshot-label", default=None)
    parser.add_argument("--expected-rounds", type=int, default=5)
    parser.add_argument("--expected-teams", type=int, default=10)
    parser.add_argument("--nwr-roster-id", type=int, default=None)
    parser.add_argument("--nwr-team-name", default="Niners")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        result = normalize_snapshot(
            snapshot_dir=args.snapshot_dir,
            output_root=args.output_root,
            write_candidates=args.write_candidates,
            snapshot_label=args.snapshot_label,
            expected_rounds=args.expected_rounds,
            expected_teams=args.expected_teams,
            nwr_roster_id=args.nwr_roster_id,
            nwr_team_name=args.nwr_team_name,
        )
    except Exception as exc:
        print(f"Sleeper normalizer failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    print(f"report_path={result.report_path}")
    print(f"write_candidates={result.wrote_candidates}")
    for package in result.packages:
        print(f"{package.package_name}: rows={len(package.rows)}")
    for package_name, path in result.candidate_paths.items():
        print(f"candidate={package_name} path={path}")
    return 0


def _read_snapshot(snapshot_dir: Path) -> dict[str, Any]:
    required = [
        "league",
        "users",
        "rosters",
        "drafts",
        "traded_picks",
        "draft_details",
        "draft_picks",
    ]
    raw: dict[str, Any] = {}
    for name in required:
        path = snapshot_dir / f"{name}.json"
        if not path.exists():
            raise NormalizationError(f"missing required raw endpoint file: {path}")
        raw[name] = _read_json(path)
    raw["transactions"] = {
        path.name: _read_json(path)
        for path in sorted(snapshot_dir.glob("transactions_round_*.json"))
        if path.stat().st_size > 0
    }
    return raw


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_optional_json(path: Path) -> dict[str, Any] | None:
    if not path.exists() or path.stat().st_size == 0:
        return None
    payload = _read_json(path)
    return payload if isinstance(payload, dict) else None


def _source_warnings(metadata: dict[str, Any]) -> list[str]:
    warnings = list(metadata.get("warnings") or [])
    for endpoint in metadata.get("endpoints") or []:
        warning = endpoint.get("warning")
        error = endpoint.get("error")
        if warning:
            warnings.append(f"{endpoint.get('name')}: {warning}")
        if error:
            warnings.append(f"{endpoint.get('name')}: {error}")
    return warnings


def _snapshot_label(snapshot_dir: Path, metadata: dict[str, Any]) -> str:
    raw = str(metadata.get("snapshot_label") or snapshot_dir.name)
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", raw)


def _as_dict(payload: Any, name: str) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise NormalizationError(f"{name} must be a JSON object")
    return payload


def _as_list(payload: Any, name: str) -> list[dict[str, Any]]:
    if not isinstance(payload, list):
        raise NormalizationError(f"{name} must be a JSON array")
    return [item for item in payload if isinstance(item, dict)]


def _team_rows_by_roster(
    rosters: list[dict[str, Any]], users_by_id: dict[str, dict[str, Any]]
) -> dict[int, dict[str, Any]]:
    teams: dict[int, dict[str, Any]] = {}
    for roster in rosters:
        roster_id = int(roster["roster_id"])
        owner_id = str(roster.get("owner_id") or "")
        user = users_by_id.get(owner_id, {})
        metadata = user.get("metadata") or {}
        team_name = metadata.get("team_name") or user.get("display_name") or owner_id
        teams[roster_id] = {
            "roster_id": roster_id,
            "owner_id": owner_id,
            "display_name": user.get("display_name") or user.get("username") or "",
            "team_name": team_name,
        }
    return teams


def _find_nwr_roster_id(
    teams_by_roster_id: dict[int, dict[str, Any]], team_name: str
) -> int | None:
    target = _norm(team_name)
    matches = [
        roster_id
        for roster_id, team in teams_by_roster_id.items()
        if _norm(team.get("team_name")) == target or _norm(team.get("display_name")) == target
    ]
    return matches[0] if len(matches) == 1 else None


def _build_pick_ownership_rows(
    *,
    league: dict[str, Any],
    draft_details: dict[str, Any],
    draft_picks: list[dict[str, Any]],
    traded_picks: list[dict[str, Any]],
    rosters_by_id: dict[int, dict[str, Any]],
    teams_by_roster_id: dict[int, dict[str, Any]],
    expected_rounds: int,
    expected_teams: int,
) -> list[dict[str, Any]]:
    if draft_picks:
        raise NormalizationError(
            "draft_picks endpoint returned picks; V0 supports pre-draft reconstruction only"
        )

    season = str(draft_details.get("season") or league.get("season") or "")
    draft_order = draft_details.get("draft_order") or {}
    owner_to_roster = {
        str(roster.get("owner_id")): int(roster["roster_id"])
        for roster in rosters_by_id.values()
        if roster.get("owner_id")
    }
    original_roster_by_slot: dict[int, int] = {}
    for owner_id, slot_value in draft_order.items():
        roster_id = owner_to_roster.get(str(owner_id))
        if roster_id is None:
            continue
        slot = int(slot_value)
        if slot in original_roster_by_slot:
            raise NormalizationError(f"duplicate draft slot in draft_order: {slot}")
        original_roster_by_slot[slot] = roster_id

    if len(original_roster_by_slot) != expected_teams:
        raise NormalizationError(
            f"draft_order mapped {len(original_roster_by_slot)} teams; expected {expected_teams}"
        )

    current_owner_by_pick = {
        (str(pick.get("season")), int(pick["round"]), int(pick["roster_id"])): int(
            pick["owner_id"]
        )
        for pick in traded_picks
        if str(pick.get("season")) == season and pick.get("round") and pick.get("roster_id")
    }
    rows: list[dict[str, Any]] = []
    for round_number in range(1, expected_rounds + 1):
        for slot in sorted(original_roster_by_slot):
            original_roster_id = original_roster_by_slot[slot]
            current_roster_id = current_owner_by_pick.get(
                (season, round_number, original_roster_id),
                original_roster_id,
            )
            original_team = teams_by_roster_id.get(original_roster_id, {})
            current_team = teams_by_roster_id.get(current_roster_id, {})
            overall_pick = (round_number - 1) * expected_teams + slot
            rows.append(
                {
                    "source_lane": "sleeper_state",
                    "season": season,
                    "draft_id": draft_details.get("draft_id") or "",
                    "round": round_number,
                    "round_pick": slot,
                    "overall_pick": overall_pick,
                    "pick_label": f"{round_number}.{slot:02d}",
                    "original_roster_id": original_roster_id,
                    "original_owner_id": original_team.get("owner_id", ""),
                    "original_owner": original_team.get("team_name", original_roster_id),
                    "current_roster_id": current_roster_id,
                    "current_owner_id": current_team.get("owner_id", ""),
                    "current_owner": current_team.get("team_name", current_roster_id),
                    "source_status": "sleeper_api_draft_order_traded_picks_candidate",
                    "approval_status": "candidate",
                    "notes": (
                        "Pre-draft pick reconstructed from Sleeper draft_order "
                        "plus traded_picks."
                    ),
                }
            )
    return rows


def _validate_pick_rows(rows: list[dict[str, Any]], expected_count: int) -> None:
    if len(rows) != expected_count:
        raise NormalizationError(f"pick_order has {len(rows)} rows; expected {expected_count}")
    overall = [int(row["overall_pick"]) for row in rows]
    if len(set(overall)) != len(overall):
        raise NormalizationError("overall_pick values are not unique")
    labels = [str(row["pick_label"]) for row in rows]
    if len(set(labels)) != len(labels):
        raise NormalizationError("pick_label values are not unique")


def _league_roster_rows(
    *,
    league_id: str,
    season: str,
    rosters: list[dict[str, Any]],
    users_by_id: dict[str, dict[str, Any]],
    teams_by_roster_id: dict[int, dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for roster in sorted(rosters, key=lambda item: int(item["roster_id"])):
        roster_id = int(roster["roster_id"])
        team = teams_by_roster_id[roster_id]
        starters = {str(player_id) for player_id in roster.get("starters") or []}
        players = [str(player_id) for player_id in roster.get("players") or []]
        if not players:
            rows.append(
                _roster_row(
                    league_id=league_id,
                    season=season,
                    roster_id=roster_id,
                    team=team,
                    player_id="",
                    slot_status="empty_roster",
                    player_count=0,
                )
            )
            continue
        for player_id in sorted(players):
            rows.append(
                _roster_row(
                    league_id=league_id,
                    season=season,
                    roster_id=roster_id,
                    team=team,
                    player_id=player_id,
                    slot_status="starter" if player_id in starters else "rostered",
                    player_count=len(players),
                )
            )
    return rows


def _roster_row(
    *,
    league_id: str,
    season: str,
    roster_id: int,
    team: dict[str, Any],
    player_id: str,
    slot_status: str,
    player_count: int,
) -> dict[str, Any]:
    return {
        "source_lane": "sleeper_state",
        "league_id": league_id,
        "season": season,
        "roster_id": roster_id,
        "owner_id": team.get("owner_id", ""),
        "display_name": team.get("display_name", ""),
        "team_name": team.get("team_name", ""),
        "player_id": player_id,
        "slot_status": slot_status,
        "player_count": player_count,
        "approval_status": "candidate",
        "notes": (
            "Sleeper roster player id only; player metadata mapping belongs in "
            "later identity normalizer."
        ),
    }


def _traded_pick_rows(
    *,
    league_id: str,
    season: str,
    traded_picks: list[dict[str, Any]],
    teams_by_roster_id: dict[int, dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for pick in traded_picks:
        original_roster_id = _int_or_blank(pick.get("roster_id"))
        current_roster_id = _int_or_blank(pick.get("owner_id"))
        original_team = teams_by_roster_id.get(original_roster_id, {})
        current_team = teams_by_roster_id.get(current_roster_id, {})
        rows.append(
            {
                "source_lane": "sleeper_state",
                "league_id": league_id,
                "season": pick.get("season") or season,
                "round": pick.get("round", ""),
                "original_roster_id": original_roster_id,
                "original_owner": original_team.get("team_name", ""),
                "current_roster_id": current_roster_id,
                "current_owner": current_team.get("team_name", ""),
                "previous_owner_id": pick.get("previous_owner_id", ""),
                "approval_status": "candidate",
                "notes": "Sleeper traded_picks row; not final draft-day approval.",
            }
        )
    return rows


def _transaction_rows(raw_transactions: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for file_name, payload in sorted(raw_transactions.items()):
        if not isinstance(payload, list):
            continue
        for transaction in payload:
            if isinstance(transaction, dict):
                row = dict(transaction)
                row["_source_file"] = file_name
                rows.append(row)
    return rows


def _transactions_package_rows(
    league_id: str, season: str, transactions: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for transaction in transactions:
        rows.append(
            {
                "source_lane": "sleeper_state",
                "league_id": league_id,
                "season": season,
                "transaction_id": transaction.get("transaction_id", ""),
                "type": transaction.get("type", ""),
                "status": transaction.get("status", ""),
                "created": transaction.get("created", ""),
                "roster_ids": _compact_json(transaction.get("roster_ids")),
                "adds": _compact_json(transaction.get("adds")),
                "drops": _compact_json(transaction.get("drops")),
                "draft_picks": _compact_json(transaction.get("draft_picks")),
                "source_file": transaction.get("_source_file", ""),
                "approval_status": "candidate",
                "notes": (
                    "Sleeper transaction evidence only; not final dropped/unavailable "
                    "approval."
                ),
            }
        )
    return rows


def _pick_order_rows(pick_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "source_lane": "league_state",
            "season": row["season"],
            "draft_id": row["draft_id"],
            "overall_pick": row["overall_pick"],
            "round": row["round"],
            "round_pick": row["round_pick"],
            "pick_label": row["pick_label"],
            "current_roster_id": row["current_roster_id"],
            "current_owner": row["current_owner"],
            "original_roster_id": row["original_roster_id"],
            "original_owner": row["original_owner"],
            "source_status": row["source_status"],
            "approval_status": "candidate",
            "notes": "Sleeper-normalized pick_order candidate; requires Master/Tim review.",
        }
        for row in pick_rows
    ]


def _nwr_pick_rows(
    pick_rows: list[dict[str, Any]], nwr_roster_id: int | None
) -> list[dict[str, Any]]:
    if nwr_roster_id is None:
        return []
    return [
        {
            "source_lane": "league_state",
            "season": row["season"],
            "draft_id": row["draft_id"],
            "overall_pick": row["overall_pick"],
            "round": row["round"],
            "round_pick": row["round_pick"],
            "pick_label": row["pick_label"],
            "nwr_roster_id": nwr_roster_id,
            "current_owner": row["current_owner"],
            "source_status": row["source_status"],
            "approval_status": "candidate",
            "notes": "Sleeper-normalized NWR pick candidate; requires Master/Tim review.",
        }
        for row in pick_rows
        if int(row["current_roster_id"]) == nwr_roster_id
    ]


def _write_candidate_package(
    *,
    output_root: Path,
    package: PackageDraft,
    label: str,
    source_metadata: dict[str, Any],
    snapshot_dir: Path,
    league_id: str,
    draft_id: str,
    season: str,
    warnings: list[str],
) -> Path:
    source_lane, short_name = package.package_name.split("/", 1)
    package_root = output_root / source_lane / short_name
    snapshot_path = package_root / label
    snapshot_path.mkdir(parents=True, exist_ok=False)
    data_path = snapshot_path / package.data_file
    _write_csv(data_path, package.rows)
    sha256 = _file_sha256(data_path)
    manifest = _manifest(
        package=package,
        label=label,
        source_metadata=source_metadata,
        snapshot_dir=snapshot_dir,
        league_id=league_id,
        draft_id=draft_id,
        season=season,
        sha256=sha256,
        warnings=warnings,
    )
    manifest_path = snapshot_path / "manifest.json"
    _write_json(manifest_path, manifest)
    pointer = {
        "pointer_type": "latest_candidate",
        "package_name": package.package_name,
        "approval_status": "candidate",
        "approval_scope": "not_approved_review_only",
        "snapshot_path": str(snapshot_path),
        "manifest_path": str(manifest_path),
        "data_file": package.data_file,
        "row_count": len(package.rows),
        "sha256": sha256,
        "updated_at": datetime.now(UTC).isoformat(),
        "allowed_use": package.allowed_use,
        "forbidden_use": package.forbidden_use,
        "notes": "latest_candidate only; latest_approved was not created or updated.",
    }
    _write_json(package_root / "latest_candidate.json", pointer)
    return snapshot_path


def _manifest(
    *,
    package: PackageDraft,
    label: str,
    source_metadata: dict[str, Any],
    snapshot_dir: Path,
    league_id: str,
    draft_id: str,
    season: str,
    sha256: str,
    warnings: list[str],
) -> dict[str, Any]:
    return {
        "source_lane": package.package_name.split("/", 1)[0],
        "source_repo": "Sleeper public API raw snapshot",
        "source_branch": "local_only_scheduled_ingest",
        "source_head": str(snapshot_dir),
        "source_snapshot_label": source_metadata.get("snapshot_label") or snapshot_dir.name,
        "source_created_at": source_metadata.get("created_at", ""),
        "source_league_id": league_id,
        "source_draft_id": draft_id,
        "package_name": package.package_name,
        "schema_version": "sleeper_normalizer_v0",
        "data_file": package.data_file,
        "row_count": len(package.rows),
        "sha256": sha256,
        "created_at": datetime.now(UTC).isoformat(),
        "approval_status": "candidate",
        "approved_for": ["review_only"],
        "allowed_use": package.allowed_use,
        "forbidden_use": package.forbidden_use,
        "contains_private_value": package.contains_private_value,
        "contains_market_data": package.contains_market_data,
        "contains_adp": package.contains_adp,
        "not_latest_approved": True,
        "not_final_draft_day_approval": True,
        "not_simulation_approval": True,
        "notes": package.notes,
        "source_warnings": warnings,
        "season": season,
        "snapshot_label": label,
    }


def _markdown_report(
    *,
    packages: list[PackageDraft],
    warnings: list[str],
    write_candidates: bool,
    candidate_paths: dict[str, Path],
    label: str,
    snapshot_dir: Path,
) -> str:
    lines = [
        "# Sleeper Normalizer V0 Report",
        "",
        "## Scope",
        "",
        "Local-only normalization report from a Sleeper raw snapshot. This does not "
        "create `latest_approved`, final draft-day truth, simulations, recommendations, "
        "deployment, private value, hidden sort, probabilities, bands, or promoted artifacts.",
        "",
        "## Snapshot",
        "",
        f"- Snapshot dir: `{snapshot_dir}`",
        f"- Candidate label: `{label}`",
        f"- Write candidates: `{write_candidates}`",
        "",
        "## Package Counts",
        "",
        "| Package | Rows | Candidate path |",
        "| --- | ---: | --- |",
    ]
    for package in packages:
        path = candidate_paths.get(package.package_name)
        lines.append(
            f"| `{package.package_name}` | {len(package.rows)} | "
            f"{f'`{path}`' if path else 'dry-run only'} |"
        )
    lines.extend(["", "## Warnings", ""])
    if warnings:
        lines.extend(f"- {warning}" for warning in warnings)
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Guardrails",
            "",
            "- `latest_approved` was not created.",
            "- Existing `latest_approved` packages were not overwritten.",
            "- Candidate packages are written only when `--write-candidates` is used.",
            "- Candidate packages require Master/Tim/QA review before downstream approval.",
        ]
    )
    return "\n".join(lines) + "\n"


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    headers = list(rows[0].keys()) if rows else ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _compact_json(value: Any) -> str:
    if value in (None, "", [], {}):
        return ""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _int_or_blank(value: Any) -> int | str:
    if value in (None, ""):
        return ""
    return int(value)


def _norm(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value).lower())


if __name__ == "__main__":
    raise SystemExit(main())
