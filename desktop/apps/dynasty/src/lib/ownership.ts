import type { AssetOwnership } from "@nwr/contracts";

export interface OwnershipBadgeDisplay {
  label: string;
  tone: "safe" | "review" | "deprioritized";
  detail: string;
}

/**
 * Dynasty League Import V1 (Worker 3). Pure, testable resolution of what
 * ownership badge/label a governed asset row should show -- follows this
 * codebase's own established `resolveFaabDisplay`-style precedent
 * (`desktop/apps/redraft/src/improve-team-explain.ts`): the decision logic
 * lives here, unit-tested directly, rather than only being exercised via a
 * live browser click-through.
 *
 * `ownership` is the real, annotated `AssetOwnership` block the backend
 * attaches (`dynasty_sleeper_league_service.annotate_ownership`) once a
 * league is connected. It is `undefined`/`null` in exactly two real cases,
 * and this function deliberately returns `null` for both rather than a
 * fabricated badge:
 *   1. No league is connected at all (the byte-identical default state).
 *   2. This specific asset has no ownership concept in a Sleeper roster
 *      (e.g. a `pick:`/`future-pick:` asset) -- `annotate_ownership` never
 *      guesses one, so callers must not either.
 *
 * A real rookie asset DOES get an `ownership` object -- always
 * `UNRESOLVED`, never omitted -- because no Sleeper-ID crosswalk exists
 * yet for the rookie board's synthetic asset IDs (see that function's own
 * docstring). This is the one status this UI must render as an honest
 * "unknown" state, never silently dropped or guessed.
 */
export function resolveOwnershipDisplay(
  ownership: AssetOwnership | null | undefined,
): OwnershipBadgeDisplay | null {
  if (!ownership) return null;
  switch (ownership.ownershipStatus) {
    case "OWNED":
      return ownership.isMyTeam
        ? {
            label: "On your roster",
            tone: "safe",
            detail: ownership.rosterSlotStatus
              ? `Your roster · ${ownership.rosterSlotStatus}`
              : "Your roster",
          }
        : {
            label: `Owned by ${ownership.rosterTeamName || "another team"}`,
            tone: "review",
            detail: ownership.rosterSlotStatus
              ? `Opponent roster · ${ownership.rosterSlotStatus}`
              : "Opponent roster",
          };
    case "FREE_AGENT":
      return {
        label: "Free agent",
        tone: "deprioritized",
        detail: "Unowned in your connected league",
      };
    case "UNRESOLVED":
      return {
        label: "Ownership unresolved",
        tone: "review",
        detail:
          ownership.reason ||
          "No identity crosswalk exists yet for this asset type -- never guessed.",
      };
    default:
      return null;
  }
}
