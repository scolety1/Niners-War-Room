import csv
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts.rookie_framework.build_rookie_historical_allowlist_qa_expanded_baseline_v1 import build_exports  # noqa: E402


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


def current_label(key: str, year: str, name: str, position: str, ready: str) -> dict[str, str]:
    return {
        "historical_prospect_key": key,
        "prospect_name": name,
        "normalized_player_name": "".join(ch for ch in name.lower() if ch.isalnum()),
        "position": position,
        "college": "Current",
        "nfl_team": "CUR",
        "rookie_class_year": year,
        "label_star_flag": "0",
        "label_bust_flag": "0",
        "label_useful_flag": "1",
        "label_first3_starter_seasons": "1",
        "label_first3_best_pos_rank": "12",
        "label_year1_points": "100",
        "label_year2_points": "100",
        "label_year3_points": "100",
        "label_first3_total_points": "300",
        "label_missing_reason": "",
        "label_scoring_quality": "exact_non_ppr_with_rush_rec_first_downs",
        "eval_backtest_ready_flag": ready,
    }


def current_feature(key: str, draft_round: str, pick: str) -> dict[str, str]:
    return {
        "historical_prospect_key": key,
        "draft_round": draft_round,
        "draft_pick": pick,
    }


def test_allowlist_qa_and_expanded_baseline_exports_are_local_only() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        draft_picks = root / "draft.csv"
        player_stats = root / "stats.csv"
        current_labels = root / "current_labels.csv"
        current_features = root / "current_features.csv"
        output_dir = root / "out"

        write_csv(
            draft_picks,
            [
                {
                    "season": "2010",
                    "round": "1",
                    "pick": "1",
                    "team": "AAA",
                    "gsis_id": "00-alpha",
                    "pfr_player_id": "AlphRu00",
                    "cfb_player_id": "alpha-runner-1",
                    "pfr_player_name": "Alpha Runner",
                    "position": "RB",
                    "college": "Test State",
                    "category": "skill",
                    "side": "offense",
                    "age": "21",
                    "w_av": "99",
                },
                {
                    "season": "2010",
                    "round": "2",
                    "pick": "40",
                    "team": "BBB",
                    "gsis_id": "00-beta",
                    "pfr_player_id": "BetaWi00",
                    "cfb_player_id": "beta-wide-1",
                    "pfr_player_name": "Beta Wide",
                    "position": "WR",
                    "college": "Example",
                    "category": "skill",
                    "side": "offense",
                    "age": "22",
                    "w_av": "50",
                },
                {
                    "season": "2010",
                    "round": "7",
                    "pick": "240",
                    "team": "CCC",
                    "gsis_id": "00-gamma",
                    "pfr_player_id": "GammTe00",
                    "cfb_player_id": "gamma-tight-1",
                    "pfr_player_name": "Gamma Tight",
                    "position": "TE",
                    "college": "No Stat",
                    "category": "skill",
                    "side": "offense",
                    "age": "23",
                    "w_av": "1",
                },
            ],
        )
        write_csv(
            player_stats,
            [
                {
                    "season": "2010",
                    "week": "1",
                    "season_type": "REG",
                    "player_id": "00-alpha",
                    "player_display_name": "Alpha Runner",
                    "position_group": "RB",
                    "rushing_yards": "100",
                    "rushing_tds": "1",
                    "rushing_first_downs": "5",
                },
                {
                    "season": "2010",
                    "week": "1",
                    "season_type": "REG",
                    "player_id": "00-beta",
                    "player_display_name": "Beta Wide",
                    "position_group": "",
                    "receiving_yards": "80",
                    "receiving_tds": "1",
                    "receiving_first_downs": "4",
                },
            ],
        )
        write_csv(
            current_labels,
            [
                current_label("backtest:2021:delta:RB:4", "2021", "Delta Back", "RB", "yes"),
                current_label("backtest:2024:epsilon:WR:5", "2024", "Epsilon Wide", "WR", "partial"),
            ],
        )
        write_csv(
            current_features,
            [
                current_feature("backtest:2021:delta:RB:4", "1", "4"),
                current_feature("backtest:2024:epsilon:WR:5", "3", "80"),
            ],
        )

        counts = build_exports(player_stats, draft_picks, current_labels, current_features, output_dir)
        allowlist = read_csv(output_dir / "draft_source_allowlist_audit_20260615.csv")
        qa = read_csv(output_dir / "assumed_zero_qa_20260615.csv")
        labels = read_csv(output_dir / "expanded_historical_labels_v2_20260615.csv")
        metrics = read_csv(output_dir / "expanded_baseline_results_20260615.csv")

        assert counts["expanded_2010_2020_rows"] == 3
        assert counts["current_2021_2025_rows"] == 2
        assert counts["partial_rows"] == 1
        assert counts["backtest_ready_rows"] == 4
        assert {row["column_name"] for row in allowlist if row["used_in_features"] == "yes"} == {"round", "pick"}
        assert any(row["column_name"] == "w_av" and row["classification"] == "quarantine_future_or_career" for row in allowlist)
        assert any(row["player_name"] == "Beta Wide" and row["qa_classification"] == "id_repaired" for row in qa)
        assert any(row["player_name"] == "Gamma Tight" and row["qa_classification"] == "true_zero_no_nfl_fantasy_stats" for row in qa)
        assert all(row["guardrails"].startswith("labels_eval_only") for row in labels)
        assert all(row["historical_label_status"] != "EXCLUDED" for row in labels)
        assert any(row["metric_scope"] == "overall" and row["bucket"] == "top_12" for row in metrics)


if __name__ == "__main__":
    test_allowlist_qa_and_expanded_baseline_exports_are_local_only()
    print("rookie_historical_allowlist_qa_expanded_baseline_v1 direct harness passed")
