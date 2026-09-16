import type { NwrApiError } from "@nwr/api-client";
import type {
  TradeAnalysisResult,
  TradeFinderCandidate,
  TradePackageCandidate,
  TradePackageEvaluation,
  TradePackageSearchMode,
  TradePackageSearchResult,
} from "@nwr/contracts";

import type { DecisionExplainTone } from "./decision-explain";

/**
 * NWR UI expansion pass (2026-09-12, Trades surface): pure derivation for
 * the ANALYZE / FIND TRADES workspace. Mirrors `lineup-explain.ts` /
 * `improve-team-explain.ts`'s own pattern -- every field reads ONLY data
 * the backend already computed on `TradeAnalysisResult` (unchanged from
 * `redraft_trade_analysis`) or `TradeFinderCandidate` (unchanged from
 * `redraft_trade_finder`). No new trade math, no roster-legality change,
 * and -- per the directive -- no acceptance-probability model, because
 * none exists on either contract; formatting/labeling only.
 */

export type TradeVerdictLabel = "Improves my roster" | "Close" | "Hurts my roster";

export interface TradeVerdict {
  label: TradeVerdictLabel;
  tone: DecisionExplainTone;
  statusBadgeTone: "safe" | "review" | "blocked";
}

/**
 * Mirrors `verdictFor` in `in-season.tsx` (the pre-existing Trade Analysis
 * page, left in place as an unrouted legacy fallback -- same precedent as
 * `WaiversPage` after the Improve Team pass) byte-for-byte for the same
 * two real signals (`netMarginalUtility`, `rosValueDelta`). Duplicated
 * rather than imported so this stays a pure, dependency-free derivation
 * module like its siblings, matching how `explainStreamerPlay` already
 * mirrors `home-action-explain.ts`'s own why-text verbatim rather than
 * importing across page files.
 */
export function tradeVerdictFor(result: TradeAnalysisResult): TradeVerdict {
  const netUtility = result.netMarginalUtility;
  const rosValue = result.rosValueDelta;
  if (netUtility > 0 && rosValue >= 0) return { label: "Improves my roster", tone: "recommended", statusBadgeTone: "safe" };
  if (netUtility < 0 && rosValue <= 0) return { label: "Hurts my roster", tone: "negative", statusBadgeTone: "blocked" };
  return { label: "Close", tone: "warning", statusBadgeTone: "review" };
}

const VERDICT_WHY: Record<TradeVerdictLabel, string> = {
  "Improves my roster": "Your starting lineup value and rest-of-season value both improve under NWR's evaluator.",
  "Hurts my roster": "Your starting lineup value and rest-of-season value both decline under NWR's evaluator.",
  Close: "Your starting lineup value and rest-of-season value move in different directions, or the net change is too small to call decisively.",
};

function formatSigned(value: number, digits = 1): string {
  const rounded = value.toFixed(digits);
  return value >= 0 ? `+${rounded}` : rounded;
}

export interface TradeAnalysisExplanation {
  /** "You give X / you receive Y" -- the real trade being evaluated, read
   * from the backend's own confirmed `gives`/`receives` player names, not
   * the picker's raw label text (which also carries "(POS)"/opponent-team
   * suffixes). */
  eyebrow: string;
  /** "Improves my roster" / "Close" / "Hurts my roster" -- the one overall
   * verdict, never an opaque magic number. */
  headline: TradeVerdictLabel;
  tone: DecisionExplainTone;
  statusBadgeTone: "safe" | "review" | "blocked";
  why: string;
  /** WEEKLY IMPACT: starting lineup value before/after, this week's real
   * lineup-optimizer scope. */
  weeklyImpact: string;
  /** ROS IMPACT: net marginal utility + rest-of-season value delta, plus a
   * real championship-equity note only when the backend supplied one. */
  rosImpact: string;
  /** DEPTH: bench contingency value before/after. */
  depth: string;
  /** POSITION EFFECT: starter holes + position redundancy before/after. */
  positionEffect: string;
  /** STATUS/RISK (aggregate half -- per-player status lives in the detail
   * tables below the card): real backend risk flags, or `null` for an
   * honest "no risk flags recorded", never a fabricated "no risk" claim. */
  risk: string | null;
}

