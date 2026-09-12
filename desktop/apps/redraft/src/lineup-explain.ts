import type { WeeklyLineupSlot, WeeklyLineupSwap } from "@nwr/contracts";

/**
 * NWR UI expansion pass (2026-09-12, Lineup surface): the Start/Sit
 * counterpart to `home-action-explain.ts`. Pure, presentation-only --
 * reads ONLY fields the backend already computed on `WeeklyLineupResult`
 * (`swaps`/`starters`, unchanged from `redraft_weekly_lineup`). No new
 * scoring, no new close-call threshold invented here -- "close call" is
 * the exact same already-computed `WeeklyLineupSlot.closeCall` boolean
 * Start/Sit and Weekly Home's START_SIT_CLOSE_CALL card already use (see
 * `home-action-explain.ts`).
 *
 * A swap is Lineup's own definition of "an actual decision" (the backend
 * only emits a swap when NWR's optimal starter differs from Sleeper's
 * current one) -- this module formats that decision using the SAME
 * decision grammar Home uses (headline / why / alternative / impact /
 * confidence / status), it does not invent a second one.
 */

export interface LineupSwapExplanation {
  /** "Start X over Y" -- the recommendation headline. */
  headline: string;
  why: string;
  /** A real, already-computed next-best alternative distinct from the
   * benched player named in the headline -- null is an honest "no
   * further alternative recorded", never a fabricated placeholder. */
  alternative: string | null;
  /** "+X.X projected points" -- the swap's own real projectedDelta. */
  impact: string;
  /** "recommended" for a confident swap, "warning" for a genuine close
   * call -- mirrors Home's own tone rule (`confidence === "LOW" ?
   * "warning" : "recommended"`), never a new visual tier. */
  tone: "recommended" | "warning";
  confidence: "LOW" | null;
  /** The resulting starter's real health/status string (`slot.status`),
   * when the matching post-swap slot is known -- null when no matching
   * slot was found (an honest "unknown", never fabricated). */
  status: string | null;
}

function formatSigned(value: number, digits = 1): string {
  const rounded = value.toFixed(digits);
  return value >= 0 ? `+${rounded}` : rounded;
}

/**
 * `resultingSlot` is the entry in `WeeklyLineupResult.starters` sharing
 * this swap's `slotType` -- i.e. the ALREADY-APPLIED recommendation NWR
 * is showing as this week's starting lineup. Passing `null` (slot not
 * found) degrades honestly: status is left `null`, and the close-call
 * signal is treated as absent (tone stays "recommended") rather than
 * guessed.
 */
export function explainLineupSwap(
  swap: WeeklyLineupSwap,
  resultingSlot: WeeklyLineupSlot | null,
): LineupSwapExplanation {
  const closeCall = resultingSlot?.closeCall ?? false;
  return {
    headline: `Start ${swap.startPlayer} over ${swap.benchPlayer}`,
    why: closeCall
      ? "Projected to outscore the current starter this week -- but the margin over the next-best option is real and small, a genuine close call, not a clear-cut start."
      : `Projected to outscore the current starter at ${swap.slotType} this week.`,
    alternative: closeCall ? (resultingSlot?.closeCallAlternative ?? null) : null,
    impact: `${formatSigned(swap.projectedDelta)} projected points`,
    tone: closeCall ? "warning" : "recommended",
    confidence: closeCall ? "LOW" : null,
    status: resultingSlot?.status ?? null,
  };
}

/** Finds the post-swap starter slot for a given swap. `slotType` alone is
 * NOT a unique key -- a roster can carry more than one starting slot of
 * the same type (two WR slots, both `slotType === "WR"`), and matching
 * only on `slotType` would silently grab the wrong slot's status/close-
 * call data whenever more than one slot of that type exists. The backend
 * itself (`weekly_lineup_optimizer_service._swap_reasons`) builds
 * `startPlayer` literally from that specific slot's `player.playerName`,
 * so requiring both `slotType` AND a matching player name is the real,
 * exact disambiguator already implied by how the data was produced --
 * not a new heuristic. */
export function findResultingSlot(
  swap: WeeklyLineupSwap,
  starters: readonly WeeklyLineupSlot[],
): WeeklyLineupSlot | null {
  return starters.find(
    (slot) => slot.slotType === swap.slotType && slot.player?.playerName === swap.startPlayer,
  ) ?? null;
}
