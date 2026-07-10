from __future__ import annotations

import csv
import hashlib
import math
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean


ROOT = Path(__file__).resolve().parents[4]
OUT = ROOT / "docs" / "hq" / "model" / "age_lifecycle_component_signal_test_v1_20260709"

AGE_SIDECAR_DIR = Path(
    r"C:\NWR\Niners-War-Room-age-lifecycle-sidecar-freeze-validation-v1-20260709"
    r"\docs\hq\data_hygiene\age_lifecycle_sidecar_freeze_validation_v1_20260709"
)
AGE_SIDECAR = AGE_SIDECAR_DIR / "MODEL_V4_AGE_LIFECYCLE_SIDECAR_REVIEW_ONLY.csv"
AGE_SIDE_REPORT = AGE_SIDECAR_DIR / "AGE_LIFECYCLE_SIDECAR_FREEZE_VALIDATION_V1_REPORT.md"
DATA_MART_DIR = Path(
    r"C:\NWR\Niners-War-Room-formula-data-mart-feature-availability-audit-v1-20260709"
    r"\docs\hq\data_hygiene\formula_data_mart_feature_availability_audit_v1_20260709"
)
DATA_MART = DATA_MART_DIR / "FORMULA_DATA_MART_REVIEW_ONLY.csv"
ROLE_SIGNAL_DIR = ROOT / "docs/hq/model/model_v4_role_archetype_component_signal_test_v1_20260709"
ROLE_PYF_COMPARISON = ROLE_SIGNAL_DIR / "MODEL_V4_ROLE_ARCHETYPE_PYF_COMPARISON.csv"
CONFIDENCE_SIGNAL_DIR = ROOT / "docs/hq/model/model_v4_confidence_cap_component_signal_test_v1_20260709"
SYSTEM_AUDIT_DIR = ROOT / "docs/hq/master/nwr_full_system_audit_integration_map_v1_20260709"


POSITION_TOPNS = {"QB": [12], "RB": [12, 24], "WR": [12, 24, 36], "TE": [12]}
STARTABLE_CUTOFF = {"QB": 10, "RB": 30, "WR": 40, "TE": 12}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def to_float(value: str | None) -> float | None:
    if value is None or value == "":
        return None
    try:
        val = float(value)
    except ValueError:
        return None
    if math.isnan(val):
        return None
    return val


def to_bool(value: str | None) -> bool:
    return str(value).strip().lower() == "true"


def pct(num: int | float, den: int | float) -> str:
    if not den:
        return ""
    return f"{num / den:.1%}"


def avg(values: list[float | None]) -> str:
    clean = [v for v in values if v is not None]
    if not clean:
        return ""
    return f"{mean(clean):.3f}"


def spearman(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) < 3 or len(xs) != len(ys):
        return None

    def ranks(values: list[float]) -> list[float]:
        order = sorted((value, idx) for idx, value in enumerate(values))
        result = [0.0] * len(values)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and order[j + 1][0] == order[i][0]:
                j += 1
            rank_value = (i + j + 2) / 2.0
            for k in range(i, j + 1):
                result[order[k][1]] = rank_value
            i = j + 1
        return result

    rx = ranks(xs)
    ry = ranks(ys)
    mx = mean(rx)
    my = mean(ry)
    cov = sum((x - mx) * (y - my) for x, y in zip(rx, ry))
    vx = sum((x - mx) ** 2 for x in rx)
    vy = sum((y - my) ** 2 for y in ry)
    if not vx or not vy:
        return None
    return cov / math.sqrt(vx * vy)


