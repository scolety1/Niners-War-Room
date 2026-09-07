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
  AdpStatus,
  DecisionBundle,
  DecisionBundleCandidate,
  DraftBoard,
  DraftPick,
  DraftRosterPlayer,
  DraftTeam,
  KhaHistoricalReplayPreview,
  LeagueProfile,
  RedraftBootstrap,
  RedraftExternalIntelligence,
  RedraftExternalIntelligenceEntry,
  RosterSettings,
} from "@nwr/contracts";
import {
  Button,
  DataTable,
  EmptyState,
  Icon,
  PageHeader,
  Panel,
  SearchInput,
  SelectField,
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
  if (tab === "BOARD") return "Draft Board";
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
  makeItBackTrials: number | null;
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
        makeItBackTrials: candidate.makeItBackTrials,
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

/**
 * Owner-test follow-up, section 3: Make-It-Back's real trial count is a
 * SMALL Monte Carlo sample (the FAST preset's `trials`) -- a candidate
 * "surviving" every simulated continuation shows a real, correctly
 * computed 100%, but that is a modeled estimate over N runs, never a
 * guarantee of real-world availability. This never changes the number;
 * it only labels what a bare "100%" would otherwise overstate.
 */
/**
 * Owner-test follow-up, section 12: round.pick display (e.g. "7.09")
 * instead of a bare overall pick number, throughout the current-pick
 * context, board cells, and recent picks. Overall pick numbers are never
 * discarded -- callers keep them for sorting/tooltips; this is display
 * only. `pickInRound` is zero-padded to two digits per the owner's own
 * examples ("4.11", not "4.1").
 */
export function formatRoundPick(overallPick: number, teamCount: number): string {
  const n = Math.max(1, teamCount);
  const round = Math.floor((overallPick - 1) / n) + 1;
  const pickInRound = ((overallPick - 1) % n) + 1;
  return `${round}.${String(pickInRound).padStart(2, "0")}`;
}

export function formatMakeItBack(probability: number | null, trials: number | null): { text: string; title: string } {
  if (probability == null) {
    return { text: "UNKNOWN", title: "Not evaluated -- no real market ADP or simulation available for this candidate." };
  }
  const pct = formatNumber(probability * 100, 0);
  if (trials == null) {
    return { text: `${pct}%`, title: "Modeled estimate; trial count not available for this source." };
  }
  if (probability >= 0.999) {
    return { text: `${pct}%*`, title: `Survived all ${trials} simulated continuations -- a real modeled estimate, not a guarantee of real-world availability.` };
  }
  return { text: `${pct}%`, title: `Modeled estimate across ${trials} simulated continuations.` };
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

/**
 * Roster-strip counts for an arbitrary roster against real configured
 * requirements -- the shared core `buildRosterStrip` (my team, from
 * `board.myRoster`) and the right-hand roster pane's per-team dropdown
 * (any team's `team.roster`) both reuse this one function rather than
 * two copies of the same capping arithmetic. Includes Superflex only
 * when the league actually configures one (owner feedback section 10:
 * "FLEX/Superflex") -- never shown as a fabricated 0/0 row for a
 * single-QB league.
 */
export function buildRosterStripFromRoster(
  roster: Pick<DraftRosterPlayer, "position">[],
  req: RosterSettings,
): RosterStripSlot[] {
  const counts: Record<string, number> = {};
  for (const player of roster) counts[player.position] = (counts[player.position] ?? 0) + 1;
  const capped = (pos: string, need: number) => Math.min(counts[pos] ?? 0, need);
  const qb = capped("QB", req.qb), rb = capped("RB", req.rb), wr = capped("WR", req.wr), te = capped("TE", req.te);
  const k = capped("K", req.k), dst = capped("DST", req.dst);
  const flexPool = Math.max(0, (counts.RB ?? 0) - rb) + Math.max(0, (counts.WR ?? 0) - wr) + Math.max(0, (counts.TE ?? 0) - te);
  const flex = Math.min(flexPool, req.flex);
  const superflexPool = Math.max(0, (counts.QB ?? 0) - qb) + Math.max(0, flexPool - flex);
  const superflex = req.superflex > 0 ? Math.min(superflexPool, req.superflex) : 0;
  const starterSlotsFilled = qb + rb + wr + te + flex + superflex + k + dst;
  const bench = Math.min(Math.max(0, roster.length - starterSlotsFilled), req.benchSize);
  const slots: RosterStripSlot[] = [
    { label: "QB", have: qb, need: req.qb }, { label: "RB", have: rb, need: req.rb },
    { label: "WR", have: wr, need: req.wr }, { label: "TE", have: te, need: req.te },
    { label: "FLEX", have: flex, need: req.flex },
  ];
  if (req.superflex > 0) slots.push({ label: "SFLX", have: superflex, need: req.superflex });
  slots.push(
    { label: "K", have: k, need: req.k }, { label: "DST", have: dst, need: req.dst },
    { label: "BN", have: bench, need: req.benchSize },
  );
  return slots;
}

export function buildRosterStrip(data: RedraftBootstrap): RosterStripSlot[] {
  const profile = data.activeProfile;
  const board = data.draftBoard;
  if (!profile || !board) return [];
  return buildRosterStripFromRoster(board.myRoster ?? [], profile.roster);
}

/**
 * One drafted player assigned to one named starter slot (or bench) --
 * NOT the same computation as the backend's value-optimized
 * `_select_starting_lineup` (shadow_numeric_authorities_service.py),
 * which needs per-player Team Score value that opponent rosters don't
 * carry to the frontend. This is a real, legal, deterministic
 * assignment (fills required positions first, then FLEX/Superflex from
 * the real remaining FLEX/Superflex-eligible players, in real draft
 * order) -- disclosed as draft-order-based, not value-optimal. FLEX and
 * Superflex never duplicate a player into two slots. Shared by the
 * right-hand roster pane and the Draft Board's "By Roster" view so both
 * surfaces agree.
 */
export interface RosterSlotAssignment {
  label: string;
  player: DraftRosterPlayer | null;
}

const FLEX_ELIGIBLE = new Set(["RB", "WR", "TE"]);
const SUPERFLEX_ELIGIBLE = new Set(["QB", "RB", "WR", "TE"]);

export function assignRosterSlots(
  roster: DraftRosterPlayer[],
  req: RosterSettings,
): { starters: RosterSlotAssignment[]; bench: DraftRosterPlayer[] } {
  const ordered = [...roster].sort((a, b) => a.pickNumber - b.pickNumber);
  const used = new Set<string>();
  const take = (predicate: (player: DraftRosterPlayer) => boolean): DraftRosterPlayer | null => {
    const found = ordered.find((player) => !used.has(player.playerId) && predicate(player));
    if (found) used.add(found.playerId);
    return found ?? null;
  };
  const starters: RosterSlotAssignment[] = [];
  const fillPosition = (label: string, position: string, count: number) => {
    for (let i = 0; i < count; i += 1) starters.push({ label, player: take((player) => player.position === position) });
  };
  fillPosition("QB", "QB", req.qb);
  fillPosition("RB", "RB", req.rb);
  fillPosition("WR", "WR", req.wr);
  fillPosition("TE", "TE", req.te);
  for (let i = 0; i < req.flex; i += 1) starters.push({ label: "FLEX", player: take((player) => FLEX_ELIGIBLE.has(player.position)) });
  for (let i = 0; i < req.superflex; i += 1) starters.push({ label: "SFLX", player: take((player) => SUPERFLEX_ELIGIBLE.has(player.position)) });
  fillPosition("K", "K", req.k);
  fillPosition("DST", "DST", req.dst);
  const bench = ordered.filter((player) => !used.has(player.playerId));
  return { starters, bench };
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
  makeItBackTrials: number | null;
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
        makeItBackTrials: candidate?.makeItBackTrials ?? null,
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
  globalSidebarCollapsed,
  onToggleGlobalSidebarCollapsed,
}: {
  client: NwrApiClient;
  data: RedraftBootstrap;
  onUpdate: (data: RedraftBootstrap) => void;
  // Owner feedback (finishing pass): "maximum horizontal room during a
  // live draft" -- an obvious toggle for the GLOBAL NWR sidebar lives
  // here, in the Draft Room header, even though the collapse state itself
  // is owned by RedraftApp/AppShell (see components.tsx) so it also
  // persists correctly if the owner leaves and returns to Draft Room.
  globalSidebarCollapsed?: boolean;
  onToggleGlobalSidebarCollapsed?: () => void;
}) {
  const [tab, setTab] = useState<DraftRoomV2Tab>("SUGGESTIONS");
  // Secondary-tools popover (Rankings/Queue/Teams/Compare/Historical
  // Replay) -- replaces the old permanent vertical secondary column
  // (owner feedback: "defeats the information-density goal").
  const [secondaryMenuOpen, setSecondaryMenuOpen] = useState(false);
  // P0 owner-workflow rescue, section 6: a real left utility pane
  // (Rankings/Teams/Queue) -- narrow, collapsible, but showing actual
  // inline content, not just a chip that switches away from the main
  // workspace. Reuses PlayersTab/MyTeamTab/QueueTab verbatim; only where
  // they render changed.
  const [leftPaneCollapsed, setLeftPaneCollapsed] = useState(false);
  const [leftPaneTab, setLeftPaneTab] = useState<"PLAYERS" | "MY_TEAM" | "QUEUE">("PLAYERS");
  // Owner feedback closure, sections 9-10: the right-hand roster pane
  // defaults to MY TEAM (null = owner's own team, resolved where it's
  // rendered) and is independently collapsible from the left pane.
  // Selecting a different team here is purely a display change -- it
  // never touches activeProfileId, board.ownerSlot, or any recommendation
  // call, so switching to inspect an opponent cannot alter the owner's
  // own draft, identity, or Suggestions.
  const [rightPaneCollapsed, setRightPaneCollapsed] = useState(false);
  const [selectedTeamSlot, setSelectedTeamSlot] = useState<number | null>(null);
  // Owner-test follow-up, section 8: an explicit Suggestions position
  // filter re-queries the backend for REAL eligible players of that
  // position (see decision_bundle_live_service.py's position_filter),
  // never a client-side re-filter of the default top-8 slice.
  const [suggestionsPositionFilter, setSuggestionsPositionFilter] = useState("ALL");
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

  // Owner feedback closure, section 17: the exact same real,
  // already-working ADP controls Legacy's Room Controls panel calls
  // (client.refreshRedraftAdp / client.importRedraftAdp) -- ported
  // verbatim so ordinary mock setup or market import never requires a
  // trip to Legacy. Refreshing/importing ADP is market-timing context
  // only; it never changes NWR's own rank (same disclosure Legacy shows).
  const [roomControlsOpen, setRoomControlsOpen] = useState(false);
  const refreshAdp = async () => {
    if (!data.activeProfileId) return;
    setWorking("adp-refresh");
    setMutationError(null);
    try {
      onUpdate(await client.refreshRedraftAdp(data.activeProfileId));
    } catch (reason) {
      setMutationError(reason instanceof NwrApiError ? reason : new NwrApiError("Fantasy Football Calculator ADP could not be refreshed."));
    } finally {
      setWorking("");
    }
  };
  const importAdp = async (file: File | undefined) => {
    if (!file || !data.activeProfileId) return;
    setWorking("adp-import");
    setMutationError(null);
    try {
      const csvText = await file.text();
      onUpdate(await client.importRedraftAdp(data.activeProfileId, csvText));
    } catch (reason) {
      setMutationError(reason instanceof NwrApiError ? reason : new NwrApiError(`${file.name} could not be imported.`));
    } finally {
      setWorking("");
    }
  };

  // P0 owner-workflow rescue: the Legacy Draft Room's own start/restart
  // control (client.startDraftRoom), ported here verbatim -- same call,
  // same semantics, so the consolidated room is self-contained and never
  // requires opening Legacy to choose a slot or (re)start a mock. A
  // second call with the board already configured genuinely IS restart
  // (Legacy's own button already reads "Restart draft" in that case) --
  // gated here behind an in-app confirmation strip (never a native
  // window.confirm(), which can freeze automated/embedded browser
  // sessions) whenever real picks already exist.
  const [setupSlot, setSetupSlot] = useState(String(data.activeProfile?.draft.draftSlot ?? 1));
  const [setupMode, setSetupMode] = useState<"MOCK" | "LIVE_READ_ONLY">("MOCK");
  const [setupSpeed, setSetupSpeed] = useState<"FAST" | "NORMAL" | "STEP">("NORMAL");
  const [restartConfirming, setRestartConfirming] = useState(false);
  const draftedCount = board?.drafted?.length ?? 0;

  const startOrRestart = async () => {
    if (!data.activeProfileId) return;
    const slot = Number(setupSlot);
    setWorking("start");
    setMutationError(null);
    try {
      onUpdate(await client.startDraftRoom(data.activeProfileId, slot, setupSpeed, 20260817, setupMode));
      setRestartConfirming(false);
    } catch (reason) {
      setMutationError(reason instanceof NwrApiError ? reason : new NwrApiError("The draft could not be started."));
    } finally {
      setWorking("");
    }
  };

  const onRestartClick = () => {
    if (draftedCount > 0 && !restartConfirming) {
      setRestartConfirming(true);
      return;
    }
    void startOrRestart();
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
      .getRedraftDecisionBundle(data.activeProfileId, "FAST", suggestionsPositionFilter === "ALL" ? undefined : suggestionsPositionFilter)
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
  }, [client, data.activeProfileId, rosterStateSignal, suggestionsPositionFilter]);

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
        description=""
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
            {onToggleGlobalSidebarCollapsed ? (
              <Button
                variant="ghost"
                onClick={onToggleGlobalSidebarCollapsed}
                title="Collapses the global NWR navigation to a narrow icon rail for maximum horizontal room during a live draft."
              >
                {globalSidebarCollapsed ? "Expand nav" : "Collapse nav"}
              </Button>
            ) : null}
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
        <CompactOnClockRow
          board={board}
          teamCount={data.activeProfile.teamCount}
          onUndo={() => void undo()}
          undoWorking={working === "undo"}
          onRestartClick={onRestartClick}
          restartConfirming={restartConfirming}
          onConfirmRestart={() => void startOrRestart()}
          onCancelRestart={() => setRestartConfirming(false)}
          restartWorking={working === "start"}
        />
      ) : null}
      {board?.configured ? (
        <RoomControls
          open={roomControlsOpen}
          onToggle={() => setRoomControlsOpen((value) => !value)}
          adp={board.adp}
          working={working}
          onRefreshAdp={() => void refreshAdp()}
          onImportAdp={(file) => void importAdp(file)}
        />
      ) : null}
      {!board?.configured ? (
        <DraftSetupPanel
          teamCount={data.activeProfile.teamCount}
          slot={setupSlot}
          onSlotChange={setSetupSlot}
          mode={setupMode}
          onModeChange={setSetupMode}
          speed={setupSpeed}
          onSpeedChange={setSetupSpeed}
          onStart={() => void startOrRestart()}
          working={working === "start"}
        />
      ) : null}
      <div className="draft-room-v2-quickpick">
        <span className="draft-room-v2-quickpick__label">Search</span>
        <label className="search-input draft-room-v2-quickpick__input">
          <Icon name="search" size={16} />
          <input
            aria-activedescendant={quickResults[quickActiveIndex] ? `quick-result-${quickActiveIndex}` : undefined}
            aria-controls="quick-capture-results"
            aria-label="Quick pick"
            disabled={!canRecordPick}
            onChange={(event) => { setQuickQuery(event.target.value); setQuickIndex(0); }}
            onFocus={(event) => event.target.select()}
            onKeyDown={onQuickKeyDown}
            placeholder="Search any player (e.g. Puka, Stafford, QB, SF)…"
            ref={quickInputRef}
            title={canRecordPick ? "Position filter ignored. Arrows/Tab to choose, Enter to record." : "Start the draft, and wait for your turn, to record picks here."}
            type="search"
            value={quickQuery}
          />
        </label>
        {quickResults.length > 0 ? (
          <ul className="rapid-capture__results draft-room-v2-quickpick__results" id="quick-capture-results" role="listbox">
            {quickResults.map((candidate, index) => (
              <li
                aria-selected={index === quickActiveIndex}
                className={index === quickActiveIndex ? "rapid-capture__result--active" : ""}
                id={`quick-result-${index}`}
                key={candidate.playerId}
                role="option"
              >
                <span
                  className="draft-room-v2-quickpick__name"
                  onClick={() => setDrawerPlayerId(candidate.playerId)}
                  title="Click for player detail"
                >
                  <strong>{candidate.playerName}</strong>
                  <small>{candidate.team} · {candidate.position}</small>
                </span>
                {/* P0 owner-workflow rescue, section 4/11: explicit
                    Draft/Queue/Detail buttons -- no mousedown-anywhere-
                    drafts, no keyboard-only path to actually record a
                    pick from search. */}
                <span className="rapid-capture__actions">
                  <Button
                    data-draft-action
                    disabled={!canRecordPick || Boolean(working)}
                    variant="primary"
                    onClick={() => void recordFromQuickCapture(candidate.playerId)}
                  >
                    {working === candidate.playerId ? "Saving…" : "Draft"}
                  </Button>
                  <Button variant="ghost" onClick={() => toggleQueue(candidate.playerId)}>
                    {queuedIds.includes(candidate.playerId) ? "Queued" : "Queue"}
                  </Button>
                </span>
              </li>
            ))}
          </ul>
        ) : null}
        {quickQuery.trim() && !quickResults.length ? <p className="draft-room-v2-quickpick__empty">No match in the ranked universe or manual K/DST/unmodeled pool.</p> : null}
      </div>
      <div className="draft-room-v2-tabbar">
        <nav className="draft-room-v2-tabbar__primary" aria-label="Draft Room modes">
          {DRAFT_ROOM_V2_PRIMARY_TABS.map((value) => (
            <button
              key={value}
              type="button"
              aria-pressed={tab === value}
              className={tab === value ? "draft-room-v2-htab draft-room-v2-htab--active" : "draft-room-v2-htab"}
              onClick={() => { setTab(value); setSecondaryMenuOpen(false); }}
            >
              {tabLabel(value)}
            </button>
          ))}
        </nav>
        <div className="draft-room-v2-tabbar__secondary">
          <div className="draft-room-v2-more">
            <button
              type="button"
              aria-expanded={secondaryMenuOpen}
              aria-haspopup="menu"
              className={secondaryMenuOpen || tab === "COMPARE" || tab === "REPLAY" ? "draft-room-v2-chip draft-room-v2-chip--active" : "draft-room-v2-chip"}
              onClick={() => setSecondaryMenuOpen((value) => !value)}
            >
              More
              {compareIds.length > 0 ? <b className="draft-room-v2-tab__badge">{compareIds.length}</b> : null}
              <Icon name="chevron" size={11} />
            </button>
            {secondaryMenuOpen ? (
              <div className="draft-room-v2-more__menu" role="menu">
                {(["COMPARE", "REPLAY"] as const).map((value) => (
                  <button key={value} role="menuitem" type="button" onClick={() => { setTab(value); setSecondaryMenuOpen(false); }}>
                    {tabLabel(value)}
                    {value === "COMPARE" && compareIds.length > 0 ? <b className="draft-room-v2-tab__badge">{compareIds.length}</b> : null}
                  </button>
                ))}
              </div>
            ) : null}
          </div>
        </div>
      </div>
      <div className="draft-room-v2-workspace">
        <LeftUtilityPane
          collapsed={leftPaneCollapsed}
          onToggleCollapsed={() => setLeftPaneCollapsed((value) => !value)}
          activeTab={leftPaneTab}
          onTabChange={setLeftPaneTab}
          queuedCount={queuedRows.length}
          data={data}
          intelById={intelById}
          onPlayerClick={onPlayerClick}
          myTeam={myTeam}
          currentScores={currentScores}
          teams={board?.teams ?? []}
          queueRows={queuedRows}
          canRecordPick={canRecordPick}
          working={working}
          onDraft={(playerId) => void mark(playerId)}
          onRemoveFromQueue={toggleQueue}
          selectedTeamSlot={selectedTeamSlot}
          onSelectTeam={setSelectedTeamSlot}
        />
      <div className="draft-room-v2-content">
        {tab === "SUGGESTIONS" ? (
          <SuggestionsTab
            rows={suggestions}
            onPlayerClick={onPlayerClick}
            decisionBundle={decisionBundle}
            loading={decisionBundleLoading}
            positionDemand={positionDemand}
            closeCall={closeCall}
            canRecordPick={canRecordPick}
            working={working}
            queuedIds={queuedIds}
            onDraft={(playerId) => void mark(playerId)}
            onQueue={toggleQueue}
            externalIntel={externalIntel}
            positionFilter={suggestionsPositionFilter}
            onPositionFilterChange={setSuggestionsPositionFilter}
            manualAssets={data.manualAssets ?? []}
            currentPick={board?.currentPick ?? null}
            teamCount={data.activeProfile?.teamCount ?? null}
          />
        ) : null}
        {tab === "CHEAT_SHEET" ? <CheatSheetPage data={data} /> : null}
        {tab === "BOARD" ? (
          <BoardTab
            board={board}
            profile={data.activeProfile}
            onPlayerClick={onPlayerClick}
            canRecordPick={canRecordPick}
            working={working}
            onDraft={(playerId) => void mark(playerId)}
            quickQuery={quickQuery}
            onQuickQueryChange={(value) => { setQuickQuery(value); setQuickIndex(0); }}
            quickResults={quickResults}
          />
        ) : null}
        {tab === "COMPARE" ? (
          <CompareTab
            rows={compareRows}
            summary={compareSummary}
            onRemove={(playerId) => setCompareIds((current) => current.filter((id) => id !== playerId))}
            currentPick={board?.currentPick ?? null}
            teamCount={data.activeProfile?.teamCount ?? null}
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
      <RightRosterPane
        collapsed={rightPaneCollapsed}
        onToggleCollapsed={() => setRightPaneCollapsed((value) => !value)}
        teams={board?.teams ?? []}
        rosterSettings={data.activeProfile?.roster ?? null}
        selectedTeamSlot={selectedTeamSlot}
        onSelectTeam={setSelectedTeamSlot}
        ownerSlot={board?.ownerSlot ?? null}
        recentPicks={board?.recentPicks ?? []}
        currentPick={board?.currentPick ?? null}
        nextOwnerPick={board?.nextOwnerPick ?? null}
        isOwnerTurn={Boolean(board?.isOwnerTurn)}
        teamCount={data.activeProfile?.teamCount ?? null}
      />
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
          currentTeamScore={decisionBundle && decisionBundle.available ? decisionBundle.currentTeamScore.percentile : null}
          staleAlertData={Boolean(externalIntel?.stale)}
          staleAlertHours={externalIntel?.snapshotAgeHours ?? null}
          canRecordPick={canRecordPick}
          working={working}
          isQueued={queuedIds.includes(drawerPlayerId)}
          onDraft={(id) => void mark(id)}
          onQueue={toggleQueue}
          onClose={() => setDrawerPlayerId(null)}
        />
      ) : null}
    </div>
  );
}

