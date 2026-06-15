import csv
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts.rookie_framework.audit_rookie_expanded_pool_baseline_tuning_readiness_v1 import build_exports  # noqa: E402


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = sorted({key for row in rows for key in row})
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def label(
    year: str,
    name: str,
    position: str,
    draft_round: str,
    pick: str,
    points: str,
    star: str,
    bust: str,
    ready: str = "yes",
    partial: str = "no",
) -> dict[str, str]:
    return {
        "historical_label_key": f"test:{year}:{name}:{position}:{pick}",
        "source_pool": "test",
        "draft_year": year,
        "player_name": name,
        "normalized_player_name": "".join(ch for ch in name.lower() if ch.isalnum()),
        "position": position,
        "college": "Test",
        "nfl_team": "TST",
        "draft_round": draft_round,
        "overall_pick": pick,
        "gsis_id": "",
        "pfr_player_id": "",
        "cfb_player_id": "",
        "historical_label_status": "GREEN_COMPLETE",
        "backtest_ready": ready,
        "partial_window_only": partial,
        "star_label": star,
        "bust_label": bust,
        "useful_label": "1" if star == "1" else "0",
        "starter_season_count": "1" if star == "1" else "0",
        "best_first_3_years_pos_finish": "1" if star == "1" else "99",
        "year1_points": points,
        "year2_points": "0",
        "year3_points": "0",
        "three_year_points": points,
        "label_quality_notes": "",
        "label_scoring_quality": "test",
        "guardrails": "labels_eval_only; no_tuning",
    }


def test_expanded_pool_baseline_audit_exports_metric_diagnostics() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        expanded_dir = root / "expanded"
        output_dir = root / "out"
        rows = [
            label("2010", "Alpha Back", "RB", "1", "1", "500", "1", "0"),
            label("2010", "Beta Bust", "WR", "1", "2", "5", "0", "1"),
            label("2010", "Gamma Late", "WR", "6", "190", "450", "1", "0"),
            label("2011", "Delta Quarter", "QB", "1", "4", "300", "1", "0"),
            label("2011", "Epsilon Tight", "TE", "2", "50", "10", "0", "1"),
            label("2024", "Partial Future", "RB", "1", "5", "100", "0", "0", ready="no", partial="yes"),
        ]
        write_csv(expanded_dir / "expanded_historical_labels_v2_20260615.csv", rows)

        counts = build_exports(expanded_dir, output_dir)
        semantics = read_csv(output_dir / "metric_semantics_audit_20260615.csv")
        year_metrics = read_csv(output_dir / "year_class_baseline_metrics_20260615.csv")
        position_metrics = read_csv(output_dir / "position_baseline_metrics_20260615.csv")
        missed = read_csv(output_dir / "top_missed_stars_diagnostic_20260615.csv")
        decisions = read_csv(output_dir / "tuning_readiness_decision_20260615.csv")

        assert counts["label_rows"] == 6
        assert counts["complete_rows"] == 5
        assert any(row["metric_name"] == "year_class_top_n" for row in semantics)
        assert any(row["metric_scope"] == "year_class" and row["scope_value"] == "2010" for row in year_metrics)
        assert {row["position"] for row in position_metrics} == {"QB", "RB", "TE", "WR"}
        assert all(row["anti_cheat_note"] == "diagnosis only; no player-specific tuning" for row in missed)
        assert any(row["gate"] == "tuning_readiness" and row["verdict"] == "YELLOW" for row in decisions)


if __name__ == "__main__":
    test_expanded_pool_baseline_audit_exports_metric_diagnostics()
    print("rookie_expanded_pool_baseline_audit_tuning_readiness_v1 direct harness passed")
