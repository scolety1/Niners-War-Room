from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

DEFAULT_OUTPUT_ROOT = Path("docs/model_v4")
DEFAULT_CSV_PATH = DEFAULT_OUTPUT_ROOT / "PHASE_10F_SOURCE_TRUST_CONTRACT.csv"
DEFAULT_DOC_PATH = DEFAULT_OUTPUT_ROOT / "PHASE_10F_SOURCE_TRUST_CONTRACT.md"

CLASSIFICATION_SCORING_EVIDENCE = "scoring_evidence"
CLASSIFICATION_DERIVED_EVIDENCE = "derived_evidence"
CLASSIFICATION_PROSPECT_PRIOR_EVIDENCE = "prospect_prior_evidence"
CLASSIFICATION_CONTEXT_ONLY = "context_only"
CLASSIFICATION_MARKET_CONTEXT_ONLY = "market_context_only"
CLASSIFICATION_SOURCE_LIMITED = "source_limited"
CLASSIFICATION_REJECTED = "rejected"

SOURCE_TRUST_CONTRACT_HEADER = (
    "source_family",
    "field_pattern",
    "classification",
    "source_status",
    "allowed_surfaces",
    "private_football_value_allowed",
    "market_liquidity_allowed",
    "confidence_effect",
    "receipt_requirement",
    "leakage_rule",
    "missing_data_rule",
    "notes",
    "direct_scoring_allowed",
    "talent_signal_allowed",
    "role_signal_allowed",
    "admitted_only_if_join_status_matched",
)

NO_ZERO_AVERAGE_MISSING_RULE = (
    "Missing data must remain missing/unavailable/review; it cannot become zero, "
    "average, or positive evidence."
)


@dataclass(frozen=True)
class SourceTrustRule:
    source_family: str
    field_pattern: str
    classification: str
    source_status: str
    allowed_surfaces: str
    private_football_value_allowed: bool
    market_liquidity_allowed: bool
    confidence_effect: str
    receipt_requirement: str
    leakage_rule: str
    missing_data_rule: str
    notes: str
    direct_scoring_allowed: bool = False
    talent_signal_allowed: bool = False
    role_signal_allowed: bool = False
    admitted_only_if_join_status_matched: bool = False

    def to_row(self) -> dict[str, object]:
        return {
            "source_family": self.source_family,
            "field_pattern": self.field_pattern,
            "classification": self.classification,
            "source_status": self.source_status,
            "allowed_surfaces": self.allowed_surfaces,
            "private_football_value_allowed": self.private_football_value_allowed,
            "market_liquidity_allowed": self.market_liquidity_allowed,
            "confidence_effect": self.confidence_effect,
            "receipt_requirement": self.receipt_requirement,
            "leakage_rule": self.leakage_rule,
            "missing_data_rule": self.missing_data_rule,
            "notes": self.notes,
            "direct_scoring_allowed": (
                self.direct_scoring_allowed
                or self.classification == CLASSIFICATION_SCORING_EVIDENCE
            ),
            "talent_signal_allowed": self.talent_signal_allowed,
            "role_signal_allowed": self.role_signal_allowed,
            "admitted_only_if_join_status_matched": (
                self.admitted_only_if_join_status_matched
            ),
        }


def build_source_trust_contract_rows() -> tuple[dict[str, object], ...]:
    return tuple(rule.to_row() for rule in SOURCE_TRUST_RULES)


def write_source_trust_contract_outputs(
    *,
    csv_path: str | Path = DEFAULT_CSV_PATH,
    doc_path: str | Path = DEFAULT_DOC_PATH,
) -> dict[str, Path]:
    rows = build_source_trust_contract_rows()
    csv_output = Path(csv_path)
    doc_output = Path(doc_path)
    csv_output.parent.mkdir(parents=True, exist_ok=True)
    _write_csv(csv_output, rows)
    _write_doc(doc_output, rows)
    return {"csv": csv_output, "doc": doc_output}


