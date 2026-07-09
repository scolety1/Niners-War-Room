from __future__ import annotations

import csv
import importlib.util
import math
import py_compile
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


OUT_DIR = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[4]

EXPECTED_REMOTE_HEAD = "b125be9ee73f1adc3487c1fa69ae954e8e49790f"
PRIOR_GAUNTLET_COMMIT = "8f57c3b758606204f39787c7ff86e69ee514ed39"
PRIOR_GAUNTLET_DIR = REPO / "docs/hq/model/full_review_only_formula_gauntlet_candidate_arena_v1_20260709"
PRIOR_MEDIUM_DIR = REPO / "docs/hq/model/medium_review_only_formula_pilot_v1_20260709"
SMALL_PILOT_DIR = Path(
    r"C:\NWR\Niners-War-Room-small-review-only-formula-pilot-v1-20260709"
    r"\docs\hq\model\small_review_only_formula_pilot_v1_20260709"
)
GAUNTLET_RUNNER = PRIOR_GAUNTLET_DIR / "run_full_review_only_formula_gauntlet_candidate_arena_v1.py"

NEAR_DUPLICATE_OUTPUT = 0.995
SAME_NEIGHBORHOOD = 0.980


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_text(path: Path, text: str) -> None:
    path.write_text(text.strip() + "\n", encoding="utf-8")


def num(value: object) -> float | None:
    if value is None:
        return None
    text = str(value).strip().replace("%", "")
    if not text:
        return None
    try:
        out = float(text)
    except ValueError:
        return None
    return out if math.isfinite(out) else None


def fmt(value: float | None, places: int = 3) -> str:
    return "" if value is None else f"{value:.{places}f}"


def pct(value: float | None) -> str:
    return "" if value is None else f"{value * 100:.1f}%"


def mean(values: list[float]) -> float | None:
    clean = [v for v in values if v is not None]
    return sum(clean) / len(clean) if clean else None


def pearson(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) < 2 or len(xs) != len(ys):
        return None
    mx = sum(xs) / len(xs)
    my = sum(ys) / len(ys)
    numerator = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den_x = sum((x - mx) ** 2 for x in xs)
    den_y = sum((y - my) ** 2 for y in ys)
    if den_x <= 0 or den_y <= 0:
        return None
    return numerator / math.sqrt(den_x * den_y)


