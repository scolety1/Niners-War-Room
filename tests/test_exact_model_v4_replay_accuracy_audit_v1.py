from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import subprocess
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/build_exact_model_v4_replay_accuracy_audit_v1.py"
PACKET = ROOT / "docs/hq/master/nwr_exact_model_v4_replay_accuracy_audit_v1_20260723"


@pytest.fixture(scope="module")
def audit() -> Any:
    spec = importlib.util.spec_from_file_location("exact_replay_audit_under_test", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def sources(audit: Any) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    return audit.load_sources()


def test_exact_replay_contracts_remain_distinct() -> None:
    text = (PACKET / "EXACT_REPLAY_CONTRACT.md").read_text(encoding="utf-8")
    assert "EXACT_CURRENT_MODEL_V4_HISTORICAL_REPLAY" in text
    assert "historical-version replay" in text
    assert "accepted production-proxy replay" in text
    assert "The three contracts remain separate" in text


def test_tracked_sources_and_temporal_contract_accept(
    audit: Any,
    sources: tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame],
) -> None:
    _panel, mart, _age, _oof = sources
    audit.validate_tracked_input_hashes()
    records = audit.historical_feature_records(
        mart.head(2),
        feature_columns=("pyf_prior_nwr_points", "prior_games"),
    )
    audit.validate_temporal_records(records)


@pytest.mark.parametrize(
    ("mutation", "expected_message"),
    [
        ("future_production", "future or target-season source"),
        ("future_games", "future or target-season source"),
        ("current_adp", "current-only"),
        ("current_board_rank", "current-only"),
        ("target_score", "current-only"),
        ("missing_source_season", "season metadata"),
        ("missing_availability", "temporal metadata blank"),
        ("contradictory_seasons", "contradictory"),
    ],
)
def test_temporal_mutations_fail_closed(
    audit: Any,
    sources: tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame],
    mutation: str,
    expected_message: str,
) -> None:
    _panel, mart, _age, _oof = sources
    records = audit.historical_feature_records(
        mart.head(1),
        feature_columns=("prior_games",),
    )
    row = records.index[0]
    if mutation == "future_production":
        records.loc[row, ["field_name", "feature_family", "source_season"]] = [
            "pyf_prior_nwr_points",
            "FUTURE_PRODUCTION",
            records.loc[row, "target_season"],
        ]
    elif mutation == "future_games":
        records.loc[row, "source_season"] = records.loc[row, "target_season"]
    elif mutation == "current_adp":
        records.loc[row, ["field_name", "feature_family"]] = [
            "current_only_adp",
            "CURRENT_ONLY_ADP",
        ]
    elif mutation == "current_board_rank":
        records.loc[row, ["field_name", "feature_family"]] = [
            "current_board_rank",
            "CURRENT_BOARD_RANK",
        ]
    elif mutation == "target_score":
        records.loc[row, ["field_name", "feature_family"]] = [
            "target_score",
            "TARGET_SEASON_SCORE",
        ]
    elif mutation == "missing_source_season":
        records.loc[row, "source_season"] = pd.NA
    elif mutation == "missing_availability":
        records.loc[row, "availability_classification"] = pd.NA
    elif mutation == "contradictory_seasons":
        records.loc[row, "target_season"] = records.loc[row, "input_season"] + 2
    with pytest.raises(RuntimeError, match=expected_message):
        audit.validate_temporal_records(records)


def test_exactness_mask_is_derived_and_fails_closed(
    audit: Any,
    sources: tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame],
) -> None:
    _panel, mart, age, _oof = sources
    frame = audit.exactness_mask(mart, age)
    assert len(frame) == 5518
    assert not frame["full_exact_row"].astype(bool).any()
    assert frame["identity_status"].eq("EXACT_PRIMARY_EVIDENCE").all()
    assert frame["position_score_status"].eq("BLOCKED_MISSING_RECEIPT").all()
    assert frame["route_status"].eq("BLOCKED_SOURCE_NOT_ADMITTED").all()
    assert audit.derive_full_row_exactness(audit.default_exactness_proofs()) is False


