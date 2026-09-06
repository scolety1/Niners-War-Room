/**
 * Draft Room V2 -- an ISOLATED candidate (sections 3-6 of the remaining-
 * overnight-runway directive; Owner Test Candidate V1 wires the real
 * DecisionBundle backend in). Reachable at /draft-room-v2, a distinct
 * route from the production Draft Room at "/" (pages.tsx#DraftRoomPage)
 * -- nothing here replaces it automatically.
 *
 * Suggestions/Team Score/Championship Equity/Pick Score/Cost of Waiting/
 * Make-It-Back are now REAL, backend-computed values from
 * client.getRedraftDecisionBundle() (src/services/decision_bundle_live_
 * service.py via DesktopBackendFacade.redraft_decision_bundle) -- never a
 * fabricated or frontend-computed number. When the backend cannot
 * compute a bundle (blocked ranking, not the owner's turn, no legal
 * candidate), the UI renders the real `reason` string, never a
 * placeholder score. RESEARCH_NOT_CONNECTED remains in use only for the
 * one piece genuinely not wired this pass: the AI Explanation API
 * (decision_bundle_explanation_service.py exists and is tested, but has
 * no HTTP route yet -- see docs/codex/OWNER_TEST_CANDIDATE_V1_REPORT_20260903.md).
 */
import type {
  DecisionBundle,
  DecisionBundleCandidate,
  DraftBoard,
  DraftRosterPlayer,
  KhaHistoricalReplayPreview,
  LeagueProfile,
  RedraftBootstrap,
  RedraftExternalIntelligence,
  RedraftExternalIntelligenceEntry,
} from "@nwr/contracts";
import {
  Button,
  DataTable,
  EmptyState,
  Icon,
  PageHeader,
  Panel,
  SearchInput,
  StatusBadge,
  type TableColumn,
  formatNumber,
} from "@nwr/ui";
import { NwrApiError, type NwrApiClient, type RedraftDecisionBundleV2CandidateResponse } from "@nwr/api-client";
import { useEffect, useMemo, useRef, useState } from "react";

import { CheatSheetPage } from "./cheat-sheet";
// Reused, not rebuilt (section 9 -- REUSE FIRST): the exact global,
// position-filter-ignoring pick search and keyboard-navigation helpers the
// production Draft Room (pages.tsx) already ships and that fixed 23 real
// SEARCH_FAILURE picks in the KHA draft reconciliation ledger.
import { globalPickSearchRows, nextRapidCaptureIndex, type PickSearchAsset, type PickSearchCandidate } from "./pages";

// Primary modes (top-level, per the consolidation directive): the dense
// actionable cockpit, the reusable Cheat Sheet, and the fixed-column board.
export const DRAFT_ROOM_V2_PRIMARY_TABS = ["SUGGESTIONS", "CHEAT_SHEET", "BOARD"] as const;
// Secondary workspace (Rankings/Teams/Queue, plus Compare/Replay which the
// consolidation directive does not name but which stay reachable rather
// than deleted -- section on routing: "do not delete" applies here too).
export const DRAFT_ROOM_V2_SECONDARY_TABS = ["PLAYERS", "QUEUE", "MY_TEAM", "COMPARE", "REPLAY"] as const;
export const DRAFT_ROOM_V2_TABS = [...DRAFT_ROOM_V2_PRIMARY_TABS, ...DRAFT_ROOM_V2_SECONDARY_TABS] as const;
export type DraftRoomV2Tab = (typeof DRAFT_ROOM_V2_TABS)[number];

export function tabLabel(tab: DraftRoomV2Tab): string {
  if (tab === "MY_TEAM") return "Teams";
  if (tab === "REPLAY") return "Historical Replay";
  if (tab === "CHEAT_SHEET") return "Cheat Sheets";
  if (tab === "PLAYERS") return "Rankings";
  return tab.charAt(0) + tab.slice(1).toLowerCase();
}

export const RESEARCH_NOT_CONNECTED = "Not connected — SHADOW/RESEARCH backend";
export const COMPARE_MAX_PLAYERS = 4;

// --- Pure data-preparation functions (unit-tested in draft-room-v2.test.ts) --

export interface SuggestionRow {
  playerId: string;
  playerName: string;
  position: string;
  team: string;
  nwrRank: number | null;
  marketExpectedPick: number | null;
  playerScore: number | null;
  // Real, backend-computed DecisionBundle fields -- never fabricated.
  pickScore: number;
  teamScoreAfter: number;
  teamScoreDelta: number;
  championshipEquityAfter: number;
  equityGain: number;
  costOfWaiting: number;
  makeItBackProbability: number | null;
  action: string;
  warnings: string[];
  uncertainty: string;
  alertSeverity: string | null;
  alertText: string | null;
  // Real Raw Action Value fields (see raw_action_value_live_service.py) --
  // the fix for the Fantasy Gamers Pick-Score-collapse bug. null/
  // "SKIPPED_TOP_N_ONLY" when this candidate was outside the RAV preset's
  // top-N (cost-controlled), never a fabricated differentiator.
  expectedRegret: number | null;
  decisionQualityPercentile: number | null;
  rawActionValueStatus: string | null;
}

/**
 * The Suggestions surface's real candidate list IS the DecisionBundle's
 * own candidate list -- default-sorted by Pick Score descending (section
 * 6), never re-derived from ADP-edge alone (which the directive warns
 * can let a deep market target dominate). NWR rank / market ADP columns
 * are enrichment looked up from the already-fetched rankings, not a
 * second candidate-selection pass. Returns [] (never fabricated rows)
 * when the bundle is unavailable -- the caller renders the real reason.
 */
export function buildSuggestionsRows(
  decisionBundle: DecisionBundle | null | undefined,
  rankings: RedraftBootstrap["rankings"],
  intelById: Map<string, RedraftExternalIntelligenceEntry>,
  rawActionValueById: Map<string, RedraftDecisionBundleV2CandidateResponse> = new Map(),
): SuggestionRow[] {
  if (!decisionBundle || !decisionBundle.available) return [];
  const rankingById = new Map(rankings.map((row) => [row.playerId, row]));
  return [...decisionBundle.candidates]
    .sort((a, b) => b.pickScore - a.pickScore)
    .map((candidate) => {
      const ranking = rankingById.get(candidate.playerId);
      const intel = intelById.get(candidate.playerId);
      const rav = rawActionValueById.get(candidate.playerId);
      return {
        playerId: candidate.playerId,
        playerName: candidate.playerName,
        position: candidate.position,
        team: ranking?.team ?? "",
        nwrRank: ranking?.overallRank ?? null,
        marketExpectedPick: ranking?.expectedPick ?? ranking?.overallAdp ?? null,
        playerScore: candidate.playerScore,
        pickScore: candidate.pickScore,
        teamScoreAfter: candidate.teamScoreAfter,
        teamScoreDelta: candidate.teamScoreDelta,
        championshipEquityAfter: candidate.championshipEquityAfter,
        equityGain: candidate.equityGain,
        costOfWaiting: candidate.costOfWaiting,
        makeItBackProbability: candidate.makeItBackProbability,
        action: candidate.action,
        warnings: candidate.warnings,
        uncertainty: candidate.uncertainty,
        alertSeverity: intel?.currentAlertSeverity ?? null,
        alertText: intel?.currentAlert ?? null,
        expectedRegret: rav?.expectedRegret ?? null,
        decisionQualityPercentile: rav?.decisionQualityPercentile ?? null,
        rawActionValueStatus: rav?.rawActionValueStatus ?? null,
      };
    });
}

export interface MyTeamSummary {
  roster: DraftRosterPlayer[];
  strengths: string[];
  holes: string[];
}

export function buildMyTeamSummary(data: RedraftBootstrap): MyTeamSummary {
  const board = data.draftBoard;
  const roster = board?.myRoster ?? [];
  const req = data.activeProfile?.roster;
  if (!req) return { roster, strengths: [], holes: [] };
  const counts: Record<string, number> = {};
  for (const player of roster) counts[player.position] = (counts[player.position] ?? 0) + 1;
  const strengths: string[] = [];
  const holes: string[] = [];
  for (const [position, need] of [
    ["QB", req.qb], ["RB", req.rb], ["WR", req.wr], ["TE", req.te], ["K", req.k], ["DST", req.dst],
  ] as Array<[string, number]>) {
    if (need <= 0) continue;
    const have = counts[position] ?? 0;
    if (have >= need) strengths.push(`${position} (${have}/${need})`);
    else holes.push(`${position} (${have}/${need})`);
  }
  return { roster, strengths, holes };
}

// StatusBadge's own tone union (packages/ui) -- "safe" plus the shared
// HealthTone set. Reused directly rather than inventing a parallel tone
// vocabulary.
export type BadgeTone = "safe" | "review" | "blocked" | "ready" | "offline";

