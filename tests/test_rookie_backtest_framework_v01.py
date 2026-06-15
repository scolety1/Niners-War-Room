from __future__ import annotations

import csv
import importlib.util
import tempfile
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "rookie_framework" / "backtest_rookie_ranking_model_v01.py"
spec = importlib.util.spec_from_file_location("backtest_rookie_ranking_model_v01", SCRIPT_PATH)
backtest = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(backtest)


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = sorted({key for row in rows for key in row})
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def feature(key: str, year: str, name: str, position: str, pick: str, warnings: str = "") -> dict[str, str]:
    return {
        "historical_prospect_key": key,
        "prospect_name": name,
        "normalized_player_name": "".join(ch for ch in name.lower() if ch.isalnum()),
        "position": position,
        "college": "Test",
        "nfl_team": "testers",
        "draft_year": year,
        "draft_round": "1",
        "draft_pick": pick,
        "identity_status": "draft_result_canonical",
        "factual_evidence_json": '{"college_season_latest":{"rushing_yards":1000,"rushing_tds":10,"games":12}}',
        "derived_evidence_json": "{}",
        "prospect_prior_evidence_json": "{}",
        "context_fields_json": "{}",
        "market_context_fields_json": "{}",
        "source_status_json": '{"factual_evidence":"present","derived_evidence":"present","prospect_prior_evidence":"present"}',
        "receipt_pointers_json": "{}",
        "warning_flags": warnings,
        "excluded_reason": "",
        "matrix_version": "test",
    }


def label(key: str, year: str, name: str, position: str, points: str, star: str, bust: str, ready: str = "yes") -> dict[str, str]:
    return {
        "historical_prospect_key": key,
        "prospect_name": name,
        "normalized_player_name": "".join(ch for ch in name.lower() if ch.isalnum()),
        "position": position,
        "college": "Test",
        "nfl_team": "testers",
        "rookie_class_year": year,
        "identity_match_status": "name_position_year_match",
        "label_quality_status": "GREEN_COMPLETE_LABEL" if ready == "yes" else "YELLOW_PARTIAL_WINDOW",
        "label_missing_reason": "",
        "label_scoring_quality": "exact_non_ppr_with_rush_rec_first_downs",
        "label_first3_total_points": points,
        "label_first3_best_season_points": points,
        "label_first3_best_pos_rank": "1" if star == "1" else "60",
        "label_first3_starter_seasons": "1" if star == "1" else "0",
        "label_first3_zero_or_low_value_flag": bust,
        "label_bust_flag": bust,
        "label_star_flag": star,
        "label_useful_flag": star,
        "eval_label_source": "test",
        "eval_join_method": "historical_prospect_key",
        "eval_backtest_ready_flag": ready,
    }


def test_backtest_integrates_labels_and_writes_baseline_metrics() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        features = root / "historical.csv"
        labels = root / "labels.csv"
        out = root / "out"
        legacy = root / "legacy"
        feature_rows = [
            feature("backtest:2021:alpha:RB:1", "2021", "Alpha Back", "RB", "1"),
            feature("backtest:2022:beta:WR:2", "2022", "Beta Wide", "WR", "2", "source_limited"),
            feature("backtest:2023:gamma:TE:3", "2023", "Gamma Tight", "TE", "3"),
            feature("backtest:2024:delta:RB:4", "2024", "Delta Back", "RB", "4"),
        ]
        label_rows = [
            label("backtest:2021:alpha:RB:1", "2021", "Alpha Back", "RB", "500", "1", "0"),
            label("backtest:2022:beta:WR:2", "2022", "Beta Wide", "WR", "10", "0", "1"),
            label("backtest:2023:gamma:TE:3", "2023", "Gamma Tight", "TE", "300", "1", "0"),
            label("backtest:2024:delta:RB:4", "2024", "Delta Back", "RB", "100", "0", "0", "partial"),
        ]
        write_csv(features, feature_rows)
        write_csv(labels, label_rows)

        counts = backtest.build_exports(features, labels, out, legacy)
        join_audit = read_csv(out / "rookie_backtest_join_audit_20260615.csv")
        metrics = read_csv(out / "rookie_baseline_backtest_metrics_20260615.csv")
        scored = read_csv(out / "rookie_baseline_scored_rows_20260615.csv")

        assert counts["joined_rows"] == 4
        assert counts["baseline_rows"] == 3
        assert join_audit[0]["join_status"] == "GREEN"
        assert any(row["draft_year"] == "2024" and row["join_status"] == "YELLOW_PARTIAL_LABELS" for row in join_audit)
        assert any(row["metric_scope"] == "overall" and row["bucket"] == "top_12" for row in metrics)
        assert all(row["market_overlay_status"].startswith("display_only") for row in scored)
        assert (legacy / "rookie_historical_backtest_inventory_20260615.csv").exists()


def test_backtest_raises_when_labels_missing() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        features = root / "historical.csv"
        labels = root / "missing.csv"
        write_csv(features, [feature("backtest:2021:alpha:RB:1", "2021", "Alpha Back", "RB", "1")])
        try:
            backtest.build_exports(features, labels, root / "out", root / "legacy")
        except backtest.RookieBacktestError as exc:
            assert "Missing historical label rows" in str(exc)
        else:
            raise AssertionError("Expected missing-label backtest error")


if __name__ == "__main__":
    test_backtest_integrates_labels_and_writes_baseline_metrics()
    test_backtest_raises_when_labels_missing()
    print("rookie_backtest_framework_v01 direct harness passed")
