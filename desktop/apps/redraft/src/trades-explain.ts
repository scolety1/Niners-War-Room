import type { TradeAnalysisResult, TradeFinderCandidate } from "@nwr/contracts";

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
