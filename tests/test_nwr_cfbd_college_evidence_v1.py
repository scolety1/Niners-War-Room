from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd

PACKET = Path(
    "docs/hq/master/nwr_cfbd_college_evidence_admission_v1_20260730"
)


def test_packet_manifest_reproduces_all_governed_artifacts() -> None:
    manifest = json.loads((PACKET / "MANIFEST.json").read_text(encoding="utf-8"))
    assert manifest["foundation_id"] == "NWR_NEW_EVIDENCE_FOUNDATION_V1"
    assert manifest["admission_id"] == "NWR_CFBD_COLLEGE_EVIDENCE_ADMISSION_V1"
    assert manifest["snapshot_aggregate_sha256"] == (
        "370ce01696c305f64792e45e1f8671cfb788b8419b257040206a6f14e5c2770a"
    )
    for artifact in manifest["artifacts"]:
        path = PACKET / artifact["path"]
        assert path.stat().st_size == artifact["bytes"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == artifact["sha256"]


def test_identity_partition_is_exact_or_explicitly_unresolved() -> None:
    exact = pd.read_csv(PACKET / "CFBD_EXACT_IDENTITY_CROSSWALK.csv")
    review = pd.read_csv(PACKET / "CFBD_REVIEW_ONLY_IDENTITY_CANDIDATES.csv")
    unresolved = pd.read_csv(PACKET / "CFBD_UNRESOLVED_IDENTITY_INVENTORY.csv")
    assert len(exact) == 1103
    assert len(review) == 0
    assert len(unresolved) == 1759
    assert exact["gsis_id"].is_unique
    assert exact["cfbd_college_athlete_id"].is_unique
    assert exact["identity_classification"].eq(
        "EXACT_DRAFT_SLOT_WITH_AUTHORITATIVE_CROSSWALK"
    ).all()
    assert ~exact["name_used_as_identity"].astype(bool).any()
    assert unresolved["identity_classification"].eq("UNRESOLVED").all()
    assert ~unresolved["name_used_as_identity"].astype(bool).any()


def test_college_features_are_exact_and_strictly_pre_draft() -> None:
    features = pd.read_csv(PACKET / "CFBD_COLLEGE_EVIDENCE_FOUNDATION.csv")
    exact = pd.read_csv(PACKET / "CFBD_EXACT_IDENTITY_CROSSWALK.csv")
    assert len(features) == 1044
    assert features["gsis_id"].is_unique
    assert set(features["gsis_id"]).issubset(set(exact["gsis_id"]))
    assert (
        features["college_terminal_season"] < features["draft_year"]
    ).all()
    assert not any("adp" in column.lower() for column in features.columns)


def test_fixed_incremental_audit_does_not_authorize_formula_redevelopment() -> None:
    decisions = pd.read_csv(PACKET / "INCREMENTAL_VALUE_DECISIONS.csv")
    assert len(decisions) == 5
    assert decisions["decision"].eq(
        "ADMIT_SOURCE_FEATURE_NOT_INCREMENTAL"
    ).all()
    contract = (PACKET / "MODEL_REENTRY_CONTRACT.md").read_text(encoding="utf-8")
    assert "Formula redevelopment and production integration remain closed" in contract
    assert "does not authorize a new" in contract
    assert "rookie formula or ranking" in contract


def test_mutation_sensitivity_fails_closed() -> None:
    mutations = pd.read_csv(PACKET / "MUTATION_SENSITIVITY_RESULTS.csv")
    assert len(mutations) == 28
    assert mutations["mutation"].is_unique
    assert mutations["result"].eq("PASS_FAIL_CLOSED").all()
    assert mutations["error_class"].str.endswith("Error").all()


def test_protected_release_identifiers_and_no_change_receipt() -> None:
    receipt = (
        PACKET / "FINISHED_V1_OUTCOME_V3_AND_STATE_NO_CHANGE.md"
    ).read_text(encoding="utf-8")
    assert "NWR_FINISHED_VERSION_1" in receipt
    assert "NWR_OUTCOME_COLUMNS_V3_RC1" in receipt
    assert "change `NONE`" in receipt