def test_exactness_label_only_promotions_fail(audit: Any) -> None:
    proofs = audit.default_exactness_proofs()
    for source_classification in ("APPROXIMATE", "NEAR_EQUIVALENT"):
        mutated = [
            replace(
                proof,
                classification="EXACT_PRIMARY_EVIDENCE",
                provenance="",
                schema_proof="",
                identity_proof="",
                historical_availability_proof="",
            )
            if proof.component == "position_score"
            else proof
            for proof in proofs
        ]
        assert source_classification in audit.ALLOWED_CLASSIFICATIONS
        with pytest.raises(RuntimeError, match="lacks complete authority proof"):
            audit.derive_full_row_exactness(mutated)


def test_exactness_completeness_and_authority_mutations_fail(audit: Any) -> None:
    proofs = audit.default_exactness_proofs()
    with pytest.raises(RuntimeError, match="completeness failure"):
        audit.derive_full_row_exactness(
            [proof for proof in proofs if proof.component != "checkpoint"]
        )
    without_provenance = [
        replace(proof, provenance="") if proof.component == "identity" else proof
        for proof in proofs
    ]
    with pytest.raises(RuntimeError, match="lacks complete authority proof"):
        audit.derive_full_row_exactness(without_provenance)
    without_availability = [
        replace(proof, historical_availability_proof="")
        if proof.component == "lagged_production"
        else proof
        for proof in proofs
    ]
    with pytest.raises(RuntimeError, match="lacks complete authority proof"):
        audit.derive_full_row_exactness(without_availability)
    unsupported = [
        replace(proof, classification="EXACTISH")
        if proof.component == "position_score"
        else proof
        for proof in proofs
    ]
    with pytest.raises(RuntimeError, match="unsupported exactness classification"):
        audit.derive_full_row_exactness(unsupported)


def test_exact_player_id_join_accepts_governed_inputs(
    audit: Any,
    sources: tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame],
) -> None:
    _panel, mart, age, _oof = sources
    joined = audit.exact_player_id_join(
        mart[list(audit.EXACT_JOIN_KEYS) + ["player_name"]].head(20),
        age[list(audit.EXACT_JOIN_KEYS) + ["player_name"]].head(20),
    )
    assert len(joined) == 20


@pytest.mark.parametrize(
    "join_keys",
    [
        ("player_name", "season", "position"),
        ("normalized_player_name", "season", "position"),
        ("player_id", "player_name", "season"),
    ],
)
def test_name_and_partial_join_mutations_fail(
    audit: Any,
    sources: tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame],
    join_keys: tuple[str, ...],
) -> None:
    _panel, mart, age, _oof = sources
    with pytest.raises(RuntimeError, match="require exact player_id"):
        audit.exact_player_id_join(mart.head(5), age.head(5), join_keys=join_keys)


def test_identity_duplicate_blank_swap_and_same_name_mutations_fail(
    audit: Any,
    sources: tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame],
) -> None:
    _panel, mart, age, _oof = sources
    left = mart[list(audit.EXACT_JOIN_KEYS) + ["player_name"]].head(30).copy()
    right = age[list(audit.EXACT_JOIN_KEYS) + ["player_name"]].head(30).copy()
    duplicate = pd.concat([right, right.iloc[[0]]], ignore_index=True)
    with pytest.raises(RuntimeError, match="duplicate exact player identity"):
        audit.exact_player_id_join(left, duplicate)
    blank = right.copy()
    blank.loc[blank.index[0], "player_id"] = ""
    with pytest.raises(RuntimeError, match="blank player_id"):
        audit.exact_player_id_join(left, blank)
    same_group = right.groupby(["season", "position"], sort=True).filter(
        lambda group: len(group) >= 2
    )
    indices = list(same_group.index[:2])
    swapped = right.copy()
    swapped.loc[indices, "player_id"] = swapped.loc[indices[::-1], "player_id"].to_numpy()
    with pytest.raises(RuntimeError, match="identity universes differ|authority mismatch"):
        audit.exact_player_id_join(left, swapped)
    same_name = right.copy()
    same_name.loc[same_name.index[0], "player_id"] = "governed-id-mutation"
    with pytest.raises(RuntimeError, match="identity universes differ"):
        audit.exact_player_id_join(left, same_name)