function draftRoomV2Eyebrow(board: DraftBoard | null | undefined): string {
  if (!board?.configured) return "Choose your draft slot below to begin";
  if (board.complete) return "Draft complete";
  return board.isOwnerTurn ? "You are on the clock" : `Team ${board.currentTeamSlot ?? "?"} is on the clock`;
}

/** Compact single-row current-pick context (P0 owner-workflow rescue,
 * section 7 -- the owner explicitly rejected the prior large hero: a
 * repeated league title, a big "CPU / NORMAL" clock ring, verbose
 * "Run: RB x3, WR x3" prose, and a separate big "next owner pick" card).
 * Keeps only what a 30-90 second pick decision actually needs: round,
 * overall pick, who's on the clock, snake direction, and picks-until-
 * your-turn -- plus Undo/Restart right here so they're never a scroll
 * away. The position-run detail is not deleted, just moved out of the
 * hero (Teams/position-demand already carries the same underlying
 * signal). */
function CompactOnClockRow({
  board,
  teamCount,
  onUndo,
  undoWorking,
  onRestartClick,
  restartConfirming,
  onConfirmRestart,
  onCancelRestart,
  restartWorking,
}: {
  board: DraftBoard;
  teamCount: number;
  onUndo: () => void;
  undoWorking: boolean;
  onRestartClick: () => void;
  restartConfirming: boolean;
  onConfirmRestart: () => void;
  onCancelRestart: () => void;
  restartWorking: boolean;
}) {
  const picksUntilOwner = board.nextOwnerPick && board.currentPick ? Math.max(0, board.nextOwnerPick - board.currentPick) : null;
  const round = board.currentPick ? Math.ceil(board.currentPick / Math.max(1, teamCount)) : null;
  const snakeForward = round == null ? true : round % 2 === 1;
  return (
    <section className="draft-room-v2-onclock" aria-label="Current pick context">
      <span className="draft-room-v2-onclock__pick" title={board.currentPick ? `Overall pick ${board.currentPick}` : undefined}>
        {board.currentPick != null ? formatRoundPick(board.currentPick, teamCount) : "Draft complete"}
      </span>
      <span className="draft-room-v2-onclock__status">
        {board.complete ? "Draft complete" : board.isOwnerTurn ? "YOU ARE ON THE CLOCK" : `On clock: Team ${board.currentTeamSlot ?? "?"}`}
      </span>
      {!board.isOwnerTurn && picksUntilOwner != null && !board.complete ? (
        <span className="draft-room-v2-onclock__until">YOU IN {picksUntilOwner} PICK{picksUntilOwner === 1 ? "" : "S"}</span>
      ) : null}
      <span className="draft-room-v2-onclock__snake" title={snakeForward ? "Odd rounds run 1→N" : "Even rounds run N→1"}>
        {snakeForward ? "1→N" : "N→1"}
      </span>
      <span className="draft-room-v2-onclock__spacer" />
      {restartConfirming ? (
        <span className="draft-room-v2-onclock__confirm">
          <span>Clear the board and restart?</span>
          <Button variant="danger" disabled={restartWorking} onClick={onConfirmRestart}>{restartWorking ? "Restarting…" : "Confirm"}</Button>
          <Button variant="ghost" onClick={onCancelRestart}>Cancel</Button>
        </span>
      ) : (
        <>
          <Button data-draft-undo disabled={!board.canUndo || undoWorking} icon="undo" variant="secondary" onClick={onUndo}>
            {undoWorking ? "Restoring…" : "Undo"}
          </Button>
          <Button variant="ghost" onClick={onRestartClick}>New / Restart</Button>
        </>
      )}
    </section>
  );
}