def no_leakage_violations(
    rows: tuple[dict[str, object], ...] | None = None,
) -> tuple[dict[str, object], ...]:
    contract_rows = rows or build_source_trust_contract_rows()
    violations: list[dict[str, object]] = []
    for row in contract_rows:
        source_family = str(row["source_family"]).lower()
        field_pattern = str(row["field_pattern"]).lower()
        classification = str(row["classification"])
        private_allowed = str(row["private_football_value_allowed"]) == "True"
        leakage_rule = str(row["leakage_rule"]).lower()
        if private_allowed and classification in PRIVATE_FORBIDDEN_CLASSIFICATIONS:
            violations.append({**row, "violation": "forbidden_classification_private_value"})
        if private_allowed and _is_market_or_ranking_context(source_family, field_pattern):
            violations.append({**row, "violation": "market_or_ranking_private_value"})
        if private_allowed and "projection" in source_family:
            violations.append({**row, "violation": "projection_private_value"})
        if private_allowed and "projection" in field_pattern:
            violations.append({**row, "violation": "projection_field_private_value"})
        if private_allowed and "league rank" in field_pattern:
            violations.append({**row, "violation": "league_rank_private_value"})
        if private_allowed and "cannot directly drive private football value" in leakage_rule:
            violations.append({**row, "violation": "leakage_rule_private_value_mismatch"})
    return tuple(violations)


def row_for_field(source_family: str, field_pattern: str) -> dict[str, object]:
    matches = [
        row
        for row in build_source_trust_contract_rows()
        if row["source_family"] == source_family and row["field_pattern"] == field_pattern
    ]
    if len(matches) != 1:
        raise KeyError(f"Expected one source trust row for {source_family}:{field_pattern}")
    return matches[0]


def _is_market_or_ranking_context(source_family: str, field_pattern: str) -> bool:
    if "market_share" in source_family or "market share" in field_pattern:
        return False
    if source_family == "recruiting_profiles":
        return False
    forbidden_markers = (
        "adp",
        "ranking",
        "rankings",
        "cheatsheet",
        "mock",
        "big_board",
        "market",
        "liquidity",
    )
    text = f"{source_family} {field_pattern}"
    return any(marker in text for marker in forbidden_markers)


PRIVATE_FORBIDDEN_CLASSIFICATIONS = {
    CLASSIFICATION_CONTEXT_ONLY,
    CLASSIFICATION_MARKET_CONTEXT_ONLY,
    CLASSIFICATION_SOURCE_LIMITED,
    CLASSIFICATION_REJECTED,
}

PRIVATE_VALUE_SURFACES = "Dynasty Asset Value; Roster Decision Value; Draft Value"
REVIEW_SURFACES = "Model Lab; Receipts; Audit Reports"
PROSPECT_SURFACES = "Draft Value; Rookie Analyzer; Young Bridge Review; Receipts"
CONTEXT_SURFACES = "Context Panels; Confidence Warnings; Receipts"
MARKET_SURFACES = "Trade Context; Market Comparison; Sanity Review"

