import { NwrApiError } from "@nwr/api-client";
import { describe, expect, it } from "vitest";

import { assertDynastyBootstrap } from "./bootstrap-guard";

function validBootstrap(): Record<string, unknown> {
  return {
    product: { title: "Niners War Room — Dynasty" },
    status: { ready: true },
    summary: { rankedPlayers: 1 },
    rankings: [{
      assetId: "player:one",
      player: "Player One",
      position: "WR",
      team: "SF",
      rank: 1,
      nwrScore: 99.5,
    }],
    rookies: [],
    assetOptions: [],
    marketFreshness: {},
    planning: {},
    notices: [],
  };
}

describe("assertDynastyBootstrap", () => {
  it("accepts an essential Dynasty payload", () => {
    expect(assertDynastyBootstrap(validBootstrap()).rankings).toHaveLength(1);
  });

  it("rejects null data with an owner-friendly contract error", () => {
    expect(() => assertDynastyBootstrap(null)).toThrow(NwrApiError);
    try {
      assertDynastyBootstrap(null);
    } catch (error) {
      expect((error as NwrApiError).code).toBe("INVALID_DYNASTY_BOOTSTRAP");
      expect((error as Error).message).not.toContain("undefined");
    }
  });

  it("rejects a payload missing rankings", () => {
    const value = validBootstrap();
    delete value.rankings;
    expect(() => assertDynastyBootstrap(value)).toThrow("Dynasty data could not be opened safely.");
  });

  it("rejects a wrong scalar type inside a ranking row", () => {
    const value = validBootstrap();
    (value.rankings as Array<Record<string, unknown>>)[0]!.rank = "1";
    expect(() => assertDynastyBootstrap(value)).toThrow("Dynasty data could not be opened safely.");
  });
});
