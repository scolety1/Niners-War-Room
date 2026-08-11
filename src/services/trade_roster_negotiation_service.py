"""Read-only roster ownership and market negotiation context for Trading Lab.

This adapter reconnects the admitted active-pack roster facts.  It never infers
ownership from an offer and never writes roster state.  Specific counteroffers are
allowed only after every asset on both sides has exact, same-snapshot ownership.
"""

from __future__ import annotations

import csv
import os
import re
from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from src.data.validators import validate_data_pack
from src.services.draft_day_trade_lab_service import TradeState, trade_item_rows

ROSTER_STATE = "PARTIAL_ROSTER_STATE"
CURRENT_ROSTER_STATE = "CURRENT_ROSTER_STATE"
COUNTER_BLOCKED = "BLOCKED_COUNTEROFFERS_NO_ROSTER_OWNERSHIP"
COUNTERPARTY_RESOLVED = "COUNTERPARTY_RESOLVED"
MARKET_LABEL = "Market negotiation context — stale as of 2026-07-17"
MARKET_DATE = "2026-07-17"
_PICK_PATTERN = re.compile(r"^(?P<year>20\d{2})\s+(?P<round>\d+)(?:st|nd|rd|th)$", re.I)


@dataclass(frozen=True)
class OwnedAsset:
    asset_id: str
    asset_name: str
    asset_kind: str
    team_id: str
    team_name: str
    position: str = ""
    pick_year: int | None = None
    pick_round: int | None = None
    original_team_name: str = ""


@dataclass(frozen=True)
class RosterOwnershipAudit:
    classification: str
    source_path: str
    snapshot_date: str
    league_id: str
    owner_team_id: str
    owner_team_name: str
    player_assets: tuple[OwnedAsset, ...]
    pick_assets: tuple[OwnedAsset, ...]
    team_asset_counts: tuple[tuple[str, int], ...]
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class AssetOwnershipCheck:
    side: str
    item_key: str
    asset_id: str
    asset_name: str
    expected_team: str
    resolved_team: str
    status: str
    evidence: str


@dataclass(frozen=True)
class TradeOwnershipResolution:
    status: str
    classification: str
    owner_team_id: str
    owner_team_name: str
    counterparty_team_id: str
    counterparty_team_name: str
    candidate_counterparty_teams: tuple[str, ...]
    checks: tuple[AssetOwnershipCheck, ...]
    conflicts: tuple[str, ...]
    owner_roster_asset_count: int
    owner_pick_count: int
    opponent_roster_asset_count: int
    opponent_pick_count: int
    source_path: str
    snapshot_date: str

    @property
    def counterparty_resolved(self) -> bool:
        return self.status == COUNTERPARTY_RESOLVED


@dataclass(frozen=True)
class MarketSideContext:
    side: str
    displayed_total: int | None
    included_assets: tuple[str, ...]
    excluded_assets: tuple[str, ...]


@dataclass(frozen=True)
class MarketNegotiationContext:
    label: str
    as_of_date: str
    give: MarketSideContext
    receive: MarketSideContext
    displayed_delta_receive_minus_give: int | None
    same_snapshot: bool
    warning: str


@dataclass(frozen=True)
class RosterComposition:
    team_name: str
    position_counts: tuple[tuple[str, int], ...]
    player_count: int
    pick_count: int


@dataclass(frozen=True)
class RosterOpportunity:
    item_key: str
    asset_id: str
    asset_name: str
    position: str
    nwr_rank: int | None
    nwr_band: str
    market_dp_value: int | None
    market_dp_rank: float | None
    market_band: str
    gap_interpretation: str
    team_fit: str


@dataclass(frozen=True)
class RosterAwareCounter:
    counter_id: str
    title: str
    give: tuple[str, ...]
    receive: tuple[str, ...]
    changes: tuple[str, ...]
    why_this_helps_me: tuple[str, ...]
    why_they_might_consider: tuple[str, ...]
    nwr_vs_market_opportunity: str
    main_risk: str
    ownership_status: str = "VERIFIED_SAME_SNAPSHOT_OWNERSHIP"