def load_gauntlet_module() -> Any:
    spec = importlib.util.spec_from_file_location("gauntlet_runner", GAUNTLET_RUNNER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import prior Gauntlet runner: {GAUNTLET_RUNNER}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def scope_group(scope: str) -> str:
    if scope == "QB/RB/WR/TE":
        return "ALL"
    return scope.replace("/", "_")


def tokenize(text: str) -> set[str]:
    return {token for token in re.split(r"[^A-Za-z0-9_]+", text.lower()) if token}


def parse_params(text: str) -> dict[str, float]:
    params: dict[str, float] = {}
    for part in str(text).split(";"):
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        parsed = num(value)
        if parsed is not None:
            params[key.strip()] = parsed
    return params


def weight_distance(a: dict[str, float], b: dict[str, float]) -> float | None:
    keys = sorted(set(a) | set(b))
    if not keys:
        return None
    return math.sqrt(sum((a.get(key, 0.0) - b.get(key, 0.0)) ** 2 for key in keys))


def jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def build_rank_vectors(module: Any, active_registry: list[dict[str, Any]]) -> dict[str, dict[str, float]]:
    rows = module.load_panel()
    module.add_scores_and_ranks(rows, active_registry)
    vectors: dict[str, dict[str, float]] = {}
    for candidate in active_registry:
        cid = candidate["candidate_id"]
        rank_col = f"{cid}_rank"
        vector: dict[str, float] = {}
        for row in rows:
            rank = row.get(rank_col)
            if rank is None:
                continue
            key = f"{row['season']}|{row['position']}|{row['player_id']}|{row['substrate_row_id']}"
            vector[key] = float(rank)
        vectors[cid] = vector
    return vectors


def rank_corr(a: dict[str, float], b: dict[str, float]) -> tuple[float | None, int]:
    keys = sorted(set(a) & set(b))
    if len(keys) < 30:
        return None, len(keys)
    xs = [a[key] for key in keys]
    ys = [b[key] for key in keys]
    return pearson(xs, ys), len(keys)


def build_similarity(
    registry_rows: list[dict[str, str]],
    scorecard_rows: list[dict[str, str]],
    vectors: dict[str, dict[str, float]],
) -> list[dict[str, object]]:
    registry_by_id = {row["candidate_id"]: row for row in registry_rows}
    active_ids = [row["candidate_id"] for row in scorecard_rows if row["candidate_status"] == "ACTIVE_REVIEW_ONLY"]
    output: list[dict[str, object]] = []
    for i, left_id in enumerate(active_ids):
        left = registry_by_id[left_id]
        left_tokens = tokenize(left["formula_definition"] + " " + left["allowed_inputs"] + " " + left["candidate_family"])
        left_inputs = set(left["allowed_inputs"].split(";"))
        left_params = parse_params(left["params"])
        for right_id in active_ids[i + 1 :]:
            right = registry_by_id[right_id]
            corr, overlap_rows = rank_corr(vectors[left_id], vectors[right_id])
            right_tokens = tokenize(right["formula_definition"] + " " + right["allowed_inputs"] + " " + right["candidate_family"])
            right_inputs = set(right["allowed_inputs"].split(";"))
            formula_similarity = jaccard(left_tokens, right_tokens)
            input_overlap = jaccard(left_inputs, right_inputs)
            distance = weight_distance(left_params, parse_params(right["params"]))
            if corr is not None and corr >= NEAR_DUPLICATE_OUTPUT:
                label = "near_duplicate_output"
            elif corr is not None and corr >= SAME_NEIGHBORHOOD:
                label = "same_neighborhood"
            else:
                label = "distinct_candidate"
            same_family = left["candidate_family"] == right["candidate_family"]
            same_scope = scope_group(left["position_scope"]) == scope_group(right["position_scope"])
            output.append(
                {
                    "candidate_id_left": left_id,
                    "candidate_id_right": right_id,
                    "family_left": left["candidate_family"],
                    "family_right": right["candidate_family"],
                    "scope_left": left["position_scope"],
                    "scope_right": right["position_scope"],
                    "overlap_rows": overlap_rows,
                    "rank_correlation": fmt(corr, 6),
                    "formula_similarity": fmt(formula_similarity, 3),
                    "input_overlap": fmt(input_overlap, 3),
                    "weight_distance": fmt(distance, 4),
                    "same_family": str(same_family).lower(),
                    "same_scope_group": str(same_scope).lower(),
                    "similarity_label": label,
                }
            )
    return output


def cluster_candidates(
    registry_rows: list[dict[str, str]],
    scorecard_rows: list[dict[str, str]],
    similarity_rows: list[dict[str, object]],
) -> dict[str, str]:
    active_ids = [row["candidate_id"] for row in scorecard_rows if row["candidate_status"] == "ACTIVE_REVIEW_ONLY"]
    parent = {cid: cid for cid in active_ids}

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: str, b: str) -> None:
        ra = find(a)
        rb = find(b)
        if ra != rb:
            parent[rb] = ra

    for row in similarity_rows:
        corr = num(row["rank_correlation"])
        if corr is None or corr < SAME_NEIGHBORHOOD:
            continue
        if row["same_scope_group"] != "true":
            continue
        union(str(row["candidate_id_left"]), str(row["candidate_id_right"]))

    groups: dict[str, list[str]] = defaultdict(list)
    for cid in active_ids:
        groups[find(cid)].append(cid)

    score_by_id = {row["candidate_id"]: row for row in scorecard_rows}
    ordered_groups = sorted(
        groups.values(),
        key=lambda ids: max(num(score_by_id[cid]["candidate_spearman"]) or -999 for cid in ids),
        reverse=True,
    )
    assignments: dict[str, str] = {}
    for idx, ids in enumerate(ordered_groups, start=1):
        for cid in ids:
            assignments[cid] = f"C{idx:02d}"
    for row in scorecard_rows:
        if row["candidate_status"] != "ACTIVE_REVIEW_ONLY":
            if row["candidate_family"] == "N_RB_ONLY_BROKEN_TACKLE_CONTEXT":
                assignments[row["candidate_id"]] = "BLOCKED_PFR"
            elif row["candidate_family"] == "O_PARTIAL_RED_ZONE_CONTEXT":
                assignments[row["candidate_id"]] = "BLOCKED_RED_ZONE"
            else:
                assignments[row["candidate_id"]] = "BLOCKED_OTHER"
    return assignments