SOURCE_TRUST_RULES: tuple[SourceTrustRule, ...] = (
    SourceTrustRule(
        "rotowire_nfl_passing",
        "COMP|ATT|YDS|TD|INT|SCK|FUM|QB rushing ATT/YDS/TD",
        CLASSIFICATION_SCORING_EVIDENCE,
        "imported_real_data",
        PRIVATE_VALUE_SURFACES,
        True,
        False,
        "Can raise confidence when identity, season, and stat type are validated.",
        "Show raw stat, season, source file/hash, normalized value, and contribution.",
        "Historical sourced stats may drive private football value.",
        NO_ZERO_AVERAGE_MISSING_RULE,
        "Passing evidence must be position-aware; raw QB points still pass through 1QB VORP.",
    ),
    SourceTrustRule(
        "rotowire_nfl_rushing",
        "ATT|YDS|TD|FUM|20+|40+|Lng",
        CLASSIFICATION_SCORING_EVIDENCE,
        "imported_real_data",
        PRIVATE_VALUE_SURFACES,
        True,
        False,
        "Can raise confidence when imported as real player rushing evidence.",
        "Show raw stat, season, source file/hash, normalized value, and contribution.",
        "Historical sourced rushing stats may drive private football value.",
        NO_ZERO_AVERAGE_MISSING_RULE,
        "Efficiency and explosive fields must be shrunk and cannot dominate volume.",
    ),
    SourceTrustRule(
        "rotowire_nfl_receiving",
        "REC|TAR|YDS|TD|FUM|20+|40+|Lng",
        CLASSIFICATION_SCORING_EVIDENCE,
        "imported_real_data",
        PRIVATE_VALUE_SURFACES,
        True,
        False,
        "Can raise confidence when imported as real receiving evidence.",
        "Show raw stat, season, source file/hash, normalized value, and contribution.",
        "Historical sourced receiving stats may drive private football value.",
        NO_ZERO_AVERAGE_MISSING_RULE,
        "Non-PPR model should favor yards, targets, and first downs over receptions.",
    ),
    SourceTrustRule(
        "rotowire_nfl_advanced_stats",
        "YAC|YACON|MTF|BTK|DROP|catchable|air-yard efficiency",
        CLASSIFICATION_DERIVED_EVIDENCE,
        "licensed_user_export",
        PRIVATE_VALUE_SURFACES,
        True,
        False,
        "Can support talent/efficiency with confidence penalty and sample-size warning.",
        "Show raw advanced field, source file/hash, sample, normalized value, warning.",
        "Advanced stats may support private value only as sourced evidence.",
        NO_ZERO_AVERAGE_MISSING_RULE,
        "Duplicate/context-sensitive fields must stay disambiguated before scoring.",
    ),
    SourceTrustRule(
        "fantasypros_historical_advanced",
        "historical advanced RB/WR/TE/QB stat fields",
        CLASSIFICATION_DERIVED_EVIDENCE,
        "source_limited_user_export",
        PRIVATE_VALUE_SURFACES,
        True,
        False,
        "Can support historical evidence after canonical file index and identity checks.",
        "Show canonical source file/hash, raw field, normalized value, and warning.",
        "Historical sourced exports may support private value after validation.",
        NO_ZERO_AVERAGE_MISSING_RULE,
        "FantasyPros advanced stats are historical evidence, not projections.",
    ),
    SourceTrustRule(
        "manual_first_down_exports",
        "Rush 1st|Rush 1st%|Receiving 1st|Receiving 1st%",
        CLASSIFICATION_SCORING_EVIDENCE,
        "imported_real_data_after_cleanup",
        PRIVATE_VALUE_SURFACES,
        True,
        False,
        "Can raise confidence after duplicate/header cleanup and identity match.",
        "Show raw first downs, cleanup warnings, source hash, scoring constant, contribution.",
        "Validated rushing/receiving first downs may drive private value.",
        NO_ZERO_AVERAGE_MISSING_RULE,
        "Only actual sourced first-down fields count as direct first-down evidence.",
        direct_scoring_allowed=True,
        talent_signal_allowed=True,
        role_signal_allowed=True,
        admitted_only_if_join_status_matched=True,
    ),
    SourceTrustRule(
        "manual_return_exports",
        "kick_return_yards|punt_return_yards|return_td",
        CLASSIFICATION_SCORING_EVIDENCE,
        "imported_real_data_after_cleanup",
        PRIVATE_VALUE_SURFACES,
        True,
        False,
        "Can support only small direct scoring evidence.",
        "Show return yards, return TDs, scoring constants, source hash, contribution.",
        "Return stats may score only through official return scoring constants.",
        NO_ZERO_AVERAGE_MISSING_RULE,
        "Return production is not a major talent signal.",
        direct_scoring_allowed=True,
        talent_signal_allowed=False,
        role_signal_allowed=False,
        admitted_only_if_join_status_matched=True,
    ),
    SourceTrustRule(
        "rotowire_snap_counts",
        "OFF|OFF%|games with offensive snaps",
        CLASSIFICATION_DERIVED_EVIDENCE,
        "licensed_user_export_proxy_only",
        PRIVATE_VALUE_SURFACES,
        True,
        False,
        "Can raise role confidence as snap evidence, with proxy warning.",
        "Show offensive snaps, snap share, games, source hash, and proxy warning.",
        "Snap share cannot be treated as route participation.",
        NO_ZERO_AVERAGE_MISSING_RULE,
        "QB snap count is generally context only because starters play full snaps.",
    ),
    SourceTrustRule(
        "rotowire_receiver_alignment",
        "Total|Out|Slot|Tight|Back|side alignment",
        CLASSIFICATION_DERIVED_EVIDENCE,
        "licensed_user_export",
        PRIVATE_VALUE_SURFACES,
        True,
        False,
        "Can support role shape and route/slot context with confidence penalty.",
        "Show raw alignment counts, source file/hash, and role warning.",
        "Alignment can inform role but cannot fabricate routes run or TPRR.",
        NO_ZERO_AVERAGE_MISSING_RULE,
        "Alignment is not a substitute for full route participation unless denominators exist.",
    ),
    SourceTrustRule(
        "rotowire_te_route_data",
        "routes|route%|TPRR|YPRR|target rate",
        CLASSIFICATION_DERIVED_EVIDENCE,
        "licensed_user_export",
        PRIVATE_VALUE_SURFACES,
        True,
        False,
        "Can raise TE role confidence when direct route fields are present.",
        "Show route field, denominator, source file/hash, sample, and contribution.",
        "Direct licensed route metrics may drive private value with route receipts.",
        NO_ZERO_AVERAGE_MISSING_RULE,
        "Do not generalize TE route fields to WR/RB route data unless sourced.",
    ),
    SourceTrustRule(
        "rotowire_target_leaders",
        "weekly targets|team target pct|yards per target",
        CLASSIFICATION_DERIVED_EVIDENCE,
        "licensed_user_export",
        PRIVATE_VALUE_SURFACES,
        True,
        False,
        "Can support usage and target-earning confidence.",
        "Show weekly target rows, team denominator if used, source hash, contribution.",
        "Targets may drive private value; yards per target must be shrunk.",
        NO_ZERO_AVERAGE_MISSING_RULE,
        "Weekly target exports are usage evidence, not projection evidence.",
    ),
    SourceTrustRule(
        "rotowire_depth_charts",
        "depth_rank|slot|status|raw_player_cell",
        CLASSIFICATION_CONTEXT_ONLY,
        "current_role_context",
        CONTEXT_SURFACES,
        False,
        False,
        "Can explain role risk and confidence but cannot directly add value.",
        "Show depth slot, status suffix, source file/hash, and date.",
        "Depth charts cannot directly drive private football value.",
        NO_ZERO_AVERAGE_MISSING_RULE,
        "Landing spot can be visible context until a formula lane explicitly accepts it.",
    ),
    SourceTrustRule(
        "rotowire_injuries",
        "status|estimated return|comment",
        CLASSIFICATION_CONTEXT_ONLY,
        "sourced_injury_context",
        CONTEXT_SURFACES,
        False,
        False,
        "Can lower confidence or add risk language; absence is not healthy evidence.",
        "Show injury status, return text, source file/hash, and timestamp.",
        "Injury context cannot directly boost private football value.",
        NO_ZERO_AVERAGE_MISSING_RULE,
        "Healthy-by-absence is rejected.",
    ),
    SourceTrustRule(
        "rotowire_team_context",
        "team stats|pace|PROE|offensive line ranking|schedule strength",
        CLASSIFICATION_CONTEXT_ONLY,
        "team_environment_context",
        CONTEXT_SURFACES,
        False,
        False,
        "Can explain environment and confidence, not direct player quality.",
        "Show team metric, season/date, source file/hash, and context label.",
        "Team context cannot directly drive private football value.",
        NO_ZERO_AVERAGE_MISSING_RULE,
        "Team context can be used for audit/sanity before explicit formula acceptance.",
    ),
    SourceTrustRule(
        "rotowire_raw_stat_projections",
        "projected passing/rushing/receiving raw stats",
        CLASSIFICATION_CONTEXT_ONLY,
        "projection_context_review_only",
        REVIEW_SURFACES,
        False,
        False,
        "Can be used only for comparison/review, not private value.",
        "Show source, date, raw projected fields, and review-only label.",
        "Projections cannot directly drive private football value.",
        NO_ZERO_AVERAGE_MISSING_RULE,
        "Local model-owned expected value should replace imported projections.",
    ),
    SourceTrustRule(
        "external_projection_points",
        "fantasy points|ranked projection total",
        CLASSIFICATION_REJECTED,
        "rejected_external_scoring_unknown",
        REVIEW_SURFACES,
        False,
        False,
        "No confidence benefit.",
        "Show rejected supplied-points warning if encountered.",
        "Projection totals cannot directly drive private football value.",
        NO_ZERO_AVERAGE_MISSING_RULE,
        "Reject supplied fantasy-point totals unless recomputed locally from raw stats.",
    ),
    SourceTrustRule(
        "rotowire_rankings_and_cheatsheets",
        "rank|pos_rank|dynasty rank|cheatsheet rank",
        CLASSIFICATION_MARKET_CONTEXT_ONLY,
        "market_or_sanity_context",
        MARKET_SURFACES,
        False,
        True,
        "Can support sanity review and market comparison only.",
        "Show ranking source/date and market-context-only label.",
        "ADP/rankings cannot directly drive private football value.",
        NO_ZERO_AVERAGE_MISSING_RULE,
        "Ranking sources may flag disagreements, not solve them.",
    ),
    SourceTrustRule(
        "fantasypros_adp",
        "ADP|rank|pos_rank|average_adp",
        CLASSIFICATION_MARKET_CONTEXT_ONLY,
        "market_context_only",
        MARKET_SURFACES,
        False,
        True,
        "Can support liquidity, sanity, and draft-market context.",
        "Show ADP source/date and market-context-only label.",
        "ADP/rankings cannot directly drive private football value.",
        NO_ZERO_AVERAGE_MISSING_RULE,
        "ADP is market context and never a private football value input.",
    ),
    SourceTrustRule(
        "rookie_adp_market",
        "rookie ADP|rookie rank|pos rank",
        CLASSIFICATION_MARKET_CONTEXT_ONLY,
        "market_context_only",
        MARKET_SURFACES,
        False,
        True,
        "Can support rookie draft liquidity and trade timing only.",
        "Show ADP window, source file/hash, and market-context-only label.",
        "ADP/rankings cannot directly drive private football value.",
        NO_ZERO_AVERAGE_MISSING_RULE,
        "Useful for pick value and market edge, not player quality.",
    ),
    SourceTrustRule(
        "kaggle_mock_drafts_big_boards",
        "mock pick|big board pick|team mock|consensus big board",
        CLASSIFICATION_MARKET_CONTEXT_ONLY,
        "public_mock_market_context",
        MARKET_SURFACES,
        False,
        True,
        "Can support public draft sentiment and uncertainty only.",
        "Show mock/big-board source, date, player URL, and market label.",
        "Mock drafts and big boards cannot directly drive private football value.",
        NO_ZERO_AVERAGE_MISSING_RULE,
        "Draft sentiment can guide audit questions, not formula value.",
    ),
    SourceTrustRule(
        "nfl_draft_results",
        "draft year|round|overall pick|NFL team",
        CLASSIFICATION_PROSPECT_PRIOR_EVIDENCE,
        "factual_draft_capital",
        PROSPECT_SURFACES,
        True,
        False,
        "Can support incoming rookie/young bridge prior with decay.",
        "Show round, pick, draft team, source file/hash, and prior weight.",
        "Factual draft capital may drive prospect prior, not market value.",
        NO_ZERO_AVERAGE_MISSING_RULE,
        "Draft capital must decay once NFL evidence exists.",
    ),
    SourceTrustRule(
        "cfbd_college_production",
        "passing|rushing|receiving college stats",
        CLASSIFICATION_PROSPECT_PRIOR_EVIDENCE,
        "redistribution_limited_but_formula_admitted_after_validation",
        PROSPECT_SURFACES,
        True,
        False,
        "Can support prospect prior when identity and season are matched.",
        "Show college stat, season, team, source file/hash, normalized value.",
        "College production can drive prospect prior only.",
        NO_ZERO_AVERAGE_MISSING_RULE,
        "Do not compare college raw totals without team/season context.",
    ),
    SourceTrustRule(
        "cfbd_market_share",
        "team yard share|TD share|attempt/share fields",
        CLASSIFICATION_PROSPECT_PRIOR_EVIDENCE,
        "redistribution_limited_but_formula_admitted_after_validation",
        PROSPECT_SURFACES,
        True,
        False,
        "Can support prospect prior with team denominator receipts.",
        "Show player numerator, team denominator, season/team, source file/hash.",
        "College market share can drive prospect prior only.",
        NO_ZERO_AVERAGE_MISSING_RULE,
        "Market share is prospect evidence, not NFL production evidence.",
    ),
    SourceTrustRule(
        "rotowire_cfb_stats_targets",
        "CFB stats|targets|team target pct|yards per target",
        CLASSIFICATION_PROSPECT_PRIOR_EVIDENCE,
        "licensed_user_export",
        PROSPECT_SURFACES,
        True,
        False,
        "Can support prospect prior after identity and season validation.",
        "Show raw stat, target fields, season, source file/hash, and contribution.",
        "College targets can drive prospect prior only.",
        NO_ZERO_AVERAGE_MISSING_RULE,
        "Yards per target remains noisy and must be shrunk.",
    ),
    SourceTrustRule(
        "rotowire_cfb_team_context",
        "plays per game|pass pct|run pct|team YPA|team YPG",
        CLASSIFICATION_CONTEXT_ONLY,
        "college_team_context",
        CONTEXT_SURFACES,
        False,
        False,
        "Can support context and normalization diagnostics.",
        "Show team, season, field, source file/hash, and context label.",
        "Team context cannot directly drive private football value.",
        NO_ZERO_AVERAGE_MISSING_RULE,
        "Use to explain environment and avoid false precision.",
    ),
    SourceTrustRule(
        "recruiting_profiles",
        "stars|rating|ranking|recruit type",
        CLASSIFICATION_PROSPECT_PRIOR_EVIDENCE,
        "structured_recruiting_context",
        PROSPECT_SURFACES,
        True,
        False,
        "Can support prospect prior with small/penalized weight.",
        "Show recruiting source, year, rating, stars, and prior contribution.",
        "Recruiting can drive prospect prior only.",
        NO_ZERO_AVERAGE_MISSING_RULE,
        "Recruiting must not override college production and draft capital.",
    ),
    SourceTrustRule(
        "rotowire_workout_combine",
        "height|weight|40|bench|vertical|broad|percentiles",
        CLASSIFICATION_PROSPECT_PRIOR_EVIDENCE,
        "licensed_user_export",
        PROSPECT_SURFACES,
        True,
        False,
        "Can support athletic profile prior with position-specific logic.",
        "Show measurement, event, source file/hash, and normalization.",
        "Workout metrics can drive prospect prior only.",
        NO_ZERO_AVERAGE_MISSING_RULE,
        "Missing workout data cannot become average athleticism.",
    ),
    SourceTrustRule(
        "third_party_combine_pro_day",
        "combine/pro-day measurements and IDs",
        CLASSIFICATION_SOURCE_LIMITED,
        "license_not_found_in_downloaded_repository_files",
        REVIEW_SURFACES,
        False,
        False,
        "Can be audited for coverage but not trusted for formula use yet.",
        "Show source repo, license status, measurement, and review-only label.",
        "Source-limited data cannot directly drive private football value.",
        NO_ZERO_AVERAGE_MISSING_RULE,
        "Requires license/provenance acceptance before formula use.",
    ),
    SourceTrustRule(
        "rotowire_rookie_rankings",
        "rookie rank|rookie projected stat fields|notes available",
        CLASSIFICATION_MARKET_CONTEXT_ONLY,
        "market_or_projection_context",
        MARKET_SURFACES,
        False,
        True,
        "Can support market review only.",
        "Show source/date, ranking/projection field, and context-only label.",
        "Rankings and projections cannot directly drive private football value.",
        NO_ZERO_AVERAGE_MISSING_RULE,
        "Rookie rankings are outside opinion context, not model evidence.",
    ),
    SourceTrustRule(
        "player_identity_crosswalk",
        "normalized name|aliases|IDs|player_url|team|college conflicts",
        CLASSIFICATION_DERIVED_EVIDENCE,
        "identity_gate",
        "All Joins; Receipts; Audit Reports",
        False,
        False,
        "Can block, warn, or review-label joined evidence.",
        "Show match names, IDs, source count, ambiguity flags, and join status.",
        "Identity crosswalk cannot directly increase private football value.",
        NO_ZERO_AVERAGE_MISSING_RULE,
        "Identity is a gate and receipt requirement, not a player-quality signal.",
    ),
    SourceTrustRule(
        "source_coverage_and_warnings",
        "missing evidence|unavailable sections|source warnings",
        CLASSIFICATION_CONTEXT_ONLY,
        "coverage_context",
        CONTEXT_SURFACES,
        False,
        False,
        "Can lower confidence and force review labels.",
        "Show source coverage, unavailable reason, and warning language.",
        "Coverage flags cannot directly increase private football value.",
        NO_ZERO_AVERAGE_MISSING_RULE,
        "Missing data reduces certainty; it is not proof of bad production.",
    ),
    SourceTrustRule(
        "league_rank_rule_context",
        "league rank|Roster's League-Rank Top Five",
        CLASSIFICATION_CONTEXT_ONLY,
        "rule_context_only",
        "Required Top-Five Release; Roster Rule Context",
        False,
        False,
        "Can drive rule mechanics only.",
        "Show league rank, top-five eligibility, and rule-context-only label.",
        "League rank cannot drive Dynasty Asset Value.",
        NO_ZERO_AVERAGE_MISSING_RULE,
        "League rank is not a player-quality input.",
    ),
    SourceTrustRule(
        "trade_market_liquidity",
        "market value|trade value|liquidity|market edge",
        CLASSIFICATION_MARKET_CONTEXT_ONLY,
        "trade_context_only",
        MARKET_SURFACES,
        False,
        True,
        "Can support trade opportunity and liquidity decisions.",
        "Show market source/date, no-private-value label, and missing-market warning.",
        "Market/liquidity cannot directly drive private football value.",
        NO_ZERO_AVERAGE_MISSING_RULE,
        "Market remains separate from private football value.",
    ),
    SourceTrustRule(
        "manual_unverified_or_malformed",
        "unvalidated manual stat tables|malformed rows|unproven scraped data",
        CLASSIFICATION_REJECTED,
        "rejected_until_structured_validation",
        REVIEW_SURFACES,
        False,
        False,
        "No confidence benefit.",
        "Show rejected source and reason.",
        "Rejected data cannot directly drive private football value.",
        NO_ZERO_AVERAGE_MISSING_RULE,
        "Manual data must pass a canonicalization phase before use.",
    ),
    SourceTrustRule(
        "unavailable_route_metrics",
        "missing route participation|missing routes run|missing TPRR|missing YPRR",
        CLASSIFICATION_SOURCE_LIMITED,
        "unavailable_or_not_imported",
        CONTEXT_SURFACES,
        False,
        False,
        "Can lower confidence and trigger route-gap labels.",
        "Show unavailable route metric and source gap reason.",
        "Unavailable route data cannot directly drive private football value.",
        NO_ZERO_AVERAGE_MISSING_RULE,
        "Snap share cannot fill this lane.",
    ),
    SourceTrustRule(
        "healthy_by_absence",
        "no injury row|blank injury status",
        CLASSIFICATION_REJECTED,
        "rejected_as_positive_evidence",
        REVIEW_SURFACES,
        False,
        False,
        "No confidence boost.",
        "Show absence as unknown, not healthy.",
        "Absence of injury data cannot directly drive private football value.",
        NO_ZERO_AVERAGE_MISSING_RULE,
        "Only sourced injury risk should affect confidence.",
    ),
)


