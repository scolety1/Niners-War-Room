from __future__ import annotations

import csv
import re
import zipfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from src.config.constants import DEFAULT_DATA_PACK
from src.services.model_v4_sprint14b_cut_keep_pressure_service import (
    DEFAULT_14B_OUTPUT_ROOT,
)

SPRINT_14C_VERSION = "model_v4_sprint_14c_external_asset_reviews_0.1.0"
DEFAULT_OUTPUT_ROOT = Path("local_exports/model_v4/external_asset_reviews/latest")
DEFAULT_PACKET_ROOT = Path("local_exports/model_v4/audit_packets")
DATA_PACK_ROOT = Path(DEFAULT_DATA_PACK)
ROSTERS_PATH = DATA_PACK_ROOT / "fact_rosters.csv"
PRESSURE_ROWS = DEFAULT_14B_OUTPUT_ROOT / "cut_keep_pressure_review_rows.csv"
PRESSURE_COMPONENTS = DEFAULT_14B_OUTPUT_ROOT / "cut_keep_pressure_component_rows.csv"
PRESSURE_RECEIPTS = DEFAULT_14B_OUTPUT_ROOT / "cut_keep_pressure_receipts.csv"
ASSET_ROWS = Path(
    "local_exports/model_v4/dynasty_asset_value/latest/dynasty_asset_value_review_rows.csv"
)
SPRINT14C_DOC = Path("docs/model_v4/SPRINT_14C_TRADE_AWAY_FOR_REVIEW.md")
SPRINT14C_AUDIT_PROMPT = Path("docs/model_v4/SPRINT_14C_EXTERNAL_AUDIT_PROMPT.md")

TRADE_AWAY_HEADER = (
    "trade_review_key",
    "player_name",
    "position",
    "nfl_team",
    "league_rank",
    "dynasty_asset_value_review_score",
    "pressure_score",
    "source_path",
    "source_column",
    "lineage_class",
    "pressure_band",
    "trade_away_review_band",
    "review_rationale",
    "risk_factors",
    "protection_factors",
    "allowed_use",
    "blocked_use",
    "warning_flags",
    "formula_version",
)

EXTERNAL_ASSET_HEADER = (
    "external_asset_review_key",
    "asset_name",
    "asset_type",
    "position",
    "team_or_college",
    "current_owner_team",
    "dynasty_asset_value_review_score",
    "source_path",
    "source_column",
    "lineage_class",
    "confidence_cap",
    "position_fit_context",
    "external_asset_review_band",
    "review_rationale",
    "allowed_use",
    "blocked_use",
    "warning_flags",
    "formula_version",
)
# Compatibility-only alias for older callers; canonical rows are External Asset
# Reviews and must not be interpreted as trade-for recommendations.
TRADE_FOR_HEADER = EXTERNAL_ASSET_HEADER

COMPONENT_HEADER = (
    "trade_review_key",
    "entity_name",
    "side",
    "component_name",
    "component_value",
    "source_status",
    "receipt_pointer",
    "formula_version",
)

RECEIPT_HEADER = (
    "trade_review_key",
    "entity_name",
    "side",
    "receipt_layer",
    "receipt_pointer",
    "source_status",
    "formula_version",
)

WARNING_HEADER = (
    "trade_review_key",
    "entity_name",
    "side",
    "severity",
    "warning_code",
    "warning_detail",
    "next_action",
    "formula_version",
)

SUMMARY_HEADER = (
    "summary_key",
    "summary_value",
    "source",
    "allowed_use",
    "formula_version",
)


@dataclass(frozen=True)
class TradeReviewResult:
    trade_away_rows: tuple[dict[str, object], ...]
    external_asset_rows: tuple[dict[str, object], ...]
    component_rows: tuple[dict[str, object], ...]
    receipt_rows: tuple[dict[str, object], ...]
    warning_rows: tuple[dict[str, object], ...]
    summary_rows: tuple[dict[str, object], ...]
    summary: dict[str, object]

    @property
    def trade_for_rows(self) -> tuple[dict[str, object], ...]:
        """Compatibility-only alias for external asset review rows."""
        return self.external_asset_rows


