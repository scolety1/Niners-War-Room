from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/build_exact_model_v4_replay_accuracy_audit_v1.py"
PACKET = ROOT / "docs/hq/master/nwr_exact_model_v4_replay_accuracy_audit_v1_20260723"


def test_exact_replay_contracts_remain_distinct() -> None:
    text = (PACKET / "EXACT_REPLAY_CONTRACT.md").read_text(encoding="utf-8")
    assert "EXACT_CURRENT_MODEL_V4_HISTORICAL_REPLAY" in text
    assert "Contract B — historical-version replay" in text
    assert "Contract C — accepted production-proxy replay" in text
    assert "The three contracts remain separate" in text


def test_exactness_mask_fails_closed() -> None:
    frame = pd.read_csv(PACKET / "COMPONENT_AND_ROW_EXACTNESS_MASK.csv")
    assert len(frame) == 5518
    assert not frame["full_exact_row"].astype(bool).any()
    assert frame["identity_status"].eq("EXACT_PRIMARY_EVIDENCE").all()
    assert frame["position_score_status"].eq("BLOCKED_MISSING_RECEIPT").all()
    assert frame["route_status"].eq("BLOCKED_SOURCE_NOT_ADMITTED").all()


def test_temporal_identity_and_panel_contract() -> None:
    frame = pd.read_csv(PACKET / "COMPONENT_AND_ROW_EXACTNESS_MASK.csv")
    assert (frame["target_season"] == frame["feature_season"] + 1).all()
    assert frame["substrate_row_id"].is_unique
    assert not frame["player_id"].isna().any()
    panels = pd.read_csv(PACKET / "LEAKAGE_SAFE_PANEL_MANIFEST.csv")
    assert set(panels["panel"]) == {
        "EXACT_REPLAY",
        "EXACT_COMPONENT_PARTIAL",
        "ACCEPTED_PROXY",
        "CANDIDATE_OOF",
    }


def test_proxy_metrics_and_candidate_gates_reproduce() -> None:
    results = pd.read_csv(PACKET / "BASELINE_ACCURACY_RESULTS.csv")
    proxy = results[
        (results["model"] == "ACCEPTED_PRODUCTION_PROXY") & (results["scope"] == "OVERALL")
    ].iloc[0]
    assert "GAUNTLET_081" in set(results["model"])
    assert 0.66 < proxy["spearman"] < 0.69
    assert 20 < proxy["rank_mae"] < 23
    gates = pd.read_csv(PACKET / "CHALLENGER_ACCEPTANCE_GATE_MATRIX.csv")
    candidate = gates[gates["candidate"] == "CANDIDATE_2"]
    assert len(candidate) == 20
    assert (candidate["result"] == "FAIL").sum() >= 6
    assert candidate.loc[candidate["gate"] == "NO_LOW_GAMES_INSTABILITY", "result"].item() == "FAIL"
    walk = pd.read_csv(PACKET / "WALK_FORWARD_RESULTS.csv")
    assert "CANDIDATE_0_CURRENT_BASELINE_PROXY" in set(walk["candidate"])
    assert "REFERENCE_PYF" in set(walk["candidate"])


def test_governed_candidate_count_and_missing_hq2_definition() -> None:
    definitions = pd.read_csv(PACKET / "CHALLENGER_DEFINITIONS.csv")
    assert len(definitions) == 4
    hq2 = definitions[definitions["candidate"] == "CANDIDATE_1"].iloc[0]
    assert hq2["status"] == "BLOCKED_MISSING_RECEIPT"
    assert "not found" in hq2["definition"]
    candidate3 = definitions[definitions["candidate"] == "CANDIDATE_3"].iloc[0]
    assert candidate3["status"] == "NOT_EVALUATED_NO_INVENTION"


def test_no_current_board_or_frozen_comparator_change() -> None:
    board = (
        ROOT / "docs/hq/model/current_board_deterministic_rebuild_with_recovery_inputs_v1_20260708/"
        "rebuilt_full_player_board_value_review_rows.csv"
    )
    assert hashlib.sha256(board.read_bytes()).hexdigest() == (
        "263cc8aa050c4670bf5ed22701d7b04801d143480c5630b98e00dd08d2968ce4"
    )
    simulation = pd.read_csv(PACKET / "CURRENT_BOARD_REVIEW_ONLY_SIMULATION.csv")
    assert simulation["production_write"].eq("NONE").all()
    proof = (PACKET / "PRODUCTION_RANKING_NO_CHANGE_PROOF.md").read_text(encoding="utf-8")
    assert "Production ranking change: `NONE`" in proof


def test_manifest_has_all_required_packet_files() -> None:
    manifest = json.loads((PACKET / "MANIFEST.json").read_text(encoding="utf-8"))
    assert manifest["exact_rows"] == 0
    assert manifest["production_ranking_change"] == "NONE"
    assert manifest["frozen_2026_change"] == "NONE"
    names = {item["path"] for item in manifest["files"]}
    assert len(names) == 27
    assert "VALIDATION_RESULTS.md" in names
    assert "DETERMINISTIC_REGENERATION_MANIFEST.csv" in names


def test_builder_contains_no_provider_or_localdata_access() -> None:
    text = SCRIPT.read_text(encoding="utf-8")
    assert "requests." not in text
    assert "http://" not in text
    assert "https://" not in text
    assert "local_exports" not in text
    assert 'on=["player_id", "season", "position"]' in text
