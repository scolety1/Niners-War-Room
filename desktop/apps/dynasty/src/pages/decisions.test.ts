import { describe, expect, it } from "vitest";
import type { AssetOption } from "@nwr/contracts";

import {
  isCurrentDecisionRequest,
  isSameTradePackage,
  nextTradeSide,
  ownerDimensionLabel,
  canSelectAsset,
} from "./decisions";

const stribling: AssetOption = {
  assetId: "blocked-rookie:dezhaun-stribling",
  name: "De'Zhaun Stribling",
  assetType: "Blocked Rookie",
  position: "WR",
  team: "SF",
  rank: null,
  authority: "UNSCORED_MANUAL_REVIEW",
  blocked: false,
  selectable: true,
  searchable: true,
  draftEligible: true,
  modelScoreEligible: false,
  evidenceBlocked: true,
  scoreStatus: "No admitted Rookie Review score — manual review required",
  identityStatus: "EXACT_GOVERNED_IDENTITY",
  playerId: "00-0041035",
  draftRound: 2,
  overallPick: 33,
  refreshAvailable: true,
};

describe("decision input guards", () => {
  it("prevents a trade asset from being added across both sides", () => {
    expect(nextTradeSide(["current:a"], ["current:b"], "current:b")).toEqual([
      "current:a",
    ]);
    expect(nextTradeSide(["current:a"], [], "current:c")).toEqual([
      "current:a",
      "current:c",
    ]);
    expect(nextTradeSide(["current:a"], ["current:b"], "current:a")).toEqual([]);
  });

  it("rejects responses from an older request or input revision", () => {
    expect(isCurrentDecisionRequest(3, 7, 3, 7)).toBe(true);
    expect(isCurrentDecisionRequest(2, 7, 3, 7)).toBe(false);
    expect(isCurrentDecisionRequest(3, 6, 3, 7)).toBe(false);
  });

  it("requires save and export to match the exact evaluated package", () => {
    expect(
      isSameTradePackage(
        ["current:a", "pick:2027:1st"],
        ["current:b", "pick:2028:2nd"],
        ["current:a", "pick:2027:1st"],
        ["current:b", "pick:2028:2nd"],
      ),
    ).toBe(true);
    expect(
      isSameTradePackage(
        ["current:a", "pick:2027:1st"],
        ["current:b"],
        ["current:a", "pick:2027:1st"],
        ["current:b", "pick:2028:2nd"],
      ),
    ).toBe(false);
  });

  it("renders machine evidence fields as owner-facing labels", () => {
    expect(ownerDimensionLabel("tierOrBand")).toBe("Tier Or Band");
    expect(ownerDimensionLabel("outcome_support")).toBe("Outcome support");
    expect(ownerDimensionLabel("reviewFlags")).toBe("Review Flags");
  });

  it("keeps a draft-eligible unscored rookie selectable", () => {
    expect(canSelectAsset(stribling)).toBe(true);
    expect(stribling.modelScoreEligible).toBe(false);
    expect(stribling.blocked).toBe(false);
  });
});
