from __future__ import annotations

# ruff: noqa: E501
import argparse
import csv
import re
import unicodedata
from collections import Counter, defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from difflib import SequenceMatcher
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CFBD_INPUT = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "data_sources"
    / "cfbd_review_artifacts_20260624"
    / "cfbd_player_identity_review_queue.csv"
)
CFBD_PRODUCTION_INPUT = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "data_sources"
    / "cfbd_review_artifacts_20260624"
    / "cfbd_player_production_review.csv"
)
OUTPUT_ROOT = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "data_sources"
    / "cfbd_identity_matching_v1_20260624"
)

MODEL_USE_ALLOWED = "false"
TRAINING_ALLOWED = "false"
REVIEW_REQUIRED = "true"
SUPPORTED_POSITIONS = {"QB", "RB", "WR", "TE"}
POSITION_ALIASES = {
    "QUARTERBACK": "QB",
    "RUNNINGBACK": "RB",
    "RUNNING BACK": "RB",
    "WIDERECEIVER": "WR",
    "WIDE RECEIVER": "WR",
    "TIGHTEND": "TE",
    "TIGHT END": "TE",
}
EXPLICIT_NAME_ALIASES = {
    "kcconcepcion": "kevinconcepcion",
    "nicksingleton": "nicholassingleton",
}

CANDIDATE_COLUMNS = (
    "cfbd_row_id",
    "cfbd_player_id",
    "cfbd_player_name",
    "cfbd_normalized_name",
    "cfbd_college_team",
    "cfbd_position",
    "cfbd_season",
    "candidate_source",
    "candidate_player_id",
    "candidate_sleeper_id",
    "candidate_player_name",
    "candidate_normalized_name",
    "candidate_position",
    "candidate_team",
    "name_score",
    "position_match",
    "team_or_college_context_match",
    "match_status",
    "match_confidence",
    "review_required",
    "model_use_allowed",
    "training_allowed",
    "notes",
)

SUMMARY_COLUMNS = (
    "run_id",
    "run_timestamp",
    "source_rows",
    "candidate_rows",
    "exact_match_count",
    "strong_candidate_count",
    "possible_candidate_count",
    "ambiguous_count",
    "unmatched_count",
    "high_confidence_count",
    "medium_confidence_count",
    "low_confidence_count",
    "unknown_confidence_count",
    "review_required_count",
    "review_required",
    "model_use_allowed",
    "training_allowed",
    "notes",
)

HIGH_CONFIDENCE_COLUMNS = (
    "cfbd_player_id",
    "cfbd_player_name",
    "cfbd_college_team",
    "cfbd_position",
    "cfbd_season",
    "candidate_source",
    "candidate_player_id",
    "candidate_sleeper_id",
    "candidate_player_name",
    "candidate_position",
    "name_score",
    "match_status",
    "match_confidence",
    "recommended_review_action",
    "human_decision",
    "human_reviewer",
    "human_review_date",
    "review_note",
    "model_use_allowed",
    "training_allowed",
    "review_required",
)

POSSIBLE_REVIEW_COLUMNS = CANDIDATE_COLUMNS + (
    "ambiguity_reason",
    "recommended_review_action",
    "human_decision",
    "human_reviewer",
    "human_review_date",
    "review_note",
)

UNMATCHED_PRIORITY_COLUMNS = (
    "priority_bucket",
    "priority_reason",
    "cfbd_player_id",
    "cfbd_player_name",
    "cfbd_college_team",
    "cfbd_position",
    "cfbd_season",
    "production_context_available",
    "recruiting_context_available",
    "needs_identity_source",
    "recommended_review_action",
    "model_use_allowed",
    "training_allowed",
    "review_required",
)

DRAFT_REGISTRY_COLUMNS = (
    "cfbd_player_id",
    "candidate_player_id",
    "candidate_sleeper_id",
    "cfbd_player_name",
    "candidate_player_name",
    "match_confidence",
    "match_status",
    "registry_status",
    "approved_by_human",
    "model_use_allowed",
    "training_allowed",
    "notes",
)

DASHBOARD_COLUMNS = ("metric", "value", "notes")

PRODUCTION_CONTEXT_COLUMNS = CANDIDATE_COLUMNS + (
    "production_context_available",
    "production_categories",
    "production_summary",
    "production_context_model_use_allowed",
    "production_context_training_allowed",
    "production_context_review_required",
)

SOURCE_PRIORITY = {
    "unified_player_universe_consolidated": 90,
    "unified_player_universe_review": 80,
    "sleeper_current_context": 70,
    "player_id_coverage_audit": 60,
    "player_identity_manual_review_queue": 50,
    "dynastyprocess_display_crosswalk": 40,
    "frozen_final_board_v1": 30,
    "sample_2026_pre_declaration_dim_players": 20,
}


@dataclass(frozen=True)
class IdentityCandidate:
    source: str
    player_id: str
    sleeper_id: str
    player_name: str
    normalized_name: str
    position: str
    team: str

    @property
    def identity_key(self) -> str:
        if self.sleeper_id:
            return f"sleeper:{self.sleeper_id}"
        if self.player_id:
            return f"player:{self.player_id}"
        return f"name:{self.normalized_name}|pos:{self.position}|team:{self.team}"

    @property
    def logical_identity_key(self) -> str:
        return f"name:{self.normalized_name}|pos:{self.position}|team:{self.team}"