export function explainTradeAnalysis(result: TradeAnalysisResult, giveNames: string[], receiveNames: string[]): TradeAnalysisExplanation {
  const verdict = tradeVerdictFor(result);

  const weeklyImpact = `Starting lineup value ${result.startingLineupValueBefore.toFixed(1)} → ${result.startingLineupValueAfter.toFixed(1)} (${formatSigned(result.startingLineupValueDelta)})`;

  const rosParts = [
    `Net marginal utility ${formatSigned(result.netMarginalUtility)}`,
    `ROS value delta ${formatSigned(result.rosValueDelta)}`,
  ];
  if (result.championshipEquityNote) rosParts.push(result.championshipEquityNote);
  const rosImpact = rosParts.join(" · ");

  const depth = `Bench contingency value ${result.benchContingencyValueBefore.toFixed(1)} → ${result.benchContingencyValueAfter.toFixed(1)}`;

  const holesSummary = `Starter holes ${result.starterHolesBefore.length} → ${result.starterHolesAfter.length}${result.starterHolesAfter.length ? ` (${result.starterHolesAfter.join(", ")})` : ""}`;
  const redundancyKeys = Array.from(new Set([...Object.keys(result.positionRedundancyBefore), ...Object.keys(result.positionRedundancyAfter)])).sort();
  const redundancySummary = redundancyKeys.length
    ? `Redundancy ${redundancyKeys.map((position) => `${position} ${result.positionRedundancyBefore[position] ?? 0}→${result.positionRedundancyAfter[position] ?? 0}`).join(", ")}`
    : null;
  const positionEffect = [holesSummary, redundancySummary].filter(Boolean).join(" · ");

  return {
    eyebrow: `You give ${giveNames.join(", ") || "—"} / you receive ${receiveNames.join(", ") || "—"}`,
    headline: verdict.label,
    tone: verdict.tone,
    statusBadgeTone: verdict.statusBadgeTone,
    why: VERDICT_WHY[verdict.label],
    weeklyImpact,
    rosImpact,
    depth,
    positionEffect,
    risk: result.riskFlags.length ? result.riskFlags.join(" · ") : null,
  };
}

export interface TradeFinderExplanation {
  /** "Send X for Y" -- the real 1-for-1 package this candidate proposes. */
  headline: string;
  /** WHY THIS FITS. */
  why: string;
  /** NWR ROSTER IMPACT -- real net marginal utility + ROS value delta on
   * the owner's own side, plus the opponent's own net marginal utility
   * (never an acceptance probability -- the backend supplies none). */
  impact: string;
  fits: boolean;
  tone: DecisionExplainTone;
}

export type TradeFinderAnalysisLinkTarget =
  /** Both sides resolved to a real raw Sleeper id -- safe to build the
   * `/trade-analysis` deep link. */
  | { kind: "ok"; href: string; reason: null }
  /** At least one side's canonical id could not be resolved back to a real
   * Sleeper id (should not happen in practice -- every candidate is built
   * from an already-resolved roster -- but this is disclosed rather than
   * crashing or silently sending a wrong/stale id across the provider
   * boundary). */
  | { kind: "blocked"; href: null; reason: string };