def audit_roster_ownership(
    data_pack_path: str | Path,
    *,
    owner_team_name: str = "Niners",
) -> RosterOwnershipAudit:
    """Audit the existing admitted roster layer without mutating or refreshing it."""

    validated = validate_data_pack(data_pack_path)
    rosters = validated.rows_by_table.get("rosters", [])
    picks = validated.rows_by_table.get("future_picks", [])
    normalized_owner = owner_team_name.strip().casefold()
    owner_rows = [
        row
        for row in rosters
        if str(row.get("team_name") or "").strip().casefold() == normalized_owner
    ]
    owner_team_id = str(owner_rows[0].get("team_id") or "") if owner_rows else ""
    player_assets = tuple(
        OwnedAsset(
            asset_id=f"current:{row.get('player_id')}",
            asset_name=str(row.get("player_name") or ""),
            asset_kind="player",
            team_id=str(row.get("team_id") or ""),
            team_name=str(row.get("team_name") or "").strip(),
            position=str(row.get("position") or ""),
        )
        for row in rosters
        if row.get("player_id")
    )
    pick_assets = tuple(
        OwnedAsset(
            asset_id=(
                f"pick:{row.get('pick_year')}:{row.get('round')}:"
                f"{row.get('original_team_id')}"
            ),
            asset_name=str(row.get("pick_label") or ""),
            asset_kind="pick",
            team_id=str(row.get("current_team_id") or ""),
            team_name=str(row.get("current_team_name") or "").strip(),
            pick_year=_integer(row.get("pick_year")),
            pick_round=_integer(row.get("round")),
            original_team_name=str(row.get("original_team_name") or "").strip(),
        )
        for row in picks
        if row.get("pick_year") and row.get("round")
    )
    years = sorted({asset.pick_year for asset in pick_assets if asset.pick_year is not None})
    warnings: list[str] = []
    if validated.has_errors:
        warnings.append("The active data pack has validation errors; ownership fails closed.")
    if not owner_rows:
        warnings.append(f"Owner team {owner_team_name!r} is absent from roster facts.")
    if not ({2027, 2028} <= set(years)):
        shown = ", ".join(map(str, years)) or "none"
        warnings.append(
            "Future-pick ownership is incomplete: the admitted pick table contains "
            f"year(s) {shown}, not the required 2027 and 2028 ownership."
        )
    counts = Counter(asset.team_name for asset in player_assets)
    league_ids = sorted(
        {
            str(row.get("league_id") or "")
            for row in rosters
            if str(row.get("league_id") or "")
        }
    )
    if len(league_ids) != 1:
        warnings.append("Roster facts do not resolve exactly one league ID.")
    return RosterOwnershipAudit(
        classification=ROSTER_STATE,
        source_path=str(Path(data_pack_path)),
        snapshot_date=str(validated.snapshot_date or "Not available"),
        league_id=league_ids[0] if len(league_ids) == 1 else "",
        owner_team_id=owner_team_id,
        owner_team_name=owner_team_name,
        player_assets=player_assets,
        pick_assets=pick_assets,
        team_asset_counts=tuple(sorted(counts.items())),
        warnings=tuple(warnings),
    )


def resolve_latest_sleeper_snapshot(
    repo_root: str | Path,
    *,
    league_id: str = "1344772855908290560",
) -> Path | None:
    """Return the newest complete local Sleeper export, never a remote runtime source."""

    roots: list[Path] = []
    configured = os.environ.get("NWR_SLEEPER_ROSTER_SNAPSHOT_ROOT")
    if configured:
        roots.append(Path(configured))
    roots.append(Path(repo_root) / "local_exports" / "sleeper")
    candidates: list[Path] = []
    required = {
        "sleeper_rosters.csv",
        "sleeper_future_picks.csv",
        "sleeper_teams.csv",
        "sleeper_metadata.csv",
    }
    for root in roots:
        if root.is_dir() and required <= {path.name for path in root.iterdir() if path.is_file()}:
            candidates.append(root)
        if root.is_dir():
            candidates.extend(
                path
                for path in root.glob(f"{league_id}_*")
                if path.is_dir()
                and required <= {child.name for child in path.iterdir() if child.is_file()}
            )
    return max(candidates, key=lambda path: path.name) if candidates else None


