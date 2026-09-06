import { describe, expect, it } from "vitest";

import {
  buildCompareRows,
  buildCurrentRosterScores,
  buildMyTeamSummary,
  buildPositionDemand,
  buildRosterStrip,
  buildSuggestionsRows,
  buildUdkBadges,
  findCloseCall,
  generateCompareSummary,
  severityToBadgeTone,
  tabLabel,
  toggleCompareSelection,
} from "./draft-room-v2";

describe("tabLabel", () => {
  // Consolidation pass: PLAYERS -> "Rankings" and MY_TEAM -> "Teams" match
  // the directive's secondary-workspace naming (Rankings/Teams/Queue).
  it("title-cases every tab and special-cases the renamed workspace tabs", () => {
    expect(tabLabel("SUGGESTIONS")).toBe("Suggestions");
    expect(tabLabel("CHEAT_SHEET")).toBe("Cheat Sheets");
    expect(tabLabel("PLAYERS")).toBe("Rankings");
    expect(tabLabel("BOARD")).toBe("Draft Board");
    expect(tabLabel("QUEUE")).toBe("Queue");
    expect(tabLabel("MY_TEAM")).toBe("Teams");
    expect(tabLabel("COMPARE")).toBe("Compare");
  });

  it("special-cases REPLAY to a readable label", () => {
    expect(tabLabel("REPLAY")).toBe("Historical Replay");
  });
});

function _candidate(overrides: Record<string, unknown> = {}) {
  return {
    playerId: "p1", playerName: "Star Runner", position: "RB",
    playerScore: 88.2, teamScoreAfter: 72.8, teamScoreDelta: 8.6,
    championshipEquityAfter: 0.107, equityGain: 0.023, costOfWaiting: 4.1,
    makeItBackProbability: 0.12, rawDecisionUtility: 10.9,
    teamScoreUtilityComponent: 8.6, equityUtilityComponent: 2.3,
    pickScore: 94.0, action: "TAKE NOW", warnings: [], uncertainty: "LOW_MODEL_UNCERTAINTY (SE=0.0100)",
    ...overrides,
  };
}

function _availableBundle(candidates: Array<Record<string, unknown>>) {
  return {
    available: true, speed: "FAST", version: "decision-bundle-live-v1",
    currentTeamScore: { percentile: 64.2, rosterValue: 1000, populationSize: 200, label: "TEAM SCORE — RESEARCH" },
    currentChampionshipEquity: { winProbability: 0.084, standardError: 0.01, seasonsSimulated: 200, assumedFormat: true, label: "SIMULATED CHAMPIONSHIP EQUITY — RESEARCH" },
    candidates,
    provenance: {}, simulationMetadata: {}, latencySeconds: 0.5,
  } as any;
}