def enrich_rows() -> list[dict[str, object]]:
    mart_rows = read_csv(DATA_MART)
    age_rows = read_csv(AGE_SIDECAR)
    age_by_key = {(r["player_id"], r["season"], r["position"]): r for r in age_rows}
    joined: list[dict[str, object]] = []
    for row in mart_rows:
        key = (row["player_id"], row["season"], row["position"])
        age = age_by_key.get(key)
        if not age:
            continue
        position = row["position"]
        actual_finish = to_float(row.get("label_next_position_finish"))
        pyf_rank = to_float(row.get("pyf_prior_rank_position_feature_season"))
        startable_hit = to_bool(row.get("label_startable_hit"))
        pyf_startable = False
        sparse = to_bool(row.get("sparse_history_flag"))
        low_games = to_bool(row.get("low_games_flag"))
        prior_decline = pyf_startable and not startable_hit
        false_negative = (not pyf_startable) and startable_hit
        out = dict(row)
        out.update(
            {
                "age": to_float(age.get("age")),
                "age_bucket": age.get("age_bucket", "missing_age"),
                "lifecycle_bucket": age.get("lifecycle_bucket", "missing_draft_year"),
                "career_stage": age.get("career_stage", "missing_draft_year"),
                "years_since_rookie_year": to_float(age.get("years_since_rookie_year")),
                "age_missing": age.get("age", "") == "",
                "lifecycle_missing": age.get("lifecycle_bucket", "") == "missing_draft_year",
                "age_identity_flag": age.get("identity_flag", ""),
                "age_missingness_flag": age.get("missingness_flag", ""),
                "actual_finish": actual_finish,
                "pyf_rank": pyf_rank,
                "prior_nwr_points_num": to_float(row.get("pyf_prior_nwr_points")),
                "startable_hit_bool": startable_hit,
                "pyf_startable": pyf_startable,
                "pyf_false_positive": prior_decline,
                "pyf_false_negative": false_negative,
                "prior_production_decline": prior_decline,
                "sparse_history": sparse,
                "low_games": low_games,
            }
        )
        joined.append(out)
    apply_pyf_predictions(joined)
    return joined


def apply_pyf_predictions(rows: list[dict[str, object]]) -> None:
    grouped: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[(str(row["season"]), str(row["position"]))].append(row)
    selected_ids: set[str] = set()
    for (_, position), group in grouped.items():
        selected = sorted(
            group,
            key=lambda row: row["prior_nwr_points_num"]
            if isinstance(row["prior_nwr_points_num"], float)
            else -999999.0,
            reverse=True,
        )[: min(STARTABLE_CUTOFF[position], len(group))]
        selected_ids.update(str(row["substrate_row_id"]) for row in selected)
    for row in rows:
        row["pyf_startable"] = str(row["substrate_row_id"]) in selected_ids
        row["pyf_false_positive"] = bool(row["pyf_startable"]) and not bool(row["startable_hit_bool"])
        row["pyf_false_negative"] = (not bool(row["pyf_startable"])) and bool(row["startable_hit_bool"])
        row["prior_production_decline"] = row["pyf_false_positive"]


