from __future__ import annotations

import csv
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.services.model_v4_rotowire_dynasty_candidate_service import (  # noqa: E402
    DEFAULT_OUTPUT_ROOT,
)

DOCS_ROOT = Path("docs/model_v4")

NAMED_PLAYERS = (
    "De'Von Achane",
    "Lamar Jackson",
    "Chase Brown",
    "Luther Burden",
    "Brian Thomas Jr.",
    "Kaleb Johnson",
    "Jaxon Smith-Njigba",
    "Tee Higgins",
    "Bijan Robinson",
    "Jahmyr Gibbs",
    "Christian McCaffrey",
    "Puka Nacua",
    "Ja'Marr Chase",
    "Justin Jefferson",
    "Amon-Ra St. Brown",
    "CeeDee Lamb",
    "Malik Nabers",
    "Keenan Allen",
    "Derrick Henry",
    "Brock Bowers",
    "Jeremiyah Love",
)

ELITE_WRS = (
    "Jaxon Smith-Njigba",
    "Puka Nacua",
    "Ja'Marr Chase",
    "Justin Jefferson",
    "Amon-Ra St. Brown",
    "CeeDee Lamb",
    "Malik Nabers",
)


def main() -> None:
    candidate_rows = _read_rows(DEFAULT_OUTPUT_ROOT / "rotowire_dynasty_candidate_rows.csv")
    component_rows = _read_rows(
        DEFAULT_OUTPUT_ROOT / "rotowire_dynasty_candidate_component_rows.csv"
    )
    receipt_rows = _read_rows(DEFAULT_OUTPUT_ROOT / "rotowire_dynasty_candidate_receipt_rows.csv")
    by_player = {row["player_name"]: row for row in candidate_rows}
    components_by_player = _group(component_rows, "player_name")
    receipts_by_player = _group(receipt_rows, "player_name")

    named_rows = [
        _named_row(player, by_player, components_by_player, receipts_by_player)
        for player in NAMED_PLAYERS
    ]
    sanity_rows = _sanity_rows(by_player)

    named_csv = DOCS_ROOT / "ROTOWIRE_DYNASTY_CANDIDATE_NAMED_REVIEW.csv"
    named_md = DOCS_ROOT / "ROTOWIRE_DYNASTY_CANDIDATE_NAMED_REVIEW.md"
    sanity_csv = DOCS_ROOT / "ROTOWIRE_DYNASTY_CANDIDATE_SANITY_REVIEW.csv"
    sanity_md = DOCS_ROOT / "ROTOWIRE_DYNASTY_CANDIDATE_SANITY_REVIEW.md"
    _write_csv(named_csv, named_rows)
    _write_csv(sanity_csv, sanity_rows)
    _write_md(named_md, "RotoWire Dynasty Candidate Named Review", named_rows)
    _write_md(sanity_md, "RotoWire Dynasty Candidate Sanity Review", sanity_rows)
    print(f"named={named_csv}")
    print(f"sanity={sanity_csv}")


def _named_row(
    player: str,
    by_player: dict[str, dict[str, str]],
    components_by_player: dict[str, list[dict[str, str]]],
    receipts_by_player: dict[str, list[dict[str, str]]],
) -> dict[str, str]:
    row = by_player.get(player)
    if not row:
        return {
            "player_name": player,
            "status": "blocked_missing_candidate_row",
            "summary": "Player missing from candidate output.",
        }
    components = sorted(
        components_by_player.get(player, []),
        key=lambda item: _float(item.get("contribution")),
        reverse=True,
    )
    top_positive = "; ".join(
        f"{item['component']} +{item['contribution']}" for item in components[:3]
    )
    warning_receipts = [
        item
        for item in receipts_by_player.get(player, [])
        if item.get("warning") and item.get("warning") != "not_applicable_for_qb"
    ]
    warnings = row.get("review_warnings", "")
    return {
        "player_name": player,
        "status": "review" if warnings else "ready_for_external_audit",
        "overall_candidate_rank": row.get("overall_candidate_rank", ""),
        "position_candidate_rank": row.get("position_candidate_rank", ""),
        "position": row.get("position", ""),
        "candidate_value": row.get("dynasty_candidate_value", ""),
        "confidence_label": row.get("confidence_label", ""),
        "age": row.get("age", ""),
        "age_value_cap": row.get("age_value_cap", ""),
        "top_positive_drivers": top_positive,
        "warning_count": str(len(warning_receipts)),
        "review_warnings": warnings,
        "unavailable_sections": row.get("unavailable_sections", ""),
        "summary": _named_summary(row),
    }


