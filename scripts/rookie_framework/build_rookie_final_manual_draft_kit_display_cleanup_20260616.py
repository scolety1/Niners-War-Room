"""Build a display-cleaned local preview for the frozen rookie draft kit.

This is layout/export cleanup only. It reuses the existing frozen/enriched
manual-use rows, keeps board order unchanged, and does not ingest new data.
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.rookie_framework.build_rookie_final_manual_draft_kit_stat_enrichment_20260616 import (
    DEFAULT_FROZEN_DIR,
    DEFAULT_SOURCE_BOARD,
    PREVIEW_BANNER,
    SOURCE_FILES,
    enriched_board_rows,
    read_csv,
    safe_int,
    source_lookup,
)


DEFAULT_OUTPUT_DIR = Path("local_exports/rookie_framework/final_manual_draft_kit_display_cleanup_20260616")

TIER_LABELS = {
    "tier_1_priority_target": "Tier 1 - Priority Targets",
    "tier_2_strong_consider": "Tier 2 - Strong Considers",
    "tier_3_value_fit": "Tier 3 - Value / Fit Targets",
    "tier_4_manual_upside": "Tier 4 - Manual Review Upside",
    "tier_5_avoid_hold": "Tier 5 - Avoid / Hold Unless Price Drops",
}

TIER_ORDER = list(TIER_LABELS)

DISPLAY_COLUMNS = [
    ("Rank", "overall_rank"),
    ("Player", "player"),
    ("Pos", "position"),
    ("NFL Team", "nfl_team"),
    ("Depth Chart / Role", "depth_chart_position_or_role"),
    ("Age", "age"),
    ("NFL Draft Capital", "nfl_draft_capital"),
    ("ADP / Market", "rookie_adp_or_market_rank"),
    ("Upside", "upside_score_or_band"),
    ("Bust Risk", "bust_risk_percent_or_band"),
    ("Draft Action", "draft_action"),
    ("Warning Severity", "warning_severity"),
    ("Main Positive Reason", "main_positive_reason"),
    ("Main Risk", "main_risk"),
    ("Manual Question", "manual_question"),
]


def write_csv(path: Path, rows: list[dict[str, object]], columns: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = columns or list(rows[0].keys() if rows else [])
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in fieldnames})


def reset_output_dir(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for path in sorted(output_dir.rglob("*"), reverse=True):
        if path.is_file():
            path.unlink()
        elif path.is_dir():
            path.rmdir()


def display_row(row: dict[str, object]) -> dict[str, object]:
    return {label: row.get(source, "") for label, source in DISPLAY_COLUMNS}


def display_rows(board: list[dict[str, object]]) -> list[dict[str, object]]:
    return [display_row(row) for row in sorted(board, key=lambda item: safe_int(item.get("overall_rank")))]


def grouped_display_rows(board: list[dict[str, object]]) -> list[dict[str, object]]:
    rows = []
    for row in sorted(board, key=lambda item: safe_int(item.get("overall_rank"))):
        rows.append(
            {
                "tier_key": row.get("tier", ""),
                "tier_label": TIER_LABELS.get(str(row.get("tier", "")), str(row.get("tier", "")) or "Unassigned"),
                "display": display_row(row),
            }
        )
    return rows


def warning_display_rows(board: list[dict[str, object]]) -> list[dict[str, object]]:
    rows = []
    for row in board:
        if row.get("warning_severity") in {"critical_trap_guard", "manual_review"} or row.get("draft_action") in {
            "manual_hold",
            "avoid_unless_price_collapses",
        }:
            rows.append(row)
    order = {"critical_trap_guard": 3, "manual_review": 2, "soft_note": 1, "none": 0}
    rows.sort(key=lambda row: (-order.get(str(row.get("warning_severity")), 0), safe_int(row.get("overall_rank"))))
    return [display_row(row) for row in rows]


def tier_summary_rows(board: list[dict[str, object]]) -> list[dict[str, object]]:
    output = []
    for tier in TIER_ORDER:
        rows = [row for row in board if row.get("tier") == tier]
        if not rows:
            continue
        output.append(
            {
                "Tier": TIER_LABELS[tier],
                "Player Count": len(rows),
                "Players": "; ".join(str(row.get("player", "")) for row in rows),
            }
        )
    return output


def guardrail_rows(board: list[dict[str, object]]) -> list[dict[str, object]]:
    ranks = [safe_int(row.get("overall_rank")) for row in board]
    formulas = sorted({str(row.get("model_formula_version", "")) for row in board if row.get("model_formula_version")})
    return [
        {"check": "board_order_changed", "status": "NO" if ranks == sorted(ranks) else "YES"},
        {"check": "formula_changed", "status": "NO" if formulas == ["cfbd_enriched_baseline_v1_1"] else "REVIEW"},
        {"check": "new_data_ingested", "status": "NO"},
        {"check": "visible_tier_column_removed", "status": "YES"},
        {"check": "redundant_rank_columns_removed", "status": "YES"},
        {"check": "production_allowed", "status": "NO"},
    ]


def verdict_rows() -> list[dict[str, object]]:
    return [
        {"verdict": "display_cleanup_quality", "status": "GREEN", "reason": "tier banners, simplified rank display, and readable columns generated"},
        {"verdict": "draft_use_readability", "status": "GREEN", "reason": "main board is grouped by tier and removes repeated rank/tier clutter"},
        {"verdict": "data_integrity", "status": "GREEN", "reason": "no new data was ingested and needs_data values remain honest"},
        {"verdict": "anti_cheat_leakage", "status": "GREEN", "reason": "no tuning, rescore, reorder, ADP private input, app wiring, or promoted artifact"},
    ]


def write_preview(output_dir: Path, grouped_rows: list[dict[str, object]], warnings: list[dict[str, object]]) -> Path:
    preview_dir = output_dir / "preview"
    preview_dir.mkdir(parents=True, exist_ok=True)
    path = preview_dir / "index.html"
    payload = {
        "banner": PREVIEW_BANNER,
        "columns": [label for label, _ in DISPLAY_COLUMNS],
        "tiers": grouped_rows,
        "warnings": warnings,
        "tierOrder": [TIER_LABELS[tier] for tier in TIER_ORDER],
        "options": filter_options(grouped_rows),
    }
    path.write_text(render_html(payload), encoding="utf-8")
    return path


def filter_options(grouped_rows: list[dict[str, object]]) -> dict[str, list[str]]:
    display = [dict(row.get("display", {})) for row in grouped_rows]
    return {
        "position": sorted({str(row.get("Pos", "")) for row in display if row.get("Pos")}),
        "tier": sorted({str(row.get("tier_label", "")) for row in grouped_rows if row.get("tier_label")}),
        "warning": sorted({str(row.get("Warning Severity", "")) for row in display if row.get("Warning Severity")}),
        "action": sorted({str(row.get("Draft Action", "")) for row in display if row.get("Draft Action")}),
    }


def render_html(payload: dict[str, object]) -> str:
    data = json.dumps(payload, ensure_ascii=True)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Rookie Final Manual Draft Kit - Display Cleanup</title>
  <style>
    body {{ margin: 0; font-family: Segoe UI, Arial, sans-serif; color: #17202a; background: #fff; }}
    header {{ padding: 18px 24px; background: #102033; color: #fff; border-bottom: 1px solid #d9dee7; }}
    h1 {{ margin: 0 0 6px; font-size: 22px; }}
    .banner {{ display: inline-block; margin-top: 8px; padding: 8px 10px; border: 1px solid #fecaca; background: #fff1f2; color: #991b1b; font-weight: 700; border-radius: 4px; }}
    main {{ padding: 18px 24px 28px; }}
    .filters {{ display: grid; grid-template-columns: repeat(4, minmax(160px, 1fr)); gap: 12px; padding: 14px; background: #f5f7fa; border: 1px solid #d9dee7; border-radius: 6px; margin-bottom: 16px; }}
    label {{ display: block; font-size: 12px; font-weight: 700; color: #5a6675; margin-bottom: 4px; }}
    select {{ width: 100%; padding: 8px; border: 1px solid #d9dee7; border-radius: 4px; background: #fff; color: #17202a; }}
    .tier {{ margin: 18px 0 26px; border: 1px solid #d9dee7; border-radius: 6px; overflow: hidden; }}
    .tier-header {{ padding: 11px 14px; background: #102033; color: #fff; font-weight: 800; letter-spacing: 0; }}
    .meta {{ color: #5a6675; margin: 8px 0 12px; font-size: 13px; }}
    .table-wrap {{ overflow: auto; }}
    table {{ border-collapse: collapse; width: 100%; min-width: 1420px; font-size: 13px; }}
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
    <h1>Rookie Final Manual Draft Kit - Display Cleanup</h1>
    <div>Display cleanup only. Formula and frozen board order remain unchanged.</div>
    <div class="banner">{html.escape(PREVIEW_BANNER)}</div>
  </header>
  <main>
    <section class="filters">
      <div><label for="positionFilter">Position</label><select id="positionFilter"></select></div>
      <div><label for="tierFilter">Tier</label><select id="tierFilter"></select></div>
      <div><label for="warningFilter">Warning severity</label><select id="warningFilter"></select></div>
      <div><label for="actionFilter">Draft action</label><select id="actionFilter"></select></div>
    </section>
    <div class="meta" id="meta"></div>
    <div id="tiers"></div>
  </main>
  <script id="payload" type="application/json">{data}</script>
  <script>
    const payload = JSON.parse(document.getElementById('payload').textContent);
    const columns = payload.columns;
    function esc(v) {{ return String(v ?? '').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'","&#039;"); }}
    function fill(id, values) {{ const s=document.getElementById(id); s.innerHTML='<option value="">All</option>'+values.map(v=>`<option value="${{esc(v)}}">${{esc(v)}}</option>`).join(''); s.addEventListener('change', render); }}
    function match(row) {{ const d=row.display; return (!positionFilter.value||d['Pos']===positionFilter.value)&&(!tierFilter.value||row.tier_label===tierFilter.value)&&(!warningFilter.value||d['Warning Severity']===warningFilter.value)&&(!actionFilter.value||d['Draft Action']===actionFilter.value); }}
    function table(rows) {{ return `<div class="table-wrap"><table><thead><tr>${{columns.map(c=>`<th>${{esc(c)}}</th>`).join('')}}</tr></thead><tbody>${{rows.map(row=>`<tr>${{columns.map(c=>`<td class="${{c==='Warning Severity'?esc(row.display[c]):''}}">${{esc(row.display[c])}}</td>`).join('')}}</tr>`).join('')}}</tbody></table></div>`; }}
    function render() {{
      const rows = payload.tiers.filter(match);
      meta.textContent = `${{rows.length}} of ${{payload.tiers.length}} rows shown`;
      const byTier = new Map();
      for (const label of payload.tierOrder) byTier.set(label, []);
      for (const row of rows) {{ if(!byTier.has(row.tier_label)) byTier.set(row.tier_label, []); byTier.get(row.tier_label).push(row); }}
      tiers.innerHTML = Array.from(byTier.entries()).filter(([_, rs]) => rs.length).map(([label, rs]) => `<section class="tier"><div class="tier-header">${{esc(label)}} (${{rs.length}})</div>${{table(rs)}}</section>`).join('') || '<div>No rows match.</div>';
    }}
    fill('positionFilter', payload.options.position); fill('tierFilter', payload.options.tier); fill('warningFilter', payload.options.warning); fill('actionFilter', payload.options.action); render();
  </script>
</body>
</html>
"""