def audit_best_available_roster_ownership(
    data_pack_path: str | Path,
    *,
    repo_root: str | Path,
    governed_asset_ids: set[str] | frozenset[str],
    owner_team_name: str = "Niners",
) -> RosterOwnershipAudit:
    """Prefer the current local Sleeper snapshot and fail back to the admitted pack."""

    snapshot = resolve_latest_sleeper_snapshot(repo_root)
    if snapshot is None:
        return audit_roster_ownership(data_pack_path, owner_team_name=owner_team_name)
    return audit_sleeper_roster_ownership(
        snapshot,
        repo_root=repo_root,
        governed_asset_ids=governed_asset_ids,
        owner_team_name=owner_team_name,
    )


def audit_sleeper_roster_ownership(
    snapshot_path: str | Path,
    *,
    repo_root: str | Path,
    governed_asset_ids: set[str] | frozenset[str],
    owner_team_name: str = "Niners",
) -> RosterOwnershipAudit:
    """Load one complete read-only Sleeper export with exact governed identity bridges."""

    snapshot = Path(snapshot_path)
    roster_rows = _csv_rows(snapshot / "sleeper_rosters.csv")
    pick_rows = _csv_rows(snapshot / "sleeper_future_picks.csv")
    metadata_rows = _csv_rows(snapshot / "sleeper_metadata.csv")
    approved_rookie_ids = _approved_rookie_sleeper_ids(Path(repo_root))
    normalized_owner = owner_team_name.strip().casefold()
    owner_rows = [
        row
        for row in roster_rows
        if row.get("team_name", "").strip().casefold() == normalized_owner
    ]
    owner_team_id = owner_rows[0].get("team_id", "") if owner_rows else ""
    assets: list[OwnedAsset] = []
    unresolved_identity_count = 0
    for row in roster_rows:
        sleeper_id = row.get("player_id", "").strip()
        current_id = f"current:{sleeper_id}"
        rookie_id = approved_rookie_ids.get(sleeper_id, "")
        if current_id in governed_asset_ids:
            asset_id = current_id
        elif rookie_id and rookie_id in governed_asset_ids:
            asset_id = rookie_id
        else:
            asset_id = f"sleeper-unmapped:{sleeper_id}"
            unresolved_identity_count += 1
        assets.append(
            OwnedAsset(
                asset_id=asset_id,
                asset_name=row.get("player_name", "").strip(),
                asset_kind="player",
                team_id=row.get("team_id", "").strip(),
                team_name=row.get("team_name", "").strip(),
                position=row.get("position", "").strip(),
            )
        )
    picks = tuple(
        OwnedAsset(
            asset_id=(
                f"pick:{row.get('pick_year', '').strip()}:"
                f"{row.get('round', '').strip()}:{row.get('original_team_id', '').strip()}"
            ),
            asset_name=row.get("pick_label", "").strip(),
            asset_kind="pick",
            team_id=row.get("current_team_id", "").strip(),
            team_name=row.get("current_team_name", "").strip(),
            pick_year=_integer(row.get("pick_year")),
            pick_round=_integer(row.get("round")),
            original_team_name=row.get("original_team_name", "").strip(),
        )
        for row in pick_rows
        if row.get("pick_year") and row.get("round")
    )
    league_ids = {
        row.get("league_id", "").strip()
        for row in metadata_rows
        if row.get("league_id", "").strip()
    }
    snapshot_dates = {
        row.get("snapshot_date", "").strip()
        for row in metadata_rows
        if row.get("snapshot_date", "").strip()
    }
    critical_warnings: list[str] = []
    if not owner_rows:
        critical_warnings.append(
            f"Owner team {owner_team_name!r} is absent from current roster facts."
        )
    if len(league_ids) != 1:
        critical_warnings.append(
            "Current roster snapshot does not resolve exactly one league ID."
        )
    years = {asset.pick_year for asset in picks if asset.pick_year is not None}
    if not ({2027, 2028} <= years):
        critical_warnings.append(
            "Current snapshot does not prove both 2027 and 2028 pick ownership."
        )
    warnings = list(critical_warnings)
    if unresolved_identity_count:
        warnings.append(
            f"{unresolved_identity_count} roster players remain outside governed NWR selectors; "
            "they can inform roster composition but cannot be named in counters."
        )
    counts = Counter(asset.team_name for asset in assets)
    return RosterOwnershipAudit(
        classification=CURRENT_ROSTER_STATE if not critical_warnings else ROSTER_STATE,
        source_path=str(snapshot),
        snapshot_date=next(iter(snapshot_dates), snapshot.name.rsplit("_", 1)[-1]),
        league_id=next(iter(league_ids), ""),
        owner_team_id=owner_team_id,
        owner_team_name=owner_team_name,
        player_assets=tuple(assets),
        pick_assets=picks,
        team_asset_counts=tuple(sorted(counts.items())),
        warnings=tuple(warnings),
    )


