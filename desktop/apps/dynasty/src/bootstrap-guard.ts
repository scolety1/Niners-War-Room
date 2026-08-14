import { NwrApiError } from "@nwr/api-client";
import type { DynastyBootstrap } from "@nwr/contracts";

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isFiniteNumberOrNull(value: unknown): boolean {
  return value === null || (typeof value === "number" && Number.isFinite(value));
}

function isDynastyRanking(value: unknown): boolean {
  return isRecord(value)
    && typeof value.assetId === "string"
    && typeof value.player === "string"
    && typeof value.position === "string"
    && typeof value.team === "string"
    && isFiniteNumberOrNull(value.rank)
    && isFiniteNumberOrNull(value.nwrScore);
}

function isRookieRanking(value: unknown): boolean {
  return isRecord(value)
    && typeof value.assetId === "string"
    && typeof value.player === "string"
    && typeof value.draftable === "boolean"
    && typeof value.modelScoreEligible === "boolean"
    && isFiniteNumberOrNull(value.rank)
    && isFiniteNumberOrNull(value.boardScore)
    && isFiniteNumberOrNull(value.reviewScore)
    && (value.modelScoreEligible
      ? value.rank !== null && value.boardScore !== null
      : value.rank === null && value.boardScore === null);
}

function isAssetOption(value: unknown): boolean {
  return isRecord(value)
    && typeof value.assetId === "string"
    && typeof value.name === "string"
    && typeof value.selectable === "boolean"
    && typeof value.modelScoreEligible === "boolean";
}

function invalidDynastyBootstrap(): never {
  throw new NwrApiError("Dynasty data could not be opened safely.", {
    code: "INVALID_DYNASTY_BOOTSTRAP",
    recoveryAction: "Retry the local snapshot. If the problem continues, open Data Health.",
  });
}

export function assertDynastyBootstrap(value: unknown): DynastyBootstrap {
  if (!isRecord(value)
    || !isRecord(value.product)
    || typeof value.product.title !== "string"
    || !isRecord(value.status)
    || typeof value.status.ready !== "boolean"
    || !isRecord(value.summary)
    || typeof value.summary.rankedPlayers !== "number"
    || !Number.isFinite(value.summary.rankedPlayers)
    || !Array.isArray(value.rankings)
    || !value.rankings.every(isDynastyRanking)
    || !Array.isArray(value.rookies)
    || !value.rookies.every(isRookieRanking)
    || !Array.isArray(value.assetOptions)
    || !value.assetOptions.every(isAssetOption)
    || !isRecord(value.rookieReadiness)
    || typeof value.rookieReadiness.ready !== "boolean"
    || typeof value.rookieReadiness.officialDrafted !== "number"
    || typeof value.rookieReadiness.missingFromDraftablePool !== "number"
    || !Array.isArray(value.rookieReadiness.surfaceGapAssetIds)
    || !Array.isArray(value.rookieReadiness.draftableAssetIds)
    || !isRecord(value.rookieReadiness.missingBySurface)
    || !isRecord(value.marketFreshness)
    || !isRecord(value.planning)
    || !Array.isArray(value.notices)) {
    return invalidDynastyBootstrap();
  }
  return value as unknown as DynastyBootstrap;
}
