from __future__ import annotations

import csv
import importlib.util
import tempfile
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "rookie_framework" / "tune_rookie_ranking_model_v01.py"
spec = importlib.util.spec_from_file_location("tune_rookie_ranking_model_v01", SCRIPT_PATH)
tuning = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(tuning)


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


def scored_row(year: str, rank: int, name: str, star: str, bust: str) -> dict[str, str]:
    return {
        "historical_prospect_key": f"backtest:{year}:{name.lower()}:RB:{rank}",
        "draft_year": year,
        "baseline_rank": str(rank),
        "prospect_name": name,
        "position": "RB",
        "draft_pick": str(rank),
        "star_upside_index": str(90 - rank),
        "bust_risk_index": str(20 + rank),
        "early_role_index": "70",
        "long_term_value_index": "75",
        "scoring_fit_index": "72",
        "evidence_confidence_index": "80",
        "positional_adjustment_index": "72",
        "warning_penalty_index": "4",
        "label_star_flag": star,
        "label_bust_flag": bust,
    }


def write_green_backtest(backtest_dir: Path) -> None:
    audit_rows = [
        {
            "draft_year": year,
            "join_status": "GREEN",
        }
        for year in ["2021", "2022", "2023"]
    ]
    write_csv(backtest_dir / "rookie_backtest_join_audit_20260615.csv", audit_rows)
    rows = []
    for year in ["2021", "2022", "2023"]:
        for rank in range(1, 15):
            rows.append(scored_row(year, rank, f"Player{year}{rank}", "1" if rank in {1, 2, 8} else "0", "1" if rank in {10, 11} else "0"))
    write_csv(backtest_dir / "rookie_baseline_scored_rows_20260615.csv", rows)


def test_tuning_runs_only_after_green_join() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        backtest_dir = root / "backtest"
        out = root / "out"
        legacy = root / "legacy"
        write_green_backtest(backtest_dir)

        counts = tuning.build_exports(backtest_dir, out, legacy)
        results = read_csv(out / "rookie_tuning_experiment_results_20260615.csv")
        recommendation = read_csv(legacy / "rookie_tuning_recommendation_v1_20260615.csv")

        assert counts["tuning_ran"] == 1
        assert len(results) == len(tuning.CANDIDATE_WEIGHTS)
        assert all(row["production_allowed"] == "no" for row in results)
        assert recommendation[0]["production_allowed"] == "no"


def test_tuning_refuses_to_run_without_green_join() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        backtest_dir = root / "backtest"
        out = root / "out"
        legacy = root / "legacy"
        write_csv(backtest_dir / "rookie_backtest_join_audit_20260615.csv", [{"draft_year": "2021", "join_status": "RED"}])

        counts = tuning.build_exports(backtest_dir, out, legacy)
        results = read_csv(out / "rookie_tuning_experiment_results_20260615.csv")
        recommendation = read_csv(legacy / "rookie_tuning_recommendation_v1_20260615.csv")

        assert counts["tuning_ran"] == 0
        assert results == []
        assert recommendation[0]["recommendation"] == "do_not_tune_yet"
        assert recommendation[0]["production_allowed"] == "no"


if __name__ == "__main__":
    test_tuning_runs_only_after_green_join()
    test_tuning_refuses_to_run_without_green_join()
    print("rookie_tuning_loop_v01 direct harness passed")
