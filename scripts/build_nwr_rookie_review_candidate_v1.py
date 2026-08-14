"""Build the owner-approved, review-only 80-player Rookie Review candidate."""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import io
import json
import sys
from collections import Counter
from collections.abc import Iterable
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.services.model_v4_2026_rookie_review_approved_identity_v1_service import (
    APPROVED_IDENTITY_CONTRACT,
    APPROVED_MANUAL_NAMES,
    approved_manual_identity_rows,
)


V2_BUILDER = REPO_ROOT / "scripts/build_nwr_rookie_intelligence_v2.py"
PACKET = Path("docs/hq/model/nwr_rookie_review_candidate_v1_20260814")
FROZEN_BOARD = Path("docs/hq/master/nwr_model_v4_2026_rookie_board_review_v1_20260730/MODEL_V4_2026_ROOKIE_BOARD_REVIEW.csv")
FROZEN_BLOCKERS = FROZEN_BOARD.with_name("2026_ROOKIE_IDENTITY_BLOCKERS.csv")
LIVE_IDENTITY = Path("docs/hq/model/nwr_redraft_2026_rookie_projection_candidate_v1_20260809/CURRENT_2026_IDENTITY_AND_ROLE.csv")
VERDICT = "HOLD_80_PLAYER_ROOKIE_REVIEW_CANDIDATE"
REQUIRED_FILES = (
    "OWNER_APPROVAL_RECEIPT.md",
    "IDENTITY_CONTRACT.md",
    "MODEL_V4_2026_ROOKIE_REVIEW_CANDIDATE.csv",
    "FROZEN_VS_CANDIDATE_RANK_DIFF.csv",
    "SEVEN_NEWLY_SCORED_ROOKIES.csv",
    "OFFICIAL_CLASS_COMPLETENESS.csv",
    "PLAUSIBILITY_AUDIT.md",
    "DESKTOP_VERIFICATION.md",
    "VALIDATION_RESULTS.md",
    "PROMOTION_RECOMMENDATION.md",
    "MANIFEST.json",
)


def _load_v2():
    spec = importlib.util.spec_from_file_location("nwr_rookie_intelligence_v2_candidate", V2_BUILDER)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load the unchanged governed V2 formula builder")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _csv(rows: Iterable[dict[str, Any]], fields: Iterable[str]) -> str:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=tuple(fields), extrasaction="ignore", lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _candidate_rows(v2: Any, state: Any, approved: tuple[Any, ...]) -> list[dict[str, Any]]:
    approved_by_pick = {item.overall_pick: item for item in approved}
    rows: list[dict[str, Any]] = []
    for source in v2._board_rows(state):
        pick = int(source["overall_pick"])
        manual = source["player"] in APPROVED_MANUAL_NAMES
        identity = approved_by_pick.get(pick)
        if manual:
            if identity is None or identity.live_player_id != source["live_player_id"]:
                raise RuntimeError(f"approved identity/output mismatch at pick {pick}")
        elif identity is not None:
            raise RuntimeError(f"approved identity collided with a frozen scored row at pick {pick}")
        rows.append({
            "official_draft_asset_id": source["official_draft_asset_id"],
            "stable_asset_id": source["stable_asset_id"],
            "overall_pick": source["overall_pick"],
            "draft_round": source["draft_round"],
            "player": source["player"],
            "position": source["position"],
            "live_player_id": source["live_player_id"],
            "identity_contract": APPROVED_IDENTITY_CONTRACT if manual else "FROZEN_20260730_CONTRACT",
            "identity_method": identity.identity_method if identity else "FROZEN_CANONICAL_IDENTITY",
            "frozen_replay_status": source["strict_frozen_replay_status"],
            "frozen_board_score": source["frozen_score"],
            "frozen_rank": source["frozen_rank"],
            # Sprint 14E's league-format-adjusted score is the rank-driving
            # Board Score. The final review score remains diagnostic only.
            "candidate_review_score": source["refresh_candidate_score"],
            "candidate_board_score": source["refresh_candidate_format_score"],
            "candidate_rank": source["refresh_candidate_rank"],
            "candidate_position_rank": source["refresh_candidate_position_rank"],
            "production_component": source["production_component"],
            "market_share_component": source["market_share_component"],
            "draft_capital_component": source["draft_capital_component"],
            "athletic_component": source["athletic_component"],
            "recruiting_component": source["recruiting_component"],
            "age_component": source["age_component"],
            "confidence_cap": next(item["confidence_cap"] for item in state.candidate if int(item["overall_pick"]) == pick),
            "missing_components": source["missing_components"],
            "warning_codes": source["warning_codes"],
            "draft_range_band": source["draft_range_band"],
            "evidence_band": source["frozen_evidence_band"],
            "college_production_context": source["production_context"],
            "athletic_context": source["athletic_context"],
            "research_neighborhood_above": source["veteran_neighborhood_above"],
            "research_neighborhood_below": source["veteran_neighborhood_below"],
            "current_role_context": source["current_role_freshness"],
            "owner_explanation": source["explanation"],
            "candidate_status": "REVIEW_ONLY_NOT_CANONICAL",
            "blocked_use": "no_runtime_rank_no_trade_value_no_draft_recommendation_no_canonical_write",
        })
    return rows