@dataclass(frozen=True)
class TradeReviewPaths:
    trade_away_rows: Path
    external_asset_rows: Path
    components: Path
    receipts: Path
    warnings: Path
    summary: Path
    doc: Path
    audit_prompt: Path
    audit_packet: Path

    @property
    def trade_for_rows(self) -> Path:
        """Compatibility-only alias for the external asset review export path."""
        return self.external_asset_rows


def build_trade_review_outputs(
    *,
    pressure_rows_path: str | Path = PRESSURE_ROWS,
    asset_rows_path: str | Path = ASSET_ROWS,
    rosters_path: str | Path = ROSTERS_PATH,
) -> TradeReviewResult:
    pressure_rows = _read_rows(Path(pressure_rows_path))
    asset_rows = _read_rows(Path(asset_rows_path))
    roster_rows = _read_rows(Path(rosters_path))
    niners_names = {_normalize_name(row["player_name"]) for row in pressure_rows}
    owner_by_name = _owner_by_name(roster_rows)
    position_counts = _position_counts(pressure_rows)

    trade_away_rows = tuple(_trade_away_row(row) for row in pressure_rows)
    external_asset_rows = tuple(
        _external_asset_row(row, owner_by_name, position_counts)
        for row in _external_asset_pool(asset_rows, niners_names)
    )
    component_rows = (
        *_trade_away_components(trade_away_rows),
        *_external_asset_components(external_asset_rows),
    )
    receipt_rows = (
        *_trade_away_receipts(trade_away_rows),
        *_external_asset_receipts(external_asset_rows),
    )
    warning_rows = (
        *_trade_away_warnings(trade_away_rows),
        *_external_asset_warnings(external_asset_rows),
        _global_warning(),
    )
    summary_rows = _summary_rows(trade_away_rows, external_asset_rows)
    summary = {
        "review_status": "review_only",
        "trade_away_rows": len(trade_away_rows),
        "external_asset_rows": len(external_asset_rows),
        "trade_for_rows": len(external_asset_rows),
        "trade_recommendations_created": False,
        "trade_packages_created": False,
        "active_rankings_changed": False,
        "readiness_unlocked": False,
    }
    return TradeReviewResult(
        trade_away_rows=trade_away_rows,
        external_asset_rows=external_asset_rows,
        component_rows=tuple(component_rows),
        receipt_rows=tuple(receipt_rows),
        warning_rows=tuple(warning_rows),
        summary_rows=summary_rows,
        summary=summary,
    )


def write_trade_review_outputs(
    *,
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
    packet_root: str | Path = DEFAULT_PACKET_ROOT,
    result: TradeReviewResult | None = None,
) -> TradeReviewPaths:
    result = result or build_trade_review_outputs()
    output = Path(output_root)
    output.mkdir(parents=True, exist_ok=True)
    packet_path = (
        Path(packet_root) / "sprint14c_external_asset_reviews_audit_packet_20260518.zip"
    )
    paths = TradeReviewPaths(
        trade_away_rows=output / "trade_away_candidate_review_rows.csv",
        external_asset_rows=output / "external_asset_context_review_rows.csv",
        components=output / "external_asset_review_component_rows.csv",
        receipts=output / "external_asset_review_receipts.csv",
        warnings=output / "external_asset_review_warnings.csv",
        summary=output / "external_asset_review_summary.csv",
        doc=SPRINT14C_DOC,
        audit_prompt=SPRINT14C_AUDIT_PROMPT,
        audit_packet=packet_path,
    )
    _write_csv(paths.trade_away_rows, TRADE_AWAY_HEADER, result.trade_away_rows)
    _write_csv(paths.external_asset_rows, EXTERNAL_ASSET_HEADER, result.external_asset_rows)
    _write_csv(paths.components, COMPONENT_HEADER, result.component_rows)
    _write_csv(paths.receipts, RECEIPT_HEADER, result.receipt_rows)
    _write_csv(paths.warnings, WARNING_HEADER, result.warning_rows)
    _write_csv(paths.summary, SUMMARY_HEADER, result.summary_rows)
    _write_text(paths.doc, _doc(result, paths))
    _write_text(paths.audit_prompt, _audit_prompt(paths))
    _write_packet(paths, packet_path)
    return paths