def _approved_rookie_sleeper_ids(repo_root: Path) -> dict[str, str]:
    path = repo_root / (
        "docs/hq/data_sources/nflverse_approved_identity_nwr_binding_v1_20260630/"
        "approved_identity_nwr_binding_matrix.csv"
    )
    if not path.is_file():
        return {}
    approved: dict[str, str] = {}
    for row in _csv_rows(path):
        safe = (
            row.get("approved_by_human", "").casefold() == "true"
            and row.get("binding_status") == "BOUND_REVIEW_ONLY"
            and row.get("ambiguity_flag", "").casefold() == "false"
            and row.get("same_name_collision_flag", "").casefold() == "false"
            and row.get("position_mismatch_flag", "").casefold() == "false"
            and row.get("team_mismatch_flag", "").casefold() == "false"
        )
        sleeper_id = row.get("candidate_nwr_player_id", "").strip()
        rookie_id = row.get("approved_nflverse_id", "").strip()
        if safe and sleeper_id and rookie_id:
            approved[sleeper_id] = f"rookie:{rookie_id}"
    return approved


def _csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise ValueError(f"Required roster snapshot file is missing: {path.name}")
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return [
            {str(key): str(value or "") for key, value in row.items()}
            for row in csv.DictReader(handle)
        ]


