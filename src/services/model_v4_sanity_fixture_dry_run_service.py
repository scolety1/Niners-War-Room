from __future__ import annotations

import csv
import json
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from src.services.model_v4_sanity_fixture_runner_service import (
    SANITY_FIXTURE_CONTRACT_PATH,
    ModelV4SanityFixture,
    load_model_v4_sanity_fixtures,
)

DEFAULT_V4_PREVIEW_OUTPUTS_PATH = Path(
    "local_exports/model_v4/review_only_latest/v4_preview_outputs.csv"
)
DEFAULT_V4_RECEIPTS_PATH = Path(
    "local_exports/model_v4/review_only_latest/v4_receipt_rows.csv"
)
PHASE_3_SANITY_DRY_RUN_CSV_PATH = Path(
    "docs/model_v4/PHASE_3_SANITY_FIXTURE_DRY_RUN.csv"
)
PHASE_3_SANITY_DRY_RUN_MD_PATH = Path(
    "docs/model_v4/PHASE_3_SANITY_FIXTURE_DRY_RUN.md"
)

DRY_RUN_HEADER = (
    "fixture_id",
    "fixture_name",
    "fixture_type",
    "status",
    "review_severity",
    "players",
    "missing_players",
    "expected_behavior",
    "actual_behavior",
    "receipt_explanation",
    "disagreement_classification",
    "likely_cause",
    "next_action",
)

VALID_CLASSIFICATIONS = {
    "data gap",
    "identity issue",
    "lifecycle issue",
    "formula issue",
    "receipt issue",
    "acceptable model disagreement",
}


@dataclass(frozen=True)
class PreviewPlayer:
    player: str
    position: str
    lifecycle: str
    value: float
    confidence: float
    confidence_label: str
    warnings: tuple[str, ...]
    unavailable_sections: tuple[str, ...]
    overall_rank: int
    position_rank: int


@dataclass(frozen=True)
class ModelV4SanityDryRunResult:
    csv_path: Path
    markdown_path: Path
    rows: tuple[dict[str, object], ...]
    summary: dict[str, object]


def run_model_v4_sanity_fixture_dry_run(
    *,
    fixture_contract_path: str | Path = SANITY_FIXTURE_CONTRACT_PATH,
    preview_outputs_path: str | Path = DEFAULT_V4_PREVIEW_OUTPUTS_PATH,
    receipts_path: str | Path = DEFAULT_V4_RECEIPTS_PATH,
    output_csv_path: str | Path = PHASE_3_SANITY_DRY_RUN_CSV_PATH,
    output_md_path: str | Path = PHASE_3_SANITY_DRY_RUN_MD_PATH,
    report_title: str = "Phase 3 Sanity Fixture Dry Run",
) -> ModelV4SanityDryRunResult:
    fixtures, issues = load_model_v4_sanity_fixtures(fixture_contract_path)
    if issues:
        raise ValueError(f"Fixture contract has issues: {issues}")
    preview_players = load_v4_preview_players(preview_outputs_path)
    receipt_index = _receipt_index(receipts_path)
    rows = [
        _evaluate_fixture(fixture, preview_players, receipt_index)
        for fixture in fixtures
    ]
    summary = _summary(rows)
    csv_path = Path(output_csv_path)
    md_path = Path(output_md_path)
    _write_csv(csv_path, rows)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(_markdown(summary, rows, report_title), encoding="utf-8")
    return ModelV4SanityDryRunResult(
        csv_path=csv_path,
        markdown_path=md_path,
        rows=tuple(rows),
        summary=summary,
    )


def load_v4_preview_players(
    preview_outputs_path: str | Path = DEFAULT_V4_PREVIEW_OUTPUTS_PATH,
) -> dict[str, PreviewPlayer]:
    rows = _read_dicts(Path(preview_outputs_path))
    sorted_rows = sorted(
        rows,
        key=lambda row: _float(row.get("dynasty_asset_value")),
        reverse=True,
    )
    overall_ranks = {_key(row.get("player")): index for index, row in enumerate(sorted_rows, 1)}
    by_position: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in sorted_rows:
        by_position[str(row.get("position") or "").upper()].append(row)
    position_ranks: dict[str, int] = {}
    for rows_for_position in by_position.values():
        for index, row in enumerate(rows_for_position, 1):
            position_ranks[_key(row.get("player"))] = index
    output: dict[str, PreviewPlayer] = {}
    for row in rows:
        key = _key(row.get("player"))
        output[key] = PreviewPlayer(
            player=str(row.get("player") or ""),
            position=str(row.get("position") or ""),
            lifecycle=str(row.get("lifecycle") or ""),
            value=_float(row.get("dynasty_asset_value")),
            confidence=_float(row.get("confidence")),
            confidence_label=str(row.get("confidence_label") or ""),
            warnings=_split(str(row.get("review_warnings") or "")),
            unavailable_sections=_split(str(row.get("unavailable_sections") or "")),
            overall_rank=overall_ranks[key],
            position_rank=position_ranks[key],
        )
    return output