def _trade_away_row(row: dict[str, str]) -> dict[str, object]:
    pressure = _float(row.get("pressure_score"), 0.0) or 0.0
    value = _float(row.get("dynasty_asset_value_review_score"), 0.0) or 0.0
    band = _trade_away_band(row, pressure, value)
    return {
        "trade_review_key": f"trade-away:{row['pressure_key']}",
        "player_name": row["player_name"],
        "position": row["position"],
        "nfl_team": row["nfl_team"],
        "league_rank": row["league_rank"],
        "dynasty_asset_value_review_score": value,
        "pressure_score": pressure,
        "source_path": str(PRESSURE_ROWS),
        "source_column": "pressure_score",
        "lineage_class": "review_v4_roster_pressure_context",
        "pressure_band": row["pressure_band"],
        "trade_away_review_band": band,
        "review_rationale": _trade_away_rationale(row, band),
        "risk_factors": row["risk_factors"],
        "protection_factors": row["protection_factors"],
        "allowed_use": "review_only_trade_away_context_not_recommendation",
        "blocked_use": "do_not_use_as_trade_offer_or_sell_call",
        "warning_flags": _join_flags(
            row.get("warning_flags"),
            "review_only_no_trade_recommendation",
        ),
        "formula_version": SPRINT_14C_VERSION,
    }


def _trade_away_band(row: dict[str, str], pressure: float, value: float) -> str:
    if row["pressure_band"] == "required_pressure_zone_review":
        return "liquidity_check_context_review"
    if pressure >= 50.0:
        return "pressure_shop_watch_review"
    if value >= 50.0:
        return "hold_core_unless_overpay_review"
    if row["pressure_band"] == "protectable_depth_review":
        return "depth_liquidity_watch_review"
    return "hold_context_review"


def _trade_away_rationale(row: dict[str, str], band: str) -> str:
    if band == "liquidity_check_context_review":
        return "Below inferred protect line; review liquidity context before any cut logic."
    if band == "pressure_shop_watch_review":
        return "Pressure score is elevated, but this is not a sell recommendation."
    if band == "hold_core_unless_overpay_review":
        return "Model value is strong enough that only audit-cleared overpay context matters."
    if band == "depth_liquidity_watch_review":
        return "Protectable depth can be reviewed for roster flexibility."
    return "No urgent trade-away pressure from current review layer."


def _external_asset_pool(
    asset_rows: tuple[dict[str, str], ...],
    niners_names: set[str],
) -> tuple[dict[str, str], ...]:
    external = [
        row
        for row in asset_rows
        if row.get("asset_type") == "current_player"
        and _normalize_name(row.get("asset_name", "")) not in niners_names
    ]
    return tuple(
        sorted(
            external,
            key=lambda row: _float(row.get("dynasty_asset_value_review_score"), -1.0) or -1.0,
            reverse=True,
        )[:35]
    )


def _external_asset_row(
    row: dict[str, str],
    owner_by_name: dict[str, str],
    position_counts: dict[str, int],
) -> dict[str, object]:
    value = _float(row.get("dynasty_asset_value_review_score"), 0.0) or 0.0
    confidence = _float(row.get("confidence_cap"), 0.75) or 0.75
    position = row.get("position", "")
    fit = _position_fit_context(position, position_counts)
    band = _external_asset_band(value, confidence, fit)
    name = row["asset_name"]
    return {
        "external_asset_review_key": f"external-asset:{row['asset_key']}",
        "asset_name": name,
        "asset_type": row["asset_type"],
        "position": position,
        "team_or_college": row.get("team_or_college", ""),
        "current_owner_team": owner_by_name.get(_normalize_name(name), "unknown_or_free_agent"),
        "dynasty_asset_value_review_score": value,
        "source_path": str(ASSET_ROWS),
        "source_column": "dynasty_asset_value_review_score",
        "lineage_class": "review_v4_dynasty_asset",
        "confidence_cap": confidence,
        "position_fit_context": fit,
        "external_asset_review_band": band,
        "review_rationale": _external_asset_rationale(band),
        "allowed_use": "review_only_external_asset_context_not_recommendation",
        "blocked_use": "do_not_use_as_trade_offer_buy_call_or_acquisition_call",
        "warning_flags": _join_flags(
            row.get("warning_flags"),
            "review_only_no_trade_recommendation",
        ),
        "formula_version": SPRINT_14C_VERSION,
    }


