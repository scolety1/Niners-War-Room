from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import date

ALLOWED_SOURCE_CATEGORIES = frozenset(
    {
        "public_market_data",
        "public_company_filings",
        "public_economic_data",
        "public_news_research",
        "manual_paper_trade_journal",
        "simulated_portfolio_watchlist",
    }
)

PROHIBITED_SOURCE_CATEGORIES = frozenset(
    {
        "broker_credentials",
        "account_keys",
        "private_brokerage_data",
        "real_money_execution_data",
        "automated_trading_endpoint",
        "secrets",
    }
)

ALLOWED_SOURCE_USES = frozenset(
    {
        "education_research",
        "paper_trading_note",
        "historical_analysis_design",
        "watchlist_note",
        "risk_journal",
        "source_inventory",
    }
)

WATCHLIST_NOTE_REQUIRED_FIELDS = (
    "symbol",
    "research_theme",
    "hypothesis",
    "public_sources",
    "risk_notes",
    "paper_only",
    "review_date",
)

PAPER_JOURNAL_REQUIRED_FIELDS = (
    "journal_id",
    "date",
    "symbol_or_topic",
    "asset_type",
    "research_question",
    "paper_action_type",
    "hypothetical_entry_reference",
    "hypothetical_exit_reference",
    "position_sizing_hypothesis",
    "risk_hypothesis",
    "invalidation_condition",
    "outcome_review_date",
    "lessons_learned",
    "status",
    "notes",
)

EXECUTION_TEXT_PATTERNS = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"\bbroker\s+order\b",
        r"\bbroker\s+api\b",
        r"\border\s+endpoint\b",
        r"\bexecution\s+endpoint\b",
        r"\bautomated\s+execution\b",
        r"\bauto[-\s]?execute\b",
        r"\breal[-\s]?money\s+trading\b",
        r"\blive\s+trading\b",
        r"\bplace\s+orders?\b",
        r"\bsubmit\s+orders?\b",
        r"\btrading\s+api\b",
    )
)

PRIVATE_ACCOUNT_TEXT_PATTERNS = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"\bbrokerage\s+balance\b",
        r"\baccount\s+balance\b",
        r"\bprivate\s+brokerage\b",
        r"\bbrokerage\s+export\b",
        r"\breal[-\s]?money\s+order\s+history\b",
        r"\baccount\s+holdings?\b",
    )
)

SECRET_FIELD_MARKERS = frozenset(
    {
        "api_key",
        "apikey",
        "secret",
        "token",
        "password",
        "passwd",
        "credential",
        "credentials",
        "account_key",
        "private_key",
        "client_secret",
        "oauth",
        "bearer",
        "session_cookie",
    }
)

SECRET_VALUE_PATTERNS = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
        r"\bAKIA[0-9A-Z]{12,}\b",
        r"\bASIA[0-9A-Z]{12,}\b",
        r"\bBearer\s+[A-Za-z0-9._~+/=-]{16,}\b",
    )
)


@dataclass(frozen=True)
class ValidationIssue:
    field: str
    code: str
    message: str


@dataclass(frozen=True)
class ResearchSourceMetadata:
    source_id: str
    name: str
    category: str
    intended_use: str
    access_method: str
    attribution: str
    reviewed_on: str | None = None
    notes: str = ""
    config: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class WatchlistNote:
    symbol: str
    research_theme: str
    hypothesis: str
    public_sources: tuple[str, ...]
    risk_notes: str
    paper_only: bool
    review_date: str


@dataclass(frozen=True)
class PaperJournalEntry:
    journal_id: str
    date: str
    symbol_or_topic: str
    asset_type: str
    research_question: str
    paper_action_type: str
    hypothetical_entry_reference: str
    hypothetical_exit_reference: str
    position_sizing_hypothesis: str
    risk_hypothesis: str
    invalidation_condition: str
    outcome_review_date: str
    lessons_learned: str
    status: str
    notes: str


