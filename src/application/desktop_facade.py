"""Framework-neutral application facade consumed by the local desktop API."""

from __future__ import annotations

import json
import os
import threading
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

import pandas as pd

from src.services.draft_day_app_v1_service import (
    DYNASTY_BOARD_FILE_NAME,
    EXPECTED_DYNASTY_RANKINGS_HASH,
    file_sha256,
    load_dynasty_rankings,
    normalize_dynasty_rankings_frame,
    validate_dynasty_rankings,
)
from src.services.draft_day_app_v1_service import (
    REPO_ROOT as SERVICE_REPO_ROOT,
)
from src.services.draft_day_trade_lab_service import (
    build_registry_trade_item_lookup,
    replace_trade_state,
)
from src.services.governed_asset_registry_service import (
    BLOCKED_ROOKIES_RELATIVE,
    CURRENT_BOARD_RELATIVE,
    CURRENT_BOARD_SHA256,
    FUTURE_PICKS_RELATIVE,
    PICKS_RELATIVE,
    ROOKIE_BOARD_RELATIVE,
    GovernedAssetRegistry,
    load_governed_asset_registry,
)
from src.services.market_baseline_service import DEFAULT_ARTIFACT_DIR
from src.services.outcome_v3_display_service import (
    OutcomeV3DisplayBundle,
    load_outcome_v3_display,
    outcome_v3_player_matrix,
)
from src.services.owner_asset_evidence_service import (
    OwnerAssetEvidenceBundle,
    compose_owner_asset_evidence,
)
from src.services.owner_caveat_presentation_service import owner_caveat_text
from src.services.owner_mode_view_service import (
    market_decision_label,
    market_rank_gap,
    owner_range_contract,
    owner_rankings_frame,
    owner_risk,
    translate_research_tier,
)
from src.services.personal_workspace_service import (
    DEFAULT_WORKSPACE_ROOT,
    WorkspaceValidationError,
    create_decision,
    create_workspace_backup,
    load_store,
    preview_workspace_restore,
    restore_workspace,
    save_personal_entry,
    save_scenario,
    scenario_source_status,
    summarize_workspace,
)
from src.services.personal_workspace_service import (
    TEAM_WINDOWS as WORKSPACE_TEAM_WINDOWS,
)
from src.services.personal_workspace_service import (
    workspace_root as resolve_workspace_root,
)
from src.services.player_compare_decision_service import (
    build_player_compare_decision_summary,
    decision_summary_rows,
)
from src.services.player_compare_owner_summary_service import build_owner_compare_summary
from src.services.player_compare_universe_service import (
    NO_COMMON_SCALE_NOTE,
    PlayerCompareUniverse,
    build_player_compare_universe,
)
from src.services.player_rank_owner_explanation_service import (
    owner_rank_explanation,
    owner_rank_reason_bullets,
)
from src.services.redraft_engine_v1_service import (
    LeagueProfile,
    RedraftPersistenceError,
    RedraftValidationError,
    active_profile,
    active_profile_id,
    build_health_report,
    builtin_presets,
    create_profile,
    duplicate_profile,
    generate_rankings,
    install_projection_snapshot,
    list_profiles,
    load_draft_board,
    load_profile,
    load_projection_snapshot,
    mark_player_drafted,
    profile_store_errors,
    projection_snapshot_path,
    redraft_store_root,
    save_profile,
    set_active_profile,
    undo_last_draft_pick,
)
from src.services.sleeper_redraft_owner_service import (
    SleeperRedraftImportError,
    import_sleeper_redraft_profile,
)
from src.services.rookie_draft_eligibility_service import (
    LIVE_IDENTITY_RELATIVE,
    load_rookie_draft_eligibility_overlay,
    reconcile_rookie_draft_readiness,
)
from src.services.rookie_owner_experience_service import load_owner_rookie_board
from src.services.trade_brief_export_service import (
    TradeBriefValidationError,
    build_trade_brief,
)
from src.services.trade_decision_assistant_service import (
    TEAM_WINDOWS,
    evaluate_trade_decision,
)
from src.services.unified_research_preview_service import (
    UnifiedResearchPreview,
    load_unified_research_preview,
)

MODES = ("dynasty", "redraft")
PLANNING_MODULE_IDS = (
    "roster",
    "picks",
    "keeper",
    "drop",
    "trade",
    "draft",
)
PLANNING_SCENARIO_PREFIX = "desktop-planning:"
PLANNING_CHECK_COUNT = 4
PLANNING_NOTES_LIMIT = 8_000
TRADE_SCENARIO_PREFIX = "desktop-trade:"
TRADE_TITLE_LIMIT = 160
TRADE_NOTES_LIMIT = 20_000
PERSONAL_NOTES_LIMIT = 8_000
DECISION_RATIONALE_LIMIT = 8_000
DESKTOP_DECISION_TYPES = {
    "player evaluation",
    "draft target",
    "roster cut",
    "waiver target",
    "custom note",
}
TRADE_COUNTER_BLOCKED_MESSAGE = (
    "Named counters are unavailable because this desktop release does not include a "
    "verified owner-and-opponent roster and future-pick ownership snapshot."
)
OUTCOME_PACKET_RELATIVE = Path("docs/hq/master/nwr_outcome_columns_v3_rc1_v1_20260729")
OUTCOME_INTEGRATION_RELATIVE = OUTCOME_PACKET_RELATIVE / "OUTCOME_V3_INTEGRATION_PACK.csv"
OUTCOME_MANIFEST_RELATIVE = OUTCOME_PACKET_RELATIVE / "MANIFEST.json"
RESEARCH_PACKET_RELATIVE = Path("docs/hq/model/nwr_unified_research_preview_v1_20260808")
FROZEN_DYNASTY_BOARD_RELATIVE = Path(
    "docs/hq/model/current_board_deterministic_rebuild_with_recovery_inputs_v1_20260708/"
    "rebuilt_full_player_board_value_review_rows.csv"
)
RESEARCH_FILES = (
    RESEARCH_PACKET_RELATIVE / "UNIFIED_DYNASTY_RESEARCH_PREVIEW.csv",
    RESEARCH_PACKET_RELATIVE / "ROOKIE_VETERAN_NEIGHBORHOODS.csv",
    RESEARCH_PACKET_RELATIVE / "MANIFEST.json",
)
DYNASTY_PRODUCT = {
    "title": "Niners War Room — Dynasty",
    "contextLabel": "Dynasty · Long term",
    "leagueLabel": "10-team · 1QB",
    "authority": "Finished V1",
}
REDRAFT_PRODUCT = {
    "title": "Niners War Room — Redraft",
    "contextLabel": "Redraft · Current season",
    "authority": "Redraft V1 — review authority",
}
REDRAFT_SEED_PACKET_RELATIVE = Path(
    "docs/hq/model/nwr_redraft_2026_rookie_projection_candidate_v1_20260809"
)
REDRAFT_SEED_SOURCE_RELATIVE = (
    REDRAFT_SEED_PACKET_RELATIVE / "GOVERNED_COMBINED_608_PROJECTION_SNAPSHOT.csv"
)
REDRAFT_SEED_APPROVAL_RELATIVE = REDRAFT_SEED_PACKET_RELATIVE / "NWR_DATA_GOVERNANCE.json"
REDRAFT_SEED_BLOCKED_RELATIVE = REDRAFT_SEED_PACKET_RELATIVE / "BLOCKED_2026_ROOKIES.csv"
REDRAFT_SEED_SHA256 = "e483caaedc236140bcdfeccdd759bf8726a4b231bbaf3e9fdc461873d3921c25"


class FacadeError(RuntimeError):
    """Controlled, user-safe application boundary error."""

    def __init__(self, code: str, message: str, *, status: int = 400) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status


@dataclass(frozen=True)
class FacadePayload:
    data: dict[str, Any]
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class _RankingsSource:
    frame: pd.DataFrame
    source_hash: str
    warnings: tuple[str, ...]
    source_file: Path


@dataclass(frozen=True)
class _OwnerSnapshot:
    rankings: pd.DataFrame
    rookies: pd.DataFrame
    registry: GovernedAssetRegistry
    research: UnifiedResearchPreview
    outcome: OutcomeV3DisplayBundle
    evidence: OwnerAssetEvidenceBundle
    compare: PlayerCompareUniverse
    rank_receipts: Mapping[str, Mapping[str, Any]]
    dynasty_hash: str
    warnings: tuple[str, ...]


