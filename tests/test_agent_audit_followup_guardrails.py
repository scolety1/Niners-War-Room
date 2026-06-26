from __future__ import annotations

import csv
import importlib
import py_compile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "docs" / "hq" / "audits" / "agent_audit_synthesis_20260626"
REGISTRY_PATH = ROOT / "docs" / "hq" / "integration" / "evidence_status_registry_v1_20260626.csv"
MORNING_DIR = ROOT / "docs" / "hq" / "review_queue" / "morning_review_20260626"
COMPLETION_DIR = ROOT / "docs" / "hq" / "review_queue" / "full_refresh_stats_completion_20260626"


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def _by_name(rows: list[dict[str, str]], column: str) -> dict[str, dict[str, str]]:
    return {row[column]: row for row in rows}


def _is_no(value: str) -> bool:
    return value.strip().lower() in {"", "no", "false", "0", "none", "not_applicable", "n/a"}


def test_required_followup_docs_exist() -> None:
    expected = [
        "critical_service_test_mapping_20260626.csv",
        "local_preflight_guardrail_checklist_20260626.md",
        "NWR_AUDIT_INTAKE_SAFE_QA_FOLLOWUPS_20260626.md",
    ]
    for name in expected:
        assert (AUDIT_DIR / name).exists(), name


def test_key_evidence_lanes_keep_model_training_and_app_gates_closed() -> None:
    rows = _by_name(_rows(REGISTRY_PATH), "evidence_lane")
    lanes = [
        "CFBD Identity Matching V1",
        "NFL Usage Evidence Layer V0",
        "NFL Usage Promotion Gate V0",
        "Historical NFL Usage Panel V0",
        "NFL Usage Target Backtest V0",
        "Unified Player Universe Review V1",
        "DynastyProcess Market Baseline",
        "Outcome Columns V1",
        "Historical Drop Lists / Proxy Evidence",
        "College/Rookie CFBD Lane Status",
        "Full Refresh Stats Completion Gate V1",
    ]

    for lane in lanes:
        row = rows[lane]
        assert _is_no(row["model_input_allowed"]), lane
        assert _is_no(row["app_wiring_allowed"]), lane
        assert _is_no(row["training_allowed"]), lane
        assert _is_no(row["raw_data_tracked"]), lane

    assert rows["DynastyProcess Market Baseline"]["display_only_allowed"].lower() == "yes"
    assert rows["Outcome Columns V1"]["display_only_allowed"].lower() == "yes"
    proxy_notes = rows["Historical Drop Lists / Proxy Evidence"]["notes"].lower()
    assert "training truth" in proxy_notes


def test_nfl_usage_blocked_fields_and_display_candidates_stay_non_model() -> None:
    promotion = _by_name(
        _rows(MORNING_DIR / "nfl_usage_promotion_review_queue_v1.csv"),
        "field_name",
    )
    for field in ["true_routes_run", "true_tprr", "true_yprr"]:
        row = promotion[field]
        assert row["current_status"] == "BLOCKED_LICENSED_DATA_GAP"
        assert row["safe_default"] == "Keep blocked"
        assert _is_no(row["model_input_allowed"])
        assert _is_no(row["app_wiring_allowed"])

    market_row = promotion["ranks_projections_adp_market_vendor_values"]
    assert market_row["current_status"] == "BLOCKED_UNSAFE"
    assert _is_no(market_row["model_input_allowed"])
    assert _is_no(market_row["app_wiring_allowed"])

    field_safety = _by_name(
        _rows(COMPLETION_DIR / "nfl_usage_field_safety_decisions.csv"),
        "field_name",
    )
    for field in ["red_zone_opportunities", "inside_10_opportunities", "inside_5_opportunities"]:
        row = field_safety[field]
        assert row["source_status"] == "DISPLAY_ONLY_CANDIDATE"
        assert row["safe_for_display_only"].startswith("conditional")
        assert _is_no(row["safe_for_model_input"])
        assert row["decision"] == "KEEP_REVIEW_ONLY_DISPLAY_CANDIDATE"

    for field in ["true_routes_run", "true_tprr", "true_yprr"]:
        row = field_safety[field]
        assert row["source_status"] == "BLOCKED_LICENSED_DATA_GAP"
        assert _is_no(row["safe_for_display_only"])
        assert _is_no(row["safe_for_model_input"])


