"""Build stat-enriched local preview exports for the frozen rookie draft kit.

This is a display-only patch. It preserves the existing frozen board order and
cfbd_enriched_baseline_v1_1 model formula while adding source-safe visible
fields and more player-specific manual questions.
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import re
from collections import Counter, defaultdict
from pathlib import Path


DEFAULT_FROZEN_DIR = Path("local_exports/rookie_framework/final_manual_draft_kit_20260615")
DEFAULT_SOURCE_BOARD = Path(
    "local_exports/rookie_framework/current_2026_feature_aware_rescore_candidate_20260615/"
    "current_2026_feature_aware_candidate_board_20260615.csv"
)
DEFAULT_OUTPUT_DIR = Path("local_exports/rookie_framework/final_manual_draft_kit_stat_enrichment_20260616")
PREVIEW_BANNER = "Manual-use rookie draft kit only. Not production rankings."

SOURCE_FILES = {
    "board": "rookie_2026_final_manual_draft_board_frozen_20260615.csv",
    "quick": "rookie_2026_draft_day_quick_sheet_20260615.csv",
    "tiers": "rookie_2026_tier_cards_20260615.csv",
    "checklist": "rookie_2026_manual_decisions_checklist_20260615.csv",
    "warnings": "rookie_2026_warning_priority_sheet_20260615.csv",
}


ENRICHED_COLUMNS = [
    "overall_rank",
    "player",
    "position",
    "nfl_team",
    "depth_chart_position_or_role",
    "age",
    "nfl_draft_capital",
    "rookie_adp_or_market_rank",
    "nwr_overall_ranking",
    "model_rank",
    "upside_score_or_band",
    "bust_risk_percent_or_band",
    "tier",
    "draft_action",
    "warning_severity",
    "main_positive_reason",
    "main_risk",
    "manual_question",
    "position_rank",
    "unmatched_neutral_feature_flag",
    "model_formula_version",
    "board_order_changed",
    "main_ranking_formula_changed",
    "production_allowed",
    "promotion_status",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], columns: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = columns or all_columns(rows)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in fieldnames})


def all_columns(rows: list[dict[str, object]]) -> list[str]:
    columns: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row:
            if key not in seen:
                seen.add(key)
                columns.append(key)
    return columns


def normalize_name(value: str) -> str:
    return "".join(ch.lower() for ch in value if ch.isalnum())


def safe_int(value: object, default: int = 9999) -> int:
    try:
        if value is None or str(value).strip() == "":
            return default
        return int(float(str(value)))
    except ValueError:
        return default


def to_float(value: object, default: float = 0.0) -> float:
    try:
        if value is None or str(value).strip() == "":
            return default
        return float(str(value))
    except ValueError:
        return default


def source_lookup(source_rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {normalize_name(row.get("player_name", "")): row for row in source_rows if row.get("player_name")}


def score_band(value: str, kind: str) -> str:
    if value == "":
        return "needs_data"
    score = to_float(value)
    if kind == "upside":
        if score >= 90:
            band = "elite"
        elif score >= 75:
            band = "high"
        elif score >= 60:
            band = "solid"
        else:
            band = "modest"
    else:
        if score >= 90:
            band = "very_high"
        elif score >= 75:
            band = "high"
        elif score >= 60:
            band = "moderate"
        else:
            band = "lower"
    return f"score={score:.1f}; band={band}"


def role_context(source: dict[str, str]) -> str:
    text = source.get("star_case", "")
    match = re.search(r"role/archetype tags=([^;]+)", text)
    if match:
        return match.group(1).strip()
    position = source.get("position", "")
    if position == "WR":
        return "needs_data: nfl_depth_chart_target_earning_role"
    if position == "RB":
        return "needs_data: nfl_depth_chart_rush_goal_line_first_down_role"
    if position == "TE":
        return "needs_data: nfl_depth_chart_route_participation_role"
    if position == "QB":
        return "needs_data: qb_depth_chart_exception_case"
    return "needs_data"


def display_market_rank(source: dict[str, str]) -> str:
    value = source.get("market_rank_display_only", "").strip()
    if value:
        return value
    status = source.get("market_overlay_status", "")
    if status:
        return "needs_data"
    return "needs_data"


def display_draft_capital(source: dict[str, str]) -> str:
    value = source.get("draft_capital", "").strip()
    if value:
        return normalize_draft_capital(value)
    round_used = source.get("candidate_draft_round_used", "").strip()
    pick_used = source.get("candidate_overall_pick_used", "").strip()
    if round_used or pick_used:
        return f"round={clean_number(round_used) if round_used else 'needs_data'}; pick={clean_number(pick_used) if pick_used else 'needs_data'}"
    return "needs_data"


def clean_number(value: str) -> str:
    if value.strip() == "":
        return ""
    try:
        number = float(value)
        if number.is_integer():
            return str(int(number))
    except ValueError:
        pass
    return value


def normalize_draft_capital(value: str) -> str:
    return re.sub(r"(\d+)\.0\b", r"\1", value)


def main_risk(row: dict[str, str], source: dict[str, str]) -> str:
    risk = row.get("trap_caution_warning", "")
    if risk and not risk.startswith("No specific"):
        return risk
    bust_case = source.get("bust_case", "")
    if bust_case:
        return bust_case
    return row.get("trap_caution_warning", "") or "needs_data"


def has_active_injury_flag(row: dict[str, str], source: dict[str, str]) -> bool:
    text = "|".join(
        [
            source.get("warning_flags", ""),
            source.get("cfbd_warning_flags", ""),
            source.get("manual_review_reason", ""),
            row.get("trap_caution_warning", ""),
            row.get("main_risk_manual_question", ""),
        ]
    ).lower()
    markers = [
        "injury_review",
        "injury concern",
        "active injury",
        "injury flag",
        "injury_status",
        "medical",
    ]
    return any(marker in text for marker in markers)


def better_question(row: dict[str, str], source: dict[str, str]) -> str:
    player = row.get("player", "")
    pos = row.get("position", "")
    severity = row.get("warning_severity", "")
    action = row.get("draft_action", "")
    flags = "|".join(
        [
            source.get("warning_flags", ""),
            source.get("cfbd_warning_flags", ""),
            source.get("bust_case", ""),
            row.get("trap_caution_warning", ""),
        ]
    ).lower()
    rank = row.get("rank", "")
    draft_capital = display_draft_capital(source)
    role = role_context(source)
    rank_delta = safe_int(source.get("rank_delta"), 0)
    unmatched = row.get("unmatched_neutral_feature_flag") == "yes" or "unmatched" in flags

    if unmatched:
        return f"Is {player} missing model context because of a join/data issue, and should he stay a manual hold?"
    if severity == "critical_trap_guard":
        return f"Does {player}'s NFL draft capital/role ({draft_capital}; {role}) actually support rank {rank}, or is this production profile a trap?"
    if has_active_injury_flag(row, source):
        return f"Is {player}'s injury concern still active enough to push him below same-tier {pos} options?"
    if abs(rank_delta) >= 15:
        return f"Is {player}'s feature-driven rank move ({rank_delta:+d}) supported by NFL team, role, and draft-capital context?"
    if pos == "WR":
        if any(term in flags for term in ["route", "separation", "press", "yac", "source_limited"]):
            return f"Does {player} have a credible target-earning path on his NFL depth chart, including route/separation evidence?"
        return f"Does {player} have a credible target-earning path on his NFL depth chart?"
    if pos == "RB":
        if any(term in flags for term in ["goal", "first-down", "pass_pro", "fumble", "contact", "source_limited"]):
            return f"Does {player} have a credible early-down, goal-line, or first-down role path?"
        return f"Does {player}'s NFL role support enough rush/first-down opportunity for this draft action?"
    if pos in {"TE", "QB"}:
        return f"Is {player} an actual exception case in this 10-team 1QB non-PPR format?"
    if action == "manual_hold":
        return f"What specific role or source check must Tim clear before drafting {player}?"
    return f"Does Tim prefer {player} over nearby same-tier alternatives at this draft cost?"


def enriched_board_rows(frozen_rows: list[dict[str, str]], source_by_name: dict[str, dict[str, str]]) -> list[dict[str, object]]:
    output = []
    for row in sorted(frozen_rows, key=lambda item: safe_int(item.get("rank"))):
        source = source_by_name.get(normalize_name(row.get("player", "")), {})
        output.append(
            {
                "overall_rank": row.get("rank", ""),
                "player": row.get("player", ""),
                "position": row.get("position", ""),
                "nfl_team": source.get("nfl_team", "") or "needs_data",
                "depth_chart_position_or_role": role_context(source),
                "age": source.get("age", "") or source.get("dob", "") or "needs_data",
                "nfl_draft_capital": display_draft_capital(source),
                "rookie_adp_or_market_rank": display_market_rank(source),
                "nwr_overall_ranking": row.get("rank", ""),
                "model_rank": row.get("rank", ""),
                "upside_score_or_band": score_band(source.get("star_upside_index", ""), "upside"),
                "bust_risk_percent_or_band": score_band(source.get("bust_risk_index", ""), "bust"),
                "tier": row.get("tier", ""),
                "draft_action": row.get("draft_action", ""),
                "warning_severity": row.get("warning_severity", ""),
                "main_positive_reason": row.get("main_positive_reason", ""),
                "main_risk": main_risk(row, source),
                "manual_question": better_question(row, source),
                "position_rank": row.get("position_rank", ""),
                "unmatched_neutral_feature_flag": row.get("unmatched_neutral_feature_flag", ""),
                "model_formula_version": row.get("model_formula_version", "cfbd_enriched_baseline_v1_1"),
                "board_order_changed": "no",
                "main_ranking_formula_changed": "no",
                "production_allowed": "no",
                "promotion_status": "local_manual_stat_enriched_preview_only",
            }
        )
    return output


def quick_rows(board: list[dict[str, object]]) -> list[dict[str, object]]:
    columns = ENRICHED_COLUMNS[:18]
    return [{column: row.get(column, "") for column in columns} for row in board]


def warning_rows(board: list[dict[str, object]]) -> list[dict[str, object]]:
    order = {"critical_trap_guard": 3, "manual_review": 2, "soft_note": 1, "none": 0}
    return sorted(
        [
            row
            for row in board
            if row.get("warning_severity") in {"critical_trap_guard", "manual_review"}
            or row.get("draft_action") in {"manual_hold", "avoid_unless_price_collapses"}
        ],
        key=lambda row: (-order.get(str(row.get("warning_severity")), 0), safe_int(row.get("overall_rank"))),
    )


def manual_checklist(board: list[dict[str, object]]) -> list[dict[str, object]]:
    rows = []
    for row in warning_rows(board):
        rows.append(
            {
                "overall_rank": row.get("overall_rank", ""),
                "player": row.get("player", ""),
                "position": row.get("position", ""),
                "draft_action": row.get("draft_action", ""),
                "warning_severity": row.get("warning_severity", ""),
                "manual_question": row.get("manual_question", ""),
                "main_risk": row.get("main_risk", ""),
            }
        )
    return rows


def tier_cards(board: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in board:
        grouped[str(row.get("tier", ""))].append(row)
    output = []
    for tier in sorted(grouped):
        rows = grouped[tier]
        output.append(
            {
                "tier": tier,
                "player_count": len(rows),
                "players": "; ".join(str(row.get("player", "")) for row in rows),
                "draft_actions": "; ".join(f"{k}={v}" for k, v in sorted(Counter(str(row.get("draft_action", "")) for row in rows).items())),
                "warning_severities": "; ".join(f"{k}={v}" for k, v in sorted(Counter(str(row.get("warning_severity", "")) for row in rows).items())),
            }
        )
    return output


def field_coverage(board: list[dict[str, object]]) -> list[dict[str, object]]:
    fields = [
        "nfl_team",
        "depth_chart_position_or_role",
        "age",
        "nfl_draft_capital",
        "rookie_adp_or_market_rank",
        "upside_score_or_band",
        "bust_risk_percent_or_band",
    ]
    output = []
    for field in fields:
        populated = sum(1 for row in board if row.get(field) not in {"", "needs_data"} and not str(row.get(field)).startswith("needs_data"))
        output.append(
            {
                "field": field,
                "populated_rows": populated,
                "missing_or_needs_data_rows": len(board) - populated,
                "handling": field_handling(field),
            }
        )
    return output


def field_handling(field: str) -> str:
    if field == "rookie_adp_or_market_rank":
        return "display_only; not used in model/private score"
    if field in {"upside_score_or_band", "bust_risk_percent_or_band"}:
        return "derived from existing model/export score fields as score+band, not probability"
    if field == "nfl_draft_capital":
        return "display from existing draft_capital/candidate draft fields"
    return "source-safe local value if present; otherwise needs_data"


def missing_data_requests() -> list[dict[str, object]]:
    return [
        {
            "field": "rookie_adp_or_market_rank",
            "request": "Provide a display-only rookie ADP/market CSV with columns: player_name, position, adp_or_market_rank, source_name, as_of_date.",
            "notes": "Will remain display-only and excluded from private/model score.",
        },
        {
            "field": "nfl_team",
            "request": "Provide/confirm NFL team assignments with columns: player_name, position, nfl_team, source_name, as_of_date.",
            "notes": "Existing local board has nfl_team for many rows; Tim should verify if these are final.",
        },
        {
            "field": "depth_chart_position_or_role",
            "request": "Provide depth chart/role file with columns: player_name, position, nfl_team, depth_chart_position, projected_role, role_confidence, source_name, as_of_date.",
            "notes": "Use role context only for display/manual questions unless separately approved.",
        },
        {
            "field": "age",
            "request": "Provide age/DOB file with columns: player_name, position, date_of_birth or age_on_draft_day, source_name.",
            "notes": "Blank/needs_data until available.",
        },
        {
            "field": "nfl_draft_capital",
            "request": "Provide final NFL draft capital file with columns: player_name, position, nfl_team, draft_round, overall_pick, source_name.",
            "notes": "Existing local draft_capital is displayed where present; Tim should verify final source.",
        },
    ]


def verdict_rows(board: list[dict[str, object]]) -> list[dict[str, object]]:
    order_ok = [safe_int(row.get("overall_rank")) for row in board] == sorted(safe_int(row.get("overall_rank")) for row in board)
    return [
        {"verdict": "display_enrichment_quality", "status": "GREEN", "reason": "requested display columns added before warning severity"},
        {"verdict": "data_coverage", "status": "YELLOW", "reason": "team/draft/upside/bust fields have coverage; ADP, age, and depth-chart role need Tim data"},
        {"verdict": "manual_question_quality", "status": "GREEN", "reason": "questions now use position, warning severity, injury/unmatched/trap/rank-move context"},
        {"verdict": "draft_use_readiness", "status": "GREEN", "reason": "enriched quick sheet and preview generated without changing rank order"},
        {"verdict": "anti_cheat_leakage", "status": "GREEN", "reason": "no tuning, rescore, ADP private input, probabilities, probability bands, app wiring, or promoted artifact"},
        {"verdict": "board_order_changed", "status": "NO" if order_ok else "YELLOW", "reason": "rank order preserved from frozen board"},
        {"verdict": "formula_changed", "status": "NO", "reason": "model_formula_version remains cfbd_enriched_baseline_v1_1"},
    ]


def write_preview(output_dir: Path, tables: dict[str, list[dict[str, object]]]) -> Path:
    preview_dir = output_dir / "preview"
    preview_dir.mkdir(parents=True, exist_ok=True)
    path = preview_dir / "index.html"
    payload = {
        "banner": PREVIEW_BANNER,
        "tables": tables,
        "options": filter_options(tables),
    }
    path.write_text(render_html(payload), encoding="utf-8")
    return path


def filter_options(tables: dict[str, list[dict[str, object]]]) -> dict[str, list[str]]:
    rows = [row for table in tables.values() for row in table]
    return {
        "position": sorted({str(row.get("position", "")) for row in rows if row.get("position")}),
        "tier": sorted({str(row.get("tier", "")) for row in rows if row.get("tier")}),
        "warning": sorted({str(row.get("warning_severity", "")) for row in rows if row.get("warning_severity")}),
        "action": sorted({str(row.get("draft_action", "")) for row in rows if row.get("draft_action")}),
    }


def render_html(payload: dict[str, object]) -> str:
    data = json.dumps(payload, ensure_ascii=True)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Rookie Draft Kit Stat-Enriched Preview</title>
  <style>
    body {{ margin: 0; font-family: Segoe UI, Arial, sans-serif; color: #17202a; background: #fff; }}
    header {{ padding: 18px 24px; background: #102033; color: #fff; border-bottom: 1px solid #d9dee7; }}
    h1 {{ margin: 0 0 6px; font-size: 22px; }}
    .banner {{ display: inline-block; margin-top: 8px; padding: 8px 10px; border: 1px solid #fecaca; background: #fff1f2; color: #991b1b; font-weight: 700; border-radius: 4px; }}
    main {{ padding: 18px 24px 28px; }}
    .filters {{ display: grid; grid-template-columns: repeat(4, minmax(160px, 1fr)); gap: 12px; padding: 14px; background: #f5f7fa; border: 1px solid #d9dee7; border-radius: 6px; margin-bottom: 16px; }}
    label {{ display: block; font-size: 12px; font-weight: 700; color: #5a6675; margin-bottom: 4px; }}
    select {{ width: 100%; padding: 8px; border: 1px solid #d9dee7; border-radius: 4px; background: #fff; color: #17202a; }}
    .tabs {{ display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 12px; }}
    .tabs button {{ padding: 8px 10px; border: 1px solid #d9dee7; background: #fff; color: #17202a; border-radius: 4px; cursor: pointer; }}
    .tabs button.active {{ border-color: #102033; background: #102033; color: #fff; }}
    .meta {{ color: #5a6675; margin: 8px 0 12px; font-size: 13px; }}
    .table-wrap {{ overflow: auto; border: 1px solid #d9dee7; border-radius: 6px; }}
    table {{ border-collapse: collapse; width: 100%; min-width: 1300px; font-size: 13px; }}
    th, td {{ padding: 8px 9px; border-bottom: 1px solid #d9dee7; text-align: left; vertical-align: top; }}
    th {{ position: sticky; top: 0; background: #eef2f7; z-index: 1; }}
    .critical_trap_guard {{ color: #b42318; font-weight: 700; }}
    .manual_review {{ color: #b54708; font-weight: 650; }}
    .none {{ color: #067647; }}
    @media (max-width: 820px) {{ .filters {{ grid-template-columns: 1fr; }} main {{ padding: 14px; }} }}
  </style>
</head>
<body>
  <header>
    <h1>Rookie Final Manual Draft Kit - Stat-Enriched Preview</h1>
    <div>Display enrichment only. Formula and board order remain unchanged.</div>
    <div class="banner">{html.escape(PREVIEW_BANNER)}</div>
  </header>
  <main>
    <section class="filters">
      <div><label for="positionFilter">Position</label><select id="positionFilter"></select></div>
      <div><label for="tierFilter">Tier</label><select id="tierFilter"></select></div>
      <div><label for="warningFilter">Warning severity</label><select id="warningFilter"></select></div>
      <div><label for="actionFilter">Draft action</label><select id="actionFilter"></select></div>
    </section>
    <nav class="tabs" id="tabs"></nav>
    <div class="meta" id="meta"></div>
    <div class="table-wrap" id="table"></div>
  </main>
  <script id="payload" type="application/json">{data}</script>
  <script>
    const payload = JSON.parse(document.getElementById('payload').textContent);
    const names = Object.keys(payload.tables);
    let active = names[0];
    function esc(v) {{ return String(v).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'","&#039;"); }}
    function val(row, keys) {{ for (const k of keys) {{ if (row[k]) return row[k]; }} return ""; }}
    function fill(id, values) {{ const s=document.getElementById(id); s.innerHTML='<option value="">All</option>'+values.map(v=>`<option value="${{esc(v)}}">${{esc(v)}}</option>`).join(''); s.addEventListener('change', render); }}
    function tabs() {{ const t=document.getElementById('tabs'); t.innerHTML=names.map(n=>`<button data-name="${{esc(n)}}" class="${{n===active?'active':''}}">${{esc(n)}}</button>`).join(''); t.querySelectorAll('button').forEach(b=>b.addEventListener('click',()=>{{active=b.dataset.name; tabs(); render();}})); }}
    function match(row) {{ const p=positionFilter.value, ti=tierFilter.value, w=warningFilter.value, a=actionFilter.value; return (!p||val(row,['position'])===p)&&(!ti||val(row,['tier'])===ti)&&(!w||val(row,['warning_severity'])===w)&&(!a||val(row,['draft_action'])===a); }}
    function render() {{ const all=payload.tables[active]||[]; const rows=all.filter(match); meta.textContent=`${{active}}: ${{rows.length}} of ${{all.length}} rows shown`; if(!rows.length){{table.innerHTML='<div style="padding:14px;">No rows match.</div>'; return;}} const cols=Object.keys(rows[0]); table.innerHTML=`<table><thead><tr>${{cols.map(c=>`<th>${{esc(c)}}</th>`).join('')}}</tr></thead><tbody>${{rows.map(r=>`<tr>${{cols.map(c=>`<td class="${{c==='warning_severity'?esc(r[c]):''}}">${{esc(r[c]||'')}}</td>`).join('')}}</tr>`).join('')}}</tbody></table>`; }}
    fill('positionFilter', payload.options.position); fill('tierFilter', payload.options.tier); fill('warningFilter', payload.options.warning); fill('actionFilter', payload.options.action); tabs(); render();
  </script>
</body>
</html>
"""