def resolve_trade_ownership(
    state: TradeState,
    lookup: Mapping[str, Mapping[str, object]],
    audit: RosterOwnershipAudit,
) -> TradeOwnershipResolution:
    """Resolve owner/counterparty from exact facts; conflicts and missing rows block counters."""

    rows = trade_item_rows(state, dict(lookup)).to_dict("records")
    players = {asset.asset_id: asset for asset in audit.player_assets}
    picks_by_class: dict[tuple[int, int], list[OwnedAsset]] = {}
    for asset in audit.pick_assets:
        if asset.pick_year is not None and asset.pick_round is not None:
            picks_by_class.setdefault((asset.pick_year, asset.pick_round), []).append(asset)

    checks: list[AssetOwnershipCheck] = []
    incoming_teams: set[tuple[str, str]] = set()
    conflicts: list[str] = []
    for row in rows:
        side = str(row.get("side") or "")
        item_key = str(row.get("item_key") or "")
        asset_id = str(row.get("asset_id") or "")
        name = str(row.get("player") or row.get("label") or asset_id)
        expected = audit.owner_team_name if side == "You give" else "one opponent team"
        owned: OwnedAsset | None = None
        evidence = ""
        status = "UNRESOLVED"
        if str(row.get("registry_asset_type") or "") in {
            "Current Player",
            "Rookie Review",
        }:
            owned = players.get(asset_id)
            if owned:
                status = "RESOLVED"
                evidence = (
                    f"The current local roster snapshot maps {name} ({asset_id}) to "
                    f"{owned.team_name} ({owned.team_id})."
                )
            else:
                evidence = f"No exact governed ownership row exists for {asset_id}."
        elif str(row.get("asset_type") or "") == "Pick context":
            parsed = _parse_pick(name)
            candidates = picks_by_class.get(parsed, []) if parsed else []
            if side == "You give":
                candidates = [asset for asset in candidates if asset.team_id == audit.owner_team_id]
            if len(candidates) == 1:
                owned = candidates[0]
                status = "RESOLVED"
                evidence = (
                    f"fact_future_picks.csv has one exact {name} ownership candidate: "
                    f"{owned.team_name}, originally {owned.original_team_name}."
                )
            elif candidates:
                status = "AMBIGUOUS"
                evidence = f"{len(candidates)} ownership rows match generic pick class {name}."
            else:
                evidence = f"No admitted future-pick ownership row matches {name}."
        else:
            evidence = (
                f"{name} is not a current-player roster row; its ownership is not present "
                "in the admitted roster snapshot."
            )

        resolved_team = owned.team_name if owned else ""
        if owned and side == "You give" and owned.team_id != audit.owner_team_id:
            status = "CONFLICT"
            conflicts.append(
                f"Owner does not have proven ownership of {name}; {owned.team_name} does."
            )
        if owned and side == "You receive":
            incoming_teams.add((owned.team_id, owned.team_name))
            if owned.team_id == audit.owner_team_id:
                status = "CONFLICT"
                conflicts.append(f"Incoming asset {name} is already mapped to the owner team.")
        if status != "RESOLVED":
            conflicts.append(f"{name}: {evidence}")
        checks.append(
            AssetOwnershipCheck(
                side=side,
                item_key=item_key,
                asset_id=asset_id,
                asset_name=name,
                expected_team=expected,
                resolved_team=resolved_team,
                status=status,
                evidence=evidence,
            )
        )

    incoming_rows = [check for check in checks if check.side == "You receive"]
    outgoing_rows = [check for check in checks if check.side == "You give"]
    all_exact = bool(incoming_rows and outgoing_rows) and all(
        check.status == "RESOLVED" for check in checks
    )
    one_counterparty = len(incoming_teams) == 1
    if len(incoming_teams) > 1:
        mapping = ", ".join(name for _, name in sorted(incoming_teams))
        conflicts.append(f"Incoming assets resolve to multiple teams: {mapping}.")
    resolved = all_exact and one_counterparty
    counterpart_id, counterpart_name = next(iter(incoming_teams)) if resolved else ("", "")
    player_counts = Counter(asset.team_id for asset in audit.player_assets)
    pick_counts = Counter(asset.team_id for asset in audit.pick_assets)
    return TradeOwnershipResolution(
        status=COUNTERPARTY_RESOLVED if resolved else COUNTER_BLOCKED,
        classification=audit.classification,
        owner_team_id=audit.owner_team_id,
        owner_team_name=audit.owner_team_name,
        counterparty_team_id=counterpart_id,
        counterparty_team_name=counterpart_name,
        candidate_counterparty_teams=tuple(name for _, name in sorted(incoming_teams)),
        checks=tuple(checks),
        conflicts=tuple(dict.fromkeys(conflicts)),
        owner_roster_asset_count=player_counts[audit.owner_team_id],
        owner_pick_count=pick_counts[audit.owner_team_id],
        opponent_roster_asset_count=player_counts[counterpart_id] if resolved else 0,
        opponent_pick_count=pick_counts[counterpart_id] if resolved else 0,
        source_path=audit.source_path,
        snapshot_date=audit.snapshot_date,
    )


def build_market_negotiation_context(
    state: TradeState,
    lookup: Mapping[str, Mapping[str, object]],
) -> MarketNegotiationContext:
    """Display same-snapshot DP totals only; never feed them into NWR synthesis."""

    rows = trade_item_rows(state, dict(lookup)).to_dict("records")
    give = _market_side("You give", rows)
    receive = _market_side("You receive", rows)
    dates = {
        _market_date(str(row.get("market_status") or ""))
        for row in rows
        if _positive_number(row.get("market_dp_value")) is not None
    }
    dates.discard("")
    same_snapshot = dates == {MARKET_DATE}
    delta = None
    if same_snapshot and give.displayed_total is not None and receive.displayed_total is not None:
        delta = receive.displayed_total - give.displayed_total
    return MarketNegotiationContext(
        label=MARKET_LABEL,
        as_of_date=MARKET_DATE,
        give=give,
        receive=receive,
        displayed_delta_receive_minus_give=delta,
        same_snapshot=same_snapshot,
        warning=(
            "External DP totals cover only listed assets with valid values from the same "
            "snapshot. Excluded rookies/picks remain excluded. This is not an NWR package value."
        ),
    )