class DesktopBackendFacade:
    """Cached, deterministic facade over admitted NWR services.

    The facade deliberately has no dependency on ``app`` or Streamlit. The Redraft
    bootstrap may install the bundled, governed projection snapshot on first use;
    all durable writes delegate to the existing validated, atomic Redraft service.
    """

    def __init__(
        self,
        *,
        repo_root: str | Path,
        mode: str,
        redraft_root: str | Path | None = None,
        workspace_root: str | Path | None = None,
        legacy_workspace_root: str | Path | None = None,
    ) -> None:
        normalized_mode = str(mode).strip().lower()
        if normalized_mode not in MODES:
            raise ValueError(f"Unsupported desktop mode: {mode}")
        self.repo_root = Path(repo_root).expanduser().resolve()
        self.mode = normalized_mode
        self.redraft_root = (
            Path(redraft_root).expanduser().resolve()
            if redraft_root is not None
            else redraft_store_root(self.repo_root)
        )
        self.workspace_root = (
            Path(workspace_root).expanduser().resolve() if workspace_root is not None else None
        )
        self.legacy_workspace_root = (
            Path(legacy_workspace_root).expanduser().resolve()
            if legacy_workspace_root is not None
            else DEFAULT_WORKSPACE_ROOT
        )
        self._snapshot_lock = threading.RLock()
        self._redraft_seed_lock = threading.Lock()
        self._snapshot_key: tuple[tuple[str, int, int], ...] | None = None
        self._snapshot_value: _OwnerSnapshot | None = None

    def bootstrap(self) -> FacadePayload:
        if self.mode == "dynasty":
            return self.dynasty_bootstrap()
        return self.redraft_bootstrap()

    def dynasty_bootstrap(self) -> FacadePayload:
        self._require_mode("dynasty")
        snapshot = self._owner_snapshot()
        warnings = list(snapshot.warnings)
        workspace_counts: dict[str, int]
        try:
            workspace_counts = summarize_workspace(root=self.workspace_root)
        except (OSError, ValueError):
            workspace_counts = {}
            warnings.append("Personal workspace status is unavailable.")

        ranking_rows = [
            self._dynasty_ranking_payload(row) for row in snapshot.rankings.to_dict("records")
        ]
        rookie_rows = self._rookie_records(snapshot.rookies)
        asset_options = [self._asset_option(row) for row in snapshot.evidence.rows]
        trade_lookup = build_registry_trade_item_lookup(snapshot.evidence.rows)
        reconciled_readiness = reconcile_rookie_draft_readiness(
            snapshot.registry.rookie_eligibility_rows,
            surface_asset_ids={
                "registry": [
                    _text(row.get("asset_id")) for row in snapshot.registry.rows
                ],
                "detail": [_text(row.get("asset_id")) for row in snapshot.evidence.rows],
                "search": [
                    _text(row.get("assetId"))
                    for row in asset_options
                    if _flag(row.get("searchable"))
                ],
                "selectable": [
                    _text(row.get("assetId"))
                    for row in asset_options
                    if _flag(row.get("selectable"))
                ],
                "compare": [
                    _text(row.get("asset_id"))
                    for row in snapshot.compare.frame.to_dict("records")
                    if _flag(row.get("selectable"), default=True)
                ],
                "trade": [
                    _text(row.get("asset_id")) for row in trade_lookup.values()
                ],
                "draftable": [
                    _text(row.get("assetId"))
                    for row in rookie_rows
                    if _flag(row.get("draftable"))
                ],
                "rookie_board": [_text(row.get("assetId")) for row in rookie_rows],
                "draft_cockpit": [
                    _text(row.get("assetId"))
                    for row in rookie_rows
                    if _flag(row.get("draftable")) and _flag(row.get("selectable"))
                ],
            },
            source_errors=snapshot.registry.errors,
        )
        rookie_readiness = self._rookie_readiness_payload(reconciled_readiness)
        current_players = tuple(
            row
            for row in snapshot.evidence.rows
            if _text(row.get("asset_type")) == "Current Player"
        )
        market_matched = sum(
            _number(row.get("market_dp_rank")) is not None for row in current_players
        )
        freshness = snapshot.evidence.market_freshness
        market_date = _text(freshness.get("upstream_scrape_date"))
        if not market_date:
            market_date = next(
                (
                    _text(row.get("market_evidence_date"))
                    for row in current_players
                    if _text(row.get("market_evidence_date"))
                ),
                "",
            )
        freshness_code = _text(freshness.get("freshness_status"))
        freshness_label = (
            freshness_code.replace("_", " ").title() if freshness_code else "Freshness unavailable"
        )
        freshness_message = _text(freshness.get("market_baseline_stale_warning"))
        if not freshness_message:
            freshness_message = (
                "Market evidence is display-only and never changes the Finished V1 order."
            )
        if freshness_message and "stale" in freshness_message.casefold():
            warnings.append(freshness_message)
        normalized_warnings = tuple(dict.fromkeys(warnings))
        status_tone = "review" if normalized_warnings or "STALE" in freshness_code else "ready"
        source_hashes = {
            **snapshot.registry.source_hashes,
            "dynasty_finished_v1": snapshot.dynasty_hash,
            "outcome_v3": snapshot.outcome.source_hash,
        }
        data = {
            "product": dict(DYNASTY_PRODUCT),
            "status": {
                "ready": True,
                "tone": status_tone,
                "authority": "Finished V1",
                "sourceAsOf": market_date,
                "freshness": freshness_label,
                "summary": ("Finished V1 rankings and governed decision context are loaded."),
                "scheduledRefresh": "Off — owner approval required",
                "errors": [],
                "warnings": list(normalized_warnings),
                "sourceHashes": source_hashes,
            },
            "summary": {
                "rankedPlayers": len(ranking_rows),
                "marketMatched": market_matched,
                "rookieRows": len(rookie_rows),
                "blockedRookies": rookie_readiness["unresolved"],
                "manualReviewRookies": rookie_readiness["manualReview"],
                "outcomeRows": snapshot.outcome.row_count,
                "workspace": self._workspace_summary(workspace_counts),
            },
            "rankings": ranking_rows,
            "rookies": rookie_rows,
            "assetOptions": asset_options,
            "rookieReadiness": rookie_readiness,
            "marketFreshness": {
                "sourceAsOf": market_date,
                "status": freshness_label,
                "message": freshness_message,
            },
            "planning": self._planning_workspace(),
            "notices": [
                {
                    "tone": "ready" if rookie_readiness["ready"] else "blocked",
                    "title": rookie_readiness["alertTitle"],
                    "message": rookie_readiness["alertMessage"],
                },
                {
                    "tone": "review",
                    "title": "Rookie Review refresh available",
                    "message": (
                        "New factual rookie information is available. Draft eligibility has "
                        "been updated, but the frozen Rookie Review score has not been rebuilt."
                    ),
                },
                {
                    "tone": "review",
                    "title": "Market evidence is display-only",
                    "message": ("External consensus never changes the Finished V1 rank or score."),
                },
                {
                    "tone": "review",
                    "title": "Rookie authority stays separate",
                    "message": (
                        "Rookie Review and current-player scores do not share a numeric scale."
                    ),
                },
                {
                    "tone": "ready",
                    "title": "Outcome V3 is context only",
                    "message": (
                        "Governed outcome probabilities remain separate from production rankings."
                    ),
                },
            ],
        }
        return FacadePayload(data=data, warnings=normalized_warnings)

    def dynasty_workspace(self) -> FacadePayload:
        """Return owner-only overlays without changing any analytical authority."""

        self._require_mode("dynasty")
        return FacadePayload(data=self._dynasty_workspace_payload())

    def save_dynasty_personal_entry(
        self,
        *,
        asset_id: str,
        watchlist: bool,
        target: bool,
        avoid: bool,
        tags: Sequence[str],
        notes: str,
        team_window: str,
    ) -> FacadePayload:
        self._require_mode("dynasty")
        snapshot = self._owner_snapshot()
        normalized_id = self._asset_id(asset_id)
        asset = snapshot.evidence.by_id.get(normalized_id)
        if asset is None:
            raise FacadeError("ASSET_NOT_FOUND", "The selected asset was not found.", status=404)
        if not all(isinstance(value, bool) for value in (watchlist, target, avoid)):
            raise FacadeError(
                "PERSONAL_BOARD_FLAGS_INVALID",
                "Personal Board flags must be selected explicitly.",
            )
        if team_window not in WORKSPACE_TEAM_WINDOWS:
            raise FacadeError(
                "PERSONAL_BOARD_WINDOW_INVALID",
                "Choose a supported team window.",
            )
        if not isinstance(notes, str) or len(notes) > PERSONAL_NOTES_LIMIT:
            raise FacadeError(
                "PERSONAL_BOARD_NOTES_INVALID",
                f"Personal notes cannot exceed {PERSONAL_NOTES_LIMIT} characters.",
            )
        if isinstance(tags, (str, bytes)) or any(not isinstance(tag, str) for tag in tags):
            raise FacadeError(
                "PERSONAL_BOARD_TAGS_INVALID",
                "Tags must be a list of short labels.",
            )
        normalized_tags = list(
            dict.fromkeys(tag.strip() for tag in tags if tag.strip())
        )
        if len(normalized_tags) > 12 or any(len(tag) > 40 for tag in normalized_tags):
            raise FacadeError(
                "PERSONAL_BOARD_TAGS_INVALID",
                "Use at most 12 tags of 40 characters or fewer.",
            )
        asset_type = _text(asset.get("asset_type"))
        try:
            save_personal_entry(
                {
                    "asset_id": normalized_id,
                    "asset_type": asset_type,
                    "source_authority_version": snapshot.dynasty_hash,
                    "watchlist": watchlist,
                    "target": target,
                    "avoid": avoid,
                    "tags": normalized_tags,
                    "notes": notes,
                    "team_window": team_window,
                },
                asset_registry={
                    key: _text(row.get("asset_type"))
                    for key, row in snapshot.evidence.by_id.items()
                },
                root=self.workspace_root,
            )
        except (OSError, WorkspaceValidationError) as exc:
            raise FacadeError(
                "PERSONAL_BOARD_SAVE_FAILED",
                "The Personal Board entry could not be saved. Your edits remain on screen.",
                status=409,
            ) from exc
        return FacadePayload(data=self._dynasty_workspace_payload())

    def create_dynasty_decision(
        self,
        *,
        title: str,
        decision_type: str,
        asset_ids: Sequence[str],
        rationale: str,
    ) -> FacadePayload:
        self._require_mode("dynasty")
        snapshot = self._owner_snapshot()
        normalized_title = str(title).strip()
        normalized_type = str(decision_type).strip().lower()
        if not normalized_title or len(normalized_title) > 160:
            raise FacadeError(
                "DECISION_TITLE_INVALID",
                "Decision title is required and cannot exceed 160 characters.",
            )
        if normalized_type not in DESKTOP_DECISION_TYPES:
            raise FacadeError(
                "DECISION_TYPE_INVALID",
                "Choose a supported owner decision type.",
            )
        if not isinstance(rationale, str) or not rationale.strip():
            raise FacadeError("DECISION_RATIONALE_INVALID", "Decision context is required.")
        if len(rationale) > DECISION_RATIONALE_LIMIT:
            raise FacadeError(
                "DECISION_RATIONALE_INVALID",
                f"Decision context cannot exceed {DECISION_RATIONALE_LIMIT} characters.",
            )
        if isinstance(asset_ids, (str, bytes)):
            raise FacadeError("DECISION_ASSETS_INVALID", "Choose between one and eight assets.")
        normalized_assets = [self._asset_id(value) for value in asset_ids]
        if not 1 <= len(normalized_assets) <= 8 or len(normalized_assets) != len(
            set(normalized_assets)
        ):
            raise FacadeError(
                "DECISION_ASSETS_INVALID",
                "Choose between one and eight unique assets.",
            )
        registry = {
            key: _text(row.get("asset_type"))
            for key, row in snapshot.evidence.by_id.items()
        }
        if any(asset_id not in registry for asset_id in normalized_assets):
            raise FacadeError(
                "DECISION_ASSETS_INVALID",
                "A selected asset is not available in the governed registry.",
            )
        source_snapshot = {
            asset_id: {
                "asset_type": registry[asset_id],
                "asset_name": _text(snapshot.evidence.by_id[asset_id].get("asset_name")),
                "authority": _text(snapshot.evidence.by_id[asset_id].get("authority")),
            }
            for asset_id in normalized_assets
        }
        try:
            create_decision(
                {
                    "decision_id": f"desktop-decision:{uuid4().hex}",
                    "decision_type": normalized_type,
                    "status": "Draft",
                    "title": normalized_title,
                    "assets": normalized_assets,
                    "source_snapshot": source_snapshot,
                    "rationale": rationale.strip(),
                },
                asset_registry=registry,
                root=self.workspace_root,
            )
        except (OSError, WorkspaceValidationError) as exc:
            raise FacadeError(
                "DECISION_SAVE_FAILED",
                "The decision could not be saved. Your edits remain on screen.",
                status=409,
            ) from exc
        return FacadePayload(data=self._dynasty_workspace_payload())

    def backup_dynasty_workspace(self) -> FacadePayload:
        self._require_mode("dynasty")
        try:
            create_workspace_backup(root=self.workspace_root)
        except (OSError, WorkspaceValidationError) as exc:
            raise FacadeError(
                "WORKSPACE_BACKUP_FAILED",
                "NWR could not create a verified local backup.",
                status=409,
            ) from exc
        return FacadePayload(data=self._dynasty_workspace_payload())

    def check_dynasty_workspace_restore(self) -> FacadePayload:
        self._require_mode("dynasty")
        return FacadePayload(data=self._dynasty_workspace_payload(check_restore=True))

    def adopt_legacy_dynasty_workspace(self, *, confirmed: bool) -> FacadePayload:
        """Create-only import from the established Streamlit workspace root."""

        self._require_mode("dynasty")
        if confirmed is not True:
            raise FacadeError(
                "LEGACY_IMPORT_CONFIRMATION_REQUIRED",
                "Confirm the create-only workspace import.",
            )
        destination = resolve_workspace_root(self.workspace_root)
        source = resolve_workspace_root(self.legacy_workspace_root)
        if source == destination:
            raise FacadeError(
                "LEGACY_IMPORT_NOT_REQUIRED",
                "Desktop is already using the established workspace.",
                status=409,
            )
        destination_stores = destination / "stores"
        if destination_stores.exists() and any(destination_stores.glob("*.json")):
            raise FacadeError(
                "LEGACY_IMPORT_DESTINATION_NOT_EMPTY",
                "Desktop workspace already contains data; nothing was overwritten.",
                status=409,
            )
        try:
            source_backup = create_workspace_backup(root=source)
            if source_backup.path is None or source_backup.file_count == 0:
                raise FacadeError(
                    "LEGACY_IMPORT_SOURCE_EMPTY",
                    "No established Streamlit workspace data was found.",
                    status=404,
                )
            preview = preview_workspace_restore(source_backup.path)
            if not preview.valid:
                raise FacadeError(
                    "LEGACY_IMPORT_SOURCE_INVALID",
                    "The established workspace did not pass its checksum and schema checks.",
                    status=409,
                )
            restored = restore_workspace(
                source_backup.path,
                confirmed=True,
                root=destination,
            )
            if restored.status != "RESTORED":
                raise FacadeError(
                    "LEGACY_IMPORT_FAILED",
                    "The established workspace could not be imported safely.",
                    status=409,
                )
        except FacadeError:
            raise
        except (OSError, WorkspaceValidationError) as exc:
            raise FacadeError(
                "LEGACY_IMPORT_FAILED",
                "The established workspace could not be imported safely.",
                status=409,
            ) from exc
        payload = self._dynasty_workspace_payload()
        payload["message"] = (
            "Established Streamlit workspace imported into Desktop without changing the source."
        )
        return FacadePayload(data=payload)

    def _dynasty_workspace_payload(self, *, check_restore: bool = False) -> dict[str, Any]:
        snapshot = self._owner_snapshot()
        try:
            board = load_store("personal_board", root=self.workspace_root)
            journal = load_store("decision_journal", root=self.workspace_root)
        except (OSError, WorkspaceValidationError):
            return {
                "storeStatus": "blocked",
                "message": "Personal Workspace recovery is required.",
                "updatedAtUtc": "",
                "personalBoard": [],
                "decisions": [],
                "backup": self._workspace_backup_payload(check_restore=check_restore),
            }
        blocked = board.status == "CORRUPT" or journal.status == "CORRUPT"
        entries = []
        for row in board.records if board.status == "LOADED" else ():
            asset_id = _text(row.get("asset_id"))
            asset = snapshot.evidence.by_id.get(asset_id, {})
            entries.append(
                {
                    "assetId": asset_id,
                    "name": _text(asset.get("asset_name")) or asset_id,
                    "assetType": _text(row.get("asset_type")),
                    "watchlist": bool(row.get("watchlist")),
                    "target": bool(row.get("target")),
                    "avoid": bool(row.get("avoid")),
                    "tags": [str(value) for value in row.get("tags", [])],
                    "notes": _text(row.get("notes")),
                    "teamWindow": _text(row.get("team_window")) or "Custom/Unspecified",
                    "createdAtUtc": _text(row.get("created_at_utc")),
                    "updatedAtUtc": _text(row.get("modified_at_utc")),
                }
            )
        entries.sort(key=lambda row: (str(row["name"]).casefold(), str(row["assetId"])))
        decisions = []
        for row in journal.records if journal.status == "LOADED" else ():
            asset_ids = [str(value) for value in row.get("assets", [])]
            decisions.append(
                {
                    "decisionId": _text(row.get("decision_id")),
                    "title": _text(row.get("title")) or "Owner decision",
                    "decisionType": _text(row.get("decision_type")),
                    "status": _text(row.get("status")),
                    "assetIds": asset_ids,
                    "assetNames": [
                        _text(snapshot.evidence.by_id.get(asset_id, {}).get("asset_name"))
                        or asset_id
                        for asset_id in asset_ids
                    ],
                    "rationale": _text(row.get("rationale")),
                    "createdAtUtc": _text(row.get("created_at_utc")),
                    "updatedAtUtc": _text(row.get("modified_at_utc")),
                }
            )
        decisions.sort(
            key=lambda row: (str(row["updatedAtUtc"]), str(row["decisionId"])),
            reverse=True,
        )
        updated_at = max(board.updated_at_utc, journal.updated_at_utc)
        return {
            "storeStatus": (
                "blocked" if blocked else ("loaded" if entries or decisions else "empty")
            ),
            "message": (
                "Personal Workspace recovery is required."
                if blocked
                else "Owner overlays are stored locally and never change NWR rankings."
            ),
            "updatedAtUtc": updated_at,
            "personalBoard": entries,
            "decisions": decisions,
            "backup": self._workspace_backup_payload(check_restore=check_restore),
        }

    def _workspace_backup_payload(self, *, check_restore: bool) -> dict[str, Any]:
        try:
            root = resolve_workspace_root(self.workspace_root)
            backups = sorted(
                (path for path in (root / "backups").glob("workspace-*") if path.is_dir()),
                key=lambda path: path.name,
                reverse=True,
            )
            if not backups:
                return {
                    "status": "none",
                    "backupId": "",
                    "fileCount": 0,
                    "message": "No workspace backup has been created yet.",
                }
            latest = backups[0]
            preview = preview_workspace_restore(latest) if check_restore else None
            return {
                "status": (
                    "ready"
                    if preview is None or preview.valid
                    else "blocked"
                ),
                "backupId": latest.name,
                "fileCount": preview.file_count if preview is not None else 0,
                "message": (
                    preview.message
                    if preview is not None
                    else "A local workspace backup is available."
                ),
            }
        except (OSError, WorkspaceValidationError):
            return {
                "status": "blocked",
                "backupId": "",
                "fileCount": 0,
                "message": "The local backup inventory could not be verified.",
            }

    def save_dynasty_planning_module(
        self,
        *,
        module_id: str,
        checks: Sequence[bool],
        notes: str,
    ) -> FacadePayload:
        """Persist one manual planning module through the governed Personal Workspace."""

        self._require_mode("dynasty")
        normalized_module = str(module_id).strip().lower()
        if normalized_module not in PLANNING_MODULE_IDS:
            raise FacadeError(
                "PLANNING_MODULE_NOT_FOUND", "The planning module was not found.", status=404
            )
        if (
            isinstance(checks, (str, bytes))
            or len(checks) != PLANNING_CHECK_COUNT
            or any(not isinstance(value, bool) for value in checks)
        ):
            raise FacadeError(
                "INVALID_PLANNING_CHECKS",
                f"Planning requires exactly {PLANNING_CHECK_COUNT} boolean checkpoints.",
            )
        if not isinstance(notes, str):
            raise FacadeError("INVALID_PLANNING_NOTES", "Planning notes must be text.")
        if len(notes) > PLANNING_NOTES_LIMIT:
            raise FacadeError(
                "PLANNING_NOTES_TOO_LONG",
                f"Planning notes cannot exceed {PLANNING_NOTES_LIMIT} characters.",
            )

        snapshot = self._owner_snapshot()
        source_versions = {
            **snapshot.registry.source_hashes,
            "dynasty_finished_v1": snapshot.dynasty_hash,
            "outcome_v3": snapshot.outcome.source_hash,
        }
        scenario_id = f"{PLANNING_SCENARIO_PREFIX}{normalized_module}"
        try:
            save_scenario(
                {
                    "scenario_id": scenario_id,
                    "scenario_type": "draft",
                    "title": f"Desktop planning - {normalized_module}",
                    "assets": [],
                    "source_versions": source_versions,
                    "payload": {
                        "module_id": normalized_module,
                        "checks": list(checks),
                        "notes": notes,
                    },
                },
                asset_registry={},
                root=self.workspace_root,
            )
        except (OSError, WorkspaceValidationError) as exc:
            raise FacadeError(
                "PLANNING_SAVE_FAILED",
                "The planning module could not be saved to the Personal Workspace.",
                status=409,
            ) from exc
        return FacadePayload(data=self._planning_workspace())

    def _planning_workspace(self) -> dict[str, Any]:
        modules = {
            module_id: {
                "moduleId": module_id,
                "checks": [False] * PLANNING_CHECK_COUNT,
                "notes": "",
                "saved": False,
                "updatedAtUtc": "",
            }
            for module_id in PLANNING_MODULE_IDS
        }
        try:
            store = load_store("saved_scenarios", root=self.workspace_root)
        except (OSError, WorkspaceValidationError):
            return {
                "storeStatus": "blocked",
                "updatedAtUtc": "",
                "message": "Personal Workspace planning state is unavailable.",
                "modules": list(modules.values()),
            }
        if store.status == "CORRUPT":
            return {
                "storeStatus": "blocked",
                "updatedAtUtc": store.updated_at_utc,
                "message": "Personal Workspace planning state requires recovery.",
                "modules": list(modules.values()),
            }
        for row in store.records:
            scenario_id = str(row.get("scenario_id", ""))
            if not scenario_id.startswith(PLANNING_SCENARIO_PREFIX):
                continue
            module_id = scenario_id.removeprefix(PLANNING_SCENARIO_PREFIX)
            payload = row.get("payload")
            if module_id not in modules or not isinstance(payload, Mapping):
                continue
            checks = payload.get("checks")
            notes = payload.get("notes")
            if (
                not isinstance(checks, list)
                or len(checks) != PLANNING_CHECK_COUNT
                or any(not isinstance(value, bool) for value in checks)
                or not isinstance(notes, str)
            ):
                continue
            modules[module_id] = {
                "moduleId": module_id,
                "checks": list(checks),
                "notes": notes[:PLANNING_NOTES_LIMIT],
                "saved": True,
                "updatedAtUtc": str(row.get("modified_at_utc", "")),
            }
        return {
            "storeStatus": "loaded" if store.status == "LOADED" else "empty",
            "updatedAtUtc": store.updated_at_utc,
            "message": store.message,
            "modules": list(modules.values()),
        }

    def rookie_review(self) -> FacadePayload:
        """Load the governed Rookie Review independently for equivalence testing/use."""

        self._require_mode("dynasty")
        path = self.repo_root / ROOKIE_BOARD_RELATIVE
        try:
            eligibility = load_rookie_draft_eligibility_overlay(repo_root=self.repo_root)
            if eligibility.errors:
                raise ValueError("Rookie eligibility overlay failed its integrity contract")
            frame = load_owner_rookie_board(
                path,
                research_packet_dir=self.repo_root / RESEARCH_PACKET_RELATIVE,
                eligibility_rows=eligibility.rows,
            )
        except (OSError, ValueError, KeyError, pd.errors.ParserError) as exc:
            raise FacadeError(
                "ROOKIE_REVIEW_UNAVAILABLE",
                "The governed Rookie Review is unavailable.",
                status=503,
            ) from exc
        return FacadePayload(data={"rookies": self._rookie_records(frame)})

    def outcome_release_status(self) -> FacadePayload:
        self._require_mode("dynasty")
        bundle = load_outcome_v3_display(
            integration_path=self.repo_root / OUTCOME_INTEGRATION_RELATIVE,
            manifest_path=self.repo_root / OUTCOME_MANIFEST_RELATIVE,
        )
        if not bundle.loaded:
            raise FacadeError(
                "OUTCOME_V3_UNAVAILABLE",
                "The governed Outcome V3 release is unavailable.",
                status=503,
            )
        return FacadePayload(
            data={
                "loaded": True,
                "rowCount": bundle.row_count,
                "playerCount": bundle.player_count,
                "sourceHash": bundle.source_hash,
                "releaseIdentifier": bundle.release_identifier,
            }
        )

    def dynasty_asset(self, asset_id: str) -> FacadePayload:
        self._require_mode("dynasty")
        normalized = self._asset_id(asset_id)
        snapshot = self._owner_snapshot()
        row = snapshot.evidence.by_id.get(normalized)
        if row is None:
            raise FacadeError(
                "ASSET_NOT_FOUND", "The requested governed asset was not found.", status=404
            )
        outcomes: list[dict[str, Any]] = []
        if str(row.get("asset_type")) == "Current Player" and str(row.get("position")) in {
            "QB",
            "RB",
            "WR",
            "TE",
        }:
            board = pd.DataFrame(
                [
                    {
                        "player_id": row.get("player_id", ""),
                        "player_name": row.get("asset_name", ""),
                        "position": row.get("position", ""),
                        "nwr_rank": row.get("dynasty_rank", ""),
                    }
                ]
            )
            matrix, _audit, _details = outcome_v3_player_matrix(
                board,
                snapshot.outcome.frame,
                position=str(row.get("position")),
            )
            outcomes = matrix.to_dict("records")
        player_id = _text(row.get("player_id"))
        return FacadePayload(
            data=self._player_detail_payload(
                row,
                outcomes=outcomes,
                rank_receipt=snapshot.rank_receipts.get(player_id),
                total_ranked=len(snapshot.rank_receipts),
            )
        )

    def compare_dynasty_assets(self, asset_ids: Sequence[str]) -> FacadePayload:
        self._require_mode("dynasty")
        normalized = [self._asset_id(value) for value in asset_ids]
        if not 2 <= len(normalized) <= 4:
            raise FacadeError(
                "INVALID_COMPARE_COUNT", "Player Compare requires two to four assets."
            )
        if len(set(normalized)) != len(normalized):
            raise FacadeError("DUPLICATE_COMPARE_ASSET", "Player Compare assets must be unique.")

        snapshot = self._owner_snapshot()
        if not snapshot.compare.loaded:
            raise FacadeError(
                "PLAYER_COMPARE_UNAVAILABLE",
                "The governed Player Compare universe is unavailable.",
                status=503,
            )
        indexed = {str(row["asset_id"]): row for row in snapshot.compare.frame.to_dict("records")}
        missing = [asset_id for asset_id in normalized if asset_id not in indexed]
        if missing:
            raise FacadeError(
                "COMPARE_ASSET_NOT_FOUND",
                "One or more requested Player Compare assets were not found.",
                status=404,
            )
        rows = [indexed[asset_id] for asset_id in normalized]
        owner_summary = build_owner_compare_summary(rows)
        visible_summary = build_player_compare_decision_summary(rows[0], rows[1], rows[2:])
        context_rows = decision_summary_rows(rows)
        notes = list(owner_summary.notes)
        players: list[dict[str, Any]] = []
        for index, row in enumerate(rows):
            context = context_rows[index] if index < len(context_rows) else {}
            note = notes[index] if index < len(notes) else {}
            players.append(
                {
                    "assetId": row.get("asset_id"),
                    "player": _text(row.get("player")) or "Unknown asset",
                    "dimensions": self._comparison_dimensions(row, context),
                    "advantages": _string_list(note.get("Advantages")),
                    "risks": _string_list(note.get("Risks")),
                }
            )
        compare_warnings = [NO_COMMON_SCALE_NOTE]
        compare_warnings.extend(
            f"No admitted Rookie Review score is available for {_text(row.get('player'))}; "
            "the comparison uses factual draft context only."
            for row in rows
            if _text(row.get("compare_asset_type")) in {"Rookie Review", "Blocked Rookie"}
            and not _flag(row.get("model_score_eligible"))
        )
        compare_warnings.extend(visible_summary.open_review_flags)
        if visible_summary.multi_player_note:
            compare_warnings.append(visible_summary.multi_player_note)
        ranges = []
        for index, value in enumerate(owner_summary.ranges):
            asset_id = normalized[index] if index < len(normalized) else ""
            ranges.append(
                {
                    "assetId": asset_id,
                    "player": _text(value.get("Player")) or "Unknown asset",
                    "floor": _text(value.get("Floor")) or "Not enough information",
                    "expected": _text(value.get("NWR Expected"))
                    or "Not enough information",
                    "ceiling": _text(value.get("Ceiling")) or "Not enough information",
                    "ageWindow": _text(value.get("Age / window"))
                    or "Age/window unavailable",
                    "risk": _text(value.get("Risk / uncertainty"))
                    or "Not enough information",
                    "authority": _text(value.get("Range authority")),
                    "method": _text(value.get("Range method")),
                }
            )
        return FacadePayload(
            data={
                "leans": [asdict(lean) for lean in owner_summary.leans],
                "ranges": ranges,
                "players": players,
                "warnings": list(dict.fromkeys(compare_warnings)),
            }
        )

    def evaluate_dynasty_trade(
        self,
        *,
        give: Sequence[str],
        receive: Sequence[str],
        team_window: str,
    ) -> FacadePayload:
        self._require_mode("dynasty")
        _snapshot, give_ids, receive_ids, lookup, key_for_id = self._trade_context(
            give=give,
            receive=receive,
            team_window=team_window,
        )
        state = replace_trade_state(
            [key_for_id[value] for value in give_ids],
            [key_for_id[value] for value in receive_ids],
        )
        decision = evaluate_trade_decision(state, lookup, team_window=team_window)
        return FacadePayload(data=self._trade_decision_payload(decision))

    def list_dynasty_trades(self) -> FacadePayload:
        """List reopenable Trading Lab scenarios from the Personal Workspace."""

        self._require_mode("dynasty")
        return FacadePayload(data=self._trade_workspace())

    def save_dynasty_trade(
        self,
        *,
        scenario_id: str | None,
        title: str,
        give: Sequence[str],
        receive: Sequence[str],
        team_window: str,
        notes: str,
    ) -> FacadePayload:
        """Atomically create or update an exact, recommendation-free trade scenario."""

        self._require_mode("dynasty")
        snapshot, give_ids, receive_ids, _lookup, _key_for_id = self._trade_context(
            give=give,
            receive=receive,
            team_window=team_window,
        )
        normalized_title = self._trade_title(title)
        normalized_notes = self._trade_notes(notes)
        try:
            store = load_store("saved_scenarios", root=self.workspace_root)
        except (OSError, WorkspaceValidationError) as exc:
            raise FacadeError(
                "TRADE_WORKSPACE_UNAVAILABLE",
                "Saved trades are unavailable until the Personal Workspace is recovered.",
                status=409,
            ) from exc
        if store.status == "CORRUPT":
            raise FacadeError(
                "TRADE_WORKSPACE_UNAVAILABLE",
                "Saved trades are unavailable until the Personal Workspace is recovered.",
                status=409,
            )
        if scenario_id is None:
            normalized_scenario_id = f"{TRADE_SCENARIO_PREFIX}{uuid4().hex}"
        else:
            normalized_scenario_id = self._scenario_id(scenario_id)
            existing = next(
                (
                    row
                    for row in store.records
                    if str(row.get("scenario_id", "")) == normalized_scenario_id
                ),
                None,
            )
            if existing is None:
                raise FacadeError(
                    "TRADE_SCENARIO_NOT_FOUND",
                    "The saved trade no longer exists. Refresh the saved-trade list and retry.",
                    status=404,
                )
            if existing.get("scenario_type") != "trading_lab":
                raise FacadeError(
                    "TRADE_SCENARIO_CONFLICT",
                    "The saved scenario ID belongs to a different workspace tool.",
                    status=409,
                )

        def side_row(asset_id: str, side: str) -> dict[str, str]:
            asset = snapshot.evidence.by_id[asset_id]
            return {
                "side": side,
                "asset_id": asset_id,
                "asset_type": _text(asset.get("asset_type")),
                "player": _text(asset.get("asset_name")) or asset_id,
            }

        selected_sides = [side_row(asset_id, "You give") for asset_id in give_ids]
        selected_sides.extend(
            side_row(asset_id, "You receive") for asset_id in receive_ids
        )
        asset_registry = {
            str(asset_id): _text(row.get("asset_type"))
            for asset_id, row in snapshot.evidence.by_id.items()
        }
        try:
            save_scenario(
                {
                    "scenario_id": normalized_scenario_id,
                    "scenario_type": "trading_lab",
                    "title": normalized_title,
                    "assets": [*give_ids, *receive_ids],
                    "source_versions": dict(snapshot.registry.source_hashes),
                    "payload": {
                        "selected_sides": selected_sides,
                        "notes": normalized_notes,
                        "team_window": team_window,
                        "unresolved_pick_context_visible": 0,
                    },
                },
                asset_registry=asset_registry,
                root=self.workspace_root,
            )
        except (OSError, WorkspaceValidationError) as exc:
            raise FacadeError(
                "TRADE_SAVE_FAILED",
                "The trade could not be saved to the Personal Workspace.",
                status=409,
            ) from exc
        return FacadePayload(
            data={
                "scenarioId": normalized_scenario_id,
                "workspace": self._trade_workspace(),
            }
        )

    def export_dynasty_trade(
        self,
        *,
        title: str,
        give: Sequence[str],
        receive: Sequence[str],
        team_window: str,
        notes: str,
    ) -> FacadePayload:
        """Build the existing governed, descriptive Markdown trade brief."""

        self._require_mode("dynasty")
        snapshot, give_ids, receive_ids, _lookup, _key_for_id = self._trade_context(
            give=give,
            receive=receive,
            team_window=team_window,
        )
        normalized_title = self._trade_title(title)
        normalized_notes = self._trade_notes(notes)
        try:
            brief = build_trade_brief(
                {
                    "title": normalized_title,
                    "created_at_utc": datetime.now(UTC).isoformat(timespec="seconds"),
                    "side_a": give_ids,
                    "side_b": receive_ids,
                    "team_window": team_window,
                    "rationale": normalized_notes,
                },
                assets=snapshot.evidence.by_id,
            )
        except TradeBriefValidationError as exc:
            raise FacadeError(
                "TRADE_EXPORT_BLOCKED",
                "The descriptive brief could not be built. Remove automatic recommendation "
                "language from the title or notes and retry.",
                status=409,
            ) from exc
        return FacadePayload(
            data={
                "fileName": "nwr-trade-brief.md",
                "markdown": brief.markdown,
                "missingData": list(brief.missing_data),
            }
        )

    def _trade_workspace(self) -> dict[str, Any]:
        snapshot = self._owner_snapshot()
        try:
            store = load_store("saved_scenarios", root=self.workspace_root)
        except (OSError, WorkspaceValidationError):
            return {
                "storeStatus": "blocked",
                "updatedAtUtc": "",
                "message": (
                    "Saved trades are unavailable until the Personal Workspace is recovered."
                ),
                "scenarios": [],
            }
        if store.status == "CORRUPT":
            return {
                "storeStatus": "blocked",
                "updatedAtUtc": store.updated_at_utc,
                "message": (
                    "Saved trades are unavailable until the Personal Workspace is recovered."
                ),
                "scenarios": [],
            }
        current_versions = dict(snapshot.registry.source_hashes)
        scenarios: list[dict[str, Any]] = []
        for row in store.records:
            if row.get("scenario_type") != "trading_lab":
                continue
            payload = row.get("payload")
            selected_sides = payload.get("selected_sides") if isinstance(payload, Mapping) else None
            if not isinstance(selected_sides, list):
                continue
            give_ids: list[str] = []
            receive_ids: list[str] = []
            seen: set[str] = set()
            valid = True
            for item in selected_sides:
                if not isinstance(item, Mapping):
                    valid = False
                    break
                asset_id = str(item.get("asset_id", "")).strip()
                side = str(item.get("side", "")).strip()
                if not asset_id or asset_id in seen or asset_id not in snapshot.evidence.by_id:
                    valid = False
                    break
                if side in {"You give", "NWR gives"}:
                    give_ids.append(asset_id)
                elif side in {"You receive", "NWR receives", "NWR gets"}:
                    receive_ids.append(asset_id)
                else:
                    valid = False
                    break
                seen.add(asset_id)
            team_window = (
                str(payload.get("team_window", ""))
                if isinstance(payload, Mapping)
                else ""
            )
            notes = payload.get("notes", "") if isinstance(payload, Mapping) else ""
            scenario_key = str(row.get("scenario_id", "")).strip()
            if (
                not valid
                or not give_ids
                or not receive_ids
                or team_window not in TEAM_WINDOWS
                or not isinstance(notes, str)
                or not scenario_key
            ):
                continue
            scenarios.append(
                {
                    "scenarioId": scenario_key,
                    "title": str(row.get("title") or "Saved Trading Lab scenario"),
                    "give": give_ids,
                    "receive": receive_ids,
                    "teamWindow": team_window,
                    "notes": notes,
                    "createdAtUtc": str(row.get("created_at_utc", "")),
                    "updatedAtUtc": str(row.get("modified_at_utc", "")),
                    "sourceStatus": scenario_source_status(row, current_versions),
                }
            )
        scenarios.sort(
            key=lambda row: (
                str(row["updatedAtUtc"]),
                str(row["createdAtUtc"]),
                str(row["scenarioId"]),
            ),
            reverse=True,
        )
        return {
            "storeStatus": "loaded" if store.status == "LOADED" else "empty",
            "updatedAtUtc": store.updated_at_utc,
            "message": store.message if scenarios else "No saved trades yet.",
            "scenarios": scenarios,
        }

    def _trade_context(
        self,
        *,
        give: Sequence[str],
        receive: Sequence[str],
        team_window: str,
    ) -> tuple[
        _OwnerSnapshot,
        list[str],
        list[str],
        dict[str, dict[str, Any]],
        dict[str, str],
    ]:
        give_ids = [self._asset_id(value) for value in give]
        receive_ids = [self._asset_id(value) for value in receive]
        if not give_ids or not receive_ids:
            raise FacadeError("INVALID_TRADE_SIDES", "Both trade sides require at least one asset.")
        if len(give_ids) + len(receive_ids) > 12:
            raise FacadeError("TRADE_TOO_LARGE", "A trade may contain at most twelve assets.")
        if len(set((*give_ids, *receive_ids))) != len(give_ids) + len(receive_ids):
            raise FacadeError(
                "DUPLICATE_TRADE_ASSET", "Trade assets must be unique across both sides."
            )
        if team_window not in TEAM_WINDOWS:
            raise FacadeError("INVALID_TEAM_WINDOW", "Unsupported team window.")
        snapshot = self._owner_snapshot()
        lookup = build_registry_trade_item_lookup(snapshot.evidence.rows)
        key_for_id = {str(row.get("asset_id")): key for key, row in lookup.items()}
        missing = [value for value in (*give_ids, *receive_ids) if value not in key_for_id]
        if missing:
            raise FacadeError(
                "TRADE_ASSET_NOT_FOUND",
                "One or more requested trade assets were not found.",
                status=404,
            )
        return snapshot, give_ids, receive_ids, lookup, key_for_id

    @staticmethod
    def _scenario_id(value: object) -> str:
        normalized = str(value or "").strip()
        if (
            not normalized
            or len(normalized) > 180
            or not all(character.isalnum() or character in "._:-" for character in normalized)
        ):
            raise FacadeError("INVALID_TRADE_SCENARIO_ID", "The saved trade ID is invalid.")
        return normalized

    @staticmethod
    def _trade_title(value: object) -> str:
        if not isinstance(value, str):
            raise FacadeError("INVALID_TRADE_TITLE", "The trade title must be text.")
        normalized = value.strip()
        if not normalized:
            raise FacadeError("INVALID_TRADE_TITLE", "The trade title is required.")
        if len(normalized) > TRADE_TITLE_LIMIT:
            raise FacadeError(
                "TRADE_TITLE_TOO_LONG",
                f"The trade title cannot exceed {TRADE_TITLE_LIMIT} characters.",
            )
        return normalized

    @staticmethod
    def _trade_notes(value: object) -> str:
        if not isinstance(value, str):
            raise FacadeError("INVALID_TRADE_NOTES", "Trade notes must be text.")
        if len(value) > TRADE_NOTES_LIMIT:
            raise FacadeError(
                "TRADE_NOTES_TOO_LONG",
                f"Trade notes cannot exceed {TRADE_NOTES_LIMIT} characters.",
            )
        return value

    def _ensure_redraft_projection_seed(self) -> tuple[bool, tuple[str, ...]]:
        """Install the accepted bundled 2026 snapshot once, never over existing state."""

        target = projection_snapshot_path(self.redraft_root, 2026)
        with self._redraft_seed_lock:
            if target.exists():
                if target.is_file():
                    return False, ()
                return False, (
                    "The Redraft projection target exists but is not a readable file; "
                    "the bundled seed was not installed.",
                )
            source = self.repo_root / REDRAFT_SEED_SOURCE_RELATIVE
            approval = self.repo_root / REDRAFT_SEED_APPROVAL_RELATIVE
            if not source.is_file() or not approval.is_file():
                return False, (
                    "The governed bundled Redraft projection seed is unavailable; "
                    "rankings remain blocked.",
                )
            try:
                source_hash = file_sha256(source)
            except OSError:
                source_hash = ""
            if source_hash != REDRAFT_SEED_SHA256:
                return False, (
                    "The governed bundled Redraft projection seed failed its integrity contract; "
                    "rankings remain blocked.",
                )
            try:
                snapshot = install_projection_snapshot(
                    self.redraft_root,
                    2026,
                    source,
                    approval,
                )
            except (OSError, RedraftPersistenceError, RedraftValidationError):
                return False, (
                    "The governed bundled Redraft projection seed failed validation; "
                    "rankings remain blocked.",
                )
            if snapshot.errors or snapshot.source_sha256 != REDRAFT_SEED_SHA256:
                return False, (
                    "The governed bundled Redraft projection seed failed its integrity contract; "
                    "rankings remain blocked.",
                )
            return True, ()

    def _bundled_redraft_blocked_rows(self) -> tuple[dict[str, str], ...]:
        path = self.repo_root / REDRAFT_SEED_BLOCKED_RELATIVE
        try:
            frame = pd.read_csv(path, dtype=str, keep_default_na=False)
        except (OSError, pd.errors.ParserError):
            return ()
        required = {
            "draft_name",
            "draft_position",
            "current_position",
            "projection_status",
            "block_reason",
        }
        if not required.issubset(frame.columns):
            return ()
        blocked = frame.loc[frame["projection_status"].eq("BLOCKED")]
        return tuple(
            {
                "player": _text(row.get("draft_name")),
                "draftPosition": _text(row.get("draft_position")),
                "currentPosition": _text(row.get("current_position")),
                "reason": _text(row.get("block_reason")),
            }
            for row in blocked.to_dict("records")
        )

    def _using_bundled_redraft_seed(self) -> bool:
        target = projection_snapshot_path(self.redraft_root, 2026)
        try:
            return target.is_file() and file_sha256(target) == REDRAFT_SEED_SHA256
        except OSError:
            return False

    def redraft_bootstrap(self) -> FacadePayload:
        self._require_mode("redraft")
        presets = builtin_presets()
        seed_installed, seed_warnings = self._ensure_redraft_projection_seed()
        warnings: list[str] = list(seed_warnings)
        try:
            profiles = list_profiles(self.redraft_root, include_archived=False)
            raw_selected_id = active_profile_id(self.redraft_root)
            selected = active_profile(self.redraft_root)
        except OSError as exc:
            raise FacadeError(
                "REDRAFT_STORE_UNAVAILABLE",
                "The Redraft profile store is unavailable.",
                status=503,
            ) from exc
        selected_id = selected.profile_id if selected is not None else None
        if raw_selected_id and selected is None:
            warnings.append("The saved active Redraft profile is invalid and was ignored.")
        if profile_store_errors(self.redraft_root):
            warnings.append("One or more saved Redraft profiles are invalid and were ignored.")

        rankings: list[dict[str, Any]] = []
        replacement_levels: list[dict[str, Any]] = []
        draft_board: dict[str, Any] | None = None
        snapshot = None
        ranking = None
        if selected is not None:
            try:
                snapshot = load_projection_snapshot(
                    projection_snapshot_path(self.redraft_root, selected.season),
                    season=selected.season,
                    require_manifest=True,
                )
                ranking = generate_rankings(selected, snapshot)
            except (OSError, RedraftPersistenceError, RedraftValidationError):
                snapshot = None
                ranking = None
                warnings.append(
                    "The active Redraft projection snapshot is unavailable; "
                    "rankings remain blocked."
                )
            if ranking is not None:
                try:
                    draft_board = load_draft_board(self.redraft_root, selected.profile_id)
                except (OSError, RedraftPersistenceError, RedraftValidationError):
                    warnings.append("The active Redraft draft board is unavailable.")
                rankings = self._redraft_ranking_payloads(ranking, draft_board)
                replacement_levels = [
                    {
                        "position": value.position,
                        "starterCount": value.starter_count,
                        "rosteredCount": value.rostered_count,
                        "starterCutoffPoints": value.starter_cutoff_points,
                        "replacementPoints": value.replacement_points,
                    }
                    for value in ranking.replacement_levels
                ]

        using_bundled_seed = self._using_bundled_redraft_seed()
        blocked_seed_rows = self._bundled_redraft_blocked_rows() if using_bundled_seed else ()
        if using_bundled_seed and not blocked_seed_rows:
            warnings.append(
                "The bundled Redraft blocked-rookie receipt is unavailable; "
                "rankings remain governed by the admitted snapshot."
            )
        elif blocked_seed_rows:
            warnings.append(
                f"{len(blocked_seed_rows)} position-conflict rookies remain blocked "
                "and excluded from rankings."
            )
        health = build_health_report(selected, snapshot, ranking)
        normalized_warnings = tuple(dict.fromkeys(warnings))
        status_errors = list(ranking.errors) if ranking is not None else []
        ready = health.status.startswith("READY") and not status_errors
        tone = (
            "ready"
            if health.status == "READY_REVIEW_ONLY" and not blocked_seed_rows
            else "review"
            if ready
            else "blocked"
        )
        source_as_of = _text(getattr(snapshot, "source_as_of", ""))
        if ready:
            summary = "Profile-adjusted Redraft rankings are ready."
        elif status_errors:
            summary = status_errors[0]
        elif health.messages:
            summary = health.messages[0]
        else:
            summary = "Redraft evidence requires review."
        notices = [
            {
                "tone": "ready",
                "title": "Redraft is isolated from Dynasty",
                "message": ("League profiles and draft state never change Dynasty authority."),
            },
            {
                "tone": "review",
                "title": "Current-season evidence only",
                "message": ("Redraft rankings require governed projections for the active season."),
            },
            {
                "tone": "review",
                "title": "Role-change context is not yet modeled",
                "message": (
                    "This projection snapshot uses prior-season production plus current "
                    "identity/status. It does not infer target or touch shares from offseason "
                    "competition, depth-chart labels, or injury news."
                ),
            },
        ]
        if selected is not None:
            import_receipt = self.redraft_root / "sleeper_imports" / f"{selected.profile_id}.json"
            try:
                receipt = json.loads(import_receipt.read_text(encoding="utf-8")) if import_receipt.is_file() else {}
            except (OSError, ValueError):
                receipt = {}
                warnings.append("The Sleeper import receipt could not be read; no Sleeper state was changed.")
            unsupported = receipt.get("unsupported_scoring") if isinstance(receipt, dict) else None
            if isinstance(unsupported, list) and unsupported:
                notices.append(
                    {
                        "tone": "review",
                        "title": "Sleeper scoring needs review",
                        "message": "Unsupported non-zero Sleeper fields are explicit: " + ", ".join(str(value) for value in unsupported) + ". NWR did not silently map them to zero.",
                    }
                )
        if using_bundled_seed:
            notices.append(
                {
                    "tone": "ready",
                    "title": (
                        "Bundled projection seed installed"
                        if seed_installed
                        else "Bundled projection seed admitted"
                    ),
                    "message": (
                        "The accepted 608-player 2026 projection snapshot is available locally."
                    ),
                }
            )
        if blocked_seed_rows:
            blocked_names = ", ".join(row["player"] for row in blocked_seed_rows)
            notices.append(
                {
                    "tone": "review",
                    "title": "Two rookies remain blocked",
                    "message": (
                        f"{blocked_names} remain excluded because their draft positions "
                        "conflict with the current factual registry; no values were imputed."
                    ),
                }
            )

        return FacadePayload(
            data={
                "product": dict(REDRAFT_PRODUCT),
                "status": {
                    "ready": ready,
                    "tone": tone,
                    "authority": "Redraft V1 — review authority",
                    "sourceAsOf": source_as_of,
                    "freshness": (
                        "Governed current-season projection snapshot"
                        if source_as_of
                        else "Projection evidence unavailable"
                    ),
                    "summary": summary,
                    "scheduledRefresh": "Off — owner approval required",
                    "errors": status_errors,
                    "warnings": list(normalized_warnings),
                    "sourceHashes": (
                        {"projectionSnapshot": ranking.projection_sha256}
                        if ranking is not None and ranking.projection_sha256
                        else {}
                    ),
                },
                "presets": [self._profile_payload(value) for value in presets],
                "profiles": [self._profile_payload(value) for value in profiles],
                "activeProfileId": selected_id,
                "activeProfile": self._profile_payload(selected) if selected else None,
                "rankings": rankings,
                "replacementLevels": replacement_levels,
                "draftBoard": self._draft_board_payload(draft_board),
                "health": self._redraft_health_payload(
                    health,
                    additional_blocked=len(blocked_seed_rows),
                ),
                "notices": notices,
            },
            warnings=normalized_warnings,
        )

    def create_redraft_profile(self, *, preset_key: str, league_name: str | None) -> FacadePayload:
        self._require_mode("redraft")
        requested = str(preset_key or "").strip()
        template = next(
            (
                profile
                for profile in builtin_presets()
                if requested in {profile.preset_key, profile.profile_id}
            ),
            None,
        )
        if template is None:
            raise FacadeError(
                "REDRAFT_PRESET_NOT_FOUND", "The requested Redraft preset was not found."
            )
        try:
            profile = create_profile(
                self.redraft_root,
                template,
                league_name=(str(league_name).strip() if league_name is not None else None),
            )
        except (OSError, RedraftPersistenceError, RedraftValidationError) as exc:
            raise FacadeError(
                "REDRAFT_PROFILE_CREATE_FAILED",
                "The Redraft profile could not be created.",
                status=409,
            ) from exc
        return FacadePayload(data={"profile": self._profile_payload(profile)})

    def import_sleeper_redraft_profile(
        self, *, league_id: str, username: str
    ) -> FacadePayload:
        """Explicit, read-only Sleeper import into the isolated Redraft store."""

        self._require_mode("redraft")
        try:
            imported = import_sleeper_redraft_profile(
                league_id=league_id,
                username=username,
                redraft_root=self.redraft_root,
            )
            set_active_profile(self.redraft_root, imported.profile.profile_id)
        except (OSError, SleeperRedraftImportError, RedraftPersistenceError, RedraftValidationError) as exc:
            raise FacadeError(
                "SLEEPER_REDRAFT_IMPORT_FAILED",
                "Sleeper league import could not be completed. No profile was activated.",
                status=409,
            ) from exc
        return FacadePayload(
            data={
                "profile": self._profile_payload(imported.profile),
                "unsupportedScoring": list(imported.unsupported_scoring),
            }
        )

    def activate_redraft_profile(self, profile_id: str) -> FacadePayload:
        self._require_mode("redraft")
        normalized = self._profile_id(profile_id)
        try:
            profile = set_active_profile(self.redraft_root, normalized)
        except (OSError, RedraftPersistenceError, RedraftValidationError) as exc:
            raise FacadeError(
                "REDRAFT_PROFILE_ACTIVATE_FAILED",
                "The Redraft profile could not be activated.",
                status=409,
            ) from exc
        return FacadePayload(data={"profile": self._profile_payload(profile)})

    def duplicate_redraft_profile(
        self,
        profile_id: str,
        *,
        league_name: str | None = None,
    ) -> FacadePayload:
        """Duplicate and activate a profile through the existing atomic Redraft store."""

        self._require_mode("redraft")
        normalized = self._profile_id(profile_id)
        normalized_name = str(league_name or "").strip() or None
        if normalized_name is not None and len(normalized_name) > 120:
            raise FacadeError(
                "REDRAFT_PROFILE_NAME_INVALID",
                "League name must be 120 characters or fewer.",
            )
        try:
            profile = duplicate_profile(
                self.redraft_root,
                normalized,
                league_name=normalized_name,
            )
            set_active_profile(self.redraft_root, profile.profile_id)
        except (OSError, RedraftPersistenceError, RedraftValidationError) as exc:
            raise FacadeError(
                "REDRAFT_PROFILE_DUPLICATE_FAILED",
                "The Redraft profile could not be duplicated.",
                status=409,
            ) from exc
        return FacadePayload(data={"profile": self._profile_payload(profile)})

    def update_redraft_profile(
        self,
        profile_id: str,
        *,
        league_name: str,
        team_count: int,
        roster: Mapping[str, int],
        scoring: Mapping[str, float],
        draft: Mapping[str, Any],
    ) -> FacadePayload:
        """Edit a bounded profile subset and delegate validation/persistence to Redraft V1."""

        self._require_mode("redraft")
        normalized = self._profile_id(profile_id)
        normalized_name = str(league_name).strip()
        if not normalized_name or len(normalized_name) > 120:
            raise FacadeError(
                "REDRAFT_PROFILE_NAME_INVALID",
                "League name is required and must be 120 characters or fewer.",
            )
        expected_roster = {
            "qb",
            "rb",
            "wr",
            "te",
            "flex",
            "superflex",
            "k",
            "dst",
            "benchSize",
        }
        expected_scoring = {"reception", "passingTd", "interception", "tePremium"}
        expected_draft = {"rounds", "draftSlot", "replacementMethod"}
        if set(roster) != expected_roster:
            raise FacadeError(
                "REDRAFT_PROFILE_ROSTER_INVALID",
                "Roster settings are incomplete or contain unsupported fields.",
            )
        if set(scoring) != expected_scoring:
            raise FacadeError(
                "REDRAFT_PROFILE_SCORING_INVALID",
                "Scoring settings are incomplete or contain unsupported fields.",
            )
        if set(draft) != expected_draft:
            raise FacadeError(
                "REDRAFT_PROFILE_DRAFT_INVALID",
                "Draft settings are incomplete or contain unsupported fields.",
            )
        if isinstance(team_count, bool) or not isinstance(team_count, int):
            raise FacadeError(
                "REDRAFT_PROFILE_TEAM_COUNT_INVALID",
                "Team count must be an integer.",
            )
        if any(type(value) is not int for value in roster.values()):
            raise FacadeError(
                "REDRAFT_PROFILE_ROSTER_INVALID",
                "Roster settings must use integers.",
            )
        if any(type(value) not in {int, float} for value in scoring.values()):
            raise FacadeError(
                "REDRAFT_PROFILE_SCORING_INVALID",
                "Scoring settings must use numbers.",
            )
        if type(draft.get("rounds")) is not int:
            raise FacadeError(
                "REDRAFT_PROFILE_DRAFT_INVALID",
                "Draft rounds must be an integer.",
            )
        draft_slot = draft.get("draftSlot")
        if draft_slot is not None and type(draft_slot) is not int:
            raise FacadeError(
                "REDRAFT_PROFILE_DRAFT_INVALID",
                "Draft slot must be an integer or blank.",
            )
        if not isinstance(draft.get("replacementMethod"), str):
            raise FacadeError(
                "REDRAFT_PROFILE_DRAFT_INVALID",
                "Replacement method must be a supported option.",
            )
        try:
            prior = load_profile(self.redraft_root, normalized)
            roster_values = {
                key: value
                for key, value in roster.items()
                if key != "benchSize"
            }
            roster_values["bench_size"] = roster["benchSize"]
            scoring_values = {
                "reception": scoring["reception"],
                "passing_td": scoring["passingTd"],
                "interception": scoring["interception"],
                "te_premium": scoring["tePremium"],
            }
            draft_values = {
                "rounds": draft["rounds"],
                "draft_slot": draft["draftSlot"],
                "replacement_method": draft["replacementMethod"],
            }
            updated = replace(
                prior,
                league_name=normalized_name,
                team_count=team_count,
                roster=replace(prior.roster, **roster_values),
                scoring=replace(prior.scoring, **scoring_values),
                draft=replace(prior.draft, **draft_values),
            )
            profile = save_profile(self.redraft_root, updated)
        except (
            OSError,
            TypeError,
            ValueError,
            RedraftPersistenceError,
            RedraftValidationError,
        ) as exc:
            raise FacadeError(
                "REDRAFT_PROFILE_EDIT_FAILED",
                "The Redraft profile settings were not valid and were not saved.",
                status=409,
            ) from exc
        return FacadePayload(data={"profile": self._profile_payload(profile)})

    def mark_redraft_player(
        self,
        *,
        profile_id: str,
        player_id: str,
        drafted: bool,
    ) -> FacadePayload:
        self._require_mode("redraft")
        normalized_profile = self._profile_id(profile_id)
        normalized_player = self._player_id(player_id)
        if active_profile_id(self.redraft_root) != normalized_profile:
            raise FacadeError(
                "REDRAFT_PROFILE_NOT_ACTIVE",
                "Draft-board changes require the active Redraft profile.",
                status=409,
            )
        ranking = self._redraft_ranking_for_profile(normalized_profile)
        if normalized_player not in {row.player_id for row in ranking.rows}:
            raise FacadeError(
                "REDRAFT_PLAYER_NOT_RANKED",
                "The requested player is not in the active Redraft ranking.",
                status=404,
            )
        try:
            board = mark_player_drafted(
                self.redraft_root,
                normalized_profile,
                normalized_player,
                drafted=bool(drafted),
            )
        except (OSError, RedraftPersistenceError, RedraftValidationError) as exc:
            raise FacadeError(
                "REDRAFT_DRAFT_MARK_FAILED",
                "The Redraft draft board could not be updated.",
                status=409,
            ) from exc
        return FacadePayload(data={"draftBoard": self._draft_board_payload(board)})

    def undo_redraft_pick(self, *, profile_id: str) -> FacadePayload:
        self._require_mode("redraft")
        normalized = self._profile_id(profile_id)
        if active_profile_id(self.redraft_root) != normalized:
            raise FacadeError(
                "REDRAFT_PROFILE_NOT_ACTIVE",
                "Draft-board changes require the active Redraft profile.",
                status=409,
            )
        try:
            board = undo_last_draft_pick(self.redraft_root, normalized)
        except (OSError, RedraftPersistenceError, RedraftValidationError) as exc:
            raise FacadeError(
                "REDRAFT_DRAFT_UNDO_FAILED",
                "The last Redraft draft-board change could not be undone.",
                status=409,
            ) from exc
        return FacadePayload(data={"draftBoard": self._draft_board_payload(board)})

    def _owner_snapshot(self) -> _OwnerSnapshot:
        key = self._owner_source_fingerprint()
        with self._snapshot_lock:
            if key == self._snapshot_key and self._snapshot_value is not None:
                return self._snapshot_value
            snapshot = self._build_owner_snapshot()
            self._snapshot_key = key
            self._snapshot_value = snapshot
            return snapshot

    def _build_owner_snapshot(self) -> _OwnerSnapshot:
        rankings_source = self._load_rankings_source()
        try:
            registry = load_governed_asset_registry(
                repo_root=self.repo_root,
                current_board_path=rankings_source.source_file,
                expected_current_hash=CURRENT_BOARD_SHA256,
            )
        except (OSError, ValueError, KeyError) as exc:
            raise FacadeError(
                "GOVERNED_ASSET_REGISTRY_UNAVAILABLE",
                "The governed asset registry is unavailable.",
                status=503,
            ) from exc
        if registry.errors:
            raise FacadeError(
                "GOVERNED_ASSET_REGISTRY_UNAVAILABLE",
                "The governed asset registry failed its integrity contract.",
                status=503,
            )
        try:
            research = load_unified_research_preview(
                self.repo_root / RESEARCH_PACKET_RELATIVE
            )
        except (OSError, ValueError, KeyError, pd.errors.ParserError) as exc:
            raise FacadeError(
                "UNIFIED_RESEARCH_UNAVAILABLE",
                "The governed research preview is unavailable.",
                status=503,
            ) from exc
        outcome = load_outcome_v3_display(
            integration_path=self.repo_root / OUTCOME_INTEGRATION_RELATIVE,
            manifest_path=self.repo_root / OUTCOME_MANIFEST_RELATIVE,
        )
        warnings: list[str] = list(rankings_source.warnings)
        if not outcome.loaded:
            warnings.append("Outcome V3 is unavailable; no substitute probabilities are shown.")
        evidence = compose_owner_asset_evidence(
            registry.rows,
            dynasty_frame=rankings_source.frame,
            research_frame=research.board,
            outcome_frame=outcome.frame,
            # The canonical sentinel deliberately resolves through the launcher-owned
            # physical refresh root in packaged and repository runtimes.
            market_artifact_dir=DEFAULT_ARTIFACT_DIR,
        )
        if evidence.errors:
            warnings.append("Optional market context is unavailable or incomplete.")
        compare = build_player_compare_universe(registry, evidence_rows=evidence.rows)
        if compare.errors:
            warnings.append(
                "Player Compare is unavailable because its governed universe is incomplete."
            )
        rankings = owner_rankings_frame(evidence.rows)
        if rankings.empty:
            raise FacadeError(
                "DYNASTY_RANKINGS_UNAVAILABLE",
                "The accepted Finished V1 rankings are unavailable; no substitute ranks are shown.",
                status=503,
            )
        try:
            rookies = load_owner_rookie_board(
                self.repo_root / ROOKIE_BOARD_RELATIVE,
                research_packet_dir=self.repo_root / RESEARCH_PACKET_RELATIVE,
                eligibility_rows=registry.rookie_eligibility_rows,
            )
        except (OSError, ValueError, KeyError, pd.errors.ParserError) as exc:
            raise FacadeError(
                "ROOKIE_REVIEW_UNAVAILABLE",
                "The governed Rookie Review is unavailable.",
                status=503,
            ) from exc
        return _OwnerSnapshot(
            rankings=rankings,
            rookies=rookies,
            registry=registry,
            research=research,
            outcome=outcome,
            evidence=evidence,
            compare=compare,
            rank_receipts={
                _text(row.get("player_id")): row
                for row in rankings_source.frame.to_dict("records")
                if _text(row.get("player_id"))
            },
            dynasty_hash=rankings_source.source_hash,
            warnings=tuple(dict.fromkeys(warnings)),
        )

    def _load_rankings_source(self) -> _RankingsSource:
        candidate = self._candidate_rankings_file()
        frozen_candidate = (self.repo_root / FROZEN_DYNASTY_BOARD_RELATIVE).resolve()
        if self.repo_root == SERVICE_REPO_ROOT.resolve() and candidate != frozen_candidate:
            try:
                bundle = load_dynasty_rankings()
            except (OSError, ValueError, KeyError, pd.errors.ParserError) as exc:
                raise FacadeError(
                    "DYNASTY_RANKINGS_UNAVAILABLE",
                    "The accepted Finished V1 rankings are unavailable; "
                    "no substitute ranks are shown.",
                    status=503,
                ) from exc
            if bundle.errors or bundle.frame.empty or bundle.source_path is None:
                raise FacadeError(
                    "DYNASTY_RANKINGS_UNAVAILABLE",
                    "The accepted Finished V1 rankings are unavailable; "
                    "no substitute ranks are shown.",
                    status=503,
                )
            return _RankingsSource(
                frame=bundle.frame,
                source_hash=str(bundle.source_hash or ""),
                warnings=tuple(bundle.warnings),
                source_file=bundle.source_path.resolve(),
            )

        if not candidate.is_file():
            raise FacadeError(
                "DYNASTY_RANKINGS_UNAVAILABLE",
                "The accepted Finished V1 rankings are unavailable; no substitute ranks are shown.",
                status=503,
            )
        try:
            raw = pd.read_csv(candidate, dtype=str).fillna("")
        except (OSError, pd.errors.ParserError) as exc:
            raise FacadeError(
                "DYNASTY_RANKINGS_UNAVAILABLE",
                "The accepted Finished V1 rankings are unavailable; no substitute ranks are shown.",
                status=503,
            ) from exc
        digest = file_sha256(candidate)
        if validate_dynasty_rankings(raw) or digest != EXPECTED_DYNASTY_RANKINGS_HASH:
            raise FacadeError(
                "DYNASTY_RANKINGS_UNAVAILABLE",
                "The accepted Finished V1 rankings failed their integrity contract.",
                status=503,
            )
        return _RankingsSource(
            frame=normalize_dynasty_rankings_frame(raw),
            source_hash=digest,
            warnings=(),
            source_file=candidate.resolve(),
        )

    def _owner_source_fingerprint(self) -> tuple[tuple[str, int, int], ...]:
        rankings = self._candidate_rankings_file()
        files = (
            rankings,
            self.repo_root / ROOKIE_BOARD_RELATIVE,
            self.repo_root / BLOCKED_ROOKIES_RELATIVE,
            self.repo_root / LIVE_IDENTITY_RELATIVE,
            self.repo_root / PICKS_RELATIVE,
            self.repo_root / FUTURE_PICKS_RELATIVE,
            self.repo_root / OUTCOME_INTEGRATION_RELATIVE,
            self.repo_root / OUTCOME_MANIFEST_RELATIVE,
            *(self.repo_root / value for value in RESEARCH_FILES),
        )
        rows: list[tuple[str, int, int]] = []
        for path in files:
            try:
                stat = path.stat()
            except OSError:
                rows.append((path.name, -1, -1))
            else:
                rows.append((path.name, stat.st_size, stat.st_mtime_ns))
        return tuple(rows)

    def _candidate_rankings_file(self) -> Path:
        if self.repo_root == SERVICE_REPO_ROOT.resolve():
            configured = os.environ.get("NWR_DYNASTY_RANKINGS_ROOT", "").strip()
            if configured:
                return Path(configured).expanduser().resolve() / DYNASTY_BOARD_FILE_NAME
        local_candidate = (self.repo_root / CURRENT_BOARD_RELATIVE).resolve()
        if local_candidate.is_file():
            return local_candidate
        return (self.repo_root / FROZEN_DYNASTY_BOARD_RELATIVE).resolve()

    def _redraft_ranking_for_profile(self, profile_id: str):
        try:
            profile = load_profile(self.redraft_root, profile_id)
        except (OSError, RedraftPersistenceError, RedraftValidationError) as exc:
            raise FacadeError(
                "REDRAFT_PROFILE_NOT_FOUND",
                "The requested Redraft profile was not found.",
                status=404,
            ) from exc
        try:
            snapshot = load_projection_snapshot(
                projection_snapshot_path(self.redraft_root, profile.season),
                season=profile.season,
                require_manifest=True,
            )
            ranking = generate_rankings(profile, snapshot)
        except (OSError, RedraftPersistenceError, RedraftValidationError) as exc:
            raise FacadeError(
                "REDRAFT_RANKINGS_UNAVAILABLE",
                "The active Redraft ranking is unavailable.",
                status=409,
            ) from exc
        if ranking.errors:
            raise FacadeError(
                "REDRAFT_RANKINGS_UNAVAILABLE",
                "The active Redraft ranking is unavailable.",
                status=409,
            )
        return ranking

    def _require_mode(self, expected: str) -> None:
        if self.mode != expected:
            raise FacadeError(
                "MODE_ROUTE_UNAVAILABLE",
                "This operation is not available in the active desktop mode.",
                status=404,
            )

    @staticmethod
    def _asset_id(value: object) -> str:
        text = str(value or "").strip()
        if (
            not text
            or len(text) > 180
            or any(character in text for character in ("/", "\\", "\x00"))
        ):
            raise FacadeError("INVALID_ASSET_ID", "The asset ID is invalid.")
        return text

    @staticmethod
    def _profile_id(value: object) -> str:
        text = str(value or "").strip()
        if (
            not text
            or len(text) > 96
            or not all(character.isalnum() or character in "._-" for character in text)
        ):
            raise FacadeError("INVALID_PROFILE_ID", "The Redraft profile ID is invalid.")
        return text

    @staticmethod
    def _player_id(value: object) -> str:
        text = str(value or "").strip()
        if (
            not text
            or len(text) > 128
            or any(character in text for character in ("/", "\\", "\x00"))
        ):
            raise FacadeError("INVALID_PLAYER_ID", "The Redraft player ID is invalid.")
        return text

    @staticmethod
    def _profile_payload(profile: LeagueProfile) -> dict[str, Any]:
        return {
            "profileId": profile.profile_id,
            "leagueName": profile.league_name,
            "season": profile.season,
            "teamCount": profile.team_count,
            "roster": {
                "qb": profile.roster.qb,
                "rb": profile.roster.rb,
                "wr": profile.roster.wr,
                "te": profile.roster.te,
                "flex": profile.roster.flex,
                "superflex": profile.roster.superflex,
                "k": profile.roster.k,
                "dst": profile.roster.dst,
                "benchSize": profile.roster.bench_size,
            },
            "scoring": {
                "passingYards": profile.scoring.passing_yards,
                "passingTd": profile.scoring.passing_td,
                "interception": profile.scoring.interception,
                "rushingYards": profile.scoring.rushing_yards,
                "rushingTd": profile.scoring.rushing_td,
                "receivingYards": profile.scoring.receiving_yards,
                "reception": profile.scoring.reception,
                "receivingTd": profile.scoring.receiving_td,
                "passingFirstDown": profile.scoring.passing_first_down,
                "rushingFirstDown": profile.scoring.rushing_first_down,
                "receivingFirstDown": profile.scoring.receiving_first_down,
                "returnYards": profile.scoring.return_yards,
                "returnTd": profile.scoring.return_td,
                "fumbleLost": profile.scoring.fumble_lost,
                "tePremium": profile.scoring.te_premium,
                "bonuses": dict(profile.scoring.bonuses),
            },
            "draft": {
                "draftType": profile.draft.draft_type,
                "draftSlot": profile.draft.draft_slot,
                "rounds": profile.draft.rounds,
                "keeperCount": profile.draft.keeper_count,
                "auctionBudget": profile.draft.auction_budget,
                "rosterLimits": dict(profile.draft.roster_limits),
                "adpContextEnabled": profile.draft.adp_context_enabled,
                "replacementMethod": profile.draft.replacement_method,
            },
            "presetKey": profile.preset_key,
            "archived": profile.archived,
            "createdAtUtc": profile.created_at_utc,
            "updatedAtUtc": profile.updated_at_utc,
        }

    @staticmethod
    def _workspace_summary(counts: Mapping[str, Any]) -> dict[str, int]:
        return {
            "watchlist": _integer(counts.get("watchlist")) or 0,
            "targets": _integer(counts.get("targets")) or 0,
            "avoid": _integer(counts.get("avoid")) or 0,
            "openDecisions": _integer(counts.get("open_decisions")) or 0,
            "savedScenarios": _integer(counts.get("saved_scenarios")) or 0,
        }

    @staticmethod
    def _dynasty_ranking_payload(source: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "rank": _integer(source.get("Rank")),
            "player": _text(source.get("Player")),
            "position": _text(source.get("Pos")),
            "team": _text(source.get("Team")),
            "age": _number(source.get("Age")),
            "positionRank": _text(source.get("Pos Rank")),
            "tier": _text(source.get("Tier")),
            "nwrScore": _number(source.get("NWR Score")),
            "nwrView": _text(source.get("NWR View")),
            "range": _text(source.get("Range")),
            "marketBand": _text(source.get("Market")),
            "marketRank": _number(source.get("Market Rank")),
            "marketGap": _number(source.get("NWR vs Market")),
            "marketValue": _number(source.get("Market Value")),
            "marketDate": _text(source.get("Market Date")),
            "confidence": _text(source.get("Confidence")),
            "risk": _text(source.get("Risk")),
            "assetId": _text(source.get("asset_id")),
        }

    @staticmethod
    def _rookie_records(frame: pd.DataFrame) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for source in frame.to_dict("records"):
            player_id = str(source.get("player_id") or "").strip()
            asset_id = (
                f"rookie:{player_id}"
                if player_id
                else "blocked-rookie:"
                + "-".join(str(source.get("player_name") or "").lower().replace("'", "").split())
            )
            rows.append(
                {
                    "assetId": asset_id,
                    "rank": _integer(source.get("Rookie Rank")),
                    "playerId": _text(source.get("Live Player ID")) or player_id,
                    "player": _text(source.get("Player")),
                    "position": _text(source.get("Pos")),
                    "team": _text(source.get("NFL Team")),
                    "evidenceBand": _text(source.get("Evidence Band")),
                    "draftRange": _text(source.get("Draft Range Band")),
                    "nflDraftCapital": _text(source.get("NFL Draft Capital")),
                    "boardScore": _number(source.get("Board Score")),
                    "reviewScore": _number(source.get("Review Score")),
                    "authority": _text(source.get("Authority")),
                    "blockedReason": owner_caveat_text(
                        source.get("Blocked / pending reason")
                    ),
                    "warnings": _text(source.get("Warnings")),
                    "confidence": _text(source.get("Confidence")),
                    "age": _number(source.get("Age")),
                    "collegeProduction": _text(source.get("College Production")),
                    "marketShare": _text(source.get("Market Share")),
                    "athleticContext": _text(source.get("Athletic Context")),
                    "researchTier": _text(source.get("Unified Research")),
                    "researchNeighborhood": _text(source.get("Research Neighborhood")),
                    "currentRole": _text(source.get("Current Role")),
                    "whatNwrLikes": _text(source.get("What NWR likes")),
                    "whatHoldsBack": _text(source.get("What holds them back")),
                    "biggestUncertainty": _text(source.get("Biggest uncertainty")),
                    "rankScoreExplanation": _text(
                        source.get("Why rank differs from raw score")
                    ),
                    "floor": _text(source.get("Floor")),
                    "expected": _text(source.get("NWR Expected")),
                    "ceiling": _text(source.get("Ceiling")),
                    "identityStatus": _text(source.get("Identity Status")),
                    "draftEligibility": _text(source.get("Draft Eligibility")),
                    "scoreStatus": _text(source.get("Score Status")),
                    "modelScoreEligible": _flag(source.get("Model Score Eligible")),
                    "searchable": _flag(source.get("Searchable"), default=True),
                    "selectable": _flag(source.get("Selectable"), default=True),
                    "draftable": _flag(source.get("Draftable"), default=True),
                    "refreshAvailable": _flag(source.get("Refresh Available")),
                    "draftRound": _integer(source.get("Draft Round")),
                    "overallPick": _integer(source.get("Overall Pick")),
                    "eligibilityReason": _text(source.get("Eligibility Reason")),
                }
            )
        return rows

    @staticmethod
    def _asset_option(row: Mapping[str, Any]) -> dict[str, Any]:
        asset_type = _text(row.get("asset_type"))
        selectable = _flag(
            row.get("selectable"),
            default=not bool(_text(row.get("selection_block_reason"))),
        )
        if row.get("model_score_eligible") is None:
            score_eligible = bool(
                _number(row.get("nwr_dynasty_score") or row.get("score_value")) is not None
            )
        else:
            score_eligible = _flag(row.get("model_score_eligible"))
        return {
            "assetId": _text(row.get("asset_id")),
            "name": _text(row.get("asset_name")),
            "assetType": asset_type,
            "position": _text(row.get("position")),
            "team": _text(row.get("team")),
            "rank": _integer(row.get("dynasty_rank") or row.get("rank_value")),
            "authority": _text(row.get("authority_status")),
            "blocked": not selectable,
            "selectable": selectable,
            "searchable": _flag(row.get("searchable"), default=True),
            "draftEligible": _flag(row.get("draft_eligible")),
            "modelScoreEligible": score_eligible,
            "evidenceBlocked": asset_type in {"Rookie Review", "Blocked Rookie"}
            and not score_eligible,
            "scoreStatus": _text(row.get("score_status"))
            or ("Score available" if score_eligible else "No common model score"),
            "identityStatus": _text(row.get("identity_status")),
            "playerId": _text(row.get("player_id")),
            "draftRound": _integer(row.get("draft_round")),
            "overallPick": _integer(row.get("overall_pick")),
            "refreshAvailable": _flag(row.get("refresh_available")),
        }

    @staticmethod
    def _rookie_readiness_payload(source: Mapping[str, Any]) -> dict[str, Any]:
        positions = source.get("position_counts")
        return {
            "verdict": _text(source.get("verdict")),
            "ready": _flag(source.get("ready")),
            "officialDrafted": _integer(source.get("official_drafted")) or 0,
            "positionCounts": dict(positions) if isinstance(positions, Mapping) else {},
            "exactIdentity": _integer(source.get("exact_identity")) or 0,
            "scored": _integer(source.get("scored")) or 0,
            "manualReview": _integer(source.get("manual_review")) or 0,
            "unresolved": _integer(source.get("unresolved")) or 0,
            "missingFromRegistry": _integer(source.get("missing_from_registry")) or 0,
            "missingFromDraftablePool": (
                _integer(source.get("missing_from_draftable_pool")) or 0
            ),
            "duplicateAssetIds": _integer(source.get("duplicate_asset_ids")) or 0,
            "refreshAvailable": _integer(source.get("refresh_available")) or 0,
            "reviewAssetIds": _string_list(source.get("review_asset_ids")),
            "missingAssetIds": _string_list(source.get("missing_asset_ids")),
            "surfaceGapAssetIds": _string_list(source.get("surface_gap_asset_ids")),
            "nonselectableAssetIds": _string_list(source.get("nonselectable_asset_ids")),
            "draftableAssetIds": _string_list(source.get("draftable_asset_ids")),
            "missingBySurface": {
                str(key): _string_list(value)
                for key, value in dict(source.get("missing_by_surface") or {}).items()
            },
            "duplicateBySurface": {
                str(key): _string_list(value)
                for key, value in dict(source.get("duplicate_by_surface") or {}).items()
            },
            "validatedSurfaces": _string_list(source.get("validated_surfaces")),
            "alertCode": _text(source.get("alert_code")),
            "alertTitle": _text(source.get("alert_title")),
            "alertMessage": _text(source.get("alert_message")),
        }

    @classmethod
    def _player_detail_payload(
        cls,
        row: Mapping[str, Any],
        *,
        outcomes: Sequence[Mapping[str, Any]],
        rank_receipt: Mapping[str, Any] | None = None,
        total_ranked: int = 0,
    ) -> dict[str, Any]:
        range_contract = owner_range_contract(row)
        market_band, _gap_label = market_decision_label(
            row.get("dynasty_rank") or row.get("rank_value"),
            row.get("market_dp_rank"),
        )
        research_values = {
            "rank": _integer(row.get("research_rank")),
            "tier": (
                translate_research_tier(row.get("research_tier"))
                if _text(row.get("research_tier"))
                else ""
            ),
            "status": _text(row.get("research_status_owner") or row.get("research_status")),
            "confidence": _number(row.get("research_confidence")),
            "outlook3y": _number(row.get("research_outlook_3y")),
            "outlook5y": _number(row.get("research_outlook_5y")),
            "ceilingSignal": _number(row.get("research_ceiling_signal")),
            "downsideSignal": _number(row.get("research_downside_signal")),
        }
        research = {key: value for key, value in research_values.items() if value not in (None, "")}
        draft_round = _integer(row.get("draft_round"))
        overall_pick = _integer(row.get("overall_pick"))
        score_eligible = _flag(
            row.get("model_score_eligible"),
            default=_number(row.get("nwr_dynasty_score") or row.get("score_value")) is not None,
        )
        is_rookie_draft_asset = bool(_text(row.get("official_draft_asset_id")))
        owner_score = (
            _number(row.get("board_score"))
            if is_rookie_draft_asset
            else _number(row.get("nwr_dynasty_score") or row.get("score_value"))
        )
        return {
            "assetId": _text(row.get("asset_id")),
            "name": _text(row.get("asset_name")),
            "assetType": _text(row.get("asset_type")),
            "position": _text(row.get("position")),
            "team": _text(row.get("team")),
            "rank": _integer(row.get("dynasty_rank") or row.get("rank_value")),
            "positionRank": _text(row.get("position_rank")),
            "nwrScore": owner_score,
            "age": _number(row.get("age")),
            "confidence": _text(row.get("confidence")) or "Not enough information",
            "authority": (
                _text(row.get("authority_status"))
                or _text(row.get("source_label"))
                or "Governed context"
            ),
            "range": {
                "floor": _text(range_contract.get("Floor")) or "Not enough information",
                "expected": (_text(range_contract.get("NWR Expected")) or "Not enough information"),
                "ceiling": _text(range_contract.get("Ceiling")) or "Not enough information",
                "method": _text(range_contract.get("Method")),
                "authority": _text(range_contract.get("Authority")),
            },
            "market": {
                "band": market_band,
                "gap": market_rank_gap(
                    row.get("dynasty_rank") or row.get("rank_value"),
                    row.get("market_dp_rank"),
                ),
                "rank": _number(row.get("market_dp_rank")),
                "value": _number(row.get("market_dp_value")),
                "sourceAsOf": _text(row.get("market_evidence_date")),
                "status": _text(row.get("market_status")) or "Market data unavailable",
            },
            "risk": owner_risk(row),
            "reasons": cls._asset_reasons(
                row,
                rank_receipt=rank_receipt,
                total_ranked=total_ranked,
            ),
            "outcomes": [dict(value) for value in outcomes],
            "research": research,
            "caveats": _string_list(row.get("owner_caveats")),
            "playerId": _text(row.get("player_id")),
            "identityStatus": _text(row.get("identity_status")),
            "officialDraftAssetId": _text(row.get("official_draft_asset_id")),
            "nflDraftCapital": (
                f"NFL Round {draft_round} · Pick {overall_pick}"
                if draft_round is not None and overall_pick is not None
                else ""
            ),
            "draftRound": draft_round,
            "overallPick": overall_pick,
            "draftEligibility": (
                "Draft eligible" if _flag(row.get("draft_eligible")) else "Not applicable"
            ),
            "modelScoreEligible": score_eligible,
            "scoreStatus": _text(row.get("score_status"))
            or ("Score available" if score_eligible else "No common model score"),
            "selectable": _flag(row.get("selectable"), default=True),
            "refreshAvailable": _flag(row.get("refresh_available")),
            "rookieIntelligence": ({
                "nwrRookieScore": _number(row.get("board_score")),
                "reviewScore": _number(row.get("review_score")),
                "rawModelScore": _number(row.get("raw_model_score")),
                "collegeProduction": _component_owner_context(
                    row.get("production_component")
                ),
                "marketShare": _component_owner_context(
                    row.get("market_share_component")
                ),
                "athleticContext": _athletic_owner_context(
                    row.get("athletic_component")
                ),
                "currentRole": _current_role_owner_context(row),
                "whatNwrLikes": _rookie_likes(row),
                "whatHoldsBack": _rookie_holds_back(row),
                "biggestUncertainty": _rookie_uncertainty(row),
                "rankScoreExplanation": _rookie_rank_score_explanation(row),
            } if _text(row.get("official_draft_asset_id")) else None),
        }

    @staticmethod
    def _asset_reasons(
        row: Mapping[str, Any],
        *,
        rank_receipt: Mapping[str, Any] | None = None,
        total_ranked: int = 0,
    ) -> list[str]:
        if rank_receipt:
            receipt = dict(rank_receipt)
            summary, _evidence, _caveat = owner_rank_explanation(
                receipt,
                total_ranked=max(total_ranked, 1),
            )
            useful_bullets = [
                bullet
                for bullet in owner_rank_reason_bullets(receipt, limit=24)
                if bullet.startswith(
                    (
                        "Helps:",
                        "Holds them back:",
                        "The admitted adjustment",
                        "Gate context:",
                        "Watch-out:",
                    )
                )
                and "raw value is not carried" not in bullet
            ]
            return list(dict.fromkeys([summary, *useful_bullets]))[:5]

        asset_type = _text(row.get("asset_type"))
        if asset_type == "Blocked Rookie":
            blocked_reason = _text(row.get("owner_reason")) or owner_caveat_text(
                row.get("blocking_reason")
            )
            return [
                "Draft eligible and selectable using the governed official draft asset.",
                f"No admitted Rookie Review score: {blocked_reason}",
                "Current factual identity and draft capital do not create a replacement rank.",
            ]

        if asset_type == "Rookie Review":
            reasons: list[str] = []
            rank = _integer(row.get("rank_value"))
            score = _number(row.get("score_value"))
            if rank is not None:
                score_copy = f" with a review score of {score:.2f}" if score is not None else ""
                reasons.append(f"Separate 2026 Rookie Review: #{rank}{score_copy}.")
            if tier := _text(row.get("tier")):
                reasons.append("Evidence band: " + _rookie_evidence_band_label(tier) + ".")
            confidence = _text(row.get("confidence"))
            if confidence == "usable_with_confidence_cap":
                reasons.append("Usable for review, with confidence capped by evidence gaps.")
            elif confidence == "capped_review_required":
                reasons.append("Review required: governed evidence gaps cap confidence.")
            return reasons

        reasons: list[str] = []
        rank = _integer(row.get("dynasty_rank") or row.get("rank_value"))
        if rank is not None:
            reasons.append(f"{_text(row.get('rank_label')) or 'Governed rank'}: #{rank}.")
        if position_rank := _text(row.get("position_rank")):
            reasons.append(f"Position rank: {position_rank}.")
        source = _text(row.get("source_label"))
        authority = _text(row.get("authority_status"))
        if source or authority:
            reasons.append(" · ".join(value for value in (source, authority) if value) + ".")
        if confidence := _text(row.get("confidence")):
            reasons.append(f"Source confidence: {confidence}.")
        return reasons

    @staticmethod
    def _comparison_dimensions(
        row: Mapping[str, Any],
        context: Mapping[str, Any],
    ) -> dict[str, str | float | int | bool | None]:
        return {
            "position": _text(row.get("position")),
            "authority": _text(row.get("compare_authority_status")),
            "boardContext": _text(context.get("Read-only board context")),
            "age": _number(row.get("age")),
            "tierOrBand": _text(context.get("Tier / band")),
            "outcomeSupport": _text(context.get("Outcome support")),
            "stabilityEvidence": _text(context.get("Stability evidence")),
            "ceilingEvidence": _text(context.get("Ceiling evidence")),
            "rosterWindow": _text(context.get("Roster-window context")),
            "reviewFlags": _text(context.get("Main review flags")),
            "draftCapital": (
                f"Round {_integer(row.get('draft_round'))} · "
                f"Pick {_integer(row.get('overall_pick'))}"
                if _integer(row.get("draft_round")) is not None
                and _integer(row.get("overall_pick")) is not None
                else "Not available"
            ),
            "draftEligibility": (
                "Draft eligible" if _flag(row.get("draft_eligible")) else "Not applicable"
            ),
            "scoreStatus": _text(row.get("score_status")) or "No admitted score status",
            "identityStatus": _text(row.get("identity_status")),
        }

    @staticmethod
    def _trade_decision_payload(decision: Any) -> dict[str, Any]:
        source = asdict(decision)
        return {
            "authority": _text(source.get("authority")),
            "recommendation": _text(source.get("recommendation")),
            "preferredSide": _text(source.get("preferred_side")),
            "confidence": _text(source.get("confidence")),
            "teamWindow": _text(source.get("team_window")),
            "summary": _text(source.get("summary")),
            "reasons": _string_list(source.get("reasons")),
            "mainUncertainty": _text(source.get("main_uncertainty")),
            "whatWouldChange": _string_list(source.get("what_would_change")),
            "synthesisTrace": _string_list(source.get("synthesis_trace")),
            "dimensions": [
                {
                    "code": _text(value.get("code")),
                    "label": _text(value.get("label")),
                    "outcome": _text(value.get("outcome")),
                    "confidence": _text(value.get("confidence")),
                    "evidence": _string_list(value.get("evidence")),
                    "explanation": _text(value.get("explanation")),
                }
                for value in source.get("dimensions", [])
            ],
            "counterStatus": "blocked",
            "counterMessage": TRADE_COUNTER_BLOCKED_MESSAGE,
        }

    @staticmethod
    def _redraft_ranking_payloads(
        ranking: Any,
        draft_board: Mapping[str, Any] | None,
    ) -> list[dict[str, Any]]:
        drafted = [str(value) for value in (draft_board or {}).get("drafted", [])]
        pick_number = {player_id: index for index, player_id in enumerate(drafted, start=1)}
        return [
            {
                "overallRank": row.overall_rank,
                "positionRank": row.position_rank,
                "playerId": row.player_id,
                "playerName": row.player_name,
                "position": row.position,
                "team": row.team,
                "projectedPoints": row.projected_points,
                "replacementPoints": row.replacement_points,
                "replacementAdjustedValue": row.replacement_adjusted_value,
                "starterGap": row.starter_gap,
                "confidence": row.confidence,
                "tier": row.tier,
                "sourceAsOf": row.source_as_of,
                "rookie": row.rookie,
                "drafted": row.player_id in pick_number,
                "draftedBy": "",
                "pickNumber": pick_number.get(row.player_id),
            }
            for row in ranking.rows
        ]

    @staticmethod
    def _draft_board_payload(board: Mapping[str, Any] | None) -> dict[str, Any] | None:
        if board is None:
            return None
        output: dict[str, Any] = {
            "schemaVersion": _integer(board.get("schema_version")) or 1,
            "profileId": _text(board.get("profile_id")),
            "drafted": [str(value) for value in board.get("drafted", [])],
        }
        if updated := _text(board.get("updated_at_utc")):
            output["updatedAtUtc"] = updated
        if board.get("recovered_from_backup") is not None:
            output["recoveredFromBackup"] = bool(board.get("recovered_from_backup"))
        return output

    @staticmethod
    def _redraft_health_payload(
        health: Any,
        *,
        additional_blocked: int = 0,
    ) -> dict[str, Any]:
        status = _text(health.status)
        messages = list(health.messages)
        if additional_blocked:
            if status.startswith("READY"):
                noun = "player" if additional_blocked == 1 else "players"
                status = f"Ready · {additional_blocked} blocked {noun} visible"
            messages.append(
                f"{additional_blocked} position-conflict rookies are excluded from rankings."
            )
        elif status.startswith("READY"):
            status = "Ready"
        elif status.startswith("BLOCKED"):
            status = "Blocked · current-season evidence required"
        return {
            "status": status,
            "playerUniverseAvailable": health.player_universe_available,
            "currentSeasonForecastAvailable": health.current_season_forecast_available,
            "scoringProfileValid": health.scoring_profile_valid,
            "replacementCalculationValid": health.replacement_calculation_valid,
            "rankedPlayers": health.ranked_players,
            "blockedPlayers": health.blocked_players + additional_blocked,
            "lastGeneratedTimestamp": health.last_generated_timestamp,
            "messages": messages,
        }