@dataclass(frozen=True)
class MatchDecision:
    candidates: tuple[IdentityCandidate, ...]
    scores: dict[str, int]
    status: str
    confidence: str
    notes: str


def main() -> int:
    parser = argparse.ArgumentParser(description="Build review-only CFBD identity matches.")
    parser.add_argument("--cfbd-input", type=Path, default=CFBD_INPUT)
    parser.add_argument("--production-input", type=Path, default=CFBD_PRODUCTION_INPUT)
    parser.add_argument("--output-root", type=Path, default=OUTPUT_ROOT)
    args = parser.parse_args()

    run_timestamp = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    run_id = f"cfbd_identity_matching_v1_20260624_{_timestamp_slug(run_timestamp)}"
    cfbd_rows = _read_rows(args.cfbd_input)
    production_context = load_production_context(args.production_input)
    candidates = build_identity_candidates(REPO_ROOT)
    candidate_rows, row_statuses = build_match_rows(
        cfbd_rows=cfbd_rows,
        candidates=candidates,
        run_id=run_id,
    )
    summary_rows = build_summary_rows(
        run_id=run_id,
        run_timestamp=run_timestamp,
        source_rows=len(cfbd_rows),
        candidate_rows=len(candidate_rows),
        row_statuses=row_statuses,
    )
    ambiguous_rows = [
        row
        for row in candidate_rows
        if row["match_status"] == "ambiguous" or row["match_confidence"] != "HIGH"
    ]
    unmatched_rows = [
        row for row in candidate_rows if row["match_status"] == "unmatched_review_required"
    ]
    high_confidence_rows = build_high_confidence_review_rows(candidate_rows)
    possible_review_rows = build_possible_review_rows(candidate_rows)
    unmatched_priority_rows = build_unmatched_priority_rows(
        unmatched_rows,
        production_context=production_context,
    )
    draft_registry_rows = build_draft_registry_rows(candidate_rows)
    production_review_rows = build_production_context_rows(
        candidate_rows,
        production_context=production_context,
    )
    dashboard_rows = build_dashboard_rows(
        source_rows=len(cfbd_rows),
        row_statuses=row_statuses,
        candidate_rows=candidate_rows,
        high_confidence_rows=high_confidence_rows,
        possible_review_rows=possible_review_rows,
        unmatched_priority_rows=unmatched_priority_rows,
        draft_registry_rows=draft_registry_rows,
        production_review_rows=production_review_rows,
    )

    args.output_root.mkdir(parents=True, exist_ok=True)
    _write_csv(args.output_root / "cfbd_identity_match_candidates.csv", CANDIDATE_COLUMNS, candidate_rows)
    _write_csv(args.output_root / "cfbd_identity_match_summary.csv", SUMMARY_COLUMNS, summary_rows)
    _write_csv(args.output_root / "cfbd_identity_ambiguous_review.csv", CANDIDATE_COLUMNS, ambiguous_rows)
    _write_csv(args.output_root / "cfbd_identity_unmatched_review.csv", CANDIDATE_COLUMNS, unmatched_rows)
    _write_csv(
        args.output_root / "cfbd_identity_high_confidence_review.csv",
        HIGH_CONFIDENCE_COLUMNS,
        high_confidence_rows,
    )
    _write_csv(
        args.output_root / "cfbd_identity_possible_review.csv",
        POSSIBLE_REVIEW_COLUMNS,
        possible_review_rows,
    )
    _write_csv(
        args.output_root / "cfbd_identity_unmatched_priority_review.csv",
        UNMATCHED_PRIORITY_COLUMNS,
        unmatched_priority_rows,
    )
    _write_csv(
        args.output_root / "cfbd_identity_link_registry_DRAFT.csv",
        DRAFT_REGISTRY_COLUMNS,
        draft_registry_rows,
    )
    _write_csv(
        args.output_root / "cfbd_identity_review_dashboard_summary.csv",
        DASHBOARD_COLUMNS,
        dashboard_rows,
    )
    _write_csv(
        args.output_root / "cfbd_identity_production_context_review.csv",
        PRODUCTION_CONTEXT_COLUMNS,
        production_review_rows,
    )
    _write_method_doc(args.output_root / "cfbd_identity_matching_method.md", candidates)
    _write_final_method_doc(
        args.output_root / "cfbd_identity_final_review_method.md",
        source_rows=len(cfbd_rows),
        high_count=len(high_confidence_rows),
        possible_count=len(possible_review_rows),
        unmatched_count=len(unmatched_priority_rows),
    )
    _write_readme(
        args.output_root / "README.md",
        run_id,
        len(cfbd_rows),
        len(candidate_rows),
        final_counts={
            "high_confidence_review": len(high_confidence_rows),
            "possible_or_ambiguous_review": len(possible_review_rows),
            "unmatched_priority_review": len(unmatched_priority_rows),
            "draft_registry": len(draft_registry_rows),
            "production_context_review": len(production_review_rows),
        },
    )
    print(
        {
            "run_id": run_id,
            "source_rows": len(cfbd_rows),
            "candidate_rows": len(candidate_rows),
            "high_confidence_review_rows": len(high_confidence_rows),
            "possible_or_ambiguous_review_rows": len(possible_review_rows),
            "unmatched_priority_rows": len(unmatched_priority_rows),
            "draft_registry_rows": len(draft_registry_rows),
            "production_context_rows": len(production_review_rows),
            "output_root": str(args.output_root),
        }
    )
    return 0


