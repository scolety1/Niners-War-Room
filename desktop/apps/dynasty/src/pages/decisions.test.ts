import { describe, expect, it } from "vitest";

import {
  isCurrentDecisionRequest,
  isSameTradePackage,
  nextTradeSide,
  ownerDimensionLabel,
} from "./decisions";

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
});
