import csv
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts.rookie_framework.tune_rookie_model_runway_v1_1 import build_exports  # noqa: E402


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = sorted({key for row in rows for key in row})
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def label_row(index: int, year: int, position: str, star: str = "0", bust: str = "0") -> dict[str, object]:
    return {
        "historical_label_key": f"label:{year}:{position}:{index}",
        "draft_year": str(year),
        "player_name": f"Player {year} {position} {index}",
        "normalized_player_name": f"player{year}{position.lower()}{index}",
        "position": position,
        "college": "Test State",
        "draft_round": "1" if index <= 4 else "3",
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


def test_model_tuning_runway_v1_1_exports_without_v2_board() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        labels = []
        repaired = []
        for year in range(2010, 2024):
            for idx, pos in enumerate(["QB", "RB", "WR", "TE", "WR", "RB"], start=1):
                labels.append(label_row(idx, year, pos, star="1" if pos == "WR" and idx == 3 else "0", bust="1" if idx == 6 else "0"))
                status = "matched_name_position_season"
                repaired.append(
                    {
                        "historical_label_key": labels[-1]["historical_label_key"],
                        "cfbd_join_status_after_repair": status,
                        "repair_classification": "already_matched",
                        "cfbd_player_id": str(idx),
                        "team": "Test State",
                        "conference": "Test",
                        "position": pos,
                        "passing_yards": "3000" if pos == "QB" else "",
                        "passing_tds": "25" if pos == "QB" else "",
                        "passing_yard_share": "0.80" if pos == "QB" else "",
                        "passing_td_share": "0.70" if pos == "QB" else "",
                        "rushing_yards": "1200" if pos == "RB" else "100" if pos == "QB" else "",
                        "rushing_tds": "12" if pos == "RB" else "",
                        "rushing_yard_share": "0.34" if pos == "RB" else "",
                        "rushing_td_share": "0.28" if pos == "RB" else "",
                        "receiving_yards": "1100" if pos in {"WR", "TE"} else "250" if pos == "RB" else "",
                        "receiving_tds": "9" if pos in {"WR", "TE"} else "",
                        "receptions": "70" if pos in {"WR", "TE"} else "25" if pos == "RB" else "",
                        "receiving_yard_share": "0.32" if pos == "WR" else "0.20" if pos == "TE" else "",
                        "reception_share": "0.27" if pos == "WR" else "0.16" if pos == "TE" else "0.08" if pos == "RB" else "",
                        "receiving_td_share": "0.25" if pos in {"WR", "TE"} else "",
                    }
                )
        labels_path = root / "labels.csv"
        repaired_path = root / "repaired.csv"
        output_dir = root / "exports"
        board_path = root / "missing_current_board.csv"
        write_csv(labels_path, labels)
        write_csv(repaired_path, repaired)

        result = build_exports(labels_path, repaired_path, output_dir, board_path)
        decisions = read_csv(output_dir / "candidate_decision_v1_1_20260615.csv")
        ablations = read_csv(output_dir / "feature_ablation_metrics_v1_1_20260615.csv")
        split_metrics = read_csv(output_dir / "candidate_validation_metrics_v1_1_20260615.csv")

        assert result["best_candidate"]
        assert result["v2_created"] == "no"
        assert any(row["candidate_name"] == "v2_board_decision" and row["decision"] == "not_created" for row in decisions)
        assert any(row["model"] == "ablation_cfbd_market_share_only" for row in ablations)
        assert any(row["scope_value"] == "dev_validation_2020_2021" for row in split_metrics)
        assert (output_dir / "README_ROOKIE_MODEL_TUNING_RUNWAY_V1_1_20260615.md").exists()
        assert not (output_dir / "rookie_draft_ranking_v2_candidate_20260615.csv").exists()


if __name__ == "__main__":
    test_model_tuning_runway_v1_1_exports_without_v2_board()
    print("rookie_model_tuning_runway_v1_1 direct harness passed")