describe("buildSuggestionsRows", () => {
  const rankings = [
    { playerId: "p1", playerName: "Star Runner", position: "RB", team: "SEA", overallRank: 5, overallAdp: 8, expectedPick: 8 },
    { playerId: "p2", playerName: "Deep Sleeper", position: "WR", team: "DET", overallRank: 90, overallAdp: null, expectedPick: null },
  ] as any;

  it("maps DecisionBundle candidates into rows, sorted by Pick Score descending", () => {
    const bundle = _availableBundle([
      _candidate({ playerId: "p2", playerName: "Deep Sleeper", position: "WR", pickScore: 40, makeItBackProbability: null }),
      _candidate({ playerId: "p1", pickScore: 94 }),
    ]);
    const rows = buildSuggestionsRows(bundle, rankings, new Map());
    expect(rows).toHaveLength(2);
    expect(rows[0]!.playerId).toBe("p1");
    expect(rows[0]!.pickScore).toBe(94);
    expect(rows[1]!.playerId).toBe("p2");
  });

  it("enriches candidates with real NWR rank / market data from rankings", () => {
    const bundle = _availableBundle([_candidate()]);
    const rows = buildSuggestionsRows(bundle, rankings, new Map());
    expect(rows[0]).toMatchObject({ nwrRank: 5, marketExpectedPick: 8 });
  });

  it("never fabricates data -- returns empty rows when the bundle is unavailable", () => {
    expect(buildSuggestionsRows({ available: false, speed: "FAST", reason: "blocked" } as any, rankings, new Map())).toEqual([]);
    expect(buildSuggestionsRows(null, rankings, new Map())).toEqual([]);
    expect(buildSuggestionsRows(undefined, rankings, new Map())).toEqual([]);
  });

  it("merges real Raw Action Value (expected regret / decision-quality percentile) by playerId from the separate V2 bundle -- the fix for the Fantasy Gamers Pick-Score-collapse bug", () => {
    const bundle = _availableBundle([_candidate({ playerId: "p1", pickScore: 50 }), _candidate({ playerId: "p2", pickScore: 50 })]);
    const rav = new Map([
      ["p1", { playerId: "p1", v2Status: "OK", teamScoreV2: null, championshipEquityV2: null, pickScore: 50, rawActionValue: null, expectedRegret: 0.0, decisionQualityPercentile: 100.0, rawActionValueStatus: "OK" }],
      ["p2", { playerId: "p2", v2Status: "OK", teamScoreV2: null, championshipEquityV2: null, pickScore: 50, rawActionValue: null, expectedRegret: 29.4, decisionQualityPercentile: 12.0, rawActionValueStatus: "OK" }],
    ]) as any;
    const rows = buildSuggestionsRows(bundle, rankings, new Map(), rav);
    // Both candidates legitimately tie on Pick Score (the real, disclosed,
    // never-modified V1 formula's own behavior) -- Raw Action Value still
    // differentiates them, which is the entire point of this fix.
    expect(rows.find((row) => row.playerId === "p1")).toMatchObject({ pickScore: 50, expectedRegret: 0.0, decisionQualityPercentile: 100.0 });
    expect(rows.find((row) => row.playerId === "p2")).toMatchObject({ pickScore: 50, expectedRegret: 29.4, decisionQualityPercentile: 12.0 });
  });

  it("carries RAV fields as null (never fabricated) for a candidate outside the RAV preset's top-N", () => {
    const bundle = _availableBundle([_candidate({ playerId: "p1" })]);
    const rows = buildSuggestionsRows(bundle, rankings, new Map());
    expect(rows[0]).toMatchObject({ expectedRegret: null, decisionQualityPercentile: null, rawActionValueStatus: null });
  });

  it("carries make_it_back as null (never fabricated) when the backend has no real ADP for a candidate", () => {
    const bundle = _availableBundle([_candidate({ playerId: "p2", makeItBackProbability: null })]);
    const rows = buildSuggestionsRows(bundle, rankings, new Map());
    expect(rows[0]!.makeItBackProbability).toBeNull();
  });

  it("attaches a real alert from the intel map when present", () => {
    const intel = new Map([["p1", { currentAlert: "Ankle sprain", currentAlertSeverity: "HIGH" } as any]]);
    const bundle = _availableBundle([_candidate()]);
    const rows = buildSuggestionsRows(bundle, rankings, intel);
    expect(rows[0]!.alertText).toBe("Ankle sprain");
    expect(rows[0]!.alertSeverity).toBe("HIGH");
  });
});