export interface UdkBadge {
  key: string;
  label: string;
  tone: BadgeTone;
  title?: string;
}

export function severityToBadgeTone(severity: string | null | undefined): BadgeTone {
  const normalized = (severity ?? "").toUpperCase();
  if (normalized === "HIGH") return "blocked";
  if (normalized === "MEDIUM") return "review";
  return "safe";
}

export function buildUdkBadges(entry: RedraftExternalIntelligenceEntry | undefined): UdkBadge[] {
  if (!entry) return [];
  const badges: UdkBadge[] = [];
  if (entry.udkPositionRank) badges.push({ key: "udk-rank", label: `UDK #${entry.udkPositionRank}`, tone: "ready" });
  if (entry.udkTier) badges.push({ key: "udk-tier", label: `Tier ${entry.udkTier}`, tone: "ready" });
  if (entry.currentAlert) {
    badges.push({
      key: "alert",
      label: entry.currentAlertSeverity || "Alert",
      tone: severityToBadgeTone(entry.currentAlertSeverity),
      title: entry.currentAlert,
    });
  }
  return badges;
}

/**
 * Real, backend-computed current Team Score / Championship Equity for
 * the roster as it stands right now -- from the same DecisionBundle the
 * Suggestions candidates come from (current_team_score/
 * current_championship_equity are computed once per bundle, independent
 * of which candidate is selected).
 */
export interface CurrentRosterScores {
  teamScorePercentile: number | null;
  teamScoreLabel: string | null;
  championshipEquityWinProbability: number | null;
  championshipEquityLabel: string | null;
  assumedFormat: boolean;
}

export function buildCurrentRosterScores(
  decisionBundle: DecisionBundle | null | undefined,
): CurrentRosterScores {
  if (!decisionBundle || !decisionBundle.available) {
    return {
      teamScorePercentile: null, teamScoreLabel: null,
      championshipEquityWinProbability: null, championshipEquityLabel: null,
      assumedFormat: false,
    };
  }
  return {
    teamScorePercentile: decisionBundle.currentTeamScore.percentile,
    teamScoreLabel: decisionBundle.currentTeamScore.label,
    championshipEquityWinProbability: decisionBundle.currentChampionshipEquity.winProbability,
    championshipEquityLabel: decisionBundle.currentChampionshipEquity.label,
    assumedFormat: decisionBundle.currentChampionshipEquity.assumedFormat,
  };
}

/**
 * Compact position-demand summary (section: "reuse the existing
 * intelligence, don't rebuild a position-demand model" -- Make-It-Back /
 * Cost of Waiting already fold opponent roster need into their own real
 * Monte Carlo trials via `_roster_need_adjustment()`, confirmed by audit;
 * this is only a UI-facing read of the same already-fetched `board.teams`
 * roster state, for the two positions that function actually penalizes
 * once filled: QB and TE, both typically single-starter). Counts every
 * NON-owner team's already-filled starter slots at that position against
 * the league's real configured requirement -- never a prediction, never a
 * hard exclusion, just what has already, factually happened this draft.
 */
export interface PositionDemandRow {
  position: string;
  filledOpponents: number;
  totalOpponents: number;
  requiredStarters: number;
}

export function buildPositionDemand(
  board: DraftBoard | null | undefined,
  profile: LeagueProfile | null | undefined,
): PositionDemandRow[] {
  if (!board?.teams?.length || !profile) return [];
  const opponents = board.teams.filter((team) => !team.owner);
  if (!opponents.length) return [];
  const rows: PositionDemandRow[] = [];
  for (const [position, required] of [
    ["QB", profile.roster.qb],
    ["TE", profile.roster.te],
  ] as Array<[string, number]>) {
    if (required <= 0) continue;
    const filledOpponents = opponents.filter(
      (team) => team.roster.filter((player) => player.position === position).length >= required,
    ).length;
    rows.push({ position, filledOpponents, totalOpponents: opponents.length, requiredStarters: required });
  }
  return rows;
}

/**
 * Compact owner-roster strip -- the same real starter-slot accounting
 * pages.tsx#DraftRoomPage's "My roster needs" panel already performs
 * (QB/RB/WR/TE/FLEX/K/DST/bench, FLEX overflow computed from RB/WR/TE
 * surplus, bench capped at the configured bench size), reused here so
 * Suggestions doesn't require a tab switch to see roster fit.
 */
export interface RosterStripSlot {
  label: string;
  have: number;
  need: number;
}

export function buildRosterStrip(data: RedraftBootstrap): RosterStripSlot[] {
  const profile = data.activeProfile;
  const board = data.draftBoard;
  if (!profile || !board) return [];
  const req = profile.roster;
  const counts: Record<string, number> = {};
  for (const player of board.myRoster ?? []) counts[player.position] = (counts[player.position] ?? 0) + 1;
  const capped = (pos: string, need: number) => Math.min(counts[pos] ?? 0, need);
  const qb = capped("QB", req.qb), rb = capped("RB", req.rb), wr = capped("WR", req.wr), te = capped("TE", req.te);
  const k = capped("K", req.k), dst = capped("DST", req.dst);
  const flexPool = Math.max(0, (counts.RB ?? 0) - rb) + Math.max(0, (counts.WR ?? 0) - wr) + Math.max(0, (counts.TE ?? 0) - te);
  const flex = Math.min(flexPool, req.flex);
  const starterSlotsFilled = qb + rb + wr + te + flex + k + dst;
  const bench = Math.min(Math.max(0, (board.myRoster?.length ?? 0) - starterSlotsFilled), req.benchSize);
  return [
    { label: "QB", have: qb, need: req.qb }, { label: "RB", have: rb, need: req.rb },
    { label: "WR", have: wr, need: req.wr }, { label: "TE", have: te, need: req.te },
    { label: "FLEX", have: flex, need: req.flex }, { label: "K", have: k, need: req.k },
    { label: "DST", have: dst, need: req.dst }, { label: "BN", have: bench, need: req.benchSize },
  ];
}

/**
 * A "close call" is two or more top-ranked Suggestions candidates whose
 * real Pick Score is nearly tied -- a real, disclosed signal that the
 * formula genuinely cannot separate them cleanly, never a UI approximation
 * that invents false precision. Threshold is on the same 0-100 Pick Score
 * scale the table already renders; does not alter any score.
 */
export function findCloseCall(rows: SuggestionRow[], threshold = 3): { a: SuggestionRow; b: SuggestionRow } | null {
  if (rows.length < 2) return null;
  const sorted = [...rows].sort((x, y) => y.pickScore - x.pickScore);
  const [a, b] = sorted;
  if (!a || !b) return null;
  return Math.abs(a.pickScore - b.pickScore) <= threshold ? { a, b } : null;
}

export function toggleCompareSelection(
  current: string[],
  playerId: string,
  max: number = COMPARE_MAX_PLAYERS,
): string[] {
  if (current.includes(playerId)) return current.filter((id) => id !== playerId);
  if (current.length >= max) return current;
  return [...current, playerId];
}

export interface CompareRow {
  playerId: string;
  playerName: string;
  position: string;
  nwrRank: number | null;
  overallAdp: number | null;
  tier: string | null;
  status: string;
  // Real DecisionBundle fields -- null (never fabricated) when this
  // player is not one of the current Suggestions candidates (Compare can
  // hold players beyond the top-N the backend evaluated this pick).
  playerScore: number | null;
  teamScoreDelta: number | null;
  equityGain: number | null;
  costOfWaiting: number | null;
  makeItBackProbability: number | null;
  pickScore: number | null;
  action: string | null;
  warnings: string[];
  evaluated: boolean;
}

export function buildCompareRows(
  playerIds: string[],
  data: RedraftBootstrap,
  intelById: Map<string, RedraftExternalIntelligenceEntry>,
  decisionBundle?: DecisionBundle | null,
): CompareRow[] {
  const candidateById = new Map(
    decisionBundle && decisionBundle.available
      ? decisionBundle.candidates.map((c) => [c.playerId, c])
      : [],
  );
  return playerIds
    .map((playerId) => {
      const ranked = data.rankings.find((row) => row.playerId === playerId);
      const manual = data.manualAssets?.find((row) => row.playerId === playerId);
      const intel = intelById.get(playerId);
      if (!ranked && !manual) return null;
      const candidate = candidateById.get(playerId);
      return {
        playerId,
        playerName: ranked?.playerName ?? manual?.playerName ?? playerId,
        position: ranked?.position ?? manual?.position ?? "?",
        nwrRank: ranked?.overallRank ?? null,
        overallAdp: ranked?.overallAdp ?? manual?.overallAdp ?? null,
        tier: ranked?.overallTierLabel ?? null,
        status: intel?.currentAlert ? `Alert: ${intel.currentAlertSeverity ?? "flagged"}` : "No current alert",
        playerScore: candidate?.playerScore ?? null,
        teamScoreDelta: candidate?.teamScoreDelta ?? null,
        equityGain: candidate?.equityGain ?? null,
        costOfWaiting: candidate?.costOfWaiting ?? null,
        makeItBackProbability: candidate?.makeItBackProbability ?? null,
        pickScore: candidate?.pickScore ?? null,
        action: candidate?.action ?? null,
        warnings: candidate?.warnings ?? [],
        evaluated: candidate !== undefined,
      };
    })
    .filter((row): row is CompareRow => row !== null);
}

