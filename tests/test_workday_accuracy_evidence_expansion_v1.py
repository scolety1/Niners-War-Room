from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/build_workday_accuracy_evidence_expansion_v1.py"
PACKET = ROOT / "docs/hq/master/nwr_workday_accuracy_evidence_expansion_v1_20260723"


@pytest.fixture(scope="module")
def audit() -> Any:
    spec = importlib.util.spec_from_file_location("workday_accuracy_evidence_v1", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_valid_exact_claim_accepts(audit: Any) -> None:
    record, expected = audit.exact_claim_fixture()
    audit.validate_exact_claim(record, expected)


@pytest.mark.parametrize(
    "mutation",
    [
        "changed_score",
        "changed_rank",
        "changed_player_id",
        "removed_as_of_date",
        "changed_model_identifier",
        "missing_code_commit",
        "future_input",
        "current_only_adp",
        "name_based_join",
        "incomplete_checkpoint_chain",
        "mutable_claimed_immutable",
        "approximate_relabel",
        "nondeterministic_order",
        "silently_dropped_prediction",
    ],
)
def test_required_mutations_fail_closed(audit: Any, mutation: str) -> None:
    _record, expected = audit.exact_claim_fixture()
    with pytest.raises(RuntimeError):
        audit.validate_exact_claim(audit.mutation_cases()[mutation], expected)


def test_row_digest_is_order_independent(audit: Any) -> None:
    rows = [
        {"player_id": "b", "season": 2020, "position": "WR", "score": 1.0},
        {"player_id": "a", "season": 2020, "position": "WR", "score": 2.0},
    ]
    assert audit.canonical_row_digest(rows) == audit.canonical_row_digest(rows[::-1])


def test_packet_is_complete_and_self_authenticating(audit: Any) -> None:
    audit.validate_packet()
    manifest = json.loads((PACKET / "MANIFEST.json").read_text(encoding="utf-8"))
    assert manifest["exact_rows_before"] == 0
    assert manifest["exact_rows_after"] == 0
    assert manifest["proxy_to_exact"] == "PROXY_TO_EXACT_NOT_TESTABLE"
    assert (
        manifest["final_challenger_disposition"]
        == "NO_ACCURACY_CHALLENGER_ADMITTED"
    )
    assert manifest["production_ranking_change"] == "NONE"
    assert manifest["frozen_2026_change"] == "NONE"


def test_tracked_artifact_paths_are_worktree_independent() -> None:
    for name in (
        "RECOVERED_RECEIPT_INVENTORY.csv",
        "RECEIPT_AUTHENTICATION_AND_PROVENANCE.csv",
    ):
        frame = pd.read_csv(PACKET / name)
        key_column = "family" if "family" in frame.columns else "candidate"
        path_column = "artifact" if "artifact" in frame.columns else "path_or_object"
        comparator = frame.loc[
            frame[key_column] == "prospective_2026_comparator"
        ]
        assert len(comparator) == 1
        artifact = str(comparator.iloc[0][path_column])
        assert artifact.startswith("docs/hq/model/")
        assert "Niners-War-Room-workday-accuracy-evidence-expansion" not in artifact


def test_packet_csv_serialization_is_lf_stable() -> None:
    for path in PACKET.glob("*.csv"):
        assert b"\r\n" not in path.read_bytes()


def test_exactness_frontier_stays_fail_closed() -> None:
    frame = pd.read_csv(
        PACKET / "COMPONENT_LIFECYCLE_CONFIDENCE_SAFETY_FRONTIER.csv",
        low_memory=False,
    )
    assert len(frame) == 5518
    assert not frame["exact_primary_row"].astype(bool).any()
    assert not frame["exact_deterministic_regeneration_row"].astype(bool).any()
    assert not frame["mandatory_chain_complete"].astype(bool).any()
    assert frame["blocked_row"].astype(bool).all()


def test_manifest_material_unknowns_block_exact_admission() -> None:
    frame = pd.read_csv(PACKET / "AS_OF_MANIFEST_COMPLETENESS.csv")
    exact = frame.loc[
        frame["candidate_manifest"] == "exact_model_v4_historical_chain"
    ]
    assert exact["material_unknown"].eq(True).any()
    assert exact.loc[exact["material_unknown"].eq(True), "exact_admission"].eq(
        "BLOCKED"
    ).all()


def test_hq2_is_definition_only_and_low_games_gate_fails() -> None:
    results = pd.read_csv(PACKET / "CHALLENGER_DEFINITIONS_AND_RESULTS.csv")
    hq2 = results.loc[results["candidate"].str.contains("HQ2")].iloc[0]
    assert hq2["definition_status"] == "RECOVERED_EXACT"
    assert hq2["admission"] == "NOT_ADMITTED_NO_EXACT_MODEL_V4_OVERLAP"
    gates = pd.read_csv(PACKET / "CHALLENGER_ACCEPTANCE_GATE_MATRIX.csv")
    low_games = gates.loc[gates["gate"] == "low_games_stability"].iloc[0]
    assert low_games["candidate_1_hq2"] == "FAIL_PLUS_12_VS_PRIOR_YEAR"


def test_no_protected_or_opaque_artifact_is_in_packet_manifest() -> None:
    changed = pd.read_csv(PACKET / "FILES_CREATED_OR_CHANGED.csv")
    paths = changed["path"].astype(str)
    attributes = changed.loc[changed["path"] == ".gitattributes"]
    assert len(attributes) == 1
    assert attributes.iloc[0]["change_type"] == "MODIFIED"
    assert attributes.iloc[0]["scope"] == "research_tooling"
    assert not paths.str.startswith(
        ("src/", "app/", "local_exports/", "config/", "launcher/")
    ).any()
    opaque = {
        "dp_freshness_report.csv",
        "dp_market_baseline_context.csv",
        "dp_nwr_join_coverage.csv",
        "dp_pick_value_context.csv",
        "dp_playerid_crosswalk_audit.csv",
    }
    assert not paths.map(lambda value: Path(value).name in opaque).any()
