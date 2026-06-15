import csv
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts.rookie_framework.audit_rookie_cfbd_enriched_baseline_runway_v1 import (  # noqa: E402
    build_exports,
)


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
        "draft_round": "1" if index <= 5 else "2",
        "overall_pick": str(index),
        "historical_label_status": "GREEN_COMPLETE",
        "backtest_ready": "yes",
        "partial_window_only": "no",
        "star_label": star,
        "bust_label": bust,
        "useful_label": "1",
        "starter_season_count": "1",
        "best_first_3_years_pos_finish": "10",
        "year1_points": "10",
        "year2_points": "10",
        "year3_points": "10",
        "three_year_points": "30",
        "label_quality_notes": "",
        "label_scoring_quality": "test",
        "guardrails": "labels_eval_only",
    }


def test_cfbd_enriched_runway_exports_phase_a_and_phase_b_safely() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        labels = []
        repaired = []
        for year in range(2010, 2024):
            for idx in range(1, 5):
                pos = ["QB", "RB", "WR", "TE"][idx - 1]
                labels.append(label_row(idx, year, pos, star="1" if idx == 3 else "0", bust="1" if idx == 4 else "0"))
                status = "matched_name_position_season"
                if year == 2022 and idx == 4:
                    status = "unmatched_cfbd_missing_row"
                if year == 2023 and idx == 2:
                    status = "matched_with_duplicate_candidate_selection"
                repaired.append(
                    {
                        "historical_label_key": labels[-1]["historical_label_key"],
                        "cfbd_join_status_after_repair": status,
                        "repair_classification": "duplicate_candidate_existing" if "duplicate" in status else "already_matched",
                        "cfbd_player_id": str(idx),
                        "team": "Test State",
                        "conference": "Test",
                        "position": pos,
                        "receiving_yards": "900" if pos in {"WR", "TE"} else "",
                        "receiving_yard_share": "0.35" if pos in {"WR", "TE"} else "",
                        "reception_share": "0.25" if pos in {"WR", "TE"} else "",
                        "receiving_td_share": "0.20" if pos in {"WR", "TE"} else "",
                        "rushing_yards": "1000" if pos == "RB" else "150" if pos == "QB" else "",
                        "rushing_yard_share": "0.30" if pos == "RB" else "",
                        "rushing_td_share": "0.25" if pos == "RB" else "",
                        "passing_yards": "3000" if pos == "QB" else "",
                        "passing_yard_share": "0.80" if pos == "QB" else "",
                        "passing_td_share": "0.70" if pos == "QB" else "",
                    }
                )
        labels_path = root / "labels.csv"
        join_path = root / "join.csv"
        phase_a = root / "phase_a"
        phase_b = root / "phase_b"
        write_csv(labels_path, labels)
        write_csv(join_path, repaired)

        result = build_exports(labels_path, join_path, phase_a, phase_b)
        coverage = read_csv(phase_a / "cfbd_enriched_feature_coverage_20260615.csv")
        unresolved = read_csv(phase_a / "unresolved_cfbd_row_policy_20260615.csv")

        assert result["phase_b_ran"] is True
        assert any(row["scope"] == "overall" and row["unresolved_no_enriched_features"] == "1" for row in coverage)
        assert unresolved[0]["policy"].startswith("not_zero_filled")
        assert (phase_b / "cfbd_enriched_candidate_decision_20260615.csv").exists()
        assert not (phase_b / "rookie_draft_ranking_v2_cfbd_candidate_20260615.csv").exists()


if __name__ == "__main__":
    test_cfbd_enriched_runway_exports_phase_a_and_phase_b_safely()
    print("rookie_cfbd_enriched_baseline_runway_v1 direct harness passed")
