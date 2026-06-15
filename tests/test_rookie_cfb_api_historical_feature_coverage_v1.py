import csv
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts.rookie_framework.audit_rookie_cfb_api_historical_feature_coverage_v1 import (  # noqa: E402
    build_exports,
)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_cfb_api_audit_exports_expected_files_without_live_sampling() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "out"
        counts = build_exports(out, live_sample=False)

        config = read_csv(out / "cfb_api_config_inventory_20260615.csv")
        samples = read_csv(out / "cfb_api_sample_plan_and_results_20260615.csv")
        coverage = read_csv(out / "cfb_api_feature_coverage_matrix_20260615.csv")
        families = read_csv(out / "cfb_api_feature_family_summary_20260615.csv")
        requests = read_csv(out / "cfb_api_missing_fields_and_tim_requests_20260615.csv")

        assert counts["config_rows"] >= 5
        assert len(samples) == 28
        assert len(coverage) == 28
        assert any(row["year"] == "2010" and row["position"] == "WR" for row in coverage)
        assert any(row["feature_family"] == "college_production_box_score" for row in families)
        assert any(row["item"] == "CFBD_API_KEY" for row in config)
        assert any(row["priority"] == "1" and "CFBD_API_KEY" in row["needed_item"] for row in requests)
        assert (out / "README_CFB_API_HISTORICAL_FEATURE_COVERAGE_AUDIT_20260615.md").exists()


if __name__ == "__main__":
    test_cfb_api_audit_exports_expected_files_without_live_sampling()
    print("rookie_cfb_api_historical_feature_coverage_v1 direct harness passed")
