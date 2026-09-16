import type { RedraftBootstrap, RedraftRanking } from "@nwr/contracts";
import { describe, expect, it } from "vitest";

import { buildCheatSheetCsv, nwrSeasonStatusText } from "./cheat-sheet";

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

/**
 * Full Cycle V1, Worker 4 (Section 3C): same compact status-line
 * convention/coverage shape this file already uses for Ballers/Market --
 * `nwrSeasonStatusText` surfaces the same `data.status.sourceAsOf` the
 * Data Health hero already shows, on the Cheat Sheet header where it was
 * previously absent.
 */
describe("nwrSeasonStatusText", () => {
  it("names the real admission date when one is known", () => {
    const data = { status: { sourceAsOf: "2026-09-08" } } as RedraftBootstrap;
    expect(nwrSeasonStatusText(data)).toBe("NWR: full-season model, admitted 2026-09-08");
  });

  it("degrades honestly (no fabricated date) when the admission date is missing", () => {
    const data = { status: { sourceAsOf: "" } } as RedraftBootstrap;
    expect(nwrSeasonStatusText(data)).toBe("NWR: admission date unavailable");
  });
});