def _position_fit_context(position: str, position_counts: dict[str, int]) -> str:
    counts = {"QB": 2, "RB": 6, "WR": 9, "TE": 3}
    if position_counts.get(position, 0) < counts.get(position, 4):
        return "possible_roster_structure_fit_review"
    if position in {"RB", "WR"}:
        return "premium_flex_asset_fit_review"
    return "luxury_or_depth_fit_review"


def _external_asset_band(value: float, confidence: float, fit: str) -> str:
    if value >= 75.0 and confidence >= 0.85:
        return "elite_external_asset_context_review"
    if value >= 60.0:
        return "strong_external_asset_context_review"
    if fit == "possible_roster_structure_fit_review" and value >= 45.0:
        return "roster_fit_external_asset_context_review"
    return "external_asset_context_review"


def _external_asset_rationale(band: str) -> str:
    if band == "elite_external_asset_context_review":
        return "High private value and usable confidence; review context separately."
    if band == "strong_external_asset_context_review":
        return "Strong private value, but no offer or acquisition logic has been generated."
    if band == "roster_fit_external_asset_context_review":
        return "Position context may fit roster construction; review before any action."
    return "Context-only external asset row; not an acquisition recommendation."


def _trade_away_components(rows: tuple[dict[str, object], ...]) -> tuple[dict[str, object], ...]:
    output: list[dict[str, object]] = []
    for row in rows:
        output.extend(
            [
                _component(
                    row["trade_review_key"],
                    row["player_name"],
                    "trade_away",
                    "pressure_score",
                    row["pressure_score"],
                    PRESSURE_ROWS,
                ),
                _component(
                    row["trade_review_key"],
                    row["player_name"],
                    "trade_away",
                    "pressure_band",
                    row["pressure_band"],
                    PRESSURE_ROWS,
                ),
                _component(
                    row["trade_review_key"],
                    row["player_name"],
                    "trade_away",
                    "risk_factors",
                    row["risk_factors"],
                    PRESSURE_ROWS,
                ),
            ]
        )
    return tuple(output)


def _external_asset_components(
    rows: tuple[dict[str, object], ...],
) -> tuple[dict[str, object], ...]:
    output: list[dict[str, object]] = []
    for row in rows:
        output.extend(
            [
                _component(
                    row["external_asset_review_key"],
                    row["asset_name"],
                    "external_asset_context",
                    "dynasty_asset_value_review_score",
                    row["dynasty_asset_value_review_score"],
                    ASSET_ROWS,
                ),
                _component(
                    row["external_asset_review_key"],
                    row["asset_name"],
                    "external_asset_context",
                    "confidence_cap",
                    row["confidence_cap"],
                    ASSET_ROWS,
                ),
                _component(
                    row["external_asset_review_key"],
                    row["asset_name"],
                    "external_asset_context",
                    "position_fit_context",
                    row["position_fit_context"],
                    PRESSURE_ROWS,
                ),
            ]
        )
    return tuple(output)


def _component(
    key: object,
    name: object,
    side: str,
    component_name: str,
    value: object,
    pointer: Path,
) -> dict[str, object]:
    return {
        "trade_review_key": key,
        "entity_name": name,
        "side": side,
        "component_name": component_name,
        "component_value": value,
        "source_status": "review_only_model_v4_output",
        "receipt_pointer": str(pointer),
        "formula_version": SPRINT_14C_VERSION,
    }


def _trade_away_receipts(rows: tuple[dict[str, object], ...]) -> tuple[dict[str, object], ...]:
    return tuple(
        _receipt(row["trade_review_key"], row["player_name"], "trade_away", PRESSURE_ROWS)
        for row in rows
    )


def _external_asset_receipts(rows: tuple[dict[str, object], ...]) -> tuple[dict[str, object], ...]:
    return tuple(
        _receipt(
            row["external_asset_review_key"],
            row["asset_name"],
            "external_asset_context",
            ASSET_ROWS,
        )
        for row in rows
    )


def _receipt(key: object, name: object, side: str, pointer: Path) -> dict[str, object]:
    return {
        "trade_review_key": key,
        "entity_name": name,
        "side": side,
        "receipt_layer": "sprint_14c_trade_review",
        "receipt_pointer": str(pointer),
        "source_status": "review_only_not_trade_recommendation",
        "formula_version": SPRINT_14C_VERSION,
    }


