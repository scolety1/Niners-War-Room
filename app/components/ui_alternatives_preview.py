from __future__ import annotations

from dataclasses import dataclass
from html import escape

import streamlit as st


@dataclass(frozen=True)
class PreviewAlternative:
    key: str
    title: str
    focus: str
    badges: tuple[tuple[str, str], ...]
    preview_points: tuple[str, ...]
    pros: tuple[str, ...]
    cons: tuple[str, ...]
    helps_pages: tuple[str, ...]


CURRENT_UI_REFERENCE_NOTES: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "What stays the same",
        (
            "Default rank logic, source truth, model behavior, runtime data sources, "
            "and page routes stay unchanged.",
            "The existing decision-first flow remains centered on Rankings, Player Compare, "
            "Trading Lab, Development Lab, Settings / Data Health, and Draft Room review sections.",
            "Existing dense tables remain available where they are useful for audit "
            "and inspection.",
        ),
    ),
    (
        "What users already like",
        (
            "Fast access to the main decision pages without a marketing-style landing screen.",
            "Clear review-only labels, gate language, and direct data-health context.",
            "Tables that expose source context, status, and receipts when Tim wants "
            "to inspect the underlying rows.",
        ),
    ),
    (
        "What should not be disrupted",
        (
            "No hidden sorting, no promoted candidate formulas, and no new recommendations.",
            "No production formula, model training, tuning, or source-truth changes.",
            "No default page behavior changes outside this isolated UI preview lane.",
        ),
    ),
)

PREVIEW_GUARDRAILS: tuple[str, ...] = (
    "Review-only UI preview. It does not feed default app pages.",
    "No production formula changes.",
    "No model training or tuning.",
    "No rankings logic changes and no hidden sort.",
    "No recommendations and no source-truth promotion.",
    "No runtime data source changes.",
    "No candidate formula output is wired into production pages.",
)

CANDIDATE_PAGES_FOR_FUTURE_IMPROVEMENT: tuple[str, ...] = (
    "Rankings",
    "Player Compare",
    "Trading Lab",
    "Development Lab",
    "Settings / Data Health",
    "Draft Room review sections",
)

ALTERNATIVES: tuple[PreviewAlternative, ...] = (
    PreviewAlternative(
        key="A",
        title="Compact Review Cards",
        focus=(
            "Turn the highest-friction review moments into clean summary cards with clear "
            "status badges and fewer first-view tables."
        ),
        badges=(
            ("Fewer dense tables", "review"),
            ("Mobile spacing", "safe"),
            ("Status badges", "safe"),
        ),
        preview_points=(
            "Use short cards for player, trade, and data-health review summaries.",
            "Keep tables available behind expanders or secondary sections.",
            "Put verdict/status language in badges before detailed row evidence.",
            "Use tighter responsive grids so mobile and desktop stay scannable.",
        ),
        pros=(
            "Best quick-read upgrade for Rankings and Draft Room review sections.",
            "Reduces first-view fatigue without hiding audit detail.",
            "Works well on mobile because each card has a stable shape.",
        ),
        cons=(
            "Can feel less precise if too many table rows move behind expanders.",
            "Needs careful copy so badges do not imply a final decision.",
        ),
        helps_pages=(
            "Rankings",
            "Player Compare",
            "Draft Room review sections",
            "Settings / Data Health",
        ),
    ),
    PreviewAlternative(
        key="B",
        title="Evidence-First Layout",
        focus=(
            "Keep the primary table central, then make evidence, source context, and warnings "
            "collapsible around it."
        ),
        badges=(
            ("Table central", "safe"),
            ("Evidence panels", "review"),
            ("Warnings tuned", "safe"),
        ),
        preview_points=(
            "Keep the table as the anchor for detailed comparison.",
            "Add collapsible evidence/context panels beside or below the table.",
            "Make warning banners explicit, narrow, and limited to true review blockers.",
            "Preserve row order exactly as the source page provides it.",
        ),
        pros=(
            "Least disruptive to the current UI.",
            "Strong fit for audit-heavy pages with source context.",
            "Keeps power-user table workflows intact.",
        ),
        cons=(
            "Still relies on dense tables for first comprehension.",
            "Collapsible panels need consistent defaults to avoid visual noise.",
        ),
        helps_pages=(
            "Rankings",
            "Trading Lab",
            "Development Lab",
            "Settings / Data Health",
        ),
    ),
    PreviewAlternative(
        key="C",
        title="Lab Console Layout",
        focus=(
            "Organize review artifacts and experiments into clear lanes for datasets, "
            "candidates, guardrails, and decisions."
        ),
        badges=(("Artifacts", "review"), ("Experiments", "blocked"), ("Decisions", "safe")),
        preview_points=(
            "Separate datasets, candidate artifacts, guardrails, and decisions into obvious zones.",
            "Show experiment status without promoting any candidate output.",
            "Use decision logs for human review state, not automated picks.",
            "Make blocked gates and source limitations visible before artifact detail.",
        ),
        pros=(
            "Best fit for Development Lab and review packets.",
            "Makes guardrails more visible for parallel lanes.",
            "Scales well for multiple artifacts without changing production behavior.",
        ),
        cons=(
            "Too heavy for the everyday Rankings first view.",
            "Needs restraint so it does not feel like a separate product.",
        ),
        helps_pages=(
            "Development Lab",
            "Settings / Data Health",
            "Draft Room review sections",
        ),
    ),
)

