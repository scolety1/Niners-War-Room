import csv
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts.rookie_framework.audit_rookie_experimental_tuning_candidate_v1 import build_exports  # noqa: E402


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


def label(year: str, name: str, position: str, draft_round: str, pick: str, star: str, bust: str) -> dict[str, str]:
    return {
        "historical_label_key": f"test:{year}:{name}:{position}:{pick}",
        "source_pool": "test",
        "draft_year": year,
        "player_name": name,
        "normalized_player_name": "".join(ch for ch in name.lower() if ch.isalnum()),
        "position": position,
        "college": "Display Only",
        "nfl_team": "TST",
        "draft_round": draft_round,
        "overall_pick": pick,
        "gsis_id": "",
        "pfr_player_id": "",
        "cfb_player_id": "",
        "historical_label_status": "GREEN_COMPLETE",
        "backtest_ready": "yes",
        "partial_window_only": "no",
        "star_label": star,
        "bust_label": bust,
        "useful_label": star,
        "starter_season_count": star,
        "best_first_3_years_pos_finish": "1" if star == "1" else "99",
        "year1_points": "300" if star == "1" else "10",
        "year2_points": "100" if star == "1" else "0",
        "year3_points": "50" if star == "1" else "0",
        "three_year_points": "450" if star == "1" else "10",
        "label_quality_notes": "",
        "label_scoring_quality": "test",
        "guardrails": "labels_eval_only; no_tuning",
    }


def test_experimental_tuning_candidate_exports_audit_only() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        labels = root / "labels.csv"
        out = root / "out"
        rows = [
            label("2010", "Alpha Back", "RB", "1", "1", "1", "0"),
            label("2010", "Beta Wide", "WR", "1", "8", "0", "1"),
            label("2010", "Gamma Tight", "TE", "2", "35", "1", "0"),
            label("2022", "Delta Back", "RB", "2", "45", "1", "0"),
            label("2022", "Epsilon Quarter", "QB", "1", "5", "0", "1"),
            label("2023", "Zeta Tight", "TE", "2", "40", "1", "0"),
            label("2024", "Partial Future", "WR", "1", "4", "1", "0") | {"backtest_ready": "no", "partial_window_only": "yes"},
        ]
        write_csv(labels, rows)

        counts = build_exports(labels, out)
        configs = read_csv(out / "candidate_configurations_v1_20260615.csv")
        split_metrics = read_csv(out / "candidate_split_metrics_v1_20260615.csv")
        decisions = read_csv(out / "candidate_decision_v1_20260615.csv")
        missed = read_csv(out / "candidate_top_missed_stars_v1_20260615.csv")

        assert counts["label_rows"] == 6
        assert counts["candidate_count"] >= 6
        assert any(row["candidate_name"] == "scoring_format_fit_plus" for row in configs)
        assert any(row["split"] == "validation_2022_2023" and row["bucket"] == "top_12" for row in split_metrics)
        assert any(row["candidate_decision"] in {"eligible_candidate", "not_selected"} for row in decisions)
        assert all("no player-specific tuning" in row["anti_cheat_note"] for row in missed)


if __name__ == "__main__":
    test_experimental_tuning_candidate_exports_audit_only()
    print("rookie_experimental_tuning_candidate_v1 direct harness passed")