def test_cfbd_review_artifacts_keep_review_flags_closed() -> None:
    cfbd_files = [
        ROOT
        / "docs"
        / "hq"
        / "data_sources"
        / "cfbd_review_artifacts_20260624"
        / "cfbd_player_identity_review_queue.csv",
        ROOT
        / "docs"
        / "hq"
        / "data_sources"
        / "cfbd_review_artifacts_20260624"
        / "cfbd_player_production_review.csv",
        ROOT
        / "docs"
        / "hq"
        / "data_sources"
        / "cfbd_identity_matching_v1_20260624"
        / "cfbd_identity_link_registry_DRAFT.csv",
        ROOT
        / "docs"
        / "hq"
        / "review_queue"
        / "morning_review_20260626"
        / "cfbd_identity_review_queue_v1.csv",
        ROOT
        / "docs"
        / "hq"
        / "review_queue"
        / "full_refresh_stats_completion_20260626"
        / "cfbd_ambiguous_identity_decisions.csv",
    ]
    guarded_columns = ["model_use_allowed", "training_allowed", "approved_by_human"]

    for path in cfbd_files:
        rows = _rows(path)
        assert rows, path
        for row in rows:
            for column in guarded_columns:
                if column in row:
                    assert _is_no(row[column]), f"{path.name} {column} {row[column]!r}"
            if "review_required" in row:
                assert row["review_required"].strip().lower() in {"yes", "true", "1"}


def test_missingness_remains_not_enough_information_or_blocked() -> None:
    blockers = _rows(MORNING_DIR / "unified_universe_blocker_review_queue_v1.csv")
    missing_id = [row for row in blockers if row["blocker_type"] == "MISSING_PLAYER_ID"]
    missing_age = [row for row in blockers if row["blocker_type"] == "MISSING_AGE"]
    assert len(missing_id) == 5
    assert missing_age
    for row in missing_id:
        assert "do not fabricate id" in row["safe_default"].lower()
        assert _is_no(row["model_input_allowed"])
        assert _is_no(row["app_wiring_allowed"])
    for row in missing_age:
        assert row["safe_default"] == "Keep age as Not enough information"
        assert _is_no(row["model_input_allowed"])
        assert _is_no(row["app_wiring_allowed"])

    age_decisions = _rows(COMPLETION_DIR / "age_gap_and_conflict_decisions.csv")
    assert any(row["player_name"] == "Joshua Palmer" for row in age_decisions)
    for row in age_decisions:
        if row["proposed_display_age"] == "Not enough information":
            assert _is_no(row["model_use_allowed"])
            assert _is_no(row["training_allowed"])
            assert row["review_required"].lower() == "yes"

    injury_rows = _rows(
        ROOT / "docs" / "hq" / "draft_day_v2" / "injury_per_game_risk_audit_20260623.csv"
    )
    for row in injury_rows:
        if row["current_injury_status_available"].strip().lower() == "no":
            status = row["current_injury_status"].lower()
            blocked_terms = {"healthy", "clean", "low-risk", "low risk", "0", "average"}
            assert status not in blocked_terms
            assert "healthy" not in status
            assert "low risk" not in status

    summary_rows = _rows(
        ROOT
        / "docs"
        / "hq"
        / "model"
        / "evaluation_v0"
        / "NWR_MODEL_EVALUATION_SUMMARY_V0_20260623.csv"
    )
    outcome_rows = [row for row in summary_rows if row["evaluation_area"] == "outcome"]
    assert outcome_rows
    assert any("Not enough information" in row["notes"] for row in outcome_rows)
    assert all(
        "not zero" in row["notes"].lower() or row["metric"] != "unsupported_or_missing_rows"
        for row in outcome_rows
    )


