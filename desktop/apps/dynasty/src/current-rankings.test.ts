import type { DynastyRanking } from "@nwr/contracts";
import { describe, expect, it } from "vitest";

import { currentDynastyRankingRows } from "./pages/rankings";

function row(rank: number, player: string, blocked = false): DynastyRanking {
  return {
    rank,
    player,
    position: "RB",
    team: "TST",
    age: 25,
    positionRank: `RB${rank}`,
    tier: "1",
    nwrScore: 100 - rank,
    nwrView: "Fixture",
    range: "Fixture",
    marketBand: "Aligned",
    marketRank: rank,
    marketGap: 0,
    marketValue: 100 - rank,
    marketDate: "2026-09-01",
    confidence: "High",
    risk: "Fixture",
    assetId: `current:${rank}`,
    currentStatusOverride: blocked ? {
      kind: "SEASON_OUT",
      reason: "Verified fixture status",
      effectiveDate: "2026-09-01",
      verifiedAtUtc: "2026-09-01T00:00:00Z",
      sources: ["https://example.test/status"],
      correctedTeam: "",
    } : null,
  };
}

describe("currentDynastyRankingRows", () => {
  it("moves a verified unavailable player out of current ordinal without changing base rank or score", () => {
    const rows = currentDynastyRankingRows([row(1, "Unavailable", true), row(2, "Available")]);
    expect(rows.map((item) => item.player)).toEqual(["Available", "Unavailable"]);
    expect(rows[0]).toMatchObject({ currentRank: 1, rank: 2, nwrScore: 98 });
    expect(rows[1]).toMatchObject({ currentRank: null, rank: 1, nwrScore: 99 });
  });
});