SIDE_BY_SIDE_ROWS: tuple[dict[str, str], ...] = (
    {
        "Alternative": "A: Compact Review Cards",
        "Best fit": "Fast review passes and mobile scanning",
        "Pros": "Lower first-view density; clear statuses",
        "Cons": "May hide detail too quickly",
        "Pages helped": "Rankings, Player Compare, Draft Room",
    },
    {
        "Alternative": "B: Evidence-First Layout",
        "Best fit": "Keeping current table workflows intact",
        "Pros": "Least disruptive; audit-friendly",
        "Cons": "Still table-heavy",
        "Pages helped": "Rankings, Trading Lab, Data Health",
    },
    {
        "Alternative": "C: Lab Console Layout",
        "Best fit": "Review artifacts and parallel lane gates",
        "Pros": "Strong guardrail visibility",
        "Cons": "Too heavy for everyday pages",
        "Pages helped": "Development Lab, Data Health, Draft Room",
    },
)


def render_preview_styles() -> None:
    st.markdown(
        """
        <style>
        .nwr-preview-banner {
            border: 1px solid #e3c875;
            border-left: 5px solid #b3995d;
            border-radius: 8px;
            background: #fffaf0;
            padding: 0.85rem 0.95rem;
            margin: 0 0 1rem 0;
        }
        .nwr-preview-banner strong {
            color: #17202a;
        }
        .nwr-preview-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.75rem;
            margin: 0.35rem 0 1rem 0;
        }
        .nwr-preview-card {
            border: 1px solid #d9dee7;
            border-radius: 8px;
            background: #ffffff;
            padding: 0.85rem 0.9rem;
            min-height: 12rem;
            overflow-wrap: anywhere;
        }
        .nwr-preview-card h3 {
            font-size: 1rem;
            margin: 0 0 0.35rem 0;
        }
        .nwr-preview-card p,
        .nwr-preview-card li {
            color: #5f6b7a;
            font-size: 0.88rem;
            line-height: 1.45;
        }
        .nwr-preview-card ul {
            padding-left: 1rem;
            margin: 0.5rem 0 0 0;
        }
        .nwr-preview-badges {
            display: flex;
            flex-wrap: wrap;
            gap: 0.35rem;
            margin: 0.5rem 0;
        }
        .nwr-preview-badge {
            border: 1px solid #d9dee7;
            border-radius: 6px;
            background: #f7f8fa;
            color: #5f6b7a;
            font-size: 0.75rem;
            font-weight: 700;
            padding: 0.22rem 0.4rem;
        }
        .nwr-preview-badge.safe {
            color: #1f7a4d;
            border-color: #bdd9ca;
            background: #f3fbf7;
        }
        .nwr-preview-badge.review {
            color: #9a6a00;
            border-color: #e5cf94;
            background: #fffaf0;
        }
        .nwr-preview-badge.blocked {
            color: #b3261e;
            border-color: #e7b8b3;
            background: #fff5f4;
        }
        .nwr-preview-snapshot {
            border: 1px solid #d9dee7;
            border-radius: 8px;
            background: #ffffff;
            padding: 0.75rem;
            min-height: 16rem;
        }
        .nwr-preview-snapshot-title {
            color: #17202a;
            font-weight: 780;
            margin-bottom: 0.35rem;
        }
        .nwr-preview-row {
            border: 1px solid #d9dee7;
            border-radius: 6px;
            padding: 0.55rem;
            margin-top: 0.45rem;
            background: #fbfcfe;
        }
        .nwr-preview-row strong {
            color: #17202a;
        }
        .nwr-preview-muted {
            color: #5f6b7a;
            font-size: 0.86rem;
        }
        @media (max-width: 1100px) {
            .nwr-preview-grid {
                grid-template-columns: 1fr;
            }
            .nwr-preview-card,
            .nwr-preview-snapshot {
                min-height: auto;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_preview_banner() -> None:
    guardrails = "".join(f"<li>{escape(item)}</li>" for item in PREVIEW_GUARDRAILS)
    st.markdown(
        f"""
        <div class="nwr-preview-banner">
          <strong>Review-only preview lane.</strong>
          <span class="nwr-preview-muted">
            These layouts are static UI alternatives for inspection. They do not change
            production rankings, models, source truth, runtime data, or default page behavior.
          </span>
          <ul>{guardrails}</ul>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_current_ui_reference_notes() -> None:
    st.markdown("## Current UI reference notes")
    cards = []
    for title, bullets in CURRENT_UI_REFERENCE_NOTES:
        bullet_html = "".join(f"<li>{escape(item)}</li>" for item in bullets)
        cards.append(
            f"""
            <div class="nwr-preview-card">
              <h3>{escape(title)}</h3>
              <ul>{bullet_html}</ul>
            </div>
            """
        )
    st.markdown(
        f'<div class="nwr-preview-grid">{"".join(cards)}</div>',
        unsafe_allow_html=True,
    )


def render_alternative_a() -> None:
    alternative = ALTERNATIVES[0]
    st.markdown("## Alternative A: Compact Review Cards")
    _render_alternative_intro(alternative)

    show_density_notes = st.checkbox(
        "Show compact-card density notes",
        value=True,
        help="Preview-only toggle. It does not persist or feed any production page.",
    )

    card_specs = (
        (
            "Rankings Review Card",
            (("Review-only", "review"), ("Rank unchanged", "safe")),
            "Condenses player status, evidence health, and context flags before the full table.",
            (
                "Keeps current rank visible",
                "Adds clear source/context status",
                "Opens table detail only when needed",
            ),
        ),
        (
            "Player Compare Card",
            (("Human review", "review"), ("No verdict", "blocked")),
            "Highlights comparison context without producing a pick, trade, or roster decision.",
            (
                "Shows same-page comparison anchors",
                "Separates warning copy from detail",
                "Avoids final-choice language",
            ),
        ),
        (
            "Data Health Card",
            (("Gate status", "safe"), ("No source truth", "safe")),
            "Turns broad data-health checks into short cards with linkable detail rows.",
            (
                "Makes blockers easier to scan",
                "Keeps table audit available",
                "Fits mobile screens cleanly",
            ),
        ),
    )
    cards_html = "".join(
        _static_card_html(title, badges, body, bullets if show_density_notes else ())
        for title, badges, body, bullets in card_specs
    )
    st.markdown(
        f'<div class="nwr-preview-grid">{cards_html}</div>',
        unsafe_allow_html=True,
    )


def render_alternative_b() -> None:
    alternative = ALTERNATIVES[1]
    st.markdown("## Alternative B: Evidence-First Layout")
    _render_alternative_intro(alternative)
    st.info(
        "Preview warning treatment: banners stay direct and narrow. They should identify a true "
        "review blocker without creating noise or implying a model action."
    )

    st.markdown("### Primary table remains central")
    st.table(
        [
            {
                "Surface": "Rankings",
                "Current anchor": "Main board table",
                "Preview addition": "Collapsible context panels",
                "Order policy": "Preserve current order",
            },
            {
                "Surface": "Trading Lab",
                "Current anchor": "External asset context table",
                "Preview addition": "Source and caveat panels",
                "Order policy": "No hidden sort",
            },
            {
                "Surface": "Settings / Data Health",
                "Current anchor": "Data-health status rows",
                "Preview addition": "Quiet blocker banner plus source detail",
                "Order policy": "Source-provided order",
            },
        ]
    )

    left, right = st.columns(2)
    with left:
        with st.expander("Evidence/context panel example", expanded=True):
            st.markdown(
                "- Shows row receipts, source status, and admitted context.\n"
                "- Keeps factual evidence separate from any human decision.\n"
                "- Leaves production tables and current rank logic untouched."
            )
    with right:
        with st.expander("Warning banner rules", expanded=False):
            st.markdown(
                "- Use warning copy only for real review blockers.\n"
                "- Avoid repeating the same warning above every table.\n"
                "- Include the guardrail that no model/rank/source-truth behavior changed."
            )


def render_alternative_c() -> None:
    alternative = ALTERNATIVES[2]
    st.markdown("## Alternative C: Lab Console Layout")
    _render_alternative_intro(alternative)

    show_decision_log = st.checkbox(
        "Show preview decision-log lane",
        value=True,
        help="Preview-only toggle. It only changes this static layout example.",
    )
    tabs = st.tabs(("Datasets", "Candidates", "Guardrails", "Decisions"))
    with tabs[0]:
        _render_console_lane(
            "Dataset lane",
            (
                "Committed artifact summaries only.",
                "No raw/shared/cache/local export files loaded.",
                "No runtime data source changes.",
            ),
        )
    with tabs[1]:
        _render_console_lane(
            "Candidate artifact lane",
            (
                "Review artifacts can be listed without promotion.",
                "Candidate formula output is not wired into default app pages.",
                "Status language stays blocked/review-only until an explicit future gate.",
            ),
        )
    with tabs[2]:
        _render_console_lane("Guardrail lane", PREVIEW_GUARDRAILS)
    with tabs[3]:
        decision_items = (
            "Human decision notes only.",
            "No automated pick, trade, rank, or roster action.",
            "No final recommendation generated by the page.",
        )
        if show_decision_log:
            _render_console_lane("Decision lane", decision_items)
        else:
            st.caption("Decision-log lane hidden by preview-only toggle.")


def render_side_by_side_comparison() -> None:
    st.markdown("## Side-by-side comparison")
    st.caption(
        "Rendered sections stand in for screenshots inside the route. The artifact packet records "
        "route-smoke status separately."
    )

    columns = st.columns(3)
    for column, alternative in zip(columns, ALTERNATIVES, strict=True):
        with column:
            _render_snapshot(alternative)

    st.markdown("### Pros, cons, and affected pages")
    st.table(SIDE_BY_SIDE_ROWS)


def render_future_page_scope() -> None:
    st.markdown("### Candidate pages to consider later")
    st.caption(
        "These are future visual-improvement candidates only. Their default behavior "
        "is not changed by this preview branch."
    )
    st.markdown(
        " ".join(
            f'<span class="nwr-preview-badge safe">{escape(page)}</span>'
            for page in CANDIDATE_PAGES_FOR_FUTURE_IMPROVEMENT
        ),
        unsafe_allow_html=True,
    )


def _render_alternative_intro(alternative: PreviewAlternative) -> None:
    badge_html = " ".join(
        f'<span class="nwr-preview-badge {escape(kind)}">{escape(label)}</span>'
        for label, kind in alternative.badges
    )
    points = "".join(f"<li>{escape(point)}</li>" for point in alternative.preview_points)
    helps = ", ".join(alternative.helps_pages)
    st.markdown(
        f"""
        <div class="nwr-preview-card">
          <h3>{escape(alternative.title)}</h3>
          <p>{escape(alternative.focus)}</p>
          <div class="nwr-preview-badges">{badge_html}</div>
          <ul>{points}</ul>
          <p><strong>Existing pages helped:</strong> {escape(helps)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _static_card_html(
    title: str,
    badges: tuple[tuple[str, str], ...],
    body: str,
    bullets: tuple[str, ...],
) -> str:
    badge_html = " ".join(
        f'<span class="nwr-preview-badge {escape(kind)}">{escape(label)}</span>'
        for label, kind in badges
    )
    bullet_html = "".join(f"<li>{escape(item)}</li>" for item in bullets)
    list_html = f"<ul>{bullet_html}</ul>" if bullet_html else ""
    return f"""
        <div class="nwr-preview-card">
          <h3>{escape(title)}</h3>
          <div class="nwr-preview-badges">{badge_html}</div>
          <p>{escape(body)}</p>
          {list_html}
        </div>
        """


def _render_console_lane(title: str, items: tuple[str, ...]) -> None:
    rows = "".join(
        f"""
        <div class="nwr-preview-row">
          <strong>{escape(item.split('.')[0])}</strong>
          <div class="nwr-preview-muted">{escape(item)}</div>
        </div>
        """
        for item in items
    )
    st.markdown(
        f"""
        <div class="nwr-preview-snapshot">
          <div class="nwr-preview-snapshot-title">{escape(title)}</div>
          {rows}
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_snapshot(alternative: PreviewAlternative) -> None:
    rows = "".join(
        f"""
        <div class="nwr-preview-row">
          <strong>{escape(point)}</strong>
        </div>
        """
        for point in alternative.preview_points[:3]
    )
    st.markdown(
        f"""
        <div class="nwr-preview-snapshot">
          <div class="nwr-preview-snapshot-title">Alternative {escape(alternative.key)}</div>
          <div class="nwr-preview-muted">{escape(alternative.title)}</div>
          {rows}
        </div>
        """,
        unsafe_allow_html=True,
    )