def test_decision_pages_do_not_wire_review_only_evidence_roots() -> None:
    decision_pages = [
        "05_rankings.py",
        "18_cheat_sheets_v2.py",
        "19_drafting_mode_v2.py",
        "21_live_draft_room_v1.py",
        "22_player_compare_v1.py",
        "23_trading_lab_v1.py",
        "24_mock_draft_v1.py",
        "29_post_draft_mode_v2.py",
    ]
    forbidden_tokens = [
        "cfbd_identity_matching_v1_20260624",
        "cfbd_review_artifacts_20260624",
        "docs/hq/data_sources/nfl_usage",
        "full_refresh_stats_completion_20260626",
        "evidence_status_registry_v1_20260626",
        "NFL Usage Evidence Layer V0",
        "CFBD Identity Matching V1",
    ]

    for page in decision_pages:
        text = (ROOT / "app" / "pages" / page).read_text(encoding="utf-8")
        for token in forbidden_tokens:
            assert token not in text, f"{page} unexpectedly references {token}"


def test_critical_service_test_mapping_is_explicit_and_current() -> None:
    mapping_path = AUDIT_DIR / "critical_service_test_mapping_20260626.csv"
    rows = _rows(mapping_path)
    assert rows
    allowed = {"COVERED", "PARTIAL", "WAIVED"}
    for row in rows:
        assert row["coverage_status"] in allowed
        assert (ROOT / row["service_path"]).exists(), row["service_path"]
        if row["coverage_status"] in {"COVERED", "PARTIAL"}:
            assert (ROOT / row["test_path"]).exists(), row["test_path"]
        partial_critical = (
            row["criticality"] in {"P0", "P1"} and row["coverage_status"] == "PARTIAL"
        )
        if row["coverage_status"] == "WAIVED" or partial_critical:
            assert row["waiver_reason"].strip()


def test_representative_services_import_and_pages_compile() -> None:
    service_modules = [
        "src.services.data_refresh_orchestrator_service",
        "src.services.data_health_dashboard_service",
        "src.services.evidence_integration_review_service",
        "src.services.draft_day_runtime_state_service",
        "src.services.draft_day_workflow_service",
        "src.services.market_baseline_service",
        "src.services.player_compare_decision_service",
        "src.services.nfl_usage_evidence_review_page_service",
        "src.services.unified_player_universe_review_page_service",
    ]
    for module_name in service_modules:
        importlib.import_module(module_name)

    page_files = [
        ROOT / "app" / "pages" / "05_rankings.py",
        ROOT / "app" / "pages" / "21_live_draft_room_v1.py",
        ROOT / "app" / "pages" / "22_player_compare_v1.py",
        ROOT / "app" / "pages" / "23_trading_lab_v1.py",
        ROOT / "app" / "pages" / "28_settings_data_health_v1.py",
        ROOT / "app" / "pages" / "31_unified_universe_review_v1.py",
        ROOT / "app" / "pages" / "32_nfl_usage_evidence_review.py",
        ROOT / "app" / "pages" / "33_evidence_integration_review_v1.py",
    ]
    for page in page_files:
        py_compile.compile(str(page), doraise=True)


def test_local_preflight_checklist_mentions_required_scans() -> None:
    checklist = (AUDIT_DIR / "local_preflight_guardrail_checklist_20260626.md").read_text(
        encoding="utf-8"
    )
    required_terms = [
        "pytest",
        "ruff",
        "protected artifact diff",
        "raw/shared/local/export/secret tracking scan",
        "blocked-field scanner",
        "absolute path scan",
        "git diff --check",
        "C:\\NWR_SHARED_DATA",
        "C:\\NWR_LOCAL_SECRETS",
        "local_exports",
    ]
    lower = checklist.lower()
    for term in required_terms:
        assert term.lower() in lower
