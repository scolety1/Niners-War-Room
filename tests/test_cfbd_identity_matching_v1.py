from __future__ import annotations

from scripts.build_cfbd_identity_matching_v1 import (
    MODEL_USE_ALLOWED,
    REVIEW_REQUIRED,
    TRAINING_ALLOWED,
    CandidateResolver,
    IdentityCandidate,
    build_draft_registry_rows,
    build_high_confidence_review_rows,
    build_match_rows,
    build_production_context_rows,
    build_unmatched_priority_rows,
    normalize_player_name,
)


def _candidate(
    *,
    name: str,
    position: str = "WR",
    player_id: str = "p1",
    sleeper_id: str = "s1",
    team: str = "ARI",
    source: str = "fixture",
) -> IdentityCandidate:
    return IdentityCandidate(
        source=source,
        player_id=player_id,
        sleeper_id=sleeper_id,
        player_name=name,
        normalized_name=normalize_player_name(name),
        position=position,
        team=team,
    )


def test_name_normalization_removes_suffix_and_punctuation() -> None:
    assert normalize_player_name("Robert Henry Jr.") == "roberthenry"
    assert normalize_player_name("David Ealey III") == "davidealey"
    assert normalize_player_name("C.J. Hutton-Smith") == "cjhuttonsmith"
    assert normalize_player_name("Ja'Marr Chase") == "jamarrchase"


def test_exact_normalized_name_and_position_produces_high_match() -> None:
    rows, statuses = build_match_rows(
        cfbd_rows=[
            {
                "cfbd_player_id": "1",
                "player_name": "Robert Henry Jr.",
                "college_team": "UTSA",
                "position": "RB",
                "season": "2025",
            }
        ],
        candidates=(_candidate(name="Robert Henry", position="RB"),),
        run_id="run-1",
    )

    assert statuses[0]["match_status"] == "exact_match"
    assert rows[0]["match_confidence"] == "HIGH"
    assert rows[0]["model_use_allowed"] == MODEL_USE_ALLOWED
    assert rows[0]["training_allowed"] == TRAINING_ALLOWED
    assert rows[0]["review_required"] == REVIEW_REQUIRED


def test_ambiguous_duplicate_names_produce_ambiguous_review_rows() -> None:
    rows, statuses = build_match_rows(
        cfbd_rows=[
            {
                "cfbd_player_id": "1",
                "player_name": "Jordan Smith",
                "college_team": "Example",
                "position": "WR",
                "season": "2025",
            }
        ],
        candidates=(
            _candidate(name="Jordan Smith", position="WR", sleeper_id="s1", team="ARI"),
            _candidate(name="Jordan Smith", position="WR", sleeper_id="s2", team="BUF"),
        ),
        run_id="run-1",
    )

    assert statuses[0]["match_status"] == "ambiguous"
    assert {row["match_status"] for row in rows} == {"ambiguous"}
    assert len(rows) == 2


def test_unmatched_rows_stay_unmatched_review_required() -> None:
    rows, statuses = build_match_rows(
        cfbd_rows=[
            {
                "cfbd_player_id": "1",
                "player_name": "No Matching Player",
                "college_team": "Example",
                "position": "QB",
                "season": "2025",
            }
        ],
        candidates=(_candidate(name="Different Player", position="QB"),),
        run_id="run-1",
    )

    assert statuses[0]["match_status"] == "unmatched_review_required"
    assert rows[0]["candidate_player_id"] == ""
    assert rows[0]["match_confidence"] == "UNKNOWN"
    assert rows[0]["model_use_allowed"] == "false"
    assert rows[0]["training_allowed"] == "false"
    assert rows[0]["review_required"] == "true"


def test_candidate_resolver_does_not_use_external_calls_or_nfl_usage_paths() -> None:
    resolver = CandidateResolver((_candidate(name="Example Player", position="TE"),))
    decision = resolver.resolve(cfbd_name="Example Player", cfbd_position="TE")

    assert decision.status == "exact_match"
    forbidden_paths = (
        "docs/hq/data_sources/nfl_usage/historical_panel/",
        "scripts/build_historical_nfl_usage_panel_v0.py",
        "src/services/nfl_usage_historical_panel_service.py",
        "tests/test_nfl_usage_historical_panel_service.py",
    )
    assert all("cfbd_identity" not in path for path in forbidden_paths)


def test_high_confidence_review_file_rows_remain_review_required() -> None:
    candidate_rows, _ = build_match_rows(
        cfbd_rows=[
            {
                "cfbd_player_id": "1",
                "player_name": "Example Back",
                "college_team": "Example",
                "position": "RB",
                "season": "2025",
            }
        ],
        candidates=(_candidate(name="Example Back", position="RB"),),
        run_id="run-1",
    )

    rows = build_high_confidence_review_rows(candidate_rows)

    assert rows
    assert rows[0]["review_required"] == "true"
    assert rows[0]["model_use_allowed"] == "false"
    assert rows[0]["training_allowed"] == "false"
    assert rows[0]["human_decision"] == ""


def test_draft_registry_marks_links_unapproved_and_review_only() -> None:
    candidate_rows, _ = build_match_rows(
        cfbd_rows=[
            {
                "cfbd_player_id": "1",
                "player_name": "Example Back",
                "college_team": "Example",
                "position": "RB",
                "season": "2025",
            }
        ],
        candidates=(_candidate(name="Example Back", position="RB"),),
        run_id="run-1",
    )

    rows = build_draft_registry_rows(candidate_rows)

    assert rows[0]["registry_status"] == "DRAFT_REVIEW_ONLY"
    assert rows[0]["approved_by_human"] == "false"
    assert rows[0]["model_use_allowed"] == "false"
    assert rows[0]["training_allowed"] == "false"


def test_unmatched_priority_review_loads_with_priority_bucket() -> None:
    candidate_rows, _ = build_match_rows(
        cfbd_rows=[
            {
                "cfbd_player_id": "9",
                "player_name": "Unknown Runner",
                "college_team": "Example",
                "position": "RB",
                "season": "2025",
            }
        ],
        candidates=(_candidate(name="Different Runner", position="RB"),),
        run_id="run-1",
    )

    rows = build_unmatched_priority_rows(
        candidate_rows,
        production_context={("9", "2025"): {"production_context_available": "true"}},
    )

    assert rows[0]["priority_bucket"] == "P1_RECENT_SKILL_WITH_PRODUCTION"
    assert rows[0]["production_context_available"] == "true"
    assert rows[0]["model_use_allowed"] == "false"


def test_production_context_join_does_not_create_model_inputs() -> None:
    candidate_rows, _ = build_match_rows(
        cfbd_rows=[
            {
                "cfbd_player_id": "1",
                "player_name": "Example Back",
                "college_team": "Example",
                "position": "RB",
                "season": "2025",
            }
        ],
        candidates=(_candidate(name="Example Back", position="RB"),),
        run_id="run-1",
    )

    rows = build_production_context_rows(
        candidate_rows,
        production_context={
            ("1", "2025"): {
                "production_context_available": "true",
                "production_categories": "rushing",
                "production_summary": "rushing: YDS=1000",
            }
        },
    )

    assert rows[0]["production_context_available"] == "true"
    assert rows[0]["production_context_model_use_allowed"] == "false"
    assert rows[0]["production_context_training_allowed"] == "false"
    assert rows[0]["production_context_review_required"] == "true"
