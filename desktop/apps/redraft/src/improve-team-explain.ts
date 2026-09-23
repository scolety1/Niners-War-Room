import type { KdstStreamerRow, WaiverAddCandidate, WaiverAddDropPairing, WaiverFaabContext } from "@nwr/contracts";

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
  const noLegalDrop = pairing?.contextLabel === 'NO_DROP_CANDIDATE_AVAILABLE';
  const headline = drop
    ? `ADD ${add.playerName} / DROP ${drop.playerName}`
    : noLegalDrop
      ? `TARGET ${add.playerName} -- NO LEGAL DROP AVAILABLE`
      : `ADD ${add.playerName}`;

  const bid = add.faabBidLowDollars != null && add.faabBidLowDollars > 0 && add.faabBidHighDollars != null
    ? `$${add.faabBidLowDollars}–${add.faabBidHighDollars}${add.faabUrgency ? ` · ${add.faabUrgency} urgency` : ""}`
    : null;

  // NWR Sunday Readiness overnight cycle, Worker 3 (W5 fix): `add.
  // becomesStarter` now carries a REAL, independently recomputed weekly
  // evaluation in THIS_WEEK mode (see `becomesStarterBasis`), and can
  // genuinely be `null` when this pass did not evaluate this candidate --
  // that must read as "unavailable", never as a false "would not start"
  // (the old ternary silently treated `null` the same as `false`).
  const thisWeekImpact = mode === "THIS_WEEK"
    ? (add.becomesStarterBasis === "THIS_WEEK_LINEUP_EVALUATION"
      ? (add.becomesStarter
        ? `Projected to become a starter this week (real legal-lineup gain: ${(add.thisWeekLineupGain ?? 0).toFixed(1)} pts).`
        : `Would not become a starter this week under NWR's lineup optimizer (real legal-lineup gain: ${(add.thisWeekLineupGain ?? 0).toFixed(1)} pts).`)
      : `A real weekly-lineup evaluation was not computed for this candidate this pass -- not the same as "would not start". Weekly projected points: ${add.weeklyProjectedPoints != null ? add.weeklyProjectedPoints.toFixed(1) : "unavailable"}.`)
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
    why: noLegalDrop
      ? `${add.marginalUtilityExplanation} This roster has no verified open slot or legal drop candidate, so this is not currently an executable claim.`
      : add.marginalUtilityExplanation || "Ranked by real marginal roster utility.",
    bid,
    thisWeekImpact,
    rosImpact,
    alternative,
    // Every candidate reaching this card is already NWR's own top-ranked
    // real recommendation (rankByMarginalUtility, unchanged) -- "warning"
    // is reserved for a genuine close-call SIGNAL this endpoint does not
    // emit for waivers, so tone stays "recommended" rather than guessing
    // one from a raw utility magnitude.
    tone: noLegalDrop ? 'neutral' : 'recommended',
    confidence: noLegalDrop ? 'LOW' : null,
  };
}

/**
 * LIVE/SCENARIO race fix (2026-09-16): the FAAB tab's "LIVE"/"SCENARIO"
 * label was previously derived from `budgetScenario`, a piece of CURRENT
 * React input state owned by `ImproveTeamPage`, while the budget numbers
 * and bid recommendations sitting next to it were always read from
 * `waivers.faabContext` -- the last-RESOLVED `useAsync` response. Because
 * a scenario edit/mode switch/profile switch updates `budgetScenario`
 * synchronously but the matching response only lands after a real network
 * round trip, the label could visibly race ahead of (or fall behind) the
 * data it was labeling -- e.g. an "SCENARIO" badge rendered over numbers
 * that were still the previous LIVE response, or vice versa.
 *
 * The fix: this function's ONLY input is `WaiverFaabContext`, the field
 * living on the SAME resolved `WaiversResult` object the numbers and
 * `addCandidates`/bid list already come from. It has no parameter for any
 * current-input-state flag, so it is structurally impossible for its
 * output to describe a different response than the one supplying the
 * numbers next to it -- the type signature itself is the guarantee, not
 * just a runtime check. `budgetScenario` (the owner's in-progress
 * what-if-scenario form) legitimately stays local React state in
 * `improve-team.tsx` -- it drives which request to send next and whether
 * the edit form is shown, never the label/tone of already-displayed data.
 */
export interface WaiverFaabDisplay {
  /** Whether the CURRENTLY DISPLAYED numbers/recommendations were priced
   * under a SCENARIO or a LIVE read -- read only from the resolved
   * response's own `budgetMode`, never from any current-input flag. */
  isScenario: boolean;
  metricTone: "crimson" | "gold";
  weeksTone: "crimson" | "violet";
  eyebrow: string;
  /** Non-null only when `isScenario` -- the exact numbers this response's
   * bid ranges were actually computed from (echoed back by the backend),
   * not whatever the owner's edit form currently shows (which may already
   * differ if they kept typing after the request was sent). */
  alertHeadline: string | null;
  alertBody: string | null;
}

export function hasTrustworthyFaabBudget(
  faabContext: WaiverFaabContext | null | undefined,
): faabContext is WaiverFaabContext & {
  totalBudgetDollars: number;
  remainingBudgetDollars: number;
  weeksRemaining: number;
} {
  if (!faabContext || faabContext.source === 'UNAVAILABLE' || faabContext.isFaabLeague !== true) return false;
  if (
    faabContext.totalBudgetDollars == null
    || faabContext.remainingBudgetDollars == null
    || faabContext.weeksRemaining == null
  ) return false;
  return faabContext.budgetMode !== 'SCENARIO' || faabContext.scenario !== null;
}