def _text(value: object) -> str:
    text = str(value if value is not None else "").strip()
    return "" if text.casefold() in {"", "nan", "none", "null", "<na>"} else text


def _number(value: object) -> float | None:
    try:
        number = float(str(value).strip())
    except (TypeError, ValueError):
        return None
    return None if pd.isna(number) else number


def _integer(value: object) -> int | None:
    number = _number(value)
    return int(number) if number is not None and number.is_integer() else None


def _flag(value: object, *, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    text = _text(value).casefold()
    if not text:
        return default
    if text in {"1", "true", "yes", "y"}:
        return True
    if text in {"0", "false", "no", "n"}:
        return False
    return default


def _string_list(value: object) -> list[str]:
    if isinstance(value, str):
        text = _text(value)
        return [text] if text else []
    if isinstance(value, Sequence):
        return [text for item in value if (text := _text(item))]
    text = _text(value)
    return [text] if text else []


def _component_owner_context(value: object) -> str:
    number = _number(value)
    return f"{number:.1f} / 100 normalized" if number is not None else "Not enough information"


def _athletic_owner_context(value: object) -> str:
    number = _number(value)
    if number is None:
        return "NOT_ENOUGH_INFORMATION"
    if number >= 70:
        return f"STRONG ({number:.1f}/100 governed component)"
    if number >= 40:
        return f"ADEQUATE ({number:.1f}/100 governed component)"
    return f"CONCERN ({number:.1f}/100 governed component)"


def _current_role_owner_context(row: Mapping[str, Any]) -> str:
    team = _text(row.get("team"))
    frozen_position = _text(row.get("position"))
    current_position = _text(row.get("current_role_position"))
    status = _text(row.get("current_role_status")).upper()
    projection_status = _text(row.get("current_role_projection_status")).lower()
    if current_position and frozen_position and current_position != frozen_position:
        return (
            f"Frozen Rookie Review position {frozen_position}; current registry position "
            f"{current_position} with {team or 'team unavailable'}. Redraft projection status "
            f"is {projection_status or 'under review'} for the role conflict; "
            "dynasty score unchanged."
        )
    if status == "ACT" and team:
        return f"Active on {team}'s current roster; not used in Rookie Review score"
    if status and team:
        return f"{status} with {team}; not used in Rookie Review score"
    if team:
        return f"Current team {team}; depth role not governed"
    return "Not enough information"


def _rookie_component_values(row: Mapping[str, Any]) -> list[tuple[float, str]]:
    fields = (
        ("college production", "production_component"),
        ("market share", "market_share_component"),
        ("NFL draft capital", "draft_capital_component"),
        ("athletic evidence", "athletic_component"),
        ("recruiting", "recruiting_component"),
        ("age", "age_component"),
    )
    values: list[tuple[float, str]] = []
    for label, field in fields:
        number = _number(row.get(field))
        if number is not None:
            values.append((number, label))
    return values


def _rookie_likes(row: Mapping[str, Any]) -> list[str]:
    values = sorted(_rookie_component_values(row), reverse=True)
    if values:
        return [
            f"{label[:1].upper() + label[1:]}: {value:.1f}/100"
            for value, label in values[:3]
        ]
    draft_round = _integer(row.get("draft_round"))
    overall_pick = _integer(row.get("overall_pick"))
    if draft_round is not None and overall_pick is not None:
        return [f"Official NFL selection: Round {draft_round}, pick {overall_pick}"]
    return ["Governed official draft asset is represented and selectable"]


def _rookie_holds_back(row: Mapping[str, Any]) -> list[str]:
    if not _flag(row.get("model_score_eligible")):
        return [
            _text(row.get("owner_reason"))
            or "Required frozen Rookie Review evidence is not admitted"
        ]
    values = _rookie_component_values(row)
    output: list[str] = []
    if values:
        value, label = min(values)
        output.append(f"Lowest available component: {label} {value:.1f}/100")
    missing = _text(row.get("missing_components"))
    if missing:
        output.append("Missing governed components: " + missing.replace("|", ", "))
    return output or ["No separately admitted negative component"]


def _rookie_uncertainty(row: Mapping[str, Any]) -> str:
    if not _flag(row.get("model_score_eligible")):
        missing = _text(row.get("missing_components"))
        suffix = f"; remaining missing components: {missing.replace('|', ', ')}" if missing else ""
        return "Owner approval of the proposed identity contract and governed rebuild" + suffix
    warnings = _text(row.get("warnings"))
    if "missing_combine_evidence" in warnings:
        return "Athletic evidence is absent and is not treated as neutral"
    if "model_edge_weirdness" in warnings:
        return "Model-edge behavior is flagged for owner review"
    if "draft_capital_anchor_warning" in warnings:
        return "Draft-capital anchoring materially limits the evidence-adjusted score"
    return "Missing athletic/recruiting evidence limits confidence"


def _rookie_rank_score_explanation(row: Mapping[str, Any]) -> str:
    if not _flag(row.get("model_score_eligible")):
        return "No rank because the frozen Rookie Review did not admit a score"
    board = _number(row.get("board_score"))
    review = _number(row.get("review_score"))
    if board is None:
        return "Rank score unavailable"
    review_text = f"; broader Review Score {review:.2f}" if review is not None else ""
    explanation = (
        f"Rank uses NWR Rookie Score {board:.2f}{review_text}. "
        "The Board Score already applies the governed format and evidence gates."
    )
    if _flag(row.get("board_score_tied")):
        explanation += (
            " Equal Board Scores use the frozen builder's deterministic secondary key: "
            "player name descending."
        )
    return explanation


def _rookie_evidence_band_label(value: str) -> str:
    return {
        "first_round_board_context_review": "First-round evidence context",
        "second_round_board_context_review": "Second-round evidence context",
        "depth_board_context_review": "Depth-board evidence context",
        "watchlist_context_review": "Watchlist evidence context",
        "watchlist_or_data_incomplete_context_review": (
            "Watchlist or incomplete evidence context"
        ),
        "manual_review": "Manual review",
    }.get(value, "Not enough information")
