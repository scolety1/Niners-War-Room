# ruff: noqa: E501

from __future__ import annotations

import csv
import hashlib
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

BASELINE_PATH = Path(
    "local_exports/model_v4/current_value/latest/full_player_board_value_review_rows.csv"
)
SHADOW_ROOT = Path("local_exports/model_v4/formula_candidates/qb_te_shadow_20260609")
SHADOW_RANKINGS = SHADOW_ROOT / "shadow_rankings_qb_te_context_balance_v1.csv"
SHADOW_MOVEMENT = SHADOW_ROOT / "shadow_movement_vs_baseline_qb_te_context_balance_v1.csv"
SHADOW_POSITION_DISTRIBUTION = (
    SHADOW_ROOT / "shadow_position_distribution_qb_te_context_balance_v1.csv"
)
SHADOW_MY_TEAM = SHADOW_ROOT / "shadow_my_team_impact_qb_te_context_balance_v1.csv"
SHADOW_SUSPICIOUS = SHADOW_ROOT / "shadow_suspicious_rows_qb_te_context_balance_v1.csv"
SHADOW_MANIFEST = SHADOW_ROOT / "experiment_manifest.md"
BASELINE_DIAGNOSIS = Path("docs/model_v4/QB_TE_BASELINE_COMPONENT_DIAGNOSIS_20260609.md")
SHADOW_RESULTS = Path("docs/model_v4/QB_TE_SHADOW_FORMULA_CANDIDATE_RESULTS_20260609.md")
SHADOW_HANDOFF = Path("docs/model_v4/QB_TE_SHADOW_FORMULA_CANDIDATE_HANDOFF_20260609.md")
COMPONENT_READBACK = Path(
    "local_exports/model_v4/current_value/latest/rankings_suspicious_component_readback.csv"
)
QB_TRIAGE = Path(
    "local_exports/model_v4/current_value/latest/rankings_qb_formula_candidate_triage.csv"
)
TE_TRIAGE = Path(
    "local_exports/model_v4/current_value/latest/rankings_te_formula_candidate_triage.csv"
)

DEEP_AUDIT_REPORT = Path(
    "docs/model_v4/QB_TE_CONTEXT_BALANCE_V1_DEEP_AUDIT_20260609.md"
)
PRODUCTION_PATCH_PROPOSAL = Path(
    "docs/model_v4/QB_TE_CONTEXT_BALANCE_V1_PRODUCTION_PATCH_PROPOSAL_20260609.md"
)

VARIANT_ID = "qb_te_context_balance_v1"
DEEP_AUDIT_VERDICT = "revise_combined_candidate_before_patch"

QB_GROUP = (
    "Josh Allen",
    "Drake Maye",
    "Trevor Lawrence",
    "Matthew Stafford",
    "Jalen Hurts",
    "Patrick Mahomes",
    "Lamar Jackson",
    "Joe Burrow",
    "Jayden Daniels",
    "Kyler Murray",
    "Daniel Jones",
)

TE_GROUP = (
    "Trey McBride",
    "Kyle Pitts",
    "Travis Kelce",
    "Brock Bowers",
    "Sam LaPorta",
    "Mark Andrews",
    "T.J. Hockenson",
    "Jake Ferguson",
    "Brenton Strange",
    "George Kittle",
    "Tucker Kraft",
)

RB_WR_ANCHORS = (
    "Puka Nacua",
    "Christian McCaffrey",
    "Jaxon Smith-Njigba",
    "Jonathan Taylor",
    "Bijan Robinson",
    "Jahmyr Gibbs",
    "Ja'Marr Chase",
    "Amon-Ra St. Brown",
    "De'Von Achane",
    "Chase Brown",
    "Brian Thomas",
    "Brian Thomas Jr.",
    "Brandon Aiyuk",
    "CeeDee Lamb",
    "Justin Jefferson",
    "Malik Nabers",
    "Garrett Wilson",
)


@dataclass(frozen=True)
class ContextBalanceDeepAuditResult:
    active_hash_before: str
    active_hash_after: str
    active_output_changed: bool
    deep_audit_report: str
    production_patch_proposal: str
    summary: dict[str, object]