def _write_csv(path: Path, rows: tuple[dict[str, object], ...]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=SOURCE_TRUST_CONTRACT_HEADER,
            extrasaction="ignore",
        )
        writer.writeheader()
        writer.writerows(rows)


def _write_doc(path: Path, rows: tuple[dict[str, object], ...]) -> None:
    counts: dict[str, int] = {}
    for row in rows:
        classification = str(row["classification"])
        counts[classification] = counts.get(classification, 0) + 1
    lines = [
        "# Phase 10F Source Trust And Leakage Contract",
        "",
        "## Purpose",
        "",
        "This contract assigns every new Model v4 data family to an explicit model lane "
        "before feature matrices or formula work use those fields. It is review-only "
        "governance and does not change scores, app rankings, or readiness gates.",
        "",
        "## Core Rules",
        "",
        "- ADP, rankings, cheat sheets, mock drafts, and big boards are market or "
        "sanity context only.",
        "- Imported projections and projected fantasy totals cannot directly drive "
        "private football value.",
        "- League rank cannot drive Dynasty Asset Value.",
        "- Market and liquidity remain separate from private football value.",
        "- Missing data remains missing/unavailable/review; it cannot become zero or "
        "average evidence.",
        "- `redistribution_limited_but_formula_admitted_after_validation` means local "
        "use is allowed after validation, while raw redistribution stays limited.",
        "- `source_limited` and `review_only_not_formula_admitted` data must stay "
        "review-only until provenance, licensing, and admission are accepted.",
        "",
        "## Classification Counts",
        "",
    ]
    lines.extend(f"- `{key}`: {counts[key]}" for key in sorted(counts))
    lines.extend(
        [
            "",
            "## Machine-Readable Contract",
            "",
            f"- CSV: `{DEFAULT_CSV_PATH}`",
            "",
            "## Formula Safety",
            "",
            "Rows with `private_football_value_allowed = False` may appear in UI, audit, "
            "confidence, or market surfaces only. They must not be included in Dynasty "
            "Asset Value feature matrices.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")