def _trade_away_warnings(rows: tuple[dict[str, object], ...]) -> tuple[dict[str, object], ...]:
    return tuple(
        _warning(
            row["trade_review_key"],
            row["player_name"],
            "trade_away",
            "review",
            "trade_away_context_not_sell_recommendation",
            "Trade-away row is pressure context only.",
            "Audit with market and package logic in later sprint.",
        )
        for row in rows
        if row["trade_away_review_band"] in {
            "liquidity_check_context_review",
            "pressure_shop_watch_review",
        }
    )


def _external_asset_warnings(rows: tuple[dict[str, object], ...]) -> tuple[dict[str, object], ...]:
    return tuple(
        _warning(
            row["external_asset_review_key"],
            row["asset_name"],
            "external_asset_context",
            "review",
            "external_asset_context_not_acquisition_recommendation",
            "External asset row is context only.",
            "Audit source, owner, and package logic separately before any action.",
        )
        for row in rows
        if row["external_asset_review_band"]
        in {"elite_external_asset_context_review", "strong_external_asset_context_review"}
    )


def _global_warning() -> dict[str, object]:
    return _warning(
        "sprint_14c",
        "External asset review layer",
        "all",
        "review",
        "no_trade_offers_or_recommendations_created",
        "Sprint 14C creates external asset context surfaces only.",
        "Run audit before pick/package/defer logic.",
    )


def _warning(
    key: object,
    name: object,
    side: str,
    severity: str,
    code: str,
    detail: str,
    next_action: str,
) -> dict[str, object]:
    return {
        "trade_review_key": key,
        "entity_name": name,
        "side": side,
        "severity": severity,
        "warning_code": code,
        "warning_detail": detail,
        "next_action": next_action,
        "formula_version": SPRINT_14C_VERSION,
    }


def _summary_rows(
    away_rows: tuple[dict[str, object], ...],
    for_rows: tuple[dict[str, object], ...],
) -> tuple[dict[str, object], ...]:
    rows = [
        _summary("trade_away_rows", len(away_rows), str(PRESSURE_ROWS)),
        _summary("external_asset_rows", len(for_rows), str(ASSET_ROWS)),
        _summary("trade_for_rows_legacy_alias", len(for_rows), str(ASSET_ROWS)),
        _summary("trade_recommendations_created", False, "sprint_14c_guardrail"),
        _summary("trade_packages_created", False, "sprint_14c_guardrail"),
    ]
    rows.extend(
        _summary(
            f"trade_away_band_count:{band}",
            sum(1 for row in away_rows if row["trade_away_review_band"] == band),
            str(DEFAULT_OUTPUT_ROOT),
        )
        for band in sorted({str(row["trade_away_review_band"]) for row in away_rows})
    )
    rows.extend(
        _summary(
            f"trade_for_band_count:{band}",
            sum(1 for row in for_rows if row["external_asset_review_band"] == band),
            str(DEFAULT_OUTPUT_ROOT),
        )
        for band in sorted({str(row["external_asset_review_band"]) for row in for_rows})
    )
    return tuple(rows)


def _summary(key: str, value: object, source: str) -> dict[str, object]:
    return {
        "summary_key": key,
        "summary_value": value,
        "source": source,
        "allowed_use": "review_only_trade_context_summary",
        "formula_version": SPRINT_14C_VERSION,
    }


def _doc(result: TradeReviewResult, paths: TradeReviewPaths) -> str:
    return "\n".join(
        [
            "# Sprint 14C External Asset Reviews",
            "",
            "Sprint 14C creates review-only roster pressure and external asset context "
            "surfaces. It does not create trade offers, sell calls, buy calls, "
            "acquisition calls, or package recommendations.",
            "",
            "## Outputs",
            "",
            f"- `{paths.trade_away_rows}`",
            f"- `{paths.external_asset_rows}`",
            f"- `{paths.components}`",
            f"- `{paths.receipts}`",
            f"- `{paths.warnings}`",
            f"- `{paths.summary}`",
            "",
            "## Summary",
            "",
            f"- Trade-away review rows: {result.summary['trade_away_rows']}",
            f"- External asset context rows: {result.summary['external_asset_rows']}",
            "- Trade recommendations created: False",
            "- Trade packages created: False",
        ]
    ) + "\n"