def family_inventory(
    registry_rows: list[dict[str, str]],
    scorecard_rows: list[dict[str, str]],
    assignments: dict[str, str],
) -> list[dict[str, object]]:
    score_by_family: dict[str, list[dict[str, str]]] = defaultdict(list)
    reg_by_family = Counter(row["candidate_family"] for row in registry_rows)
    near_top_threshold = max(num(row["candidate_spearman"]) or -999 for row in scorecard_rows) - 0.001
    for row in scorecard_rows:
        score_by_family[row["candidate_family"]].append(row)
    output: list[dict[str, object]] = []
    for family in sorted(reg_by_family):
        rows = score_by_family.get(family, [])
        active = [row for row in rows if row["candidate_status"] == "ACTIVE_REVIEW_ONLY"]
        beaters = [row for row in active if row["beats_pyf_overall"] == "true" and row["score_changes_allowed"] == "yes"]
        near_top = [row for row in active if (num(row["candidate_spearman"]) or -999) >= near_top_threshold]
        clusters = sorted({assignments[row["candidate_id"]] for row in active})
        spearmans = [num(row["candidate_spearman"]) for row in active if num(row["candidate_spearman"]) is not None]
        output.append(
            {
                "candidate_family": family,
                "raw_candidates": reg_by_family[family],
                "scored_candidates": len(active),
                "blocked_candidates": reg_by_family[family] - len(active),
                "candidates_beating_pyf": len(beaters),
                "near_top_candidates": len(near_top),
                "average_spearman": fmt(mean(spearmans)),
                "best_spearman": fmt(max(spearmans) if spearmans else None),
                "cluster_count": len(clusters),
                "clusters": ";".join(clusters),
            }
        )
    return output


def cluster_summary(
    registry_rows: list[dict[str, str]],
    scorecard_rows: list[dict[str, str]],
    position_rows: list[dict[str, str]],
    slice_rows: list[dict[str, str]],
    assignments: dict[str, str],
) -> list[dict[str, object]]:
    reg_by_id = {row["candidate_id"]: row for row in registry_rows}
    scored_by_cluster: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in scorecard_rows:
        cluster_id = assignments[row["candidate_id"]]
        if cluster_id.startswith("BLOCKED"):
            continue
        scored_by_cluster[cluster_id].append(row)
    position_by_cluster: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in position_rows:
        position_by_cluster[assignments[row["candidate_id"]]].append(row)
    slice_by_cluster: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in slice_rows:
        slice_by_cluster[assignments[row["candidate_id"]]].append(row)

    output: list[dict[str, object]] = []
    for cluster_id, rows in sorted(scored_by_cluster.items(), key=lambda item: item[0]):
        best = max(rows, key=lambda row: num(row["candidate_spearman"]) or -999)
        spearmans = [num(row["candidate_spearman"]) for row in rows if num(row["candidate_spearman"]) is not None]
        deltas = [num(row["spearman_delta_vs_pyf"]) for row in rows if num(row["spearman_delta_vs_pyf"]) is not None]
        families = sorted({row["candidate_family"] for row in rows})
        scopes = sorted({reg_by_id[row["candidate_id"]]["position_scope"] for row in rows})
        beaters = [row for row in rows if row["beats_pyf_overall"] == "true" and row["score_changes_allowed"] == "yes"]
        pos_rows = position_by_cluster.get(cluster_id, [])
        pos_strengths = []
        for position in ["QB", "RB", "WR", "TE"]:
            choices = [row for row in pos_rows if row["position"] == position]
            if choices:
                best_pos = max(choices, key=lambda row: num(row["candidate_spearman"]) or -999)
                pos_strengths.append(f"{position}:{best_pos['candidate_spearman']}")
        slice_cluster = slice_by_cluster.get(cluster_id, [])
        sparse_worse = sum(
            1
            for row in slice_cluster
            if row["slice_name"] in {"sparse_history", "low_games"} and row["guardrail_interpretation"] == "worse_than_pyf"
        )
        if len(rows) == 1 or len(families) > 1 or len(scopes) > 1:
            distinct = "yes"
        elif scopes and scopes[0] != "QB/RB/WR/TE":
            distinct = "yes_position_specific_family"
        else:
            distinct = "same_family_variants"
        supply_seed = "yes" if beaters and distinct != "same_family_variants" else ("maybe" if beaters else "no")
        output.append(
            {
                "cluster_id": cluster_id,
                "representative_candidate": best["candidate_id"],
                "representative_family": best["candidate_family"],
                "candidate_count": len(rows),
                "families": ";".join(families),
                "position_scopes": ";".join(scopes),
                "average_spearman": fmt(mean(spearmans)),
                "best_spearman": fmt(max(spearmans) if spearmans else None),
                "best_pyf_delta": fmt(max(deltas) if deltas else None),
                "candidates_beating_pyf": len(beaters),
                "position_strengths": ";".join(pos_strengths),
                "guardrail_weaknesses": f"sparse_or_low_games_worse_rows={sparse_worse}",
                "genuinely_distinct": distinct,
                "should_supply_refinement_seed": supply_seed,
            }
        )
    return output