@pytest.mark.parametrize(
    "mutation",
    ["score", "rank", "player_id", "add_row", "remove_row", "reorder", "source_asof"],
)
def test_frozen_comparator_mutations_fail(
    audit: Any,
    tmp_path: Path,
    mutation: str,
) -> None:
    frame = pd.read_csv(audit.FROZEN_2026, low_memory=False)
    if mutation == "score":
        frame.loc[frame.index[0], "raw_score"] = float(frame.loc[frame.index[0], "raw_score"]) + 1
    elif mutation == "rank":
        frame.loc[frame.index[0], "within_position_rank"] = (
            float(frame.loc[frame.index[0], "within_position_rank"]) + 1
        )
    elif mutation == "player_id":
        frame.loc[frame.index[0], "player_id"] = "governed-id-mutation"
    elif mutation == "add_row":
        frame = pd.concat([frame, frame.iloc[[0]]], ignore_index=True)
    elif mutation == "remove_row":
        frame = frame.iloc[1:].reset_index(drop=True)
    elif mutation == "reorder":
        frame = frame.iloc[::-1].reset_index(drop=True)
    elif mutation == "source_asof":
        frame.loc[frame.index[0], "input_source_dates"] = "2099-01-01"
    path = tmp_path / "frozen.csv"
    frame.to_csv(path, index=False, lineterminator="\n")
    with pytest.raises(RuntimeError, match="frozen 2026 comparator hash changed"):
        audit.validate_frozen_comparator(path)


def test_input_order_is_canonicalized(
    audit: Any,
) -> None:
    hashes = []
    for mode in ("original", "reverse", "random"):
        _panel, mart, age, _oof = audit.load_sources(input_order=mode, order_seed=20260723)
        data = audit.exactness_mask(mart, age).to_csv(
            index=False,
            lineterminator="\n",
            float_format="%.6f",
        )
        hashes.append(hashlib.sha256(data.encode("utf-8")).hexdigest())
    assert len(set(hashes)) == 1


def test_rank_ties_nulls_and_non_ascii_are_stable(audit: Any) -> None:
    rows = pd.DataFrame(
        [
            {
                "season": 2020,
                "position": "WR",
                "player_id": "id-2",
                "player_name": "Zoë",
                "score": 10.0,
            },
            {
                "season": 2020,
                "position": "WR",
                "player_id": "id-1",
                "player_name": "Zoë",
                "score": 10.0,
            },
            {
                "season": 2020,
                "position": "WR",
                "player_id": "id-3",
                "player_name": pd.NA,
                "score": pd.NA,
            },
        ]
    )
    mappings = []
    for ordered in (rows, rows.iloc[::-1], rows.sample(frac=1, random_state=20260723)):
        ranked = audit.add_ranks(ordered, "score", name="rank")
        mappings.append(ranked.set_index("player_id")["rank"].to_dict())
    for mapping in mappings:
        assert mapping["id-1"] == 1
        assert mapping["id-2"] == 2
        assert pd.isna(mapping["id-3"])