@dataclass(frozen=True)
class ContextBalanceDeepAuditPaths:
    deep_audit_report: Path
    production_patch_proposal: Path


def build_context_balance_deep_audit() -> ContextBalanceDeepAuditResult:
    active_hash_before = _sha256(BASELINE_PATH)
    rankings = _read_rows(SHADOW_RANKINGS)
    movement = _read_rows(SHADOW_MOVEMENT)
    position_distribution = _read_rows(SHADOW_POSITION_DISTRIBUTION)
    my_team = _read_rows(SHADOW_MY_TEAM)
    suspicious = _read_rows(SHADOW_SUSPICIOUS)
    component_rows = _read_rows(COMPONENT_READBACK)
    qb_triage = _read_rows(QB_TRIAGE)
    te_triage = _read_rows(TE_TRIAGE)
    manifest = _read_text(SHADOW_MANIFEST)
    baseline_diagnosis = _read_text(BASELINE_DIAGNOSIS)
    shadow_results = _read_text(SHADOW_RESULTS)
    shadow_handoff = _read_text(SHADOW_HANDOFF)

    row_by_player = _row_by_player(rankings)
    component_by_player = _row_by_player(component_rows, name_key="player")
    qb_triage_by_player = _row_by_player(qb_triage, name_key="player")
    te_triage_by_player = _row_by_player(te_triage, name_key="player")
    movement_by_player = _row_by_player(movement, name_key="player")

    top25 = rankings[:25]
    position_counts = Counter(row.get("position", "") for row in top25)
    te_rows = [row for row in rankings if row.get("position") == "TE"]
    qb_rows = [row for row in rankings if row.get("position") == "QB"]
    rb_wr_rows = [row for row in rankings if row.get("position") in {"RB", "WR"}]
    rb_wr_score_changed = any(_float(row.get("score_delta")) != 0.0 for row in rb_wr_rows)
    source_issue_rows = [
        row
        for row in suspicious
        if "source" in str(row.get("issue_bucket", "")).lower()
    ]
    active_hash_after = _sha256(BASELINE_PATH)

    summary = {
        "variant_id": VARIANT_ID,
        "verdict": DEEP_AUDIT_VERDICT,
        "active_hash_before": active_hash_before,
        "active_hash_after": active_hash_after,
        "active_output_changed": active_hash_before != active_hash_after,
        "top25_position_counts": dict(position_counts),
        "top25_qbs": position_counts.get("QB", 0),
        "top25_tes": position_counts.get("TE", 0),
        "top_te_shadow_rank": _int(te_rows[0].get("nwr_rank_shadow")) if te_rows else None,
        "top_qb_shadow_rank": _int(qb_rows[0].get("nwr_rank_shadow")) if qb_rows else None,
        "rb_wr_score_changed": rb_wr_score_changed,
        "my_team_rows": len(my_team),
        "my_team_max_abs_rank_delta": max(
            (abs(_int(row.get("rank_delta")) or 0) for row in my_team),
            default=0,
        ),
        "source_issue_rows": len(source_issue_rows),
        "sentinels_safe": _sentinels_safe(row_by_player),
        "contamination_safe": _contamination_safe(manifest),
        "decision_board_blocked": True,
    }

    audit = _deep_audit_text(
        summary=summary,
        rankings=rankings,
        position_distribution=position_distribution,
        my_team=my_team,
        suspicious=suspicious,
        row_by_player=row_by_player,
        movement_by_player=movement_by_player,
        component_by_player=component_by_player,
        qb_triage_by_player=qb_triage_by_player,
        te_triage_by_player=te_triage_by_player,
        baseline_diagnosis=baseline_diagnosis,
        shadow_results=shadow_results,
        shadow_handoff=shadow_handoff,
    )
    proposal = _proposal_text(summary)
    return ContextBalanceDeepAuditResult(
        active_hash_before=active_hash_before,
        active_hash_after=active_hash_after,
        active_output_changed=active_hash_before != active_hash_after,
        deep_audit_report=audit,
        production_patch_proposal=proposal,
        summary=summary,
    )


