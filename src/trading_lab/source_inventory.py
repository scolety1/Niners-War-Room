from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

FANTASY_SOURCE_CATEGORIES = frozenset(
    {
        "nwr_private_value_outputs",
        "outcome_v1_display_values",
        "rookie_board_values",
        "drop_decision_roster_pressure",
        "mock_draft_pick_player_context",
        "public_fantasy_rankings",
        "public_dynasty_trade_calculators",
        "public_adp",
        "public_dynasty_market_value",
        "manual_opponent_roster_context",
    }
)

PROHIBITED_SOURCE_CATEGORIES = frozenset(
    {
        "stock_market_api",
        "broker_api",
        "real_money_account_data",
        "credentials_or_secrets",
        "paid_private_data_unapproved",
        "unapproved_scraping",
        "fantasy_source_as_nwr_private_score",
    }
)

TRADE_PACKAGE_REQUIRED_FIELDS = (
    "trade_mode",
    "target_player",
    "outgoing_player",
    "give_assets",
    "get_assets",
    "picks_included",
    "nwr_value_delta",
    "public_market_fairness",
    "opponent_fit_score",
    "roster_impact_score",
    "keeper_impact",
    "drop_pressure_impact",
    "rookie_pick_context",
    "negotiation_ladder",
    "risk_flags",
    "verdict",
    "review_status",
)

VALID_TRADE_MODES = frozenset({"trade_for", "trade_away", "package_builder"})
VALID_REVIEW_STATUSES = frozenset({"draft", "needs_review", "ready_for_manual_review", "rejected"})

WALL_STREET_PATTERNS = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"\bstocks?\b",
        r"\bequit(?:y|ies)\b",
        r"\bcrypto\b",
        r"\bforex\b",
        r"\boptions?\b",
        r"\bmarket[-\s]?data\s+api\b",
        r"\bbroker\s+api\b",
        r"\bbrokerage\b",
        r"\bsec\s+edgar\b",
        r"\bfred\b",
        r"\bnasdaq\b",
        r"\balpaca\b",
        r"\bpolygon\b",
        r"\bmassive\b",
        r"\bdatabento\b",
        r"\btiingo\b",
        r"\btwelve\s+data\b",
        r"\border\s+execution\b",
        r"\breal[-\s]?money\s+trading\b",
        r"\binvestment\s+advice\b",
    )
)

SECRET_PATTERNS = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"\bapi[\s_-]+key\b",
        r"\bsecret\b",
        r"\btoken\b",
        r"\bcredential\b",
        r"\bpassword\b",
        r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
        r"\bBearer\s+[A-Za-z0-9._~+/=-]{16,}\b",
    )
)

AUTOMATED_DECISION_PATTERNS = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"\bauto[-\s]?accept\b",
        r"\bauto[-\s]?send\b",
        r"\bauto[-\s]?execute\b",
        r"\bautomated\s+trade\s+execution\b",
        r"\bsubmit\s+trade\b",
    )
)


@dataclass(frozen=True)
class ValidationIssue:
    field: str
    code: str
    message: str


@dataclass(frozen=True)
class FantasySourceMetadata:
    source_id: str
    source_name: str
    source_category: str
    allowed_use: str
    prohibited_use: str
    attribution: str
    notes: str = ""
    config: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class FantasyTradePackage:
    trade_mode: str
    target_player: str
    outgoing_player: str
    give_assets: Sequence[str]
    get_assets: Sequence[str]
    picks_included: Sequence[str]
    nwr_value_delta: float
    public_market_fairness: str
    opponent_fit_score: float
    roster_impact_score: float
    keeper_impact: str
    drop_pressure_impact: str
    rookie_pick_context: str
    negotiation_ladder: Mapping[str, str]
    risk_flags: Sequence[str]
    verdict: str
    review_status: str


def validate_fantasy_source_metadata(
    source: FantasySourceMetadata,
) -> tuple[ValidationIssue, ...]:
    issues: list[ValidationIssue] = []
    required = {
        "source_id": source.source_id,
        "source_name": source.source_name,
        "source_category": source.source_category,
        "allowed_use": source.allowed_use,
        "prohibited_use": source.prohibited_use,
        "attribution": source.attribution,
    }
    issues.extend(_required_issues(required))

    if source.source_category in PROHIBITED_SOURCE_CATEGORIES:
        issues.append(
            ValidationIssue(
                "source_category",
                "prohibited_source_category",
                f"{source.source_category} is not allowed for Fantasy Trade Lab.",
            )
        )
    elif source.source_category and source.source_category not in FANTASY_SOURCE_CATEGORIES:
        issues.append(
            ValidationIssue(
                "source_category",
                "unknown_source_category",
                f"{source.source_category} is not a recognized fantasy source category.",
            )
        )

    issues.extend(
        validate_artifact_text_fields(
            "fantasy_source",
            {
                "source_id": source.source_id,
                "source_name": source.source_name,
                "allowed_use": source.allowed_use,
                "prohibited_use": source.prohibited_use,
                "attribution": source.attribution,
                "notes": source.notes,
            },
        )
    )
    issues.extend(validate_research_config(source.config))
    return tuple(issues)


