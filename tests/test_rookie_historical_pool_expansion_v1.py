from __future__ import annotations

import csv
import importlib.util
import tempfile
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "rookie_framework" / "audit_rookie_historical_pool_expansion_v1.py"
spec = importlib.util.spec_from_file_location("audit_rookie_historical_pool_expansion_v1", SCRIPT_PATH)
audit = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(audit)


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


def test_historical_pool_expansion_audit_builds_local_preview_without_tuning() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        player_stats = root / "player_stats.csv"
        draft_picks = root / "draft_picks.csv"
        current_labels = root / "current_labels.csv"
        outcome_readiness = root / "outcome_readiness"
        output = root / "out"

        write_csv(
            player_stats,
            [
                {
                    "season": "2010",
                    "season_type": "REG",
                    "player_display_name": "Alpha Runner",
                    "position_group": "RB",
                    "rushing_yards": "900",
                    "rushing_tds": "6",
                    "rushing_first_downs": "40",
                },
                {
                    "season": "2011",
                    "season_type": "REG",
                    "player_display_name": "Alpha Runner",
                    "position_group": "RB",
                    "rushing_yards": "400",
                    "rushing_tds": "2",
                    "rushing_first_downs": "20",
                },
            ],
        )
        write_csv(
            draft_picks,
            [
                {
                    "season": "2010",
                    "round": "1",
                    "pick": "12",
                    "team": "TST",
                    "gsis_id": "00-test",
                    "pfr_player_id": "AlphRu00",
                    "cfb_player_id": "alpha-runner-1",
                    "pfr_player_name": "Alpha Runner",
                    "position": "RB",
                    "college": "Test State",
                    "hof": "FALSE",
                    "w_av": "0",
                    "games": "0",
                }
            ],
        )
        write_csv(
            current_labels,
            [
                {
                    "rookie_class_year": "2021",
                    "position": "RB",
                    "label_year1_points": "1",
                    "label_star_flag": "0",
                    "label_bust_flag": "0",
                }
            ],
        )
        write_csv(
            outcome_readiness / "package_inventory.csv",
            [{"label_rows": "10"}],
        )
        write_csv(
            outcome_readiness / "support_readiness_by_head.csv",
            [{"outcome_head": "same_year_starter"}],
        )

        counts = audit.build_exports(player_stats, draft_picks, current_labels, outcome_readiness, output)
        source_inventory = read_csv(output / "historical_source_inventory_20260615.csv")
        draft_inventory = read_csv(output / "draft_source_inventory_20260615.csv")
        preview = read_csv(output / "expanded_label_pool_preview_20260615.csv")

        assert counts["preview_rows"] == 1
        assert counts["preview_green_rows"] == 1
        assert draft_inventory[0]["draft_source_status"] == "YELLOW_ALLOWLIST_REQUIRED"
        assert "w_av" in draft_inventory[0]["quarantined_outcome_fields"]
        assert source_inventory[0]["source_role"] == "preferred_label_component_source"
        assert preview[0]["guardrails"].startswith("audit_preview_only")
        assert preview[0]["eval_backtest_ready_flag"] == "yes"


if __name__ == "__main__":
    test_historical_pool_expansion_audit_builds_local_preview_without_tuning()
    print("rookie_historical_pool_expansion_v1 direct harness passed")