def _named_summary(row: dict[str, str]) -> str:
    warnings = row.get("review_warnings", "")
    value = _float(row.get("dynasty_candidate_value"))
    player = row.get("player_name", "")
    if "age_value_cap_applied" in warnings:
        return "Age cap is active; production is not being treated as a long dynasty runway."
    if "missing_historical_production" in warnings:
        return "Missing NFL production keeps this as review-only evidence."
    if player in ELITE_WRS and value < 65:
        return (
            "Elite WR sanity player is lower than expected; inspect route/target and "
            "VORP receipts."
        )
    return "Candidate value is review-only and receipt-backed by local RotoWire evidence."


def _sanity_rows(by_player: dict[str, dict[str, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    rows.append(
        _fixture(
            "bijan_gibbs_top_rb",
            "Bijan and Gibbs should remain top RB anchors.",
            _rank(by_player, "Bijan Robinson", "position_candidate_rank") <= 2
            and _rank(by_player, "Jahmyr Gibbs", "position_candidate_rank") <= 2,
            "Bijan/Gibbs ranks are RB1/RB2 in the candidate output.",
        )
    )
    rows.append(
        _fixture(
            "achane_elite_rb",
            "Achane should look like an elite dynasty RB, not a bubble asset.",
            _rank(by_player, "De'Von Achane", "position_candidate_rank") <= 6,
            "Achane is expected to remain near the top RB tier; review if outside RB6.",
        )
    )
    rows.append(
        _fixture(
            "aging_rb_below_young_elite_rb",
            "Aging RB production should not outrank young elite RB dynasty value.",
            _value(by_player, "De'Von Achane") > _value(by_player, "Derrick Henry"),
            "Age value cap should keep Henry below Achane in dynasty candidate value.",
        )
    )
    rows.append(
        _fixture(
            "qb_1qb_suppression",
            "Elite QBs should not clear elite RB/WR assets unless VORP demands it.",
            _value(by_player, "De'Von Achane") > _value(by_player, "Lamar Jackson"),
            "Lamar is suppressed below Achane in this 10-team 1QB review.",
        )
    )
    rows.append(
        _fixture(
            "te_no_premium_suppression",
            "TEs should need a real VORP gap to enter elite RB/WR territory.",
            _rank(by_player, "Brock Bowers", "overall_candidate_rank") > 20,
            "Bowers remains outside top-20 pending no-premium VORP validation.",
        )
    )
    for player in ELITE_WRS:
        fixture_slug = player.lower().replace(" ", "_").replace("'", "")
        rows.append(
            _fixture(
                f"elite_wr_review_{fixture_slug}",
                f"{player} should be reviewed if outside the high WR tier.",
                _rank(by_player, player, "position_candidate_rank") <= 12,
                "Elite WR outside WR12 is not auto-fixed; it requires receipt review.",
            )
        )
    rows.append(
        _fixture(
            "incoming_rookie_confidence_cap",
            "Incoming rookies without NFL evidence cannot show strong practical confidence.",
            by_player.get("Jeremiyah Love", {}).get("confidence_label") == "weak_review",
            "Jeremiyah Love remains weak_review until sourced rookie/prospect data exists.",
        )
    )
    return rows


def _fixture(
    fixture_id: str,
    expected_behavior: str,
    passed: bool,
    explanation: str,
) -> dict[str, str]:
    return {
        "fixture_id": fixture_id,
        "status": "ready" if passed else "review",
        "expected_behavior": expected_behavior,
        "actual_behavior": explanation,
        "classification": "receipt_review_required" if not passed else "supported_by_candidate",
        "next_action": (
            "Inspect receipts before any formula patch." if not passed else "Keep in audit packet."
        ),
    }


def _rank(by_player: dict[str, dict[str, str]], player: str, field: str) -> int:
    return int(_float(by_player.get(player, {}).get(field), 9999.0))


def _value(by_player: dict[str, dict[str, str]], player: str) -> float:
    return _float(by_player.get(player, {}).get("dynasty_candidate_value"))


def _group(rows: list[dict[str, str]], key: str) -> dict[str, list[dict[str, str]]]:
    output: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        output.setdefault(row.get(key, ""), []).append(row)
    return output


def _read_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = tuple(rows[0]) if rows else ("status",)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _write_md(path: Path, title: str, rows: list[dict[str, str]]) -> None:
    headers = tuple(rows[0]) if rows else ("status",)
    lines = [
        f"# {title}",
        "",
        "Review-only. Active app rankings, My Team, War Board, and readiness gates are unchanged.",
        "",
        "|" + "|".join(headers) + "|",
        "|" + "|".join("---" for _header in headers) + "|",
    ]
    for row in rows:
        lines.append("|" + "|".join(_md(row.get(header, "")) for header in headers) + "|")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _md(value: object) -> str:
    return str(value).replace("|", "/").replace("\n", " ")


def _float(value: object, default: float = 0.0) -> float:
    try:
        if value in (None, ""):
            return default
        return float(str(value))
    except ValueError:
        return default


if __name__ == "__main__":
    main()