/**
 * Owner feedback closure, section 17: "keep all proven room controls...
 * do not require Legacy for ordinary mock setup or market import." This
 * is the exact real, working refresh/import pathway Legacy's own Room
 * Controls panel already calls (client.refreshRedraftAdp /
 * client.importRedraftAdp -- verified live against the real Fantasy
 * Football Calculator API, not a stub); ported verbatim, not
 * reimplemented. Less-frequent than Undo/Restart, so it lives in one
 * compact expansion rather than permanent header space.
 */
function RoomControls({
  open,
  onToggle,
  adp,
  working,
  onRefreshAdp,
  onImportAdp,
}: {
  open: boolean;
  onToggle: () => void;
  adp: AdpStatus | undefined;
  working: string;
  onRefreshAdp: () => void;
  onImportAdp: (file: File | undefined) => void;
}) {
  return (
    <section className="draft-room-v2-room-controls">
      <button type="button" className="draft-room-v2-room-controls__toggle" onClick={onToggle} aria-expanded={open}>
        Room Controls <Icon name="chevron" size={11} />
      </button>
      {open ? (
        <div className="draft-room-v2-room-controls__body">
          <Button disabled={Boolean(working)} variant="secondary" onClick={onRefreshAdp}>
            {working === "adp-refresh" ? "Refreshing…" : "Refresh FFC ADP"}
          </Button>
          <Button variant="secondary" onClick={() => { window.location.hash = "#/adp"; }}>
            Paste Rankings / ADP
          </Button>
          <label className="file-action">
            Import owner ADP CSV
            <input accept=".csv,text/csv" disabled={Boolean(working)} onChange={(event) => onImportAdp(event.target.files?.[0])} type="file" />
          </label>
          <p className="boundary-note">
            {adp?.available
              ? `${adp.source} · ${adp.dateWindow || adp.sourceDate}${adp.sampleSize ? ` · ${adp.sampleSize.toLocaleString()} drafts` : ""}. ADP is market-timing context only -- it never changes NWR rank.`
              : "No market ADP loaded yet. ADP is optional market-timing context and never changes NWR value rank."}
          </p>
        </div>
      ) : null}
    </section>
  );
}

/** P0 owner-workflow rescue, sections 1+3: a real, self-contained
 * draft-slot/mode setup control -- the consolidated room must never say
 * "go to Legacy" to start or restart a mock. Ported from pages.tsx#
 * DraftRoomPage's own "Set your draft slot" panel (same
 * client.startDraftRoom call, same MOCK/LIVE_READ_ONLY/speed options),
 * not rebuilt. Shown instead of a dead Suggestions panel whenever the
 * board is not yet configured. */
function DraftSetupPanel({
  teamCount,
  slot,
  onSlotChange,
  mode,
  onModeChange,
  speed,
  onSpeedChange,
  onStart,
  working,
}: {
  teamCount: number;
  slot: string;
  onSlotChange: (value: string) => void;
  mode: "MOCK" | "LIVE_READ_ONLY";
  onModeChange: (value: "MOCK" | "LIVE_READ_ONLY") => void;
  speed: "FAST" | "NORMAL" | "STEP";
  onSpeedChange: (value: "FAST" | "NORMAL" | "STEP") => void;
  onStart: () => void;
  working: boolean;
}) {
  return (
    <Panel title="Your draft slot" eyebrow="Choose a slot and start -- no other setup required">
      <div className="draft-room-v2-setup">
        <div className="draft-room-v2-setup__slots">
          {Array.from({ length: teamCount }, (_, index) => index + 1).map((value) => (
            <button
              key={value}
              type="button"
              aria-pressed={slot === String(value)}
              className={slot === String(value) ? "draft-room-v2-chip draft-room-v2-chip--active" : "draft-room-v2-chip"}
              onClick={() => onSlotChange(String(value))}
            >
              {value}
            </button>
          ))}
        </div>
        <SelectField
          label="Draft mode"
          value={mode}
          onChange={(value) => onModeChange(value as "MOCK" | "LIVE_READ_ONLY")}
          options={[{ value: "MOCK", label: "Practice mock (CPU opponents)" }, { value: "LIVE_READ_ONLY", label: "Live (I enter every real pick)" }]}
        />
        {mode === "MOCK" ? (
          <SelectField
            label="CPU speed"
            value={speed}
            onChange={(value) => onSpeedChange(value as "FAST" | "NORMAL" | "STEP")}
            options={[{ value: "FAST", label: "Fast" }, { value: "NORMAL", label: "Normal" }, { value: "STEP", label: "Step" }]}
          />
        ) : null}
        <Button disabled={working} variant="primary" onClick={onStart}>
          {working ? "Starting…" : "Start Mock"}
        </Button>
      </div>
    </Panel>
  );
}