def validate_trade_package(package: FantasyTradePackage) -> tuple[ValidationIssue, ...]:
    issues: list[ValidationIssue] = []
    required = {
        "trade_mode": package.trade_mode,
        "target_player": package.target_player,
        "outgoing_player": package.outgoing_player,
        "public_market_fairness": package.public_market_fairness,
        "keeper_impact": package.keeper_impact,
        "drop_pressure_impact": package.drop_pressure_impact,
        "rookie_pick_context": package.rookie_pick_context,
        "verdict": package.verdict,
        "review_status": package.review_status,
    }
    issues.extend(_required_issues(required))

    if package.trade_mode and package.trade_mode not in VALID_TRADE_MODES:
        issues.append(
            ValidationIssue("trade_mode", "invalid_trade_mode", "Unknown trade mode.")
        )
    if package.review_status and package.review_status not in VALID_REVIEW_STATUSES:
        issues.append(
            ValidationIssue(
                "review_status",
                "invalid_review_status",
                "Unknown review status.",
            )
        )
    if not package.give_assets and not package.get_assets:
        issues.append(
            ValidationIssue(
                "assets",
                "assets_required",
                "At least one give or get asset is required.",
            )
        )

    issues.extend(validate_trade_package_payload(package.__dict__))
    return tuple(issues)


def validate_trade_package_payload(
    payload: Mapping[str, object],
) -> tuple[ValidationIssue, ...]:
    issues: list[ValidationIssue] = []
    for field_name in TRADE_PACKAGE_REQUIRED_FIELDS:
        value = payload.get(field_name)
        if value is None or (isinstance(value, str) and not value.strip()):
            issues.append(
                ValidationIssue(field_name, "required", f"{field_name} is required.")
            )

    text_fields = _collect_text_fields(payload)
    issues.extend(validate_artifact_text_fields("trade_package", text_fields))
    return tuple(issues)


def validate_artifact_text_fields(
    artifact_type: str,
    fields: Mapping[str, str],
) -> tuple[ValidationIssue, ...]:
    issues: list[ValidationIssue] = []
    scoped = {f"{artifact_type}.{key}": value for key, value in fields.items()}
    issues.extend(_pattern_issues(scoped, WALL_STREET_PATTERNS, "prohibited_wall_street_language"))
    issues.extend(_pattern_issues(scoped, SECRET_PATTERNS, "secret_like_language"))
    issues.extend(
        _pattern_issues(
            scoped,
            AUTOMATED_DECISION_PATTERNS,
            "prohibited_automated_decisioning",
        )
    )
    return tuple(issues)


def validate_research_config(config: Mapping[str, object]) -> tuple[ValidationIssue, ...]:
    text_fields = _collect_text_fields(config)
    text_fields.update(_collect_key_fields(config))
    return validate_artifact_text_fields("config", text_fields)


def _required_issues(fields: Mapping[str, object]) -> tuple[ValidationIssue, ...]:
    issues: list[ValidationIssue] = []
    for field_name, value in fields.items():
        if value is None or not str(value).strip():
            issues.append(
                ValidationIssue(field_name, "required", f"{field_name} is required.")
            )
    return tuple(issues)


def _pattern_issues(
    fields: Mapping[str, str],
    patterns: tuple[re.Pattern[str], ...],
    code: str,
) -> tuple[ValidationIssue, ...]:
    issues: list[ValidationIssue] = []
    for field_name, value in fields.items():
        for pattern in patterns:
            if pattern.search(value):
                issues.append(
                    ValidationIssue(field_name, code, "Text contains prohibited language.")
                )
                break
    return tuple(issues)


def _collect_text_fields(value: object, path: str = "") -> dict[str, str]:
    fields: dict[str, str] = {}
    if isinstance(value, str):
        fields[path or "value"] = value
    elif isinstance(value, Mapping):
        for key, nested_value in value.items():
            nested_path = f"{path}.{key}" if path else str(key)
            fields.update(_collect_text_fields(nested_value, nested_path))
    elif isinstance(value, (list, tuple, set)):
        for index, nested_value in enumerate(value):
            nested_path = f"{path}[{index}]" if path else f"value[{index}]"
            fields.update(_collect_text_fields(nested_value, nested_path))
    return fields


def _collect_key_fields(value: object, path: str = "") -> dict[str, str]:
    fields: dict[str, str] = {}
    if isinstance(value, Mapping):
        for key, nested_value in value.items():
            key_text = str(key)
            nested_path = f"{path}.{key_text}" if path else key_text
            fields[f"{nested_path}.__key__"] = key_text
            fields.update(_collect_key_fields(nested_value, nested_path))
    elif isinstance(value, (list, tuple, set)):
        for index, nested_value in enumerate(value):
            nested_path = f"{path}[{index}]" if path else f"value[{index}]"
            fields.update(_collect_key_fields(nested_value, nested_path))
    return fields