def validate_source_metadata(source: ResearchSourceMetadata) -> tuple[ValidationIssue, ...]:
    issues: list[ValidationIssue] = []

    required_fields = {
        "source_id": source.source_id,
        "name": source.name,
        "category": source.category,
        "intended_use": source.intended_use,
        "access_method": source.access_method,
        "attribution": source.attribution,
    }
    for field_name, value in required_fields.items():
        if not str(value).strip():
            issues.append(
                ValidationIssue(field_name, "required", f"{field_name} is required.")
            )

    if source.category in PROHIBITED_SOURCE_CATEGORIES:
        issues.append(
            ValidationIssue(
                "category",
                "prohibited_source_category",
                f"{source.category} is prohibited in Trading Lab.",
            )
        )
    elif source.category and source.category not in ALLOWED_SOURCE_CATEGORIES:
        issues.append(
            ValidationIssue(
                "category",
                "unknown_source_category",
                f"{source.category} is not an allowed Trading Lab source category.",
            )
        )

    if source.intended_use and source.intended_use not in ALLOWED_SOURCE_USES:
        issues.append(
            ValidationIssue(
                "intended_use",
                "unknown_source_use",
                f"{source.intended_use} is not an allowed Trading Lab source use.",
            )
        )

    if source.reviewed_on and not _is_iso_date(source.reviewed_on):
        issues.append(
            ValidationIssue(
                "reviewed_on",
                "invalid_date",
                "reviewed_on must use YYYY-MM-DD when provided.",
            )
        )

    text_fields = {
        "source_id": source.source_id,
        "name": source.name,
        "access_method": source.access_method,
        "attribution": source.attribution,
        "notes": source.notes,
    }
    issues.extend(_execution_text_issues(text_fields))
    issues.extend(validate_research_config(source.config))
    return tuple(issues)


def assert_valid_source_metadata(source: ResearchSourceMetadata) -> None:
    issues = validate_source_metadata(source)
    if issues:
        detail = "; ".join(f"{issue.field}:{issue.code}" for issue in issues)
        raise ValueError(f"Invalid Trading Lab source metadata: {detail}")


def validate_paper_journal_entry(entry: PaperJournalEntry) -> tuple[ValidationIssue, ...]:
    issues: list[ValidationIssue] = []
    required_fields = {
        "journal_id": entry.journal_id,
        "date": entry.date,
        "symbol_or_topic": entry.symbol_or_topic,
        "asset_type": entry.asset_type,
        "research_question": entry.research_question,
        "paper_action_type": entry.paper_action_type,
        "hypothetical_entry_reference": entry.hypothetical_entry_reference,
        "hypothetical_exit_reference": entry.hypothetical_exit_reference,
        "position_sizing_hypothesis": entry.position_sizing_hypothesis,
        "risk_hypothesis": entry.risk_hypothesis,
        "invalidation_condition": entry.invalidation_condition,
        "outcome_review_date": entry.outcome_review_date,
        "lessons_learned": entry.lessons_learned,
        "status": entry.status,
        "notes": entry.notes,
    }
    for field_name, value in required_fields.items():
        if not str(value).strip():
            issues.append(
                ValidationIssue(field_name, "required", f"{field_name} is required.")
            )

    if entry.date and not _is_iso_date(entry.date):
        issues.append(
            ValidationIssue("date", "invalid_date", "date must use YYYY-MM-DD.")
        )
    if entry.outcome_review_date and not _is_iso_date(entry.outcome_review_date):
        issues.append(
            ValidationIssue(
                "outcome_review_date",
                "invalid_date",
                "outcome_review_date must use YYYY-MM-DD.",
            )
        )

    text_fields = {
        "journal_id": entry.journal_id,
        "symbol_or_topic": entry.symbol_or_topic,
        "asset_type": entry.asset_type,
        "research_question": entry.research_question,
        "paper_action_type": entry.paper_action_type,
        "hypothetical_entry_reference": entry.hypothetical_entry_reference,
        "hypothetical_exit_reference": entry.hypothetical_exit_reference,
        "position_sizing_hypothesis": entry.position_sizing_hypothesis,
        "risk_hypothesis": entry.risk_hypothesis,
        "invalidation_condition": entry.invalidation_condition,
        "lessons_learned": entry.lessons_learned,
        "status": entry.status,
        "notes": entry.notes,
    }
    issues.extend(_execution_text_issues(text_fields))
    issues.extend(_private_account_text_issues(text_fields))
    issues.extend(_secret_value_text_issues(text_fields))
    return tuple(issues)