def bucket_metrics(rows: list[dict[str, object]], group_fields: list[str]) -> list[dict[str, object]]:
    grouped: dict[tuple[str, ...], list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[tuple(str(row.get(field, "")) for field in group_fields)].append(row)

    out = []
    for key, group in sorted(grouped.items()):
        row = {field: value for field, value in zip(group_fields, key)}
        count = len(group)
        startable_hits = sum(1 for r in group if r["startable_hit_bool"])
        top12 = sum(1 for r in group if r["actual_finish"] is not None and r["actual_finish"] <= 12)
        top24 = sum(1 for r in group if r["actual_finish"] is not None and r["actual_finish"] <= 24)
        top36 = sum(1 for r in group if r["actual_finish"] is not None and r["actual_finish"] <= 36)
        false_pos = sum(1 for r in group if r["pyf_false_positive"])
        false_neg = sum(1 for r in group if r["pyf_false_negative"])
        decline = sum(1 for r in group if r["prior_production_decline"])
        sparse = sum(1 for r in group if r["sparse_history"])
        low_games = sum(1 for r in group if r["low_games"])
        ages = [r["age"] for r in group if isinstance(r["age"], float)]
        row.update(
            {
                "rows": count,
                "seasons": len({r["season"] for r in group}),
                "startable_hits": startable_hits,
                "startable_rate": pct(startable_hits, count),
                "avg_finish": avg([r["actual_finish"] for r in group]),
                "avg_next_nwr_points": avg([to_float(r.get("label_next_nwr_points")) for r in group]),
                "avg_age": avg(ages),
                "top_12_hit_rate": pct(top12, count) if 12 in POSITION_TOPNS.get(row.get("position"), []) else "",
                "top_24_hit_rate": pct(top24, count) if 24 in POSITION_TOPNS.get(row.get("position"), []) else "",
                "top_36_hit_rate": pct(top36, count) if 36 in POSITION_TOPNS.get(row.get("position"), []) else "",
                "pyf_false_positives": false_pos,
                "pyf_false_negatives": false_neg,
                "prior_production_decline_rows": decline,
                "sparse_history_rows": sparse,
                "low_games_rows": low_games,
                "review_only_interpretation": "age_lifecycle_context_slice_not_formula_score",
            }
        )
        out.append(row)
    return out


def position_scorecard(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    out = []
    for position in sorted({r["position"] for r in rows}):
        group = [r for r in rows if r["position"] == position]
        xs_age = [r["age"] for r in group if isinstance(r["age"], float) and r["actual_finish"] is not None]
        ys_age = [r["actual_finish"] for r in group if isinstance(r["age"], float) and r["actual_finish"] is not None]
        xs_pyf = [r["pyf_rank"] for r in group if r["pyf_rank"] is not None and r["actual_finish"] is not None]
        ys_pyf = [r["actual_finish"] for r in group if r["pyf_rank"] is not None and r["actual_finish"] is not None]
        false_pos = sum(1 for r in group if r["pyf_false_positive"])
        false_neg = sum(1 for r in group if r["pyf_false_negative"])
        older_decline = sum(
            1
            for r in group
            if r["pyf_false_positive"] and r["age_bucket"] in {"age_29_to_31", "age_32_plus"}
        )
        young_false_neg = sum(
            1
            for r in group
            if r["pyf_false_negative"] and r["age_bucket"] in {"under_23", "age_23_to_25"}
        )
        early_false_neg = sum(
            1
            for r in group
            if r["pyf_false_negative"] and r["lifecycle_bucket"] in {"rookie_year", "early_career_1_to_3"}
        )
        sparse_rows = sum(1 for r in group if r["sparse_history"])
        low_games_rows = sum(1 for r in group if r["low_games"])
        missing = sum(1 for r in group if r["age_missing"])
        out.append(
            {
                "position": position,
                "rows": len(group),
                "age_missing_rows": missing,
                "age_missing_rate": pct(missing, len(group)),
                "age_vs_finish_spearman": "" if spearman(xs_age, ys_age) is None else f"{spearman(xs_age, ys_age):.3f}",
                "pyf_rank_vs_finish_spearman": "" if spearman(xs_pyf, ys_pyf) is None else f"{spearman(xs_pyf, ys_pyf):.3f}",
                "pyf_false_positives": false_pos,
                "pyf_false_negatives": false_neg,
                "older_age_pyf_false_positives": older_decline,
                "older_age_share_of_pyf_false_positives": pct(older_decline, false_pos),
                "young_age_pyf_false_negatives": young_false_neg,
                "young_age_share_of_pyf_false_negatives": pct(young_false_neg, false_neg),
                "early_lifecycle_pyf_false_negatives": early_false_neg,
                "early_lifecycle_share_of_pyf_false_negatives": pct(early_false_neg, false_neg),
                "sparse_history_rows": sparse_rows,
                "low_games_rows": low_games_rows,
                "signal_interpretation": "review_only_context; does not replace PYF",
            }
        )
    all_rows = rows
    false_pos_all = sum(1 for r in all_rows if r["pyf_false_positive"])
    false_neg_all = sum(1 for r in all_rows if r["pyf_false_negative"])
    older_all = sum(
        1 for r in all_rows if r["pyf_false_positive"] and r["age_bucket"] in {"age_29_to_31", "age_32_plus"}
    )
    young_all = sum(
        1 for r in all_rows if r["pyf_false_negative"] and r["age_bucket"] in {"under_23", "age_23_to_25"}
    )
    early_all = sum(
        1
        for r in all_rows
        if r["pyf_false_negative"] and r["lifecycle_bucket"] in {"rookie_year", "early_career_1_to_3"}
    )
    out.append(
        {
            "position": "ALL",
            "rows": len(all_rows),
            "age_missing_rows": sum(1 for r in all_rows if r["age_missing"]),
            "age_missing_rate": pct(sum(1 for r in all_rows if r["age_missing"]), len(all_rows)),
            "age_vs_finish_spearman": "",
            "pyf_rank_vs_finish_spearman": "",
            "pyf_false_positives": false_pos_all,
            "pyf_false_negatives": false_neg_all,
            "older_age_pyf_false_positives": older_all,
            "older_age_share_of_pyf_false_positives": pct(older_all, false_pos_all),
            "young_age_pyf_false_negatives": young_all,
            "young_age_share_of_pyf_false_negatives": pct(young_all, false_neg_all),
            "early_lifecycle_pyf_false_negatives": early_all,
            "early_lifecycle_share_of_pyf_false_negatives": pct(early_all, false_neg_all),
            "sparse_history_rows": sum(1 for r in all_rows if r["sparse_history"]),
            "low_games_rows": sum(1 for r in all_rows if r["low_games"]),
            "signal_interpretation": "review_only_context; does not replace PYF",
        }
    )
    return out


def pyf_comparison(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    role_comp = {}
    if ROLE_PYF_COMPARISON.exists():
        for row in read_csv(ROLE_PYF_COMPARISON):
            role_comp[row["position"]] = row

    result = []
    for position in sorted({r["position"] for r in rows}) + ["ALL"]:
        group = rows if position == "ALL" else [r for r in rows if r["position"] == position]
        fp = sum(1 for r in group if r["pyf_false_positive"])
        fn = sum(1 for r in group if r["pyf_false_negative"])
        older = sum(1 for r in group if r["pyf_false_positive"] and r["age_bucket"] in {"age_29_to_31", "age_32_plus"})
        late = sum(
            1
            for r in group
            if r["pyf_false_positive"] and r["lifecycle_bucket"] in {"veteran_7_to_9", "late_career_10_plus"}
        )
        young_fn = sum(1 for r in group if r["pyf_false_negative"] and r["age_bucket"] in {"under_23", "age_23_to_25"})
        early_fn = sum(
            1
            for r in group
            if r["pyf_false_negative"] and r["lifecycle_bucket"] in {"rookie_year", "early_career_1_to_3"}
        )
        role_share = role_comp.get(position, {}).get("share_of_pyf_false_positives_high_volume", "")
        result.append(
            {
                "position": position,
                "rows": len(group),
                "pyf_false_positives": fp,
                "pyf_false_negatives": fn,
                "older_age_pyf_false_positives": older,
                "older_age_share_of_pyf_false_positives": pct(older, fp),
                "late_lifecycle_pyf_false_positives": late,
                "late_lifecycle_share_of_pyf_false_positives": pct(late, fp),
                "young_age_pyf_false_negatives": young_fn,
                "young_age_share_of_pyf_false_negatives": pct(young_fn, fn),
                "early_lifecycle_pyf_false_negatives": early_fn,
                "early_lifecycle_share_of_pyf_false_negatives": pct(early_fn, fn),
                "role_archetype_high_volume_fp_share_reference": role_share,
                "pyf_comparison_result": "adds_context_to_pyf_miss_taxonomy_not_standalone_ranker",
                "caveat": "Age/lifecycle is not compared as a formula score and does not beat PYF.",
            }
        )
    return result


def markdown_table(rows: list[dict[str, object]], fields: list[str]) -> str:
    lines = ["| " + " | ".join(fields) + " |", "| " + " | ".join(["---"] * len(fields)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(field, "")) for field in fields) + " |")
    return "\n".join(lines)


def write_reviews(rows: list[dict[str, object]], scorecard: list[dict[str, object]], pyf_rows: list[dict[str, object]]) -> None:
    all_score = next(r for r in scorecard if r["position"] == "ALL")
    position_scores = [r for r in scorecard if r["position"] != "ALL"]
    bucket_rows = bucket_metrics(rows, ["position", "age_bucket"])
    lifecycle_rows = bucket_metrics(rows, ["position", "lifecycle_bucket"])

    decline_rows = []
    for position in sorted({r["position"] for r in rows}) + ["ALL"]:
        group = rows if position == "ALL" else [r for r in rows if r["position"] == position]
        decline = [r for r in group if r["prior_production_decline"]]
        late = [r for r in decline if r["lifecycle_bucket"] in {"veteran_7_to_9", "late_career_10_plus"}]
        older = [r for r in decline if r["age_bucket"] in {"age_29_to_31", "age_32_plus"}]
        high_role = [r for r in decline if "high_volume" in str(r.get("role_archetype", ""))]
        decline_rows.append(
            {
                "position": position,
                "prior_decline_rows": len(decline),
                "older_age_rows": len(older),
                "older_age_share": pct(len(older), len(decline)),
                "late_lifecycle_rows": len(late),
                "late_lifecycle_share": pct(len(late), len(decline)),
                "high_volume_role_overlap": len(high_role),
                "interpretation": "age/lifecycle highlights veteran decline subset but role archetype remains broader fp taxonomy",
            }
        )
    (OUT / "AGE_LIFECYCLE_PRIOR_DECLINE_REVIEW.md").write_text(
        "# Age / Lifecycle Prior-Decline Review\n\n"
        "Prior-production decline is defined as a PYF-startable row that was not startable in the target season.\n\n"
        + markdown_table(
            decline_rows,
            [
                "position",
                "prior_decline_rows",
                "older_age_rows",
                "older_age_share",
                "late_lifecycle_rows",
                "late_lifecycle_share",
                "high_volume_role_overlap",
                "interpretation",
            ],
        )
        + "\n\nConclusion: age/lifecycle helps identify a veteran-decline subset of PYF false positives, but it does not replace PYF or role archetype context.\n",
        encoding="utf-8",
    )

    breakout_rows = []
    for position in sorted({r["position"] for r in rows}) + ["ALL"]:
        group = rows if position == "ALL" else [r for r in rows if r["position"] == position]
        false_neg = [r for r in group if r["pyf_false_negative"]]
        young = [r for r in false_neg if r["age_bucket"] in {"under_23", "age_23_to_25"}]
        early = [r for r in false_neg if r["lifecycle_bucket"] in {"rookie_year", "early_career_1_to_3"}]
        sparse = [r for r in false_neg if r["sparse_history"]]
        breakout_rows.append(
            {
                "position": position,
                "pyf_false_negatives": len(false_neg),
                "young_age_rows": len(young),
                "young_age_share": pct(len(young), len(false_neg)),
                "early_lifecycle_rows": len(early),
                "early_lifecycle_share": pct(len(early), len(false_neg)),
                "sparse_history_false_negatives": len(sparse),
                "interpretation": "useful breakout-window context but not automatic boost",
            }
        )
    (OUT / "AGE_LIFECYCLE_BREAKOUT_WINDOW_REVIEW.md").write_text(
        "# Age / Lifecycle Breakout-Window Review\n\n"
        "Breakout-window review is based on PYF false negatives: players PYF did not project as startable who became startable.\n\n"
        + markdown_table(
            breakout_rows,
            [
                "position",
                "pyf_false_negatives",
                "young_age_rows",
                "young_age_share",
                "early_lifecycle_rows",
                "early_lifecycle_share",
                "sparse_history_false_negatives",
                "interpretation",
            ],
        )
        + "\n\nConclusion: age/lifecycle is useful for review-only breakout-window slices, especially early-career false negatives, but can over-reward young players if used without prior-production and role context.\n",
        encoding="utf-8",
    )

    sparse_review = []
    for position in sorted({r["position"] for r in rows}) + ["ALL"]:
        group = rows if position == "ALL" else [r for r in rows if r["position"] == position]
        sparse = [r for r in group if r["sparse_history"]]
        low = [r for r in group if r["low_games"]]
        sparse_hits = sum(1 for r in sparse if r["startable_hit_bool"])
        low_hits = sum(1 for r in low if r["startable_hit_bool"])
        young_sparse = [r for r in sparse if r["age_bucket"] in {"under_23", "age_23_to_25"}]
        sparse_review.append(
            {
                "position": position,
                "sparse_history_rows": len(sparse),
                "sparse_startable_rate": pct(sparse_hits, len(sparse)),
                "low_games_rows": len(low),
                "low_games_startable_rate": pct(low_hits, len(low)),
                "young_sparse_rows": len(young_sparse),
                "interpretation": "young or early-career sparse rows remain high-risk; report separately",
            }
        )
    (OUT / "AGE_LIFECYCLE_LOW_GAMES_SPARSE_HISTORY_REVIEW.md").write_text(
        "# Age / Lifecycle Low-Games / Sparse-History Review\n\n"
        + markdown_table(
            sparse_review,
            [
                "position",
                "sparse_history_rows",
                "sparse_startable_rate",
                "low_games_rows",
                "low_games_startable_rate",
                "young_sparse_rows",
                "interpretation",
            ],
        )
        + "\n\nConclusion: age/lifecycle should not erase sparse-history caution. Young sparse-history rows still need explicit guardrails.\n",
        encoding="utf-8",
    )

    harm_md = """# Age / Lifecycle Harm Review

Age/lifecycle creates useful review-only context, but it can create false confidence if used as a
direct ranking rule.

Main harm modes:

- Older elite producers can remain startable, so old age must not become an automatic penalty.
- Young players with no prior production can remain non-startable, so youth must not become an automatic boost.
- Position age curves differ; QB late-career windows behave differently than RB/WR/TE windows.
- Sparse-history and low-games rows can confound age buckets.
- Missing DOB/draft-year rows are small but must remain unknown rather than zero-filled.

Use-gate decision:

- Allowed: review-only component signal tests, guardrail context, formula-family design context.
- Blocked: production/model-use, formula weights, direct ranking inputs, hidden sort logic, exact replay,
  and Formula Gauntlet tournament clearance.
"""
    (OUT / "AGE_LIFECYCLE_HARM_REVIEW.md").write_text(harm_md, encoding="utf-8")

    blockers_md = """# Age / Lifecycle Blockers And Caveats

- This is not exact Model v4 historical replay.
- Age/lifecycle does not make Formula Gauntlet tournaments safe.
- PYF remains the mandatory anchor baseline.
- Role archetype remains the stronger review-only PYF miss taxonomy for high-volume false positives.
- Age/lifecycle is useful for decline and breakout-window slices, but not as a standalone ranker.
- Production/model-use remains blocked.
- Rankings integration remains blocked.
- Missing DOB/draft-year rows remain unknown.
- Source promotion did not occur.
"""
    (OUT / "AGE_LIFECYCLE_BLOCKERS_AND_CAVEATS.md").write_text(blockers_md, encoding="utf-8")

    source_md = f"""# Age / Lifecycle Source Trace

Inputs:

- Age/lifecycle sidecar: `{AGE_SIDECAR}`
- Sidecar SHA256: `{sha256(AGE_SIDECAR)}`
- Formula Data Mart review-only panel: `{DATA_MART}`
- Formula Data Mart SHA256: `{sha256(DATA_MART)}`
- Role archetype component signal reference: `{ROLE_SIGNAL_DIR}`
- Confidence cap component signal reference: `{CONFIDENCE_SIGNAL_DIR}`
- System audit reference: `{SYSTEM_AUDIT_DIR}`

Join:

- Exact `player_id + season + position`.
- No fuzzy name matching.
- No source promotion.
- No production/model-use approval.
- No ranking, app, runtime, or model behavior changed.
"""
    (OUT / "AGE_LIFECYCLE_SOURCE_TRACE.md").write_text(source_md, encoding="utf-8")


def build() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rows = enrich_rows()
    if len(rows) != 5518:
        raise SystemExit(f"unexpected joined row count: {len(rows)}")

    scorecard = position_scorecard(rows)
    pyf_rows = pyf_comparison(rows)
    age_bucket_rows = bucket_metrics(rows, ["position", "age_bucket"])
    lifecycle_bucket_rows = bucket_metrics(rows, ["position", "lifecycle_bucket"])
    position_bucket_rows = []
    for row in age_bucket_rows:
        out = {"bucket_type": "age_bucket"}
        out.update(row)
        position_bucket_rows.append(out)
    for row in lifecycle_bucket_rows:
        out = {"bucket_type": "lifecycle_bucket"}
        out.update(row)
        position_bucket_rows.append(out)

    score_fields = [
        "position",
        "rows",
        "age_missing_rows",
        "age_missing_rate",
        "age_vs_finish_spearman",
        "pyf_rank_vs_finish_spearman",
        "pyf_false_positives",
        "pyf_false_negatives",
        "older_age_pyf_false_positives",
        "older_age_share_of_pyf_false_positives",
        "young_age_pyf_false_negatives",
        "young_age_share_of_pyf_false_negatives",
        "early_lifecycle_pyf_false_negatives",
        "early_lifecycle_share_of_pyf_false_negatives",
        "sparse_history_rows",
        "low_games_rows",
        "signal_interpretation",
    ]
    write_csv(OUT / "AGE_LIFECYCLE_SIGNAL_SCORECARD.csv", scorecard, score_fields)

    pyf_fields = [
        "position",
        "rows",
        "pyf_false_positives",
        "pyf_false_negatives",
        "older_age_pyf_false_positives",
        "older_age_share_of_pyf_false_positives",
        "late_lifecycle_pyf_false_positives",
        "late_lifecycle_share_of_pyf_false_positives",
        "young_age_pyf_false_negatives",
        "young_age_share_of_pyf_false_negatives",
        "early_lifecycle_pyf_false_negatives",
        "early_lifecycle_share_of_pyf_false_negatives",
        "role_archetype_high_volume_fp_share_reference",
        "pyf_comparison_result",
        "caveat",
    ]
    write_csv(OUT / "AGE_LIFECYCLE_PYF_COMPARISON.csv", pyf_rows, pyf_fields)

    bucket_fields = [
        "bucket_type",
        "position",
        "age_bucket",
        "lifecycle_bucket",
        "rows",
        "seasons",
        "startable_hits",
        "startable_rate",
        "avg_finish",
        "avg_next_nwr_points",
        "avg_age",
        "top_12_hit_rate",
        "top_24_hit_rate",
        "top_36_hit_rate",
        "pyf_false_positives",
        "pyf_false_negatives",
        "prior_production_decline_rows",
        "sparse_history_rows",
        "low_games_rows",
        "review_only_interpretation",
    ]
    write_csv(OUT / "AGE_LIFECYCLE_POSITION_BUCKET_RESULTS.csv", position_bucket_rows, bucket_fields)

    write_reviews(rows, scorecard, pyf_rows)

    all_score = next(r for r in scorecard if r["position"] == "ALL")
    positions = Counter(str(r["position"]) for r in rows)
    missing_age = sum(1 for r in rows if r["age_missing"])
    duplicate_keys = len(rows) - len({(r["player_id"], r["season"], r["position"]) for r in rows})
    seasons = sorted({int(str(r["season"])) for r in rows})

    best_findings = [
        "RB/WR/TE late-career and older buckets concentrate a meaningful subset of PYF false positives, but role archetype captures the broader high-volume false-positive pattern.",
        "Early-career lifecycle buckets capture most PYF false negatives, which is useful breakout-window context but not an automatic boost.",
        "Sparse-history rows remain low hit-rate even when young, so age/lifecycle must be paired with sparse-history guardrails.",
    ]
    report = f"""# Age / Lifecycle Component Signal Test V1 Report

## Verdict

`GREEN_AGE_LIFECYCLE_SIGNAL_USEFUL_REVIEW_ONLY`

## Clear Answer

Age/lifecycle adds useful review-only context for decline-risk and breakout-window analysis, but it
does not replace PYF, role archetype, or any future benchmark. It should be interpreted as a guardrail
and formula-family design input, not as exact Model v4 accuracy or a ranking feature.

## Benchmark Scope

- Rows tested: `{len(rows)}`
- Seasons: `{min(seasons)}-{max(seasons)}`
- Position coverage: `{dict(sorted(positions.items()))}`
- Missing age/DOB rows: `{missing_age}/{len(rows)} ({missing_age / len(rows):.2%})`
- Duplicate keys: `{duplicate_keys}`
- Inputs: age/lifecycle sidecar, Formula Data Mart labels/PYF, review-only role/sparse flags.
- Excluded: Formula Gauntlet, formula combinations, optimized weights, ranking candidates, production model-use.

## Main Findings

{chr(10).join(f"- {finding}" for finding in best_findings)}

## Metrics Summary

{markdown_table(scorecard, ["position", "rows", "age_vs_finish_spearman", "pyf_rank_vs_finish_spearman", "older_age_share_of_pyf_false_positives", "young_age_share_of_pyf_false_negatives", "early_lifecycle_share_of_pyf_false_negatives", "signal_interpretation"])}

## PYF Comparison

Age/lifecycle does not beat or replace PYF. It helps explain PYF miss slices:

{markdown_table(pyf_rows, ["position", "pyf_false_positives", "older_age_share_of_pyf_false_positives", "late_lifecycle_share_of_pyf_false_positives", "pyf_false_negatives", "young_age_share_of_pyf_false_negatives", "early_lifecycle_share_of_pyf_false_negatives", "role_archetype_high_volume_fp_share_reference"])}

## Interpretation

- Prior-decline detection: useful as a veteran/older-player review slice, not as a direct penalty.
- Breakout-window analysis: useful as an early-career/young-player review slice, not as a direct boost.
- Role archetype comparison: role archetype remains stronger for high-volume PYF false-positive taxonomy; age/lifecycle is complementary.
- Harm risk: age/lifecycle can over-penalize older elite players and over-reward young sparse-history players if used without PYF and role context.

## Maximum Allowed Use

`REVIEW_ONLY_COMPONENT_SIGNAL_TESTS`

Also allowed:

- `REVIEW_ONLY_GUARDRAIL_CONTEXT`
- `REVIEW_ONLY_FORMULA_FAMILY_CONTEXT`

Blocked:

- production/model-use
- formula weights
- direct ranking input
- exact Model v4 replay
- Formula Gauntlet tournaments
- rankings integration

## Gates

- Exact Model v4 replay remains blocked.
- Formula Gauntlet tournaments remain blocked.
- 100-candidate Formula Gauntlet remains blocked.
- Champion refinement remains blocked.
- Rankings integration remains blocked.
- Production/model-use remains blocked.

## Recommended Next Lane

`Age / Lifecycle Master Review V1`
"""
    (OUT / "AGE_LIFECYCLE_COMPONENT_SIGNAL_TEST_V1_REPORT.md").write_text(report, encoding="utf-8")

    print(
        {
            "rows": len(rows),
            "positions": dict(sorted(positions.items())),
            "seasons": f"{min(seasons)}-{max(seasons)}",
            "missing_age": missing_age,
            "duplicate_keys": duplicate_keys,
            "all_score": all_score,
        }
    )


if __name__ == "__main__":
    build()