def test_proxy_metrics_and_candidate_gates_reproduce() -> None:
    results = pd.read_csv(PACKET / "BASELINE_ACCURACY_RESULTS.csv")
    proxy = results[
        (results["model"] == "ACCEPTED_PRODUCTION_PROXY") & (results["scope"] == "OVERALL")
    ].iloc[0]
    assert proxy["spearman"] == pytest.approx(0.674739, abs=0.000001)
    assert proxy["rank_mae"] == pytest.approx(21.649511, abs=0.000001)
    assert "GAUNTLET_081" in set(results["model"])
    gates = pd.read_csv(PACKET / "CHALLENGER_ACCEPTANCE_GATE_MATRIX.csv")
    candidate = gates[gates["candidate"] == "CANDIDATE_2"]
    assert len(candidate) == 20
    assert (candidate["result"] == "FAIL").sum() >= 6
    assert candidate.loc[candidate["gate"] == "NO_LOW_GAMES_INSTABILITY", "result"].item() == "FAIL"


def test_governed_candidate_count_and_missing_hq2_definition() -> None:
    definitions = pd.read_csv(PACKET / "CHALLENGER_DEFINITIONS.csv")
    assert len(definitions) == 4
    hq2 = definitions[definitions["candidate"] == "CANDIDATE_1"].iloc[0]
    assert hq2["status"] == "BLOCKED_MISSING_RECEIPT"
    assert "not found" in hq2["definition"]
    candidate3 = definitions[definitions["candidate"] == "CANDIDATE_3"].iloc[0]
    assert candidate3["status"] == "NOT_EVALUATED_NO_INVENTION"


def test_no_current_board_or_frozen_comparator_change(audit: Any) -> None:
    assert hashlib.sha256(audit.CURRENT_BOARD.read_bytes()).hexdigest() == audit.BOARD_HASH
    assert hashlib.sha256(audit.FROZEN_2026.read_bytes()).hexdigest() == audit.FROZEN_2026_HASH
    assert len(pd.read_csv(audit.CURRENT_BOARD, low_memory=False)) == 240
    assert len(audit.validate_frozen_comparator()) == 924
    simulation = pd.read_csv(PACKET / "CURRENT_BOARD_REVIEW_ONLY_SIMULATION.csv")
    assert simulation["production_write"].eq("NONE").all()


def test_manifest_has_all_required_packet_files() -> None:
    manifest = json.loads((PACKET / "MANIFEST.json").read_text(encoding="utf-8"))
    assert manifest["exact_rows"] == 0
    assert manifest["production_ranking_change"] == "NONE"
    assert manifest["frozen_2026_change"] == "NONE"
    assert manifest["fixed_source_commit"] == "0929ce6ec058a698efeee10fe5770f56047bab21"
    assert manifest["canonical_serialization"]["line_endings"] == "LF"
    names = {item["path"] for item in manifest["files"]}
    assert len(names) == 27
    assert "VALIDATION_RESULTS.md" in names
    assert "DETERMINISTIC_REGENERATION_MANIFEST.csv" in names


def run_builder(output: Path, *, order: str, timezone: str) -> None:
    environment = os.environ.copy()
    environment["TZ"] = timezone
    environment["PYTHONUTF8"] = "1"
    subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--source-commit",
            "0929ce6ec058a698efeee10fe5770f56047bab21",
            "--repo-root",
            str(ROOT),
            "--output-dir",
            str(output),
            "--input-order",
            order,
            "--order-seed",
            "20260723",
        ],
        cwd=ROOT,
        check=True,
        env=environment,
        capture_output=True,
        text=True,
    )


def test_full_packet_repeats_and_input_order_environment_do_not_change_bytes(
    audit: Any,
    tmp_path: Path,
) -> None:
    outputs = [
        (tmp_path / "original_a", "original", "UTC"),
        (tmp_path / "original_b", "original", "America/Denver"),
        (tmp_path / "reverse", "reverse", "UTC"),
        (tmp_path / "random", "random", "America/Denver"),
    ]
    for output, order, timezone in outputs:
        run_builder(output, order=order, timezone=timezone)
    baseline = outputs[0][0]
    for output, _order, _timezone in outputs[1:]:
        comparisons = audit.compare_packet_dirs(baseline, output)
        assert comparisons
        assert all(row["result"] == "PASS" for row in comparisons)
