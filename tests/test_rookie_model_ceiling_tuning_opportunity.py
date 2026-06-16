import csv
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts.rookie_framework.audit_rookie_model_ceiling_tuning_opportunity import build_exports  # noqa: E402


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = []
    seen = set()
    for row in rows:
        for key in row:
            if key not in seen:
                seen.add(key)
                columns.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def label_row(index: int, year: int, position: str, star: str, bust: str) -> dict[str, object]:
    return {
        "historical_label_key": f"label:{year}:{position}:{index}",
        "draft_year": str(year),
        "player_name": f"Player {year} {position} {index}",
        "normalized_player_name": f"player{year}{position.lower()}{index}",
        "position": position,
        "college": "Test State",
        "draft_round": "1" if index <= 3 else "4",
        "overall_pick": str(index),
        "historical_label_status": "GREEN_COMPLETE",
        "backtest_ready": "yes",
        "partial_window_only": "no",
        "star_label": star,
        "bust_label": bust,
        "useful_label": "1",
        "starter_season_count": "1",
        "best_first_3_years_pos_finish": "8",
        "year1_points": "25",
        "year2_points": "25",
        "year3_points": "25",
        "three_year_points": "75",
        "label_quality_notes": "",
        "label_scoring_quality": "test",
        "guardrails": "labels_eval_only",
    }


def repaired_row(label: dict[str, object]) -> dict[str, object]:
    position = str(label["position"])
    return {
        "historical_label_key": label["historical_label_key"],
        "cfbd_join_status_after_repair": "matched_name_position_season",
        "repair_classification": "already_matched",
        "cfbd_player_id": str(label["overall_pick"]),
        "team": "Test State",
        "conference": "Test",
        "position": position,
        "passing_yards": "3100" if position == "QB" else "",
        "passing_tds": "25" if position == "QB" else "",
        "passing_yard_share": "0.80" if position == "QB" else "",
        "passing_td_share": "0.70" if position == "QB" else "",
        "rushing_yards": "1200" if position == "RB" else "100" if position == "QB" else "",
        "rushing_tds": "12" if position == "RB" else "",
        "rushing_yard_share": "0.34" if position == "RB" else "",
        "rushing_td_share": "0.28" if position == "RB" else "",
        "receiving_yards": "1100" if position in {"WR", "TE"} else "250" if position == "RB" else "",
        "receiving_tds": "9" if position in {"WR", "TE"} else "",
        "receptions": "70" if position in {"WR", "TE"} else "25" if position == "RB" else "",
        "receiving_yard_share": "0.32" if position == "WR" else "0.20" if position == "TE" else "",
        "reception_share": "0.27" if position == "WR" else "0.16" if position == "TE" else "0.08" if position == "RB" else "",
        "receiving_td_share": "0.25" if position in {"WR", "TE"} else "",
    }


def test_model_ceiling_tuning_opportunity_exports() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        labels = []
        repaired = []
        for year in range(2010, 2024):
            for idx, position in enumerate(["QB", "RB", "WR", "TE", "WR", "RB"], start=1):
                row = label_row(
                    idx,
                    year,
                    position,
                    star="1" if position == "WR" and idx == 3 else "0",
                    bust="1" if idx == 6 else "0",
                )
                labels.append(row)
                repaired.append(repaired_row(row))

        labels_path = root / "labels.csv"
        repaired_path = root / "repaired.csv"
        ablation_path = root / "ablation.csv"
        output_dir = root / "exports"
        write_csv(labels_path, labels)
        write_csv(repaired_path, repaired)
        write_csv(
            ablation_path,
            [
                {
                    "model": "ablation_cfbd_market_share_only",
                    "scope_value": "final_validation_2022_2023",
                    "bucket": "top_24",
                    "star_capture_rate": "0.500",
                    "bust_rate_selected": "0.100",
                }
            ],
        )

        result = build_exports(labels_path, repaired_path, output_dir, ablation_path)
        metrics = read_csv(output_dir / "rolling_validation_metrics_20260615.csv")
        decisions = read_csv(output_dir / "model_ceiling_decision_20260615.csv")
        anti_cheat = read_csv(output_dir / "anti_cheat_leakage_audit_20260615.csv")

        assert result["rows"]
        assert any(row["metric_scope"] == "rolling_holdout_year" for row in metrics)
        assert any(row["decision_item"] == "v2_board" and row["verdict"] == "not_created" for row in decisions)
        assert all(row["status"] == "PASS" for row in anti_cheat)
        assert (output_dir / "README_ROOKIE_MODEL_CEILING_TUNING_OPPORTUNITY_AUDIT_20260615.md").exists()


if __name__ == "__main__":
    test_model_ceiling_tuning_opportunity_exports()
    print("rookie_model_ceiling_tuning_opportunity direct harness passed")