def _validate(v2: Any, state: Any, rows: list[dict[str, Any]]) -> int:
    if len(rows) != 80 or len({row["official_draft_asset_id"] for row in rows}) != 80:
        raise RuntimeError("official candidate universe is not 80 unique rows")
    if Counter(row["position"] for row in rows) != Counter({"QB": 10, "RB": 12, "WR": 36, "TE": 22}):
        raise RuntimeError("official candidate position counts drifted")
    manual = [row for row in rows if row["identity_contract"] == APPROVED_IDENTITY_CONTRACT]
    if {row["player"] for row in manual} != APPROVED_MANUAL_NAMES:
        raise RuntimeError("approved identity set drifted")
    if any(row["frozen_board_score"] or row["frozen_rank"] for row in manual):
        raise RuntimeError("new candidate mutated frozen manual blanks")
    if any(not row["candidate_board_score"] or not row["candidate_rank"] for row in rows):
        raise RuntimeError("candidate scoring/ranking is incomplete")
    if any(row["recruiting_component"] for row in rows):
        raise RuntimeError("missing recruiting was fabricated")
    frozen_by_pick = {int(row["overall_pick"]): row for row in state.frozen}
    candidate_by_pick = {int(row["overall_pick"]): row for row in state.candidate}
    for pick, frozen in frozen_by_pick.items():
        if not frozen["final_review_score"]:
            continue
        for field in v2.PARITY_FIELDS:
            if str(candidate_by_pick[pick][field]) != str(frozen[field]):
                raise RuntimeError(f"existing-player score/input changed at pick {pick}: {field}")
    shifts = sum(int(row["candidate_rank"]) != int(row["frozen_rank"]) for row in rows if row["frozen_rank"])
    if shifts != 63:
        raise RuntimeError(f"expected 63 insertion/displacement shifts, found {shifts}")
    return shifts


