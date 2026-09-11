import type {
  KdstStreamerRow,
  TradeFinderCandidate,
  WaiverAddCandidate,
  WeeklyHomeAction,
  WeeklyLineupSlot,
  WeeklyLineupSwap,
} from "@nwr/contracts";

/**
 * NWR UI foundation pass (2026-09-10, directive Phase 4/6): the standard
 * "why does NWR want me to do this" breakdown for one `WeeklyHomeAction`.
 * Pure, presentation-only, and reads ONLY fields the backend already
 * computed and attached to `action.detail` (see
 * `desktop_facade.py::redraft_weekly_home_actions` -- each category's
 * `detail` is literally the same sub-object Lineup/Waivers/Trade
 * Finder/K-DST Streamer already render elsewhere in this app). No new
 * scoring, no new heuristic invented here beyond formatting/labeling --
 * see each branch's comment for exactly which already-computed field it
 * reads.
 *
 * `confidence` mirrors the product's existing `DecisionConfidenceState`
 * vocabulary (HIGH/NOMINAL/LOW) so it reads consistently with
 * `DecisionResultEnvelope.confidenceState` elsewhere in the app, but is
 * only populated where a real, already-computed signal justifies it --
 * `null` ("not scored") is left alone rather than guessed, matching this
 * repo's disclosed-heuristic-only posture (see DECISION_CONTRACTS.md's
 * "Confidence heuristic" section for the pattern this follows).
 */

export type HomeActionConfidence = "HIGH" | "NOMINAL" | "LOW" | null;

export interface HomeActionExplanation {
  /** The action's own headline, verbatim -- the backend's `summary`. */
  doThis: string;
  categoryLabel: string;
  /** The single biggest reason, in plain language. */
  why: string;
  /** A second, optional supporting reason. */
  secondaryWhy: string | null;
  /** A short, formatted "what changes" figure -- null when no real
   * per-action delta/utility figure exists for this category. */
  expectedImpact: string | null;
  confidence: HomeActionConfidence;
  /** The next-best alternative NWR already computed for this decision,
   * when one exists -- null is a real, honest "no alternative recorded"
   * state, never a fabricated placeholder. */
  alternative: string | null;
}

function formatSigned(value: number, digits = 1): string {
  const rounded = value.toFixed(digits);
  return value >= 0 ? `+${rounded}` : rounded;
}

export const HOME_ACTION_CATEGORY_LABEL: Record<WeeklyHomeAction["category"], string> = {
  START_SIT: "Start / Sit",
  START_SIT_CLOSE_CALL: "Start / Sit — close call",
  WAIVER: "Waiver",
  TRADE: "Trade opportunity",
  STREAMER: "Streamer",
};

export function explainHomeAction(action: WeeklyHomeAction): HomeActionExplanation {
  const categoryLabel = HOME_ACTION_CATEGORY_LABEL[action.category] ?? action.category;

  if (action.category === "START_SIT") {
    // detail is the real WeeklyLineupSwap NWR already computed for this
    // swap (see redraft_weekly_lineup's own `swaps` field, unchanged).
    const swap = action.detail as unknown as WeeklyLineupSwap;
    return {
      doThis: action.summary,
      categoryLabel,
      why: `Projected to outscore the current starter at ${swap.slotType} this week.`,
      secondaryWhy: null,
      expectedImpact: Number.isFinite(swap.projectedDelta)
        ? `${formatSigned(swap.projectedDelta)} projected points`
        : null,
      confidence: null,
      alternative: null,
    };
  }

  if (action.category === "START_SIT_CLOSE_CALL") {
    // detail is the real WeeklyLineupSlot -- closeCall/closeCallAlternative/
    // closeCallMargin are already-computed fields (unchanged from Lineup).
    const slot = action.detail as unknown as WeeklyLineupSlot;
    const margin = slot.closeCallMargin;
    return {
      doThis: action.summary,
      categoryLabel,
      why: `The projection margin over the next-best option is real but small -- a genuine close call, not a clear-cut start.`,
      secondaryWhy: null,
      expectedImpact: margin != null ? `${margin.toFixed(1)} pt margin` : null,
      // "closeCall" is itself the already-computed real signal for lower
      // certainty -- reusing it as LOW confidence is a direct read, not a
      // new heuristic.
      confidence: "LOW",
      alternative: slot.closeCallAlternative ?? null,
    };
  }

  if (action.category === "WAIVER") {
    // detail is the real WaiverAddCandidate -- marginalUtilityExplanation/
    // marginalUtility/becomesStarter are already-computed fields (unchanged
    // from Waivers).
    const candidate = action.detail as unknown as WaiverAddCandidate;
    return {
      doThis: action.summary,
      categoryLabel,
      why: candidate.marginalUtilityExplanation || "Ranked by real marginal roster utility.",
      secondaryWhy: candidate.becomesStarter
        ? "Projected to become a starter this week under NWR's lineup optimizer."
        : null,
      expectedImpact: candidate.marginalUtility != null
        ? `Marginal utility ${formatSigned(candidate.marginalUtility)}`
        : null,
      confidence: null,
      alternative: null,
    };
  }

  if (action.category === "TRADE") {
    // detail is the real TradeFinderCandidate -- myNetMarginalUtility/
    // opponentNetMarginalUtility are the same already-computed fields
    // TradeFinderCard already renders (see in-season.tsx).
    const candidate = action.detail as unknown as TradeFinderCandidate;
    const mutual = candidate.myNetMarginalUtility > 0 && candidate.opponentNetMarginalUtility > 0;
    return {
      doThis: action.summary,
      categoryLabel,
      why: mutual
        ? "Both sides' real marginal roster utility improves under NWR's evaluator."
        : "Your marginal utility improves under NWR's evaluator -- the other team may not agree.",
      secondaryWhy: null,
      expectedImpact: `Net marginal utility ${formatSigned(candidate.myNetMarginalUtility)}`,
      confidence: mutual ? "NOMINAL" : "LOW",
      alternative: null,
    };
  }

  // STREAMER -- detail is the real KdstStreamerRow (ecr/tier/authority are
  // already-computed fields, unchanged from the K/DST Streamer page).
  const row = action.detail as unknown as KdstStreamerRow;
  return {
    doThis: action.summary,
    categoryLabel,
    why: row.tier != null
      ? `NWR's ${row.authority} consensus places ${row.playerName} in Tier ${row.tier} at ${row.position} for Week ${row.week}.`
      : `NWR's ${row.authority} consensus ranks ${row.playerName} #${row.ecr} at ${row.position} for Week ${row.week}.`,
    secondaryWhy: null,
    expectedImpact: null,
    confidence: null,
    alternative: null,
  };
}
