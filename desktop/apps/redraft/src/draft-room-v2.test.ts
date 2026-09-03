import { describe, expect, it } from "vitest";

import {
  buildCompareRows,
  buildMyTeamSummary,
  buildSuggestionsRows,
  buildUdkBadges,
  generateCompareSummary,
  severityToBadgeTone,
  tabLabel,
  toggleCompareSelection,
} from "./draft-room-v2";

describe("tabLabel", () => {
  it("title-cases every tab and special-cases MY_TEAM", () => {
    expect(tabLabel("SUGGESTIONS")).toBe("Suggestions");
    expect(tabLabel("PLAYERS")).toBe("Players");
    expect(tabLabel("BOARD")).toBe("Board");
    expect(tabLabel("MY_TEAM")).toBe("My Team");
    expect(tabLabel("COMPARE")).toBe("Compare");
  });
});

describe("buildSuggestionsRows", () => {
  const board = {
    beatAdpPool: [
      {
        playerId: "p1", playerName: "Star Runner", position: "RB", team: "SEA",
        nwrRank: 5, expectedPick: 8, overallAdp: 8, nwrEdge: 3, nwrView: "Undervalued",
        draftTiming: "Take now", makeItBackProbability: 0.12, makeItBackMethod: "SIMULATED",
        confidence: "HIGH",
      },
      {
        playerId: "p2", playerName: "Deep Sleeper", position: "WR", team: "DET",
        nwrRank: 90, expectedPick: null, overallAdp: null, nwrEdge: null, nwrView: "Fair value",
        draftTiming: "Wait", makeItBackProbability: null, makeItBackMethod: "UNAVAILABLE",
        confidence: "LOW",
      },
    ],
  } as any;

  it("maps beatAdpPool rows into dense suggestion rows with real fields", () => {
    const rows = buildSuggestionsRows(board, new Map());
    expect(rows).toHaveLength(2);
    expect(rows[0]).toMatchObject({
      playerId: "p1", playerName: "Star Runner", nwrRank: 5, marketExpectedPick: 8, nwrEdge: 3,
    });
  });

  it("falls back to overallAdp for marketExpectedPick and the method label when probability is unavailable", () => {
    const rows = buildSuggestionsRows(board, new Map());
    expect(rows[1]!.marketExpectedPick).toBeNull();
    expect(rows[1]!.makeItBack).toBe("UNAVAILABLE");
  });

  it("never fabricates a SHADOW/RESEARCH number -- always the disclosed placeholder", () => {
    const rows = buildSuggestionsRows(board, new Map());
    for (const row of rows) {
      expect(row.pickScore).toBe("Not connected — SHADOW/RESEARCH backend");
      expect(row.teamScoreAfter).toBe("Not connected — SHADOW/RESEARCH backend");
      expect(row.championshipEquityAfter).toBe("Not connected — SHADOW/RESEARCH backend");
    }
  });

  it("respects the limit and returns an empty array with no board", () => {
    expect(buildSuggestionsRows(board, new Map(), 1)).toHaveLength(1);
    expect(buildSuggestionsRows(null, new Map())).toEqual([]);
    expect(buildSuggestionsRows(undefined, new Map())).toEqual([]);
  });

  it("attaches a real alert from the intel map when present", () => {
    const intel = new Map([["p1", { currentAlert: "Ankle sprain", currentAlertSeverity: "HIGH" } as any]]);
    const rows = buildSuggestionsRows(board, intel);
    expect(rows[0]!.alertText).toBe("Ankle sprain");
    expect(rows[0]!.alertSeverity).toBe("HIGH");
    expect(rows[1]!.alertText).toBeNull();
  });
});

describe("buildMyTeamSummary", () => {
  const data = {
    draftBoard: {
      myRoster: [
        { playerId: "p1", playerName: "QB One", position: "QB", team: "SEA", pickNumber: 9 },
        { playerId: "p2", playerName: "RB One", position: "RB", team: "DET", pickNumber: 24 },
      ],
    },
    activeProfile: { roster: { qb: 1, rb: 2, wr: 2, te: 1, flex: 1, superflex: 0, k: 1, dst: 1, benchSize: 6 } },
  } as any;

  it("classifies filled slots as strengths and unfilled slots as holes", () => {
    const summary = buildMyTeamSummary(data);
    expect(summary.strengths).toContain("QB (1/1)");
    expect(summary.holes).toContain("RB (1/2)");
    expect(summary.holes).toContain("WR (0/2)");
    expect(summary.holes).toContain("TE (0/1)");
  });

  it("returns an empty summary when there is no active profile roster shape", () => {
    const summary = buildMyTeamSummary({ draftBoard: { myRoster: [] } } as any);
    expect(summary.strengths).toEqual([]);
    expect(summary.holes).toEqual([]);
  });
});