def build_roster_composition(
    audit: RosterOwnershipAudit, team_id: str
) -> RosterComposition:
    players = [asset for asset in audit.player_assets if asset.team_id == team_id]
    picks = [asset for asset in audit.pick_assets if asset.team_id == team_id]
    counts = Counter(asset.position or "Unknown" for asset in players)
    team_name = next((asset.team_name for asset in players), "Not resolved")
    return RosterComposition(
        team_name=team_name,
        position_counts=tuple(sorted(counts.items())),
        player_count=len(players),
        pick_count=len(picks),
    )


def build_opponent_opportunity_map(
    audit: RosterOwnershipAudit,
    resolution: TradeOwnershipResolution,
    lookup: Mapping[str, Mapping[str, object]],
    *,
    team_window: str,
) -> tuple[RosterOpportunity, ...]:
    """Compare ordinal NWR/market bands for every governed opponent player."""

    if not resolution.counterparty_resolved:
        return ()
    key_by_asset = {
        str(row.get("asset_id") or ""): key
        for key, row in lookup.items()
        if str(row.get("asset_id") or "")
    }
    opportunities: list[RosterOpportunity] = []
    for owned in audit.player_assets:
        if owned.team_id != resolution.counterparty_team_id:
            continue
        item_key = key_by_asset.get(owned.asset_id, "")
        row = lookup.get(item_key, {})
        nwr_rank = _integer(row.get("dynasty_rank"))
        market_rank = _positive_number(row.get("market_dp_rank"))
        nwr_index, nwr_band = _rank_band(nwr_rank)
        market_index, market_band = _rank_band(market_rank)
        if nwr_rank is None or market_rank is None:
            interpretation = "Insufficient comparable rank-band evidence"
        elif nwr_index < market_index:
            interpretation = "NWR higher than market — potential buy-low"
        elif market_index < nwr_index:
            interpretation = "Market higher than NWR — acquisition caution"
        else:
            interpretation = "NWR and market agree at the declared rank-band level"
        opportunities.append(
            RosterOpportunity(
                item_key=item_key,
                asset_id=owned.asset_id,
                asset_name=owned.asset_name,
                position=owned.position,
                nwr_rank=nwr_rank,
                nwr_band=nwr_band,
                market_dp_value=(
                    round(value)
                    if (value := _positive_number(row.get("market_dp_value"))) is not None
                    else None
                ),
                market_dp_rank=market_rank,
                market_band=market_band,
                gap_interpretation=interpretation,
                team_fit=_team_fit(owned.position, nwr_rank, team_window),
            )
        )
    return tuple(
        sorted(
            opportunities,
            key=lambda row: (
                row.nwr_rank is None,
                row.nwr_rank or 9999,
                row.asset_name.casefold(),
            ),
        )
    )