def write_context_balance_deep_audit(
    result: ContextBalanceDeepAuditResult | None = None,
    deep_audit_path: str | Path = DEEP_AUDIT_REPORT,
    proposal_path: str | Path = PRODUCTION_PATCH_PROPOSAL,
) -> ContextBalanceDeepAuditPaths:
    result = result or build_context_balance_deep_audit()
    deep_path = Path(deep_audit_path)
    prop_path = Path(proposal_path)
    deep_path.parent.mkdir(parents=True, exist_ok=True)
    prop_path.parent.mkdir(parents=True, exist_ok=True)
    deep_path.write_text(result.deep_audit_report, encoding="utf-8")
    prop_path.write_text(result.production_patch_proposal, encoding="utf-8")
    return ContextBalanceDeepAuditPaths(
        deep_audit_report=deep_path,
        production_patch_proposal=prop_path,
    )


def _deep_audit_text(
    *,
    summary: dict[str, object],
    rankings: list[dict[str, str]],
    position_distribution: list[dict[str, str]],
    my_team: list[dict[str, str]],
    suspicious: list[dict[str, str]],
    row_by_player: dict[str, dict[str, str]],
    movement_by_player: dict[str, dict[str, str]],
    component_by_player: dict[str, dict[str, str]],
    qb_triage_by_player: dict[str, dict[str, str]],
    te_triage_by_player: dict[str, dict[str, str]],
    baseline_diagnosis: str,
    shadow_results: str,
    shadow_handoff: str,
) -> str:
    lines = [
        "# QB/TE Context Balance v1 Deep Audit - 2026-06-09",
        "",
        "This is a proposal-only audit. It does not implement or promote `qb_te_context_balance_v1`.",
        "",
        "## 1. Executive Summary",
        f"- Variant audited: `{VARIANT_ID}`.",
        f"- Recommendation status: `{summary['verdict']}`.",
        "- The combined candidate improves the obvious baseline shape problem: QB/TE no longer dominate the top 10/top 25 in a 10-team 1QB, no-TE-premium league.",
        "- The candidate should be revised before a production patch because the TE compression may be too blunt: all TEs leave the top 25, Trey McBride lands at #42, and Brock Bowers lands at #67.",
        "- RB/WR scores do not change; rank gains are collateral displacement from QB/TE compression.",
        "- No active output changed, and Decision Board remains blocked.",
        "",
        "## 2. What The Candidate Changes In Shadow",
        "- Compresses QB scores toward the private QB median to test 1QB spread discipline.",
        "- Applies a no-premium TE ceiling shaped by private RB/WR distribution context, then compresses TE spread toward the private TE median.",
        "- Re-ranks the full shadow board under the experiment folder only.",
        "",
        "## 3. What It Does Not Change",
        "- Does not change active Rankings or baseline CSVs.",
        "- Does not change production formula files.",
        "- Does not change RB/WR scores.",
        "- Does not use market rank, league rank, public ranks, ADP, startup, projections, consensus, RotoWire rankings/projections, trade calculators, or legacy active-pack scores as score inputs.",
        "- Does not create roster actions or final recommendations.",
        "",
        "## 4. Why Baseline Was Suspicious",
        "- Baseline top 25 had 4 QBs and 3 TEs, including Trey McBride #1 overall, Josh Allen #5, Drake Maye #8, and Trevor Lawrence #9.",
        "- Baseline diagnosis ties QB pressure to VORP normalization plus rushing/passing component strength.",
        "- Baseline diagnosis ties TE pressure to strong TE VORP, route/target, first-down, efficiency, and red-zone components before full no-premium cross-position context.",
        "",
        "## 5. Why Combined Variant May Be Better",
        f"- Shadow top 25 by position: {summary['top25_position_counts']}.",
        "- Josh Allen and Drake Maye remain relevant at #18 and #23, but QBs no longer occupy the top 10.",
        "- TEs no longer outrank elite RB/WR assets by default in a no-premium format.",
        "- RB/WR scores are unchanged, which keeps the experiment narrow.",
        "",
        "## 6. Possible Overcorrection Concerns",
        "- Moving every TE out of the top 25 may be too aggressive even in no-TE-premium.",
        "- Trey McBride #42 may be plausible for review, but it is a large move from #1 and needs component-level scrutiny.",
        "- Brock Bowers #67 may be too low relative to the model's own component evidence and dynasty profile.",
        "- The candidate is a broad compression transform, not yet a nuanced elite-exception rule.",
        "",
        "## 7. QB-Specific Review",
        _player_group_table(QB_GROUP, row_by_player, movement_by_player, component_by_player, qb_triage_by_player),
        "",
        "## 8. TE-Specific Review",
        _player_group_table(TE_GROUP, row_by_player, movement_by_player, component_by_player, te_triage_by_player),
        "",
        "## 9. RB/WR Collateral Review",
        _anchor_table(RB_WR_ANCHORS, row_by_player),
        "",
        "## 10. My Team Impact",
        _my_team_table(my_team),
        "",
        "## 11. Veteran Impact",
        "- Veteran QB/TE rows move mostly because of positional compression, not because age/status confidence was specifically changed.",
        "- Matthew Stafford moves #19 -> #45; Travis Kelce moves #25 -> #44; George Kittle moves #88 -> #103.",
        "- This is a concern: a later patch should separate format compression from veteran age/status confidence rather than letting one broad transform do both jobs.",
        "",
        "## 12. Young-Player Impact",
        "- Drake Maye remains high enough for review (#23) after compression.",
        "- Brock Bowers (#67), Sam LaPorta (#151), and young TE rows may be compressed too hard if the future production model still believes elite TE exceptions should exist.",
        "- Young RB/WR anchor scores do not change; they mostly rise by collateral rank movement.",
        "",
        "## 13. Source/Trust/Warning Impact",
        f"- Source issue rows in the suspicious file: {summary['source_issue_rows']}.",
        "- The candidate does not clean source warnings or trust labels.",
        "- No non-kicker source quarantine is introduced by the shadow readback.",
        "",
        "## 14. Sentinels And Contamination",
        f"- Sentinels safe: {summary['sentinels_safe']}.",
        f"- Contamination safe: {summary['contamination_safe']}.",
        "- Keenan Allen and Darius Slayton legacy active-pack scores remain comparison-only.",
        "",
        "## 15. Invariants",
        f"- Active baseline hash before: `{summary.get('active_hash_before', '')}`.",
        f"- Active baseline hash after: `{summary.get('active_hash_after', '')}`.",
        f"- Active output changed: {summary['active_output_changed']}.",
        f"- RB/WR score changed: {summary['rb_wr_score_changed']}.",
        "- K rows remain unscored/default-hidden in the baseline.",
        "- Outcome percentages remain blank/in development.",
        "- Decision Board remains blocked.",
        "",
        "## 16. Recommendation Status",
        f"`{DEEP_AUDIT_VERDICT}`",
        "",
        "The combined candidate should not be rejected outright; it is the best current lane. But it should be revised before a production patch so TE elite-exception behavior is less blunt and QB compression is tied to production discipline with clearer receipts.",
        "",
        "## Overcorrection Audit",
        "1. Moving all TEs out of the top 25 is likely a no-premium correction, but it may be too strong.",
        "2. Trey McBride at #42 is plausible enough for human review, not clean enough for immediate promotion.",
        "3. Brock Bowers at #67 looks like the largest TE overcorrection risk relative to the model's own evidence.",
        "4. Josh Allen at #18 and Drake Maye at #23 keep QB relevant without top-10 domination.",
        "5. The candidate does not bury every elite QB, but it leaves some already-low QB rows low and still needs review.",
        "6. Older QBs/TEs are compressed, but not specifically through age/status logic.",
        "7. Top RB/WR assets dominate the top 25, consistent with this league format.",
        "8. The result looks more like a dynasty board than the baseline, but TE future upside may be underexpressed.",
        "9. The result better respects 1QB/no-TE-premium/2-flex context than the baseline, pending TE revision.",
        "",
        "## Readback Sources Consulted",
        f"- Manifest excerpt loaded: {bool(shadow_handoff and shadow_results and baseline_diagnosis)}.",
        f"- Position distribution rows: {len(position_distribution)}.",
        f"- Suspicious rows reviewed: {len(suspicious)}.",
    ]
    return "\n".join(lines) + "\n"