function SuggestionsTab({
  rows,
  onPlayerClick,
  decisionBundle,
  loading,
  positionDemand,
  closeCall,
  canRecordPick,
  working,
  queuedIds,
  onDraft,
  onQueue,
  externalIntel,
  positionFilter,
  onPositionFilterChange,
  manualAssets,
  currentPick,
  teamCount,
}: {
  rows: SuggestionRow[];
  onPlayerClick: (playerId: string, event: React.MouseEvent) => void;
  decisionBundle: DecisionBundle | null;
  loading: boolean;
  positionDemand: PositionDemandRow[];
  closeCall: { a: SuggestionRow; b: SuggestionRow } | null;
  canRecordPick: boolean;
  working: string;
  queuedIds: string[];
  onDraft: (playerId: string) => void;
  onQueue: (playerId: string) => void;
  externalIntel: RedraftExternalIntelligence | null;
  positionFilter: string;
  onPositionFilterChange: (value: string) => void;
  manualAssets: RedraftBootstrap["manualAssets"];
  currentPick: number | null;
  teamCount: number | null;
}) {
  const [newsDetailOpen, setNewsDetailOpen] = useState(false);
  const [closeCallDetailOpen, setCloseCallDetailOpen] = useState(false);
  const isManualPosition = positionFilter === "K" || positionFilter === "DST";
  const manualRows = isManualPosition
    ? (manualAssets ?? []).filter((row) => row.position === positionFilter)
    : [];
  // Compact primary table (owner feedback: headers must read as drafting
  // chrome, not research-development labels). Evidence status
  // (EXPERIMENTAL/RESEARCH/SIMULATED RESEARCH) moves to a header hover
  // tooltip (titleHint) rather than living in the visible label -- the
  // exact same underlying real, unmodified fields, never removed, always
  // still one click away in the player drawer.
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
    { key: "playerName", label: "Player", sort: "text", render: (row) => (
      <span
        className="player-cell player-cell--clickable"
        onClick={(event) => onPlayerClick(String(row.playerId), event as unknown as React.MouseEvent)}
        title="Click for Score Details / Why"
      >
        <strong>
          {row.alertText ? (
            <i
              className={`draft-room-v2-alert-dot draft-room-v2-alert-dot--${severityToBadgeTone(row.alertSeverity as string | null)}`}
              title={`${String(row.alertSeverity ?? "Alert")}: ${String(row.alertText)}`}
            />
          ) : null}
          {String(row.playerName)}
        </strong>
        <small>{String(row.team)} · {String(row.position)}</small>
      </span>
    ) },
    { key: "pickScore", label: "Pick Score", titleHint: "Pick Score — EXPERIMENTAL: the historically-validated but not yet independently audited combined recommendation.", sort: "number", render: (row) => formatNumber(row.pickScore as number, 1) },
    { key: "teamScoreAfter", label: "Team After", titleHint: "Team Score — RESEARCH. 'After' projects a full-draft completion assuming this pick now; the (Δ) in parentheses reflects this pick PLUS the rest of the draft playing out, not an isolated single-pick value. See player detail for current→after.", sort: "number", render: (row) => (
      <span>{formatNumber(row.teamScoreAfter as number, 1)} ({row.teamScoreDelta as number >= 0 ? "+" : ""}{formatNumber(row.teamScoreDelta as number, 1)})</span>
    ) },
    { key: "championshipEquityAfter", label: "Equity Δ", titleHint: "Championship Equity — SIMULATED RESEARCH. Percentage-point change from this pick.", sort: "number", render: (row) => (
      <span title={`${formatNumber((row.championshipEquityAfter as number) * 100, 1)}% after this pick`}>{row.equityGain as number >= 0 ? "+" : ""}{formatNumber((row.equityGain as number) * 100, 1)} pp</span>
    ) },
    { key: "makeItBackProbability", label: "Make Back", titleHint: "Make-It-Back: modeled probability this player survives to your next pick if you wait. 100%* means it survived every simulated continuation -- a real estimate, not a guarantee.", sort: "number", render: (row) => {
      const mib = formatMakeItBack(row.makeItBackProbability as number | null, row.makeItBackTrials as number | null);
      return <span title={mib.title}>{mib.text}</span>;
    } },
    { key: "decisionQualityPercentile", label: "DQ", titleHint: "Decision Quality — Raw Action Value: differentiates candidates even when Pick Score ties (0-100). Hover a value for expected regret.", sort: "number", render: (row) => {
      const status = row.rawActionValueStatus as string | null;
      if (row.decisionQualityPercentile == null) return status === "SKIPPED_TOP_N_ONLY" ? <span title="Outside this pick's cost-controlled Raw Action Value candidate set.">n/a</span> : (status ?? "n/a");
      return <span title={`Expected regret: ${row.expectedRegret != null ? formatNumber(row.expectedRegret as number, 1) : "—"}`}>{formatNumber(row.decisionQualityPercentile as number, 0)}</span>;
    } },
    { key: "playerScore", label: "Player Score", sort: "number", render: (row) => row.playerScore == null ? "—" : formatNumber(row.playerScore as number, 1) },
    { key: "marketExpectedPick", label: "ADP", sort: "number", render: (row) => row.marketExpectedPick == null ? "—" : formatNumber(row.marketExpectedPick as number, 1) },
    { key: "action", label: "Action", titleHint: "What to do -- reuses the existing real Cost-of-Waiting/ADP-timing labels, split from Value below.", sort: "text", render: (row) => {
      const split = splitActionValue(String(row.action), row.nwrRank as number | null, row.marketExpectedPick as number | null, currentPick, teamCount);
      return <StatusBadge tone={actionToBadgeTone(String(row.action))} label={split.action} />;
    } },
    { key: "value", label: "Value", titleHint: "How the market sees this player right now (Falling/Reach = real-time draft behavior vs. cited ADP; Value = NWR ranks them meaningfully ahead of ADP; Unknown when ADP is unavailable).", sort: "text", render: (row) => {
      const split = splitActionValue(String(row.action), row.nwrRank as number | null, row.marketExpectedPick as number | null, currentPick, teamCount);
      const title = split.gapPicks != null ? `${split.gapPicks >= 0 ? "+" : ""}${split.gapPicks} picks vs. cited ADP` : "No real market ADP for this player.";
      return <span title={title}>{split.value}</span>;
    } },
  ];
  const unavailableReason = decisionBundle && !decisionBundle.available ? decisionBundle.reason : null;
  return (
    <>
      {(positionDemand.length > 0 || externalIntel?.stale || closeCall) ? (
        <div className="draft-room-v2-compact-context">
          {positionDemand.length > 0 ? (
            <div
              className="draft-room-v2-compact-context__row"
              title="Opponents who already have a full starting group at this position -- reused from the same real roster-need signal Make-It-Back/Cost of Waiting already fold into their own simulations."
            >
              {positionDemand.map((row) => (
                <span key={row.position} className="roster-slot">
                  {row.position} demand {row.filledOpponents}/{row.totalOpponents}
                </span>
              ))}
            </div>
          ) : null}
          {externalIntel?.stale ? (
            <button
              type="button"
              className="draft-room-v2-status-chip"
              aria-expanded={newsDetailOpen}
              onClick={() => setNewsDetailOpen((value) => !value)}
              title="Click for detail"
            >
              ⚠ News {externalIntel.snapshotAgeHours != null ? `${formatNumber(externalIntel.snapshotAgeHours, 0)}h` : "?"} stale
            </button>
          ) : null}
          {closeCall ? (
            <button
              type="button"
              className="draft-room-v2-status-chip"
              aria-expanded={closeCallDetailOpen}
              onClick={() => setCloseCallDetailOpen((value) => !value)}
              title="Click for detail"
            >
              CLOSE CALL: {closeCall.a.playerName} ≈ {closeCall.b.playerName}
            </button>
          ) : null}
          {newsDetailOpen && externalIntel?.stale ? (
            <p className="draft-room-v2-compact-context__detail">
              The current-alert snapshot is {externalIntel.snapshotAgeHours != null ? `${formatNumber(externalIntel.snapshotAgeHours, 1)}h` : "an unknown amount of time"} old
              {externalIntel.snapshotGeneratedAtUtc ? ` (built ${externalIntel.snapshotGeneratedAtUtc})` : ""}. A quiet player below may mean no current news, or it may mean this snapshot hasn't been refreshed since it was built — not a confirmed absence of news. A player with a real current alert on file still shows the marker next to their name regardless of this global staleness.
            </p>
          ) : null}
          {closeCallDetailOpen && closeCall ? (
            <p className="draft-room-v2-compact-context__detail">
              {closeCall.a.playerName} ({formatNumber(closeCall.a.pickScore, 1)}) and {closeCall.b.playerName} ({formatNumber(closeCall.b.pickScore, 1)}) have nearly
              identical Pick Score — EXPERIMENTAL. The formula cannot cleanly separate them; use roster fit, Make Back, DQ, and any alert marker to break the tie.
            </p>
          ) : null}
        </div>
      ) : null}
      <Panel title="Suggestions" eyebrow="Real DecisionBundle candidates — default sorted by Pick Score, descending">
        <div className="draft-room-v2-position-filter">
          {["ALL", "QB", "RB", "WR", "TE", "K", "DST"].map((value) => (
            <button
              key={value}
              type="button"
              aria-pressed={positionFilter === value}
              className={positionFilter === value ? "draft-room-v2-chip draft-room-v2-chip--active" : "draft-room-v2-chip"}
              onClick={() => onPositionFilterChange(value)}
            >
              {value}
            </button>
          ))}
        </div>
        {isManualPosition ? (
          // NWR does not model K/DST -- never routed through DecisionBundle/
          // Team Score/Equity/Pick Score. A real, honest listing of the
          // manual asset pool with the same Draft/Queue actions instead of
          // a fabricated advanced score.
          manualRows.length === 0 ? (
            <EmptyState icon="activity" title={`No available ${positionFilter}`} message="Every manual asset at this position has already been drafted." />
          ) : (
            <DataTable
              columns={[
                { key: "playerName", label: "Player", sort: "text", render: (row) => (
                  <span className="player-cell"><strong>{String(row.playerName)}</strong><small>{String(row.team)} · {String(row.position)}</small></span>
                ) },
                { key: "authority", label: "Status", sort: "text", render: () => <StatusBadge tone="review" label="Manual · not modeled" /> },
                { key: "actions", label: "", align: "right", render: (row) => (
                  <span className="draft-room-v2-pick-actions">
                    <Button data-draft-action disabled={!canRecordPick || Boolean(working)} variant="primary" onClick={() => onDraft(String(row.playerId))}>
                      {working === String(row.playerId) ? "Saving…" : "Draft"}
                    </Button>
                    <Button variant="ghost" onClick={() => onQueue(String(row.playerId))}>{queuedIds.includes(String(row.playerId)) ? "Queued" : "Queue"}</Button>
                  </span>
                ) },
              ]}
              rows={manualRows as unknown as Array<Record<string, unknown>>}
              rowKey={(row) => String(row.playerId)}
            />
          )
        ) : loading ? (
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

/**
 * Owner-test follow-up, section 7: "Action" (what to do) and "Value"
 * (how the market sees this player right now) were conflated into one
 * label that described the player without telling the owner what to do.
 * Reuses the EXACT existing evidence -- the real `action` string
 * (label_pick_decisions -- never recomputed here) and the real NWR
 * rank / market ADP already on the row -- rather than a second scoring
 * system. Missing/stale ADP never produces a confident market label
 * (real disclosed limitation, not silently guessed).
 */
export interface ActionValueSplit {
  action: string;
  value: string;
  gapPicks: number | null;
}

export function splitActionValue(
  action: string,
  nwrRank: number | null,
  marketExpectedPick: number | null,
  currentPick: number | null,
  teamCount: number | null,
): ActionValueSplit {
  const normalized = action.toUpperCase().replace(/_/g, " ");
  const actionLabel =
    normalized === "TAKE NOW" ? "Pick now"
    : normalized === "GOOD VALUE" ? "Consider now"
    : normalized === "DEEP TARGET" ? "Queue for later"
    : normalized === "WAIT" ? "Wait until next turn"
    : normalized === "WAIVER WATCH" ? "Review data"
    : "Review data";
  if (marketExpectedPick == null || currentPick == null || teamCount == null || teamCount <= 0) {
    return { action: actionLabel, value: "Unknown", gapPicks: null };
  }
  const gapPicks = Math.round(marketExpectedPick - currentPick);
  // "Falling" / "Reach" describe THIS draft's real-time behavior (has this
  // player actually gone later/earlier than their own cited ADP so far),
  // never the NWR-vs-market rank gap -- that discount is "Value" instead,
  // a distinct, disclosed signal per the owner's own requested split.
  // gapPicks = marketExpectedPick - currentPick: very negative means the
  // player's own cited ADP has already passed and they are still on the
  // board (Falling); very positive means we are being asked to take them
  // well before their own cited ADP (Reach).
  if (-gapPicks >= teamCount) return { action: actionLabel, value: "Falling", gapPicks };
  if (gapPicks >= teamCount) return { action: actionLabel, value: "Reach", gapPicks };
  if (nwrRank != null && marketExpectedPick - nwrRank >= 10) {
    return { action: actionLabel, value: "Value", gapPicks };
  }
  return { action: actionLabel, value: "Fair", gapPicks };
}

/** P0 owner-workflow rescue, section 8: a real, narrow, collapsible
 * contextual draft pane (Rankings/Teams/Queue) beside the main workspace
 * -- not a full-page tab switch, not tiny chips with no inline content.
 * Reuses PlayersTab/MyTeamTab/QueueTab verbatim; only reachable via a
 * mini tab strip inside the pane itself. */
function LeftUtilityPane({
  collapsed,
  onToggleCollapsed,
  activeTab,
  onTabChange,
  queuedCount,
  data,
  intelById,
  onPlayerClick,
  myTeam,
  currentScores,
  teams,
  queueRows,
  canRecordPick,
  working,
  onDraft,
  onRemoveFromQueue,
  selectedTeamSlot,
  onSelectTeam,
}: {
  collapsed: boolean;
  onToggleCollapsed: () => void;
  activeTab: "PLAYERS" | "MY_TEAM" | "QUEUE";
  onTabChange: (tab: "PLAYERS" | "MY_TEAM" | "QUEUE") => void;
  queuedCount: number;
  data: RedraftBootstrap;
  intelById: Map<string, RedraftExternalIntelligenceEntry>;
  onPlayerClick: (playerId: string, event: React.MouseEvent) => void;
  myTeam: MyTeamSummary;
  currentScores: CurrentRosterScores;
  teams: DraftTeam[];
  queueRows: Array<{ playerId: string; playerName: string; position: string; team: string; nwrRank: number | null }>;
  canRecordPick: boolean;
  working: string;
  onDraft: (playerId: string) => void;
  onRemoveFromQueue: (playerId: string) => void;
  selectedTeamSlot: number | null;
  onSelectTeam: (teamSlot: number) => void;
}) {
  if (collapsed) {
    return (
      <button type="button" className="draft-room-v2-leftpane-rail" onClick={onToggleCollapsed} title="Show Rankings/Teams/Queue">
        <Icon name="chevron" size={13} />
      </button>
    );
  }
  return (
    <aside className="draft-room-v2-leftpane" aria-label="Rankings, Teams, Queue">
      <div className="draft-room-v2-leftpane__tabs">
        {(["PLAYERS", "MY_TEAM", "QUEUE"] as const).map((value) => (
          <button
            key={value}
            type="button"
            aria-pressed={activeTab === value}
            className={activeTab === value ? "draft-room-v2-chip draft-room-v2-chip--active" : "draft-room-v2-chip"}
            onClick={() => onTabChange(value)}
          >
            {value === "PLAYERS" ? "Rankings" : value === "MY_TEAM" ? "Teams" : "Queue"}
            {value === "QUEUE" && queuedCount > 0 ? <b className="draft-room-v2-tab__badge">{queuedCount}</b> : null}
          </button>
        ))}
        <button type="button" className="draft-room-v2-leftpane-collapse" onClick={onToggleCollapsed} title="Collapse this pane">
          <Icon name="chevron" size={13} />
        </button>
      </div>
      <div className="draft-room-v2-leftpane__body">
        {activeTab === "PLAYERS" ? (
          <PlayersTab
            data={data}
            intelById={intelById}
            onPlayerClick={onPlayerClick}
            compact
            canRecordPick={canRecordPick}
            working={working}
            onDraft={onDraft}
            queuedIds={queueRows.map((row) => row.playerId)}
            onQueue={onRemoveFromQueue}
          />
        ) : null}
        {activeTab === "MY_TEAM" ? (
          <TeamsPaneContent teams={teams} myTeam={myTeam} currentScores={currentScores} selectedTeamSlot={selectedTeamSlot} onSelectTeam={onSelectTeam} />
        ) : null}
        {activeTab === "QUEUE" ? (
          <QueueTab rows={queueRows} canRecordPick={canRecordPick} working={working} onDraft={onDraft} onRemove={onRemoveFromQueue} compact />
        ) : null}
      </div>
    </aside>
  );
}

/**
 * Owner feedback closure, sections 9-10: the right-hand contextual pane.
 * Defaults to MY TEAM; the dropdown lets the owner inspect ANY fantasy
 * team's real configured roster without touching the active league,
 * owner identity, draft slot, or recommendation perspective -- inspecting
 * an opponent is purely a read of `selectedTeamSlot` here, nothing else
 * in DraftRoomV2Page's state changes. Below the roster: the authoritative
 * recent-picks log (board.recentPicks, the same field Legacy's own
 * "Recent picks" panel already reads) and the real next-owner-pick /
 * picks-until-owner figures already computed on `board`.
 */
function RightRosterPane({
  collapsed,
  onToggleCollapsed,
  teams,
  rosterSettings,
  selectedTeamSlot,
  onSelectTeam,
  ownerSlot,
  recentPicks,
  currentPick,
  nextOwnerPick,
  isOwnerTurn,
  teamCount,
}: {
  collapsed: boolean;
  onToggleCollapsed: () => void;
  teams: DraftTeam[];
  rosterSettings: RosterSettings | null;
  selectedTeamSlot: number | null;
  onSelectTeam: (teamSlot: number) => void;
  ownerSlot: number | null;
  recentPicks: DraftPick[];
  currentPick: number | null;
  nextOwnerPick: number | null;
  isOwnerTurn: boolean;
  teamCount: number | null;
}) {
  if (collapsed) {
    return (
      <button type="button" className="draft-room-v2-rightpane-rail" onClick={onToggleCollapsed} title="Show Team & Recent Picks">
        <Icon name="chevron" size={13} />
      </button>
    );
  }
  const effectiveSlot = selectedTeamSlot ?? ownerSlot;
  const team = teams.find((value) => value.teamSlot === effectiveSlot) ?? teams.find((value) => value.owner) ?? null;
  const assignment = team && rosterSettings ? assignRosterSlots(team.roster, rosterSettings) : null;
  const strip = team && rosterSettings ? buildRosterStripFromRoster(team.roster, rosterSettings) : [];
  const picksUntilOwner = nextOwnerPick != null && currentPick != null ? Math.max(0, nextOwnerPick - currentPick) : null;
  return (
    <aside className="draft-room-v2-rightpane" aria-label="Team roster and recent picks">
      <div className="draft-room-v2-rightpane__header">
        <label className="draft-room-v2-rightpane__team-select">
          <span className="draft-room-v2-leftpane__label">Roster</span>
          <select
            value={effectiveSlot ?? ""}
            onChange={(event) => onSelectTeam(Number(event.target.value))}
            aria-label="Inspect team roster"
          >
            {teams.map((value) => (
              <option key={value.teamSlot} value={value.teamSlot}>
                {value.name}{value.owner ? " (You)" : ""}
              </option>
            ))}
          </select>
        </label>
        <button type="button" className="draft-room-v2-rightpane-collapse" onClick={onToggleCollapsed} title="Collapse this pane">
          <Icon name="chevron" size={13} />
        </button>
      </div>
      {strip.length > 0 ? (
        <div className="roster-strip" title="Real configured starter slots, FLEX/Superflex, K/DST and bench for this team">
          {strip.map((slot) => (
            <span key={slot.label} className={`roster-slot ${slot.have >= slot.need && slot.need > 0 ? "roster-slot--full" : ""}`}>
              {slot.label} {slot.have}/{slot.need}
            </span>
          ))}
        </div>
      ) : null}
      {assignment ? (
        <div className="draft-room-v2-rightpane__section">
          <ul className="draft-room-v2-roster-slots">
            {assignment.starters.map((slot, index) => (
              <li key={`${slot.label}-${index}`} className={slot.player ? "" : "draft-room-v2-roster-slots__empty"}>
                <span className="draft-room-v2-roster-slots__label">{slot.label}</span>
                {slot.player ? (
                  <span>
                    <strong>{slot.player.playerName}</strong>
                    <small>{slot.player.team} · {slot.player.position}</small>
                  </span>
                ) : (
                  <span className="draft-room-v2-roster-slots__placeholder">Empty</span>
                )}
              </li>
            ))}
          </ul>
          {assignment.bench.length > 0 ? (
            <>
              <span className="draft-room-v2-leftpane__label">Bench ({assignment.bench.length})</span>
              <ul className="draft-room-v2-roster-slots draft-room-v2-roster-slots--bench">
                {assignment.bench.map((player) => (
                  <li key={player.playerId}>
                    <span className="draft-room-v2-roster-slots__label">BN</span>
                    <span><strong>{player.playerName}</strong><small>{player.team} · {player.position}</small></span>
                  </li>
                ))}
              </ul>
            </>
          ) : null}
        </div>
      ) : (
        <p className="draft-room-v2-rightpane__empty">No players drafted by this team yet.</p>
      )}
      <div className="draft-room-v2-rightpane__section">
        <span className="draft-room-v2-leftpane__label">Recent picks</span>
        {recentPicks.length > 0 ? (
          <ul className="draft-room-v2-recent-picks">
            {[...recentPicks].reverse().map((pick) => (
              <li key={pick.pickNumber}>
                <span className="draft-room-v2-recent-picks__pick">{teamCount ? formatRoundPick(pick.pickNumber, teamCount) : pick.pickNumber}</span>
                <span>
                  <strong>{pick.playerName}</strong>
                  <small>{pick.position} · Team {pick.teamSlot}</small>
                </span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="draft-room-v2-rightpane__empty">No picks yet.</p>
        )}
        {nextOwnerPick != null ? (
          <p className="draft-room-v2-rightpane__next-turn">
            {isOwnerTurn
              ? "You are on the clock now."
              : `Your next pick: ${teamCount ? formatRoundPick(nextOwnerPick, teamCount) : nextOwnerPick}${picksUntilOwner != null ? ` (${picksUntilOwner} pick${picksUntilOwner === 1 ? "" : "s"} away)` : ""}`}
          </p>
        ) : null}
      </div>
    </aside>
  );
}

/** Teams pane content (section 8: "each fantasy team's compact roster,
 * positional starter fill, opponent demand/roster needs, owner
 * obvious") -- reads the same real `board.teams` roster state already
 * fetched for the board/drawer, no new backend call.
 *
 * Owner feedback closure, section 9: this list drives the SAME
 * `selectedTeamSlot` state as the right-hand roster pane -- clicking a
 * team here just changes what the right pane inspects, exactly like its
 * own dropdown. It never touches the active league, owner identity,
 * draft slot, or recommendation perspective; there is only one roster-
 * inspection system, not two.
 */
function TeamsPaneContent({
  teams,
  myTeam,
  currentScores,
  selectedTeamSlot,
  onSelectTeam,
}: {
  teams: DraftTeam[];
  myTeam: MyTeamSummary;
  currentScores: CurrentRosterScores;
  selectedTeamSlot: number | null;
  onSelectTeam: (teamSlot: number) => void;
}) {
  return (
    <>
      <div className="draft-room-v2-leftpane__section">
        <span className="draft-room-v2-leftpane__label">Your roster</span>
        <div className="roster-strip">
          {myTeam.strengths.map((label) => <span key={label} className="roster-slot roster-slot--full">{label}</span>)}
          {myTeam.holes.map((label) => <span key={label} className="roster-slot">{label}</span>)}
        </div>
        {currentScores.teamScorePercentile != null ? (
          <p className="boundary-note">Team Score: {formatNumber(currentScores.teamScorePercentile, 1)}</p>
        ) : null}
      </div>
      <div className="draft-room-v2-leftpane__section">
        <span className="draft-room-v2-leftpane__label">League teams — click to inspect in the roster pane</span>
        <ul className="draft-room-v2-teams-list">
          {teams.map((team) => {
            const counts: Record<string, number> = {};
            for (const player of team.roster) counts[player.position] = (counts[player.position] ?? 0) + 1;
            const isSelected = (selectedTeamSlot ?? teams.find((value) => value.owner)?.teamSlot) === team.teamSlot;
            return (
              <li key={team.teamSlot}>
                <button
                  type="button"
                  onClick={() => onSelectTeam(team.teamSlot)}
                  aria-pressed={isSelected}
                  className={
                    (team.owner ? "draft-room-v2-teams-list__item draft-room-v2-teams-list__item--owner" : "draft-room-v2-teams-list__item") +
                    (isSelected ? " draft-room-v2-teams-list__item--selected" : "")
                  }
                >
                  <strong>{team.name}{team.owner ? " · YOU" : ""}</strong>
                  <span>{team.roster.length} drafted{Object.entries(counts).length ? ` — ${Object.entries(counts).map(([pos, n]) => `${pos} ${n}`).join(", ")}` : ""}</span>
                </button>
              </li>
            );
          })}
        </ul>
      </div>
    </>
  );
}

function PlayersTab({
  data,
  intelById,
  onPlayerClick,
  compact = false,
  canRecordPick = false,
  working = "",
  onDraft,
  queuedIds = [],
  onQueue,
}: {
  data: RedraftBootstrap;
  intelById: Map<string, RedraftExternalIntelligenceEntry>;
  onPlayerClick: (playerId: string, event: React.MouseEvent) => void;
  compact?: boolean;
  canRecordPick?: boolean;
  working?: string;
  onDraft?: (playerId: string) => void;
  queuedIds?: string[];
  onQueue?: (playerId: string) => void;
}) {
  const [position, setPosition] = useState("ALL");
  const rows = data.rankings.filter((row) => !row.drafted && (position === "ALL" || row.position === position));
  const columns: TableColumn[] = compact
    ? [
        { key: "playerName", label: "Player", sort: "text", render: (row) => (
          <span className="player-cell player-cell--clickable" onClick={(event) => onPlayerClick(String(row.playerId), event as unknown as React.MouseEvent)}>
            <strong>#{String(row.overallRank)} {String(row.playerName)}</strong>
            <small>{String(row.team)} · {String(row.position)}</small>
          </span>
        ) },
        ...(onDraft ? [{ key: "actions", label: "", align: "right" as const, render: (row: Record<string, unknown>) => (
          <span className="draft-room-v2-pick-actions">
            <Button data-draft-action disabled={!canRecordPick || Boolean(working)} variant="primary" onClick={() => onDraft(String(row.playerId))}>
              {working === String(row.playerId) ? "…" : "Draft"}
            </Button>
            {onQueue ? <Button variant="ghost" onClick={() => onQueue(String(row.playerId))}>{queuedIds.includes(String(row.playerId)) ? "✓" : "Q"}</Button> : null}
          </span>
        ) }] : []),
      ]
    : [
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
        ...(onDraft ? [{ key: "actions", label: "", align: "right" as const, render: (row: Record<string, unknown>) => (
          <span className="draft-room-v2-pick-actions">
            <Button data-draft-action disabled={!canRecordPick || Boolean(working)} variant="primary" onClick={() => onDraft(String(row.playerId))}>
              {working === String(row.playerId) ? "Saving…" : "Draft"}
            </Button>
            {onQueue ? <Button variant="ghost" onClick={() => onQueue(String(row.playerId))}>{queuedIds.includes(String(row.playerId)) ? "Queued" : "Queue"}</Button> : null}
          </span>
        ) }] : []),
      ];
  const positionFilter = (
    <div className="draft-room-v2-position-filter">
      {["ALL", "QB", "RB", "WR", "TE", "K", "DST"].map((value) => (
        <button key={value} type="button" aria-pressed={position === value} className={position === value ? "draft-room-v2-chip draft-room-v2-chip--active" : "draft-room-v2-chip"} onClick={() => setPosition(value)}>
          {value}
        </button>
      ))}
    </div>
  );
  if (compact) {
    return (
      <div className="draft-room-v2-leftpane__section">
        {positionFilter}
        <DataTable columns={columns} rows={rows as unknown as Array<Record<string, unknown>>} rowKey={(row) => String(row.playerId)} />
      </div>
    );
  }
  return (
    <Panel title="Players" eyebrow={`${rows.length} undrafted players`}>
      {positionFilter}
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
  canRecordPick,
  working,
  onDraft,
  quickQuery,
  onQuickQueryChange,
  quickResults,
}: {
  board: DraftBoard | null | undefined;
  profile: LeagueProfile | null | undefined;
  onPlayerClick: (playerId: string, event: React.MouseEvent) => void;
  canRecordPick: boolean;
  working: string;
  onDraft: (playerId: string) => void;
  quickQuery: string;
  onQuickQueryChange: (value: string) => void;
  quickResults: PickSearchCandidate[];
}) {
  // P0 owner-workflow rescue, section 13: click the current/open pick to
  // record it directly from the board, reusing the exact same search
  // state as the main Search box (one source of truth, not a second
  // search implementation).
  const [recordingPick, setRecordingPick] = useState<number | null>(null);
  // Owner feedback closure, section 11: By Picks (chronological, existing,
  // owner-preferred) vs. By Roster (same fixed team columns, rows follow
  // real roster slots via the shared assignRosterSlots -- the same
  // deterministic legal assignment the right-hand roster pane uses, so
  // both surfaces always agree). Purely a display toggle -- it reads
  // `board`/`profile` and renders differently; it never calls a mutation.
  const [boardView, setBoardView] = useState<"BY_PICKS" | "BY_ROSTER">("BY_PICKS");
  if (!board?.boardCells || !profile) {
    return <EmptyState icon="activity" title="No draft board yet" message="Choose your draft slot and click Start above." />;
  }
  const teamCount = profile.teamCount;
  const rounds = profile.draft.rounds;
  const cellByRoundAndSlot = new Map(board.boardCells.map((cell) => [`${cell.round}-${cell.teamSlot}`, cell]));
  const openRecordable = (cell: { current?: boolean; playerId?: string } | undefined) =>
    Boolean(cell?.current && !cell.playerId && canRecordPick);
  const teams = board.teams ?? [];
  const assignmentsBySlot =
    boardView === "BY_ROSTER" ? new Map(teams.map((team) => [team.teamSlot, assignRosterSlots(team.roster, profile.roster)])) : null;
  const starterLabels = assignmentsBySlot ? assignRosterSlots([], profile.roster).starters.map((slot) => slot.label) : [];
  const benchRows = assignmentsBySlot ? Math.max(0, ...teams.map((team) => assignmentsBySlot.get(team.teamSlot)?.bench.length ?? 0)) : 0;
  return (
    <Panel
      title="Draft Board"
      eyebrow={`${teamCount} teams × ${rounds} rounds — fixed columns, scroll for wide leagues`}
      action={
        <div className="draft-room-v2-position-filter" role="group" aria-label="Board view">
          {(["BY_PICKS", "BY_ROSTER"] as const).map((value) => (
            <button
              key={value}
              type="button"
              className={boardView === value ? "draft-room-v2-chip draft-room-v2-chip--active" : "draft-room-v2-chip"}
              onClick={() => setBoardView(value)}
              aria-pressed={boardView === value}
            >
              {value === "BY_PICKS" ? "By Picks" : "By Roster"}
            </button>
          ))}
        </div>
      }
    >
      {recordingPick != null ? (
        <div className="draft-room-v2-board-record">
          <div className="draft-room-v2-board-record__header">
            <strong>Record pick {recordingPick != null ? formatRoundPick(recordingPick, teamCount) : ""}</strong>
            <Button variant="ghost" onClick={() => setRecordingPick(null)}>Close</Button>
          </div>
          <label className="search-input">
            <Icon name="search" size={16} />
            <input
              autoFocus
              onChange={(event) => onQuickQueryChange(event.target.value)}
              placeholder="Type a player, K, or D/ST…"
              type="search"
              value={quickQuery}
            />
          </label>
          <ul className="rapid-capture__results">
            {quickResults.map((candidate) => (
              <li key={candidate.playerId}>
                <span><strong>{candidate.playerName}</strong> <small>{candidate.team} · {candidate.position}</small></span>
                <Button
                  data-draft-action
                  disabled={Boolean(working)}
                  variant="primary"
                  onClick={() => { onDraft(candidate.playerId); setRecordingPick(null); onQuickQueryChange(""); }}
                >
                  {working === candidate.playerId ? "Saving…" : "Draft"}
                </Button>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
      {boardView === "BY_PICKS" ? (
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
                const recordable = openRecordable(cell);
                const onClick = cell?.playerId
                  ? (event: React.MouseEvent) => onPlayerClick(cell.playerId, event)
                  : recordable
                    ? () => setRecordingPick(cell!.pickNumber)
                    : undefined;
                return (
                  <article
                    key={`${round}-${slot}`}
                    className={`draft-board-v2-cell ${cell?.ownerPick ? "draft-board-v2-cell--owner" : ""} ${cell?.current ? "draft-board-v2-cell--current" : ""} ${recordable ? "draft-board-v2-cell--recordable" : ""}`}
                    onClick={onClick}
                    role={onClick ? "button" : undefined}
                    tabIndex={onClick ? 0 : undefined}
                    title={recordable ? "Click to record this pick" : undefined}
                  >
                    <span className="draft-board-v2-cell__pick" title={cell?.pickNumber ? `Overall pick ${cell.pickNumber}` : undefined}>
                      {cell?.pickNumber ? formatRoundPick(cell.pickNumber, teamCount) : ""}
                    </span>
                    <span className="draft-board-v2-cell__player">
                      {cell?.playerName || (cell?.status === "UNRESOLVED" ? "Unresolved" : recordable ? "Record pick" : "Open")}
                    </span>
                  </article>
                );
              }),
            ])}
          </div>
        </div>
      ) : (
        // By Roster: same fixed team columns; rows follow the real,
        // legal starter/bench slot assignment (assignRosterSlots -- the
        // SAME function the right-hand roster pane uses, so both views
        // always agree) instead of draft chronology. A pure read of
        // `board.teams`/`profile.roster`; switching here never mutates
        // the draft. FLEX/Superflex never duplicate a player -- each
        // player is consumed exactly once inside assignRosterSlots.
        <div className="draft-board-scroll">
          <div
            className="draft-board-v2-grid"
            style={{ gridTemplateColumns: `38px repeat(${teamCount}, minmax(105px, 1fr))`, minWidth: `${38 + teamCount * 111}px` }}
          >
            <div className="draft-board-v2-corner">Slot</div>
            {Array.from({ length: teamCount }, (_, index) => index + 1).map((slot) => (
              <div key={`head-${slot}`} className={slot === board.ownerSlot ? "draft-board-v2-head draft-board-v2-head--owner" : "draft-board-v2-head"}>
                T{slot}{slot === board.ownerSlot ? " · YOU" : ""}
              </div>
            ))}
            {starterLabels.flatMap((label, rowIndex) => [
              <b className="draft-board-v2-round" key={`slot-${rowIndex}`}>{label}</b>,
              ...Array.from({ length: teamCount }, (_, column) => {
                const slot = column + 1;
                const player = assignmentsBySlot?.get(slot)?.starters[rowIndex]?.player ?? null;
                return (
                  <article
                    key={`${label}-${rowIndex}-${slot}`}
                    className={`draft-board-v2-cell ${slot === board.ownerSlot ? "draft-board-v2-cell--owner" : ""}`}
                    onClick={player ? (event: React.MouseEvent) => onPlayerClick(player.playerId, event) : undefined}
                    role={player ? "button" : undefined}
                    tabIndex={player ? 0 : undefined}
                  >
                    <span className="draft-board-v2-cell__player">{player ? player.playerName : "Empty"}</span>
                    {player ? <span className="draft-board-v2-cell__pick">{player.team} · {player.position}</span> : null}
                  </article>
                );
              }),
            ])}
            {benchRows > 0
              ? Array.from({ length: benchRows }, (_, benchIndex) => [
                  <b className="draft-board-v2-round" key={`bench-${benchIndex}`}>BN</b>,
                  ...Array.from({ length: teamCount }, (_, column) => {
                    const slot = column + 1;
                    const player = assignmentsBySlot?.get(slot)?.bench[benchIndex] ?? null;
                    return (
                      <article
                        key={`bench-${benchIndex}-${slot}`}
                        className={`draft-board-v2-cell ${slot === board.ownerSlot ? "draft-board-v2-cell--owner" : ""}`}
                        onClick={player ? (event: React.MouseEvent) => onPlayerClick(player.playerId, event) : undefined}
                        role={player ? "button" : undefined}
                        tabIndex={player ? 0 : undefined}
                      >
                        <span className="draft-board-v2-cell__player">{player ? player.playerName : ""}</span>
                        {player ? <span className="draft-board-v2-cell__pick">{player.team} · {player.position}</span> : null}
                      </article>
                    );
                  }),
                ]).flat()
              : null}
          </div>
        </div>
      )}
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
  currentPick,
  teamCount,
}: {
  rows: CompareRow[];
  summary: string;
  onRemove: (playerId: string) => void;
  currentPick: number | null;
  teamCount: number | null;
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
            { key: "makeItBackProbability", label: "Make It Back", sort: "number", render: (row) => {
              const mib = formatMakeItBack(row.makeItBackProbability as number | null, row.makeItBackTrials as number | null);
              return <span title={mib.title}>{mib.text}</span>;
            } },
            { key: "pickScore", label: "Pick Score — EXPERIMENTAL", sort: "number", render: (row) => row.pickScore == null ? "—" : formatNumber(row.pickScore as number, 1) },
            { key: "action", label: "Action", titleHint: "What to do -- split from Value below; reuses the existing real Cost-of-Waiting/ADP-timing labels.", sort: "text", render: (row) => {
              if (row.action == null) return "—";
              const split = splitActionValue(String(row.action), row.nwrRank as number | null, row.overallAdp as number | null, currentPick, teamCount);
              return <StatusBadge tone={actionToBadgeTone(String(row.action))} label={split.action} />;
            } },
            { key: "value", label: "Value", titleHint: "How the market sees this player right now (Falling/Reach = real-time draft behavior vs. cited ADP; Value = NWR ranks them meaningfully ahead of ADP; Unknown when ADP is unavailable).", sort: "text", render: (row) => {
              if (row.action == null) return "—";
              const split = splitActionValue(String(row.action), row.nwrRank as number | null, row.overallAdp as number | null, currentPick, teamCount);
              const title = split.gapPicks != null ? `${split.gapPicks >= 0 ? "+" : ""}${split.gapPicks} picks vs. cited ADP` : "No real market ADP for this player.";
              return <span title={title}>{split.value}</span>;
            } },
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
  compact = false,
}: {
  rows: QueueRow[];
  canRecordPick: boolean;
  working: string;
  onDraft: (playerId: string) => void;
  onRemove: (playerId: string) => void;
  compact?: boolean;
}) {
  if (rows.length === 0) {
    const empty = (
      <EmptyState
        icon="activity"
        title="Queue is empty"
        message="Queue a player from Suggestions, Rankings, or Search to track it here without drafting it yet."
      />
    );
    return compact ? <div className="draft-room-v2-leftpane__section">{empty}</div> : empty;
  }
  const table = (
    <DataTable
      columns={[
        { key: "playerName", label: "Player", sort: "text", render: (row) => (
          <span className="player-cell"><strong>{compact ? "" : row.nwrRank != null ? `#${row.nwrRank} ` : ""}{String(row.playerName)}</strong><small>{String(row.team)} · {String(row.position)}</small></span>
        ) },
        { key: "actions", label: "", align: "right", render: (row) => (
          <span className="draft-room-v2-pick-actions">
            <Button data-draft-action disabled={!canRecordPick || Boolean(working)} variant="primary" onClick={() => onDraft(String(row.playerId))}>
              {working === String(row.playerId) ? "…" : "Draft"}
            </Button>
            <Button variant="ghost" onClick={() => onRemove(String(row.playerId))}>{compact ? "✕" : "Remove"}</Button>
          </span>
        ) },
      ]}
      rows={rows as unknown as Array<Record<string, unknown>>}
      rowKey={(row) => String(row.playerId)}
    />
  );
  return compact ? (
    <div className="draft-room-v2-leftpane__section">{table}</div>
  ) : (
    <Panel title="Queue" eyebrow={`${rows.length} queued — session-local, never affects the draft board until you Draft`}>
      {table}
    </Panel>
  );
}

/** Owner-test follow-up: the drawer was too verbose/research-oriented for
 * live use. Redesigned to a compact primary block (player, Pick Score,
 * Team Score current->after->delta, Championship Equity, Make-It-Back,
 * Cost of Waiting, Player Score, Market ADP, Action), with WHY/NEWS/
 * DETAILS as collapsed-by-default sections. Research-development wording
 * (EXPERIMENTAL/RESEARCH/SIMULATED RESEARCH, Raw Decision Utility
 * component math) moves into DETAILS/tooltips rather than the primary
 * view -- never removed, never hidden from the system, just not the
 * first thing a live-draft owner has to read past. */
function PlayerDrawer({
  playerId,
  ranking,
  intel,
  candidate,
  currentTeamScore,
  staleAlertData,
  staleAlertHours,
  canRecordPick,
  working,
  isQueued,
  onDraft,
  onQueue,
  onClose,
}: {
  playerId: string;
  ranking: RedraftBootstrap["rankings"][number] | undefined;
  intel: RedraftExternalIntelligenceEntry | undefined;
  candidate: DecisionBundleCandidate | undefined;
  currentTeamScore: number | null;
  staleAlertData: boolean;
  staleAlertHours: number | null;
  // Owner-test follow-up, section 16: the player popup MUST have an
  // obvious Draft button -- every other player surface already reuses
  // this exact same mark()/toggleQueue() pair; the drawer was the one
  // real gap.
  canRecordPick: boolean;
  working: string;
  isQueued: boolean;
  onDraft: (playerId: string) => void;
  onQueue: (playerId: string) => void;
  onClose: () => void;
}) {
  const playerScore = candidate?.playerScore ?? (ranking ? ranking.replacementAdjustedValue : null);
  return (
    <aside className="player-drawer" role="dialog" aria-label={`${ranking?.playerName ?? playerId} detail`}>
      <div className="player-drawer__header">
        <div>
          <strong>{ranking?.playerName ?? candidate?.playerName ?? playerId}</strong>
          <small>{String(ranking?.position ?? candidate?.position ?? "")} · {String(ranking?.team ?? "")}</small>
        </div>
        <Button variant="ghost" onClick={onClose}>Close</Button>
      </div>
      <div className="player-drawer__actions">
        <Button
          data-draft-action
          disabled={!canRecordPick || Boolean(working)}
          variant="primary"
          onClick={() => onDraft(playerId)}
          title={canRecordPick ? "Records this pick for whichever team is currently on the clock." : "Start the draft, and wait for your turn, to record picks here."}
        >
          {working === playerId ? "Saving…" : "Draft"}
        </Button>
        <Button variant="ghost" onClick={() => onQueue(playerId)}>{isQueued ? "Queued" : "Queue"}</Button>
      </div>
      {candidate ? (
        <div className="player-drawer__primary">
          <div className="player-drawer__stat player-drawer__stat--headline" title="Pick Score — EXPERIMENTAL: historically-validated but not yet independently audited.">
            <span>Pick Score</span>
            <strong>{formatNumber(candidate.pickScore, 1)}</strong>
          </div>
          <div
            className="player-drawer__stat"
            title="Team Score — RESEARCH. 'After' reflects a full-draft-completion projection assuming this pick now; the delta therefore reflects this pick PLUS the rest of the draft playing out under the model's continuation policy, not an isolated single-pick value."
          >
            <span>Team Score</span>
            <strong>{currentTeamScore != null ? formatNumber(currentTeamScore, 1) : "—"} → {formatNumber(candidate.teamScoreAfter, 1)}</strong>
            <small>{candidate.teamScoreDelta >= 0 ? "+" : ""}{formatNumber(candidate.teamScoreDelta, 1)}</small>
          </div>
          <div className="player-drawer__stat" title="Championship Equity — SIMULATED RESEARCH.">
            <span>Championship Equity</span>
            <strong>{formatNumber(candidate.championshipEquityAfter * 100, 1)}%</strong>
            <small>{candidate.equityGain >= 0 ? "+" : ""}{formatNumber(candidate.equityGain * 100, 2)} pp</small>
          </div>
          <div className="player-drawer__stat" title={formatMakeItBack(candidate.makeItBackProbability, candidate.makeItBackTrials).title}>
            <span>Make-It-Back</span>
            <strong>{formatMakeItBack(candidate.makeItBackProbability, candidate.makeItBackTrials).text}</strong>
          </div>
          <div className="player-drawer__stat">
            <span>Cost of Waiting</span>
            <strong>{formatNumber(candidate.costOfWaiting, 1)}</strong>
          </div>
          <div className="player-drawer__stat">
            <span>Player Score</span>
            <strong>{playerScore != null ? formatNumber(playerScore, 1) : "—"}</strong>
          </div>
          <div className="player-drawer__stat">
            <span>Market ADP</span>
            <strong>{ranking?.overallAdp != null ? formatNumber(ranking.overallAdp, 1) : "—"}</strong>
          </div>
          <div className="player-drawer__stat">
            <span>Action</span>
            <StatusBadge tone={actionToBadgeTone(candidate.action)} label={candidate.action} />
          </div>
        </div>
      ) : (
        <div className="player-drawer__primary">
          <div className="player-drawer__stat">
            <span>Player Score</span>
            <strong>{playerScore != null ? formatNumber(playerScore, 1) : "—"}</strong>
          </div>
          <div className="player-drawer__stat">
            <span>Market ADP</span>
            <strong>{ranking?.overallAdp != null ? formatNumber(ranking.overallAdp, 1) : "—"}</strong>
          </div>
          <div className="player-drawer__stat">
            <span>NWR Rank</span>
            <strong>#{ranking?.overallRank ?? "—"}</strong>
          </div>
          <p className="boundary-note">
            Not among this pick's evaluated Suggestions candidates — Pick Score/Team Score/Championship Equity impact is
            only computed for the actionable candidates the backend evaluated this turn.
          </p>
        </div>
      )}
      {candidate ? (
        <details className="player-drawer__section">
          <summary>Why</summary>
          <p>Raw Decision Utility: {formatNumber(candidate.rawDecisionUtility, 2)} (Team Score component {formatNumber(candidate.teamScoreUtilityComponent, 2)} + Equity component {formatNumber(candidate.equityUtilityComponent, 2)})</p>
          {candidate.warnings.length > 0 ? (
            <ul className="drawer-warnings">
              {candidate.warnings.map((warning) => <li key={warning}>{warning}</li>)}
            </ul>
          ) : null}
        </details>
      ) : null}
      <details className="player-drawer__section">
        <summary>News{staleAlertData ? ` — STALE${staleAlertHours != null ? ` (${formatNumber(staleAlertHours, 0)}h)` : ""}` : ""}</summary>
        {intel?.currentAlert ? (
          <p><StatusBadge tone={severityToBadgeTone(intel.currentAlertSeverity)} label={intel.currentAlertSeverity ?? "Alert"} /> {intel.currentAlert}</p>
        ) : (
          <p>No current alert on file.{staleAlertData ? " This does not confirm there is no current news -- the source snapshot has not been refreshed recently (see below)." : ""}</p>
        )}
        {staleAlertData ? (
          <p className="boundary-note">
            NEWS DATA STALE{staleAlertHours != null ? ` — ${formatNumber(staleAlertHours, 0)}h` : ""}. This player's alert fields come from an
            aging local snapshot; treat a quiet alert as unconfirmed, not as real-world clearance.
          </p>
        ) : null}
        {intel?.udkPositionRank ? <p>UDK position rank: {intel.udkPositionRank} (tier {intel.udkTier ?? "—"})</p> : null}
        {intel?.fantasyProsEcr ? <p>FantasyPros ECR: {intel.fantasyProsEcr}</p> : null}
      </details>
      <details className="player-drawer__section">
        <summary>Details</summary>
        <p>NWR Rank #{ranking?.overallRank ?? "—"} · {ranking?.overallTierLabel ?? "—"} · Expected round {ranking?.expectedRound ?? "—"}</p>
        {candidate ? (
          <>
            <p>Pick Score is EXPERIMENTAL — historically validated but not yet independently audited. Team Score and Championship Equity are RESEARCH-labeled simulation estimates, not calibrated probabilities.</p>
            {/* Decision Confidence/uncertainty is NOT validated (program verdict) -- the raw SE-derived tier
                (e.g. "LOW_MODEL_UNCERTAINTY") must never be presented as an authoritative confidence claim. */}
            <p title={candidate.uncertainty}>Uncertainty: NOT VALIDATED</p>
          </>
        ) : null}
      </details>
    </aside>
  );
}