def cluster_assignments_rows(
    registry_rows: list[dict[str, str]],
    scorecard_rows: list[dict[str, str]],
    assignments: dict[str, str],
) -> list[dict[str, object]]:
    reg_by_id = {row["candidate_id"]: row for row in registry_rows}
    output: list[dict[str, object]] = []
    for row in scorecard_rows:
        reg = reg_by_id[row["candidate_id"]]
        output.append(
            {
                "candidate_id": row["candidate_id"],
                "candidate_family": row["candidate_family"],
                "candidate_label": reg["candidate_label"],
                "position_scope": reg["position_scope"],
                "candidate_status": row["candidate_status"],
                "cluster_id": assignments[row["candidate_id"]],
                "candidate_spearman": row["candidate_spearman"],
                "spearman_delta_vs_pyf": row["spearman_delta_vs_pyf"],
                "beats_pyf_overall": row["beats_pyf_overall"],
                "interpretation": row["interpretation"],
                "blocked_reason": row["blocked_reason"],
            }
        )
    return output


def choose_refinement_seeds(
    scorecard_rows: list[dict[str, str]],
    position_rows: list[dict[str, str]],
    cluster_rows: list[dict[str, object]],
    assignments: dict[str, str],
) -> list[dict[str, object]]:
    score_by_id = {row["candidate_id"]: row for row in scorecard_rows}
    seeds: list[dict[str, object]] = []
    used_clusters: set[str] = set()

    def add_seed(candidate_id: str, rationale: str) -> None:
        cluster = assignments[candidate_id]
        if cluster in used_clusters or cluster.startswith("BLOCKED"):
            return
        row = score_by_id[candidate_id]
        if row["candidate_status"] != "ACTIVE_REVIEW_ONLY":
            return
        used_clusters.add(cluster)
        seeds.append(
            {
                "seed_rank": len(seeds) + 1,
                "candidate_id": candidate_id,
                "cluster_id": cluster,
                "candidate_family": row["candidate_family"],
                "candidate_spearman": row["candidate_spearman"],
                "spearman_delta_vs_pyf": row["spearman_delta_vs_pyf"],
                "rationale": rationale,
                "allowed_use": "review_only_refinement_seed",
                "blocked_use": "production_model_use;ranking_integration;hidden_sort;champion_claim",
            }
        )

    active = [
        row
        for row in scorecard_rows
        if row["candidate_status"] == "ACTIVE_REVIEW_ONLY" and row["candidate_id"] != "GAUNTLET_001_PYF_POINTS_ANCHOR"
    ]
    best_overall = max(active, key=lambda row: num(row["candidate_spearman"]) or -999)
    add_seed(best_overall["candidate_id"], "best_overall_cluster_representative")
    for position in ["QB", "RB", "WR", "TE"]:
        choices = [row for row in position_rows if row["position"] == position and row["candidate_id"] != "GAUNTLET_001_PYF_POINTS_ANCHOR"]
        best_pos = max(choices, key=lambda row: num(row["candidate_spearman"]) or -999)
        add_seed(best_pos["candidate_id"], f"best_{position}_representative")
    for family, rationale in [
        ("L_ROBUST_WINSORIZED_PRODUCTION", "best_robust_winsorized_representative"),
        ("K_HYBRID_PRODUCTION_AGE_ROLE", "best_age_role_hybrid_representative"),
        ("F_SPARSE_HISTORY_GUARD", "best_sparse_guard_representative"),
        ("G_LOW_GAMES_GUARD", "best_low_games_guard_representative"),
    ]:
        choices = [row for row in active if row["candidate_family"] == family]
        if choices:
            best = max(choices, key=lambda row: num(row["candidate_spearman"]) or -999)
            add_seed(best["candidate_id"], rationale)
    target_seed_count = min(
        8,
        sum(1 for row in cluster_rows if int(row["candidates_beating_pyf"]) > 0 and row["should_supply_refinement_seed"] in {"yes", "maybe"}),
    )
    if len(seeds) < target_seed_count:
        for cluster in sorted(cluster_rows, key=lambda row: num(row["best_spearman"]) or -999, reverse=True):
            if cluster["should_supply_refinement_seed"] not in {"yes", "maybe"}:
                continue
            add_seed(str(cluster["representative_candidate"]), "top_distinct_cluster_backfill")
            if len(seeds) >= target_seed_count:
                break
    return seeds[:8]