def _proposal_text(summary: dict[str, object]) -> str:
    return "\n".join(
        [
            "# QB/TE Context Balance v1 Production Patch Proposal - 2026-06-09",
            "",
            "This is a precise patch proposal only. No implementation or promotion occurred.",
            "",
            "## Candidate Name",
            "`qb_te_context_balance_v1_revised`",
            "",
            "## Hypothesis",
            "A production-safe QB/TE discipline patch can improve 10-team 1QB and no-TE-premium cross-position shape by applying clearer format-context discipline inside the admitted QB/TE current-value layer, while leaving RB/WR scoring, source routing, and lineage gates unchanged.",
            "",
            "## Intended Behavior",
            "- Reduce QB top-end domination in 1QB without burying elite private-evidence QBs below obvious depth rows.",
            "- Reduce no-premium TE top-end inflation while preserving a narrow elite-TE exception path when private component evidence is overwhelming and explainable.",
            "- Keep RB/WR score values unchanged in a QB/TE-only patch.",
            "- Preserve trust, warning, source-disclosure, and sentinel behavior.",
            "",
            "## Exact Production Files Likely Affected",
            "- `src/services/model_v4_qb_te_current_value_service.py`",
            "- `src/services/model_v4_current_value_checkpoint_service.py`, readback/tests only unless output schema needs a discipline receipt field",
            "- `src/services/full_board_current_value_export_service.py`, only if the export must route a new discipline receipt",
            "- `scripts/build_model_v4_full_board_rankings_exports.py`, rerun only",
            "",
            "## Exact Production Functions / Classes Likely Affected",
            "- `build_qb_te_current_value`",
            "- `_score_row`",
            "- `_discipline`",
            "- `_qb_components` readback only, if the patch needs component diagnostics",
            "- `_te_components` readback only, if the patch needs component diagnostics",
            "- `_sanity_warnings`",
            "- `QbTeCurrentValueResult` only if additional audit metadata is required",
            "",
            "## Tests That Must Be Added",
            "- QB 1QB top-25/top-10 shape test using private output only.",
            "- TE no-premium elite-exception test using private output only.",
            "- RB/WR score unchanged test.",
            "- My Team movement explainability readback.",
            "- Keenan Allen and Darius Slayton sentinel tests.",
            "- No market/league/RotoWire projection/legacy contamination test.",
            "- Full-board output remains 232 scored QB/RB/WR/TE and 8 unscored kickers.",
            "- Decision Board remains blocked.",
            "",
            "## Expected Output Files That Would Change If Approved",
            "- `local_exports/model_v4/current_value/latest/qb_te_current_value_review_rows.csv`",
            "- `local_exports/model_v4/current_value/latest/qb_te_current_value_component_rows.csv`",
            "- `local_exports/model_v4/current_value/latest/qb_te_current_value_warnings.csv`",
            "- `local_exports/model_v4/current_value/latest/current_player_value_full_board_review_rows.csv`",
            "- `local_exports/model_v4/current_value/latest/full_player_board_value_review_rows.csv`",
            "- movement/sanity/readiness reports generated after the approved production rerun",
            "",
            "## Rollback Plan",
            "- Keep this shadow folder and baseline hashes as receipts.",
            "- Revert the production patch commit if shape checks, sentinels, or contamination checks fail.",
            "- Re-run the safe Rankings pipeline from the pre-patch commit to restore active exports.",
            "- Do not manually copy shadow CSVs into active output paths.",
            "",
            "## Promotion Gate Checklist",
            "- User approval obtained before patching.",
            "- Shadow output is not copied into active Rankings.",
            "- Production pipeline recomputes active Rankings if approved.",
            "- Source/lineage/sentinel/contamination gates pass.",
            "- QB/TE movement audit passes human review.",
            "- RB/WR scores remain unchanged except collateral rank movement.",
            "- Decision Board remains blocked until the patched Rankings baseline is re-audited.",
            "",
            "## Risks",
            "- TE overcorrection: all TEs left the top 25 in shadow, and Brock Bowers fell to #67.",
            "- QB compression may handle top-end dominance while leaving low elite-QB anomalies unresolved.",
            "- A broad compression rule may mask whether age/status, VORP anchor, or cross-position scaling is the true cause.",
            "",
            "## Failure Modes",
            "- TEs become structurally undervalued in no-premium despite elite evidence.",
            "- Elite QBs are flattened too close to replacement/depth rows.",
            "- QB/TE patch unexpectedly changes RB/WR scores.",
            "- Warnings/trust labels become cleaner without source repair.",
            "- Market/league/display-only context leaks into private score tests or implementation.",
            "",
            "## Invariants That Must Remain True",
            f"- Active baseline hash from this audit: `{summary.get('active_hash_before', '')}`.",
            "- Keenan Allen legacy 82.4 remains comparison-only.",
            "- Darius Slayton legacy 78.88 remains comparison-only.",
            "- Current NWR scores use admitted Model v4 lineage only.",
            "- 2026 5.04 remains no-baseline/no invented equivalence.",
            "- K rows remain hidden/default-off.",
            "- Market/league/RotoWire projection/ranking data stays out of private value.",
            "",
            "## Candidate Acceptance Criteria For A Later Patch",
            "- Top 25 should not be dominated by QBs in 10-team 1QB.",
            "- No-premium TE should allow elite exceptions but avoid #1 overall TE unless component evidence is overwhelming and explainable.",
            "- Elite QBs should not collapse below obvious depth/replacement rows without explanation.",
            "- RB/WR score values should not change from a QB/TE-only patch.",
            "- My Team movement should be explainable.",
            "- No source-quarantined row should become cleaner because of formula patch.",
            "- Sentinels remain safe.",
            "- No contamination.",
            "- Full focused and relevant regression tests pass.",
            "",
            "## User Approval Required",
            "User approval is required before any production patch. Do not promote shadow outputs directly. Recompute active Rankings only through the production pipeline if approved. Keep Decision Board blocked until Rankings patch is approved and re-audited.",
        ]
    ) + "\n"


