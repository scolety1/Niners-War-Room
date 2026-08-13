import { NwrApiError } from "@nwr/api-client";
import type { RedraftBootstrap } from "@nwr/contracts";

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isFiniteNumber(value: unknown): boolean {
  return typeof value === "number" && Number.isFinite(value);
}

function isRedraftRanking(value: unknown): boolean {
  return isRecord(value)
    && typeof value.playerId === "string"
    && typeof value.playerName === "string"
    && typeof value.position === "string"
    && typeof value.team === "string"
    && isFiniteNumber(value.overallRank)
    && isFiniteNumber(value.projectedPoints)
    && isFiniteNumber(value.replacementAdjustedValue);
}

function invalidRedraftBootstrap(): never {
  throw new NwrApiError("Redraft data could not be opened safely.", {
    code: "INVALID_REDRAFT_BOOTSTRAP",
    recoveryAction: "Retry the local snapshot. If the problem continues, open Data Health.",
  });
}

export function assertRedraftBootstrap(value: unknown): RedraftBootstrap {
  if (!isRecord(value)
    || !isRecord(value.product)
    || typeof value.product.title !== "string"
    || !isRecord(value.status)
    || typeof value.status.ready !== "boolean"
    || !Array.isArray(value.profiles)
    || !Array.isArray(value.presets)
    || !(value.activeProfileId === null || typeof value.activeProfileId === "string")
    || !(value.activeProfile === null || isRecord(value.activeProfile))
    || !Array.isArray(value.rankings)
    || !value.rankings.every(isRedraftRanking)
    || !Array.isArray(value.replacementLevels)
    || !(value.draftBoard === null || isRecord(value.draftBoard))
    || !isRecord(value.health)
    || typeof value.health.rankedPlayers !== "number"
    || !Number.isFinite(value.health.rankedPlayers)
    || !Array.isArray(value.notices)) {
    return invalidRedraftBootstrap();
  }
  return value as unknown as RedraftBootstrap;
}
