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
    parser.add_argument("--output-root", type=Path, default=OUTPUT_ROOT)
    args = parser.parse_args()

    run_timestamp = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    run_id = f"cfbd_identity_matching_v1_20260624_{_timestamp_slug(run_timestamp)}"
    cfbd_rows = _read_rows(args.cfbd_input)
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

    args.output_root.mkdir(parents=True, exist_ok=True)
    _write_csv(args.output_root / "cfbd_identity_match_candidates.csv", CANDIDATE_COLUMNS, candidate_rows)
    _write_csv(args.output_root / "cfbd_identity_match_summary.csv", SUMMARY_COLUMNS, summary_rows)
    _write_csv(args.output_root / "cfbd_identity_ambiguous_review.csv", CANDIDATE_COLUMNS, ambiguous_rows)
    _write_csv(args.output_root / "cfbd_identity_unmatched_review.csv", CANDIDATE_COLUMNS, unmatched_rows)
    _write_method_doc(args.output_root / "cfbd_identity_matching_method.md", candidates)
    _write_readme(args.output_root / "README.md", run_id, len(cfbd_rows), len(candidate_rows))
    print(
        {
            "run_id": run_id,
            "source_rows": len(cfbd_rows),
            "candidate_rows": len(candidate_rows),
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
        candidates = tuple(item[0] for item in plausible)
        scores = {candidate.identity_key: score for candidate, score in plausible}

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


def _write_readme(path: Path, run_id: str, source_rows: int, candidate_rows: int) -> None:
    lines = [
        "# CFBD Identity Matching V1 - 2026-06-24",
        "",
        f"Run ID: `{run_id}`",
        f"Input CFBD identity rows: {source_rows}",
        f"Candidate output rows: {candidate_rows}",
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


def _timestamp_slug(value: str) -> str:
    return value.replace("-", "").replace(":", "")


if __name__ == "__main__":
    raise SystemExit(main())