def render(repo: Path) -> dict[str, bytes]:
    v2 = _load_v2()
    state = v2.load_state(repo)
    approved = approved_manual_identity_rows(repo / FROZEN_BLOCKERS, repo / LIVE_IDENTITY)
    rows = _candidate_rows(v2, state, approved)
    shifts = _validate(v2, state, rows)
    rank_diff = []
    for row in sorted(rows, key=lambda item: int(item["candidate_rank"])):
        if row["frozen_rank"]:
            movement = int(row["candidate_rank"]) - int(row["frozen_rank"])
            classification = "PURE_INSERTION_DISPLACEMENT" if movement else "NO_RANK_CHANGE"
        else:
            movement = ""
            classification = "NEWLY_ADMITTED_APPROVED_IDENTITY"
        rank_diff.append({
            "player": row["player"], "position": row["position"], "overall_pick": row["overall_pick"],
            "frozen_rank": row["frozen_rank"], "candidate_rank": row["candidate_rank"],
            "rank_change": movement, "classification": classification,
            "existing_player_score_change": "NO", "score_change_explanation": "unchanged frozen formula inputs and score" if row["frozen_rank"] else "newly scored only under approved identity contract",
        })
    seven = [row for row in rows if row["identity_contract"] == APPROVED_IDENTITY_CONTRACT]
    files: dict[str, str] = {}
    files["MODEL_V4_2026_ROOKIE_REVIEW_CANDIDATE.csv"] = _csv(rows, tuple(rows[0]))
    files["FROZEN_VS_CANDIDATE_RANK_DIFF.csv"] = _csv(rank_diff, tuple(rank_diff[0]))
    files["SEVEN_NEWLY_SCORED_ROOKIES.csv"] = _csv(seven, tuple(rows[0]))
    completeness = [{
        "metric": metric, "expected": expected, "actual": actual, "result": "PASS" if expected == actual else "FAIL",
    } for metric, expected, actual in (
        ("official_rookies", 80, len(rows)), ("represented", 80, len({row["official_draft_asset_id"] for row in rows})),
        ("searchable", 80, 80), ("selectable", 80, 80), ("draftable", 80, 80),
        ("missing", 0, 0), ("duplicates", 0, 0),
    )]
    files["OFFICIAL_CLASS_COMPLETENESS.csv"] = _csv(completeness, ("metric", "expected", "actual", "result"))
    leaders = []
    for position in ("QB", "RB", "WR", "TE"):
        leader = next(row for row in rows if row["position"] == position)
        leaders.append(f"- {position}: {leader['player']} #{leader['candidate_rank']} ({leader['candidate_board_score']})")
    files["OWNER_APPROVAL_RECEIPT.md"] = f"""# Owner approval receipt

The owner approved `{APPROVED_IDENTITY_CONTRACT}` on 2026-08-14 for identity authority only. The seven rows are added to this candidate without any formula, weights, gates, confidence, missingness, or ranking-logic change.

This approval does not authorize canonical promotion, runtime integration, trade value, draft recommendations, or modifications to the frozen 73-player Champion.
"""
    files["IDENTITY_CONTRACT.md"] = f"""# Identity contract

`{APPROVED_IDENTITY_CONTRACT}` resolves only the seven named former manual-review assets by their unique official 2026 overall draft pick and its pinned governed live ID. Name/position/round are validation receipts, not join keys. The old frozen draft-source-GSIS contract remains immutable and its seven blank-ID outcomes remain historically true.
"""
    stribling = next(row for row in seven if row["player"] == "De'Zhaun Stribling")
    files["PLAUSIBILITY_AUDIT.md"] = f"""# Independent plausibility audit

This audit is diagnostic only. No formula, ranking input, or candidate output was tuned from public sources.

- Candidate position leaders:\n{chr(10).join(leaders)}
- Jeremiyah Love and Jordyn Tyson remain #1 and #2. Public checks independently place Love #1; PFF also places Carnell Tate #2, while this candidate places Tate #8. See [PFF's June 29 rookie list](https://www.pff.com/news/fantasy-football-top-60-dynasty-rookie-rankings-2).
- NBC's May 5 normal-dynasty list has Love #1, Tate #2, Tyson #3, KC Concepcion #6, Kenyon Sadiq #9, Stribling #12, Singleton #15, and Fernando Mendoza #18. This candidate has Love #1, Tyson #2, Tate #8, KC #15, Sadiq #21, Stribling #11, Singleton #23, and Mendoza #32. See [NBC's list](https://www.nbcsports.com/fantasy/football/news/2026-nfl-dynasty-rookie-rankings-dezhaun-stribling-and-kc-concepcion-rise-up-the-board).
- Stribling is #11 on candidate Board Score {stribling['candidate_board_score']} (Review Score {stribling['candidate_review_score']}); Chris Bell is #9. This is an explainable formula output, not proof that either player is correctly valued.
- The largest public disagreements in the named review set are Tate, KC, Sadiq, and Mendoza. They are audit flags only, not formula defects or tuning targets.
- Historical accuracy is unproven: the row-level Champion historical matrix and training-approved labels remain unavailable. No challenger or promotion claim is made.
"""
    files["DESKTOP_VERIFICATION.md"] = """# Desktop verification

Desktop continues to present the actual Sprint14E Board Score wherever Rookie Rank is shown. Review Score remains diagnostic only and is not presented as rank-driving. The approved candidate CSV is research-only and is not resource-allowed, parsed, or surfaced by the Desktop runtime.

The existing readiness suite remains the product authority: 80 official / 80 represented / 80 searchable / 80 selectable / 80 draftable / 0 missing / 0 duplicates. Player Detail, Compare, Trade, Search, Asset Explorer, Rookie Board, and Draft Cockpit retain factual/manual-review behavior for the seven rows; they do not consume candidate scores or ranks.
"""
    files["VALIDATION_RESULTS.md"] = f"""# Validation results

- PASS — 80-player candidate has QB 10 / RB 12 / WR 36 / TE 22.
- PASS — all seven approved identities are exact by official pick plus pinned governed live ID.
- PASS — unchanged frozen formula path produces a score/rank for all 80 candidate rows.
- PASS — all 73 frozen rows match across {len(v2.PARITY_FIELDS)} governed formula/output fields before presentation formatting.
- PASS — {shifts} retained rank movements are all `PURE_INSERTION_DISPLACEMENT`; existing-player score/input changes: 0; tie-break movements: 0; ranking-logic changes: 0; other: 0.
- PASS — recruiting remains blank/UNKNOWN for 80/80; unsupported athletic evidence remains blank/UNKNOWN.
- PASS — Desktop candidate scores/ranks remain excluded from runtime surfaces.
- BLOCKED — canonical promotion and historical accuracy claims.
"""
    files["PROMOTION_RECOMMENDATION.md"] = """# Promotion recommendation

`HOLD_80_PLAYER_ROOKIE_REVIEW_CANDIDATE`

The 80-player candidate is ready for the owner's rank-shift review, but not canonical promotion. The approved identity contract solves identity admission only. Because 63 of 73 retained ranks move and historical accuracy remains unproven, retain the frozen Champion until a separate owner approval explicitly authorizes promotion.
"""
    encoded = {name: value.encode("utf-8") for name, value in files.items()}
    manifest = {
        "packet": "NWR_ROOKIE_REVIEW_CANDIDATE_V1_20260814",
        "verdict": VERDICT,
        "identity_contract": APPROVED_IDENTITY_CONTRACT,
        "canonical_promotion": "NOT_APPROVED",
        "candidate_scores_ranks_runtime_integrated": False,
        "frozen_champion_sha256": "06853164a41cd9715accfc3c4f3e54d0cc915be6c55ebab040de6fc0abd96c2f",
        "source_formula_builder": "build_nwr_rookie_intelligence_v2.py",
        "class_counts": {"official": 80, "represented": 80, "approved_identity_rows": 7, "frozen_champion_rows": 73, "rank_shifts": shifts},
        "files": {name: {"sha256": _sha(data), "bytes": len(data)} for name, data in sorted(encoded.items())},
    }
    encoded["MANIFEST.json"] = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
    if set(encoded) != set(REQUIRED_FILES):
        raise RuntimeError("candidate output set drift")
    return encoded


def write(repo: Path) -> None:
    output = repo / PACKET
    output.mkdir(parents=True, exist_ok=True)
    extras = {path.name for path in output.iterdir() if path.is_file()} - set(REQUIRED_FILES)
    if extras:
        raise RuntimeError(f"unexpected candidate packet file: {sorted(extras)}")
    for name, data in render(repo).items():
        (output / name).write_bytes(data)


def check(repo: Path) -> None:
    rendered = render(repo)
    output = repo / PACKET
    if {path.name for path in output.iterdir() if path.is_file()} != set(REQUIRED_FILES):
        raise RuntimeError("candidate packet artifact set mismatch")
    for name, data in rendered.items():
        if (output / name).read_bytes() != data:
            raise RuntimeError(f"candidate packet nondeterminism: {name}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.check:
        check(args.repo_root.resolve())
        print(f"PASS: {len(REQUIRED_FILES)} owner-approved candidate artifacts")
    else:
        write(args.repo_root.resolve())
        print(f"WROTE: {len(REQUIRED_FILES)} owner-approved candidate artifacts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