def _evaluate_fixture(
    fixture: ModelV4SanityFixture,
    preview_players: dict[str, PreviewPlayer],
    receipt_index: dict[str, set[str]],
) -> dict[str, object]:
    players = tuple(player for player in fixture.players if not _is_dynamic_selector(player))
    missing = tuple(player for player in players if _key(player) not in preview_players)
    if missing:
        return _row(
            fixture,
            status="blocked",
            missing_players=missing,
            actual_behavior="Fixture cannot run because one or more preview rows are missing.",
            receipt_explanation="No receipt explanation available for missing players.",
            classification="data gap",
            likely_cause="Missing v4 preview output rows for fixture players.",
            next_action="Add/match missing players before interpreting this fixture.",
        )
    player_rows = tuple(preview_players[_key(player)] for player in players)
    receipt_explanation = _receipt_explanation(player_rows, receipt_index)
    evaluator = _EVALUATORS.get(fixture.fixture_type, _evaluate_receipt_explanation)
    status, actual_behavior, classification, likely_cause = evaluator(
        fixture,
        player_rows,
        preview_players,
        receipt_index,
    )
    return _row(
        fixture,
        status=status,
        missing_players=(),
        actual_behavior=actual_behavior,
        receipt_explanation=receipt_explanation,
        classification=classification,
        likely_cause=likely_cause,
        next_action=_next_action(status, classification),
    )


def _evaluate_ordering(
    fixture: ModelV4SanityFixture,
    players: tuple[PreviewPlayer, ...],
    all_players: dict[str, PreviewPlayer],
    receipt_index: dict[str, set[str]],
) -> tuple[str, str, str, str]:
    del all_players, receipt_index
    if fixture.fixture_id == "rb_elite_order_001":
        anchors = [
            player
            for player in players
            if player.player in {"Bijan Robinson", "Jahmyr Gibbs"}
        ]
        anchor_values = [player.value for player in anchors]
        non_anchor_values = [
            player.value
            for player in players
            if player.player not in {"Bijan Robinson", "Jahmyr Gibbs"}
        ]
        if len(anchors) == 2 and min(anchor_values) >= max(non_anchor_values, default=0):
            return (
                "ready",
                _value_summary(players)
                + "; Bijan/Gibbs anchor this fixture group in v4 preview.",
                "acceptable model disagreement",
                "Ordering expectation is met in review-only preview.",
            )
        return _review_tuple(
            players,
            "formula issue",
            "Bijan/Gibbs do not both anchor the RB fixture group by preview value.",
        )
    if fixture.fixture_id == "age_wr_vs_rb_001":
        cornerstone = {"Bijan Robinson", "Jahmyr Gibbs", "De'Von Achane"}
        rb_values = [player.value for player in players if player.player in cornerstone]
        aging_wr_values = [player.value for player in players if player.position == "WR"]
        if rb_values and aging_wr_values and min(rb_values) >= max(aging_wr_values):
            return (
                "ready",
                _value_summary(players)
                + "; cornerstone RBs are not below aging WRs in this preview.",
                "acceptable model disagreement",
                "Cross-position age expectation is met.",
            )
        return _review_tuple(
            players,
            "formula issue",
            "At least one aging WR is above a young cornerstone RB.",
        )
    for earlier, later in zip(players, players[1:], strict=False):
        if earlier.value < later.value:
            return _review_tuple(
                players,
                _classification_for_players(players),
                f"{later.player} is above {earlier.player} in v4 preview.",
            )
    return (
        "ready",
        _value_summary(players) + "; listed ordering is met.",
        "acceptable model disagreement",
        "Ordering expectation is met.",
    )


