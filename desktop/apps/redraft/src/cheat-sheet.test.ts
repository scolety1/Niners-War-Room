import type { RedraftBootstrap, RedraftRanking } from "@nwr/contracts";
import { describe, expect, it } from "vitest";

import { buildCheatSheetCsv } from "./cheat-sheet";

describe("buildCheatSheetCsv", () => {
  it("exports the exact active Redraft profile and admitted rows", () => {
    const data = {
      activeProfile: {
        leagueName: 'Owner, "Sunday" League',
        season: 2026,
        teamCount: 10,
        scoring: { reception: 1, tePremium: 0.5 },
      },
    } as RedraftBootstrap;
    const rows = [
      {
        playerId: "player-1",
        playerName: "D'Andre Swift",
        overallRank: 17,
        positionRank: 8,
        position: "RB",
        team: "CHI",
        tier: 4,
        projectedPoints: 211.4,
        replacementAdjustedValue: 48.2,
        confidence: "HIGH",
        rookie: false,
        sourceAsOf: "2026-08-11",
      },
    ] as RedraftRanking[];

    const csv = buildCheatSheetCsv(data, rows);

    expect(csv).toContain('"Owner, ""Sunday"" League"');
    expect(csv).toContain("D'Andre Swift");
    expect(csv).toContain("RB8");
    expect(csv).not.toContain("Dynasty");
    expect(csv.endsWith("\r\n")).toBe(true);
  });

  it("fails closed when no league is active", () => {
    expect(buildCheatSheetCsv({ activeProfile: null } as RedraftBootstrap, [])).toBe("");
  });
});