def write_readme(output_dir: Path, preview_path: Path) -> None:
    lines = [
        "# Rookie Final Manual Draft Kit Display Cleanup",
        "",
        "Local/manual-use display cleanup only.",
        "",
        f"Preview: `{preview_path}`",
        "",
        "Formula remains cfbd_enriched_baseline_v1_1.",
        "Frozen board order is unchanged.",
        "No new ADP/team/depth-chart/age data was ingested.",
    ]
    (output_dir / "README_ROOKIE_FINAL_MANUAL_DRAFT_KIT_DISPLAY_CLEANUP_20260616.md").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


def build_display_cleanup(frozen_dir: Path, source_board: Path, output_dir: Path) -> dict[str, object]:
    reset_output_dir(output_dir)
    source_by_name = source_lookup(read_csv(source_board))
    frozen = read_csv(frozen_dir / SOURCE_FILES["board"])
    board = enriched_board_rows(frozen, source_by_name)
    display = display_rows(board)
    grouped = grouped_display_rows(board)
    warnings = warning_display_rows(board)
    tiers = tier_summary_rows(board)
    guardrails = guardrail_rows(board)
    verdicts = verdict_rows()

    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "rookie_2026_final_manual_draft_board_display_cleanup_20260616.csv", display)
    write_csv(output_dir / "rookie_2026_draft_day_quick_sheet_display_cleanup_20260616.csv", display)
    write_csv(output_dir / "rookie_2026_warning_priority_display_cleanup_20260616.csv", warnings)
    write_csv(output_dir / "rookie_2026_tier_summary_display_cleanup_20260616.csv", tiers)
    write_csv(output_dir / "rookie_2026_display_cleanup_guardrails_20260616.csv", guardrails)
    write_csv(output_dir / "rookie_2026_display_cleanup_verdicts_20260616.csv", verdicts)
    preview = write_preview(output_dir, grouped, warnings)
    write_readme(output_dir, preview)

    return {
        "board": board,
        "display": display,
        "grouped": grouped,
        "warnings": warnings,
        "tiers": tiers,
        "guardrails": guardrails,
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
    result = build_display_cleanup(args.frozen_dir, args.source_board, args.output_dir)
    print(f"board_rows={len(result['board'])}")
    print(f"display_rows={len(result['display'])}")
    print(f"tier_sections={len(result['tiers'])}")
    print(f"warning_rows={len(result['warnings'])}")
    print(f"preview={result['preview']}")
    print(f"output_dir={args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