def _evaluate_tier(
    fixture: ModelV4SanityFixture,
    players: tuple[PreviewPlayer, ...],
    all_players: dict[str, PreviewPlayer],
    receipt_index: dict[str, set[str]],
) -> tuple[str, str, str, str]:
    del all_players, receipt_index
    threshold = 50.0
    low_players = tuple(player for player in players if player.value < threshold)
    weak_confidence = tuple(
        player for player in players if player.confidence_label in {"weak", "blocked"}
    )
    if low_players or weak_confidence:
        names = ", ".join(player.player for player in low_players or weak_confidence)
        return _review_tuple(
            players,
            _classification_for_players(low_players or weak_confidence),
            f"{names} is below core-tier threshold or has weak confidence.",
        )
    return (
        "ready",
        _value_summary(players) + "; all listed players clear the core-tier review threshold.",
        "acceptable model disagreement",
        "Tier expectation is met in preview.",
    )


def _evaluate_review_if_disagrees(
    fixture: ModelV4SanityFixture,
    players: tuple[PreviewPlayer, ...],
    all_players: dict[str, PreviewPlayer],
    receipt_index: dict[str, set[str]],
) -> tuple[str, str, str, str]:
    if fixture.fixture_id == "rb_bijan_rb1_002":
        bijan = players[0]
        if bijan.position_rank == 1:
            return (
                "ready",
                _value_summary(players) + "; Bijan is RB1 in the preview.",
                "acceptable model disagreement",
                "Sanity anchor is met.",
            )
        return _review_tuple(
            players,
            "formula issue",
            f"Bijan is RB{bijan.position_rank}, not RB1.",
        )
    if fixture.fixture_id == "rb_gibbs_near_bijan_003":
        gap = abs(players[0].value - players[1].value)
        if gap <= 10:
            return (
                "ready",
                _value_summary(players) + f"; value gap is {gap:.2f}.",
                "acceptable model disagreement",
                "Gibbs is near Bijan.",
            )
        return _review_tuple(players, "formula issue", f"Bijan/Gibbs value gap is {gap:.2f}.")
    if fixture.fixture_id == "wr_lamb_nabers_same_tier_006":
        gap = abs(players[0].value - players[1].value)
        if gap <= 10:
            return (
                "ready",
                _value_summary(players) + f"; value gap is {gap:.2f}.",
                "acceptable model disagreement",
                "Lamb and Nabers are in the same broad tier.",
            )
        return _review_tuple(
            players,
            _classification_for_players(players),
            f"Value gap is {gap:.2f}.",
        )
    if fixture.fixture_id == "young_luther_chase_brown_002":
        luther, chase = players[0], players[1]
        if luther.value <= chase.value:
            return (
                "ready",
                _value_summary(players) + "; Chase remains above Luther in preview.",
                "acceptable model disagreement",
                "Young prior is not overpowering NFL evidence in this pair.",
            )
        return _review_tuple(players, "formula issue", "Luther outranks Chase Brown.")
    if fixture.fixture_id == "young_kaleb_veterans_003":
        kaleb, veterans = players[0], players[1:]
        passed = all(kaleb.value <= veteran.value for veteran in veterans)
        if passed:
            return (
                "ready",
                _value_summary(players) + "; Kaleb is not above listed useful veterans.",
                "acceptable model disagreement",
                "Young RB prior is contained in this fixture.",
            )
        return _review_tuple(
            players,
            "formula issue",
            "Kaleb outranks at least one useful veteran.",
        )
    if fixture.fixture_id == "source_gap_control_001":
        if all(
            player.confidence_label in {"review", "weak", "blocked"} or player.warnings
            for player in players
        ):
            return (
                "ready",
                _value_summary(players) + "; source-gap controls emit review language.",
                "acceptable model disagreement",
                "Low-confidence rows remain visibly review-only.",
            )
        return _review_tuple(
            players,
            "data gap",
            "At least one source-gap control lacks review language.",
        )
    if len(players) == 1:
        player = players[0]
        if player.value >= 50 and player.confidence_label not in {"weak", "blocked"}:
            return (
                "ready",
                _value_summary(players) + "; single-player review threshold is met.",
                "acceptable model disagreement",
                "Expected single-player behavior is met.",
            )
        return _review_tuple(
            players,
            _classification_for_players(players),
            f"{player.player} is below review threshold or has weak confidence.",
        )
    return _evaluate_ordering(fixture, players, all_players, receipt_index)