def _audit_prompt(paths: TradeReviewPaths) -> str:
    return "\n".join(
        [
            "# Sprint 14C External Asset Reviews Audit Prompt",
            "",
            "Audit Sprint 14C for Model v4. The attached outputs are review-only.",
            "",
            "Verify:",
            "- roster pressure rows are context, not sell recommendations",
            "- external asset rows are context, not buy/acquisition recommendations",
            "- no trade package or offer logic was created",
            "- owner/team context is descriptive only",
            "- market/ADP/projection/ranking context does not drive private football value",
            "- candidate bands are reasonable given 14B pressure and Sprint 12/13 asset value",
            "- whether Sprint 14D pick trade/defer logic can begin review-only",
            "",
            "Verdict options:",
            "- ready_for_sprint_14d_review_only_pick_trade_defer_work",
            "- needs_trade_context_repair",
            "- needs_pressure_repair",
            "- needs_source_or_identity_repair",
            "",
            "Primary files:",
            f"- `{paths.trade_away_rows}`",
            f"- `{paths.external_asset_rows}`",
            f"- `{paths.components}`",
            f"- `{paths.warnings}`",
        ]
    ) + "\n"


def _write_packet(paths: TradeReviewPaths, packet_path: Path) -> None:
    files = (
        paths.trade_away_rows,
        paths.external_asset_rows,
        paths.components,
        paths.receipts,
        paths.warnings,
        paths.summary,
        paths.doc,
        paths.audit_prompt,
        PRESSURE_ROWS,
        PRESSURE_COMPONENTS,
        PRESSURE_RECEIPTS,
        ASSET_ROWS,
    )
    packet_path.parent.mkdir(parents=True, exist_ok=True)
    if packet_path.exists():
        packet_path.unlink()
    manifest = packet_path.with_suffix(".manifest.json")
    manifest.write_text(
        "{\n"
        f'  "created_at_utc": "{datetime.now(UTC).isoformat()}",\n'
        '  "packet_type": "model_v4_sprint14c_external_asset_reviews_audit",\n'
        '  "review_only": true\n'
        "}\n",
        encoding="utf-8",
    )
    with zipfile.ZipFile(packet_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in (*files, manifest):
            if path.exists():
                archive.write(path, path.as_posix())


def _owner_by_name(rows: tuple[dict[str, str], ...]) -> dict[str, str]:
    return {
        _normalize_name(row.get("player_name", "")): row.get("team_name", "")
        for row in rows
        if row.get("player_name")
    }


def _position_counts(rows: tuple[dict[str, str], ...]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        counts[row["position"]] = counts.get(row["position"], 0) + 1
    return counts


def _read_rows(path: Path) -> tuple[dict[str, str], ...]:
    with path.open(newline="", encoding="utf-8") as handle:
        return tuple(csv.DictReader(handle))


def _write_csv(path: Path, header: tuple[str, ...], rows: tuple[dict[str, object], ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    ordered = _sort_rows(rows, header)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=header, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(ordered)


def _sort_rows(
    rows: tuple[dict[str, object], ...],
    header: tuple[str, ...],
) -> tuple[dict[str, object], ...]:
    if header == TRADE_AWAY_HEADER:
        return tuple(
            sorted(
                rows,
                key=lambda row: _float(row.get("pressure_score"), 0.0) or 0.0,
                reverse=True,
            )
        )
    if header == TRADE_FOR_HEADER:
        return tuple(
            sorted(
                rows,
                key=lambda row: _float(row.get("dynasty_asset_value_review_score"), 0.0) or 0.0,
                reverse=True,
            )
        )
    return rows


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _normalize_name(value: str) -> str:
    normalized = value.lower().replace("&", "and")
    normalized = re.sub(r"\b(jr|sr|ii|iii|iv)\b", "", normalized)
    return re.sub(r"[^a-z0-9]+", "", normalized)


def _float(value: object, default: float | None = None) -> float | None:
    if value in (None, ""):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _join_flags(*values: object) -> str:
    flags: list[str] = []
    for value in values:
        flags.extend(flag for flag in str(value or "").split("|") if flag)
    return "|".join(dict.fromkeys(flags))
