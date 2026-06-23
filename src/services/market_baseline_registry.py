from __future__ import annotations

from dataclasses import dataclass

DISPLAY_LABEL = "Market Baseline / Display-Only"
DEFAULT_STALE_BEHAVIOR = "show_stale_warning_no_rank_or_model_use"


@dataclass(frozen=True)
class MarketBaselinePageUsage:
    page: str
    enabled: bool
    fields_allowed: tuple[str, ...]
    display_label: str
    default_visible: bool
    stale_behavior: str
    sort_allowed: bool
    model_input_allowed: bool


PAGE_USAGE: dict[str, MarketBaselinePageUsage] = {
    "player_compare": MarketBaselinePageUsage(
        page="player_compare",
        enabled=True,
        fields_allowed=(
            "market_baseline_label",
            "dp_market_rank_1qb",
            "dp_value_1qb",
            "market_gap",
            "market_sanity_label",
            "join_confidence",
            "freshness_status",
            "market_baseline_stale_warning",
        ),
        display_label=DISPLAY_LABEL,
        default_visible=True,
        stale_behavior=DEFAULT_STALE_BEHAVIOR,
        sort_allowed=False,
        model_input_allowed=False,
    ),
    "trading_lab": MarketBaselinePageUsage(
        page="trading_lab",
        enabled=True,
        fields_allowed=(
            "market_baseline_label",
            "dp_value_1qb",
            "pick_label",
            "market_sanity_label",
            "freshness_status",
            "market_baseline_stale_warning",
        ),
        display_label=DISPLAY_LABEL,
        default_visible=True,
        stale_behavior=DEFAULT_STALE_BEHAVIOR,
        sort_allowed=False,
        model_input_allowed=False,
    ),
    "dynasty_rankings": MarketBaselinePageUsage(
        page="dynasty_rankings",
        enabled=True,
        fields_allowed=(
            "market_baseline_label",
            "market_sanity_label",
            "market_gap",
            "freshness_status",
        ),
        display_label=DISPLAY_LABEL,
        default_visible=False,
        stale_behavior=DEFAULT_STALE_BEHAVIOR,
        sort_allowed=False,
        model_input_allowed=False,
    ),
    "live_draft_room": MarketBaselinePageUsage(
        page="live_draft_room",
        enabled=True,
        fields_allowed=(
            "market_baseline_label",
            "market_sanity_label",
            "market_baseline_stale_warning",
        ),
        display_label=DISPLAY_LABEL,
        default_visible=False,
        stale_behavior="advanced_view_warning_only",
        sort_allowed=False,
        model_input_allowed=False,
    ),
    "post_draft_mode": MarketBaselinePageUsage(
        page="post_draft_mode",
        enabled=True,
        fields_allowed=(
            "market_baseline_label",
            "dp_value_1qb",
            "market_gap",
            "market_sanity_label",
            "freshness_status",
        ),
        display_label=DISPLAY_LABEL,
        default_visible=False,
        stale_behavior=DEFAULT_STALE_BEHAVIOR,
        sort_allowed=False,
        model_input_allowed=False,
    ),
    "settings_data_health": MarketBaselinePageUsage(
        page="settings_data_health",
        enabled=True,
        fields_allowed=(
            "freshness_status",
            "upstream_scrape_date",
            "upstream_latest_commit_sha",
            "upstream_latest_commit_timestamp",
            "local_cache_path",
            "market_baseline_stale_warning",
        ),
        display_label=DISPLAY_LABEL,
        default_visible=True,
        stale_behavior="show_health_status_and_manual_refresh_command",
        sort_allowed=False,
        model_input_allowed=False,
    ),
}


def get_market_baseline_page_usage(page: str) -> MarketBaselinePageUsage | None:
    return PAGE_USAGE.get(page)


def validate_market_baseline_registry() -> list[str]:
    issues: list[str] = []
    for page, usage in PAGE_USAGE.items():
        if usage.page != page:
            issues.append(f"{page}: registry key does not match page value")
        if usage.display_label != DISPLAY_LABEL:
            issues.append(f"{page}: display label must be {DISPLAY_LABEL!r}")
        if usage.model_input_allowed:
            issues.append(f"{page}: model_input_allowed must remain false")
        if usage.sort_allowed:
            issues.append(f"{page}: sort_allowed must remain false")
        if "rank" in " ".join(usage.fields_allowed).lower():
            allowed_rank_fields = {"dp_market_rank_1qb"}
            rank_fields = {
                field for field in usage.fields_allowed if "rank" in field.lower()
            }
            if not rank_fields.issubset(allowed_rank_fields):
                issues.append(f"{page}: rank-like field not allowed: {sorted(rank_fields)}")
    return issues