/**
 * NWR Post-UI closure pass (bug 2): the fix for the old "Open in Analyze"
 * button, which built its `/trade-analysis` deep link directly from
 * `TradeFinderCandidate.myGivePlayerId`/`opponentGivePlayerId` -- NWR's own
 * canonical (GSIS-style) ids -- through the `giveSleeperId`/
 * `receiveSleeperId` query params `TradeAnalysisPage` sends VERBATIM to
 * `redraftTradeAnalysis`, an endpoint that requires real raw Sleeper ids.
 * That always failed (`TRADE_ANALYSIS_IDENTITY_UNRESOLVED`) for the
 * opponent side -- a real, previously-disclosed always-fails path.
 *
 * Fixed by resolving through the real raw Sleeper ids the backend now also
 * returns alongside each canonical one (`mySleeperPlayerId`/
 * `opponentSleeperPlayerId` -- see `DesktopBackendFacade.
 * redraft_trade_finder`'s own reverse-lookup of the SAME
 * `resolve_roster_canonical_ids` map every other canonical-id call site
 * already uses), never re-derived or guessed client-side. An unresolved id
 * on either side is reported honestly (`kind: "blocked"`) rather than
 * building a link that is guaranteed to fail, or silently substituting the
 * wrong (canonical) id as if it were a Sleeper one.
 */
export function tradeFinderAnalysisLinkTarget(candidate: TradeFinderCandidate): TradeFinderAnalysisLinkTarget {
  if (!candidate.mySleeperPlayerId || !candidate.opponentSleeperPlayerId) {
    return {
      kind: "blocked",
      href: null,
      reason: "This candidate's player identity could not be resolved to a live Sleeper roster id -- Trade Analysis needs a real Sleeper id for both sides.",
    };
  }
  const params = new URLSearchParams({
    giveSleeperId: candidate.mySleeperPlayerId,
    giveName: candidate.myGivePlayerName,
    receiveSleeperId: candidate.opponentSleeperPlayerId,
    receiveName: candidate.opponentGivePlayerName,
  });
  return { kind: "ok", href: `/trade-analysis?${params.toString()}`, reason: null };
}

export function explainTradeFinderCandidate(candidate: TradeFinderCandidate): TradeFinderExplanation {
  const fits = candidate.myNetMarginalUtility > 0 && candidate.opponentNetMarginalUtility > 0;
  return {
    headline: `Send ${candidate.myGivePlayerName} for ${candidate.opponentGivePlayerName}`,
    why: fits
      ? "Both sides' real marginal roster utility improves under NWR's evaluator."
      : "Only your side's marginal utility improves under NWR's evaluator -- the other team may not agree.",
    impact: `Your net marginal utility ${formatSigned(candidate.myNetMarginalUtility)} · ROS value delta ${formatSigned(candidate.myRosValueDelta)} · their net marginal utility ${formatSigned(candidate.opponentNetMarginalUtility)}`,
    fits,
    tone: fits ? "recommended" : "neutral",
  };
}

// ---------------------------------------------------------------------------
// TRADE PACKAGE SEARCH (P1-3, Worker 7) -- FIND WIN-WIN PACKAGES /
// TARGET PLAYER / IMPROVE POSITION. Pure derivation over
// `TradePackageCandidate`, unchanged from
// `DesktopBackendFacade.redraft_trade_package_search` (Worker 6). Same
// disclosed rule as every sibling in this file: never fabricates an
// acceptance probability -- the backend computes none, in any mode, and
// `whyItHelpsYou`/`whyItMayFitThem` are rendered verbatim (real, backend-
// computed sentences), never paraphrased into "likely to accept" language.
// ---------------------------------------------------------------------------

export interface TradePackageExplanation {
  /** "Send X, Y for A" -- the real package identity, built from the
   * candidate's own confirmed `youSendNames`/`youReceiveNames`. */
  headline: string;
  tone: DecisionExplainTone;
  /** WHY IT HELPS YOU -- the backend's own `whyItHelpsYou` sentences,
   * joined and explicitly labeled. */
  why: string;
  /** WHY IT MAY FIT THEM -- the backend's own `whyItMayFitThem` sentences
   * (computed from the opponent's own roster, never a promise the
   * opponent will accept). */
  secondaryWhy: string;
  /** WEEKLY IMPACT -- the owner side's starting lineup value before/after,
   * the same real signal `explainTradeAnalysis`'s own `weeklyImpact`
   * already uses for the identical field on the single-package Trade
   * Analysis workspace. */
  thisWeekImpact: string;
  /** ROS IMPACT -- owner net marginal utility + ROS value delta. Unlike
   * `TradeAnalysisResult`, this nested evaluation carries no
   * `championshipEquityNote` field (verified against a real computed
   * payload, not assumed from the ledger's doc) -- nothing is appended
   * here that the backend didn't actually send. */
  rosImpact: string;
  depth: string;
  positionEffect: string;
  risk: string | null;
}