describe("severityToBadgeTone", () => {
  it("maps HIGH/MEDIUM/other to blocked/review/safe", () => {
    expect(severityToBadgeTone("HIGH")).toBe("blocked");
    expect(severityToBadgeTone("MEDIUM")).toBe("review");
    expect(severityToBadgeTone("LOW")).toBe("safe");
    expect(severityToBadgeTone(null)).toBe("safe");
    expect(severityToBadgeTone(undefined)).toBe("safe");
  });
});

describe("buildUdkBadges", () => {
  it("returns no badges for an undefined entry", () => {
    expect(buildUdkBadges(undefined)).toEqual([]);
  });

  it("builds a badge per real available UDK/alert field, never inventing one", () => {
    const badges = buildUdkBadges({
      udkPositionRank: "4", udkTier: "1", currentAlert: "Role uncertainty", currentAlertSeverity: "MEDIUM",
    } as any);
    expect(badges.map((badge) => badge.key)).toEqual(["udk-rank", "udk-tier", "alert"]);
    expect(badges.find((badge) => badge.key === "alert")?.tone).toBe("review");
  });

  it("omits a badge for a field that is not present", () => {
    const badges = buildUdkBadges({ udkPositionRank: null, udkTier: null, currentAlert: null } as any);
    expect(badges).toEqual([]);
  });
});

describe("toggleCompareSelection", () => {
  it("adds an unselected player and removes an already-selected one", () => {
    expect(toggleCompareSelection([], "p1")).toEqual(["p1"]);
    expect(toggleCompareSelection(["p1"], "p1")).toEqual([]);
    expect(toggleCompareSelection(["p1"], "p2")).toEqual(["p1", "p2"]);
  });

  it("never exceeds the max selection count", () => {
    const atMax = ["p1", "p2", "p3", "p4"];
    expect(toggleCompareSelection(atMax, "p5", 4)).toEqual(atMax);
    // removing one that IS selected still works even at max
    expect(toggleCompareSelection(atMax, "p1", 4)).toEqual(["p2", "p3", "p4"]);
  });
});

describe("buildCompareRows", () => {
  const data = {
    rankings: [
      { playerId: "p1", playerName: "Ranked One", position: "RB", overallRank: 5, overallAdp: 8, overallTierLabel: "Tier 1" },
    ],
    manualAssets: [
      { playerId: "m1", playerName: "Manual One", position: "K", overallAdp: null },
    ],
  } as any;

  it("resolves both ranked and manual players, skipping unknown ids", () => {
    const rows = buildCompareRows(["p1", "m1", "unknown"], data, new Map());
    expect(rows).toHaveLength(2);
    expect(rows[0]).toMatchObject({ playerId: "p1", nwrRank: 5, overallAdp: 8 });
    expect(rows[1]).toMatchObject({ playerId: "m1", nwrRank: null });
  });

  it("surfaces a real current alert as status when present", () => {
    const intel = new Map([["p1", { currentAlert: "Trade rumor", currentAlertSeverity: "LOW" } as any]]);
    const rows = buildCompareRows(["p1"], data, intel);
    expect(rows[0]!.status).toBe("Alert: LOW");
  });
});

describe("generateCompareSummary", () => {
  it("asks for at least two players when fewer are selected", () => {
    expect(generateCompareSummary([], {})).toMatch(/at least two/);
  });

  it("calls out the best NWR rank, the largest ADP discount, and the deepest position", () => {
    const rows = [
      { playerId: "a", playerName: "Player A", position: "QB", nwrRank: 20, overallAdp: 25, tier: null, status: "" },
      { playerId: "b", playerName: "Player B", position: "RB", nwrRank: 5, overallAdp: 40, tier: null, status: "" },
    ];
    const summary = generateCompareSummary(rows, { QB: 10, RB: 30 });
    expect(summary).toContain("Player B has the best NWR rank (#5)");
    expect(summary).toContain("Player B offers the largest market discount");
    expect(summary).toContain("RB is the deepest position");
  });

  it("never fabricates a claim when the underlying structured field is missing", () => {
    const rows = [
      { playerId: "a", playerName: "Player A", position: "QB", nwrRank: null, overallAdp: null, tier: null, status: "" },
      { playerId: "b", playerName: "Player B", position: "QB", nwrRank: null, overallAdp: null, tier: null, status: "" },
    ];
    const summary = generateCompareSummary(rows, {});
    expect(summary).not.toContain("best NWR rank");
    expect(summary).not.toContain("market discount");
  });
});
