import { describe, expect, it } from "vitest";
import type { AssetOption, AssetOwnership, BridgeDecision, DynastyComparison } from "@nwr/contracts";

import {
  bridgeBadgeTone,
  bridgeDecisionGroups,
  isCurrentDecisionRequest,
  isSameTradePackage,
  nextTradeSide,
  ownerBridgePreference,
  ownerDimensionLabel,
  canSelectAsset,
  resolveTradeRosterWarnings,
  tradeAssetsForMode,
  tradeCounterparties,
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
  it("keeps rookie-veteran horizons and authority badges explicit", () => {
    const decisionInputs: Array<[string, BridgeDecision["badge"]]> = [
      ["win", "PRODUCTION"],
      ["today", "RESEARCH ONLY"],
      ["three", "RESEARCH ONLY"],
      ["long", "INSUFFICIENT EVIDENCE"],
      ["safety", "REVIEW"],
      ["upside", "RESEARCH ONLY"],
      ["uncertainty", "REVIEW"],
    ];
    const decisions = decisionInputs.map(([key, badge]) => ({
      key,
      label: key,
      preferred: "TOO CLOSE",
      badge,
      authority: "test",
      reason: "test",
      evidence: [],
    }));
    const result = {
      leans: [],
      ranges: [],
      players: [],
      warnings: [],
      bridge: {
        mode: "ROOKIE_VETERAN",
        players: ["Rookie", "Veteran"],
        decisions,
        immediateProduction: [],
        why: [],
        warnings: [],
      },
    } satisfies DynastyComparison;

    expect(bridgeDecisionGroups(result).horizons).toHaveLength(4);
    expect(bridgeDecisionGroups(result).traits).toHaveLength(3);
    expect(bridgeBadgeTone("PRODUCTION")).toBe("safe");
    expect(bridgeBadgeTone("RESEARCH ONLY")).toBe("review");
    expect(bridgeBadgeTone("INSUFFICIENT EVIDENCE")).toBe("blocked");
    expect(ownerBridgePreference("Gibbs", "RESEARCH ONLY")).toBe("NWR research leans Gibbs");
    expect(ownerBridgePreference("TOO CLOSE", "RESEARCH ONLY")).toBe("TOO CLOSE");
    expect(ownerBridgePreference("Veteran", "PRODUCTION")).toBe("Veteran");
  });

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

function ownership(overrides: Partial<AssetOwnership> = {}): AssetOwnership {
  return {
    ownershipStatus: "OWNED",
    rosterId: 7,
    rosterTeamName: "Niners",
    rosterSlotStatus: "starter",
    isMyTeam: true,
    reason: "",
    ...overrides,
  };
}

function assetWithOwnership(
  assetId: string,
  overrides: Partial<AssetOwnership> = {},
): AssetOption {
  return { ...stribling, assetId, name: assetId, ownership: ownership(overrides) };
}

describe("real-trade ownership gating", () => {
  it("limits outgoing to the owner's real roster and incoming to the selected opponent", () => {
    const assets: AssetOption[] = [
      assetWithOwnership("current:mine-1", { isMyTeam: true }),
      assetWithOwnership("current:opponent", {
        isMyTeam: false,
        rosterId: 9,
        rosterTeamName: "Rocky Mountain High",
      }),
      assetWithOwnership("current:other-opponent", {
        isMyTeam: false,
        rosterId: 4,
        rosterTeamName: "Fourth Team",
      }),
      assetWithOwnership("current:free-agent", {
        ownershipStatus: "FREE_AGENT",
        isMyTeam: false,
        rosterId: null,
        rosterTeamName: null,
      }),
      { ...stribling, assetId: "rookie:unresolved" },
    ];
    expect(tradeAssetsForMode(assets, "give", "REAL", 9).map((asset) => asset.assetId))
      .toEqual(["current:mine-1"]);
    expect(tradeAssetsForMode(assets, "receive", "REAL", 9).map((asset) => asset.assetId))
      .toEqual(["current:opponent"]);
    expect(tradeAssetsForMode(assets, "receive", "REAL", null)).toEqual([]);
    expect(tradeAssetsForMode(assets, "give", "HYPOTHETICAL", null)).toHaveLength(5);
  });

  it("builds one stable opponent choice per real roster", () => {
    const assets = [
      assetWithOwnership("current:a", { isMyTeam: false, rosterId: 9, rosterTeamName: "Rocky" }),
      assetWithOwnership("current:b", { isMyTeam: false, rosterId: 9, rosterTeamName: "Rocky" }),
      assetWithOwnership("current:c", { isMyTeam: false, rosterId: 4, rosterTeamName: "Alpha" }),
      assetWithOwnership("current:mine", { isMyTeam: true }),
    ];
    expect(tradeCounterparties(assets)).toEqual([
      { rosterId: 4, teamName: "Alpha" },
      { rosterId: 9, teamName: "Rocky" },
    ]);
  });

  it("flags a give-side asset the owner does not actually hold -- opponent, free agent, and unresolved rookie cases", () => {
    const map = new Map<string, AssetOwnership>([
      ["current:mine", ownership({ isMyTeam: true })],
      ["current:opponent", ownership({ isMyTeam: false, rosterTeamName: "Rocky Mountain High" })],
      ["current:free-agent", ownership({ ownershipStatus: "FREE_AGENT", isMyTeam: false, rosterTeamName: null })],
      ["rookie:x", ownership({ ownershipStatus: "UNRESOLVED", isMyTeam: false, reason: "No crosswalk yet." })],
    ]);
    const name = (id: string) => `Name(${id})`;
    const warnings = resolveTradeRosterWarnings(
      ["current:mine", "current:opponent", "current:free-agent", "rookie:x"],
      [],
      map,
      name,
    );
    expect(warnings).toHaveLength(3);
    expect(warnings.map((warning) => warning.kind)).toEqual([
      "GIVE_OWNED_BY_OPPONENT",
      "GIVE_NOT_ON_ROSTER",
      "GIVE_UNRESOLVED",
    ]);
    expect(warnings.at(0)?.message).toContain("Rocky Mountain High");
    expect(warnings.at(2)?.message).toContain("No crosswalk yet.");
  });

  it("flags a receive-side asset already on the owner's roster, and never warns on an asset with no ownership concept", () => {
    const map = new Map<string, AssetOwnership>([
      ["current:mine", ownership({ isMyTeam: true })],
    ]);
    const warnings = resolveTradeRosterWarnings(
      ["pick:2027:1st"],
      ["current:mine"],
      map,
      (id) => id,
    );
    expect(warnings).toEqual([
      { assetId: "current:mine", kind: "RECEIVE_ALREADY_OWNED", message: expect.stringContaining("already on your roster") },
    ]);
  });

  it("never warns when ownership data is entirely absent (no league connected)", () => {
    expect(resolveTradeRosterWarnings(["current:a"], ["current:b"], new Map(), (id) => id)).toEqual(
      [],
    );
  });
});