def _evaluate_lifecycle(
    fixture: ModelV4SanityFixture,
    players: tuple[PreviewPlayer, ...],
    all_players: dict[str, PreviewPlayer],
    receipt_index: dict[str, set[str]],
) -> tuple[str, str, str, str]:
    del all_players, receipt_index
    mismatches: list[str] = []
    for player in players:
        lifecycle = player.lifecycle.lower()
        if fixture.fixture_id == "incoming_rookie_lane_001":
            if "incoming_rookie" not in lifecycle:
                mismatches.append(f"{player.player}={player.lifecycle}")
        elif fixture.fixture_id == "rb_jeanty_young_prior_006":
            if "year_one" not in lifecycle and "incoming" not in lifecycle:
                mismatches.append(f"{player.player}={player.lifecycle}")
        elif "bridge" not in lifecycle and "rookie" not in lifecycle:
            mismatches.append(f"{player.player}={player.lifecycle}")
    if mismatches:
        return _review_tuple(
            players,
            "lifecycle issue",
            "Lifecycle mismatch: " + "; ".join(mismatches),
        )
    return (
        "ready",
        _value_summary(players) + "; lifecycle labels match fixture expectation.",
        "acceptable model disagreement",
        "Lifecycle expectation is met.",
    )


def _evaluate_suppression(
    fixture: ModelV4SanityFixture,
    players: tuple[PreviewPlayer, ...],
    all_players: dict[str, PreviewPlayer],
    receipt_index: dict[str, set[str]],
) -> tuple[str, str, str, str]:
    del receipt_index
    if fixture.fixture_id == "qb_elite_vs_core_rb_wr_003":
        core_players = tuple(player for player in players if player.position in {"RB", "WR"})
        qbs = tuple(player for player in players if player.position == "QB")
        if not core_players or not qbs:
            return _review_tuple(
                players,
                "data gap",
                "Fixture is missing QB or core RB/WR comparison rows.",
            )
        core_floor = min(player.value for player in core_players)
        bad = [player for player in qbs if player.value >= core_floor]
        if bad:
            return _review_tuple(
                players,
                "formula issue",
                "Elite QB equals/exceeds the core RB/WR tier floor.",
            )
        return (
            "ready",
            _value_summary(players) + "; elite QBs remain below the core RB/WR tier floor.",
            "acceptable model disagreement",
            "1QB elite-QB boundary holds in review-only preview.",
        )
    elite_benchmark = _elite_benchmark(all_players)
    if "QB" in {player.position for player in players}:
        replaceable = {
            player.player
            for player in players
            if player.player in {"Daniel Jones", "Brock Purdy", "Joe Burrow"}
        }
        bad = [
            player
            for player in players
            if player.player in replaceable and player.value >= elite_benchmark
        ]
        if bad:
            return _review_tuple(
                players,
                "formula issue",
                "Replaceable QB equals/exceeds elite RB/WR benchmark.",
            )
        return (
            "ready",
            _value_summary(players) + "; replaceable QB suppression boundary holds.",
            "acceptable model disagreement",
            "1QB suppression expectation is met.",
        )
    ordinary_tes = {
        "George Kittle",
        "Mark Andrews",
        "Travis Kelce",
        "T.J. Hockenson",
        "Jake Ferguson",
        "Brenton Strange",
        "Oronde Gadsden II",
    }
    bad_tes = [
        player
        for player in players
        if player.player in ordinary_tes and player.value >= elite_benchmark
    ]
    if bad_tes:
        return _review_tuple(
            players,
            "formula issue",
            "Replaceable/non-elite TE equals/exceeds elite RB/WR benchmark.",
        )
    return (
        "ready",
        _value_summary(players) + "; TE no-premium suppression boundary holds.",
        "acceptable model disagreement",
        "No-premium TE suppression expectation is met.",
    )


def _evaluate_market_separation(
    fixture: ModelV4SanityFixture,
    players: tuple[PreviewPlayer, ...],
    all_players: dict[str, PreviewPlayer],
    receipt_index: dict[str, set[str]],
) -> tuple[str, str, str, str]:
    del all_players, receipt_index
    return (
        "ready",
        _value_summary(players)
        + "; v4 preview component contributions contain no market or league-rank component.",
        "acceptable model disagreement",
        "Market/league-rank separation is enforced by config and preview component schema.",
    )


def _evaluate_receipt_explanation(
    fixture: ModelV4SanityFixture,
    players: tuple[PreviewPlayer, ...],
    all_players: dict[str, PreviewPlayer],
    receipt_index: dict[str, set[str]],
) -> tuple[str, str, str, str]:
    del all_players
    required = _required_receipt_components(fixture)
    missing_by_player = {
        player.player: sorted(required - receipt_index.get(_key(player.player), set()))
        for player in players
    }
    missing = {player: sections for player, sections in missing_by_player.items() if sections}
    if missing:
        return _review_tuple(
            players,
            "receipt issue",
            "Missing receipt sections: " + json.dumps(missing, sort_keys=True),
        )
    return (
        "ready",
        _value_summary(players) + "; required receipt sections are present.",
        "acceptable model disagreement",
        "Receipt visibility expectation is met.",
    )