describe("buildCurrentRosterScores", () => {
  it("surfaces the real current Team Score / Championship Equity from an available bundle", () => {
    const bundle = _availableBundle([]);
    const scores = buildCurrentRosterScores(bundle);
    expect(scores.teamScorePercentile).toBe(64.2);
    expect(scores.championshipEquityWinProbability).toBe(0.084);
    expect(scores.assumedFormat).toBe(true);
  });

  it("never fabricates a score when the bundle is unavailable", () => {
    const scores = buildCurrentRosterScores({ available: false, speed: "FAST", reason: "blocked" } as any);
    expect(scores.teamScorePercentile).toBeNull();
    expect(scores.championshipEquityWinProbability).toBeNull();
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
    expect(rows[0]).toMatchObject({ playerId: "p1", nwrRank: 5, overallAdp: 8, evaluated: false });
    expect(rows[1]).toMatchObject({ playerId: "m1", nwrRank: null, evaluated: false });
  });

  it("surfaces a real current alert as status when present", () => {
    const intel = new Map([["p1", { currentAlert: "Trade rumor", currentAlertSeverity: "LOW" } as any]]);
    const rows = buildCompareRows(["p1"], data, intel);
    expect(rows[0]!.status).toBe("Alert: LOW");
  });

  it("attaches real DecisionBundle fields when the player is a current candidate", () => {
    const bundle = _availableBundle([_candidate({ playerId: "p1", pickScore: 77 })]);
    const rows = buildCompareRows(["p1"], data, new Map(), bundle);
    expect(rows[0]!.evaluated).toBe(true);
    expect(rows[0]!.pickScore).toBe(77);
    expect(rows[0]!.teamScoreDelta).toBe(8.6);
  });

  it("leaves DecisionBundle fields null (never fabricated) for a non-candidate player", () => {
    const bundle = _availableBundle([_candidate({ playerId: "someone-else" })]);
    const rows = buildCompareRows(["p1"], data, new Map(), bundle);
    expect(rows[0]!.evaluated).toBe(false);
    expect(rows[0]!.pickScore).toBeNull();
  });
});

describe("generateCompareSummary", () => {
  it("asks for at least two players when fewer are selected", () => {
    expect(generateCompareSummary([], {})).toMatch(/at least two/);
  });

  it("calls out the best NWR rank, the largest ADP discount, and the deepest position", () => {
    const rows = [
      { playerId: "a", playerName: "Player A", position: "QB", nwrRank: 20, overallAdp: 25, tier: null, status: "", playerScore: null, teamScoreDelta: null, equityGain: null, costOfWaiting: null, makeItBackProbability: null, pickScore: null, action: null, warnings: [], evaluated: false },
      { playerId: "b", playerName: "Player B", position: "RB", nwrRank: 5, overallAdp: 40, tier: null, status: "", playerScore: null, teamScoreDelta: null, equityGain: null, costOfWaiting: null, makeItBackProbability: null, pickScore: null, action: null, warnings: [], evaluated: false },
    ];
    const summary = generateCompareSummary(rows, { QB: 10, RB: 30 });
    expect(summary).toContain("Player B has the best NWR rank (#5)");
    expect(summary).toContain("Player B offers the largest market discount");
    expect(summary).toContain("RB is the deepest position");
  });

  it("never fabricates a claim when the underlying structured field is missing", () => {
    const rows = [
      { playerId: "a", playerName: "Player A", position: "QB", nwrRank: null, overallAdp: null, tier: null, status: "", playerScore: null, teamScoreDelta: null, equityGain: null, costOfWaiting: null, makeItBackProbability: null, pickScore: null, action: null, warnings: [], evaluated: false },
      { playerId: "b", playerName: "Player B", position: "QB", nwrRank: null, overallAdp: null, tier: null, status: "", playerScore: null, teamScoreDelta: null, equityGain: null, costOfWaiting: null, makeItBackProbability: null, pickScore: null, action: null, warnings: [], evaluated: false },
    ];
    const summary = generateCompareSummary(rows, {});
    expect(summary).not.toContain("best NWR rank");
    expect(summary).not.toContain("market discount");
  });

  it("cites the highest Pick Score among evaluated candidates when available", () => {
    const rows = [
      { playerId: "a", playerName: "Player A", position: "QB", nwrRank: 20, overallAdp: 25, tier: null, status: "", playerScore: 50, teamScoreDelta: 2, equityGain: 0.01, costOfWaiting: 1, makeItBackProbability: 0.5, pickScore: 40, action: "WAIT", warnings: [], evaluated: true },
      { playerId: "b", playerName: "Player B", position: "RB", nwrRank: 5, overallAdp: 40, tier: null, status: "", playerScore: 80, teamScoreDelta: 8, equityGain: 0.03, costOfWaiting: 3, makeItBackProbability: 0.2, pickScore: 90, action: "TAKE NOW", warnings: [], evaluated: true },
    ];
    const summary = generateCompareSummary(rows, { QB: 10, RB: 30 });
    expect(summary).toContain("Player B has the highest Pick Score");
  });
});

