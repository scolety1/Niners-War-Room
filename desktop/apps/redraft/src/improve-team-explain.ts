import type { KdstStreamerRow, WaiverAddCandidate, WaiverAddDropPairing } from "@nwr/contracts";

import type { DecisionExplainConfidence, DecisionExplainTone } from "./decision-explain";

/**
 * NWR UI expansion pass (2026-09-12, Improve Team surface): pure
 * derivation for the unified "How can I improve my roster?" workspace
 * (TARGETS / ADD-DROP / FAAB / STREAMERS / ALL FREE AGENTS). Mirrors
 * `home-action-explain.ts` and `lineup-explain.ts`'s own pattern -- every
 * field reads ONLY data the backend already computed on `WaiverAddCandidate`/
 * `WaiverDropCandidate`/`WaiverAddDropPairing` (unchanged from
 * `redraft_waivers`) or `KdstStreamerRow` (unchanged from `kdst_streamer`).
 * No new scoring, no new marginal-utility/FAAB/ECR heuristic invented here
 * -- formatting/labeling only.
 *
 * Grammar (directive): "ADD Player X / DROP Player Y / BID $14-18 / WHY
 * <roster reason> / THIS WEEK <impact> / ROS <impact> / ALTERNATIVE Player
 * Z". `DecisionExplain`'s rendering treats every field here as optional and
 * honest -- a real "not applicable" (no FAAB estimate, no drop pairing
 * suggested, no next-best alternative on hand) is left `null`, never
 * fabricated.
 */

export interface WaiverTargetExplanation {
  /** "ADD X" or "ADD X / DROP Y" -- the recommendation headline. */
  headline: string;
  why: string;
  /** "$14–18 · HIGH urgency", or null when no real FAAB estimate exists
   * for this candidate (an honest absence, not a guessed range). */
  bid: string | null;
  /** Only populated in THIS_WEEK mode -- a real weekly-lineup read is not
   * computed at all in REST_OF_SEASON mode, so this stays null rather
   * than fabricating one. */
  thisWeekImpact: string | null;
  rosImpact: string | null;
  /** A real, already-ranked next-best add candidate distinct from this
   * one -- null is an honest "no further alternative on hand", never a
   * fabricated placeholder. */
  alternative: string | null;
  tone: DecisionExplainTone;
  confidence: DecisionExplainConfidence | null;
}

function formatSigned(value: number, digits = 1): string {
  const rounded = value.toFixed(digits);
  return value >= 0 ? `+${rounded}` : rounded;
}

export function explainWaiverTarget(
  add: WaiverAddCandidate,
  pairing: WaiverAddDropPairing | null,
  mode: "THIS_WEEK" | "REST_OF_SEASON",
  alternativeAdd: WaiverAddCandidate | null,
): WaiverTargetExplanation {
  const drop = pairing?.drop ?? null;
  const headline = drop ? `ADD ${add.playerName} / DROP ${drop.playerName}` : `ADD ${add.playerName}`;

  const bid = add.faabBidLowDollars != null && add.faabBidHighDollars != null
    ? `$${add.faabBidLowDollars}–${add.faabBidHighDollars}${add.faabUrgency ? ` · ${add.faabUrgency} urgency` : ""}`
    : null;

  const thisWeekImpact = mode === "THIS_WEEK"
    ? (add.becomesStarter
      ? `Projected to become a starter this week${add.weeklyProjectedPoints != null ? ` (${add.weeklyProjectedPoints.toFixed(1)} pts)` : ""}.`
      : "Would not become a starter this week under NWR's lineup optimizer.")
    : null;

  const rosParts: string[] = [];
  if (add.rosReplacementValue != null) rosParts.push(`Replacement value ${formatSigned(add.rosReplacementValue)}`);
  if (add.marginalUtility != null) rosParts.push(`Marginal utility ${formatSigned(add.marginalUtility)}`);
  if (drop && pairing?.netMarginalUtility != null) rosParts.push(`Net vs. dropping ${drop.playerName} ${formatSigned(pairing.netMarginalUtility)}`);
  const rosImpact = rosParts.length ? rosParts.join(" · ") : null;

  const alternative = alternativeAdd
    ? `${alternativeAdd.playerName}${alternativeAdd.rosOverallRank != null ? ` (ROS #${alternativeAdd.rosOverallRank})` : ""}`
    : null;

  return {
    headline,
    why: add.marginalUtilityExplanation || "Ranked by real marginal roster utility.",
    bid,
    thisWeekImpact,
    rosImpact,
    alternative,
    // Every candidate reaching this card is already NWR's own top-ranked
    // real recommendation (rankByMarginalUtility, unchanged) -- "warning"
    // is reserved for a genuine close-call SIGNAL this endpoint does not
    // emit for waivers, so tone stays "recommended" rather than guessing
    // one from a raw utility magnitude.
    tone: "recommended",
    confidence: null,
  };
}

export interface StreamerExplanation {
  /** "START X (K)" / "ADD X (DST)" / etc -- the recommendation headline,
   * built from the real `recommendation` enum. */
  headline: string;
  why: string;
  thisWeekImpact: string | null;
  alternative: string | null;
  tone: DecisionExplainTone;
}

const STREAMER_VERB: Record<KdstStreamerRow["recommendation"], string> = {
  START: "START",
  ADD: "ADD",
  HOLD: "HOLD",
  ROSTERED_ELSEWHERE: "NOTE",
  ALTERNATIVE: "CONSIDER",
};

// Reuses `DecisionExplain`'s existing tone vocabulary -- ALTERNATIVE maps
// onto the tone's own "alternative" value rather than a new one.
const STREAMER_TONE: Record<KdstStreamerRow["recommendation"], DecisionExplainTone> = {
  START: "recommended",
  ADD: "recommended",
  HOLD: "neutral",
  ROSTERED_ELSEWHERE: "neutral",
  ALTERNATIVE: "alternative",
};

/**
 * `alternativeRow` is a real, already-ranked other row at the SAME
 * position for the SAME week (the streamer/positions list is already
 * ordered by the provider's own ECR) -- null is an honest "no further
 * alternative on hand", matching the waiver-target grammar above.
 */
export function explainStreamerPlay(row: KdstStreamerRow, alternativeRow: KdstStreamerRow | null): StreamerExplanation {
  return {
    headline: `${STREAMER_VERB[row.recommendation] ?? row.recommendation} ${row.playerName} (${row.position})`,
    // Mirrors `home-action-explain.ts`'s own STREAMER `why` text verbatim
    // so Improve Team and Home read as one vocabulary for the same real
    // ECR/tier data.
    why: row.tier != null
      ? `NWR's ${row.authority} consensus places ${row.playerName} in Tier ${row.tier} at ${row.position} for Week ${row.week}.`
      : `NWR's ${row.authority} consensus ranks ${row.playerName} #${row.ecr} at ${row.position} for Week ${row.week}.`,
    thisWeekImpact: `${row.rosterStatus} · Week ${row.week}`,
    alternative: alternativeRow
      ? `${alternativeRow.playerName}${alternativeRow.tier != null ? ` (Tier ${alternativeRow.tier})` : ` (#${alternativeRow.ecr})`}`
      : null,
    tone: STREAMER_TONE[row.recommendation] ?? "neutral",
  };
}