/**
 * A real, deterministic, template-based summary from structured fields
 * only -- no invented reasoning, no LLM call. Reports the best NWR rank,
 * the largest ADP discount (NWR rank meaningfully earlier than market),
 * and the position with the most remaining depth among the compared
 * players, using only fields already on CompareRow/the ranking data
 * passed in.
 */
export function generateCompareSummary(rows: CompareRow[], positionDepth: Record<string, number>): string {
  if (rows.length < 2) return "Select at least two players to compare.";
  const evaluated = rows.filter((row) => row.evaluated && row.pickScore != null);
  const parts: string[] = [];
  if (evaluated.length > 0) {
    const bestPickScore = evaluated.reduce((a, b) => (a.pickScore! > b.pickScore! ? a : b));
    parts.push(
      `${bestPickScore.playerName} has the highest Pick Score — EXPERIMENTAL among the evaluated candidates in this comparison (${formatNumber(bestPickScore.pickScore!, 1)}).`,
    );
  }
  const ranked = rows.filter((row) => row.nwrRank != null);
  if (ranked.length > 0) {
    const best = ranked.reduce((a, b) => (a.nwrRank! < b.nwrRank! ? a : b));
    parts.push(`${best.playerName} has the best NWR rank (#${best.nwrRank}) in this comparison.`);
  }
  const withAdpGap = rows
    .filter((row) => row.nwrRank != null && row.overallAdp != null)
    .map((row) => ({ row, gap: row.overallAdp! - row.nwrRank! }))
    .filter((entry) => entry.gap > 0);
  if (withAdpGap.length > 0) {
    const biggest = withAdpGap.reduce((a, b) => (a.gap > b.gap ? a : b));
    parts.push(
      `${biggest.row.playerName} offers the largest market discount (NWR #${biggest.row.nwrRank} vs. ADP ${formatNumber(biggest.row.overallAdp!, 1)}, a ${formatNumber(biggest.gap, 1)}-spot gap).`,
    );
  }
  const positions = [...new Set(rows.map((row) => row.position))];
  if (positions.length > 1) {
    const deepest = positions.reduce((a, b) => ((positionDepth[a] ?? 0) >= (positionDepth[b] ?? 0) ? a : b));
    const count = positionDepth[deepest] ?? 0;
    parts.push(`${deepest} is the deepest position among these ${rows.length} players (${count} other ranked ${deepest}s remain).`);
  }
  return parts.join(" ") || "No structured comparison signal available for this selection.";
}

// --- Component -------------------------------------------------------------