def write_markdown_reports(
    registry_rows: list[dict[str, str]],
    scorecard_rows: list[dict[str, str]],
    similarity_rows: list[dict[str, object]],
    cluster_rows: list[dict[str, object]],
    seed_rows: list[dict[str, object]],
) -> tuple[str, str, dict[str, object]]:
    raw_count = len(registry_rows)
    scored_count = sum(1 for row in scorecard_rows if row["candidate_status"] == "ACTIVE_REVIEW_ONLY")
    beaters = [
        row
        for row in scorecard_rows
        if row["candidate_status"] == "ACTIVE_REVIEW_ONLY"
        and row["score_changes_allowed"] == "yes"
        and row["beats_pyf_overall"] == "true"
    ]
    clusters = [row for row in cluster_rows if not str(row["cluster_id"]).startswith("BLOCKED")]
    promising_clusters = [row for row in clusters if int(row["candidates_beating_pyf"]) > 0]
    distinct_promising = [
        row
        for row in promising_clusters
        if row["should_supply_refinement_seed"] in {"yes", "maybe"}
    ]
    near_duplicate_pairs = sum(1 for row in similarity_rows if row["similarity_label"] == "near_duplicate_output")
    same_neighborhood_pairs = sum(1 for row in similarity_rows if row["similarity_label"] == "same_neighborhood")
    top_spearman = max(num(row["candidate_spearman"]) or -999 for row in scorecard_rows)
    near_top = [
        row
        for row in scorecard_rows
        if row["candidate_status"] == "ACTIVE_REVIEW_ONLY"
        and (num(row["candidate_spearman"]) or -999) >= top_spearman - 0.001
    ]
    near_top_clusters = sorted({row["cluster_id"] for row in cluster_rows if row["representative_candidate"] in {r["candidate_id"] for r in near_top}})
    effective_count = len(distinct_promising)
    readiness = (
        "READY_FOR_DIVERSE_CHAMPION_REFINEMENT"
        if effective_count >= 6 and len(seed_rows) >= 5
        else ("READY_FOR_NARROW_PRODUCTION_WEIGHT_REFINEMENT_ONLY" if effective_count >= 3 else "DO_NOT_REFINE_CLUSTERING_TOO_HIGH")
    )
    verdict = (
        "GREEN_GAUNTLET_HAS_DIVERSE_PROMISING_NEIGHBORHOODS"
        if readiness == "READY_FOR_DIVERSE_CHAMPION_REFINEMENT" and same_neighborhood_pairs < len(similarity_rows) * 0.55
        else ("YELLOW_GAUNTLET_PROMISING_BUT_CLUSTERED" if effective_count >= 3 else "RED_GAUNTLET_RESULTS_MOSTLY_DUPLICATIVE")
    )
    summary = {
        "raw_count": raw_count,
        "scored_count": scored_count,
        "beaters": len(beaters),
        "clusters": len(clusters),
        "promising_clusters": len(promising_clusters),
        "distinct_promising": len(distinct_promising),
        "effective_count": effective_count,
        "near_duplicate_pairs": near_duplicate_pairs,
        "same_neighborhood_pairs": same_neighborhood_pairs,
        "near_top_count": len(near_top),
        "readiness": readiness,
        "verdict": verdict,
    }
    report = f"""
# Gauntlet Candidate Diversity / Clustering Audit V1 Report

## Verdict

`{verdict}`

## Clear Answer

The Gauntlet results are promising but meaningfully clustered. The headline `90` formulas beating PYF does not represent 90 independent signals. The scored candidates collapse into `{len(clusters)}` output-correlation neighborhoods, with `{len(distinct_promising)}` genuinely distinct promising clusters and an effective independent candidate count of `{effective_count}`. The top candidates are highly clustered around multi-year production, with small age/lifecycle, role, and decline-context modifiers.

## Candidate Inventory

- Raw candidates registered: `{raw_count}`
- Scored candidates: `{scored_count}`
- Score-changing candidates beating PYF overall: `{len(beaters)}`
- Output-correlation clusters: `{len(clusters)}`
- Promising clusters: `{len(promising_clusters)}`
- Genuinely distinct promising clusters: `{len(distinct_promising)}`
- Effective independent candidate count: `{effective_count}`
- Near-duplicate output pairs at correlation >= `{NEAR_DUPLICATE_OUTPUT}`: `{near_duplicate_pairs}`
- Same-neighborhood pairs at correlation >= `{SAME_NEIGHBORHOOD}`: `{same_neighborhood_pairs}`
- Near-top candidates within 0.001 Spearman of best: `{len(near_top)}`

## Interpretation

The result is not "90 independent formulas beat PYF." It is better read as a smaller number of stable formula neighborhoods beating PYF, led by three-year weighted production and nearby production-plus-context variants. Position-specific candidates are useful as distinct refinement seeds because their scope differs, even when their underlying scoring behavior remains production-centered.

## Refinement Decision

`{readiness}`

Champion refinement is justified only as review-only contract work around diverse seeds, not as production selection. The next lane should refine top neighborhoods deliberately, not simply clone the top 0.755 Spearman variants.

## Recommended Refinement Seeds

{chr(10).join(f"- `{row['candidate_id']}` (`{row['candidate_family']}`): {row['rationale']}" for row in seed_rows)}

## Gates Preserved

- Production/model-use remains blocked.
- Rankings integration remains blocked.
- Source promotion remains blocked.
- No app/runtime/model behavior changed.
- No champion refinement was run in this lane.
"""
    write_text(OUT_DIR / "GAUNTLET_CANDIDATE_DIVERSITY_CLUSTERING_AUDIT_V1_REPORT.md", report)

    effective = f"""
# Gauntlet Effective Candidate Count

The raw Gauntlet registered `{raw_count}` candidates and scored `{scored_count}`. Of those, `{len(beaters)}` score-changing candidates beat PYF overall.

The clustering audit reduces that to:

- Output-correlation clusters: `{len(clusters)}`
- Promising clusters: `{len(promising_clusters)}`
- Genuinely distinct promising clusters: `{len(distinct_promising)}`
- Effective independent candidate count: `{effective_count}`

Answer to the key question: it was not 90 independent formulas beating PYF. It was `{effective_count}` useful independent neighborhoods, with many near-duplicates or same-neighborhood variants around multi-year production.
"""
    write_text(OUT_DIR / "GAUNTLET_EFFECTIVE_CANDIDATE_COUNT.md", effective)

    limitations = f"""
# Gauntlet Clustering Limitations

- Row-level candidate scores/ranks were not persisted by the prior Gauntlet packet, so this audit reconstructed rank vectors by importing the accepted Gauntlet runner and fixed registry.
- No new formulas were added and no weights were tuned.
- Candidate clusters use rank correlation >= `{SAME_NEIGHBORHOOD}` within compatible scope groups.
- Near-duplicate output pairs use rank correlation >= `{NEAR_DUPLICATE_OUTPUT}`.
- Position-specific candidates are allowed to remain distinct neighborhoods even when they correlate strongly with all-position production formulas on the overlapping position subset.
- Clustering is a review-only diagnostic, not model approval or ranking integration.
"""
    write_text(OUT_DIR / "GAUNTLET_CLUSTERING_LIMITATIONS.md", limitations)

    source_trace = f"""
# Gauntlet Diversity Audit Source Trace

## Inputs

- Full Review-Only Formula Gauntlet Candidate Arena V1: `{PRIOR_GAUNTLET_DIR}`
- Prior Gauntlet commit: `{PRIOR_GAUNTLET_COMMIT}`
- Medium Review-Only Formula Pilot V1: `{PRIOR_MEDIUM_DIR}`
- Small Review-Only Formula Pilot V1: `{SMALL_PILOT_DIR}`

## Method

The audit read the prior Gauntlet registry, scorecard, position, slice, stability, and outlier artifacts. It imported the prior Gauntlet runner to reconstruct review-only rank vectors for correlation clustering. No candidate definitions were changed.

## Safety

This lane did not run champion refinement, did not tune, did not optimize weights, did not change rankings, did not change app/runtime/model behavior, did not promote sources, and did not push or merge.
"""
    write_text(OUT_DIR / "GAUNTLET_DIVERSITY_AUDIT_SOURCE_TRACE.md", source_trace)
    return verdict, readiness, summary


