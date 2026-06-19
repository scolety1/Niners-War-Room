from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

AssetType = Literal["player", "pick"]
ReviewStatus = Literal["review", "hold", "blocked"]


@dataclass(frozen=True, kw_only=True)
class FantasyAsset:
    asset_id: str
    display_name: str
    asset_type: AssetType
    nwr_value: float
    public_market_value: float
    position: str = ""
    team_name: str = ""
    scarcity_tag: str = "normal"
    keeper_status: str = "review"
    drop_pressure_tag: str = "neutral"
    rookie_pick_context: str = "not a rookie pick"
    notes: tuple[str, ...] = ()


@dataclass(frozen=True, kw_only=True)
class PlayerAsset(FantasyAsset):
    asset_type: AssetType = "player"


@dataclass(frozen=True, kw_only=True)
class PickAsset(FantasyAsset):
    asset_type: AssetType = "pick"
    position: str = "PICK"
    keeper_status: str = "not keeper eligible"


@dataclass(frozen=True, kw_only=True)
class TeamContext:
    team_name: str
    roster_needs: tuple[str, ...] = ()
    surplus_tags: tuple[str, ...] = ()
    trade_style: str = "manual review"
    notes: tuple[str, ...] = ()


@dataclass(frozen=True, kw_only=True)
class TradeSide:
    team_name: str
    assets: tuple[FantasyAsset, ...]
    notes: tuple[str, ...] = ()

    @property
    def nwr_value_total(self) -> float:
        return sum(asset.nwr_value for asset in self.assets)

    @property
    def public_market_value_total(self) -> float:
        return sum(asset.public_market_value for asset in self.assets)


@dataclass(frozen=True, kw_only=True)
class TradePackage:
    package_id: str
    mode: str
    give_side: TradeSide
    get_side: TradeSide
    opponent_context: TeamContext
    notes: tuple[str, ...] = ()


@dataclass(frozen=True, kw_only=True)
class ValueSnapshot:
    snapshot_id: str
    assets: tuple[FantasyAsset, ...]
    team_contexts: tuple[TeamContext, ...]
    source_note: str = "fixture-only values"


@dataclass(frozen=True, kw_only=True)
class PackageScore:
    nwr_delta: float
    public_market_delta: float
    market_fairness: str
    opponent_fit: str
    roster_impact: str
    keeper_drop_impact: str
    risk_label: str


@dataclass(frozen=True, kw_only=True)
class TradeReview:
    package: TradePackage
    score: PackageScore
    verdict: str
    warnings: tuple[str, ...] = ()
    review_status: ReviewStatus = "review"
    manual_notes: tuple[str, ...] = field(default_factory=tuple)