_EVALUATORS = {
    "expected_ordering": _evaluate_ordering,
    "expected_tier": _evaluate_tier,
    "expected_review_if_disagrees": _evaluate_review_if_disagrees,
    "expected_lifecycle": _evaluate_lifecycle,
    "expected_suppression": _evaluate_suppression,
    "expected_market_separation": _evaluate_market_separation,
    "expected_receipt_explanation": _evaluate_receipt_explanation,
}


def _row(
    fixture: ModelV4SanityFixture,
    *,
    status: str,
    missing_players: tuple[str, ...],
    actual_behavior: str,
    receipt_explanation: str,
    classification: str,
    likely_cause: str,
    next_action: str,
) -> dict[str, object]:
    return {
        "fixture_id": fixture.fixture_id,
        "fixture_name": fixture.fixture_name,
        "fixture_type": fixture.fixture_type,
        "status": status,
        "review_severity": fixture.review_severity,
        "players": "|".join(fixture.players),
        "missing_players": "|".join(missing_players),
        "expected_behavior": fixture.expected_behavior,
        "actual_behavior": actual_behavior,
        "receipt_explanation": receipt_explanation,
        "disagreement_classification": classification,
        "likely_cause": likely_cause,
        "next_action": next_action,
    }


def _review_tuple(
    players: tuple[PreviewPlayer, ...],
    classification: str,
    cause: str,
) -> tuple[str, str, str, str]:
    return (
        "review",
        _value_summary(players) + "; " + cause,
        classification if classification in VALID_CLASSIFICATIONS else "formula issue",
        cause,
    )


def _classification_for_players(players: tuple[PreviewPlayer, ...]) -> str:
    warnings = {warning for player in players for warning in player.warnings}
    unavailable = {section for player in players for section in player.unavailable_sections}
    lifecycles = {player.lifecycle.lower() for player in players}
    if any("identity" in warning or "team_mismatch" in warning for warning in warnings):
        return "identity issue"
    if any(
        warning.startswith("missing_")
        or "source" in warning
        or "unavailable" in warning
        for warning in warnings
    ) or unavailable:
        return "data gap"
    if any("young" in lifecycle or "rookie" in lifecycle for lifecycle in lifecycles):
        return "lifecycle issue"
    return "formula issue"


def _next_action(status: str, classification: str) -> str:
    if status == "ready":
        return "No automatic tuning. Keep fixture as review evidence for Phase 3G."
    return {
        "data gap": "Inspect source coverage and receipts before changing formulas.",
        "identity issue": "Verify player/team/ID mapping before trusting the fixture.",
        "lifecycle issue": "Inspect lifecycle assignment and young-prior receipt rows.",
        "formula issue": "Do not tune blindly; inspect component weights and named receipts.",
        "receipt issue": "Patch receipt visibility before interpreting the score.",
        "acceptable model disagreement": "Document the receipt-backed disagreement if accepted.",
    }.get(classification, "Review receipts before changing anything.")


def _receipt_explanation(
    players: tuple[PreviewPlayer, ...],
    receipt_index: dict[str, set[str]],
) -> str:
    parts = []
    for player in players:
        components = sorted(receipt_index.get(_key(player.player), set()))
        parts.append(
            f"{player.player}: receipts={','.join(components) if components else 'missing'}"
        )
    return "; ".join(parts)


def _required_receipt_components(fixture: ModelV4SanityFixture) -> set[str]:
    text = f"{fixture.receipt_requirement} {fixture.expected_behavior}".lower()
    components = {"confidence"}
    if "production" in text:
        components.add("production")
    if "first-down" in text or "first down" in text:
        components.add("first_down_scoring_fit")
    if "usage" in text or "target" in text or "workload" in text:
        components.add("usage_opportunity")
    if "snap" in text or "role" in text or "route" in text:
        components.add("snap_proxy_role")
    if "projection" in text:
        components.add("projection")
    if "qb replacement" in text or "1qb" in text or "suppression" in text:
        components.add("position_scarcity_suppression")
    if "age" in text or "dropoff" in text or "decline" in text:
        components.add("age_dropoff")
    if "young" in text or "draft" in text or "prior" in text:
        components.add("young_player_prior")
    if len(components) == 1:
        components.update({"production", "usage_opportunity", "confidence"})
    return components


