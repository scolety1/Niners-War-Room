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


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_backtest_inventory_blocks_when_labels_are_missing() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        source = root / "historical.csv"
        out = root / "out"
        write_csv(
            source,
            [
                {
                    "historical_prospect_key": "backtest:2021:alpha:RB:1",
                    "prospect_name": "Alpha Back",
                    "position": "RB",
                    "draft_year": "2021",
                    "factual_evidence_json": "{}",
                    "derived_evidence_json": "{}",
                    "market_context_fields_json": "{}",
                }
            ],
            [
                "historical_prospect_key",
                "prospect_name",
                "position",
                "draft_year",
                "factual_evidence_json",
                "derived_evidence_json",
                "market_context_fields_json",
            ],
        )
        backtest.build_exports(source, out)
        inventory = read_csv(out / "rookie_historical_backtest_inventory_20260615.csv")
        failures = read_csv(out / "rookie_historical_backtest_failures_v1_20260615.csv")
        assert inventory[0]["backtest_runnable"] == "no"
        assert failures[0]["failure_type"] == "missing_evaluation_labels"
        assert (out / "README_ROOKIE_HISTORICAL_BACKTEST_V1_20260615.md").exists()


if __name__ == "__main__":
    test_backtest_inventory_blocks_when_labels_are_missing()