def validate_watchlist_note(note: WatchlistNote) -> tuple[ValidationIssue, ...]:
    issues: list[ValidationIssue] = []
    required_fields = {
        "symbol": note.symbol,
        "research_theme": note.research_theme,
        "hypothesis": note.hypothesis,
        "risk_notes": note.risk_notes,
        "review_date": note.review_date,
    }
    for field_name, value in required_fields.items():
        if not str(value).strip():
            issues.append(
                ValidationIssue(field_name, "required", f"{field_name} is required.")
            )

    if not note.paper_only:
        issues.append(
            ValidationIssue(
                "paper_only",
                "paper_only_required",
                "Watchlist notes must be paper-only research records.",
            )
        )

    if not note.public_sources:
        issues.append(
            ValidationIssue(
                "public_sources",
                "public_source_required",
                "At least one public source citation is required.",
            )
        )
    elif any(not source.strip() for source in note.public_sources):
        issues.append(
            ValidationIssue(
                "public_sources",
                "blank_public_source",
                "Public source citations cannot be blank.",
            )
        )

    if note.review_date and not _is_iso_date(note.review_date):
        issues.append(
            ValidationIssue(
                "review_date",
                "invalid_date",
                "review_date must use YYYY-MM-DD.",
            )
        )

    issues.extend(
        _execution_text_issues(
            {
                "symbol": note.symbol,
                "research_theme": note.research_theme,
                "hypothesis": note.hypothesis,
                "risk_notes": note.risk_notes,
                "public_sources": " ".join(note.public_sources),
            }
        )
    )
    return tuple(issues)


def validate_research_config(
    config: Mapping[str, object],
    *,
    path: str = "config",
) -> tuple[ValidationIssue, ...]:
    issues: list[ValidationIssue] = []
    for key, value in config.items():
        key_text = str(key)
        key_path = f"{path}.{key_text}"
        if _contains_secret_field_marker(key_text):
            issues.append(
                ValidationIssue(
                    key_path,
                    "secret_like_field",
                    "Secret-like config fields are prohibited in Trading Lab.",
                )
            )

        if isinstance(value, Mapping):
            issues.extend(validate_research_config(value, path=key_path))
        elif isinstance(value, str):
            issues.extend(_execution_text_issues({key_path: value}))
            if _contains_secret_value_marker(value):
                issues.append(
                    ValidationIssue(
                        key_path,
                        "secret_like_value",
                        "Secret-like values are prohibited in Trading Lab.",
                    )
                )
    return tuple(issues)


def _execution_text_issues(fields: Mapping[str, str]) -> tuple[ValidationIssue, ...]:
    issues: list[ValidationIssue] = []
    for field_name, value in fields.items():
        for pattern in EXECUTION_TEXT_PATTERNS:
            if pattern.search(value):
                issues.append(
                    ValidationIssue(
                        field_name,
                        "prohibited_execution_language",
                        "Broker, order, live-trading, or execution language is prohibited.",
                    )
                )
                break
    return tuple(issues)


def _private_account_text_issues(fields: Mapping[str, str]) -> tuple[ValidationIssue, ...]:
    issues: list[ValidationIssue] = []
    for field_name, value in fields.items():
        for pattern in PRIVATE_ACCOUNT_TEXT_PATTERNS:
            if pattern.search(value):
                issues.append(
                    ValidationIssue(
                        field_name,
                        "prohibited_private_account_language",
                        "Private brokerage or account-balance language is prohibited.",
                    )
                )
                break
    return tuple(issues)


def _secret_value_text_issues(fields: Mapping[str, str]) -> tuple[ValidationIssue, ...]:
    issues: list[ValidationIssue] = []
    for field_name, value in fields.items():
        if _contains_secret_value_marker(value):
            issues.append(
                ValidationIssue(
                    field_name,
                    "secret_like_value",
                    "Secret-like values are prohibited in Trading Lab.",
                )
            )
    return tuple(issues)


def _contains_secret_field_marker(value: str) -> bool:
    normalized = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    parts = frozenset(part for part in normalized.split("_") if part)
    return normalized in SECRET_FIELD_MARKERS or bool(parts & SECRET_FIELD_MARKERS)


def _contains_secret_value_marker(value: str) -> bool:
    return any(pattern.search(value) for pattern in SECRET_VALUE_PATTERNS)


def _is_iso_date(value: str) -> bool:
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True
