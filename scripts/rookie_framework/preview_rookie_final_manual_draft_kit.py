"""Build or run a local preview for the frozen rookie manual draft kit.

Streamlit is optional. When Streamlit is unavailable, this script builds a
static browser preview under local_exports. It does not touch production app
wiring or alter the frozen board order.
"""

from __future__ import annotations

import argparse
import csv
import html
import json
from pathlib import Path


DEFAULT_KIT_DIR = Path("local_exports/rookie_framework/final_manual_draft_kit_20260615")
DEFAULT_PREVIEW_DIR = DEFAULT_KIT_DIR / "preview"
BANNER = "Manual-use rookie draft kit only. Not production rankings."

FILES = {
    "Final board": "rookie_2026_final_manual_draft_board_frozen_20260615.csv",
    "Draft-day quick sheet": "rookie_2026_draft_day_quick_sheet_20260615.csv",
    "Tier cards": "rookie_2026_tier_cards_20260615.csv",
    "Manual decision checklist": "rookie_2026_manual_decisions_checklist_20260615.csv",
    "Warning-priority sheet": "rookie_2026_warning_priority_sheet_20260615.csv",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def load_tables(kit_dir: Path) -> dict[str, list[dict[str, str]]]:
    return {label: read_csv(kit_dir / filename) for label, filename in FILES.items()}


def sorted_unique(values: set[str]) -> list[str]:
    return sorted(value for value in values if value)


def filter_options(tables: dict[str, list[dict[str, str]]]) -> dict[str, list[str]]:
    rows = [row for table in tables.values() for row in table]
    return {
        "position": sorted_unique({row.get("position", "") for row in rows}),
        "tier": sorted_unique({row.get("tier", row.get("target_tier", "")) for row in rows}),
        "warning": sorted_unique({row.get("warning_severity", row.get("trap_guard_severity", "")) for row in rows}),
        "action": sorted_unique({row.get("draft_action", "") for row in rows}),
    }


def build_static_html(kit_dir: Path = DEFAULT_KIT_DIR, preview_dir: Path = DEFAULT_PREVIEW_DIR) -> Path:
    tables = load_tables(kit_dir)
    if not tables["Final board"]:
        raise FileNotFoundError(kit_dir / FILES["Final board"])
    preview_dir.mkdir(parents=True, exist_ok=True)
    html_path = preview_dir / "index.html"
    options = filter_options(tables)
    payload = {
        "tables": tables,
        "options": options,
        "banner": BANNER,
    }
    html_path.write_text(render_html(payload), encoding="utf-8")
    return html_path


def render_html(payload: dict[str, object]) -> str:
    data = json.dumps(payload, ensure_ascii=True)
    escaped_banner = html.escape(BANNER)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Rookie Final Manual Draft Kit Preview</title>
  <style>
    :root {{
      color-scheme: light;
      --ink: #17202a;
      --muted: #5a6675;
      --line: #d9dee7;
      --soft: #f5f7fa;
      --accent: #b42318;
      --good: #067647;
      --warn: #b54708;
    }}
    body {{
      margin: 0;
      font-family: Segoe UI, Arial, sans-serif;
      color: var(--ink);
      background: #ffffff;
    }}
    header {{
      padding: 18px 24px;
      border-bottom: 1px solid var(--line);
      background: #0f172a;
      color: #ffffff;
    }}
    header h1 {{
      margin: 0 0 6px;
      font-size: 22px;
      font-weight: 650;
    }}
    .banner {{
      display: inline-block;
      margin-top: 8px;
      padding: 8px 10px;
      border: 1px solid #fecaca;
      background: #fff1f2;
      color: #991b1b;
      font-weight: 700;
      border-radius: 4px;
    }}
    main {{
      padding: 18px 24px 28px;
    }}
    .filters {{
      display: grid;
      grid-template-columns: repeat(4, minmax(160px, 1fr));
      gap: 12px;
      padding: 14px;
      background: var(--soft);
      border: 1px solid var(--line);
      border-radius: 6px;
      margin-bottom: 16px;
    }}
    label {{
      display: block;
      font-size: 12px;
      font-weight: 700;
      color: var(--muted);
      margin-bottom: 4px;
    }}
    select {{
      width: 100%;
      padding: 8px;
      border: 1px solid var(--line);
      border-radius: 4px;
      background: #ffffff;
      color: var(--ink);
    }}
    .tabs {{
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      margin-bottom: 12px;
    }}
    .tabs button {{
      padding: 8px 10px;
      border: 1px solid var(--line);
      background: #ffffff;
      color: var(--ink);
      border-radius: 4px;
      cursor: pointer;
    }}
    .tabs button.active {{
      border-color: #0f172a;
      background: #0f172a;
      color: #ffffff;
    }}
    .table-wrap {{
      overflow: auto;
      border: 1px solid var(--line);
      border-radius: 6px;
    }}
    table {{
      border-collapse: collapse;
      width: 100%;
      min-width: 980px;
      font-size: 13px;
    }}
    th, td {{
      padding: 8px 9px;
      border-bottom: 1px solid var(--line);
      text-align: left;
      vertical-align: top;
    }}
    th {{
      position: sticky;
      top: 0;
      background: #eef2f7;
      z-index: 1;
    }}
    .severity-critical_trap_guard {{
      color: var(--accent);
      font-weight: 700;
    }}
    .severity-manual_review {{
      color: var(--warn);
      font-weight: 650;
    }}
    .severity-none {{
      color: var(--good);
    }}
    .meta {{
      color: var(--muted);
      margin: 8px 0 12px;
      font-size: 13px;
    }}
    @media (max-width: 820px) {{
      .filters {{ grid-template-columns: 1fr; }}
      main {{ padding: 14px; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>Rookie Final Manual Draft Kit Preview</h1>
    <div>Frozen local/manual-use board from cfbd_enriched_baseline_v1_1. Board order is unchanged.</div>
    <div class="banner">{escaped_banner}</div>
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
  <script id="draftKitData" type="application/json">{data}</script>
  <script>
    const payload = JSON.parse(document.getElementById('draftKitData').textContent);
    const tableNames = Object.keys(payload.tables);
    let activeTable = tableNames[0];

    function valueFor(row, keys) {{
      for (const key of keys) {{
        if (row[key]) return row[key];
      }}
      return "";
    }}

    function optionList(id, values) {{
      const select = document.getElementById(id);
      select.innerHTML = '<option value="">All</option>' + values.map(v => `<option value="${{escapeHtml(v)}}">${{escapeHtml(v)}}</option>`).join('');
      select.addEventListener('change', renderTable);
    }}

    function renderTabs() {{
      const tabs = document.getElementById('tabs');
      tabs.innerHTML = tableNames.map(name => `<button data-name="${{escapeHtml(name)}}" class="${{name === activeTable ? 'active' : ''}}">${{escapeHtml(name)}}</button>`).join('');
      tabs.querySelectorAll('button').forEach(button => {{
        button.addEventListener('click', () => {{
          activeTable = button.dataset.name;
          renderTabs();
          renderTable();
        }});
      }});
    }}

    function rowMatches(row) {{
      const position = document.getElementById('positionFilter').value;
      const tier = document.getElementById('tierFilter').value;
      const warning = document.getElementById('warningFilter').value;
      const action = document.getElementById('actionFilter').value;
      return (!position || valueFor(row, ['position']) === position)
        && (!tier || valueFor(row, ['tier', 'target_tier']) === tier)
        && (!warning || valueFor(row, ['warning_severity', 'trap_guard_severity']) === warning)
        && (!action || valueFor(row, ['draft_action']) === action);
    }}

    function renderTable() {{
      const allRows = payload.tables[activeTable] || [];
      const rows = allRows.filter(rowMatches);
      document.getElementById('meta').textContent = `${{activeTable}}: ${{rows.length}} of ${{allRows.length}} rows shown`;
      if (!rows.length) {{
        document.getElementById('table').innerHTML = '<div style="padding: 14px;">No rows match the selected filters.</div>';
        return;
      }}
      const columns = Object.keys(rows[0]);
      const thead = `<thead><tr>${{columns.map(c => `<th>${{escapeHtml(c)}}</th>`).join('')}}</tr></thead>`;
      const tbody = `<tbody>${{rows.map(row => `<tr>${{columns.map(c => cell(c, row[c] || '')).join('')}}</tr>`).join('')}}</tbody>`;
      document.getElementById('table').innerHTML = `<table>${{thead}}${{tbody}}</table>`;
    }}

    function cell(column, value) {{
      const className = column.includes('warning') ? ` class="severity-${{String(value).replaceAll('_', '-')}}"` : '';
      return `<td${{className}}>${{escapeHtml(String(value))}}</td>`;
    }}

    function escapeHtml(value) {{
      return String(value)
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&#039;');
    }}

    optionList('positionFilter', payload.options.position);
    optionList('tierFilter', payload.options.tier);
    optionList('warningFilter', payload.options.warning);
    optionList('actionFilter', payload.options.action);
    renderTabs();
    renderTable();
  </script>
</body>
</html>
"""


def run_streamlit(kit_dir: Path) -> None:
    import streamlit as st  # type: ignore

    tables = load_tables(kit_dir)
    options = filter_options(tables)
    st.set_page_config(page_title="Rookie Draft Kit Preview", layout="wide")
    st.title("Rookie Final Manual Draft Kit Preview")
    st.warning(BANNER)
    st.caption("Frozen local/manual-use board from cfbd_enriched_baseline_v1_1. Board order is unchanged.")
    col1, col2, col3, col4 = st.columns(4)
    position = col1.selectbox("Position", ["", *options["position"]])
    tier = col2.selectbox("Tier", ["", *options["tier"]])
    warning = col3.selectbox("Warning severity", ["", *options["warning"]])
    action = col4.selectbox("Draft action", ["", *options["action"]])
    tab_objects = st.tabs(list(tables.keys()))
    for tab, (name, rows) in zip(tab_objects, tables.items()):
        with tab:
            filtered = []
            for row in rows:
                if position and row.get("position", "") != position:
                    continue
                if tier and row.get("tier", row.get("target_tier", "")) != tier:
                    continue
                if warning and row.get("warning_severity", row.get("trap_guard_severity", "")) != warning:
                    continue
                if action and row.get("draft_action", "") != action:
                    continue
                filtered.append(row)
            st.write(f"{len(filtered)} of {len(rows)} rows shown")
            st.dataframe(filtered, use_container_width=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kit-dir", type=Path, default=DEFAULT_KIT_DIR)
    parser.add_argument("--preview-dir", type=Path, default=DEFAULT_PREVIEW_DIR)
    parser.add_argument("--build-html", action="store_true", help="Build static HTML preview and exit.")
    args = parser.parse_args(argv)
    if args.build_html:
        html_path = build_static_html(args.kit_dir, args.preview_dir)
        print(f"preview_html={html_path}")
        return 0
    try:
        run_streamlit(args.kit_dir)
    except ModuleNotFoundError:
        html_path = build_static_html(args.kit_dir, args.preview_dir)
        print("streamlit_unavailable=No module named streamlit")
        print(f"preview_html={html_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
