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


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_tuning_refuses_to_run_without_label_backed_backtest() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        backtest_dir = root / "backtest"
        out = root / "out"
        write_csv(
            backtest_dir / "rookie_historical_backtest_inventory_20260615.csv",
            [
                {
                    "backtest_runnable": "no",
                    "label_columns": "",
                    "reason": "historical features exist, but no evaluation label columns were found",
                }
            ],
            ["backtest_runnable", "label_columns", "reason"],
        )
        tuning.build_exports(backtest_dir, out)
        recommendation = read_csv(out / "rookie_tuning_recommendation_v1_20260615.csv")
        results = read_csv(out / "rookie_tuning_results_v1_20260615.csv")
        assert recommendation[0]["recommendation"] == "do_not_tune_yet"
        assert recommendation[0]["production_allowed"] == "no"
        assert results[0]["status"] == "blocked_missing_label_backtest"


if __name__ == "__main__":
    test_tuning_refuses_to_run_without_label_backed_backtest()