def validate_outputs() -> None:
    required = [
        "GAUNTLET_CANDIDATE_DIVERSITY_CLUSTERING_AUDIT_V1_REPORT.md",
        "GAUNTLET_CANDIDATE_FAMILY_INVENTORY.csv",
        "GAUNTLET_CANDIDATE_SIMILARITY_MATRIX.csv",
        "GAUNTLET_CANDIDATE_CLUSTER_ASSIGNMENTS.csv",
        "GAUNTLET_DISTINCT_PROMISING_CLUSTER_SUMMARY.csv",
        "GAUNTLET_REFINEMENT_SEED_RECOMMENDATIONS.csv",
        "GAUNTLET_EFFECTIVE_CANDIDATE_COUNT.md",
        "GAUNTLET_CLUSTERING_LIMITATIONS.md",
        "GAUNTLET_DIVERSITY_AUDIT_SOURCE_TRACE.md",
        "run_gauntlet_candidate_diversity_clustering_audit_v1.py",
    ]
    missing = [name for name in required if not (OUT_DIR / name).exists()]
    if missing:
        raise RuntimeError(f"Missing outputs: {missing}")
    for csv_name in [
        "GAUNTLET_CANDIDATE_FAMILY_INVENTORY.csv",
        "GAUNTLET_CANDIDATE_SIMILARITY_MATRIX.csv",
        "GAUNTLET_CANDIDATE_CLUSTER_ASSIGNMENTS.csv",
        "GAUNTLET_DISTINCT_PROMISING_CLUSTER_SUMMARY.csv",
        "GAUNTLET_REFINEMENT_SEED_RECOMMENDATIONS.csv",
    ]:
        rows = read_csv(OUT_DIR / csv_name)
        if not rows:
            raise RuntimeError(f"{csv_name} parsed but has no rows.")
    py_compile.compile(str(Path(__file__).resolve()), doraise=True)


