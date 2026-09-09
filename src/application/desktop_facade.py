"""Framework-neutral application facade consumed by the local desktop API."""

from __future__ import annotations

import base64
import binascii
import json
import os
import tempfile
import threading
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

import pandas as pd

from src.services.current_kdst_eligibility_service import (
    filter_current_kdst_assets,
    load_nflverse_status_by_name,
)
from src.services.current_player_status_overrides_service import (
    StatusOverrideIntakeError,
    add_verified_status_override,
    apply_status_overrides_to_ranking,
    load_status_overrides,
)
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
from src.services.fantasypros_kdst_consensus_service import (
    FantasyProsConsensusClient,
    FantasyProsProviderError,
    sleeper_free_agent_pool,
    sleeper_opponent_rosters,
    sleeper_streamer_actions,
)
from src.services.fantasypros_kdst_consensus_service import (
    provider_status as fantasypros_provider_status,
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
from src.services.decision_bundle_live_service import (
    LiveDecisionBundleUnavailable,
    build_live_decision_bundle,
)
from src.services.decision_bundle_live_service_v2 import build_live_decision_bundle_v2
from src.services.point_in_time_feature_store_service import provenance_hash
from src.services.metric_status_contract_service import raw_action_value_status
from src.services.score_provenance_service import build_score_provenance
from src.services.shadow_numeric_authorities_service import (
    evaluate_pick_pairs,
    simulate_comparable_leagues,
)
from src.services.nwr_pure_experiment_service import (
    NwrPureExperimentError,
    ReceiptCorrectionRecord,
    append_correction_record,
    build_and_append_owner_decision_receipt,
)
from src.services.owner_mode_view_service import (
    market_decision_label,
    market_rank_gap,
    owner_range_contract,
    owner_rankings_frame,
    owner_risk,
    translate_research_tier,
)
from src.services.owner_test_instrumentation_service import (
    OwnerTestDiagnosticEvent,
    append_owner_test_event,
    build_decision_bundle_diagnostic_event,
    build_draft_state_change_event,
)
from src.services.kha_shadow_replay_reader_service import (
    KhaShadowReplayUnavailable,
    kha_shadow_replay_payload,
    load_kha_shadow_replay_preview,
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
from src.services.redraft_draft_room_v1_service import (
    advance_cpu_to_owner,
    apply_catch_up_paste,
    build_draft_room_payload,
    import_owner_adp_csv,
    load_udk_rankings,
    parse_udk_position_csv,
    parse_udk_position_pdf,
    rollback_udk_position_rankings,
    save_udk_position_pdf_rankings,
    save_udk_position_rankings,
    preview_catch_up_paste,
    preview_owner_paste_adp,
    approve_owner_platform_manual_match,
    clear_owner_platform_manual_match,
    clear_pick,
    draft_order,
    fill_gap_pick,
    ingest_read_only_sleeper_pick,
    load_adp_snapshot,
    load_room_state,
    owner_platform_provider_breakdown,
    owner_platform_snapshot_status,
    owner_pick_and_advance,
    refresh_fantasy_football_calculator_adp,
    replace_pick,
    save_owner_paste_adp,
    set_owner_platform_selection,
    clear_owner_platform_selection,
    set_owner_paste_adp_active,
    start_draft_room,
    sync_read_only_sleeper_picks,
    undo_pick_correction,
    undo_room_pick,
)
from src.services.redraft_external_intelligence_service import load_external_intelligence
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
    reconcile_sleeper_profile_identities,
    redraft_store_root,
    save_profile,
    set_active_profile,
    undo_last_draft_pick,
    utc_now,
)
from src.services.rookie_draft_eligibility_service import (
    LIVE_IDENTITY_RELATIVE,
    load_rookie_draft_eligibility_overlay,
    reconcile_rookie_draft_readiness,
)
from src.services.rookie_owner_experience_service import load_owner_rookie_board
from src.services.rookie_veteran_dynasty_bridge_service import (
    build_rookie_veteran_bridge,
    immediate_production_for_row,
    immediate_production_payload,
    load_redraft_bridge_context,
)
from src.services.sleeper_import_service import SleeperHttpClient
from src.services.sleeper_redraft_owner_service import (
    SleeperRedraftImportError,
    import_sleeper_redraft_profile,
    load_sleeper_draft_picks,
    load_sleeper_import_receipt,
    manual_kdst_assets_from_sleeper_players,
    resync_sleeper_redraft_profile,
)
from src.services.trade_brief_export_service import (
    TradeBriefValidationError,
    build_trade_brief,
)
from src.services.udk_unmodeled_skill_asset_service import (
    UdkKdstSnapshotError,
    UdkUnmodeledSkillAssetError,
    merge_manual_assets,
    parse_udk_kdst_snapshot,
    parse_udk_unmatched_skill_assets,
    write_manual_assets_file,
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
# DecisionBundle speed presets (Owner Test Candidate V1, section 11) --
# real, measured trial/season/candidate-count values, not guesses. See
# docs/codex/DECISION_BUNDLE_LATENCY_BENCHMARK_20260903.md /
# scripts/run_decision_bundle_latency_benchmark_v1.py for the original
# benchmark; re-measured 20260906 (owner-test follow-up) against the real
# isolated install.
#
# FAST's original trials=2/seasons=20 gave only a 20-roster comparable
# population (percentile steps of 5.0) and only 20 Monte Carlo seasons per
# candidate (win-probability steps of 5%) -- confirmed (not guessed) as
# the real cause of live Suggestions candidates collapsing to 0/50/100-
# style Pick Score groups: `team_score()`'s percentile
# (100*below/population_size) and `championship_equity()`'s win_probability
# (wins/seasons) are both frozen, unmodified formulas -- this widens their
# INPUT population/sample size only, the same category of fix as
# raw_action_value_live_service.py's earlier percentile->roster_value fix
# (change what feeds the frozen math, never the math itself).
# Measured real cost of the increase (isolated install, mid-draft state):
# comparable-league population 20->100 (trials 2->10, one-time per unique
# board state, cached) costs ~+1.3s; championship_equity at seasons
# 20->300 costs ~+0.1s for a full 8-candidate FAST slate (that computation
# is cheap regardless of season count). Real end-to-end FAST latency moved
# from ~1.5s to ~3.3s cold / ~1.4s warm (cached) in direct measurement --
# still trivially inside the owner's real 60-second pick clock.
DECISION_BUNDLE_SPEED_PRESETS: dict[str, dict[str, int]] = {
    # `continuationSeeds` (NWR OVERNIGHT -- Team-After saturation): each
    # candidate's full-draft-completion look-ahead re-runs this many times
    # (different continuation seeds), averaging Team Score/win_probability
    # -- see evaluate_pick_candidates' own docstring for why a single fixed
    # seed can make very different candidates converge to a near-identical
    # simulated final roster. 3 measured at ~1.6x FAST's own prior latency
    # in a real practice-profile timing check (docs/codex/
    # NWR_OVERNIGHT_CONTINUATION_SEEDS_LATENCY_20260907.md) -- comfortably
    # inside the owner's 60-second draft clock.
    "FAST": {"trials": 10, "seasons": 300, "maxCandidates": 8, "continuationSeeds": 3},
    "STANDARD": {"trials": 20, "seasons": 100, "maxCandidates": 10, "continuationSeeds": 3},
    "DEEP": {"trials": 50, "seasons": 200, "maxCandidates": 12, "continuationSeeds": 5},
}
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
        # DecisionBundle comparable-league Monte Carlo population cache
        # (section 10, Owner Test Candidate V1): keyed by every piece of
        # provenance that could make a cached population wrong to reuse --
        # profile_id, the real universe/market hashes, and the simulation
        # parameters. Never keyed by draft-board state, since that changes
        # every pick; the comparable-league population itself is independent
        # of the CURRENT roster, only of the universe/market/format it was
        # simulated under.
        self._comparable_leagues_lock = threading.RLock()
        self._comparable_leagues_key: tuple[str, str, str, int, int] | None = None
        self._comparable_leagues_value: list[Any] | None = None

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
                "registry": [_text(row.get("asset_id")) for row in snapshot.registry.rows],
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
                "trade": [_text(row.get("asset_id")) for row in trade_lookup.values()],
                "draftable": [
                    _text(row.get("assetId")) for row in rookie_rows if _flag(row.get("draftable"))
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
        normalized_tags = list(dict.fromkeys(tag.strip() for tag in tags if tag.strip()))
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
            key: _text(row.get("asset_type")) for key, row in snapshot.evidence.by_id.items()
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
                "status": ("ready" if preview is None or preview.valid else "blocked"),
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
        immediate_production = immediate_production_for_row(
            row,
            load_redraft_bridge_context(self.repo_root),
        )
        return FacadePayload(
            data=self._player_detail_payload(
                row,
                outcomes=outcomes,
                rank_receipt=snapshot.rank_receipts.get(player_id),
                total_ranked=len(snapshot.rank_receipts),
                immediate_production=immediate_production_payload(immediate_production),
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
        bridge = build_rookie_veteran_bridge(
            rows,
            redraft_context=load_redraft_bridge_context(self.repo_root),
        )
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
                    "expected": _text(value.get("NWR Expected")) or "Not enough information",
                    "ceiling": _text(value.get("Ceiling")) or "Not enough information",
                    "ageWindow": _text(value.get("Age / window")) or "Age/window unavailable",
                    "risk": _text(value.get("Risk / uncertainty")) or "Not enough information",
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
                "bridge": bridge.as_payload() if bridge is not None else None,
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
        selected_sides.extend(side_row(asset_id, "You receive") for asset_id in receive_ids)
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
                str(payload.get("team_window", "")) if isinstance(payload, Mapping) else ""
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
        redraft_context = load_redraft_bridge_context(self.repo_root)
        evidence_by_id = snapshot.evidence.by_id
        for value in lookup.values():
            asset_id = _text(value.get("asset_id"))
            evidence = evidence_by_id.get(asset_id, {})
            immediate = immediate_production_for_row(evidence, redraft_context)
            value.update(
                {
                    "redraft_available": immediate.available,
                    "redraft_projected_points": immediate.projected_points,
                    "redraft_overall_rank": immediate.overall_rank,
                    "redraft_position_rank": immediate.position_rank,
                    "redraft_vbd": immediate.replacement_adjusted_value,
                    "redraft_confidence": immediate.confidence,
                    "research_outlook_3y": evidence.get("research_outlook_3y", ""),
                    "research_outlook_5y": evidence.get("research_outlook_5y", ""),
                    "research_ceiling_signal": evidence.get("research_ceiling_signal", ""),
                }
            )
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
            reconcile_sleeper_profile_identities(self.redraft_root)
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
        adp_snapshot = None
        manual_assets: list[dict[str, str]] = []
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
                ranking = apply_status_overrides_to_ranking(
                    ranking, load_status_overrides(self.repo_root)
                )
            except (OSError, RedraftPersistenceError, RedraftValidationError):
                snapshot = None
                ranking = None
                warnings.append(
                    "The active Redraft projection snapshot is unavailable; "
                    "rankings remain blocked."
                )
            # NWR LAST PRE-DRAFT BLOCKER CLOSURE (section 1, real gap found
            # while completing this same closure pass): this used to load
            # manual K/DST assets ONLY `if selected.practical_mode` --
            # since K/DST rostering no longer REQUIRES practical_mode at
            # all (see the real fix in redraft_engine_v1_service.py), a
            # league with K/DST slots and real imported manual assets
            # would never actually see them in Suggestions/Draft Board
            # unless practical_mode was ALSO separately enabled, silently
            # reopening the same footgun this pass exists to close. Tied
            # to the real structural condition instead (the roster
            # actually configures K or DST), independent of the flag.
            if selected.roster.k or selected.roster.dst:
                manual_assets = self._manual_assets_for_profile(selected.profile_id)
                if not manual_assets:
                    warnings.append(
                        "This league rosters K and/or DST, but no manual K/DST assets are "
                        "loaded yet. Import a UDK K/DST snapshot from Room Controls."
                    )
            if ranking is not None:
                try:
                    adp_snapshot = load_adp_snapshot(self.redraft_root, selected)
                    room_state = load_room_state(
                        self.redraft_root,
                        selected,
                        ranking,
                        manual_assets,
                    )
                    draft_board = build_draft_room_payload(
                        selected,
                        ranking,
                        manual_assets,
                        adp_snapshot,
                        room_state,
                    )
                    for asset in manual_assets:
                        entry = adp_snapshot.by_player_id.get(str(asset.get("player_id") or ""))
                        asset["overallAdp"] = entry.overall_adp if entry else None  # type: ignore[assignment]
                        asset["expectedPick"] = entry.expected_pick if entry else None  # type: ignore[assignment]
                        asset["expectedRound"] = entry.expected_round if entry else None  # type: ignore[assignment]
                        asset["adpSource"] = adp_snapshot.source if entry else ""
                except (OSError, RedraftPersistenceError, RedraftValidationError):
                    warnings.append("The active Redraft draft board is unavailable.")
                rankings = self._redraft_ranking_payloads(
                    ranking,
                    draft_board,
                    adp_snapshot,
                )
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
        fantasypros_status = fantasypros_provider_status()
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
            {
                "tone": "review" if fantasypros_status.configured else "blocked",
                "title": "External K/DST consensus boundary",
                "message": fantasypros_status.message,
            },
        ]
        if selected is not None:
            import_receipt = self.redraft_root / "sleeper_imports" / f"{selected.profile_id}.json"
            try:
                receipt = (
                    json.loads(import_receipt.read_text(encoding="utf-8"))
                    if import_receipt.is_file()
                    else {}
                )
            except (OSError, ValueError):
                receipt = {}
                warnings.append(
                    "The Sleeper import receipt could not be read; no Sleeper state was changed."
                )
            unsupported = receipt.get("unsupported_scoring") if isinstance(receipt, dict) else None
            if isinstance(unsupported, list) and unsupported:
                notices.append(
                    {
                        "tone": "review",
                        "title": "Sleeper scoring needs review",
                        "message": "Unsupported non-zero Sleeper fields are explicit: "
                        + ", ".join(str(value) for value in unsupported)
                        + ". NWR did not silently map them to zero.",
                    }
                )
            if selected.practical_mode:
                notices.append(
                    {
                        "tone": "review",
                        "title": "PRACTICAL SCORING",
                        "message": (
                            "NWR models the major QB/RB/WR/TE scoring rules for Fantasy "
                            "Gamers. Five uncommon scoring events are not included. Kicker "
                            "and DST are manual/unmodeled."
                        ),
                    }
                )
            # NWR OVERNIGHT (roster-completion correctness, Section 3): a
            # real top-suggestion mock finished with the bench header
            # showing "6/6" but a true bench of 9 -- traced to this exact
            # kind of mismatch (this profile's own starters + bench_size
            # do not equal its configured draft rounds, so the draft asks
            # for more picks than the roster has real slots for). This is
            # disclosed here, non-blocking (an already-running/owner-active
            # profile is never silently rejected or auto-corrected), while
            # the actual bench count display itself is now never clamped
            # to hide the resulting overflow.
            starter_slots = (
                selected.roster.qb + selected.roster.rb + selected.roster.wr
                + selected.roster.te + selected.roster.flex + selected.roster.superflex
                + selected.roster.k + selected.roster.dst
            )
            total_capacity = starter_slots + selected.roster.bench_size
            if selected.draft.rounds != total_capacity:
                notices.append(
                    {
                        "tone": "review",
                        "title": "Draft rounds do not match roster capacity",
                        "message": (
                            f"This profile is configured for {selected.draft.rounds} rounds "
                            f"but {starter_slots} starters + {selected.roster.bench_size} bench "
                            f"= {total_capacity} real roster slots. "
                            + (
                                "A completed draft will roster more players than fit -- the real "
                                "count is shown, never clamped to look correct."
                                if selected.draft.rounds > total_capacity
                                else "Some rounds will draft players with no starter/bench slot to fill."
                            )
                        ),
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
                "ownerPlatformSnapshot": owner_platform_snapshot_status(self.redraft_root, selected),
                "marketProviderAdp": {
                    player_id: {
                        "consensus": values.get("consensus"),
                        "sleeper": values.get("sleeper"),
                        "espn": values.get("espn"),
                        "fantasypros": values.get("fantasypros"),
                    }
                    for player_id, values in owner_platform_provider_breakdown(self.redraft_root).items()
                },
                "manualAssets": [
                    {
                        "playerId": str(asset.get("player_id") or ""),
                        "playerName": str(asset.get("player_name") or ""),
                        "position": str(asset.get("position") or ""),
                        "team": str(asset.get("team") or ""),
                        "authority": str(asset.get("authority") or ""),
                        "overallAdp": asset.get("overallAdp"),
                        "expectedPick": asset.get("expectedPick"),
                        "expectedRound": asset.get("expectedRound"),
                        "adpSource": asset.get("adpSource"),
                    }
                    for asset in manual_assets
                ],
                # NWR class-time hardening, section 18 (real owner-runtime
                # acceptance crash, found via real Chrome rendering): the
                # no-active-profile fallback used `{"positions": {}}` (an
                # object) while `load_udk_rankings` always returns
                # `{"positions": [...]}` (a list) -- the frontend's
                # `buildUdkEntryById` does `for (const position of
                # udkRankings?.positions ?? [])`, and `for...of` over a
                # plain object throws "object is not iterable", crashing
                # the ENTIRE Draft Room on first load whenever no profile
                # is active yet (a real, fresh-install, first-run state).
                # Matches the real, consistent list contract every other
                # caller already relies on.
                "udkRankings": load_udk_rankings(self.redraft_root, selected.profile_id) if selected else {"positions": []},
                "externalConsensus": {
                    "authority": fantasypros_status.authority,
                    "configured": fantasypros_status.configured,
                    "manualFallback": "NOT_ADMITTED",
                    "message": fantasypros_status.message,
                },
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

    def import_sleeper_redraft_profile(self, *, league_id: str, username: str) -> FacadePayload:
        """Explicit, read-only Sleeper import into the isolated Redraft store."""

        self._require_mode("redraft")
        try:
            imported = import_sleeper_redraft_profile(
                league_id=league_id,
                username=username,
                redraft_root=self.redraft_root,
            )
            set_active_profile(self.redraft_root, imported.profile.profile_id)
        except (
            OSError,
            SleeperRedraftImportError,
            RedraftPersistenceError,
            RedraftValidationError,
        ) as exc:
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

    def redraft_sleeper_resync(self, *, profile_id: str) -> FacadePayload:
        """Refresh one stored Sleeper profile and its durable owner roster snapshot."""

        self._require_mode("redraft")
        normalized = self._profile_id(profile_id)
        try:
            imported = resync_sleeper_redraft_profile(
                profile_id=normalized,
                redraft_root=self.redraft_root,
            )
        except (
            OSError,
            SleeperRedraftImportError,
            RedraftPersistenceError,
            RedraftValidationError,
        ) as exc:
            raise FacadeError(
                "SLEEPER_REDRAFT_RESYNC_FAILED",
                "Only a valid Sleeper-imported profile can be refreshed. No Sleeper data was changed.",
                status=409,
            ) from exc
        snapshot = imported.receipt.get("roster_snapshot") or {}
        return FacadePayload(
            data={
                "profile": self._profile_payload(imported.profile),
                "rosterSnapshot": {
                    "syncedAtUtc": snapshot.get("synced_at_utc"),
                    "rosterId": snapshot.get("roster_id"),
                    "playerCount": len(snapshot.get("players") or []),
                    "unresolvedSleeperPlayerIds": list(
                        snapshot.get("unresolved_sleeper_player_ids") or []
                    ),
                },
                "writeBehavior": "NO_SLEEPER_WRITES",
            }
        )

    def start_practical_redraft_mock(self, *, profile_id: str) -> FacadePayload:
        """Owner-authorized local practical mode; never changes a Sleeper league."""

        self._require_mode("redraft")
        normalized = self._profile_id(profile_id)
        if active_profile_id(self.redraft_root) != normalized:
            raise FacadeError(
                "REDRAFT_PROFILE_NOT_ACTIVE",
                "Start Practical Mock from the active Redraft profile.",
                status=409,
            )
        try:
            profile = load_profile(self.redraft_root, normalized)
            receipt_path = self.redraft_root / "sleeper_imports" / f"{normalized}.json"
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            league_id = str(receipt["league"]["league_id"])
            if league_id != "1312983576827920384":
                raise FacadeError(
                    "PRACTICAL_MODE_NOT_AUTHORIZED",
                    "Practical Mock authorization is limited to Fantasy Gamers.",
                    status=409,
                )
            assets = manual_kdst_assets_from_sleeper_players(
                SleeperHttpClient().get_json("players/nfl")
            )
            # RELEASE-BLOCKER FIX: Sleeper's own `active`/`team` fields can be
            # stale (live-confirmed: a real cut kicker still reported
            # active=true, team=<his old team> by Sleeper's public players
            # endpoint). Cross-checked here against NWR's own already-
            # admitted nflverse players snapshot -- the same real, more
            # authoritative identity source, not a re-fetch -- and only
            # excludes a K whose cross-referenced status is unambiguously
            # non-current (cut/released/retired/not-with-team/inactive);
            # never for an injury-adjacent status, never by player name.
            status_by_name = load_nflverse_status_by_name()
            assets, _kdst_eligibility_counts = filter_current_kdst_assets(
                assets, status_by_name
            )
            if not any(item["position"] == "K" for item in assets) or not any(
                item["position"] == "DST" for item in assets
            ):
                raise SleeperRedraftImportError(
                    "Sleeper did not return usable K and DST manual assets."
                )
            manual_path = self.redraft_root / "manual_assets" / f"{normalized}.json"
            manual_path.parent.mkdir(parents=True, exist_ok=True)
            temporary = manual_path.with_suffix(".tmp")
            temporary.write_text(
                json.dumps(
                    {"schema_version": 1, "profile_id": normalized, "assets": list(assets)},
                    indent=2,
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
            temporary.replace(manual_path)
            profile = replace(profile, practical_mode=True)
            save_profile(self.redraft_root, profile)
        except FacadeError:
            raise
        except (
            OSError,
            ValueError,
            KeyError,
            SleeperRedraftImportError,
            RedraftPersistenceError,
            RedraftValidationError,
        ) as exc:
            raise FacadeError(
                "PRACTICAL_MODE_START_FAILED",
                "Practical Mock could not refresh its read-only Sleeper K/DST identities. "
                "No Sleeper state was changed.",
                status=409,
            ) from exc
        return FacadePayload(
            data={"profile": self._profile_payload(profile), "manualAssets": list(assets)}
        )

    def import_udk_unmodeled_skill_assets(self, *, profile_id: str, csv_path: str) -> FacadePayload:
        """Add manual, unranked draftable assets for real skill-position
        players an owner-authorized UDK identity snapshot flags as having
        no NWR universe match (identity_status=UNMATCHED) -- e.g. rookies
        or veterans missing from projections/<season>/current.csv.

        Additive only: never overwrites an existing manual asset (K/DST or
        otherwise), works for any profile/league, and never assigns a
        score, rank, or projection to these players (see
        src/services/udk_unmodeled_skill_asset_service.py).
        """

        self._require_mode("redraft")
        normalized = self._profile_id(profile_id)
        try:
            load_profile(self.redraft_root, normalized)
        except RedraftPersistenceError as exc:
            raise FacadeError("REDRAFT_PROFILE_NOT_FOUND", str(exc), status=404) from exc
        try:
            new_rows = parse_udk_unmatched_skill_assets(csv_path)
        except UdkUnmodeledSkillAssetError as exc:
            raise FacadeError("UDK_SKILL_SNAPSHOT_INVALID", str(exc), status=422) from exc
        existing = self._manual_assets_for_profile(normalized)
        merged = merge_manual_assets(existing, new_rows)
        manual_path = self.redraft_root / "manual_assets" / f"{normalized}.json"
        try:
            write_manual_assets_file(manual_path, profile_id=normalized, assets=merged)
        except OSError as exc:
            raise FacadeError(
                "UDK_SKILL_ASSET_WRITE_FAILED",
                "Could not save the unmodeled skill player assets.",
                status=409,
            ) from exc
        return FacadePayload(
            data={
                "profileId": normalized,
                "manualAssets": merged,
                "addedCount": len(merged) - len(existing),
            }
        )

    def import_udk_kdst_snapshot(self, *, profile_id: str, csv_text: str) -> FacadePayload:
        """NWR LAST PRE-DRAFT BLOCKER CLOSURE (section 2, real release-
        blocker found while building the exact 16-round acceptance mock):
        `parse_udk_kdst_snapshot()` (all 32 real NFL teams' current K/DST,
        an owner-authorized UDK CSV export -- see its own docstring) has
        existed in this codebase but was never reachable from any facade
        method, HTTP route, or GUI control. The ONLY real, live K/DST
        source ever wired anywhere (`start_practical_redraft_mock`) is
        hard-gated to the owner's one real Fantasy Gamers Sleeper league
        -- a manually-configured league (e.g. tonight's real ESPN league)
        had NO real path to a current K/DST pool at all. Wires this real,
        already-existing, already-tested parser (unmodified -- it reads a
        file path, so the browser-uploaded text is staged to a private
        temp file first, exactly the same "additive, never overwrites an
        existing manual asset" contract `import_udk_unmodeled_skill_assets`
        already proved for skill positions) into a normal profile-scoped
        import reachable from any profile/league. Never assigns an NWR
        score to K/DST; positions stay EXTERNAL_UDK_UNMODELED_BY_NWR."""

        self._require_mode("redraft")
        normalized = self._profile_id(profile_id)
        try:
            load_profile(self.redraft_root, normalized)
        except RedraftPersistenceError as exc:
            raise FacadeError("REDRAFT_PROFILE_NOT_FOUND", str(exc), status=404) from exc
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".csv", encoding="utf-8", delete=False
            ) as handle:
                handle.write(csv_text)
                staged_path = Path(handle.name)
            try:
                new_rows = parse_udk_kdst_snapshot(staged_path)
            finally:
                staged_path.unlink(missing_ok=True)
        except UdkKdstSnapshotError as exc:
            raise FacadeError("UDK_KDST_SNAPSHOT_INVALID", str(exc), status=422) from exc
        existing = self._manual_assets_for_profile(normalized)
        merged = merge_manual_assets(existing, new_rows)
        manual_path = self.redraft_root / "manual_assets" / f"{normalized}.json"
        try:
            write_manual_assets_file(manual_path, profile_id=normalized, assets=merged)
        except OSError as exc:
            raise FacadeError(
                "UDK_KDST_ASSET_WRITE_FAILED",
                "Could not save the K/DST manual assets.",
                status=409,
            ) from exc
        return FacadePayload(
            data={
                "profileId": normalized,
                "manualAssets": merged,
                "addedCount": len(merged) - len(existing),
            }
        )

    def list_player_status_overrides(self) -> FacadePayload:
        """NWR class-time autonomous hardening, section 6: the real, live
        status/risk READ path (`load_status_overrides` +
        `apply_status_overrides_to_ranking`) has been wired into both live
        ranking call sites all along -- what was missing was any way to
        SEE the currently-active overrides without opening the committed
        JSON file by hand. A thin, read-only listing, not a control panel.
        """
        overrides = load_status_overrides(self.repo_root)
        return FacadePayload(
            data={
                "overrides": [
                    {
                        "playerId": override.player_id,
                        "playerName": override.player_name,
                        "kind": override.kind,
                        "reason": override.reason,
                        "effectiveDate": override.effective_date,
                        "verifiedAtUtc": override.verified_at_utc,
                        "sources": list(override.sources),
                        "correctedTeam": override.corrected_team,
                    }
                    for override in overrides
                ]
            }
        )

    def submit_player_status_override(
        self,
        *,
        player_id: str,
        player_name: str,
        kind: str,
        reason: str,
        effective_date: str,
        verified_at_utc: str,
        sources: list[str],
        corrected_team: str = "",
    ) -> FacadePayload:
        """NWR class-time autonomous hardening, section 6: the real status/
        risk intake CONTRACT (`add_verified_status_override`,
        current_player_status_overrides_service.py) has existed since the
        post-draft overnight repair, with real validation (kind must be
        one of the three real, disclosed kinds; at least one cited source;
        real ISO dates; no silently-stacked duplicate) -- but was never
        reachable from any facade method, HTTP route, or GUI control. The
        only way to add a new real, verified event was to hand-edit the
        committed JSON file directly, bypassing that validation entirely.
        This wires the existing, already-tested contract as-is: no new
        event kinds invented here (the real taxonomy is SEASON_OUT /
        NOT_WITH_TEAM / TEAM_CORRECTION -- see
        docs/codex/NWR_STATUS_RISK_INTAKE_PATH_V1_20260908.md for why this
        differs from a richer taxonomy that was assumed but never actually
        built). A rejected submission surfaces the real, specific reason
        (`StatusOverrideIntakeError`) rather than a generic failure, so an
        owner-facing caller can show it directly.

        Once written, the override takes effect on the NEXT live ranking
        build automatically (`apply_status_overrides_to_ranking` already
        reads the same committed file at both live call sites) -- this
        method does not need to, and does not, touch the ranking itself.
        """
        self._require_mode("redraft")
        try:
            override = add_verified_status_override(
                self.repo_root,
                player_id=player_id,
                player_name=player_name,
                kind=kind,
                reason=reason,
                effective_date=effective_date,
                verified_at_utc=verified_at_utc,
                sources=tuple(sources),
                corrected_team=corrected_team,
            )
        except StatusOverrideIntakeError as exc:
            raise FacadeError("STATUS_OVERRIDE_REJECTED", str(exc), status=422) from exc
        return FacadePayload(
            data={
                "playerId": override.player_id,
                "playerName": override.player_name,
                "kind": override.kind,
                "reason": override.reason,
                "effectiveDate": override.effective_date,
                "verifiedAtUtc": override.verified_at_utc,
                "sources": list(override.sources),
                "correctedTeam": override.corrected_team,
            }
        )

    def redraft_kdst_streamer(self, *, week: int) -> FacadePayload:
        """Read FantasyPros K/DST ECR and Sleeper availability; never writes either service."""

        self._require_mode("redraft")
        if not isinstance(week, int) or isinstance(week, bool) or not 1 <= week <= 18:
            raise FacadeError(
                "KDST_STREAMER_WEEK_INVALID", "Week must be an integer from 1 through 18."
            )
        selected = active_profile(self.redraft_root)
        if selected is None:
            raise FacadeError(
                "KDST_STREAMER_PROFILE_REQUIRED",
                "Activate a Sleeper-imported Redraft profile first.",
                status=409,
            )
        receipt_path = self.redraft_root / "sleeper_imports" / f"{selected.profile_id}.json"
        try:
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            league = receipt["league"]
            owner = receipt["owner"]
            league_id = str(league["league_id"])
            owner_user_id = str(owner["user_id"])
        except (OSError, ValueError, KeyError, TypeError) as exc:
            raise FacadeError(
                "KDST_STREAMER_SLEEPER_CONTEXT_REQUIRED",
                "The active profile has no valid Sleeper import receipt. Re-import it before "
                "opening the K/DST Streamer.",
                status=409,
            ) from exc
        status = fantasypros_provider_status()
        if not status.configured:
            raise FacadeError("KDST_STREAMER_PROVIDER_UNAVAILABLE", status.message, status=409)
        try:
            sleeper = SleeperHttpClient()
            rosters = sleeper.get_json(f"league/{league_id}/rosters")
            players = sleeper.get_json("players/nfl")
            consensus = FantasyProsConsensusClient()
            positions: dict[str, list[dict[str, Any]]] = {}
            unmatched: dict[str, list[str]] = {}
            for position in ("K", "DST"):
                rows = consensus.consensus_rankings(
                    season=selected.season,
                    position=position,
                    week=week,
                    scoring="PPR",
                )
                actions, unresolved = sleeper_streamer_actions(
                    rows,
                    rosters=rosters,
                    players=players,
                    owner_user_id=owner_user_id,
                )
                positions[position] = list(actions)
                unmatched[position] = list(unresolved)
        except (FantasyProsProviderError, OSError, ValueError) as exc:
            raise FacadeError(
                "KDST_STREAMER_READ_FAILED",
                "K/DST consensus or Sleeper roster data could not be read. No local or "
                "remote state was changed.",
                status=503,
            ) from exc
        return FacadePayload(
            data={
                "authority": status.authority,
                "week": week,
                "leagueId": league_id,
                "positions": positions,
                "unmatchedSleeperPlayerIds": unmatched,
                "writeBehavior": "NO_SLEEPER_WRITES_NO_FANTASYPROS_WRITES",
            }
        )

    def redraft_free_agents(self) -> FacadePayload:
        """Return every currently unrostered Sleeper fantasy player."""

        self._require_mode("redraft")
        selected, league_id, _owner_user_id = self._active_sleeper_context()
        ranking_warning = ""
        try:
            ranking = self._redraft_ranking_for_profile(selected.profile_id)
            ranking_rows = self._redraft_ranking_payloads(ranking, None)
        except FacadeError as exc:
            if exc.code != "REDRAFT_RANKINGS_UNAVAILABLE":
                raise
            ranking_rows = []
            ranking_warning = (
                "NWR rankings are unavailable for this profile; live free agents are shown "
                "as explicitly unranked."
            )
        try:
            sleeper = SleeperHttpClient()
            rosters = sleeper.get_json(f"league/{league_id}/rosters")
            players = sleeper.get_json("players/nfl")
            free_agents = sleeper_free_agent_pool(
                rosters=rosters,
                players=players,
                rankings=ranking_rows,
            )
        except (FantasyProsProviderError, OSError, ValueError) as exc:
            raise FacadeError(
                "REDRAFT_FREE_AGENTS_READ_FAILED",
                "Sleeper roster or player data could not be read. No local or remote state was changed.",
                status=503,
            ) from exc
        return FacadePayload(
            data={
                "leagueId": league_id,
                "freeAgents": list(free_agents),
                "rankingWarning": ranking_warning,
                "writeBehavior": "NO_SLEEPER_WRITES",
            }
        )

    def redraft_opponent_rosters(self) -> FacadePayload:
        """Return every non-owner roster for the active Sleeper league."""

        self._require_mode("redraft")
        _selected, league_id, owner_user_id = self._active_sleeper_context()
        try:
            sleeper = SleeperHttpClient()
            rosters = sleeper.get_json(f"league/{league_id}/rosters")
            users = sleeper.get_json(f"league/{league_id}/users")
            players = sleeper.get_json("players/nfl")
            opponents = sleeper_opponent_rosters(
                rosters=rosters,
                users=users,
                players=players,
                owner_user_id=owner_user_id,
            )
        except (FantasyProsProviderError, OSError, ValueError) as exc:
            raise FacadeError(
                "REDRAFT_OPPONENT_ROSTERS_READ_FAILED",
                "Sleeper opponent rosters could not be read. No local or remote state was changed.",
                status=503,
            ) from exc
        return FacadePayload(
            data={
                "leagueId": league_id,
                "opponents": list(opponents),
                "writeBehavior": "NO_SLEEPER_WRITES",
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
        practical_mode: bool | None = None,
    ) -> FacadePayload:
        """Edit a bounded profile subset and delegate validation/persistence to Redraft V1.

        `practical_mode` (NWR Mock-Draft QA Day, real gap found and fixed):
        omitted/None preserves the profile's existing value unchanged --
        fully backward compatible with every prior caller. Before this fix,
        the ONLY place in this codebase that ever set `practical_mode=True`
        was the Sleeper-import code path; a manually-created or manually-
        edited profile (e.g. an ESPN league, which has no live-sync import)
        had NO way to enable it, so rostering K/DST as real starters on such
        a profile made ranking generation fail with an opaque
        "REDRAFT_RANKINGS_UNAVAILABLE" error that never surfaced the real
        cause (K/DST have zero rows in the ranked universe by design --
        Practical Mode is what tells the replacement-level calculation to
        stop expecting ranked K/DST rows and treat them as manual-only)."""

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
            roster_values = {key: value for key, value in roster.items() if key != "benchSize"}
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
                practical_mode=(
                    prior.practical_mode if practical_mode is None else bool(practical_mode)
                ),
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
        emergency_override: bool = False,
    ) -> FacadePayload:
        """`emergency_override`: the ONLY sanctioned way to proceed with an
        owner pick in NWR PURE experimental mode when writing its
        immutable decision receipt fails. Without it, a receipt-write
        failure blocks the pick entirely -- see section 18's "do not
        silently proceed with an unlogged experimental decision" rule."""
        self._require_mode("redraft")
        normalized_profile = self._profile_id(profile_id)
        normalized_player = self._player_id(player_id)
        if active_profile_id(self.redraft_root) != normalized_profile:
            raise FacadeError(
                "REDRAFT_PROFILE_NOT_ACTIVE",
                "Draft-board changes require the active Redraft profile.",
                status=409,
            )
        profile = load_profile(self.redraft_root, normalized_profile)
        ranking = self._redraft_ranking_for_profile(normalized_profile)
        manual_assets = self._manual_assets_for_profile(normalized_profile)
        manual_ids = {item["player_id"] for item in manual_assets}
        if normalized_player not in {row.player_id for row in ranking.rows} | manual_ids:
            raise FacadeError(
                "REDRAFT_PLAYER_NOT_RANKED",
                "The requested player is not in the active Redraft ranking.",
                status=404,
            )
        receipt_skipped_reason: str | None = None
        try:
            existing = load_draft_board(self.redraft_root, normalized_profile)
            is_owner_pick = drafted and isinstance(existing.get("owner_slot"), int)
            if is_owner_pick and profile.nwr_pure_experimental:
                try:
                    build_and_append_owner_decision_receipt(
                        self.redraft_root,
                        experiment_id=profile.profile_id,
                        profile=profile,
                        ranking=ranking,
                        manual_assets=manual_assets,
                        state_before=existing,
                        selected_player_id=normalized_player,
                    )
                except (NwrPureExperimentError, OSError) as exc:
                    if not emergency_override:
                        raise FacadeError(
                            "NWR_PURE_DECISION_RECEIPT_FAILED",
                            "NWR PURE experimental mode requires an immutable decision "
                            "receipt for every owner pick, and writing it failed. The "
                            "pick was not recorded. Pass an explicit emergency override "
                            "to proceed without logging this decision.",
                            status=409,
                        ) from exc
                    receipt_skipped_reason = str(exc)
            if is_owner_pick:
                board = owner_pick_and_advance(
                    self.redraft_root,
                    profile,
                    ranking,
                    manual_assets,
                    load_adp_snapshot(self.redraft_root, profile),
                    player_id=normalized_player,
                )
                board = build_draft_room_payload(
                    profile,
                    ranking,
                    manual_assets,
                    load_adp_snapshot(self.redraft_root, profile),
                    board,
                )
            else:
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
        payload_data: dict[str, Any] = {"draftBoard": self._draft_board_payload(board)}
        if receipt_skipped_reason is not None:
            payload_data["nwrPureDecisionReceiptSkipped"] = receipt_skipped_reason
        if is_owner_pick:
            self._log_owner_test_event(
                build_draft_state_change_event(
                    profile_id=normalized_profile, timestamp_utc=utc_now(),
                    change_kind="OWNER_PICK", player_id=normalized_player,
                )
            )
        return FacadePayload(data=payload_data)

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
            profile = load_profile(self.redraft_root, normalized)
            ranking = self._redraft_ranking_for_profile(normalized)
            manual_assets = self._manual_assets_for_profile(normalized)
            existing = load_draft_board(self.redraft_root, normalized)
            if isinstance(existing.get("owner_slot"), int):
                state = undo_room_pick(
                    self.redraft_root,
                    profile,
                    ranking,
                    manual_assets,
                )
                board = build_draft_room_payload(
                    profile,
                    ranking,
                    manual_assets,
                    load_adp_snapshot(self.redraft_root, profile),
                    state,
                )
            else:
                board = undo_last_draft_pick(self.redraft_root, normalized)
        except (OSError, RedraftPersistenceError, RedraftValidationError) as exc:
            raise FacadeError(
                "REDRAFT_DRAFT_UNDO_FAILED",
                "The last Redraft draft-board change could not be undone.",
                status=409,
            ) from exc
        return FacadePayload(data={"draftBoard": self._draft_board_payload(board)})

    def _redraft_correction_context(
        self, profile_id: str
    ) -> tuple[LeagueProfile, Any, list[dict[str, str]]]:
        self._require_mode("redraft")
        normalized = self._profile_id(profile_id)
        if active_profile_id(self.redraft_root) != normalized:
            raise FacadeError(
                "REDRAFT_PROFILE_NOT_ACTIVE",
                "Draft-board corrections require the active Redraft profile.",
                status=409,
            )
        profile = load_profile(self.redraft_root, normalized)
        ranking = self._redraft_ranking_for_profile(normalized)
        manual_assets = self._manual_assets_for_profile(normalized)
        existing = load_draft_board(self.redraft_root, normalized)
        if not isinstance(existing.get("owner_slot"), int):
            raise FacadeError(
                "REDRAFT_ROOM_NOT_STARTED",
                "Start the Draft Room before correcting a pick.",
                status=409,
            )
        return profile, ranking, manual_assets

    def _append_nwr_pure_correction_record(
        self,
        *,
        profile: LeagueProfile,
        correction_type: str,
        pick_number: int,
        detail: dict[str, Any],
    ) -> None:
        """Best-effort audit trail: a correction (fixing already-recorded
        state, often to fix a mistake) is never blocked by a failure to
        write this secondary record -- unlike the original decision
        receipt (section 18's own "do not silently proceed with an
        unlogged experimental decision" rule applies to the ORIGINAL
        pick, not to the owner fixing one after the fact). Never mutates
        any existing decisions.jsonl line -- always a new, separate
        corrections.jsonl entry referencing the pick_number."""
        if not profile.nwr_pure_experimental:
            return
        try:
            append_correction_record(
                self.redraft_root,
                ReceiptCorrectionRecord(
                    experiment_id=profile.profile_id,
                    timestamp_utc=datetime.now(UTC).isoformat(timespec="seconds"),
                    original_pick_number=int(pick_number),
                    reason=f"Event-ledger {correction_type} applied by the owner.",
                    correction_type=correction_type,
                    detail=detail,
                ),
            )
        except OSError:
            pass

    def replace_redraft_pick(
        self, *, profile_id: str, pick_number: int, player_id: str
    ) -> FacadePayload:
        """REPLACE PICK: swap the player at an exact historical pick.
        Every other pick's number/round/team is untouched."""
        normalized_player = self._player_id(player_id)
        profile, ranking, manual_assets = self._redraft_correction_context(profile_id)
        try:
            state = replace_pick(
                self.redraft_root,
                profile,
                ranking,
                manual_assets,
                pick_number=int(pick_number),
                player_id=normalized_player,
            )
            adp = load_adp_snapshot(self.redraft_root, profile)
            board = build_draft_room_payload(profile, ranking, manual_assets, adp, state)
        except (OSError, RedraftPersistenceError, RedraftValidationError) as exc:
            raise FacadeError("REDRAFT_REPLACE_PICK_FAILED", str(exc), status=409) from exc
        self._append_nwr_pure_correction_record(
            profile=profile, correction_type="REPLACE_PICK", pick_number=pick_number,
            detail={"new_player_id": normalized_player},
        )
        self._log_owner_test_event(
            build_draft_state_change_event(
                profile_id=profile.profile_id, timestamp_utc=utc_now(),
                change_kind="CORRECTION_REPLACE", pick_number=int(pick_number),
                player_id=normalized_player,
            )
        )
        return FacadePayload(data={"draftBoard": self._draft_board_payload(board)})

    def clear_redraft_pick(self, *, profile_id: str, pick_number: int) -> FacadePayload:
        """CLEAR PICK: mark a pick UNRESOLVED. pick_number/round/team are
        preserved; every later pick is untouched."""
        profile, ranking, manual_assets = self._redraft_correction_context(profile_id)
        try:
            state = clear_pick(
                self.redraft_root, profile, ranking, manual_assets, pick_number=int(pick_number)
            )
            adp = load_adp_snapshot(self.redraft_root, profile)
            board = build_draft_room_payload(profile, ranking, manual_assets, adp, state)
        except (OSError, RedraftPersistenceError, RedraftValidationError) as exc:
            raise FacadeError("REDRAFT_CLEAR_PICK_FAILED", str(exc), status=409) from exc
        self._append_nwr_pure_correction_record(
            profile=profile, correction_type="CLEAR_PICK", pick_number=pick_number, detail={},
        )
        self._log_owner_test_event(
            build_draft_state_change_event(
                profile_id=profile.profile_id, timestamp_utc=utc_now(),
                change_kind="CORRECTION_CLEAR", pick_number=int(pick_number),
            )
        )
        return FacadePayload(data={"draftBoard": self._draft_board_payload(board)})

    def fill_redraft_pick_gap(
        self, *, profile_id: str, pick_number: int, player_id: str
    ) -> FacadePayload:
        """FILL GAP: assign a player to an exact UNRESOLVED pick slot."""
        normalized_player = self._player_id(player_id)
        profile, ranking, manual_assets = self._redraft_correction_context(profile_id)
        try:
            state = fill_gap_pick(
                self.redraft_root,
                profile,
                ranking,
                manual_assets,
                pick_number=int(pick_number),
                player_id=normalized_player,
            )
            adp = load_adp_snapshot(self.redraft_root, profile)
            board = build_draft_room_payload(profile, ranking, manual_assets, adp, state)
        except (OSError, RedraftPersistenceError, RedraftValidationError) as exc:
            raise FacadeError("REDRAFT_FILL_GAP_FAILED", str(exc), status=409) from exc
        self._append_nwr_pure_correction_record(
            profile=profile, correction_type="FILL_GAP", pick_number=pick_number,
            detail={"filled_player_id": normalized_player},
        )
        self._log_owner_test_event(
            build_draft_state_change_event(
                profile_id=profile.profile_id, timestamp_utc=utc_now(),
                change_kind="CORRECTION_FILL_GAP", pick_number=int(pick_number),
                player_id=normalized_player,
            )
        )
        return FacadePayload(data={"draftBoard": self._draft_board_payload(board)})

    def undo_redraft_pick_correction(self, *, profile_id: str) -> FacadePayload:
        """Reverse only the single most recent REPLACE/CLEAR/FILL GAP
        correction -- independent of undo_redraft_pick's separate
        global-LIFO 'undo the latest recorded pick.'"""
        profile, ranking, manual_assets = self._redraft_correction_context(profile_id)
        try:
            state = undo_pick_correction(self.redraft_root, profile, ranking, manual_assets)
            adp = load_adp_snapshot(self.redraft_root, profile)
            board = build_draft_room_payload(profile, ranking, manual_assets, adp, state)
        except (OSError, RedraftPersistenceError, RedraftValidationError) as exc:
            raise FacadeError("REDRAFT_UNDO_CORRECTION_FAILED", str(exc), status=409) from exc
        self._log_owner_test_event(
            build_draft_state_change_event(
                profile_id=profile.profile_id, timestamp_utc=utc_now(),
                change_kind="CORRECTION_UNDO",
            )
        )
        return FacadePayload(data={"draftBoard": self._draft_board_payload(board)})

    def preview_redraft_catch_up(self, *, profile_id: str, paste: str) -> FacadePayload:
        """Section 10: pure preview of a multi-line catch-up paste -- never
        writes. See docs/codex/CATCH_UP_MODE_CONTRACT_20260903.md."""
        profile, ranking, manual_assets = self._redraft_correction_context(profile_id)
        try:
            preview = preview_catch_up_paste(
                self.redraft_root, profile, ranking, manual_assets, paste=str(paste)
            )
        except (OSError, RedraftPersistenceError, RedraftValidationError) as exc:
            raise FacadeError("REDRAFT_CATCH_UP_PREVIEW_FAILED", str(exc), status=409) from exc
        return FacadePayload(data={"catchUpPreview": preview})

    def apply_redraft_catch_up(self, *, profile_id: str, paste: str) -> FacadePayload:
        """Section 10: apply a catch-up paste -- refuses (via
        apply_catch_up_paste) if any line is unresolved, ambiguous, or
        there are more names than open slots. Re-resolves from scratch
        rather than trusting a client-held preview."""
        profile, ranking, manual_assets = self._redraft_correction_context(profile_id)
        try:
            result = apply_catch_up_paste(
                self.redraft_root, profile, ranking, manual_assets, paste=str(paste)
            )
            adp = load_adp_snapshot(self.redraft_root, profile)
            board = build_draft_room_payload(
                profile, ranking, manual_assets, adp, result["state"]
            )
        except (OSError, RedraftPersistenceError, RedraftValidationError) as exc:
            raise FacadeError("REDRAFT_CATCH_UP_APPLY_FAILED", str(exc), status=409) from exc
        self._log_owner_test_event(
            build_draft_state_change_event(
                profile_id=profile.profile_id, timestamp_utc=utc_now(),
                change_kind="CATCH_UP_APPLIED",
            )
        )
        return FacadePayload(
            data={
                "draftBoard": self._draft_board_payload(board),
                "catchUpApplied": result["applied"],
            }
        )

    def redraft_external_intelligence(self, *, profile_id: str) -> FacadePayload:
        """Read-only owner-authorized UDK/FantasyPros/current-alert context,
        already merged offline into a local CSV. Never touches NWR Core,
        ranks, projections, or CPU/live-mode mechanics -- display only. A
        missing/unreadable file returns an explicit unavailable result; it
        never raises and never blocks the Draft Room.

        NWR PURE — EXPERIMENTAL (profile.nwr_pure_experimental): external
        expert opinion must never reach the owner before a pick in this
        mode (section 6 of the Saturday NWR PURE wave) -- returns an
        explicitly hidden result instead of the real one. UDK/FantasyPros
        may still be logged silently for postmortem via a separate,
        not-owner-facing path; this method is the owner-facing one and
        stays hidden."""
        profile, ranking, _ = self._redraft_room_context(profile_id)
        if profile.nwr_pure_experimental:
            return FacadePayload(
                data={
                    "externalIntelligence": {
                        "available": False,
                        "generatedNote": (
                            "EXTERNAL INTEL HIDDEN — NWR PURE EXPERIMENTAL decision policy is "
                            "active. UDK/FantasyPros are logged for postmortem only, never shown "
                            "before a pick."
                        ),
                        "entries": [],
                        "hiddenByExperimentalMode": True,
                    }
                }
            )
        intel = load_external_intelligence(ranking)
        return FacadePayload(data={"externalIntelligence": intel})

    def _log_owner_test_event(self, event: OwnerTestDiagnosticEvent) -> None:
        """Owner Test Candidate V1, section 15: best-effort, local,
        non-sensitive product diagnostics only -- never allowed to block
        or fail a real DecisionBundle call or draft-state mutation, so
        every call site wraps this in a narrow except rather than letting
        a disk/IO problem in the diagnostics log surface as a user-facing
        error for an otherwise-successful action."""
        try:
            append_owner_test_event(self.redraft_root, event)
        except OSError:
            pass

    def redraft_decision_bundle(
        self, *, profile_id: str, speed: str = "FAST", position_filter: str | None = None,
    ) -> FacadePayload:
        """Owner Test Candidate V1, section 2: the real, live DecisionBundle
        for the CURRENT draft state -- backend computes, this method never
        substitutes a placeholder number.

        `speed` (section 11) selects real, benchmarked trial/season/
        candidate-count presets --
        docs/codex/DECISION_BUNDLE_LATENCY_BENCHMARK_20260903.md has the
        real measured latency behind each: FAST (~0.7s cold, ~0.1-0.2s once
        the comparable-league population is cached) is the default and the
        only preset that comfortably clears the owner's 60-second clock
        with margin; STANDARD (~3.8s cold) and DEEP (~9.6s cold) are
        available but not the default for live play. Raises the same
        REDRAFT_RANKINGS_UNAVAILABLE FacadeError every other per-action
        Redraft endpoint already raises when the ranking is blocked/
        unavailable (a systemic block, not a per-pick condition); when the
        ranking IS ready but no roster-legal candidate exists right now
        (e.g. every open position is already at its configured maximum),
        returns a normal 200 payload with `available: false` and a real
        reason instead -- an expected late-draft state, not a system error.

        NWR PURE — EXPERIMENTAL: unaffected. This never reads external
        intelligence (UDK/FantasyPros) at all -- only NWR's own admitted
        ranking and the SHADOW/RESEARCH numeric authorities -- so the real
        Pick Score/Team Score/Championship Equity stay visible under NWR
        PURE exactly as they do outside it."""
        preset = DECISION_BUNDLE_SPEED_PRESETS.get(str(speed).upper())
        if preset is None:
            raise FacadeError(
                "REDRAFT_DECISION_BUNDLE_INVALID_SPEED",
                f"Unknown DecisionBundle speed {speed!r}; expected one of "
                f"{sorted(DECISION_BUNDLE_SPEED_PRESETS)}.",
                status=400,
            )
        trials, seasons, max_candidates = preset["trials"], preset["seasons"], preset["maxCandidates"]
        continuation_seeds = preset.get("continuationSeeds", 1)

        profile, ranking, manual_assets = self._redraft_room_context(profile_id)
        normalized = self._profile_id(profile_id)
        adp = load_adp_snapshot(self.redraft_root, profile)
        room_state = load_room_state(self.redraft_root, profile, ranking, manual_assets)

        base_seed = 20260903
        comparable_leagues_key = (
            normalized, ranking.projection_sha256, adp.source_sha256, trials, base_seed,
        )
        with self._comparable_leagues_lock:
            if comparable_leagues_key == self._comparable_leagues_key:
                comparable_leagues = self._comparable_leagues_value
            else:
                comparable_leagues = simulate_comparable_leagues(
                    profile, ranking, manual_assets, adp, trials=trials, base_seed=base_seed,
                )
                self._comparable_leagues_key = comparable_leagues_key
                self._comparable_leagues_value = comparable_leagues

        roster_state_hash = provenance_hash(
            {"picks": [dict(p) for p in room_state.get("picks", [])]}
        )
        available_player_hash = provenance_hash(
            {"drafted": sorted(str(v) for v in room_state.get("drafted", []))}
        )
        provenance = build_score_provenance(
            league_profile_hash=provenance_hash(asdict(profile)),
            roster_state_hash=roster_state_hash,
            available_player_hash=available_player_hash,
            universe_hash=ranking.projection_sha256,
            projection_model_version=ranking.generated_at_utc,
            market_snapshot_hash=adp.source_sha256,
            feature_set_version="redraft-live-v1",
            team_score_version="team-score-v2",
            championship_equity_version="championship-equity-v2",
            pick_score_version="pick-score-experimental-v1",
            optimizer_version="decision-bundle-live-v1",
            seed=base_seed,
            simulation_count=trials,
            timestamp_utc=ranking.generated_at_utc,
        )

        result = build_live_decision_bundle(
            profile, ranking, manual_assets, adp, room_state,
            comparable_leagues=comparable_leagues, provenance=provenance,
            max_candidates=max_candidates, trials=trials, seasons=seasons, base_seed=base_seed,
            position_filter=position_filter, continuation_seeds=continuation_seeds,
        )
        resolved_speed = str(speed).upper()
        if isinstance(result, LiveDecisionBundleUnavailable):
            self._log_owner_test_event(
                build_decision_bundle_diagnostic_event(
                    profile_id=normalized, timestamp_utc=utc_now(), speed=resolved_speed,
                    bundle_available=False, blocked_reason=result.reason,
                )
            )
            return FacadePayload(
                data={
                    "decisionBundle": {
                        "available": False, "reason": result.reason, "speed": resolved_speed,
                    }
                }
            )
        self._log_owner_test_event(
            build_decision_bundle_diagnostic_event(
                profile_id=normalized, timestamp_utc=utc_now(), speed=resolved_speed,
                bundle_available=True, latency_seconds=result.latency_seconds,
                top_candidate_player_ids=tuple(c.player_id for c in result.candidates[:3]),
                selected_player_id=(result.candidates[0].player_id if result.candidates else None),
                team_score_before=result.current_team_score.percentile,
                championship_equity_before=result.current_championship_equity.win_probability,
            )
        )
        return FacadePayload(
            data={
                "decisionBundle": {
                    "available": True, "speed": resolved_speed,
                    "bestTurnPlan": _best_turn_plan_payload(
                        profile, ranking, manual_assets, adp, room_state,
                        comparable_leagues, result, base_seed,
                    ),
                    **_decision_bundle_payload(
                        result, ranking, manual_assets,
                        profile=profile,
                        current_owner_player_ids=tuple(
                            str(pick["player_id"])
                            for pick in room_state.get("picks", [])
                            if pick.get("team_slot") == room_state.get("owner_slot") and pick.get("player_id")
                        ),
                    ),
                }
            }
        )

    def redraft_decision_bundle_v2(
        self, *, profile_id: str, speed: str = "FAST",
    ) -> FacadePayload:
        """The historically-validated CHALLENGER DecisionBundle (NWR
        Big-Draft Readiness Overnight V1) -- a SEPARATE, explicitly opt-in
        endpoint. Composes Team Score V2 / Championship Equity V2 on top of
        the exact same real live draft state `redraft_decision_bundle()`
        already reads; it never modifies that method or its response, and
        nothing calls this endpoint unless a caller deliberately requests
        it. Degrades gracefully (never raises) for an unsupported
        team_count or a missing frozen-model file -- the underlying V1
        fields are always still returned. Decision Confidence is never
        computed or exposed here (remains NOT_VALIDATED, diagnostic-only,
        out of scope for this endpoint by design)."""
        preset = DECISION_BUNDLE_SPEED_PRESETS.get(str(speed).upper())
        if preset is None:
            raise FacadeError(
                "REDRAFT_DECISION_BUNDLE_INVALID_SPEED",
                f"Unknown DecisionBundle speed {speed!r}; expected one of "
                f"{sorted(DECISION_BUNDLE_SPEED_PRESETS)}.",
                status=400,
            )
        trials = preset["trials"]
        seasons = preset["seasons"]
        max_candidates = preset["maxCandidates"]

        profile, ranking, manual_assets = self._redraft_room_context(profile_id)
        normalized = self._profile_id(profile_id)
        adp = load_adp_snapshot(self.redraft_root, profile)
        room_state = load_room_state(self.redraft_root, profile, ranking, manual_assets)

        base_seed = 20260903
        comparable_leagues_key = (
            normalized, ranking.projection_sha256, adp.source_sha256, trials, base_seed,
        )
        with self._comparable_leagues_lock:
            if comparable_leagues_key == self._comparable_leagues_key:
                comparable_leagues = self._comparable_leagues_value
            else:
                comparable_leagues = simulate_comparable_leagues(
                    profile, ranking, manual_assets, adp, trials=trials, base_seed=base_seed,
                )
                self._comparable_leagues_key = comparable_leagues_key
                self._comparable_leagues_value = comparable_leagues

        roster_state_hash = provenance_hash(
            {"picks": [dict(p) for p in room_state.get("picks", [])]}
        )
        available_player_hash = provenance_hash(
            {"drafted": sorted(str(v) for v in room_state.get("drafted", []))}
        )
        provenance = build_score_provenance(
            league_profile_hash=provenance_hash(asdict(profile)),
            roster_state_hash=roster_state_hash,
            available_player_hash=available_player_hash,
            universe_hash=ranking.projection_sha256,
            projection_model_version=ranking.generated_at_utc,
            market_snapshot_hash=adp.source_sha256,
            feature_set_version="redraft-live-v1",
            team_score_version="team-score-v2-multi-league-20260905",
            championship_equity_version="championship-equity-v2-multi-league-20260906",
            pick_score_version="pick-score-experimental-v1",
            optimizer_version="decision-bundle-live-v2-challenger-v1",
            seed=base_seed,
            simulation_count=trials,
            timestamp_utc=ranking.generated_at_utc,
        )

        # NWR Final Pre-Draft Product Hardening V1, section 9 (original):
        # FAST's RAV budget was 3 candidates x 2 trials ("measured ~6s at 5
        # x 2"). NWR post-draft overnight, phase 2: re-measured live against
        # the real 403 profile after fixing the None-value crash that had
        # been blocking this study -- budget 8 (== max_candidates, full DQ
        # coverage) x 5 trials (DEEP's own trial count) now measures 4.15s
        # wall, not the ~6s the old comment cited even at a smaller budget.
        # The prior FAST budget of 3 left 5 of 8 Suggestions rows with no
        # DQ/RAV at all (a real, owner-reported "DQ is always Skipped"
        # complaint) for a latency saving of under 2 real seconds against a
        # 90-second pick clock -- not a defensible trade. FAST now computes
        # DQ for every candidate it shows.
        rav_preset = {"FAST": (8, 3), "STANDARD": (10, 4), "DEEP": (12, 5)}[str(speed).upper()]
        result = build_live_decision_bundle_v2(
            profile, ranking, manual_assets, adp, room_state,
            comparable_leagues=comparable_leagues, provenance=provenance,
            max_candidates=max_candidates, trials=trials, seasons=seasons, base_seed=base_seed,
            max_rav_candidates=rav_preset[0], rav_trials=rav_preset[1],
        )
        resolved_speed = str(speed).upper()
        if isinstance(result, LiveDecisionBundleUnavailable):
            return FacadePayload(
                data={
                    "decisionBundleV2": {
                        "available": False, "reason": result.reason, "speed": resolved_speed,
                    }
                }
            )
        return FacadePayload(
            data={
                "decisionBundleV2": {
                    "available": True, "speed": resolved_speed,
                    **_decision_bundle_v2_payload(result, ranking),
                }
            }
        )

    def redraft_historical_replay_preview(self) -> FacadePayload:
        """Owner Test Candidate V1, section 12 (Path B) / section 13: a
        safe, read-only owner-test preview of the real 2026 KHA draft,
        labeled unambiguously HISTORICAL REPLAY -- 2026-09-02 -- never
        presented as current. Reads the already-shipped, tested
        docs/codex/KHA_SHADOW_OPTIMIZER_REPLAY.csv
        (scripts/run_kha_shadow_optimizer_replay_v1.py's real output);
        never regenerates it, never touches the live KHA draft board,
        and never extends a disclosed proxy/NOT_COMPUTABLE marker into a
        fabricated real number. Section 13's no-leakage guarantee is the
        replay script's own (each row's comparison fields are built only
        from picks strictly before it) -- unchanged and re-verified by
        that script's own test suite, not re-implemented here."""
        try:
            preview = load_kha_shadow_replay_preview(self.repo_root)
        except KhaShadowReplayUnavailable as exc:
            raise FacadeError(
                "REDRAFT_HISTORICAL_REPLAY_UNAVAILABLE", str(exc), status=409
            ) from exc
        return FacadePayload(data={"historicalReplay": kha_shadow_replay_payload(preview)})

    def set_redraft_nwr_pure_mode(self, *, profile_id: str, enabled: bool) -> FacadePayload:
        """Toggle NWR PURE — EXPERIMENTAL for a profile. Never affects NWR's
        own admitted ranking/Suggestions authority -- only gates whether
        external expert opinion (UDK/FantasyPros) is shown to the owner
        pre-pick (see redraft_external_intelligence)."""
        self._require_mode("redraft")
        normalized = self._profile_id(profile_id)
        profile = load_profile(self.redraft_root, normalized)
        updated = save_profile(
            self.redraft_root, replace(profile, nwr_pure_experimental=bool(enabled))
        )
        return FacadePayload(data={"profile": self._profile_payload(updated)})

    def start_redraft_draft_room(
        self,
        *,
        profile_id: str,
        owner_slot: int,
        seed: int,
        speed: str,
        mode: str,
    ) -> FacadePayload:
        profile, ranking, manual_assets = self._redraft_room_context(profile_id)
        try:
            adp = load_adp_snapshot(self.redraft_root, profile)
            state = start_draft_room(
                self.redraft_root,
                profile,
                ranking,
                manual_assets,
                adp,
                owner_slot=owner_slot,
                seed=seed,
                speed=speed,
                mode=mode,
            )
        except (OSError, RedraftPersistenceError, RedraftValidationError) as exc:
            raise FacadeError(
                "REDRAFT_DRAFT_START_FAILED",
                "The Draft Room could not be started with those settings.",
                status=409,
            ) from exc
        return FacadePayload(
            data={
                "draftBoard": build_draft_room_payload(profile, ranking, manual_assets, adp, state)
            }
        )

    def advance_redraft_draft_room(
        self,
        *,
        profile_id: str,
        one_pick: bool,
    ) -> FacadePayload:
        profile, ranking, manual_assets = self._redraft_room_context(profile_id)
        try:
            adp = load_adp_snapshot(self.redraft_root, profile)
            state = advance_cpu_to_owner(
                self.redraft_root,
                profile,
                ranking,
                manual_assets,
                adp,
                one_pick=one_pick,
            )
        except (OSError, RedraftPersistenceError, RedraftValidationError) as exc:
            raise FacadeError(
                "REDRAFT_DRAFT_ADVANCE_FAILED",
                "The CPU draft could not advance.",
                status=409,
            ) from exc
        return FacadePayload(
            data={
                "draftBoard": build_draft_room_payload(profile, ranking, manual_assets, adp, state)
            }
        )

    def import_redraft_adp(self, *, profile_id: str, csv_text: str) -> FacadePayload:
        profile, ranking, manual_assets = self._redraft_room_context(profile_id)
        try:
            snapshot = import_owner_adp_csv(
                self.redraft_root,
                profile,
                ranking,
                csv_text,
                manual_assets,
            )
        # NWR DATA-IMPORT UX FIX (2026-09-08, directive section 18): the real,
        # specific validation reason (e.g. "ADP CSV is missing columns: X") is
        # a deliberate, human-authored, safe-to-show message -- it must reach
        # the owner, not be swallowed into one generic sentence that gives no
        # actionable next step. Only genuine I/O/persistence failures (which
        # could carry a raw path) stay generic.
        except RedraftValidationError as exc:
            raise FacadeError("REDRAFT_ADP_IMPORT_FAILED", str(exc), status=409) from exc
        except (OSError, RedraftPersistenceError) as exc:
            raise FacadeError(
                "REDRAFT_ADP_IMPORT_FAILED",
                "The owner-supplied ADP CSV could not be saved.",
                status=409,
            ) from exc
        return FacadePayload(
            data={
                "adp": {
                    "available": snapshot.available,
                    "source": snapshot.source,
                    "sourceDate": snapshot.source_date,
                    "matched": len(snapshot.entries),
                    "unmatched": list(snapshot.unmatched),
                    "sourceSha256": snapshot.source_sha256,
                }
            }
        )

    def preview_ballers_import(
        self, *, profile_id: str, csv_text: str = "", pdf_base64: str = "",
    ) -> FacadePayload:
        """NWR DATA-IMPORT UX FIX (2026-09-08, directive section 2): a real
        preview-before-activate step for the Ballers cheat sheet, matching
        the same real pattern the owner platform ADP snapshot already uses
        (preview -> owner reviews match/coverage -> explicit activate).
        Never persists -- `parse_udk_position_csv`/`parse_udk_position_pdf`
        are read-only parsers; this method's whole job is calling one of
        them and returning the result, never calling `save_udk_position_
        *_rankings`. Exactly one of `csv_text`/`pdf_base64` is expected."""
        self._require_mode("redraft")
        if bool(csv_text.strip()) == bool(pdf_base64.strip()):
            raise FacadeError(
                "REDRAFT_UDK_PREVIEW_INVALID",
                "Provide exactly one of csvText or pdfBase64.",
                status=400,
            )
        profile, ranking, manual_assets = self._redraft_room_context(profile_id)
        try:
            if csv_text.strip():
                preview = parse_udk_position_csv(profile, ranking, csv_text, manual_assets)
                source_format = "CSV"
            else:
                pdf_bytes = base64.b64decode(pdf_base64, validate=True)
                preview = parse_udk_position_pdf(profile, ranking, pdf_bytes, manual_assets)
                source_format = "PDF"
        except (ValueError, binascii.Error) as exc:
            raise FacadeError(
                "REDRAFT_UDK_PDF_UNREADABLE", f"The UDK PDF upload was not valid base64 data: {exc}", status=400
            ) from exc
        except RedraftValidationError as exc:
            raise FacadeError("REDRAFT_UDK_PREVIEW_FAILED", str(exc), status=409) from exc
        return FacadePayload(
            data={
                "ballersPreview": {
                    "sourceFormat": preview.get("sourceFormat", source_format),
                    "sourceRows": preview["sourceRows"],
                    "matchedRows": preview["matchedRows"],
                    "unmatched": preview["unmatched"][:40],
                    "warnings": preview["warnings"][:40],
                    "sourceSha256": preview["sourceSha256"],
                    "perPositionCounts": preview.get("perPositionCounts", {}),
                    "duplicateRows": preview.get("duplicateRows", [])[:20],
                    "positions": {
                        position: entries[:20] for position, entries in preview["positions"].items()
                    },
                }
            }
        )

    def import_udk_rankings(self, *, profile_id: str, csv_text: str) -> FacadePayload:
        """Owner feedback closure, section 7: the owner's real UDK
        ("Position Rankings -- Fantasy Footballers Podcast") CSV export.
        Reuses the exact existing owner-paste identity matching; never
        replaces NWR's own rankings, only adds a separately-attributed
        UDK lane. A single export may legitimately cover only one
        position (the owner's real file is 36 QB rows) -- positions are
        read from the file itself, never assumed."""
        profile, ranking, manual_assets = self._redraft_room_context(profile_id)
        try:
            result = save_udk_position_rankings(
                self.redraft_root, profile, ranking, csv_text, manual_assets,
            )
        except RedraftValidationError as exc:
            raise FacadeError("REDRAFT_UDK_IMPORT_FAILED", str(exc), status=409) from exc
        except (OSError, RedraftPersistenceError) as exc:
            raise FacadeError(
                "REDRAFT_UDK_IMPORT_FAILED",
                "The UDK CSV could not be saved.",
                status=409,
            ) from exc
        return FacadePayload(data={"udk": result})

    def import_udk_pdf_rankings(self, *, profile_id: str, pdf_base64: str) -> FacadePayload:
        """NWR class-time autonomous hardening, section 7, superseded by the
        NWR DATA-IMPORT UX FIX (2026-09-08): `parse_udk_position_pdf`/
        `save_udk_position_pdf_rankings` have existed since the post-draft
        overnight repair (real, fixture-tested, real-sample structural
        fidelity BLOCKED_PENDING_OWNER_SAMPLE -- see
        docs/codex/NWR_PROSPECTIVE_2026_FREEZE_V2_20260908.md) but were
        never reachable from any facade method -- CSV was the only real
        owner-facing UDK import path.

        Transport changed from a local `pdf_path` (the original,
        never-actually-wired design, matching `import_udk_unmodeled_skill_
        assets`'s own convention) to base64-encoded bytes: this method had
        zero real HTTP route or frontend caller before this fix, and a real
        search of this codebase found no Tauri native file-dialog plugin
        installed anywhere (`@tauri-apps/plugin-dialog` is not a
        dependency) -- a `pdf_path` design would have required adding one.
        A standard `<input type="file">` already gives the browser/webview
        direct byte access with zero native plugin, exactly like the
        existing CSV import's `file.text()` -- this uses the same real,
        already-working mechanism, just base64-encoded for a binary
        payload. Same shared persistence/versioning as the CSV path
        (`_persist_udk_preview`), same identity-matching rules -- no
        second, parallel PDF-specific matching implementation."""
        self._require_mode("redraft")
        try:
            pdf_bytes = base64.b64decode(pdf_base64, validate=True)
        except (ValueError, binascii.Error) as exc:
            raise FacadeError(
                "REDRAFT_UDK_PDF_UNREADABLE", f"The UDK PDF upload was not valid base64 data: {exc}", status=400
            ) from exc
        profile, ranking, manual_assets = self._redraft_room_context(profile_id)
        try:
            result = save_udk_position_pdf_rankings(
                self.redraft_root, profile, ranking, pdf_bytes, manual_assets,
            )
        except RedraftValidationError as exc:
            raise FacadeError("REDRAFT_UDK_IMPORT_FAILED", str(exc), status=409) from exc
        except (OSError, RedraftPersistenceError) as exc:
            raise FacadeError(
                "REDRAFT_UDK_IMPORT_FAILED",
                "The UDK PDF could not be saved.",
                status=409,
            ) from exc
        return FacadePayload(data={"udk": result})

    def rollback_udk_position_rankings(self, *, profile_id: str, position: str) -> FacadePayload:
        """NWR class-time autonomous hardening, section 7: the directive's
        real "allow rollback to previous version" requirement -- restores
        the most recent prior UDK import for ONE position (CSV or PDF,
        whichever was previously active), leaving every other position's
        active version untouched. A position with no earlier version to
        roll back to is a real, disclosed rejection
        (`REDRAFT_UDK_ROLLBACK_UNAVAILABLE`), never a silent no-op."""
        self._require_mode("redraft")
        normalized = self._profile_id(profile_id)
        try:
            load_profile(self.redraft_root, normalized)
        except RedraftPersistenceError as exc:
            raise FacadeError("REDRAFT_PROFILE_NOT_FOUND", str(exc), status=404) from exc
        try:
            result = rollback_udk_position_rankings(self.redraft_root, normalized, position)
        except (OSError, RedraftPersistenceError, RedraftValidationError) as exc:
            raise FacadeError("REDRAFT_UDK_ROLLBACK_UNAVAILABLE", str(exc), status=409) from exc
        return FacadePayload(data={"rollback": result})

    def refresh_redraft_adp(self, *, profile_id: str) -> FacadePayload:
        profile, ranking, manual_assets = self._redraft_room_context(profile_id)
        try:
            snapshot = refresh_fantasy_football_calculator_adp(
                self.redraft_root,
                profile,
                ranking,
                manual_assets,
            )
        except (OSError, RedraftPersistenceError, RedraftValidationError) as exc:
            raise FacadeError(
                "REDRAFT_ADP_REFRESH_FAILED",
                "Fantasy Football Calculator ADP could not be refreshed. The last known "
                "good cache remains unchanged.",
                status=503,
            ) from exc
        return FacadePayload(
            data={
                "adp": {
                    "available": snapshot.available,
                    "source": snapshot.source,
                    "sourceDate": snapshot.source_date,
                    "freshness": snapshot.freshness,
                    "matched": len(snapshot.entries),
                    "unmatched": list(snapshot.unmatched),
                    "sourceSha256": snapshot.source_sha256,
                    "lastRefreshError": snapshot.last_refresh_error,
                }
            }
        )

    def preview_redraft_paste_adp(
        self, *, profile_id: str, paste_text: str, selected_source: str
    ) -> FacadePayload:
        profile, ranking, manual_assets = self._redraft_room_context(profile_id)
        try:
            preview = preview_owner_paste_adp(
                profile, ranking, paste_text, selected_source, manual_assets, root=self.redraft_root
            )
        except RedraftValidationError as exc:
            raise FacadeError("REDRAFT_PASTE_ADP_PREVIEW_FAILED", str(exc), status=409) from exc
        except (OSError, RedraftPersistenceError) as exc:
            raise FacadeError(
                "REDRAFT_PASTE_ADP_PREVIEW_FAILED",
                "The pasted platform ADP table could not be parsed. No local state changed.",
                status=409,
            ) from exc
        return FacadePayload(data={
            "pastePreview": {
                "selectedSource": preview["selectedSource"],
                "parserMode": preview["parserMode"],
                "platformCoverage": preview["platformCoverage"],
                "sourceRows": preview["sourceRows"],
                "matchedRows": preview["matchedRows"],
                "skippedRows": preview["skippedRows"],
                "unmatched": preview["unmatched"][:20],
                "warnings": preview["warnings"][:20],
            "rows": preview["parsedRows"],
            }
        })

    def save_redraft_paste_adp(
        self, *, profile_id: str, paste_text: str, selected_source: str, source_label: str
    ) -> FacadePayload:
        profile, ranking, manual_assets = self._redraft_room_context(profile_id)
        try:
            save_owner_paste_adp(
                self.redraft_root, profile, ranking, paste_text, selected_source,
                source_label, manual_assets, activate=False,
            )
        except RedraftValidationError as exc:
            raise FacadeError("REDRAFT_PASTE_ADP_SAVE_FAILED", str(exc), status=409) from exc
        except (OSError, RedraftPersistenceError) as exc:
            raise FacadeError("REDRAFT_PASTE_ADP_SAVE_FAILED", "The pasted platform ADP snapshot could not be saved.", status=409) from exc
        return self.redraft_bootstrap()

    def activate_redraft_paste_adp(self, *, profile_id: str) -> FacadePayload:
        profile, _, _ = self._redraft_room_context(profile_id)
        try:
            set_owner_paste_adp_active(self.redraft_root, profile, active=True)
        except (OSError, RedraftPersistenceError, RedraftValidationError) as exc:
            raise FacadeError("REDRAFT_PASTE_ADP_ACTIVATE_FAILED", "The pasted platform ADP snapshot could not be activated.", status=409) from exc
        return self.redraft_bootstrap()

    def clear_redraft_paste_adp(self, *, profile_id: str) -> FacadePayload:
        profile, _, _ = self._redraft_room_context(profile_id)
        try:
            if owner_platform_snapshot_status(self.redraft_root).get("available"):
                clear_owner_platform_selection(self.redraft_root, profile)
            else:
                set_owner_paste_adp_active(self.redraft_root, profile, active=False)
        except (OSError, RedraftPersistenceError, RedraftValidationError) as exc:
            raise FacadeError("REDRAFT_PASTE_ADP_CLEAR_FAILED", "The active pasted platform ADP snapshot could not be cleared.", status=409) from exc
        return self.redraft_bootstrap()

    def set_redraft_owner_platform_selection(self, *, profile_id: str, selection: str) -> FacadePayload:
        profile, _, _ = self._redraft_room_context(profile_id)
        try:
            set_owner_platform_selection(self.redraft_root, profile, selection)
        except (OSError, RedraftPersistenceError, RedraftValidationError) as exc:
            raise FacadeError("REDRAFT_OWNER_PLATFORM_SELECTION_FAILED", "The league ADP column selection could not be saved.", status=409) from exc
        return self.redraft_bootstrap()

    def approve_redraft_owner_platform_manual_match(self, *, profile_id: str, pasted_name: str, pasted_position: str, pasted_position_rank: str, selected_nwr_player_id: str, source_snapshot_hash: str = "") -> FacadePayload:
        _, ranking, manual_assets = self._redraft_room_context(profile_id)
        try:
            approve_owner_platform_manual_match(self.redraft_root, ranking, manual_assets, pasted_name=pasted_name, pasted_position=pasted_position, pasted_position_rank=pasted_position_rank, selected_nwr_player_id=selected_nwr_player_id, source_snapshot_hash=source_snapshot_hash)
        except (OSError, RedraftPersistenceError, RedraftValidationError) as exc:
            raise FacadeError("REDRAFT_OWNER_PLATFORM_ALIAS_FAILED", "The local ADP-only match was not saved.", status=409) from exc
        return self.redraft_bootstrap()

    def clear_redraft_owner_platform_manual_match(self, *, profile_id: str, pasted_name: str, pasted_position: str) -> FacadePayload:
        self._redraft_room_context(profile_id)
        clear_owner_platform_manual_match(self.redraft_root, pasted_name=pasted_name, pasted_position=pasted_position)
        return self.redraft_bootstrap()

    def ingest_redraft_sleeper_pick(
        self,
        *,
        profile_id: str,
        player_id: str,
        pick_number: int,
    ) -> FacadePayload:
        profile, ranking, manual_assets = self._redraft_room_context(profile_id)
        try:
            state = ingest_read_only_sleeper_pick(
                self.redraft_root,
                profile,
                ranking,
                manual_assets,
                player_id=self._player_id(player_id),
                pick_number=pick_number,
            )
            adp = load_adp_snapshot(self.redraft_root, profile)
        except (OSError, RedraftPersistenceError, RedraftValidationError) as exc:
            raise FacadeError(
                "REDRAFT_SLEEPER_PICK_REJECTED",
                "The read-only Sleeper pick event was rejected.",
                status=409,
            ) from exc
        return FacadePayload(
            data={
                "draftBoard": build_draft_room_payload(profile, ranking, manual_assets, adp, state)
            }
        )

    def sync_redraft_sleeper_picks(self, *, profile_id: str) -> FacadePayload:
        """Bounded, read-only auto-sync of a live Sleeper draft (section 8):
        GET .../draft/<draft_id>/picks, never a write. Applies at most
        MAX_SLEEPER_AUTO_SYNC_BATCH new picks per call and stops at the
        first conflict; the caller (frontend) re-invokes this on its own
        polling cadence -- there is no background thread here."""
        profile, ranking, manual_assets = self._redraft_room_context(profile_id)
        if profile.provider != "sleeper" or not profile.provider_league_id:
            raise FacadeError(
                "REDRAFT_SLEEPER_SYNC_NOT_LINKED",
                "Sleeper auto-sync requires a profile imported from Sleeper.",
                status=409,
            )
        receipt = load_sleeper_import_receipt(self.redraft_root, profile.profile_id)
        draft_id = str(((receipt or {}).get("draft") or {}).get("draft_id") or "")
        if not draft_id:
            raise FacadeError(
                "REDRAFT_SLEEPER_SYNC_NO_DRAFT_ID",
                "No Sleeper draft id is on record for this profile's import receipt.",
                status=409,
            )
        try:
            client = SleeperHttpClient()
            picks = load_sleeper_draft_picks(draft_id=draft_id, client=client)
            players = client.get_json("players/nfl")
            if not isinstance(players, dict):
                raise SleeperRedraftImportError("Sleeper player catalog response is malformed.")
            summary = sync_read_only_sleeper_picks(
                self.redraft_root,
                profile,
                ranking,
                manual_assets,
                sleeper_picks=picks,
                sleeper_players=players,
            )
            adp = load_adp_snapshot(self.redraft_root, profile)
        except (
            OSError,
            ValueError,
            SleeperRedraftImportError,
            RedraftPersistenceError,
            RedraftValidationError,
        ) as exc:
            raise FacadeError(
                "REDRAFT_SLEEPER_SYNC_FAILED",
                "The Sleeper auto-sync could not be completed. No local pick was changed "
                "beyond what synced before the failure.",
                status=409,
            ) from exc
        state = load_room_state(self.redraft_root, profile, ranking, manual_assets)
        if summary.get("applied"):
            self._log_owner_test_event(
                build_draft_state_change_event(
                    profile_id=profile.profile_id, timestamp_utc=utc_now(),
                    change_kind="SLEEPER_SYNC_APPLIED",
                )
            )
        return FacadePayload(
            data={
                "draftBoard": build_draft_room_payload(profile, ranking, manual_assets, adp, state),
                "sleeperSync": summary,
            }
        )

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
            research = load_unified_research_preview(self.repo_root / RESEARCH_PACKET_RELATIVE)
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

    def _active_sleeper_context(self) -> tuple[LeagueProfile, str, str]:
        selected = active_profile(self.redraft_root)
        if selected is None or selected.provider != "sleeper" or not selected.provider_league_id:
            raise FacadeError(
                "SLEEPER_REDRAFT_PROFILE_REQUIRED",
                "Activate a Sleeper-imported Redraft profile first.",
                status=409,
            )
        receipt = load_sleeper_import_receipt(self.redraft_root, selected.profile_id)
        try:
            league_id = str((receipt or {})["league"]["league_id"])
            owner_user_id = str((receipt or {})["owner"]["user_id"])
        except (KeyError, TypeError) as exc:
            raise FacadeError(
                "SLEEPER_REDRAFT_CONTEXT_REQUIRED",
                "The active Sleeper profile has no valid import receipt. Re-import it first.",
                status=409,
            ) from exc
        if league_id != selected.provider_league_id or not owner_user_id:
            raise FacadeError(
                "SLEEPER_REDRAFT_CONTEXT_REQUIRED",
                "The active Sleeper profile receipt does not match the selected league.",
                status=409,
            )
        return selected, league_id, owner_user_id

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
            ranking = apply_status_overrides_to_ranking(
                ranking, load_status_overrides(self.repo_root)
            )
        except (OSError, RedraftPersistenceError, RedraftValidationError) as exc:
            raise FacadeError(
                "REDRAFT_RANKINGS_UNAVAILABLE",
                "The active Redraft ranking is unavailable.",
                status=409,
            ) from exc
        if ranking.errors:
            # NWR Mock-Draft QA Day: surfaces the real, already-disclosed
            # validation message (e.g. "Projection universe cannot support
            # profile replacement depth: K 0/11, DST 0/11") instead of a
            # bare, unhelpful "unavailable" -- these messages never contain
            # a filesystem path or other sensitive detail, only a real
            # diagnostic an owner or a future session can act on (e.g.
            # "enable Practical Mode for a K/DST-rostering profile").
            raise FacadeError(
                "REDRAFT_RANKINGS_UNAVAILABLE",
                "The active Redraft ranking is unavailable: " + "; ".join(ranking.errors),
                status=409,
            )
        return ranking

    def _redraft_room_context(self, profile_id: str):
        self._require_mode("redraft")
        normalized = self._profile_id(profile_id)
        if active_profile_id(self.redraft_root) != normalized:
            raise FacadeError(
                "REDRAFT_PROFILE_NOT_ACTIVE",
                "Draft Room changes require the active Redraft profile.",
                status=409,
            )
        try:
            profile = load_profile(self.redraft_root, normalized)
        except (OSError, RedraftPersistenceError, RedraftValidationError) as exc:
            raise FacadeError(
                "REDRAFT_PROFILE_NOT_FOUND",
                "The requested Redraft profile was not found.",
                status=404,
            ) from exc
        return (
            profile,
            self._redraft_ranking_for_profile(normalized),
            self._manual_assets_for_profile(normalized),
        )

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

    def _manual_assets_for_profile(self, profile_id: str) -> list[dict[str, str]]:
        path = self.redraft_root / "manual_assets" / f"{profile_id}.json"
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
            values = document.get("assets") if isinstance(document, dict) else None
        except (OSError, ValueError):
            return []
        if not isinstance(values, list):
            return []
        output: list[dict[str, str]] = []
        for value in values:
            if not isinstance(value, dict):
                continue
            player_id = _text(value.get("player_id"))
            name = _text(value.get("player_name"))
            position = _text(value.get("position")).upper()
            team = _text(value.get("team")).upper()
            if player_id and name and team and position in {"K", "DST", "QB", "RB", "WR", "TE"}:
                output.append(
                    {
                        "player_id": player_id,
                        "player_name": name,
                        "position": position,
                        "team": team,
                        "authority": _text(value.get("authority")) or "MANUAL — NOT MODELED BY NWR",
                    }
                )
        return output

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
            "practicalMode": profile.practical_mode,
            "nwrPureExperimental": profile.nwr_pure_experimental,
            "provider": profile.provider,
            "providerLeagueId": profile.provider_league_id,
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
                    "blockedReason": owner_caveat_text(source.get("Blocked / pending reason")),
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
                    "rankScoreExplanation": _text(source.get("Why rank differs from raw score")),
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
            "missingFromDraftablePool": (_integer(source.get("missing_from_draftable_pool")) or 0),
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
        immediate_production: Mapping[str, Any] | None = None,
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
            "immediateProduction": dict(immediate_production or {}),
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
            "rookieIntelligence": (
                {
                    "nwrRookieScore": _number(row.get("board_score")),
                    "reviewScore": _number(row.get("review_score")),
                    "rawModelScore": _number(row.get("raw_model_score")),
                    "collegeProduction": _component_owner_context(row.get("production_component")),
                    "marketShare": _component_owner_context(row.get("market_share_component")),
                    "athleticContext": _athletic_owner_context(row.get("athletic_component")),
                    "currentRole": _current_role_owner_context(row),
                    "whatNwrLikes": _rookie_likes(row),
                    "whatHoldsBack": _rookie_holds_back(row),
                    "biggestUncertainty": _rookie_uncertainty(row),
                    "rankScoreExplanation": _rookie_rank_score_explanation(row),
                }
                if _text(row.get("official_draft_asset_id"))
                else None
            ),
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
        adp_snapshot: Any | None = None,
    ) -> list[dict[str, Any]]:
        drafted = [str(value) for value in (draft_board or {}).get("drafted", [])]
        pick_number = {player_id: index for index, player_id in enumerate(drafted, start=1)}
        adp_by_id = adp_snapshot.by_player_id if adp_snapshot is not None else {}
        decision_by_id = {
            str(value.get("playerId") or ""): value
            for value in (draft_board or {}).get("decisionRows", [])
            if isinstance(value, Mapping)
        }
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
                "positionTier": row.position_tier,
                "overallTierLabel": row.overall_tier_label,
                "positionTierLabel": row.position_tier_label,
                "sourceAsOf": row.source_as_of,
                "rookie": row.rookie,
                "overallAdp": (
                    adp_by_id[row.player_id].overall_adp if row.player_id in adp_by_id else None
                ),
                "expectedPick": (
                    adp_by_id[row.player_id].expected_pick if row.player_id in adp_by_id else None
                ),
                "expectedRound": (
                    adp_by_id[row.player_id].expected_round
                    if row.player_id in adp_by_id
                    else None
                ),
                "nwrAdpGap": decision_by_id.get(row.player_id, {}).get("nwrEdge"),
                "valueLabel": decision_by_id.get(row.player_id, {}).get(
                    "nwrView", "ADP UNAVAILABLE"
                ),
                "timingLabel": decision_by_id.get(row.player_id, {}).get(
                    "draftTiming", "ADP UNAVAILABLE"
                ),
                "makeItBack": decision_by_id.get(row.player_id, {}).get(
                    "makeItBack", "MAKE-IT-BACK: UNAVAILABLE"
                ),
                "adpSource": (adp_snapshot.source if row.player_id in adp_by_id else ""),
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
        if "boardCells" in board:
            return dict(board)
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


def _metric_status_payload(status: Any) -> dict[str, Any]:
    """Shared camelCase JSON shape for any `metric_status_contract_service.
    MetricStatus` -- previously duplicated as a nested closure inside
    `_decision_bundle_payload` alone; hoisted to module scope (NWR FINAL
    PRE-DRAFT GAP CLOSURE, section 2) so `_decision_bundle_v2_payload` can
    reuse the exact same real conversion for Raw Action Value / Decision
    Quality's status, instead of leaving RAV/DQ as the one metric with no
    shared-taxonomy disclosure. Pure presentation -- never touches a
    metric's own computed value."""
    return {
        "computationState": status.computation_state,
        "genuineZero": status.genuine_zero,
        "tiedNoSpread": status.tied_no_spread,
        "validationDomain": status.validation_domain,
        "sourceFreshness": status.source_freshness,
        "dataCoverage": status.data_coverage,
    }


def _best_turn_plan_payload(
    profile: Any,
    ranking: Any,
    manual_assets: Sequence[Mapping[str, Any]],
    adp: Any,
    room_state: Mapping[str, Any],
    comparable_leagues: Any,
    result: Any,
    base_seed: int,
) -> dict[str, Any] | None:
    """NWR post-draft overnight, section 18: wires the real, tested
    pair-pick optimizer (`evaluate_pick_pairs`,
    shadow_numeric_authorities_service.py) into the live DecisionBundle
    payload as an additive "BEST TURN PLAN" -- ONLY computed for a
    genuine back-to-back turn (this pick and the owner's immediately
    next pick, zero opponent picks between, the exact real scenario
    `evaluate_pick_pairs`'s own docstring requires), and ONLY across the
    top few candidates the DecisionBundle already computed (never a
    second, unbounded search). Returns None for any non-back-to-back
    turn, fewer than 2 real candidates, or any failure -- this never
    changes `pickScore`/`action`/candidate order; it is additional,
    owner-visible context about the specific NEXT-TWO-PICKS pair, not a
    replacement for the per-pick recommendation `evaluate_pick_pairs`
    (RESEARCH_ONLY, quadratic-by-design) itself already discloses."""
    try:
        owner_slot = room_state.get("owner_slot")
        if not isinstance(owner_slot, int):
            return None
        order = draft_order(profile)
        picks_so_far = len(room_state.get("picks", []))
        if picks_so_far >= len(order) or order[picks_so_far] != owner_slot:
            return None  # not actually the owner's turn right now
        if picks_so_far + 1 >= len(order) or order[picks_so_far + 1] != owner_slot:
            return None  # not a genuine back-to-back turn
        shortlist = [c.player_id for c in result.candidates[:3]]
        if len(shortlist) < 2:
            return None
        pair_results = evaluate_pick_pairs(
            profile, ranking, manual_assets, adp,
            owner_slot=owner_slot, candidate_player_ids=shortlist,
            comparable_leagues=comparable_leagues, seasons=100, base_seed=base_seed,
            from_state=room_state,
        )
        if not pair_results:
            return None
        best_ordering, best = max(
            pair_results.items(),
            key=lambda item: item[1].championship_equity_result.win_probability,
        )
        rows_by_id = {row.player_id: row for row in ranking.rows}

        def _name(player_id: str) -> str:
            row = rows_by_id.get(player_id)
            return row.player_name if row is not None else player_id

        return {
            "firstPickPlayerId": best_ordering[0],
            "firstPickPlayerName": _name(best_ordering[0]),
            "secondPickPlayerId": best_ordering[1],
            "secondPickPlayerName": _name(best_ordering[1]),
            "projectedTeamScorePercentile": best.team_score_result.percentile,
            "projectedWinProbability": best.championship_equity_result.win_probability,
            "candidatesConsidered": len(shortlist),
            "label": (
                "BEST TURN PLAN — EXPERIMENTAL: the best evaluated order for your "
                "NEXT TWO immediate picks (a genuine back-to-back turn, zero opponent "
                "picks between) -- does not change this pick's own recommendation."
            ),
        }
    except Exception:
        # Never let an experimental, additive field break the real
        # DecisionBundle response -- silently omitted, not a crash.
        return None


def _decision_bundle_payload(
    bundle: Any,
    ranking: Any,
    manual_assets: Sequence[Mapping[str, Any]] = (),
    *,
    profile: Any = None,
    current_owner_player_ids: Sequence[str] = (),
) -> dict[str, Any]:
    """Converts a real decision_bundle_live_service DecisionBundle into the
    camelCase JSON shape Draft Room V2 consumes (Owner Test Candidate V1,
    section 2). Enriches each candidate with player_name/position from the
    ranking (CandidateBundle itself only carries player_id) -- never invents
    a value not already on the bundle or the ranking.

    NWR OVERNIGHT (K/DST completion): a manual-only candidate (K/DST, now
    a real Suggestions candidate when genuinely needed) has no `ranking`
    row -- without this, the payload fell back to the raw internal
    player_id (e.g. "manual:K:11533") as the displayed name and a blank
    position. Falls back to the real manual_assets entry instead; only
    the raw id itself is a last resort if even that's missing.

    `profile`/`current_owner_player_ids` (NWR post-draft overnight,
    section 7): optional, both default to a falsy value -- every existing
    caller that doesn't pass them (the V2 sub-bundle embedding at line
    ~4505) gets byte-identical output. When supplied, adds a real,
    additive `marginalRosterUtility` explanation block per candidate
    (explain_marginal_roster_reason + marginal_roster_utility).

    PROMOTION UPDATE: marginal_roster_utility passed its real,
    preregistered walk-forward evaluation (4 real historical seasons x
    12 real draft slots; see
    docs/codex/NWR_MARGINAL_UTILITY_WALK_FORWARD_PROMOTION_V1.md) and is
    now the PRIMARY candidate ORDER (`_candidate_sort_key` in
    decision_bundle_service.py) -- `bundle.candidates` already arrives
    here in marginal-utility order, this function does not re-sort.
    `pickScore`'s own VALUE is completely unchanged; only which
    candidate is first/what "NWR PICK NOW" means was promoted. This
    block remains additional, disclosed context (the full explanation,
    not just the sort-driving number), not a second, undisclosed
    policy."""
    rows_by_id = {row.player_id: row for row in ranking.rows}
    manual_by_id = {
        str(asset.get("player_id") or ""): asset for asset in manual_assets
    }
    metric_status_payload = _metric_status_payload
    marginal_utility_fn = None
    if profile is not None:
        from src.services.shadow_numeric_authorities_service import marginal_roster_utility as _mru
        marginal_utility_fn = _mru

    def candidate_payload(candidate: Any) -> dict[str, Any]:
        row = rows_by_id.get(candidate.player_id)
        manual = manual_by_id.get(candidate.player_id)
        fallback_name = (
            str(manual.get("player_name") or manual.get("playerName") or "")
            if manual is not None
            else ""
        ) or candidate.player_id
        fallback_position = str(manual.get("position") or "") if manual is not None else ""
        marginal_utility_payload = None
        if marginal_utility_fn is not None:
            try:
                result = marginal_utility_fn(
                    candidate.player_id, current_owner_player_ids, profile, ranking, manual_assets
                )
                marginal_utility_payload = {
                    "utility": result.utility,
                    "becomesStarter": result.becomes_starter,
                    "benchRedundancyBefore": result.bench_redundancy_before,
                    "explanation": result.explanation,
                    "label": "MARGINAL ROSTER UTILITY — PROMOTED: the real, walk-forward-validated basis for this recommendation's order",
                }
            except Exception:
                # Never let an experimental, additive field break the real
                # DecisionBundle response -- silently omitted, not a crash.
                marginal_utility_payload = None
        return {
            "playerId": candidate.player_id,
            "playerName": row.player_name if row is not None else fallback_name,
            "position": row.position if row is not None else fallback_position,
            "marginalRosterUtility": marginal_utility_payload,
            # The exact raw number _candidate_sort_key actually sorted by
            # (computed once in build_decision_bundle) -- distinct from
            # marginalRosterUtility.utility above, which is a separate,
            # independent recomputation for the richer explanation block;
            # both call the same real function with the same real inputs
            # and will always agree numerically.
            "marginalUtility": candidate.marginal_utility,
            "playerScore": candidate.player_score,
            "teamScoreAfter": candidate.team_score_after,
            "teamScoreDelta": candidate.team_score_delta,
            "championshipEquityAfter": candidate.championship_equity_after,
            "equityGain": candidate.equity_gain,
            "costOfWaiting": candidate.cost_of_waiting,
            "makeItBackProbability": candidate.make_it_back_probability,
            "makeItBackTrials": candidate.make_it_back_trials,
            "rawDecisionUtility": candidate.raw_decision_utility,
            "teamScoreUtilityComponent": candidate.team_score_utility_component,
            "equityUtilityComponent": candidate.equity_utility_component,
            "pickScore": candidate.pick_score,
            "pickScoreTiedNoSpread": candidate.pick_score_tied_no_spread,
            "action": candidate.action.replace("_", " "),
            "warnings": list(candidate.warnings),
            "uncertainty": candidate.uncertainty,
            "metricStatus": {
                key: metric_status_payload(status)
                for key, status in candidate.metric_status.items()
            },
        }

    return {
        "version": bundle.version,
        "currentTeamScore": {
            "percentile": bundle.current_team_score.percentile,
            "rosterValue": bundle.current_team_score.roster_value,
            "populationSize": bundle.current_team_score.population_size,
            "label": bundle.current_team_score.label,
        },
        "currentChampionshipEquity": {
            "winProbability": bundle.current_championship_equity.win_probability,
            "standardError": bundle.current_championship_equity.standard_error,
            "seasonsSimulated": bundle.current_championship_equity.seasons_simulated,
            "assumedFormat": True,
            "label": bundle.current_championship_equity.label,
        },
        "candidates": [candidate_payload(c) for c in bundle.candidates],
        "provenance": {
            "leagueProfileHash": bundle.provenance.league_profile_hash,
            "rosterStateHash": bundle.provenance.roster_state_hash,
            "availablePlayerHash": bundle.provenance.available_player_hash,
            "universeHash": bundle.provenance.universe_hash,
            "projectionModelVersion": bundle.provenance.projection_model_version,
            "marketSnapshotHash": bundle.provenance.market_snapshot_hash,
            "featureSetVersion": bundle.provenance.feature_set_version,
            "teamScoreVersion": bundle.provenance.team_score_version,
            "championshipEquityVersion": bundle.provenance.championship_equity_version,
            "pickScoreVersion": bundle.provenance.pick_score_version,
            "optimizerVersion": bundle.provenance.optimizer_version,
            "seed": bundle.provenance.seed,
            "simulationCount": bundle.provenance.simulation_count,
            "timestampUtc": bundle.provenance.timestamp_utc,
            "bundleHash": bundle.provenance.bundle_hash,
        },
        "simulationMetadata": bundle.simulation_metadata,
        "latencySeconds": bundle.latency_seconds,
    }


def _decision_bundle_v2_payload(bundle_v2: Any, ranking: Any) -> dict[str, Any]:
    """Converts a real `decision_bundle_service_v2.DecisionBundleV2` into
    the camelCase JSON shape a future Draft Room UI toggle would consume.
    Nests the complete, unmodified V1 payload under `v1` so a caller (or a
    future UI) can render V1 exactly as it already does today, plus the
    additive `teamScoreV2`/`championshipEquityV2` fields per candidate --
    never replaces or reorders anything V1 already returns."""
    v1_by_id = {c.player_id: c for c in bundle_v2.v1_bundle.candidates}
    # NWR FINAL PRE-DRAFT GAP CLOSURE (section 2, "Metric Status
    # Consistency"): Raw Action Value / expected regret / Decision
    # Quality were the one metric family with no shared-taxonomy status --
    # only a bare "OK"/"UNAVAILABLE: <reason>"/"SKIPPED_TOP_N_ONLY" string,
    # handled by ad hoc frontend string-matching instead of the same
    # EVALUATED/BUDGET_LIMITED/UNSUPPORTED/... vocabulary every other
    # metric already gets. `raw_action_value_status()` already existed in
    # metric_status_contract_service.py (built for exactly this mapping)
    # but was never actually called anywhere in the live pipeline -- real,
    # additive wiring only: reads the SAME `raw_action_value_status`/
    # `decision_quality_percentile` fields this payload already returns,
    # computes zero new values, and changes no candidate ordering.
    source_as_of = ranking.rows[0].source_as_of if ranking.rows else ""

    def candidate_v2_payload(candidate: Any) -> dict[str, Any]:
        v1_candidate = v1_by_id.get(candidate.player_id)
        dq_status = raw_action_value_status(
            candidate.raw_action_value_status,
            candidate.decision_quality_percentile,
            source_as_of=source_as_of,
        )
        return {
            "playerId": candidate.player_id,
            "v2Status": candidate.v2_status,
            "teamScoreV2": candidate.team_score_v2,
            "championshipEquityV2": candidate.championship_equity_v2,
            "pickScore": v1_candidate.pick_score if v1_candidate is not None else None,
            "rawActionValue": candidate.raw_action_value,
            "expectedRegret": candidate.expected_regret,
            "decisionQualityPercentile": candidate.decision_quality_percentile,
            "rawActionValueStatus": candidate.raw_action_value_status,
            "decisionQualityStatus": _metric_status_payload(dq_status),
        }

    return {
        "version": bundle_v2.version,
        "v2Status": bundle_v2.v2_status,
        "teamCount": bundle_v2.team_count,
        "evidenceContext": bundle_v2.evidence_context,
        "currentTeamScoreV2": bundle_v2.current_team_score_v2,
        "candidates": [candidate_v2_payload(c) for c in bundle_v2.candidates],
        "warnings": list(bundle_v2.warnings),
        "v1": _decision_bundle_payload(bundle_v2.v1_bundle, ranking),
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
        return [f"{label[:1].upper() + label[1:]}: {value:.1f}/100" for value, label in values[:3]]
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
        "watchlist_or_data_incomplete_context_review": ("Watchlist or incomplete evidence context"),
        "manual_review": "Manual review",
    }.get(value, "Not enough information")