def normalize_player_name(value: object) -> str:
    text = str(value or "").strip()
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = text.replace("&", " and ")
    text = re.sub(r"\b(jr|sr|ii|iii|iv|v)\.?\b", "", text, flags=re.IGNORECASE)
    normalized = re.sub(r"[^a-zA-Z0-9]+", "", text).lower()
    return EXPLICIT_NAME_ALIASES.get(normalized, normalized)


def normalize_position(value: object) -> str:
    raw = _clean(value).upper()
    compact = re.sub(r"[^A-Z]+", "", raw)
    return POSITION_ALIASES.get(raw, POSITION_ALIASES.get(compact, raw))


def build_identity_candidates(repo_root: Path) -> tuple[IdentityCandidate, ...]:
    rows: list[IdentityCandidate] = []
    rows.extend(
        _candidates_from_csv(
            repo_root / "docs/hq/model/unified_player_universe_v0/unified_player_universe_v1_consolidated_review.csv",
            source="unified_player_universe_consolidated",
            name_col="player_name",
            pos_col="position",
            team_col="nfl_team",
            player_id_col="player_id",
            sleeper_id_col="player_id",
            normalized_col="normalized_name",
        )
    )
    rows.extend(
        _candidates_from_csv(
            repo_root / "docs/hq/model/unified_player_universe_v0/unified_player_universe_v1_review.csv",
            source="unified_player_universe_review",
            name_col="player_name",
            pos_col="position",
            team_col="nfl_team",
            player_id_col="player_id",
            sleeper_id_col="player_id",
            normalized_col="normalized_name",
        )
    )
    rows.extend(
        _candidates_from_csv(
            repo_root / "docs/hq/data_sources/current_context/sleeper_player_status_context_sample_or_current_v1.csv",
            source="sleeper_current_context",
            name_col="player",
            pos_col="pos",
            team_col="nfl_team",
            player_id_col="sleeper_player_id",
            sleeper_id_col="sleeper_player_id",
        )
    )
    rows.extend(
        _candidates_from_csv(
            repo_root / "docs/hq/data_sources/identity/player_id_coverage_audit_v1.csv",
            source="player_id_coverage_audit",
            name_col="player_name",
            pos_col="position",
            team_col="team",
            player_id_col="sleeper_id",
            sleeper_id_col="sleeper_id",
        )
    )
    rows.extend(
        _candidates_from_csv(
            repo_root / "docs/hq/data_sources/identity/player_identity_manual_review_queue_v1.csv",
            source="player_identity_manual_review_queue",
            name_col="player_name",
            pos_col="position",
            team_col="team",
            player_id_col="sleeper_id",
            sleeper_id_col="sleeper_id",
        )
    )
    rows.extend(
        _candidates_from_csv(
            repo_root / "docs/hq/parallel_lanes/dynastyprocess_market_baseline_20260622/dp_playerid_crosswalk_audit.csv",
            source="dynastyprocess_display_crosswalk",
            name_col="nwr_name",
            fallback_name_col="player",
            pos_col="nwr_pos",
            fallback_pos_col="pos",
            team_col="team",
            player_id_col="nwr_player_id",
            sleeper_id_col="sleeper_id",
        )
    )
    rows.extend(
        _candidates_from_csv(
            repo_root / "docs/draft_day_exports/final_board_v1_20260622/FINAL_DRAFT_BOARD_V1_FROZEN.csv",
            source="frozen_final_board_v1",
            name_col="player",
            pos_col="position",
            team_col="nfl_team",
            player_id_col="",
            sleeper_id_col="",
        )
    )
    rows.extend(
        _candidates_from_csv(
            repo_root / "sample_data/2026_pre_declaration/dim_players.csv",
            source="sample_2026_pre_declaration_dim_players",
            name_col="player_name",
            pos_col="position",
            team_col="nfl_team",
            player_id_col="player_id",
            sleeper_id_col="sleeper_id",
            normalized_col="merge_name",
        )
    )
    return _dedupe_candidates(rows)