function _rosterPlayer(position: string, pickNumber = 1) {
  return { playerId: `${position}-${pickNumber}`, playerName: `${position} Player`, position, team: "TST", pickNumber };
}

function _team(teamSlot: number, owner: boolean, roster: Array<Record<string, unknown>>) {
  return { teamSlot, name: owner ? "My Team" : `Team ${teamSlot}`, owner, roster, picks: [] } as any;
}

describe("buildPositionDemand", () => {
  const profile = { roster: { qb: 1, rb: 2, wr: 2, te: 1, flex: 1, superflex: 0, k: 1, dst: 1, benchSize: 5 } } as any;

  it("counts opponents (never the owner) who already have a full starting group at QB/TE", () => {
    const board = {
      teams: [
        _team(1, true, [_rosterPlayer("QB")]), // owner -- must never be counted as an "opponent"
        _team(2, false, [_rosterPlayer("QB")]), // filled
        _team(3, false, [_rosterPlayer("RB")]), // not filled
        _team(4, false, [_rosterPlayer("QB"), _rosterPlayer("TE")]), // filled QB and TE
      ],
    } as any;
    const rows = buildPositionDemand(board, profile);
    const qb = rows.find((row) => row.position === "QB")!;
    const te = rows.find((row) => row.position === "TE")!;
    expect(qb).toEqual({ position: "QB", filledOpponents: 2, totalOpponents: 3, requiredStarters: 1 });
    expect(te).toEqual({ position: "TE", filledOpponents: 1, totalOpponents: 3, requiredStarters: 1 });
  });

  it("returns [] when there is no board or profile yet", () => {
    expect(buildPositionDemand(null, profile)).toEqual([]);
    expect(buildPositionDemand({ teams: [] } as any, null)).toEqual([]);
  });
});

describe("buildRosterStrip", () => {
  it("reproduces the same starter-slot accounting as the production Draft Room (FLEX overflow, capped bench)", () => {
    const data = {
      activeProfile: { roster: { qb: 1, rb: 2, wr: 2, te: 1, flex: 1, superflex: 0, k: 1, dst: 1, benchSize: 5 } },
      draftBoard: {
        myRoster: [
          _rosterPlayer("QB", 1), _rosterPlayer("RB", 2), _rosterPlayer("RB", 3), _rosterPlayer("RB", 4),
          _rosterPlayer("WR", 5), _rosterPlayer("K", 6),
        ],
      },
    } as any;
    const strip = buildRosterStrip(data);
    expect(strip).toEqual([
      { label: "QB", have: 1, need: 1 }, { label: "RB", have: 2, need: 2 },
      { label: "WR", have: 1, need: 2 }, { label: "TE", have: 0, need: 1 },
      { label: "FLEX", have: 1, need: 1 }, { label: "K", have: 1, need: 1 },
      { label: "DST", have: 0, need: 1 }, { label: "BN", have: 0, need: 5 },
    ]);
  });

  it("returns [] with no active profile or board", () => {
    expect(buildRosterStrip({ activeProfile: null, draftBoard: null } as any)).toEqual([]);
  });
});

describe("findCloseCall", () => {
  it("flags the top two candidates when their Pick Score is within the threshold", () => {
    const rows = [_candidate({ playerId: "a", playerName: "A", pickScore: 90 }), _candidate({ playerId: "b", playerName: "B", pickScore: 88 })] as any;
    const result = findCloseCall(rows, 3);
    expect(result).not.toBeNull();
    expect([result!.a.playerId, result!.b.playerId]).toEqual(["a", "b"]);
  });

  it("does not flag a clear leader", () => {
    const rows = [_candidate({ playerId: "a", pickScore: 95 }), _candidate({ playerId: "b", pickScore: 60 })] as any;
    expect(findCloseCall(rows, 3)).toBeNull();
  });

  it("never alters pickScore -- purely a read", () => {
    const rows = [_candidate({ playerId: "a", pickScore: 90 }), _candidate({ playerId: "b", pickScore: 89 })] as any;
    findCloseCall(rows, 3);
    expect(rows[0].pickScore).toBe(90);
    expect(rows[1].pickScore).toBe(89);
  });
});