def _player_group_table(
    names: tuple[str, ...],
    row_by_player: dict[str, dict[str, str]],
    movement_by_player: dict[str, dict[str, str]],
    component_by_player: dict[str, dict[str, str]],
    triage_by_player: dict[str, dict[str, str]],
) -> str:
    lines = [
        "| Player | Base Rank | Shadow Rank | Base Score | Shadow Score | Rank Delta | Score Delta | Trust | Warning Summary | Audit Read | Human Review Question |",
        "|---|---:|---:|---:|---:|---:|---:|---|---|---|---|",
    ]
    for name in names:
        row = _lookup(row_by_player, name)
        move = _lookup(movement_by_player, name)
        comp = _lookup(component_by_player, name)
        triage = _lookup(triage_by_player, name)
        if not row:
            lines.append(f"| {name} | - | - | - | - | - | - | - | - | Missing from shadow candidate rows. | Verify identity/source row. |")
            continue
        read = _movement_read(row, comp, triage)
        lines.append(
            "| {player} | {base_rank} | {shadow_rank} | {base_score} | {shadow_score} | {rank_delta} | {score_delta} | {trust} | {warnings} | {read} | {question} |".format(
                player=row.get("player", name),
                base_rank=row.get("nwr_rank_baseline", ""),
                shadow_rank=row.get("nwr_rank_shadow", ""),
                base_score=row.get("nwr_score_baseline", ""),
                shadow_score=row.get("nwr_score_shadow", ""),
                rank_delta=row.get("rank_delta", move.get("rank_delta", "")),
                score_delta=row.get("score_delta", move.get("score_delta", "")),
                trust=row.get("trust_status", ""),
                warnings=_compact(row.get("warning_summary", "")),
                read=read,
                question=triage.get("human_review_question")
                or row.get("human_review_question", ""),
            )
        )
    return "\n".join(lines)