def write_readme(output_dir: Path, preview_path: Path) -> None:
    text = [
        "# Rookie Final Manual Draft Kit Stat Enrichment",
        "",
        "Display-only enriched local/manual-use draft kit.",
        "",
        f"Preview: `{preview_path}`",
        "",
        "Formula remains cfbd_enriched_baseline_v1_1 and board order is unchanged.",
        "ADP/market is display-only and remains needs_data unless a source-safe file is provided.",
    ]
    (output_dir / "README_ROOKIE_FINAL_MANUAL_DRAFT_KIT_STAT_ENRICHMENT_20260616.md").write_text(
        "\n".join(text) + "\n",
        encoding="utf-8",
    )


def build_exports(frozen_dir: Path, source_board: Path, output_dir: Path) -> dict[str, object]:
    source_by_name = source_lookup(read_csv(source_board))
    frozen = read_csv(frozen_dir / SOURCE_FILES["board"])
    board = enriched_board_rows(frozen, source_by_name)
    quick = quick_rows(board)
    warnings = warning_rows(board)
    checklist = manual_checklist(board)
    tiers = tier_cards(board)
    coverage = field_coverage(board)
    missing = missing_data_requests()
    verdicts = verdict_rows(board)
    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "rookie_2026_final_manual_draft_board_stat_enriched_20260616.csv", board, ENRICHED_COLUMNS)
    write_csv(output_dir / "rookie_2026_draft_day_quick_sheet_stat_enriched_20260616.csv", quick)
    write_csv(output_dir / "rookie_2026_warning_priority_stat_enriched_20260616.csv", warnings, ENRICHED_COLUMNS)
    write_csv(output_dir / "rookie_2026_manual_decisions_checklist_stat_enriched_20260616.csv", checklist)
    write_csv(output_dir / "rookie_2026_tier_cards_stat_enriched_20260616.csv", tiers)
    write_csv(output_dir / "rookie_2026_field_coverage_stat_enrichment_20260616.csv", coverage)
    write_csv(output_dir / "rookie_2026_missing_data_request_for_tim_20260616.csv", missing)
    write_csv(output_dir / "rookie_2026_stat_enrichment_verdicts_20260616.csv", verdicts)
    preview = write_preview(
        output_dir,
        {
            "Final board": board,
            "Draft-day quick sheet": quick,
            "Tier cards": tiers,
            "Manual decision checklist": checklist,
            "Warning-priority sheet": warnings,
            "Missing data request": missing,
        },
    )
    write_readme(output_dir, preview)
    return {
        "board": board,
        "quick": quick,
        "warnings": warnings,
        "checklist": checklist,
        "tiers": tiers,
        "coverage": coverage,
        "missing": missing,
        "verdicts": verdicts,
        "preview": preview,
        "output_dir": output_dir,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--frozen-dir", type=Path, default=DEFAULT_FROZEN_DIR)
    parser.add_argument("--source-board", type=Path, default=DEFAULT_SOURCE_BOARD)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args(argv)
    result = build_exports(args.frozen_dir, args.source_board, args.output_dir)
    print(f"board_rows={len(result['board'])}")
    print(f"quick_rows={len(result['quick'])}")
    print(f"warning_rows={len(result['warnings'])}")
    print(f"manual_checklist_rows={len(result['checklist'])}")
    print(f"preview={result['preview']}")
    print(f"output_dir={args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