def build_match_rows(
    *,
    cfbd_rows: list[dict[str, str]],
    candidates: tuple[IdentityCandidate, ...],
    run_id: str,
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    resolver = CandidateResolver(candidates)
    output: list[dict[str, str]] = []
    statuses: list[dict[str, str]] = []
    for index, row in enumerate(cfbd_rows, start=1):
        cfbd_row_id = f"cfbd-{index:06d}"
        decision = resolver.resolve(
            cfbd_name=row.get("player_name", ""),
            cfbd_position=row.get("position", ""),
        )
        statuses.append(
            {
                "cfbd_row_id": cfbd_row_id,
                "match_status": decision.status,
                "match_confidence": decision.confidence,
            }
        )
        if not decision.candidates:
            output.append(
                _match_row(
                    cfbd_row_id=cfbd_row_id,
                    cfbd_row=row,
                    candidate=None,
                    score=0,
                    status=decision.status,
                    confidence=decision.confidence,
                    notes=decision.notes,
                )
            )
            continue
        for candidate in decision.candidates:
            output.append(
                _match_row(
                    cfbd_row_id=cfbd_row_id,
                    cfbd_row=row,
                    candidate=candidate,
                    score=decision.scores[candidate.identity_key],
                    status=decision.status,
                    confidence=decision.confidence,
                    notes=decision.notes,
                )
            )
    return output, statuses


class CandidateResolver:
    def __init__(self, candidates: tuple[IdentityCandidate, ...]) -> None:
        self.by_name: dict[str, list[IdentityCandidate]] = defaultdict(list)
        self.by_position_first_letter: dict[tuple[str, str], list[IdentityCandidate]] = defaultdict(list)
        for candidate in candidates:
            self.by_name[candidate.normalized_name].append(candidate)
            first = candidate.normalized_name[:1]
            self.by_position_first_letter[(candidate.position, first)].append(candidate)

    def resolve(self, *, cfbd_name: str, cfbd_position: str) -> MatchDecision:
        normalized = normalize_player_name(cfbd_name)
        position = normalize_position(cfbd_position)
        if not normalized:
            return MatchDecision((), {}, "unmatched_review_required", "UNKNOWN", "Blank CFBD name.")

        exact_candidates = self.by_name.get(normalized, [])
        scored: dict[str, tuple[IdentityCandidate, int]] = {}
        for candidate in exact_candidates:
            score = 100 if _positions_compatible(position, candidate.position) else 95
            scored[candidate.identity_key] = (candidate, score)

        if not scored:
            for candidate in self.by_position_first_letter.get((position, normalized[:1]), []):
                score = int(round(SequenceMatcher(None, normalized, candidate.normalized_name).ratio() * 100))
                if score >= 88:
                    existing = scored.get(candidate.identity_key)
                    if existing is None or score > existing[1]:
                        scored[candidate.identity_key] = (candidate, score)

        if not scored:
            return MatchDecision(
                (),
                {},
                "unmatched_review_required",
                "UNKNOWN",
                "No normalized-name candidate reached the review threshold.",
            )

        ranked = sorted(
            scored.values(),
            key=lambda item: (
                item[1],
                _positions_compatible(position, item[0].position),
                item[0].source,
            ),
            reverse=True,
        )
        best_score = ranked[0][1]
        plausible = [item for item in ranked if item[1] >= max(88, best_score - 3)]
        candidates, scores = _representative_candidates(plausible)

        distinct_keys = {candidate.logical_identity_key for candidate in candidates}
        position_match = any(_positions_compatible(position, candidate.position) for candidate in candidates)
        if len(distinct_keys) > 1:
            return MatchDecision(
                candidates,
                scores,
                "ambiguous",
                "MEDIUM" if best_score >= 95 and position_match else "LOW",
                "Multiple plausible identity candidates require human review.",
            )
        if best_score == 100 and position_match:
            return MatchDecision(
                candidates,
                scores,
                "exact_match",
                "HIGH",
                "Exact normalized name and compatible position; still review-only.",
            )
        if best_score >= 95 and position_match:
            return MatchDecision(
                candidates,
                scores,
                "strong_candidate",
                "MEDIUM",
                "Strong normalized-name candidate; human review required.",
            )
        return MatchDecision(
            candidates,
            scores,
            "possible_candidate",
            "LOW",
            "Possible fuzzy candidate; human review required.",
        )


def _representative_candidates(
    plausible: list[tuple[IdentityCandidate, int]],
) -> tuple[tuple[IdentityCandidate, ...], dict[str, int]]:
    by_logical_key: dict[str, tuple[IdentityCandidate, int]] = {}
    for candidate, score in plausible:
        current = by_logical_key.get(candidate.logical_identity_key)
        rank = (score, SOURCE_PRIORITY.get(candidate.source, 0), bool(candidate.sleeper_id))
        current_rank = (
            (
                current[1],
                SOURCE_PRIORITY.get(current[0].source, 0),
                bool(current[0].sleeper_id),
            )
            if current
            else None
        )
        if current is None or rank > current_rank:
            by_logical_key[candidate.logical_identity_key] = (candidate, score)
    selected = tuple(
        item[0]
        for item in sorted(
            by_logical_key.values(),
            key=lambda item: (
                item[1],
                SOURCE_PRIORITY.get(item[0].source, 0),
                item[0].normalized_name,
            ),
            reverse=True,
        )
    )
    scores = {candidate.identity_key: by_logical_key[candidate.logical_identity_key][1] for candidate in selected}
    return selected, scores


def load_production_context(path: Path) -> dict[tuple[str, str], dict[str, str]]:
    context: dict[tuple[str, str], dict[str, str]] = {}
    if not path.exists():
        return context
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in _read_rows(path):
        key = (_clean(row.get("cfbd_player_id")), _clean(row.get("season")))
        if key[0] and key[1]:
            grouped[key].append(row)
    for key, rows in grouped.items():
        categories = sorted({_clean(row.get("stat_category")) for row in rows if row.get("stat_category")})
        summary_bits: list[str] = []
        for row in sorted(rows, key=lambda item: _clean(item.get("stat_category"))):
            category = _clean(row.get("stat_category"))
            stats = []
            for index in range(1, 6):
                name = _clean(row.get(f"stat_{index}_name"))
                value = _clean(row.get(f"stat_{index}_value"))
                if name and value:
                    stats.append(f"{name}={value}")
            if category and stats:
                summary_bits.append(f"{category}: " + "; ".join(stats[:3]))
        context[key] = {
            "production_context_available": "true",
            "production_categories": "|".join(categories),
            "production_summary": " | ".join(summary_bits[:3]),
        }
    return context


def build_high_confidence_review_rows(
    candidate_rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for row in candidate_rows:
        if row["match_status"] != "exact_match" or row["match_confidence"] != "HIGH":
            continue
        rows.append(
            {
                "cfbd_player_id": row["cfbd_player_id"],
                "cfbd_player_name": row["cfbd_player_name"],
                "cfbd_college_team": row["cfbd_college_team"],
                "cfbd_position": row["cfbd_position"],
                "cfbd_season": row["cfbd_season"],
                "candidate_source": row["candidate_source"],
                "candidate_player_id": row["candidate_player_id"],
                "candidate_sleeper_id": row["candidate_sleeper_id"],
                "candidate_player_name": row["candidate_player_name"],
                "candidate_position": row["candidate_position"],
                "name_score": row["name_score"],
                "match_status": row["match_status"],
                "match_confidence": row["match_confidence"],
                "recommended_review_action": "verify_identity_link_before_any_use",
                "human_decision": "",
                "human_reviewer": "",
                "human_review_date": "",
                "review_note": "High confidence remains review-only; not automatically approved.",
                "model_use_allowed": MODEL_USE_ALLOWED,
                "training_allowed": TRAINING_ALLOWED,
                "review_required": REVIEW_REQUIRED,
            }
        )
    return rows


def build_possible_review_rows(candidate_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for row in candidate_rows:
        if row["match_confidence"] == "HIGH":
            continue
        if row["match_status"] not in {"possible_candidate", "ambiguous"}:
            continue
        ambiguity_reason = (
            "multiple_plausible_candidate_identities"
            if row["match_status"] == "ambiguous"
            else "low_fuzzy_name_score_or_partial_context"
        )
        rows.append(
            {
                **row,
                "ambiguity_reason": ambiguity_reason,
                "recommended_review_action": "manual_compare_name_position_team_context",
                "human_decision": "",
                "human_reviewer": "",
                "human_review_date": "",
                "review_note": "Candidate requires human approval or rejection.",
            }
        )
    return rows


def build_unmatched_priority_rows(
    unmatched_rows: list[dict[str, str]],
    *,
    production_context: dict[tuple[str, str], dict[str, str]],
) -> list[dict[str, str]]:
    rows = [
        _unmatched_priority_row(row, production_context=production_context)
        for row in unmatched_rows
    ]
    return sorted(
        rows,
        key=lambda row: (
            _priority_order(row["priority_bucket"]),
            -_safe_int(row["cfbd_season"]),
            row["cfbd_position"],
            row["cfbd_player_name"],
        ),
    )


def build_draft_registry_rows(candidate_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for row in candidate_rows:
        if row["match_status"] not in {"exact_match", "possible_candidate", "ambiguous"}:
            continue
        rows.append(
            {
                "cfbd_player_id": row["cfbd_player_id"],
                "candidate_player_id": row["candidate_player_id"],
                "candidate_sleeper_id": row["candidate_sleeper_id"],
                "cfbd_player_name": row["cfbd_player_name"],
                "candidate_player_name": row["candidate_player_name"],
                "match_confidence": row["match_confidence"],
                "match_status": row["match_status"],
                "registry_status": "DRAFT_REVIEW_ONLY",
                "approved_by_human": "false",
                "model_use_allowed": MODEL_USE_ALLOWED,
                "training_allowed": TRAINING_ALLOWED,
                "notes": "Draft link registry only; not source truth and not model input.",
            }
        )
    return rows


def build_production_context_rows(
    candidate_rows: list[dict[str, str]],
    *,
    production_context: dict[tuple[str, str], dict[str, str]],
) -> list[dict[str, str]]:
    output: list[dict[str, str]] = []
    for row in candidate_rows:
        key = (row["cfbd_player_id"], row["cfbd_season"])
        context = production_context.get(key)
        if not context:
            continue
        output.append(
            {
                **row,
                **context,
                "production_context_model_use_allowed": MODEL_USE_ALLOWED,
                "production_context_training_allowed": TRAINING_ALLOWED,
                "production_context_review_required": REVIEW_REQUIRED,
            }
        )
    return output


def build_dashboard_rows(
    *,
    source_rows: int,
    row_statuses: list[dict[str, str]],
    candidate_rows: list[dict[str, str]],
    high_confidence_rows: list[dict[str, str]],
    possible_review_rows: list[dict[str, str]],
    unmatched_priority_rows: list[dict[str, str]],
    draft_registry_rows: list[dict[str, str]],
    production_review_rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    status_counts = Counter(row["match_status"] for row in row_statuses)
    confidence_counts = Counter(row["match_confidence"] for row in row_statuses)
    production_cfbd_ids = {
        (row["cfbd_player_id"], row["cfbd_season"]) for row in production_review_rows
    }
    metrics = [
        ("total CFBD rows", source_rows, "Input identity queue rows."),
        ("candidate rows", len(candidate_rows), "Review candidate CSV rows."),
        ("high confidence rows", confidence_counts["HIGH"], "Still human-review required."),
        ("medium confidence rows", confidence_counts["MEDIUM"], "Ambiguous rows."),
        ("low confidence rows", confidence_counts["LOW"], "Possible fuzzy candidates."),
        ("unknown confidence rows", confidence_counts["UNKNOWN"], "Unmatched rows."),
        ("unmatched rows", status_counts["unmatched_review_required"], "No candidate above threshold."),
        ("ambiguous rows", status_counts["ambiguous"], "Multiple plausible identities."),
        ("high confidence review rows", len(high_confidence_rows), "Exact-match review file rows."),
        ("possible or ambiguous review rows", len(possible_review_rows), "Manual review candidates."),
        ("unmatched priority rows", len(unmatched_priority_rows), "Prioritized unmatched review."),
        ("draft registry rows", len(draft_registry_rows), "Draft review-only registry rows."),
        ("rows with production context", len(production_cfbd_ids), "CFBD production context available."),
        ("rows with recruiting context", 0, "No row-level recruiting artifact exists in V1."),
        ("rows requiring human review", source_rows, "All rows require human review."),
        ("rows approved for model use", 0, "Must remain zero in V1."),
    ]
    return [
        {"metric": metric, "value": str(value), "notes": notes}
        for metric, value, notes in metrics
    ]


def _unmatched_priority_row(
    row: dict[str, str],
    *,
    production_context: dict[tuple[str, str], dict[str, str]],
) -> dict[str, str]:
    key = (row["cfbd_player_id"], row["cfbd_season"])
    has_production = key in production_context
    is_skill = row["cfbd_position"] in SUPPORTED_POSITIONS
    season = _safe_int(row["cfbd_season"])
    if has_production and is_skill and season >= 2025:
        bucket = "P1_RECENT_SKILL_WITH_PRODUCTION"
    elif has_production and is_skill:
        bucket = "P2_SKILL_WITH_PRODUCTION"
    elif is_skill and season >= 2025:
        bucket = "P3_RECENT_SKILL_NO_PRODUCTION"
    elif has_production:
        bucket = "P4_OTHER_WITH_PRODUCTION"
    else:
        bucket = "P5_OTHER_UNMATCHED"
    reason_parts = []
    if is_skill:
        reason_parts.append("offensive_skill_position")
    if has_production:
        reason_parts.append("production_context_available")
    if season >= 2025:
        reason_parts.append("recent_cfbd_season")
    if not reason_parts:
        reason_parts.append("identity_source_needed")
    return {
        "priority_bucket": bucket,
        "priority_reason": ";".join(reason_parts),
        "cfbd_player_id": row["cfbd_player_id"],
        "cfbd_player_name": row["cfbd_player_name"],
        "cfbd_college_team": row["cfbd_college_team"],
        "cfbd_position": row["cfbd_position"],
        "cfbd_season": row["cfbd_season"],
        "production_context_available": str(has_production).lower(),
        "recruiting_context_available": "false",
        "needs_identity_source": "true",
        "recommended_review_action": "search_existing_identity_sources_or_defer",
        "model_use_allowed": MODEL_USE_ALLOWED,
        "training_allowed": TRAINING_ALLOWED,
        "review_required": REVIEW_REQUIRED,
    }


def _priority_order(value: str) -> int:
    order = {
        "P1_RECENT_SKILL_WITH_PRODUCTION": 1,
        "P2_SKILL_WITH_PRODUCTION": 2,
        "P3_RECENT_SKILL_NO_PRODUCTION": 3,
        "P4_OTHER_WITH_PRODUCTION": 4,
        "P5_OTHER_UNMATCHED": 5,
    }
    return order.get(value, 99)


def build_summary_rows(
    *,
    run_id: str,
    run_timestamp: str,
    source_rows: int,
    candidate_rows: int,
    row_statuses: list[dict[str, str]],
) -> list[dict[str, str]]:
    status_counts = Counter(row["match_status"] for row in row_statuses)
    confidence_counts = Counter(row["match_confidence"] for row in row_statuses)
    return [
        {
            "run_id": run_id,
            "run_timestamp": run_timestamp,
            "source_rows": str(source_rows),
            "candidate_rows": str(candidate_rows),
            "exact_match_count": str(status_counts["exact_match"]),
            "strong_candidate_count": str(status_counts["strong_candidate"]),
            "possible_candidate_count": str(status_counts["possible_candidate"]),
            "ambiguous_count": str(status_counts["ambiguous"]),
            "unmatched_count": str(status_counts["unmatched_review_required"]),
            "high_confidence_count": str(confidence_counts["HIGH"]),
            "medium_confidence_count": str(confidence_counts["MEDIUM"]),
            "low_confidence_count": str(confidence_counts["LOW"]),
            "unknown_confidence_count": str(confidence_counts["UNKNOWN"]),
            "review_required_count": str(source_rows),
            "review_required": REVIEW_REQUIRED,
            "model_use_allowed": MODEL_USE_ALLOWED,
            "training_allowed": TRAINING_ALLOWED,
            "notes": "Review-only CFBD identity candidates; no source-truth promotion.",
        }
    ]


def _match_row(
    *,
    cfbd_row_id: str,
    cfbd_row: dict[str, str],
    candidate: IdentityCandidate | None,
    score: int,
    status: str,
    confidence: str,
    notes: str,
) -> dict[str, str]:
    cfbd_position = normalize_position(cfbd_row.get("position", ""))
    position_match = (
        str(_positions_compatible(cfbd_position, candidate.position)).lower() if candidate else "false"
    )
    context_match = "unknown"
    if candidate and candidate.team and candidate.team == _clean(cfbd_row.get("college_team")).upper():
        context_match = "true"
    elif candidate and candidate.team:
        context_match = "not_comparable_nfl_team_vs_college"
    return {
        "cfbd_row_id": cfbd_row_id,
        "cfbd_player_id": _clean(cfbd_row.get("cfbd_player_id")),
        "cfbd_player_name": _clean(cfbd_row.get("player_name")),
        "cfbd_normalized_name": normalize_player_name(cfbd_row.get("player_name")),
        "cfbd_college_team": _clean(cfbd_row.get("college_team")),
        "cfbd_position": cfbd_position,
        "cfbd_season": _clean(cfbd_row.get("season")),
        "candidate_source": candidate.source if candidate else "",
        "candidate_player_id": candidate.player_id if candidate else "",
        "candidate_sleeper_id": candidate.sleeper_id if candidate else "",
        "candidate_player_name": candidate.player_name if candidate else "",
        "candidate_normalized_name": candidate.normalized_name if candidate else "",
        "candidate_position": candidate.position if candidate else "",
        "candidate_team": candidate.team if candidate else "",
        "name_score": str(score),
        "position_match": position_match,
        "team_or_college_context_match": context_match,
        "match_status": status,
        "match_confidence": confidence,
        "review_required": REVIEW_REQUIRED,
        "model_use_allowed": MODEL_USE_ALLOWED,
        "training_allowed": TRAINING_ALLOWED,
        "notes": f"{notes} Not source truth; not model input.",
    }


def _candidates_from_csv(
    path: Path,
    *,
    source: str,
    name_col: str,
    pos_col: str,
    team_col: str,
    player_id_col: str,
    sleeper_id_col: str,
    normalized_col: str = "",
    fallback_name_col: str = "",
    fallback_pos_col: str = "",
) -> list[IdentityCandidate]:
    output: list[IdentityCandidate] = []
    if not path.exists():
        return output
    for row in _read_rows(path):
        name = _clean(row.get(name_col)) or _clean(row.get(fallback_name_col))
        position = normalize_position(row.get(pos_col) or row.get(fallback_pos_col))
        if position and position not in SUPPORTED_POSITIONS:
            continue
        normalized = normalize_player_name(row.get(normalized_col) or name)
        if not name or not normalized:
            continue
        output.append(
            IdentityCandidate(
                source=source,
                player_id=_clean(row.get(player_id_col)) if player_id_col else "",
                sleeper_id=_clean(row.get(sleeper_id_col)) if sleeper_id_col else "",
                player_name=name,
                normalized_name=normalized,
                position=position,
                team=_clean(row.get(team_col)).upper(),
            )
        )
    return output


def _dedupe_candidates(candidates: Iterable[IdentityCandidate]) -> tuple[IdentityCandidate, ...]:
    by_key: dict[tuple[str, str, str, str, str, str], IdentityCandidate] = {}
    for candidate in candidates:
        key = (
            candidate.source,
            candidate.player_id,
            candidate.sleeper_id,
            candidate.normalized_name,
            candidate.position,
            candidate.team,
        )
        by_key[key] = candidate
    return tuple(sorted(by_key.values(), key=lambda item: (item.normalized_name, item.source)))


def _positions_compatible(left: str, right: str) -> bool:
    if not left or not right:
        return False
    return normalize_position(left) == normalize_position(right)


def _write_method_doc(path: Path, candidates: tuple[IdentityCandidate, ...]) -> None:
    source_counts = Counter(candidate.source for candidate in candidates)
    source_lines = [f"- {source}: {count} candidate rows" for source, count in sorted(source_counts.items())]
    lines = [
        "# CFBD Identity Matching V1 Method",
        "",
        "## Source Inputs Used",
        "",
        "- `docs/hq/data_sources/cfbd_review_artifacts_20260624/cfbd_player_identity_review_queue.csv`",
        "- Unified player universe review/consolidated review artifacts",
        "- Sleeper current-context status artifact",
        "- Player ID coverage audit and manual identity review queue",
        "- DynastyProcess display-only crosswalk audit",
        "- Frozen Final Draft Board V1 as display-only identity context",
        "- Sample 2026 pre-declaration `dim_players.csv` reference rows",
        "",
        "## Candidate Source Counts",
        "",
        *source_lines,
        "",
        "## Normalization Rules",
        "",
        "- Unicode text is converted to ASCII where possible.",
        "- Ampersands are normalized to `and`.",
        "- Suffixes `Jr.`, `Sr.`, `II`, `III`, `IV`, and `V` are removed for matching.",
        "- Punctuation, apostrophes, hyphens, whitespace, and symbols are removed.",
        "- Names are lowercased and compared as compact normalized strings.",
        "- Existing aliases for `KC Concepcion` and `Nick Singleton` are preserved.",
        "",
        "## Scoring Rules",
        "",
        "- Exact normalized name and compatible position: name score `100`.",
        "- Exact normalized name with position mismatch or missing position context: name score `95`.",
        "- Fuzzy fallback uses Python `SequenceMatcher` among same-position, same-first-letter candidates.",
        "- Fuzzy candidates below score `88` are treated as unmatched.",
        "",
        "## Match Status And Confidence",
        "",
        "- `exact_match` / `HIGH`: one identity candidate, exact normalized name, compatible position.",
        "- `strong_candidate` / `MEDIUM`: one strong candidate requiring review.",
        "- `possible_candidate` / `LOW`: fuzzy candidate requiring review.",
        "- `ambiguous` / `MEDIUM` or `LOW`: multiple plausible identities require review.",
        "- `unmatched_review_required` / `UNKNOWN`: no candidate reached threshold.",
        "",
        "## Review-Only Guardrail",
        "",
        "All outputs are review-only identity suggestions. They are not source truth, not model input,",
        "not training truth, and not candidate/rank outputs. Even `HIGH` confidence rows require human",
        "review before any future promotion.",
        "",
        "## Known Limitations",
        "",
        "- CFBD college team is not directly comparable to current NFL team for most candidates.",
        "- Transfer history and draft-year context are not resolved in V1.",
        "- Matching uses existing tracked artifacts only and does not repull CFBD or Sleeper.",
        "- Ambiguous common names remain intentionally visible for human review.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_final_method_doc(
    path: Path,
    *,
    source_rows: int,
    high_count: int,
    possible_count: int,
    unmatched_count: int,
) -> None:
    lines = [
        "# CFBD Identity Matching V1 Final Review Method",
        "",
        "## How To Use This Package",
        "",
        "Start with `cfbd_identity_review_dashboard_summary.csv`, then review the focused CSVs in this order:",
        "",
        "1. `cfbd_identity_high_confidence_review.csv`",
        "2. `cfbd_identity_possible_review.csv`",
        "3. `cfbd_identity_unmatched_priority_review.csv`",
        "4. `cfbd_identity_link_registry_DRAFT.csv`",
        "",
        "The draft registry is a work queue, not source truth. Human reviewers should fill the blank",
        "`human_decision`, `human_reviewer`, `human_review_date`, and `review_note` fields in a future",
        "review lane or copied review sheet. This package itself does not approve any link.",
        "",
        "## Why HIGH Is Not Automatically Approved",
        "",
        "`HIGH` means the normalized CFBD name and position align with one existing NWR/Sleeper reference.",
        "It does not verify transfer history, draft class timing, NFL landing spot, duplicate identities, or",
        "whether the existing source should be treated as authoritative for CFBD. Every row remains",
        "`review_required=true`.",
        "",
        "## What Humans Should Approve Or Reject Later",
        "",
        "- Approve only when the CFBD player and candidate identity are clearly the same person.",
        "- Reject when names are aliases/collisions or college/NFL context conflicts.",
        "- Defer when more identity evidence is needed.",
        "- Never use production stats alone to approve identity.",
        "",
        "## Why Unmatched Rows Are Expected",
        "",
        "The CFBD roster covers broad college football rosters, while NWR/Sleeper/final-board sources cover a",
        "smaller fantasy/draft-relevant universe. Most CFBD rows should remain unmatched in V1.",
        "",
        "## Why This Is Not Model Input",
        "",
        "All outputs keep `model_use_allowed=false`, `training_allowed=false`, and `review_required=true`.",
        "No candidate rank, Dynasty Rank, final board rank, tiers, source truth, or model feature files are",
        "created or changed.",
        "",
        "## Counts",
        "",
        f"- Source CFBD rows: {source_rows}",
        f"- High-confidence review rows: {high_count}",
        f"- Possible/ambiguous review rows: {possible_count}",
        f"- Unmatched priority rows: {unmatched_count}",
        "",
        "## CFBD Identity Matching V2 Next Steps",
        "",
        "- Add a human-review workflow for approve/reject/defer decisions.",
        "- Add row-level recruiting context only if a tracked review-only recruiting artifact exists.",
        "- Add transfer/team-season context before any source-truth promotion.",
        "- Design a separate promotion gate after manual review and backtesting requirements are defined.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_readme(
    path: Path,
    run_id: str,
    source_rows: int,
    candidate_rows: int,
    *,
    final_counts: dict[str, int],
) -> None:
    lines = [
        "# CFBD Identity Matching V1 - 2026-06-24",
        "",
        f"Run ID: `{run_id}`",
        f"Input CFBD identity rows: {source_rows}",
        f"Candidate output rows: {candidate_rows}",
        "",
        "## Final Review Files",
        "",
        f"- `cfbd_identity_high_confidence_review.csv`: {final_counts['high_confidence_review']} rows",
        f"- `cfbd_identity_possible_review.csv`: {final_counts['possible_or_ambiguous_review']} rows",
        f"- `cfbd_identity_unmatched_priority_review.csv`: {final_counts['unmatched_priority_review']} rows",
        f"- `cfbd_identity_link_registry_DRAFT.csv`: {final_counts['draft_registry']} rows",
        f"- `cfbd_identity_production_context_review.csv`: {final_counts['production_context_review']} rows",
        "- `cfbd_identity_review_dashboard_summary.csv`",
        "- `cfbd_identity_final_review_method.md`",
        "",
        "This folder contains review-only identity matching suggestions.",
        "",
        "- Not source truth.",
        "- Not model input.",
        "- Not training truth.",
        "- Human review is required before any future use.",
        "- `model_use_allowed=false`.",
        "- `training_allowed=false`.",
        "- `review_required=true`.",
        "",
        "Suggested review workflow: review high-confidence rows first, then ambiguous/possible rows, then",
        "the unmatched priority queue. The draft registry must not be treated as approved identity truth.",
        "",
        "The CFBD identity lane is separate from nflverse and the active NFL usage/data-loader lane.",
        "No CFBD rows are promoted into rankings, model features, candidates, or source-truth files.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, columns: tuple[str, ...], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _clean(value: object) -> str:
    return str(value or "").strip()


def _safe_int(value: object) -> int:
    try:
        return int(str(value or "").strip())
    except ValueError:
        return 0


def _timestamp_slug(value: str) -> str:
    return value.replace("-", "").replace(":", "")


if __name__ == "__main__":
    raise SystemExit(main())