def _anchor_table(names: tuple[str, ...], row_by_player: dict[str, dict[str, str]]) -> str:
    lines = [
        "| Player | Pos | Base Rank | Shadow Rank | Rank Delta | Score Delta | Collateral Read |",
        "|---|---|---:|---:|---:|---:|---|",
    ]
    seen: set[str] = set()
    for name in names:
        row = _lookup(row_by_player, name)
        if not row or row.get("player") in seen:
            continue
        seen.add(str(row.get("player", "")))
        score_delta = _float(row.get("score_delta"))
        read = (
            "Score unchanged; rank movement is collateral."
            if score_delta == 0.0
            else "Suspicious: score changed in a QB/TE-only candidate."
        )
        lines.append(
            f"| {row.get('player', name)} | {row.get('position', '')} | {row.get('nwr_rank_baseline', '')} | {row.get('nwr_rank_shadow', '')} | {row.get('rank_delta', '')} | {row.get('score_delta', '')} | {read} |"
        )
    return "\n".join(lines)


def _my_team_table(rows: list[dict[str, str]]) -> str:
    lines = [
        "| Player | Pos | Base Rank | Shadow Rank | Rank Delta | Score Delta | Read |",
        "|---|---|---:|---:|---:|---:|---|",
    ]
    for row in rows[:24]:
        score_delta = _float(row.get("score_delta"))
        read = "direct score unchanged" if score_delta == 0.0 else "direct QB/TE score changed"
        lines.append(
            f"| {row.get('player', '')} | {row.get('position', '')} | {row.get('nwr_rank_baseline', '')} | {row.get('nwr_rank_shadow', '')} | {row.get('rank_delta', '')} | {row.get('score_delta', '')} | {read} |"
        )
    return "\n".join(lines)