export function DraftRoomV2Page({
  client,
  data,
  onUpdate,
}: {
  client: NwrApiClient;
  data: RedraftBootstrap;
  onUpdate: (data: RedraftBootstrap) => void;
}) {
  const [tab, setTab] = useState<DraftRoomV2Tab>("SUGGESTIONS");
  const [sidebarVisible, setSidebarVisible] = useState(true);
  const [drawerPlayerId, setDrawerPlayerId] = useState<string | null>(null);
  const [compareIds, setCompareIds] = useState<string[]>([]);
  const [externalIntel, setExternalIntel] = useState<RedraftExternalIntelligence | null>(null);
  const [decisionBundle, setDecisionBundle] = useState<DecisionBundle | null>(null);
  const [decisionBundleLoading, setDecisionBundleLoading] = useState(false);
  // Real Raw Action Value / expected regret / decision-quality percentile
  // per candidate -- the actual, historically-validated fix for the
  // Fantasy Gamers Pick-Score-collapse bug (see raw_action_value_live_
  // service.py). Fetched from the SEPARATE, additive decision-bundle-v2
  // endpoint (its `v1` field is the unmodified V1 bundle used for
  // `decisionBundle` above); a fetch failure here degrades to no RAV
  // columns, never to a fabricated number and never to blocking Pick Score.
  const [rawActionValueById, setRawActionValueById] = useState<Map<string, RedraftDecisionBundleV2CandidateResponse>>(new Map());
  const [nwrPureToggling, setNwrPureToggling] = useState(false);
  const [historicalReplay, setHistoricalReplay] = useState<KhaHistoricalReplayPreview | null>(null);
  const [historicalReplayLoading, setHistoricalReplayLoading] = useState(false);
  const [historicalReplayError, setHistoricalReplayError] = useState<string | null>(null);
  // Queue is a real, session-local watchlist -- proven absent as a backend
  // or frontend capability by direct audit (grep across desktop/ and src/
  // found no "queue" concept anywhere in Redraft) before adding it here,
  // per the reuse-first/build-only-when-absent rule. It never records a
  // pick by itself; queuing a player changes nothing about the draft board.
  const [queuedIds, setQueuedIds] = useState<string[]>([]);
  // Quick pick search -- reuses V1's exact globalPickSearchRows/
  // nextRapidCaptureIndex helpers (imported from ./pages) rather than a
  // second search implementation. Visible from every tab, not buried.
  const [quickQuery, setQuickQuery] = useState("");
  const [quickIndex, setQuickIndex] = useState(0);
  const quickCaptureActive = useRef(false);
  const quickInputRef = useRef<HTMLInputElement>(null);
  const [working, setWorking] = useState("");
  const [mutationError, setMutationError] = useState<NwrApiError | null>(null);
  const board = data.draftBoard;
  const nwrPureActive = data.activeProfile?.nwrPureExperimental ?? false;
  const liveMode = board?.mode === "LIVE_READ_ONLY";
  const ownerTurn = Boolean(board?.isOwnerTurn);
  // Identical semantics to pages.tsx#DraftRoomPage's canRecordPick: MOCK
  // mode only allows recording when it is genuinely the owner's turn (CPU
  // turns advance automatically); LIVE_READ_ONLY allows recording every
  // real pick, owner's and opponents', in sequence.
  const canRecordPick = (liveMode ? !board?.complete : ownerTurn) && Boolean(board?.configured);

  const mark = async (playerId: string) => {
    if (!data.activeProfileId) return;
    const playerName =
      data.rankings.find((row) => row.playerId === playerId)?.playerName ??
      data.manualAssets?.find((row) => row.playerId === playerId)?.playerName ??
      "Player";
    setWorking(playerId);
    setMutationError(null);
    try {
      const next = liveMode
        ? await client.ingestSleeperDraftPick(data.activeProfileId, playerId, (board?.drafted?.length ?? 0) + 1)
        : await client.markDrafted(data.activeProfileId, playerId);
      onUpdate(next);
      setQueuedIds((current) => current.filter((id) => id !== playerId));
    } catch (reason) {
      setMutationError(reason instanceof NwrApiError ? reason : new NwrApiError(`${playerName} could not be recorded.`));
    } finally {
      setWorking("");
    }
  };

  const toggleQueue = (playerId: string) => {
    setQueuedIds((current) => (current.includes(playerId) ? current.filter((id) => id !== playerId) : [...current, playerId]));
  };

  // Feature-parity gap closed: Undo (client.undoDraftPick) already exists
  // and is exercised in the Legacy Draft Room -- reused here verbatim so
  // the consolidated room does not require a tab switch to correct a
  // mis-click.
  const undo = async () => {
    if (!data.activeProfileId) return;
    setWorking("undo");
    setMutationError(null);
    try {
      onUpdate(await client.undoDraftPick(data.activeProfileId));
    } catch (reason) {
      setMutationError(reason instanceof NwrApiError ? reason : new NwrApiError("The last pick could not be restored."));
    } finally {
      setWorking("");
    }
  };

  const draftedIds = board?.drafted ?? [];
  const quickResults = globalPickSearchRows(
    data.rankings as unknown as PickSearchAsset[],
    (data.manualAssets ?? []) as unknown as PickSearchAsset[],
    draftedIds,
    quickQuery,
    8,
  );
  const quickActiveIndex = quickResults.length ? Math.min(quickIndex, quickResults.length - 1) : 0;

  const recordFromQuickCapture = async (playerId: string) => {
    if (!canRecordPick || Boolean(working)) return;
    quickCaptureActive.current = true;
    await mark(playerId);
    quickCaptureActive.current = false;
    setQuickQuery("");
    setQuickIndex(0);
    window.requestAnimationFrame(() => quickInputRef.current?.focus({ preventScroll: true }));
  };

  const onQuickKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
    const stepped = nextRapidCaptureIndex(event.key, event.shiftKey, quickActiveIndex, quickResults.length);
    if (stepped !== null) {
      event.preventDefault();
      setQuickIndex(stepped);
    } else if (event.key === "Enter") {
      event.preventDefault();
      const candidate = quickResults[quickActiveIndex];
      if (candidate) void recordFromQuickCapture(candidate.playerId);
    } else if (event.key === "Escape") {
      setQuickQuery("");
      setQuickIndex(0);
    }
  };

  const onToggleNwrPure = () => {
    if (!data.activeProfileId || nwrPureToggling) return;
    setNwrPureToggling(true);
    client
      .setNwrPureMode(data.activeProfileId, !nwrPureActive)
      .then((updated) => onUpdate(updated))
      .catch(() => {
        // Real failures are surfaced by the standard error boundary this
        // page's caller already installs -- this toggle simply stops
        // spinning rather than silently pretending the switch happened.
      })
      .finally(() => setNwrPureToggling(false));
  };
  // A real recomputation trigger, not a poll: updatedAtUtc changes on every
  // real draft-board mutation (pick, correction, Catch-Up, Sleeper sync),
  // so a stale DecisionBundle can never survive a changed roster/universe
  // (section 10) -- the effect below re-fetches whenever this changes.
  const rosterStateSignal = board?.updatedAtUtc ?? "";

  useEffect(() => {
    if (!data.activeProfileId) return;
    let cancelled = false;
    client
      .getRedraftExternalIntelligence(data.activeProfileId)
      .then((response) => {
        if (!cancelled) setExternalIntel(response.externalIntelligence);
      })
      .catch(() => {
        if (!cancelled) setExternalIntel({ available: false, generatedNote: "EXTERNAL INTEL UNAVAILABLE", entries: [] });
      });
    return () => {
      cancelled = true;
    };
  }, [client, data.activeProfileId]);

  useEffect(() => {
    if (!data.activeProfileId) return;
    let cancelled = false;
    setDecisionBundleLoading(true);
    client
      .getRedraftDecisionBundle(data.activeProfileId, "FAST")
      .then((response) => {
        if (!cancelled) setDecisionBundle(response.decisionBundle);
      })
      .catch(() => {
        if (!cancelled) {
          setDecisionBundle({
            available: false, speed: "FAST",
            reason: "The DecisionBundle request failed -- backend calculation unavailable.",
          });
        }
      })
      .finally(() => {
        if (!cancelled) setDecisionBundleLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [client, data.activeProfileId, rosterStateSignal]);

  useEffect(() => {
    // Separate, additive fetch (never replaces the V1 bundle above --
    // matches the backend's own "SEPARATE, explicitly opt-in endpoint"
    // contract). A failure here only means no RAV columns this render,
    // never a blocked Suggestions table -- Pick Score keeps working from
    // the V1 fetch regardless.
    if (!data.activeProfileId) return;
    let cancelled = false;
    client
      .getRedraftDecisionBundleV2(data.activeProfileId, "FAST")
      .then((response) => {
        if (cancelled) return;
        const byId = new Map<string, RedraftDecisionBundleV2CandidateResponse>();
        for (const candidate of response.decisionBundleV2.candidates ?? []) byId.set(candidate.playerId, candidate);
        setRawActionValueById(byId);
      })
      .catch(() => {
        if (!cancelled) setRawActionValueById(new Map());
      });
    return () => {
      cancelled = true;
    };
  }, [client, data.activeProfileId, rosterStateSignal]);

  useEffect(() => {
    // Lazy, tab-gated fetch: a fixed, static, non-current artifact -- no
    // reason to load it before the owner actually opens the tab, and no
    // reason to refetch on every draft-state change the way the live
    // DecisionBundle does (sections 12/13 -- this never changes with the
    // current draft, it is a historical replay).
    if (tab !== "REPLAY" || historicalReplay || historicalReplayLoading) return;
    let cancelled = false;
    setHistoricalReplayLoading(true);
    client
      .getKhaHistoricalReplayPreview()
      .then((response) => {
        if (!cancelled) setHistoricalReplay(response.historicalReplay);
      })
      .catch((error: unknown) => {
        if (!cancelled) {
          setHistoricalReplayError(
            error instanceof Error ? error.message : "The historical replay preview failed to load.",
          );
        }
      })
      .finally(() => {
        if (!cancelled) setHistoricalReplayLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [client, tab, historicalReplay, historicalReplayLoading]);

  const intelById = useMemo(() => {
    const map = new Map<string, RedraftExternalIntelligenceEntry>();
    for (const entry of externalIntel?.entries ?? []) map.set(entry.playerId, entry);
    return map;
  }, [externalIntel]);

  const positionDepth = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const row of data.rankings) {
      if (row.drafted) continue;
      counts[row.position] = (counts[row.position] ?? 0) + 1;
    }
    return counts;
  }, [data.rankings]);

  const suggestions = useMemo(
    () => buildSuggestionsRows(decisionBundle, data.rankings, intelById, rawActionValueById),
    [decisionBundle, data.rankings, intelById, rawActionValueById],
  );
  const myTeam = useMemo(() => buildMyTeamSummary(data), [data]);
  const currentScores = useMemo(() => buildCurrentRosterScores(decisionBundle), [decisionBundle]);
  const compareRows = useMemo(
    () => buildCompareRows(compareIds, data, intelById, decisionBundle),
    [compareIds, data, intelById, decisionBundle],
  );
  const compareSummary = useMemo(() => generateCompareSummary(compareRows, positionDepth), [compareRows, positionDepth]);
  const positionDemand = useMemo(() => buildPositionDemand(board, data.activeProfile), [board, data.activeProfile]);
  const rosterStrip = useMemo(() => buildRosterStrip(data), [data]);
  const closeCall = useMemo(() => findCloseCall(suggestions), [suggestions]);
  const queuedRows = useMemo(
    () =>
      queuedIds
        .map((playerId) => {
          const ranked = data.rankings.find((row) => row.playerId === playerId);
          const manual = data.manualAssets?.find((row) => row.playerId === playerId);
          if (!ranked && !manual) return null;
          return {
            playerId,
            playerName: ranked?.playerName ?? manual?.playerName ?? playerId,
            position: ranked?.position ?? manual?.position ?? "?",
            team: ranked?.team ?? manual?.team ?? "",
            nwrRank: ranked?.overallRank ?? null,
          };
        })
        .filter((row): row is { playerId: string; playerName: string; position: string; team: string; nwrRank: number | null } => row !== null),
    [queuedIds, data.rankings, data.manualAssets],
  );

  const onPlayerClick = (playerId: string, event: React.MouseEvent) => {
    if (event.altKey) {
      setCompareIds((current) => toggleCompareSelection(current, playerId));
      return;
    }
    setDrawerPlayerId(playerId);
  };

  if (!data.activeProfile) {
    return (
      <EmptyState
        icon="profile"
        title="No active league profile"
        message="Draft Room V2 needs an active Redraft profile -- set one up from the standard Draft Room first."
      />
    );
  }

  const drawerEntry = drawerPlayerId ? intelById.get(drawerPlayerId) : undefined;
  const drawerRanking = drawerPlayerId ? data.rankings.find((row) => row.playerId === drawerPlayerId) : undefined;
  const drawerCandidate =
    drawerPlayerId && decisionBundle && decisionBundle.available
      ? decisionBundle.candidates.find((c) => c.playerId === drawerPlayerId)
      : undefined;

  return (
    <div className="draft-room-v2-page">
      <PageHeader
        eyebrow={draftRoomV2Eyebrow(board)}
        title={`${data.activeProfile.leagueName} — Draft Room`}
        description="Suggestions / Cheat Sheets / Draft Board, plus Rankings, Queue, Teams, Compare and Historical Replay in the workspace. Alt+click any player to add them to Compare."
        actions={
          <>
            <Button data-draft-undo disabled={!board?.canUndo || Boolean(working)} icon="undo" variant="secondary" onClick={() => void undo()}>
              {working === "undo" ? "Restoring…" : "Undo"}
            </Button>
            <Button
              variant={nwrPureActive ? "primary" : "ghost"}
              onClick={onToggleNwrPure}
              disabled={nwrPureToggling}
              title="NWR PURE — EXPERIMENTAL: when on, external expert intelligence (UDK/FantasyPros) is hidden. Platform market data, current factual news/status, and the real Pick Score/Team Score/Championship Equity stay visible -- DecisionBundle never reads external intelligence regardless of this switch."
            >
              {nwrPureToggling ? "NWR PURE — updating…" : nwrPureActive ? "NWR PURE — EXPERIMENTAL: ON" : "NWR PURE — EXPERIMENTAL: OFF"}
            </Button>
            <Button variant="ghost" onClick={() => setSidebarVisible((value) => !value)}>
              {sidebarVisible ? "Hide sidebar" : "Show sidebar"}
            </Button>
          </>
        }
      />
      {mutationError ? (
        <div className="alert-strip alert-strip--blocked" role="alert">
          <strong>Pick could not be recorded</strong>
          <span>{mutationError.message}</span>
        </div>
      ) : null}
      {board?.configured ? (
        <OnClockStrip board={board} />
      ) : (
        <p className="boundary-note">Start the draft from the Legacy Draft Room to set your slot before using this room.</p>
      )}
      <Panel className="quick-capture-panel" title="Quick pick" eyebrow={canRecordPick ? "Position filter ignored · type, arrows/Tab to choose, Enter to record" : "Start the draft, and wait for your turn, to record picks here"}>
        <div className="rapid-capture">
          <label className="search-input rapid-capture__input">
            <Icon name="search" size={16} />
            <input
              aria-activedescendant={quickResults[quickActiveIndex] ? `quick-result-${quickActiveIndex}` : undefined}
              aria-controls="quick-capture-results"
              aria-label="Quick pick"
              disabled={!canRecordPick}
              onChange={(event) => { setQuickQuery(event.target.value); setQuickIndex(0); }}
              onFocus={(event) => event.target.select()}
              onKeyDown={onQuickKeyDown}
              placeholder="Type a player, K, or D/ST…"
              ref={quickInputRef}
              type="search"
              value={quickQuery}
            />
          </label>
          <ul className="rapid-capture__results" id="quick-capture-results" role="listbox">
            {quickResults.map((candidate, index) => (
              <li
                aria-selected={index === quickActiveIndex}
                className={index === quickActiveIndex ? "rapid-capture__result--active" : ""}
                id={`quick-result-${index}`}
                key={candidate.playerId}
                onMouseDown={(event) => { event.preventDefault(); void recordFromQuickCapture(candidate.playerId); }}
                role="option"
              >
                <strong>{candidate.playerName}</strong>
                <small>{candidate.team} · {candidate.position}</small>
                <span className="rapid-capture__actions">
                  <Button variant="ghost" onClick={(event) => { event.stopPropagation(); toggleQueue(candidate.playerId); }}>
                    {queuedIds.includes(candidate.playerId) ? "Queued" : "Queue"}
                  </Button>
                </span>
              </li>
            ))}
            {quickQuery.trim() && !quickResults.length ? <li className="rapid-capture__empty">No match in the ranked universe or manual K/DST/unmodeled pool.</li> : null}
          </ul>
        </div>
      </Panel>
      <div className="draft-room-v2-layout">
        {sidebarVisible ? (
          <nav className="draft-room-v2-sidebar" aria-label="Draft Room tabs">
            <span className="draft-room-v2-sidebar-group">Draft Room</span>
            {DRAFT_ROOM_V2_PRIMARY_TABS.map((value) => (
              <button
                key={value}
                type="button"
                aria-pressed={tab === value}
                className={tab === value ? "draft-room-v2-tab draft-room-v2-tab--active" : "draft-room-v2-tab"}
                onClick={() => setTab(value)}
              >
                {tabLabel(value)}
              </button>
            ))}
            <span className="draft-room-v2-sidebar-group">Workspace</span>
            {DRAFT_ROOM_V2_SECONDARY_TABS.map((value) => (
              <button
                key={value}
                type="button"
                aria-pressed={tab === value}
                className={tab === value ? "draft-room-v2-tab draft-room-v2-tab--active" : "draft-room-v2-tab"}
                onClick={() => setTab(value)}
              >
                {tabLabel(value)}
                {value === "QUEUE" && queuedRows.length > 0 ? <b className="draft-room-v2-tab__badge">{queuedRows.length}</b> : null}
              </button>
            ))}
          </nav>
        ) : null}
        <div className="draft-room-v2-content">
          {tab === "SUGGESTIONS" ? (
            <SuggestionsTab
              rows={suggestions}
              onPlayerClick={onPlayerClick}
              decisionBundle={decisionBundle}
              loading={decisionBundleLoading}
              rosterStrip={rosterStrip}
              positionDemand={positionDemand}
              closeCall={closeCall}
              canRecordPick={canRecordPick}
              working={working}
              queuedIds={queuedIds}
              onDraft={(playerId) => void mark(playerId)}
              onQueue={toggleQueue}
              externalIntel={externalIntel}
            />
          ) : null}
          {tab === "CHEAT_SHEET" ? <CheatSheetPage data={data} /> : null}
          {tab === "PLAYERS" ? (
            <PlayersTab data={data} intelById={intelById} onPlayerClick={onPlayerClick} />
          ) : null}
          {tab === "BOARD" ? <BoardTab board={board} profile={data.activeProfile} onPlayerClick={onPlayerClick} /> : null}
          {tab === "QUEUE" ? (
            <QueueTab
              rows={queuedRows}
              canRecordPick={canRecordPick}
              working={working}
              onDraft={(playerId) => void mark(playerId)}
              onRemove={toggleQueue}
            />
          ) : null}
          {tab === "MY_TEAM" ? <MyTeamTab summary={myTeam} currentScores={currentScores} /> : null}
          {tab === "COMPARE" ? (
            <CompareTab
              rows={compareRows}
              summary={compareSummary}
              onRemove={(playerId) => setCompareIds((current) => current.filter((id) => id !== playerId))}
            />
          ) : null}
          {tab === "REPLAY" ? (
            <ReplayTab
              replay={historicalReplay}
              loading={historicalReplayLoading}
              error={historicalReplayError}
            />
          ) : null}
        </div>
      </div>
      {compareIds.length > 0 && tab !== "COMPARE" ? (
        <div className="draft-room-v2-compare-tray" role="status">
          <span>{compareIds.length} selected for Compare</span>
          <Button variant="secondary" onClick={() => setTab("COMPARE")}>
            Open Compare
          </Button>
        </div>
      ) : null}
      {drawerPlayerId ? (
        <PlayerDrawer
          playerId={drawerPlayerId}
          ranking={drawerRanking}
          intel={drawerEntry}
          candidate={drawerCandidate}
          staleAlertData={Boolean(externalIntel?.stale)}
          onClose={() => setDrawerPlayerId(null)}
        />
      ) : null}
    </div>
  );
}

function draftRoomV2Eyebrow(board: DraftBoard | null | undefined): string {
  if (!board?.configured) return "Set your draft slot from the Legacy Draft Room to begin";
  if (board.complete) return "Draft complete";
  return board.isOwnerTurn ? "You are on the clock" : `Team ${board.currentTeamSlot ?? "?"} is on the clock`;
}

/** Always-visible current-pick/clock context -- identical fields to
 * pages.tsx#DraftRoomPage's ".on-clock" section (round/overall pick,
 * on-clock team, next owner pick, picks-until-owner via the snake position
 * run, snake direction implied by round parity), reused here rather than
 * re-derived, so the consolidated room never requires a tab switch to see
 * whose turn it is. */
function OnClockStrip({ board }: { board: DraftBoard }) {
  const picksUntilOwner = board.nextOwnerPick && board.currentPick ? Math.max(0, board.nextOwnerPick - board.currentPick) : null;
  return (
    <section className="on-clock">
      <div>
        <span>{board.complete ? "Draft complete" : board.isOwnerTurn ? "You are on the clock" : `Team ${board.currentTeamSlot ?? "?"} is on the clock`}</span>
        <strong>{board.currentPick ? `Pick ${board.currentPick}` : "Draft complete"}</strong>
        <small>{board.positionRun?.length ? `Run: ${board.positionRun.map((run) => `${run.position} ×${run.count}`).join(", ")}` : "No active position run"}</small>
      </div>
      <div className="clock-ring">
        <strong>{board.mode === "LIVE_READ_ONLY" ? "ENTER PICK" : board.isOwnerTurn ? "YOU" : "CPU"}</strong>
        <span>{board.mode === "LIVE_READ_ONLY" ? "LIVE" : (board.speed ?? "")}</span>
      </div>
      <div>
        <span>Next owner pick</span>
        <strong>{board.nextOwnerPick ?? "—"}</strong>
        <small>{picksUntilOwner != null ? `${picksUntilOwner} pick${picksUntilOwner === 1 ? "" : "s"} until your turn` : ""}</small>
      </div>
    </section>
  );
}

function SuggestionsTab({
  rows,
  onPlayerClick,
  decisionBundle,
  loading,
  rosterStrip,
  positionDemand,
  closeCall,
  canRecordPick,
  working,
  queuedIds,
  onDraft,
  onQueue,
  externalIntel,
}: {
  rows: SuggestionRow[];
  onPlayerClick: (playerId: string, event: React.MouseEvent) => void;
  decisionBundle: DecisionBundle | null;
  loading: boolean;
  rosterStrip: RosterStripSlot[];
  positionDemand: PositionDemandRow[];
  closeCall: { a: SuggestionRow; b: SuggestionRow } | null;
  canRecordPick: boolean;
  working: string;
  queuedIds: string[];
  onDraft: (playerId: string) => void;
  onQueue: (playerId: string) => void;
  externalIntel: RedraftExternalIntelligence | null;
}) {
  const columns: TableColumn[] = [
    { key: "pick", label: "Pick", align: "right", render: (row) => (
      <span className="draft-room-v2-pick-actions">
        <Button
          data-draft-action
          disabled={!canRecordPick || Boolean(working)}
          variant="primary"
          onClick={() => onDraft(String(row.playerId))}
        >
          {working === String(row.playerId) ? "Saving…" : "Draft"}
        </Button>
        <Button variant="ghost" onClick={() => onQueue(String(row.playerId))}>
          {queuedIds.includes(String(row.playerId)) ? "Queued" : "Queue"}
        </Button>
      </span>
    ) },
    { key: "pickScore", label: "Pick Score — EXPERIMENTAL", sort: "number", render: (row) => formatNumber(row.pickScore as number, 1) },
    { key: "playerName", label: "Player", sort: "text", render: (row) => (
      <span
        className="player-cell player-cell--clickable"
        onClick={(event) => onPlayerClick(String(row.playerId), event as unknown as React.MouseEvent)}
        title="Click for Score Details / Why"
      >
        <strong>{String(row.playerName)}</strong>
        <small>{String(row.team)} · {String(row.position)}</small>
      </span>
    ) },
    { key: "nwrRank", label: "NWR", sort: "number", render: (row) => row.nwrRank == null ? "—" : String(row.nwrRank) },
    { key: "marketExpectedPick", label: "Market", sort: "number", render: (row) => row.marketExpectedPick == null ? "—" : formatNumber(row.marketExpectedPick as number, 1) },
    { key: "teamScoreAfter", label: "Team Score — RESEARCH", sort: "number", render: (row) => (
      <span title="Before → After, see Score Details">{formatNumber(row.teamScoreAfter as number, 1)} ({row.teamScoreDelta as number >= 0 ? "+" : ""}{formatNumber(row.teamScoreDelta as number, 1)})</span>
    ) },
    { key: "championshipEquityAfter", label: "Champ Eq — SIMULATED RESEARCH", sort: "number", render: (row) => (
      <span>{formatNumber((row.championshipEquityAfter as number) * 100, 1)}% ({row.equityGain as number >= 0 ? "+" : ""}{formatNumber((row.equityGain as number) * 100, 1)} pp)</span>
    ) },
    { key: "costOfWaiting", label: "Wait Cost", sort: "number", render: (row) => formatNumber(row.costOfWaiting as number, 1) },
    { key: "makeItBackProbability", label: "Make It Back", sort: "number", render: (row) => row.makeItBackProbability == null ? "UNKNOWN" : `${formatNumber((row.makeItBackProbability as number) * 100, 0)}%` },
    { key: "decisionQualityPercentile", label: "Decision Quality — RAW ACTION VALUE", sort: "number", render: (row) => {
      const status = row.rawActionValueStatus as string | null;
      if (row.decisionQualityPercentile == null) return status === "SKIPPED_TOP_N_ONLY" ? <span title="Outside this pick's cost-controlled Raw Action Value candidate set.">n/a</span> : (status ?? "n/a");
      return <span title={`Expected regret: ${row.expectedRegret != null ? formatNumber(row.expectedRegret as number, 1) : "—"}`}>{formatNumber(row.decisionQualityPercentile as number, 0)}</span>;
    } },
    { key: "action", label: "Action", sort: "text", render: (row) => <StatusBadge tone={actionToBadgeTone(String(row.action))} label={String(row.action)} /> },
    { key: "alertText", label: "Alert", sort: "text", render: (row) => row.alertText ? <span title={String(row.alertText)}><StatusBadge tone={severityToBadgeTone(row.alertSeverity as string | null)} label={String(row.alertSeverity ?? "Alert")} /></span> : "—" },
  ];
  const unavailableReason = decisionBundle && !decisionBundle.available ? decisionBundle.reason : null;
  return (
    <>
      {(rosterStrip.length > 0 || positionDemand.length > 0) ? (
        <Panel title="My roster & opponent demand" eyebrow="Compact context — full detail in Teams">
          {rosterStrip.length > 0 ? (
            <div className="roster-strip">
              {rosterStrip.map((slot) => (
                <span key={slot.label} className={`roster-slot ${slot.have >= slot.need && slot.need > 0 ? "roster-slot--full" : ""}`}>
                  {slot.label} {slot.have}/{slot.need}
                </span>
              ))}
            </div>
          ) : null}
          {positionDemand.length > 0 ? (
            <div className="roster-strip draft-room-v2-position-demand" title="Opponents who already have a full starting group at this position -- reused from the same real roster-need signal Make-It-Back/Cost of Waiting already fold into their own simulations.">
              {positionDemand.map((row) => (
                <span key={row.position} className="roster-slot">
                  {row.position} demand: {row.filledOpponents}/{row.totalOpponents} opponents filled
                </span>
              ))}
            </div>
          ) : null}
        </Panel>
      ) : null}
      {externalIntel?.stale ? (
        <div className="alert-strip" role="status">
          <strong>STALE ALERT DATA</strong>
          <span>
            The current-alert snapshot is {externalIntel.snapshotAgeHours != null ? `${formatNumber(externalIntel.snapshotAgeHours, 1)}h` : "an unknown amount of time"} old
            {externalIntel.snapshotGeneratedAtUtc ? ` (built ${externalIntel.snapshotGeneratedAtUtc})` : ""}. A quiet Alert column below may mean no current news, or it may mean this snapshot has not been refreshed since it was built -- not a confirmed absence of news.
          </span>
        </div>
      ) : null}
      {closeCall ? (
        <div className="alert-strip" role="status">
          <strong>CLOSE CALL</strong>
          <span>
            {closeCall.a.playerName} and {closeCall.b.playerName} have nearly identical Pick Score — EXPERIMENTAL
            ({formatNumber(closeCall.a.pickScore, 1)} vs {formatNumber(closeCall.b.pickScore, 1)}). The formula cannot cleanly separate them; use roster fit, Make-It-Back, Decision Quality — RAW ACTION VALUE, and Alert context below to break the tie.
          </span>
        </div>
      ) : null}
      <Panel title="Suggestions" eyebrow="Real DecisionBundle candidates — default sorted by Pick Score, descending">
        {loading ? (
          <EmptyState icon="activity" title="Computing…" message="Calculating the real DecisionBundle for this pick." />
        ) : unavailableReason ? (
          <EmptyState icon="alert" title="DecisionBundle unavailable" message={unavailableReason} />
        ) : rows.length === 0 ? (
          <EmptyState icon="activity" title="No suggestions yet" message="Start the Draft Room to populate this table." />
        ) : (
          <DataTable columns={columns} rows={rows as unknown as Array<Record<string, unknown>>} rowKey={(row) => String(row.playerId)} />
        )}
      </Panel>
    </>
  );
}

function actionToBadgeTone(action: string): BadgeTone {
  const normalized = action.toUpperCase();
  if (normalized === "TAKE NOW") return "blocked";
  if (normalized === "DEEP TARGET" || normalized === "GOOD VALUE") return "ready";
  if (normalized === "WAIVER WATCH") return "offline";
  return "review";
}

function PlayersTab({
  data,
  intelById,
  onPlayerClick,
}: {
  data: RedraftBootstrap;
  intelById: Map<string, RedraftExternalIntelligenceEntry>;
  onPlayerClick: (playerId: string, event: React.MouseEvent) => void;
}) {
  const rows = data.rankings.filter((row) => !row.drafted);
  const columns: TableColumn[] = [
    { key: "overallRank", label: "NWR", sort: "number" },
    { key: "playerName", label: "Player", sort: "text", render: (row) => (
      <span
        className="player-cell player-cell--clickable"
        onClick={(event) => onPlayerClick(String(row.playerId), event as unknown as React.MouseEvent)}
      >
        <strong>{String(row.playerName)}</strong>
        <small>{String(row.team)} · {String(row.position)}</small>
      </span>
    ) },
    { key: "overallAdp", label: "ADP", sort: "number", render: (row) => row.overallAdp == null ? "—" : formatNumber(row.overallAdp as number, 1) },
    { key: "badges", label: "UDK", sort: "text", render: (row) => (
      <span className="udk-badge-row">
        {buildUdkBadges(intelById.get(String(row.playerId))).map((badge) => (
          <span key={badge.key} title={badge.title}><StatusBadge tone={badge.tone} label={badge.label} /></span>
        ))}
      </span>
    ) },
  ];
  return (
    <Panel title="Players" eyebrow={`${rows.length} undrafted players`}>
      <DataTable columns={columns} rows={rows as unknown as Array<Record<string, unknown>>} rowKey={(row) => String(row.playerId)} />
    </Panel>
  );
}

/**
 * Fixed team-column geometry (section: "one fixed column per team, not
 * capped/wrapping"): a real, reproduced bug -- the prior grid used
 * `repeat(auto-fill, minmax(96px, 1fr))`, which wraps to however many
 * columns fit the viewport, completely independent of the league's real
 * team count (the exact "wraps at 12 columns" symptom this fixed-column
 * layout, ported directly from the already-correct pages.tsx#DraftRoomPage
 * board, was reported to reproduce). Team columns are fixed vertically by
 * `teamSlot` regardless of snake direction; rounds are rows; the whole
 * grid scrolls horizontally rather than wrapping for a wide league.
 */
function BoardTab({
  board,
  profile,
  onPlayerClick,
}: {
  board: DraftBoard | null | undefined;
  profile: LeagueProfile | null | undefined;
  onPlayerClick: (playerId: string, event: React.MouseEvent) => void;
}) {
  if (!board?.boardCells || !profile) {
    return <EmptyState icon="activity" title="No draft board yet" message="Start the Draft Room from the standard Draft Room page first." />;
  }
  const teamCount = profile.teamCount;
  const rounds = profile.draft.rounds;
  const cellByRoundAndSlot = new Map(board.boardCells.map((cell) => [`${cell.round}-${cell.teamSlot}`, cell]));
  return (
    <Panel title="Draft Board" eyebrow={`${teamCount} teams × ${rounds} rounds — fixed columns, scroll for wide leagues`}>
      <div className="draft-board-scroll">
        <div
          className="draft-board-v2-grid"
          style={{ gridTemplateColumns: `38px repeat(${teamCount}, minmax(105px, 1fr))`, minWidth: `${38 + teamCount * 111}px` }}
        >
          <div className="draft-board-v2-corner">Rd</div>
          {Array.from({ length: teamCount }, (_, index) => index + 1).map((slot) => (
            <div key={`head-${slot}`} className={slot === board.ownerSlot ? "draft-board-v2-head draft-board-v2-head--owner" : "draft-board-v2-head"}>
              T{slot}{slot === board.ownerSlot ? " · YOU" : ""}
            </div>
          ))}
          {Array.from({ length: rounds }, (_, index) => index + 1).flatMap((round) => [
            <b className="draft-board-v2-round" key={`round-${round}`}>{round}</b>,
            ...Array.from({ length: teamCount }, (_, column) => {
              const slot = column + 1;
              const cell = cellByRoundAndSlot.get(`${round}-${slot}`);
              return (
                <article
                  key={`${round}-${slot}`}
                  className={`draft-board-v2-cell ${cell?.ownerPick ? "draft-board-v2-cell--owner" : ""} ${cell?.current ? "draft-board-v2-cell--current" : ""}`}
                  onClick={cell?.playerId ? (event) => onPlayerClick(cell.playerId, event) : undefined}
                >
                  <span className="draft-board-v2-cell__pick">{cell?.pickNumber ? `#${cell.pickNumber}` : ""}</span>
                  <span className="draft-board-v2-cell__player">
                    {cell?.playerName || (cell?.status === "UNRESOLVED" ? "Unresolved" : "Open")}
                  </span>
                </article>
              );
            }),
          ])}
        </div>
      </div>
    </Panel>
  );
}

function MyTeamTab({ summary, currentScores }: { summary: MyTeamSummary; currentScores: CurrentRosterScores }) {
  return (
    <>
      <Panel title="My roster" eyebrow={`${summary.roster.length} players`}>
        <DataTable
          columns={[
            { key: "pickNumber", label: "Pick", sort: "number" },
            { key: "playerName", label: "Player", sort: "text" },
            { key: "position", label: "Pos", sort: "text" },
            { key: "team", label: "Team", sort: "text" },
          ]}
          rows={summary.roster as unknown as Array<Record<string, unknown>>}
          rowKey={(row) => String(row.playerId)}
        />
      </Panel>
      <Panel title="Strengths & holes" eyebrow="Filled vs. open roster slots">
        <div className="roster-strip">
          {summary.strengths.map((label) => (
            <span key={label} className="roster-slot roster-slot--full">{label}</span>
          ))}
          {summary.holes.map((label) => (
            <span key={label} className="roster-slot">{label}</span>
          ))}
        </div>
      </Panel>
      <Panel title={currentScores.teamScoreLabel ?? "Team Score — RESEARCH"} eyebrow="Current roster, real backend percentile">
        {currentScores.teamScorePercentile == null ? (
          <p className="boundary-note">{RESEARCH_NOT_CONNECTED}. DecisionBundle has not returned a current roster score yet.</p>
        ) : (
          <p className="score-headline">{formatNumber(currentScores.teamScorePercentile, 1)}</p>
        )}
      </Panel>
      <Panel
        title={currentScores.championshipEquityLabel ?? "Simulated Championship Equity — RESEARCH"}
        eyebrow={currentScores.assumedFormat ? "ASSUMED FORMAT — see simulation assumptions" : "Current roster"}
      >
        {currentScores.championshipEquityWinProbability == null ? (
          <p className="boundary-note">{RESEARCH_NOT_CONNECTED}. DecisionBundle has not returned a current roster score yet.</p>
        ) : (
          <p className="score-headline">{formatNumber(currentScores.championshipEquityWinProbability * 100, 1)}%</p>
        )}
      </Panel>
    </>
  );
}

function CompareTab({
  rows,
  summary,
  onRemove,
}: {
  rows: CompareRow[];
  summary: string;
  onRemove: (playerId: string) => void;
}) {
  if (rows.length === 0) {
    return <EmptyState icon="activity" title="Nothing selected" message="Alt+click a player anywhere in Draft Room V2 to add them here." />;
  }
  return (
    <>
      <Panel title="Compare" eyebrow={`${rows.length} of ${COMPARE_MAX_PLAYERS} players`}>
        <DataTable
          columns={[
            { key: "playerName", label: "Player", sort: "text" },
            { key: "position", label: "Pos", sort: "text" },
            { key: "playerScore", label: "Player Score", sort: "number", render: (row) => row.playerScore == null ? "—" : formatNumber(row.playerScore as number, 1) },
            { key: "overallAdp", label: "Market", sort: "number", render: (row) => row.overallAdp == null ? "—" : formatNumber(row.overallAdp as number, 1) },
            { key: "teamScoreDelta", label: "Team Score Δ — RESEARCH", sort: "number", render: (row) => row.teamScoreDelta == null ? "Not evaluated" : `${row.teamScoreDelta as number >= 0 ? "+" : ""}${formatNumber(row.teamScoreDelta as number, 1)}` },
            { key: "equityGain", label: "Champ Eq Δ — SIMULATED RESEARCH", sort: "number", render: (row) => row.equityGain == null ? "Not evaluated" : `${row.equityGain as number >= 0 ? "+" : ""}${formatNumber((row.equityGain as number) * 100, 2)} pp` },
            { key: "costOfWaiting", label: "Wait Cost", sort: "number", render: (row) => row.costOfWaiting == null ? "—" : formatNumber(row.costOfWaiting as number, 1) },
            { key: "makeItBackProbability", label: "Make It Back", sort: "number", render: (row) => row.makeItBackProbability == null ? "UNKNOWN" : `${formatNumber((row.makeItBackProbability as number) * 100, 0)}%` },
            { key: "pickScore", label: "Pick Score — EXPERIMENTAL", sort: "number", render: (row) => row.pickScore == null ? "—" : formatNumber(row.pickScore as number, 1) },
            { key: "action", label: "Action", sort: "text", render: (row) => row.action == null ? "—" : <StatusBadge tone={actionToBadgeTone(String(row.action))} label={String(row.action)} /> },
            { key: "warnings", label: "Warnings", sort: "text", render: (row) => {
              const warnings = row.warnings as string[];
              return warnings.length === 0 ? "—" : <span title={warnings.join(" ")}>{warnings.length} warning{warnings.length > 1 ? "s" : ""}</span>;
            } },
            { key: "status", label: "Status", sort: "text" },
            { key: "remove", label: "", align: "right", render: (row) => <Button variant="ghost" onClick={() => onRemove(String(row.playerId))}>Remove</Button> },
          ]}
          rows={rows as unknown as Array<Record<string, unknown>>}
          rowKey={(row) => String(row.playerId)}
        />
      </Panel>
      <Panel title="AI Compare Summary" eyebrow="Structured fields only — no invented reasoning">
        <p>{summary}</p>
      </Panel>
    </>
  );
}

function ReplayTab({
  replay,
  loading,
  error,
}: {
  replay: KhaHistoricalReplayPreview | null;
  loading: boolean;
  error: string | null;
}) {
  if (loading) {
    return <EmptyState icon="activity" title="Loading…" message="Fetching the historical replay preview." />;
  }
  if (error) {
    return <EmptyState icon="alert" title="Historical replay unavailable" message={error} />;
  }
  if (!replay) {
    return <EmptyState icon="activity" title="Historical Replay" message="Open this tab to load the KHA 2026-09-02 replay preview." />;
  }
  const columns: TableColumn[] = [
    { key: "pickNumber", label: "Pick", sort: "number" },
    { key: "round", label: "Rd", sort: "number" },
    { key: "playerName", label: "Player", sort: "text", render: (row) => (
      <span><strong>{String(row.playerName)}</strong> <small>{String(row.team)} · {String(row.position)}</small></span>
    ) },
    { key: "realNwrRankAtTimeOfPick", label: "Real NWR Rank (at pick)", sort: "number" },
    { key: "teamScoreAfter", label: "Team Score — proxy", sort: "number", render: (row) => row.teamScoreAfter == null ? "—" : formatNumber(row.teamScoreAfter as number, 1) },
    { key: "champEquityAfter", label: "Champ Eq — proxy", sort: "number", render: (row) => row.champEquityAfter == null ? "—" : `${formatNumber((row.champEquityAfter as number) * 100, 1)}%` },
    { key: "topCandidateAlternatives", label: "Alternatives", sort: "text" },
    { key: "productionNwrRecommendation", label: "NWR Recommendation", sort: "text" },
  ];
  return (
    <>
      <Panel
        title={replay.label}
        eyebrow="Owner-test preview only — never the current draft. Do NOT judge historical accuracy from this pass (see the owner test checklist)."
      >
        <p className="boundary-note">{replay.disclosedLimitations}</p>
        <p className="boundary-note">Source: {replay.sourceRelativePath} (read-only, never regenerated by this page).</p>
      </Panel>
      <Panel title="Real KHA picks, with disclosed proxy values" eyebrow={`${replay.picks.length} picks`}>
        <DataTable columns={columns} rows={replay.picks as unknown as Array<Record<string, unknown>>} rowKey={(row) => String(row.pickNumber)} />
      </Panel>
    </>
  );
}

interface QueueRow {
  playerId: string;
  playerName: string;
  position: string;
  team: string;
  nwrRank: number | null;
}

/** First-class Queue -- a proven-absent capability (audited before being
 * added, see the comment on `queuedIds` in DraftRoomV2Page). Session-local
 * only: it never mutates the draft board, and Draft here calls the same
 * real markDrafted/ingestSleeperDraftPick path as every other Draft button
 * in this room. */
function QueueTab({
  rows,
  canRecordPick,
  working,
  onDraft,
  onRemove,
}: {
  rows: QueueRow[];
  canRecordPick: boolean;
  working: string;
  onDraft: (playerId: string) => void;
  onRemove: (playerId: string) => void;
}) {
  if (rows.length === 0) {
    return (
      <EmptyState
        icon="activity"
        title="Queue is empty"
        message="Queue a player from Suggestions, Rankings, or the Quick pick box above to track it here without drafting it yet."
      />
    );
  }
  return (
    <Panel title="Queue" eyebrow={`${rows.length} queued — session-local, never affects the draft board until you Draft`}>
      <DataTable
        columns={[
          { key: "nwrRank", label: "NWR", sort: "number", render: (row) => row.nwrRank == null ? "—" : String(row.nwrRank) },
          { key: "playerName", label: "Player", sort: "text", render: (row) => (
            <span className="player-cell"><strong>{String(row.playerName)}</strong><small>{String(row.team)} · {String(row.position)}</small></span>
          ) },
          { key: "actions", label: "", align: "right", render: (row) => (
            <span className="draft-room-v2-pick-actions">
              <Button data-draft-action disabled={!canRecordPick || Boolean(working)} variant="primary" onClick={() => onDraft(String(row.playerId))}>
                {working === String(row.playerId) ? "Saving…" : "Draft"}
              </Button>
              <Button variant="ghost" onClick={() => onRemove(String(row.playerId))}>Remove</Button>
            </span>
          ) },
        ]}
        rows={rows as unknown as Array<Record<string, unknown>>}
        rowKey={(row) => String(row.playerId)}
      />
    </Panel>
  );
}

function PlayerDrawer({
  playerId,
  ranking,
  intel,
  candidate,
  staleAlertData,
  onClose,
}: {
  playerId: string;
  ranking: RedraftBootstrap["rankings"][number] | undefined;
  intel: RedraftExternalIntelligenceEntry | undefined;
  candidate: DecisionBundleCandidate | undefined;
  staleAlertData: boolean;
  onClose: () => void;
}) {
  return (
    <aside className="player-drawer" role="dialog" aria-label={`${ranking?.playerName ?? playerId} detail`}>
      <div className="player-drawer__header">
        <strong>{ranking?.playerName ?? candidate?.playerName ?? playerId}</strong>
        <Button variant="ghost" onClick={onClose}>Close</Button>
      </div>
      <section>
        <h3>NWR</h3>
        <p>Rank #{ranking?.overallRank ?? "—"} · {ranking?.overallTierLabel ?? "—"}</p>
        <p>Player Score: {candidate?.playerScore != null ? formatNumber(candidate.playerScore, 1) : ranking ? formatNumber(ranking.replacementAdjustedValue, 1) : "—"}</p>
      </section>
      <section>
        <h3>Draft</h3>
        <p>Market ADP: {ranking?.overallAdp != null ? formatNumber(ranking.overallAdp, 1) : "—"}</p>
        <p>Expected round: {ranking?.expectedRound ?? "—"}</p>
        <p>Cost of Waiting: {candidate ? formatNumber(candidate.costOfWaiting, 1) : "Not evaluated as a current Suggestions candidate."}</p>
        <p>Make-It-Back: {candidate?.makeItBackProbability != null ? `${formatNumber(candidate.makeItBackProbability * 100, 0)}%` : "UNKNOWN"}</p>
      </section>
      <section>
        <h3>Roster Impact — Pick Score EXPERIMENTAL / Team Score &amp; Championship Equity RESEARCH</h3>
        {candidate ? (
          <>
            <p>Team Score Delta: {candidate.teamScoreDelta >= 0 ? "+" : ""}{formatNumber(candidate.teamScoreDelta, 1)}</p>
            <p>Championship Equity Gain: {candidate.equityGain >= 0 ? "+" : ""}{formatNumber(candidate.equityGain * 100, 2)} pp</p>
            <p>Pick Score — EXPERIMENTAL: {formatNumber(candidate.pickScore, 1)}</p>
            <p>Raw Decision Utility: {formatNumber(candidate.rawDecisionUtility, 2)} (Team Score component {formatNumber(candidate.teamScoreUtilityComponent, 2)} + Equity component {formatNumber(candidate.equityUtilityComponent, 2)})</p>
            <p>Action: <StatusBadge tone={actionToBadgeTone(candidate.action)} label={candidate.action} /></p>
            <p>Uncertainty: {candidate.uncertainty}</p>
            {candidate.warnings.length > 0 ? (
              <ul className="drawer-warnings">
                {candidate.warnings.map((warning) => <li key={warning}>{warning}</li>)}
              </ul>
            ) : null}
          </>
        ) : (
          <p className="boundary-note">
            Not among the top ranked Suggestions candidates this pick — Team Score / Championship
            Equity impact is only computed for the actionable candidates the backend evaluated. See
            the Suggestions tab.
          </p>
        )}
      </section>
      <section>
        <h3>Current</h3>
        {intel?.currentAlert ? (
          <p><StatusBadge tone={severityToBadgeTone(intel.currentAlertSeverity)} label={intel.currentAlertSeverity ?? "Alert"} /> {intel.currentAlert}</p>
        ) : (
          <p>No current alert on file.{staleAlertData ? " (Snapshot is stale -- see below. Absence of an alert here is not confirmed absence of news.)" : ""}</p>
        )}
        {staleAlertData ? <p className="boundary-note">STALE ALERT DATA — this player's alert fields come from an aging local snapshot; treat a quiet alert as unconfirmed, not as cleared.</p> : null}
        {intel?.udkPositionRank ? <p>UDK position rank: {intel.udkPositionRank} (tier {intel.udkTier ?? "—"})</p> : null}
        {intel?.fantasyProsEcr ? <p>FantasyPros ECR: {intel.fantasyProsEcr}</p> : null}
      </section>
    </aside>
  );
}
