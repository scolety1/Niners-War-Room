from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.services.lve_stats_first_veteran_formula_service import (  # noqa: E402
    score_stats_first_veteran_row,
)
from src.services.market_influence_policy_service import (  # noqa: E402
    market_edge_classification,
    market_status_warning,
    market_value_status,
    safe_market_edge_score,
)

DEFAULT_ACTIVE_ROOT = REPO_ROOT / "local_exports" / "active_veteran_model_public_sources"
DEFAULT_AUDIT_ROOT = REPO_ROOT / "local_exports" / "model_audits"
NORMALIZED_FILE = "stats_first_normalized_features.csv"
OUTPUT_FILE = "stats_first_veteran_model_preview_outputs.csv"

PRIVATE_FIELDS = (
    "private_lve_value",
    "win_now_value",
    "dynasty_hold_value",
    "keeper_score",
    "drop_candidate_score",
    "horizon_retention_score",
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Export a repeatable market-contamination audit for the stats-first "
            "veteran model. This is read-only and keeps rankings review-only."
        )
    )
    parser.add_argument(
        "--active-root",
        type=Path,
        default=DEFAULT_ACTIVE_ROOT,
        help="Folder containing active stats-first preview CSVs.",
    )
    parser.add_argument(
        "--audit-root",
        type=Path,
        default=DEFAULT_AUDIT_ROOT,
        help="Folder where a timestamped audit packet will be written.",
    )
    parser.add_argument(
        "--audit-id",
        help="Optional deterministic audit id.",
    )
    args = parser.parse_args()

    computed_at = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    audit_id = args.audit_id or "sprint2_phase11_market_contamination_" + (
        computed_at.replace("-", "").replace(":", "").replace("Z", "")
    )
    audit_dir = args.audit_root / audit_id
    audit_dir.mkdir(parents=True, exist_ok=False)

    normalized_path = args.active_root / NORMALIZED_FILE
    output_path = args.active_root / OUTPUT_FILE
    normalized_rows = _read_csv(normalized_path)
    output_rows = _read_csv(output_path)

    extreme_rows = _extreme_market_rows(normalized_rows)
    status_rows = _market_status_rows(output_rows)
    summary_rows = _summary_rows(extreme_rows, status_rows)

    extreme_path = audit_dir / "market_contamination_extreme_test.csv"
    status_path = audit_dir / "market_status_rows.csv"
    summary_path = audit_dir / "market_status_summary.csv"
    manifest_path = audit_dir / "manifest.json"

    _write_csv(extreme_path, extreme_rows)
    _write_csv(status_path, status_rows)
    _write_csv(summary_path, summary_rows)

    private_failures = sum(
        1 for row in extreme_rows if row["private_values_unchanged"] != "true"
    )
    trade_failures = sum(1 for row in extreme_rows if row["trade_value_moved"] != "true")
    unusable_edge_failures = sum(
        1
        for row in status_rows
        if row["market_status"] in {
            "missing_market",
            "disabled_market",
            "neutral_market_placeholder",
        }
        and (
            row["safe_market_edge_score"] not in {"", "0.0", "0"}
            or row["market_edge_view"] != "market_unavailable"
        )
    )
    status_counts = Counter(str(row["market_status"]) for row in status_rows)
    manifest = {
        "audit_id": audit_id,
        "created_at": computed_at,
        "active_root": str(args.active_root.resolve()),
        "normalized_file": str(normalized_path.resolve()),
        "preview_output_file": str(output_path.resolve()),
        "extreme_test_file": str(extreme_path.resolve()),
        "market_status_file": str(status_path.resolve()),
        "summary_file": str(summary_path.resolve()),
        "normalized_rows": len(normalized_rows),
        "preview_output_rows": len(output_rows),
        "private_value_failure_rows": private_failures,
        "trade_value_failure_rows": trade_failures,
        "unusable_market_edge_failure_rows": unusable_edge_failures,
        "market_status_counts": dict(sorted(status_counts.items())),
        "review_only": True,
        "decision_ready": False,
        "verdict": (
            "pass"
            if private_failures == 0
            and trade_failures == 0
            and unusable_edge_failures == 0
            else "review"
        ),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")

    print(f"audit_id={audit_id}")
    print(f"audit_dir={audit_dir.resolve()}")
    print(f"normalized_rows={len(normalized_rows)}")
    print(f"preview_output_rows={len(output_rows)}")
    print(f"private_value_failure_rows={private_failures}")
    print(f"trade_value_failure_rows={trade_failures}")
    print(f"unusable_market_edge_failure_rows={unusable_edge_failures}")
    print(f"market_status_counts={dict(sorted(status_counts.items()))}")
    print(f"verdict={manifest['verdict']}")
    return 0 if manifest["verdict"] == "pass" else 2


def _extreme_market_rows(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    for row in rows:
        low_row = dict(row)
        low_row["market_liquidity"] = "0"
        low_row["market_value_status"] = "real_imported_market"
        high_row = dict(row)
        high_row["market_liquidity"] = "100"
        high_row["market_value_status"] = "real_imported_market"

        low = score_stats_first_veteran_row(low_row)
        high = score_stats_first_veteran_row(high_row)
        private_unchanged = all(
            getattr(low, field) == getattr(high, field) for field in PRIVATE_FIELDS
        )
        output.append(
            {
                "player_id": low.player_id,
                "player_name": low.player_name,
                "position": low.position,
                "low_market_value": low.market_trade_value,
                "high_market_value": high.market_trade_value,
                "low_private_lve_value": low.private_lve_value,
                "high_private_lve_value": high.private_lve_value,
                "low_keeper_score": low.keeper_score,
                "high_keeper_score": high.keeper_score,
                "low_drop_candidate_score": low.drop_candidate_score,
                "high_drop_candidate_score": high.drop_candidate_score,
                "low_trade_value": low.trade_value,
                "high_trade_value": high.trade_value,
                "low_market_edge_score": low.market_edge_score,
                "high_market_edge_score": high.market_edge_score,
                "private_values_unchanged": _bool_text(private_unchanged),
                "trade_value_moved": _bool_text(high.trade_value > low.trade_value),
                "market_edge_moved": _bool_text(
                    high.market_edge_score != low.market_edge_score
                ),
                "low_market_status": low.market_value_status,
                "high_market_status": high.market_value_status,
            }
        )
    return output


def _market_status_rows(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    for row in rows:
        private_value = _float(row.get("private_lve_value"))
        market_value = _float(row.get("market_trade_value"))
        status = market_value_status(row)
        safe_edge = safe_market_edge_score(
            private_value,
            market_value,
            status,
            explicit_edge=row.get("market_edge_score"),
        )
        output.append(
            {
                "player_id": row.get("player_id", ""),
                "player_name": row.get("player_name", ""),
                "position": row.get("position", ""),
                "team": row.get("team", ""),
                "private_lve_value": row.get("private_lve_value", ""),
                "market_trade_value": row.get("market_trade_value", ""),
                "raw_market_edge_score": row.get("market_edge_score", ""),
                "safe_market_edge_score": "" if safe_edge is None else safe_edge,
                "market_status": status,
                "market_edge_warning": market_status_warning(status),
                "market_edge_view": (
                    "market_unavailable"
                    if safe_edge is None
                    else market_edge_classification(status, safe_edge)
                ),
                "missing_or_default_market": _bool_text(
                    status
                    in {
                        "missing_market",
                        "disabled_market",
                        "neutral_market_placeholder",
                    }
                ),
            }
        )
    return output


def _summary_rows(
    extreme_rows: list[dict[str, object]],
    status_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    status_counts = Counter(str(row["market_status"]) for row in status_rows)
    return [
        {
            "check": "private_model_value_extreme_market_test",
            "status": (
                "pass"
                if all(row["private_values_unchanged"] == "true" for row in extreme_rows)
                else "review"
            ),
            "rows": len(extreme_rows),
            "detail": (
                "Private/model, keeper, drop, and horizon values are unchanged "
                "when market is forced from 0 to 100."
            ),
        },
        {
            "check": "trade_liquidity_extreme_market_test",
            "status": (
                "pass"
                if all(row["trade_value_moved"] == "true" for row in extreme_rows)
                else "review"
            ),
            "rows": len(extreme_rows),
            "detail": "Trade/liquidity value moves when market is forced from 0 to 100.",
        },
        {
            "check": "missing_default_market_unavailable",
            "status": (
                "pass"
                if all(
                    row["market_edge_view"] == "market_unavailable"
                    for row in status_rows
                    if row["missing_or_default_market"] == "true"
                )
                else "review"
            ),
            "rows": sum(
                1 for row in status_rows if row["missing_or_default_market"] == "true"
            ),
            "detail": (
                "Missing/default market rows are unavailable for edge, not "
                "treated as real edge."
            ),
        },
        *(
            {
                "check": f"market_status_count_{status}",
                "status": "info",
                "rows": count,
                "detail": "Active preview row count by market source status.",
            }
            for status, count in sorted(status_counts.items())
        ),
    ]


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise SystemExit(f"Required CSV not found: {path}")
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _float(value: object) -> float | None:
    if value in {None, ""}:
        return None
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return None


def _bool_text(value: bool) -> str:
    return "true" if value else "false"


if __name__ == "__main__":
    raise SystemExit(main())