function tradePackageToneFor(evaluation: TradePackageEvaluation): DecisionExplainTone {
  const netUtility = evaluation.netMarginalUtility;
  const rosValue = evaluation.rosValueDelta;
  if (netUtility > 0 && rosValue >= 0) return "recommended";
  if (netUtility < 0 && rosValue <= 0) return "negative";
  return "warning";
}

export function explainTradePackageCandidate(candidate: TradePackageCandidate): TradePackageExplanation {
  const owner = candidate.ownerEvaluation;

  const thisWeekImpact = `Starting lineup value ${owner.startingLineupValueBefore.toFixed(1)} → ${owner.startingLineupValueAfter.toFixed(1)} (${formatSigned(owner.startingLineupValueDelta)})`;
  const rosImpact = `Net marginal utility ${formatSigned(owner.netMarginalUtility)} · ROS value delta ${formatSigned(owner.rosValueDelta)}`;
  const depth = `Bench contingency value ${owner.benchContingencyValueBefore.toFixed(1)} → ${owner.benchContingencyValueAfter.toFixed(1)}`;

  const holesSummary = `Starter holes ${owner.starterHolesBefore.length} → ${owner.starterHolesAfter.length}${owner.starterHolesAfter.length ? ` (${owner.starterHolesAfter.join(", ")})` : ""}`;
  const redundancyKeys = Array.from(new Set([...Object.keys(owner.positionRedundancyBefore), ...Object.keys(owner.positionRedundancyAfter)])).sort();
  const redundancySummary = redundancyKeys.length
    ? `Redundancy ${redundancyKeys.map((position) => `${position} ${owner.positionRedundancyBefore[position] ?? 0}→${owner.positionRedundancyAfter[position] ?? 0}`).join(", ")}`
    : null;
  const positionEffect = [holesSummary, redundancySummary].filter(Boolean).join(" · ");

  return {
    headline: `Send ${candidate.youSendNames.join(", ") || "—"} for ${candidate.youReceiveNames.join(", ") || "—"}`,
    tone: tradePackageToneFor(owner),
    why: `Why it helps you: ${candidate.whyItHelpsYou.length ? candidate.whyItHelpsYou.join(" ") : "NWR's evaluator found this package legal but recorded no specific reason."}`,
    secondaryWhy: `Why it may fit them: ${candidate.whyItMayFitThem.length ? candidate.whyItMayFitThem.join(" ") : "NWR did not record a specific reason this may fit the other team."}`,
    thisWeekImpact,
    rosImpact,
    depth,
    positionEffect,
    risk: owner.riskFlags.length ? owner.riskFlags.join(" · ") : null,
  };
}

/** Softened, owner-friendly copy for Trade Package Search's own error
 * codes -- specifically the disclosed
 * `TRADE_PACKAGE_SEARCH_TARGET_IDENTITY_UNRESOLVED` open item (Worker 6's
 * ledger entry, P1-3 open issue #5): a raw error code is never shown to
 * the owner. Every other code falls back to the facade's own already-
 * human-readable `message`/`recoveryAction` (e.g. "Sleeper roster/user/
 * player data could not be read...") -- honest passthrough, not a second
 * layer of invented copy for a case with no disclosed UX gap. */
export interface SoftenedTradePackageSearchError {
  message: string;
  recovery: string;
}