def generate_roster_aware_counters(
    state: TradeState,
    lookup: Mapping[str, Mapping[str, object]],
    audit: RosterOwnershipAudit,
    resolution: TradeOwnershipResolution,
    *,
    team_window: str,
) -> tuple[RosterAwareCounter, ...]:
    """Return a small, constructible counter set or nothing when ownership is blocked.

    Candidate selection uses declared rank bands, team fit, and external market context as
    separate heuristics.  It does not calculate an NWR package value.
    """

    if not resolution.counterparty_resolved:
        return ()
    normalized = {
        "give": tuple(key for key in state.get("give", []) if key in lookup),
        "get": tuple(key for key in state.get("get", []) if key in lookup),
    }
    owned_by_key = {check.item_key: check for check in resolution.checks}
    if not all(
        check.status == "RESOLVED" for check in resolution.checks
    ) or not normalized["give"] or not normalized["get"]:
        return ()
    opportunities = tuple(
        row
        for row in build_opponent_opportunity_map(
            audit, resolution, lookup, team_window=team_window
        )
        if row.item_key and row.item_key not in normalized["get"]
    )
    if not opportunities:
        return ()
    buy_lows = [row for row in opportunities if "potential buy-low" in row.gap_interpretation]
    best = opportunities[0]
    exploit = buy_lows[0] if buy_lows else best
    fit = next((row for row in opportunities if row.team_fit.startswith("Strong")), best)
    original_names = {
        key: str(lookup[key].get("player") or lookup[key].get("label") or key)
        for key in (*normalized["give"], *normalized["get"])
    }
    candidates: list[RosterAwareCounter] = []

    def add_counter(
        counter_id: str,
        title: str,
        give: tuple[str, ...],
        receive: tuple[str, ...],
        changes: tuple[str, ...],
        target: RosterOpportunity,
        risk: str,
    ) -> None:
        if not _counter_is_constructible(give, receive, audit, resolution, lookup):
            return
        counter = RosterAwareCounter(
            counter_id=counter_id,
            title=title,
            give=give,
            receive=receive,
            changes=changes,
            why_this_helps_me=(
                f"Targets {target.asset_name}, an opponent-owned {target.position} with "
                f"{target.nwr_band} NWR standing.",
                f"The {team_window.upper()} view labels this fit: {target.team_fit}",
            ),
            why_they_might_consider=(
                "They retain the owner assets already offered and negotiate from their "
                "documented roster depth.",
                (
                    f"External market context lists {target.asset_name} at DP Value "
                    f"{target.market_dp_value:,}."
                    if target.market_dp_value is not None
                    else "No DP Value is used for this target; plausibility needs manager review."
                ),
            ),
            nwr_vs_market_opportunity=target.gap_interpretation,
            main_risk=risk,
        )
        if counter not in candidates:
            candidates.append(counter)

    add_counter(
        "best-nwr-value",
        "Best NWR value",
        normalized["give"],
        (*normalized["get"], best.item_key),
        (f"Add opponent-owned {best.asset_name} to the incoming side.",),
        best,
        (
            "This is an aggressive ask; external market context is negotiation evidence, "
            "not acceptance proof."
        ),
    )
    if exploit.item_key != best.item_key:
        replace_key = _weakest_ranked_key(normalized["get"], lookup)
        receive = tuple(key for key in normalized["get"] if key != replace_key) + (
            exploit.item_key,
        )
        add_counter(
            "best-market-exploit",
            "Best market exploit",
            normalized["give"],
            receive,
            (
                f"Replace {original_names.get(replace_key, replace_key)} with "
                f"opponent-owned {exploit.asset_name}.",
            ),
            exploit,
            "The NWR/market gap is ordinal and may not match the other manager's preferences.",
        )
    premium_give = _best_ranked_key(normalized["give"], lookup)
    if premium_give and len(normalized["give"]) > 1:
        give = tuple(key for key in normalized["give"] if key != premium_give)
        replace_receive = _best_ranked_key(normalized["get"], lookup)
        receive = tuple(key for key in normalized["get"] if key != replace_receive)
        if fit.item_key not in receive:
            receive = (*receive, fit.item_key)
        if receive:
            add_counter(
                "keep-premium",
                "Keep the premium outgoing asset",
                give,
                receive,
                (
                    f"Keep {original_names[premium_give]} and remove "
                    f"{original_names.get(replace_receive, replace_receive)} from the return.",
                ),
                fit,
                (
                    "Removing both anchors changes the negotiation materially and still "
                    "needs owner judgment."
                ),
            )
    if fit.item_key not in {best.item_key, exploit.item_key}:
        replace_key = _weakest_ranked_key(normalized["get"], lookup)
        receive = tuple(key for key in normalized["get"] if key != replace_key) + (
            fit.item_key,
        )
        add_counter(
            "best-roster-fit",
            "Best roster-fit counter",
            normalized["give"],
            receive,
            (f"Target opponent-owned {fit.asset_name} for the {team_window} plan.",),
            fit,
            "Roster fit does not guarantee equivalent negotiation value.",
        )
    # Every give/receive key is rechecked against the full audit before display.
    assert all(
        _counter_is_constructible(row.give, row.receive, audit, resolution, lookup)
        for row in candidates
    )
    assert all(check.status == "RESOLVED" for check in owned_by_key.values())
    return tuple(candidates[:4])


def _counter_is_constructible(
    give: tuple[str, ...],
    receive: tuple[str, ...],
    audit: RosterOwnershipAudit,
    resolution: TradeOwnershipResolution,
    lookup: Mapping[str, Mapping[str, object]],
) -> bool:
    if not give or not receive or len(set(give)) != len(give) or len(set(receive)) != len(receive):
        return False
    if set(give) & set(receive):
        return False
    return (
        all(
            _lookup_asset_owned_by_team(lookup[key], audit.owner_team_id, audit)
            for key in give
            if key in lookup
        )
        and all(
            _lookup_asset_owned_by_team(
                lookup[key], resolution.counterparty_team_id, audit
            )
            for key in receive
            if key in lookup
        )
        and all(key in lookup for key in (*give, *receive))
    )


