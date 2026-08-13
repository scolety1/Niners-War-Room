import { NwrApiError } from "@nwr/api-client";
import { describe, expect, it } from "vitest";

import { assertRedraftBootstrap } from "./bootstrap-guard";

function validBootstrap(): Record<string, unknown> {
  return {
    product: { title: "Niners War Room — Redraft" },
    status: { ready: true },
    profiles: [],
    presets: [],
    activeProfileId: null,
    activeProfile: null,
    rankings: [{
      playerId: "player:one",
      playerName: "Player One",
      position: "WR",
      team: "SF",
      overallRank: 1,
      projectedPoints: 250,
      replacementAdjustedValue: 100,
    }],
    replacementLevels: [],
    draftBoard: null,
    health: { rankedPlayers: 1 },
    notices: [],
  };
}

describe("assertRedraftBootstrap", () => {
  it("accepts an essential Redraft payload", () => {
    expect(assertRedraftBootstrap(validBootstrap()).rankings).toHaveLength(1);
  });

  it("rejects null data with an owner-friendly contract error", () => {
    expect(() => assertRedraftBootstrap(null)).toThrow(NwrApiError);
    try {
      assertRedraftBootstrap(null);
    } catch (error) {
      expect((error as NwrApiError).code).toBe("INVALID_REDRAFT_BOOTSTRAP");
      expect((error as Error).message).not.toContain("undefined");
    }
  });

  it("rejects a payload missing rankings", () => {
    const value = validBootstrap();
    delete value.rankings;
    expect(() => assertRedraftBootstrap(value)).toThrow("Redraft data could not be opened safely.");
  });

  it("rejects a wrong scalar type inside a ranking row", () => {
    const value = validBootstrap();
    (value.rankings as Array<Record<string, unknown>>)[0]!.overallRank = "1";
    expect(() => assertRedraftBootstrap(value)).toThrow("Redraft data could not be opened safely.");
  });
});
