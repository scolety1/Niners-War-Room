from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd

from src.services.outcome_v3_calibration_service import (
    NOT_ENOUGH_INFORMATION,
    RELEASE_IDENTIFIER,
)
from src.services.outcome_v3_display_service import (
    load_outcome_v3_display,
    outcome_v3_player_matrix,
    player_compare_outcome_v3_rows,
    rankings_outcome_v3_rows,
)


def test_owner_matrix_is_one_qb_per_row_with_all_applicable_thresholds() -> None:
    bundle = load_outcome_v3_display()
    board = (
        bundle.frame[["player_id", "player_name", "position", "finished_v1_rank"]]
        .drop_duplicates("player_id")
        .rename(columns={"finished_v1_rank": "nwr_rank"})
    )

    matrix, coverage, details = outcome_v3_player_matrix(
        board, bundle.frame, position="QB"
    )

    assert matrix["Player"].is_unique
    assert {"2026 T6", "2026 T12", "Within 5Y T6", "2 of 3Y T12"} <= set(
        matrix.columns
    )
    assert coverage.applicable == len(matrix) * 2 * 6
    assert coverage.numeric + sum(count for _, count in coverage.classifications) == (
        coverage.applicable
    )
    assert len(details) == coverage.applicable
    assert "—" in set(matrix.drop(columns=["NWR Rank", "Player", "Pos"]).stack())


def test_committed_outcome_v3_release_loads_with_manifest_and_schema_checks() -> None:
    bundle = load_outcome_v3_display()

    assert bundle.loaded
    assert bundle.row_count == 240 * 72
    assert bundle.player_count == 240
    assert bundle.release_identifier == RELEASE_IDENTIFIER
    assert not bundle.errors


def test_rankings_lens_is_exact_id_ordered_and_omits_two_of_three() -> None:
    bundle = load_outcome_v3_display()
    players = (
        bundle.frame.loc[
            bundle.frame["position"].eq("WR")
            & bundle.frame["evidence_state"].eq("complete"),
            ["player_id", "player_name", "finished_v1_rank"],
        ]
        .drop_duplicates("player_id")
        .head(2)
        .iloc[::-1]
    )
    board = players.rename(columns={"finished_v1_rank": "nwr_rank"}).assign(
        position="WR"
    )

    rows = rankings_outcome_v3_rows(
        board,
        bundle.frame,
        position="WR",
        threshold=12,
    )

    assert len(rows) == 10
    assert rows["Player"].drop_duplicates().tolist() == board["player_name"].tolist()
    assert rows.groupby("Player", sort=False)["Horizon"].count().eq(5).all()
    assert set(rows["Horizon"]) == {
        "2026",
        "2027",
        "2028",
        "Within 3 Years",
        "Within 5 Years",
    }
    assert "Two Qualifying Seasons Within 3 Years" not in set(rows["Horizon"])


def test_player_compare_expands_two_of_three_and_never_name_falls_back() -> None:
    bundle = load_outcome_v3_display()
    known = (
        bundle.frame.loc[
            bundle.frame["position"].eq("RB")
            & bundle.frame["evidence_state"].eq("complete")
        ]
        .drop_duplicates("player_id")
        .iloc[0]
    )
    compare = pd.DataFrame(
        [
            {
                "player_id": known["player_id"],
                "player": known["player_name"],
                "position": "RB",
                "final_board_rank": known["finished_v1_rank"],
            },
            {
                "player_id": "",
                "player": known["player_name"],
                "position": "RB",
                "final_board_rank": "999",
            },
        ]
    )

    rows = player_compare_outcome_v3_rows(compare, bundle.frame)
    known_rows = rows.loc[rows["Finished V1 Rank"].eq(known["finished_v1_rank"])]
    missing_rows = rows.loc[rows["Finished V1 Rank"].eq("999")]

    assert len(known_rows) == 4 * 6
    assert "Two Qualifying Seasons Within 3 Years" in set(known_rows["Horizon"])
    assert len(missing_rows) == 4 * 6
    assert missing_rows["Probability"].eq(NOT_ENOUGH_INFORMATION).all()
    assert missing_rows["Missing-state explanation"].str.contains(
        "missing exact player_id"
    ).all()


def test_manifest_hash_and_blocked_numeric_mutations_fail_closed(tmp_path: Path) -> None:
    bundle = load_outcome_v3_display()
    frame = bundle.frame.copy()
    blocked_index = frame.index[
        frame["evidence_state"].eq("blocked_or_unsupported")
    ][0]
    frame.loc[blocked_index, "probability"] = "0.0"
    frame.loc[blocked_index, "probability_display"] = "0.0%"
    integration = tmp_path / "OUTCOME_V3_INTEGRATION_PACK.csv"
    frame.to_csv(integration, index=False, lineterminator="\n")
    source_hash = hashlib.sha256(integration.read_bytes()).hexdigest()
    manifest = tmp_path / "MANIFEST.json"
    manifest.write_text(
        json.dumps(
            {
                "release_identifier": RELEASE_IDENTIFIER,
                "artifacts": [
                    {
                        "path": integration.name,
                        "sha256": source_hash,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    mutated = load_outcome_v3_display(
        integration_path=integration,
        manifest_path=manifest,
    )

    assert not mutated.loaded
    assert "blocked or insufficient row is numeric" in " ".join(mutated.errors)

    manifest.write_text(
        json.dumps(
            {
                "release_identifier": RELEASE_IDENTIFIER,
                "artifacts": [
                    {
                        "path": integration.name,
                        "sha256": "0" * 64,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    bad_hash = load_outcome_v3_display(
        integration_path=integration,
        manifest_path=manifest,
    )
    assert not bad_hash.loaded
    assert "hash mismatch" in " ".join(bad_hash.errors)