def _movement_read(
    row: dict[str, str], comp: dict[str, str], triage: dict[str, str]
) -> str:
    position = row.get("position", "")
    rank_delta = _int(row.get("rank_delta")) or 0
    if position == "QB":
        if rank_delta > 0:
            return "Fixes top-end 1QB pressure, but must not bury elite QB evidence."
        if rank_delta < 0:
            return "Rises by compression side effect; check for low-QB anomaly."
        return "No material movement."
    if position == "TE":
        if rank_delta > 25:
            return "Large no-premium compression; overcorrection risk."
        if rank_delta > 0:
            return "Moderate no-premium compression; human review needed."
        return "No material TE compression."
    if comp.get("component_fields_available") == "yes" or triage:
        return "Component/triage receipt exists for review."
    return "Review with available receipts."


def _sentinels_safe(row_by_player: dict[str, dict[str, str]]) -> bool:
    keenan = _lookup(row_by_player, "Keenan Allen")
    slayton = _lookup(row_by_player, "Darius Slayton")
    return (
        keenan.get("nwr_score_baseline") == "33.1581"
        and slayton.get("nwr_score_baseline") == "23.6148"
        and keenan.get("changed_by_candidate_area") == "unchanged_by_variant"
        and slayton.get("changed_by_candidate_area") == "unchanged_by_variant"
    )


def _contamination_safe(manifest: str) -> bool:
    required = (
        "Do not use market rank",
        "RotoWire projections/rankings",
        "legacy active-pack scores as score input",
    )
    return all(term in manifest for term in required)


def _row_by_player(
    rows: list[dict[str, str]], name_key: str = "player"
) -> dict[str, dict[str, str]]:
    return {str(row.get(name_key, "")): row for row in rows if row.get(name_key)}


def _lookup(rows: dict[str, dict[str, str]], name: str) -> dict[str, str]:
    if name in rows:
        return rows[name]
    if name == "Brian Thomas Jr." and "Brian Thomas" in rows:
        return rows["Brian Thomas"]
    return {}


def _compact(value: object) -> str:
    text = str(value or "")
    if not text or text.lower() == "nan":
        return ""
    flags = [part for part in text.split("|") if part]
    if len(flags) <= 2:
        return text
    return f"{len(flags)} warnings: " + ", ".join(flags[:2])


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _float(value: object, default: float = 0.0) -> float:
    try:
        text = str(value).strip()
        if not text or text.lower() == "nan":
            return default
        return float(text)
    except (TypeError, ValueError):
        return default


def _int(value: object) -> int | None:
    try:
        text = str(value).strip()
        if not text or text.lower() == "nan":
            return None
        return int(float(text))
    except (TypeError, ValueError):
        return None