export function hasRetainedRowsAfterFailedRefresh(
  error: unknown,
  waivers: unknown,
): boolean {
  return error != null && waivers != null;
}

export function resolveFaabDisplay(faabContext: WaiverFaabContext): WaiverFaabDisplay {
  const isScenario = faabContext.budgetMode === "SCENARIO";
  const scenario = faabContext.scenario;
  return {
    isScenario,
    metricTone: isScenario ? "crimson" : "gold",
    weeksTone: isScenario ? "crimson" : "violet",
    eyebrow: isScenario
      ? "SCENARIO -- your own hypothetical inputs, not read from Sleeper"
      : "LIVE -- read this request from your real Sleeper league",
    alertHeadline: isScenario ? "SCENARIO -- not your real live budget" : null,
    alertBody: isScenario && scenario
      ? `You're viewing a hypothetical: what if your budget were $${scenario.remainingBudgetDollars} of $${scenario.totalBudgetDollars}, ${scenario.weeksRemaining} weeks remaining? Bid ranges below are computed from these numbers, not your real Sleeper budget.`
      : null,
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

// NWR Sunday Readiness overnight cycle, Worker 3 (W6 fix): "START" here
// means the owner's own current starter is genuinely the best reachable
// option this week (per the backend's own corrected primary-recommendation
// selection -- see `desktop_facade.py`'s `redraft_kdst_streamer`) -- labeled
// "KEEP" so a real KEEP-CURRENT recommendation reads as one, not as an
// instruction to take some new action.
const STREAMER_VERB: Record<KdstStreamerRow["recommendation"], string> = {
  START: "KEEP",
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

// Waiver-Night Hardening cycle, Worker B (2026-09-22): a real,
// live-reproducible frontend/backend divergence. `redraft_kdst_streamer`
// (`desktop_facade.py`) selects its own primary recommendation as the
// first ECR-ranked row whose recommendation is genuinely actionable --
// `_STREAMER_ACTIONABLE_RECOMMENDATIONS = {"START", "HOLD", "ADD"}` -- but
// this file's own UI previously re-derived "top" independently, inline in
// `StreamersTab`, checking only `recommendation === "START" || "ADD"`
// (HOLD omitted). Whenever the real best-actionable row for a position was
// HOLD (a player the owner already rosters but is not currently
// starting -- e.g. a real bench K/DST), the UI's own re-derivation missed
// it and fell through to `rows[0]`, the single best-ECR row regardless of
// ownership -- which can be a real OPPONENT'S rostered player
// (`ROSTERED_ELSEWHERE`). That is exactly the "opponent's rostered player
// recommended" bug class an earlier cycle already fixed for Waivers/Free
// Agents; this closes the same class of gap for the K/DST Streamer's own
// UI-level primary-row selection (the backend's own selection was already
// correct -- this is a presentation-layer re-derivation bug, not a data
// bug). Extracted to a pure, tested function so the UI's selection can
// never silently drift from the backend's own actionable set again.
const STREAMER_ACTIONABLE_RECOMMENDATIONS: ReadonlySet<KdstStreamerRow["recommendation"]> = new Set([
  "START",
  "HOLD",
  "ADD",
]);

export interface StreamerPrimarySelection {
  top: KdstStreamerRow | null;
  alternative: KdstStreamerRow | null;
}

/**
 * `rows` must already be ECR-ordered for the target position/week (the
 * backend's own `positions` list already is). Mirrors
 * `desktop_facade.py::redraft_kdst_streamer`'s own primary-recommendation
 * selection exactly -- the first actionable (START/HOLD/ADD) row, never a
 * real opponent's `ROSTERED_ELSEWHERE` row, falling back to the single
 * best-ECR row only when NO row is actionable at all (an honest "nothing
 * to recommend", not a fabricated one).
 */
export function selectPrimaryStreamerRow(rows: KdstStreamerRow[]): StreamerPrimarySelection {
  const topIndex = rows.findIndex((row) => STREAMER_ACTIONABLE_RECOMMENDATIONS.has(row.recommendation));
  const top = (topIndex >= 0 ? rows[topIndex] : rows[0]) ?? null;
  const alternative = top ? (rows[(topIndex >= 0 ? topIndex : 0) + 1] ?? null) : null;
  return { top, alternative };
}

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
    // Real display bug found + fixed alongside the STREAMERS table (same
    // pass): `rosterStatus` is the backend's raw enum ("YOUR_STARTER",
    // "ROSTERED_ELSEWHERE") -- humanized here too so the DecisionExplain
    // card's "THIS WEEK" line and the table below it read consistently.
    // Presentation-only; `row.rosterStatus` itself is unchanged.
    thisWeekImpact: `${row.rosterStatus.replaceAll("_", " ")} · Week ${row.week}`,
    alternative: alternativeRow
      ? `${alternativeRow.playerName}${alternativeRow.tier != null ? ` (Tier ${alternativeRow.tier})` : ` (#${alternativeRow.ecr})`}`
      : null,
    tone: STREAMER_TONE[row.recommendation] ?? "neutral",
  };
}