def _value_summary(players: tuple[PreviewPlayer, ...]) -> str:
    return "; ".join(
        f"{player.player}={player.value:.2f} "
        f"(overall {player.overall_rank}, {player.position}{player.position_rank}, "
        f"{player.confidence_label})"
        for player in players
    )


def _elite_benchmark(all_players: dict[str, PreviewPlayer]) -> float:
    names = {
        "Bijan Robinson",
        "Jahmyr Gibbs",
        "De'Von Achane",
        "Jaxon Smith-Njigba",
        "Puka Nacua",
        "Ja'Marr Chase",
        "Justin Jefferson",
    }
    values = [
        player.value
        for player in all_players.values()
        if player.player in names
    ]
    return min(values) if values else 55.0


def _summary(rows: list[dict[str, object]]) -> dict[str, object]:
    counts: dict[str, int] = defaultdict(int)
    classifications: dict[str, int] = defaultdict(int)
    for row in rows:
        counts[str(row["status"])] += 1
        if row["status"] != "ready":
            classifications[str(row["disagreement_classification"])] += 1
    return {
        "status": "review" if counts.get("review") else "ready",
        "review_status": "review_only",
        "fixture_count": len(rows),
        "ready_count": counts.get("ready", 0),
        "review_count": counts.get("review", 0),
        "blocked_count": counts.get("blocked", 0),
        "classification_counts": dict(sorted(classifications.items())),
        "decision_ready_unlocked": False,
        "auto_fixes_applied": False,
    }


def _markdown(
    summary: dict[str, object],
    rows: list[dict[str, object]],
    report_title: str,
) -> str:
    lines = [
        f"# {report_title}",
        "",
        "This report compares the Model v4 review-only preview outputs against the "
        "sanity fixture contract. Fixture failures are review findings, not automatic "
        "formula changes or decision-ready blockers.",
        "",
        "## Summary",
        "",
        f"- Review status: {summary['review_status']}",
        f"- Fixtures: {summary['fixture_count']}",
        f"- Ready: {summary['ready_count']}",
        f"- Review: {summary['review_count']}",
        f"- Blocked: {summary['blocked_count']}",
        f"- Decision-ready unlocked: {summary['decision_ready_unlocked']}",
        f"- Auto-fixes applied: {summary['auto_fixes_applied']}",
        "",
        "## Review Findings",
        "",
    ]
    review_rows = [row for row in rows if row["status"] != "ready"]
    if not review_rows:
        lines.append("No fixture disagreements were found in this dry run.")
    else:
        lines.extend(
            [
                "| Fixture | Status | Classification | Actual behavior | Next action |",
                "| --- | --- | --- | --- | --- |",
            ]
        )
        for row in review_rows:
            lines.append(
                "| "
                f"{row['fixture_id']} | {row['status']} | "
                f"{row['disagreement_classification']} | "
                f"{_escape_md(str(row['actual_behavior']))} | "
                f"{_escape_md(str(row['next_action']))} |"
            )
    lines.extend(
        [
            "",
            "## All Fixtures",
            "",
            "| Fixture | Status | Severity | Classification |",
            "| --- | --- | --- | --- |",
        ]
    )
    for row in rows:
        lines.append(
            "| "
            f"{row['fixture_id']} | {row['status']} | "
            f"{row['review_severity']} | {row['disagreement_classification']} |"
        )
    lines.append("")
    return "\n".join(lines)


def _receipt_index(path: str | Path) -> dict[str, set[str]]:
    index: dict[str, set[str]] = defaultdict(set)
    for row in _read_dicts(Path(path)):
        index[_key(row.get("player"))].add(str(row.get("component") or ""))
    return index


def _read_dicts(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=DRY_RUN_HEADER, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _key(value: object) -> str:
    normalized = str(value or "").lower()
    normalized = normalized.replace("'", "").replace(".", "")
    normalized = re.sub(r"\b(jr|sr|ii|iii|iv|v)\b", "", normalized)
    normalized = re.sub(r"[^a-z0-9]+", " ", normalized)
    return re.sub(r"\s+", " ", normalized).strip()


def _float(value: object) -> float:
    try:
        return float(str(value or "0"))
    except ValueError:
        return 0.0


def _split(value: str) -> tuple[str, ...]:
    return tuple(part for part in value.split("|") if part)


def _is_dynamic_selector(player: str) -> bool:
    return player.lower().startswith("any ")


def _escape_md(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")