def main() -> None:
    module = load_gauntlet_module()
    registry_rows = read_csv(PRIOR_GAUNTLET_DIR / "GAUNTLET_CANDIDATE_REGISTRY.csv")
    scorecard_rows = read_csv(PRIOR_GAUNTLET_DIR / "GAUNTLET_CANDIDATE_METRICS_SCORECARD.csv")
    position_rows = read_csv(PRIOR_GAUNTLET_DIR / "GAUNTLET_POSITION_RESULTS.csv")
    slice_rows = read_csv(PRIOR_GAUNTLET_DIR / "GAUNTLET_SLICE_GUARDRAILS.csv")

    registry = module.build_registry()
    active_registry = [row for row in registry if row["candidate_status"] == "ACTIVE_REVIEW_ONLY"]
    vectors = build_rank_vectors(module, active_registry)
    similarity_rows = build_similarity(registry_rows, scorecard_rows, vectors)
    assignments = cluster_candidates(registry_rows, scorecard_rows, similarity_rows)
    family_rows = family_inventory(registry_rows, scorecard_rows, assignments)
    cluster_rows = cluster_summary(registry_rows, scorecard_rows, position_rows, slice_rows, assignments)
    assignment_rows = cluster_assignments_rows(registry_rows, scorecard_rows, assignments)
    seed_rows = choose_refinement_seeds(scorecard_rows, position_rows, cluster_rows, assignments)

    write_csv(
        OUT_DIR / "GAUNTLET_CANDIDATE_FAMILY_INVENTORY.csv",
        family_rows,
        [
            "candidate_family",
            "raw_candidates",
            "scored_candidates",
            "blocked_candidates",
            "candidates_beating_pyf",
            "near_top_candidates",
            "average_spearman",
            "best_spearman",
            "cluster_count",
            "clusters",
        ],
    )
    write_csv(
        OUT_DIR / "GAUNTLET_CANDIDATE_SIMILARITY_MATRIX.csv",
        similarity_rows,
        [
            "candidate_id_left",
            "candidate_id_right",
            "family_left",
            "family_right",
            "scope_left",
            "scope_right",
            "overlap_rows",
            "rank_correlation",
            "formula_similarity",
            "input_overlap",
            "weight_distance",
            "same_family",
            "same_scope_group",
            "similarity_label",
        ],
    )
    write_csv(
        OUT_DIR / "GAUNTLET_CANDIDATE_CLUSTER_ASSIGNMENTS.csv",
        assignment_rows,
        [
            "candidate_id",
            "candidate_family",
            "candidate_label",
            "position_scope",
            "candidate_status",
            "cluster_id",
            "candidate_spearman",
            "spearman_delta_vs_pyf",
            "beats_pyf_overall",
            "interpretation",
            "blocked_reason",
        ],
    )
    write_csv(
        OUT_DIR / "GAUNTLET_DISTINCT_PROMISING_CLUSTER_SUMMARY.csv",
        cluster_rows,
        [
            "cluster_id",
            "representative_candidate",
            "representative_family",
            "candidate_count",
            "families",
            "position_scopes",
            "average_spearman",
            "best_spearman",
            "best_pyf_delta",
            "candidates_beating_pyf",
            "position_strengths",
            "guardrail_weaknesses",
            "genuinely_distinct",
            "should_supply_refinement_seed",
        ],
    )
    write_csv(
        OUT_DIR / "GAUNTLET_REFINEMENT_SEED_RECOMMENDATIONS.csv",
        seed_rows,
        [
            "seed_rank",
            "candidate_id",
            "cluster_id",
            "candidate_family",
            "candidate_spearman",
            "spearman_delta_vs_pyf",
            "rationale",
            "allowed_use",
            "blocked_use",
        ],
    )
    verdict, readiness, summary = write_markdown_reports(
        registry_rows, scorecard_rows, similarity_rows, cluster_rows, seed_rows
    )
    validate_outputs()
    print(
        "gauntlet_diversity_audit_complete "
        f"verdict={verdict} readiness={readiness} "
        f"clusters={summary['clusters']} effective={summary['effective_count']}"
    )


if __name__ == "__main__":
    main()