const TRADE_PACKAGE_SEARCH_ERROR_COPY: Record<string, SoftenedTradePackageSearchError> = {
  TRADE_PACKAGE_SEARCH_TARGET_IDENTITY_UNRESOLVED: {
    message: "Couldn't find that player on a tradeable roster.",
    recovery: "Pick the player from the search list above instead -- they may not be in NWR's governed rankings yet.",
  },
};

export function describeTradePackageSearchError(error: NwrApiError): SoftenedTradePackageSearchError {
  return TRADE_PACKAGE_SEARCH_ERROR_COPY[error.code] ?? { message: error.message, recovery: error.recoveryAction };
}

/**
 * Find-trades mode-display race fix (shared upgrade B, 2026-09-16): same
 * bug class as the FAAB LIVE/SCENARIO race (`resolveFaabDisplay`,
 * improve-team-explain.ts) and the Weekly Home/Start-Sit week race
 * (`resolveWeekDisplay`, weekly-shared.tsx). `FindTradesTab` (trades.tsx)
 * auto-refetches via `useAsync` whenever the owner changes search mode
 * (FIND_WIN_WIN / TARGET_PLAYER / IMPROVE_POSITION) -- the segmented
 * control updates immediately, but the candidate cards below keep
 * rendering the PREVIOUS mode's `result` (a completely different kind of
 * search, over a different set of packages) until the new mode's fetch
 * resolves, with nothing distinguishing that gap from a genuinely current
 * result. The backend echoes back which mode it actually searched
 * (`TradePackageSearchResult.mode`) -- the one authoritative record of what
 * the displayed candidates represent -- so staleness is a structural
 * comparison against that field, never a `working`-flag guess.
 */
export function isTradePackageSearchStale(
  result: Pick<TradePackageSearchResult, "mode"> | null,
  requestedMode: TradePackageSearchMode,
): boolean {
  return result != null && result.mode !== requestedMode;
}

/**
 * Full Cycle V1, Worker 5 (Section 3D, Worker 3's open item #4): the
 * Analyze tab (`AnalyzeTab` in trades.tsx) is explicit-submit (a single
 * "Analyze trade" button, disabled while `working`), so it is safe from the
 * FAAB-class auto-refetch race -- but it had a real, separate small UX gap:
 * once a result is shown, editing `gives`/`receives` (adding/removing a
 * player on either side) leaves the fully-confident-looking prior result
 * panel on screen completely unmarked, even though it no longer describes
 * the trade currently built above it. Unlike `isTradePackageSearchStale`
 * (which compares against a field the BACKEND echoes back,
 * `TradePackageSearchResult.mode`), `TradeAnalysisResult.gives`/`.receives`
 * carry NWR's own canonical player ids (`TradePlayerImpact.playerId`), not
 * the raw Sleeper ids the picker UI tracks (`TradeSide.sleeperPlayerId`) --
 * there is no direct id-space match between the two (the same
 * canonical-vs-Sleeper-id gap already documented above for Find Trades'
 * deliberately-omitted "Open in Analyze" jump). So staleness here compares
 * the CURRENT picker selection against a snapshot of the exact Sleeper ids
 * that were actually submitted for the result on screen, taken at the
 * moment `onAnalyze` fired -- order-independent (re-picking the same two
 * players in a different order is not a real change to the trade).
 */
export function isTradeAnalysisStale(
  analyzedGiveIds: readonly string[] | null,
  analyzedReceiveIds: readonly string[] | null,
  currentGiveIds: readonly string[],
  currentReceiveIds: readonly string[],
): boolean {
  if (analyzedGiveIds == null || analyzedReceiveIds == null) return false;
  const sameSet = (a: readonly string[], b: readonly string[]) =>
    a.length === b.length && [...a].sort().join("|") === [...b].sort().join("|");
  return !sameSet(analyzedGiveIds, currentGiveIds) || !sameSet(analyzedReceiveIds, currentReceiveIds);
}
