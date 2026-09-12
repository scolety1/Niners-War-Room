import type { DecisionBundle, DecisionBundleCandidate } from "@nwr/contracts";
import { formatNumber } from "@nwr/ui";

import type { PickNowBanner, SuggestionRow } from "./draft-room-v2";

/**
 * NWR UI expansion pass (2026-09-12, Draft Room surface, Work Unit 6): the
 * primary pick-hierarchy grammar the directive asks for -- NWR PICK NOW
 * (the player) -> WHY -> ALTERNATIVE -> WAIT/AVAILABILITY -> ROSTER EFFECT
 * -- mapped onto the SAME `DecisionExplain` component every other surface
 * (Home/Lineup/Improve Team/Trades/League) already uses, so an active pick
 * reads as one coherent product instead of Draft Room's own bespoke banner.
 *
 * Pure, presentation-only, same family as `lineup-explain.ts`/
 * `trades-explain.ts`: every field traces to a value the backend already
 * computed on `PickNowBanner`/`SuggestionRow` (unchanged -- `findPickNow`,
 * `buildSuggestionsRows`) or the matching real `DecisionBundleCandidate`
 * (for `marginalRosterUtility`, the real walk-forward-promoted primary
 * ordering signal -- see `MarginalRosterUtility` in `@nwr/contracts`).
 * Never invents a number, a confidence claim, or an alternative the
 * backend didn't already supply -- `findPickNow` itself only ever
 * populates `runnerUp` in the genuine close-call state, and this module
 * preserves that exactly (no alternative is fabricated for a clear "NWR
 * PICK NOW").
 */

export interface PickHierarchyExplain {
  /** "NWR PICK NOW: Justin Jefferson (WR)" -- preserves the exact same
   * three-state label (`findPickNow`'s own `PickNowBanner.label`) the
   * pre-existing banner already showed, word for word. */
  headline: string;
  why: string;
  /** Only non-null in the genuine close-call state -- mirrors
   * `PickNowBanner.runnerUp` exactly (null in every other state). */
  alternative: string | null;
  waitAvailability: string;
  rosterEffect: string;
  tone: "recommended" | "warning" | "neutral";
}

function formatSigned(value: number, digits = 1): string {
  const rounded = formatNumber(Math.abs(value), digits);
  return value >= 0 ? `+${rounded}` : `-${rounded}`;
}

// Deliberately duplicated from `draft-room-v2.tsx`'s own `formatMakeItBack`
// (same real fields, same "100%*" survived-every-trial convention) rather
// than imported, so this module stays pure and dependency-free like its
// sibling `*-explain.ts` files (see `trades-explain.ts`'s own precedent for
// `tradeVerdictFor` vs. `in-season.tsx`'s `verdictFor`) and never creates a
// runtime import cycle with the page module that renders it.
function makeItBackText(probability: number | null, trials: number | null): string {
  if (probability == null) return "UNKNOWN";
  const pct = formatNumber(probability * 100, 0);
  return probability >= 0.999 && trials != null ? `${pct}%*` : `${pct}%`;
}

function toneFor(label: PickNowBanner["label"]): PickHierarchyExplain["tone"] {
  if (label === "NWR PICK NOW") return "recommended";
  if (label === "BEST CURRENT PICK — CLOSE CALL") return "warning";
  return "neutral";
}

function explainWhy(row: SuggestionRow, candidate: DecisionBundleCandidate | undefined, label: PickNowBanner["label"]): string {
  // The real, walk-forward-promoted primary ordering signal (see
  // `nwr-post-draft-engine-forensics-v1` -- marginal_roster_utility is the
  // PRIMARY live candidate-ordering signal) -- when the backend supplied
  // its own explanation for this candidate, that IS the "why", verbatim,
  // never paraphrased.
  if (candidate?.marginalRosterUtility?.explanation) return candidate.marginalRosterUtility.explanation;
  if (label === "BEST CURRENT PICK — NO SMASH VALUE") {
    return "Every evaluated candidate this pick shares the same real Championship Equity — a genuine tie in the model's own numbers, not a missing or broken signal.";
  }
  return `Highest Pick Score (${formatNumber(row.pickScore, 1)}) among this pick's evaluated candidates.`;
}

function explainAlternative(runnerUp: SuggestionRow | null, row: SuggestionRow): string | null {
  if (!runnerUp) return null;
  const gap = formatNumber(Math.abs(row.pickScore - runnerUp.pickScore), 1);
  return `${runnerUp.playerName} (${runnerUp.position}) — Pick Score ${formatNumber(runnerUp.pickScore, 1)}, within ${gap} of the top pick.`;
}

function explainWaitAvailability(row: SuggestionRow, isBackToBackTurn: boolean): string {
  const survival = row.makeItBackProbability == null
    ? "Make-It-Back is not evaluated for this candidate"
    : `${makeItBackText(row.makeItBackProbability, row.makeItBackTrials)} modeled chance this player is still available at your next pick if you wait`;
  const cost = `Cost of Waiting ${formatNumber(row.costOfWaiting, 1)}`;
  const backToBack = isBackToBackTurn ? " — though you pick again immediately this turn, so waiting costs nothing this time." : ".";
  return `${survival} (${cost})${backToBack}`;
}

function explainRosterEffect(
  row: SuggestionRow,
  candidate: DecisionBundleCandidate | undefined,
  currentTeamScorePercentile: number | null,
): string {
  const afterText = formatNumber(row.teamScoreAfter, 1);
  const deltaText = formatSigned(row.teamScoreDelta);
  const teamScoreText = currentTeamScorePercentile != null
    ? `Team Score (full draft) ${formatNumber(currentTeamScorePercentile, 1)} → ${afterText} (${deltaText})`
    : `Team Score (full draft) ${afterText} (${deltaText} vs. not taking this pick)`;
  if (!candidate?.marginalRosterUtility) return `${teamScoreText}.`;
  const starterNote = candidate.marginalRosterUtility.becomesStarter
    ? "becomes an immediate starter"
    : `adds bench depth (${candidate.marginalRosterUtility.benchRedundancyBefore} already at this position before the pick)`;
  return `${teamScoreText} — ${starterNote}.`;
}

/**
 * `decisionBundle` is the SAME bundle `SuggestionsTab` already receives --
 * used only to look up the pick-now candidate's own `marginalRosterUtility`
 * and the real current (pre-pick) Team Score, both already flowing to the
 * specialized Draft Room `PlayerDrawer` unchanged. A missing/unavailable
 * bundle degrades honestly (generic Pick-Score-based why, no "before" team
 * score, no starter/bench note) rather than blocking the card.
 */
export function explainPickNow(
  pickNow: PickNowBanner,
  decisionBundle: DecisionBundle | null | undefined,
  isBackToBackTurn: boolean,
): PickHierarchyExplain {
  const { row, runnerUp, label } = pickNow;
  const candidate = decisionBundle && decisionBundle.available
    ? decisionBundle.candidates.find((entry) => entry.playerId === row.playerId)
    : undefined;
  const currentTeamScorePercentile = decisionBundle && decisionBundle.available
    ? decisionBundle.currentTeamScore.percentile
    : null;

  return {
    headline: `${label}: ${row.playerName} (${row.position})`,
    why: explainWhy(row, candidate, label),
    alternative: explainAlternative(runnerUp, row),
    waitAvailability: explainWaitAvailability(row, isBackToBackTurn),
    rosterEffect: explainRosterEffect(row, candidate, currentTeamScorePercentile),
    tone: toneFor(label),
  };
}