def _lookup_asset_owned_by_team(
    row: Mapping[str, object], team_id: str, audit: RosterOwnershipAudit
) -> bool:
    asset_id = str(row.get("asset_id") or "")
    if any(
        asset.asset_id == asset_id and asset.team_id == team_id
        for asset in audit.player_assets
    ):
        return True
    if str(row.get("asset_type") or "") != "Pick context":
        return False
    parsed = _parse_pick(str(row.get("player") or row.get("label") or ""))
    if parsed is None:
        return False
    year, round_number = parsed
    candidates = [
        asset
        for asset in audit.pick_assets
        if asset.team_id == team_id
        and asset.pick_year == year
        and asset.pick_round == round_number
    ]
    return len(candidates) == 1


def _best_ranked_key(
    keys: tuple[str, ...], lookup: Mapping[str, Mapping[str, object]]
) -> str:
    ranked = [
        (_integer(lookup[key].get("dynasty_rank")), key)
        for key in keys
        if key in lookup and _integer(lookup[key].get("dynasty_rank")) is not None
    ]
    return min(ranked)[1] if ranked else ""


def _weakest_ranked_key(
    keys: tuple[str, ...], lookup: Mapping[str, Mapping[str, object]]
) -> str:
    ranked = [
        (_integer(lookup[key].get("dynasty_rank")), key)
        for key in keys
        if key in lookup and _integer(lookup[key].get("dynasty_rank")) is not None
    ]
    return max(ranked)[1] if ranked else keys[-1]


def _rank_band(rank: int | float | None) -> tuple[int, str]:
    if rank is None:
        return (99, "NWR/market rank unavailable")
    for index, (ceiling, label) in enumerate(
        ((25, "Top 25"), (50, "Top 50"), (100, "Top 100"), (150, "Top 150"))
    ):
        if rank <= ceiling:
            return (index, label)
    return (4, "Outside Top 150")


def _team_fit(position: str, nwr_rank: int | None, team_window: str) -> str:
    if nwr_rank is None:
        return "Unresolved — NWR rank unavailable"
    if team_window == "Contending":
        if position in {"RB", "WR", "TE"} and nwr_rank <= 100:
            return "Strong immediate/flex fit"
        return "Secondary fit"
    if team_window == "Rebuilding":
        if nwr_rank <= 100:
            return "Strong long-horizon candidate; verify age/youth evidence"
        return "Secondary fit"
    return "Strong total-dynasty fit" if nwr_rank <= 100 else "Secondary fit"


def _market_side(side: str, rows: list[dict[str, object]]) -> MarketSideContext:
    included: list[str] = []
    excluded: list[str] = []
    values: list[int] = []
    for row in rows:
        if str(row.get("side") or "") != side:
            continue
        name = str(row.get("player") or row.get("label") or "Unknown asset")
        value = _positive_number(row.get("market_dp_value"))
        date = _market_date(str(row.get("market_status") or ""))
        if value is not None and date == MARKET_DATE:
            values.append(round(value))
            included.append(f"{name} ({round(value):,})")
        else:
            excluded.append(name)
    return MarketSideContext(
        side=side,
        displayed_total=sum(values) if values else None,
        included_assets=tuple(included),
        excluded_assets=tuple(excluded),
    )


def _parse_pick(name: str) -> tuple[int, int] | None:
    match = _PICK_PATTERN.match(name.strip())
    return (int(match.group("year")), int(match.group("round"))) if match else None


def _market_date(status: str) -> str:
    match = re.search(r"20\d{2}-\d{2}-\d{2}", status)
    return match.group(0) if match else ""


def _positive_number(value: object) -> float | None:
    try:
        number = float(str(value or "").replace(",", "").strip())
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None


def _integer(value: object) -> int | None:
    try:
        return int(str(value or "").strip())
    except (TypeError, ValueError):
        return None
