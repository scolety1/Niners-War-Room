import { describe, expect, it } from "vitest";

import {
  actionToBadgeTone,
  resolveDisplayAction,
  assignRosterSlots,
  buildCompareRows,
  buildCurrentRosterScores,
  buildMyTeamSummary,
  buildPositionDemand,
  buildRosterStrip,
  buildRosterStripFromRoster,
  buildSuggestionsRows,
  buildUdkBadges,
  buildUdkEntryById,
  buildScarcityCounterfactual,
  findCloseCall,
  findPickNow,
  formatAdpRoundPick,
  formatMakeItBack,
  formatPickScore,
  formatRoundPick,
  generateCompareSummary,
  severityToBadgeTone,
  shouldFocusSearchShortcut,
  splitActionValue,
  tabLabel,
  toggleCompareSelection,
} from "./draft-room-v2";

describe("formatRoundPick", () => {
  // Owner-test follow-up, section 12 -- the owner's own worked examples.
  it("matches the owner's exact worked examples", () => {
    expect(formatRoundPick(69, 10)).toBe("7.09");
    expect(formatRoundPick(47, 12)).toBe("4.11");
  });

  it("zero-pads the pick-in-round to two digits", () => {
    expect(formatRoundPick(1, 10)).toBe("1.01");
    expect(formatRoundPick(10, 10)).toBe("1.10");
  });

  it("rolls over correctly at round boundaries", () => {
    expect(formatRoundPick(10, 10)).toBe("1.10");
    expect(formatRoundPick(11, 10)).toBe("2.01");
  });

  // NWR CHEAT SHEET -- COMBINED NWR + MARKET + BALLERS VIEW (2026-09-08,
  // directive section 10): a real, live bug found and fixed while building
  // Cheat Sheets' Combined view -- a fractional overall ADP (real market
  // data is frequently not a whole number, e.g. a consensus/averaged
  // 13.3, or Sleeper's own 168.6) previously leaked raw floating-point
  // error into the displayed round.pick string (e.g. "2.3.3000000000000007"
  // instead of "2.03"). Reproduced exactly the owner's quoted examples
  // before this fix.
  it("never leaks floating-point error for a fractional overall ADP", () => {
    expect(formatRoundPick(13.3, 10)).toBe("2.03");
    expect(formatRoundPick(23.3, 10)).toBe("3.03");
    expect(formatRoundPick(15.6, 10)).toBe("2.06");
    expect(formatRoundPick(22.8, 10)).toBe("3.03");
    for (const [pick, teamCount] of [[13.3, 10], [23.3, 10], [15.6, 10], [22.8, 10], [168.6, 10]] as const) {
      expect(formatRoundPick(pick, teamCount)).not.toMatch(/\.\d+\./);
      expect(formatRoundPick(pick, teamCount)).toMatch(/^\d+\.\d{2}$/);
    }
  });
});

describe("formatMakeItBack", () => {
  it("labels a literal 100% as a modeled estimate over the real trial count, not a guarantee", () => {
    const result = formatMakeItBack(1.0, 10);
    expect(result.text).toBe("100%*");
    expect(result.title).toContain("10 simulated continuations");
    expect(result.title).toContain("not a guarantee");
  });

  it("never fabricates a value when the probability is null", () => {
    expect(formatMakeItBack(null, null).text).toBe("UNKNOWN");
  });

  it("renders a normal percentage without the asterisk when not a literal 100%", () => {
    expect(formatMakeItBack(0.4, 10).text).toBe("40%");
  });
});

describe("formatPickScore", () => {
  // Owner feedback closure (result-status taxonomy): a bare 50.0 must
  // never look identical to an unevaluated/placeholder cell when it is
  // actually a real, computed tie.
  it("marks a genuine tied-no-spread result distinctly, without changing the number", () => {
    const result = formatPickScore(50.0, true);
    expect(result.text).toBe("50.0 (tied)");
    expect(result.title).toContain("cannot distinguish");
  });

  it("renders a normal score plainly when there is real spread", () => {
    const result = formatPickScore(72.3, false);
    expect(result.text).toBe("72.3");
    expect(result.title).not.toContain("cannot distinguish");
  });

  it("never fabricates a value for a genuinely unevaluated candidate", () => {
    const result = formatPickScore(null, false);
    expect(result.text).toBe("—");
    expect(result.title).toContain("Not evaluated");
  });
});

describe("splitActionValue", () => {
  // Owner-test section 7: split "what to do" from "how the market sees
  // this player right now" -- both reuse existing evidence (the real
  // action string, real NWR rank, real market ADP/expected pick) rather
  // than a second scoring system.
  it("maps every existing action string to a distinct owner-facing verb", () => {
    expect(splitActionValue("TAKE_NOW", 5, 5, 69, 10).action).toBe("Pick now");
    expect(splitActionValue("GOOD_VALUE", 5, 5, 69, 10).action).toBe("Consider now");
    expect(splitActionValue("DEEP_TARGET", 5, 5, 69, 10).action).toBe("Queue for later");
    expect(splitActionValue("WAIT", 5, 5, 69, 10).action).toBe("Wait until next turn");
    expect(splitActionValue("WAIVER_WATCH", 5, 5, 69, 10).action).toBe("Review data");
    expect(splitActionValue("UNSCORED", 5, 5, 69, 10).action).toBe("Review data");
  });

  it("never produces a confident market label when ADP/current pick evidence is missing", () => {
    expect(splitActionValue("TAKE_NOW", 5, null, 69, 10)).toEqual({ action: "Pick now", value: "Unknown", gapPicks: null });
    expect(splitActionValue("TAKE_NOW", 5, 60, null, 10).value).toBe("Unknown");
    expect(splitActionValue("TAKE_NOW", 5, 60, 69, null).value).toBe("Unknown");
    expect(splitActionValue("TAKE_NOW", 5, 60, 69, 0).value).toBe("Unknown");
  });

  it("labels a player who has actually gone later than their own cited ADP as Falling", () => {
    // Expected pick 50, we're on the clock at 70 (a full team-count of
    // picks past their own ADP) and they are STILL on the board.
    const result = splitActionValue("WAIT", 20, 50, 70, 10);
    expect(result.value).toBe("Falling");
    expect(result.gapPicks).toBe(-20);
  });

  it("labels a player being drafted well ahead of their own cited ADP as a Reach", () => {
    const result = splitActionValue("TAKE_NOW", 20, 90, 70, 10);
    expect(result.value).toBe("Reach");
    expect(result.gapPicks).toBe(20);
  });

  it("labels a real NWR-vs-market discount as Value, distinct from real-time Falling/Reach behavior", () => {
    // NWR has them ranked #10 while the market doesn't expect them until
    // pick 25 -- a real >=10-spot discount -- but the current pick (24) is
    // still inside one team-count of their own ADP, so it is not "Falling".
    const result = splitActionValue("GOOD_VALUE", 10, 25, 24, 10);
    expect(result.value).toBe("Value");
  });

  it("labels an ordinary in-range player as Fair rather than manufacturing separation", () => {
    const result = splitActionValue("GOOD_VALUE", 22, 25, 24, 10);
    expect(result.value).toBe("Fair");
  });
});

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
    makeItBackProbability: 0.12, makeItBackTrials: 10, rawDecisionUtility: 10.9,
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

  it("maps DecisionBundle candidates without discarding backend order", () => {
    const bundle = _availableBundle([
      _candidate({ playerId: "p2", playerName: "Deep Sleeper", position: "WR", pickScore: 40, makeItBackProbability: null }),
      _candidate({ playerId: "p1", pickScore: 94 }),
    ]);
    const rows = buildSuggestionsRows(bundle, rankings, new Map());
    expect(rows).toHaveLength(2);
    expect(rows[0]!.playerId).toBe("p2");
    expect(rows[0]!.pickScore).toBe(40);
    expect(rows[1]!.playerId).toBe("p1");
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

describe("shared Ballers lookup", () => {
  it("indexes the current imported UDK snapshot by matched player id", () => {
    const current = {
      playerId: "player:puka-nacua",
      playerName: "Puka Nacua",
      team: "LAR",
      position: "WR",
      byeWeek: "8",
      rank: 7,
      points: 301.2,
      risk: 2,
      upside: 9,
      adpRaw: "1.08",
      tier: 1,
      outlook: "Current import",
      dynastyLocked: false,
      matchStatus: "MATCHED" as const,
    };
    const byId = buildUdkEntryById({
      positions: [{ position: "WR", entries: [current], provider: "Ballers", importedAtUtc: "2026-09-09T00:00:00Z", sourceSha256: "current", sourceRows: 1 }],
    });
    expect(byId.get("player:puka-nacua")).toBe(current);
  });
});

describe("slash search shortcut", () => {
  const event = (target: { tagName?: string; isContentEditable?: boolean } | null, overrides: Record<string, unknown> = {}) => ({
    key: "/",
    altKey: false,
    ctrlKey: false,
    metaKey: false,
    shiftKey: false,
    defaultPrevented: false,
    target,
    ...overrides,
  } as unknown as KeyboardEvent);

  it("focuses search for an unmodified slash outside text entry", () => {
    expect(shouldFocusSearchShortcut(event({ tagName: "DIV" }))).toBe(true);
  });

  it("does not hijack typing in inputs, textareas, or editable content", () => {
    expect(shouldFocusSearchShortcut(event({ tagName: "INPUT" }))).toBe(false);
    expect(shouldFocusSearchShortcut(event({ tagName: "TEXTAREA" }))).toBe(false);
    expect(shouldFocusSearchShortcut(event({ tagName: "DIV", isContentEditable: true }))).toBe(false);
  });

  it("ignores modified, handled, and non-slash key presses", () => {
    expect(shouldFocusSearchShortcut(event({ tagName: "DIV" }, { ctrlKey: true }))).toBe(false);
    expect(shouldFocusSearchShortcut(event({ tagName: "DIV" }, { defaultPrevented: true }))).toBe(false);
    expect(shouldFocusSearchShortcut(event({ tagName: "DIV" }, { key: "?" }))).toBe(false);
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
      { playerId: "a", playerName: "Player A", position: "QB", nwrRank: 20, overallAdp: 25, tier: null, status: "", playerScore: null, teamScoreDelta: null, equityGain: null, costOfWaiting: null, makeItBackProbability: null, makeItBackTrials: null, pickScore: null, pickScoreTiedNoSpread: false, action: null, warnings: [], evaluated: false, metricStatus: {} },
      { playerId: "b", playerName: "Player B", position: "RB", nwrRank: 5, overallAdp: 40, tier: null, status: "", playerScore: null, teamScoreDelta: null, equityGain: null, costOfWaiting: null, makeItBackProbability: null, makeItBackTrials: null, pickScore: null, pickScoreTiedNoSpread: false, action: null, warnings: [], evaluated: false, metricStatus: {} },
    ];
    const summary = generateCompareSummary(rows, { QB: 10, RB: 30 });
    expect(summary).toContain("Player B has the best NWR rank (#5)");
    expect(summary).toContain("Player B offers the largest market discount");
    expect(summary).toContain("RB is the deepest position");
  });

  it("never fabricates a claim when the underlying structured field is missing", () => {
    const rows = [
      { playerId: "a", playerName: "Player A", position: "QB", nwrRank: null, overallAdp: null, tier: null, status: "", playerScore: null, teamScoreDelta: null, equityGain: null, costOfWaiting: null, makeItBackProbability: null, makeItBackTrials: null, pickScore: null, pickScoreTiedNoSpread: false, action: null, warnings: [], evaluated: false, metricStatus: {} },
      { playerId: "b", playerName: "Player B", position: "QB", nwrRank: null, overallAdp: null, tier: null, status: "", playerScore: null, teamScoreDelta: null, equityGain: null, costOfWaiting: null, makeItBackProbability: null, makeItBackTrials: null, pickScore: null, pickScoreTiedNoSpread: false, action: null, warnings: [], evaluated: false, metricStatus: {} },
    ];
    const summary = generateCompareSummary(rows, {});
    expect(summary).not.toContain("best NWR rank");
    expect(summary).not.toContain("market discount");
  });

  it("cites the highest Pick Score among evaluated candidates when available", () => {
    const rows = [
      { playerId: "a", playerName: "Player A", position: "QB", nwrRank: 20, overallAdp: 25, tier: null, status: "", playerScore: 50, teamScoreDelta: 2, equityGain: 0.01, costOfWaiting: 1, makeItBackProbability: 0.5, makeItBackTrials: 10, pickScore: 40, pickScoreTiedNoSpread: false, action: "WAIT", warnings: [], evaluated: true, metricStatus: {} },
      { playerId: "b", playerName: "Player B", position: "RB", nwrRank: 5, overallAdp: 40, tier: null, status: "", playerScore: 80, teamScoreDelta: 8, equityGain: 0.03, costOfWaiting: 3, makeItBackProbability: 0.2, makeItBackTrials: 10, pickScore: 90, pickScoreTiedNoSpread: false, action: "TAKE NOW", warnings: [], evaluated: true, metricStatus: {} },
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

describe("buildRosterStripFromRoster", () => {
  it("includes a Superflex row only when the league actually configures one", () => {
    const single = buildRosterStripFromRoster([], { qb: 1, rb: 2, wr: 2, te: 1, flex: 1, superflex: 0, k: 1, dst: 1, benchSize: 5 });
    expect(single.some((slot) => slot.label === "SFLX")).toBe(false);
    const superflexLeague = buildRosterStripFromRoster(
      [_rosterPlayer("QB", 1), _rosterPlayer("QB", 2)],
      { qb: 1, rb: 2, wr: 2, te: 1, flex: 1, superflex: 1, k: 1, dst: 1, benchSize: 5 },
    );
    const sflx = superflexLeague.find((slot) => slot.label === "SFLX");
    expect(sflx).toEqual({ label: "SFLX", have: 1, need: 1 });
  });
});

describe("assignRosterSlots", () => {
  const req = { qb: 1, rb: 2, wr: 2, te: 1, flex: 1, superflex: 0, k: 1, dst: 1, benchSize: 6 };

  it("fills required positions first, then FLEX from the real remaining FLEX-eligible players, in draft order", () => {
    const roster = [
      _rosterPlayer("QB", 1), _rosterPlayer("RB", 2), _rosterPlayer("RB", 3), _rosterPlayer("WR", 4),
      _rosterPlayer("WR", 5), _rosterPlayer("TE", 6), _rosterPlayer("RB", 7), _rosterPlayer("K", 8), _rosterPlayer("DST", 9),
    ];
    const { starters, bench } = assignRosterSlots(roster, req);
    expect(starters.map((slot) => slot.label)).toEqual(["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "K", "DST"]);
    expect(starters.find((slot) => slot.label === "FLEX")?.player?.playerId).toBe("RB-7");
    expect(bench).toEqual([]);
  });

  it("never assigns the same player into two slots (FLEX does not duplicate a starter)", () => {
    // req.rb=2, req.flex=1: two RB starters, and the FLEX slot consumes a
    // real, DIFFERENT extra RB rather than reusing RB-1 or RB-2 -- the
    // player pool that would demonstrate double-assignment if it existed.
    const roster = [_rosterPlayer("RB", 1), _rosterPlayer("RB", 2), _rosterPlayer("RB", 3), _rosterPlayer("RB", 4)];
    const { starters, bench } = assignRosterSlots(roster, req);
    const assignedIds = starters.filter((slot) => slot.player).map((slot) => slot.player!.playerId);
    expect(assignedIds).toEqual(["RB-1", "RB-2", "RB-3"]);
    expect(new Set(assignedIds).size).toBe(assignedIds.length);
    expect(bench.map((player) => player.playerId)).toEqual(["RB-4"]);
  });

  it("leaves a slot null (Empty) rather than fabricating a player when the roster is short", () => {
    const { starters } = assignRosterSlots([_rosterPlayer("QB", 1)], req);
    expect(starters[0]).toEqual({ label: "QB", player: expect.objectContaining({ playerId: "QB-1" }) });
    expect(starters[1]).toEqual({ label: "RB", player: null });
  });

  it("Superflex draws from any Superflex-eligible position (QB/RB/WR/TE), not just leftover FLEX players", () => {
    const sflxReq = { ...req, superflex: 1 };
    const roster = [_rosterPlayer("QB", 1), _rosterPlayer("QB", 2), _rosterPlayer("RB", 3), _rosterPlayer("WR", 4), _rosterPlayer("TE", 5)];
    const { starters } = assignRosterSlots(roster, sflxReq);
    expect(starters.find((slot) => slot.label === "SFLX")?.player?.playerId).toBe("QB-2");
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

describe("findPickNow", () => {
  it("labels a clear leader NWR PICK NOW", () => {
    const rows = [
      _candidate({ playerId: "a", playerName: "A", pickScore: 95, pickScoreTiedNoSpread: false }),
      _candidate({ playerId: "b", playerName: "B", pickScore: 60, pickScoreTiedNoSpread: false }),
    ] as any;
    const result = findPickNow(rows, 3);
    expect(result?.label).toBe("NWR PICK NOW");
    expect(result?.row.playerId).toBe("a");
    expect(result?.runnerUp).toBeNull();
  });

  it("labels a genuine near-tie CLOSE CALL and surfaces the runner-up", () => {
    const rows = [
      _candidate({ playerId: "a", playerName: "A", pickScore: 90, pickScoreTiedNoSpread: false }),
      _candidate({ playerId: "b", playerName: "B", pickScore: 88, pickScoreTiedNoSpread: false }),
    ] as any;
    const result = findPickNow(rows, 3);
    expect(result?.label).toBe("BEST CURRENT PICK — CLOSE CALL");
    expect(result?.row.playerId).toBe("a");
    expect(result?.runnerUp?.playerId).toBe("b");
  });

  it("labels a genuine tied/no-spread Pick Score NO SMASH VALUE rather than fabricating separation", () => {
    const rows = [
      _candidate({ playerId: "a", playerName: "A", pickScore: 50, pickScoreTiedNoSpread: true }),
      _candidate({ playerId: "b", playerName: "B", pickScore: 50, pickScoreTiedNoSpread: true }),
    ] as any;
    const result = findPickNow(rows, 3);
    expect(result?.label).toBe("BEST CURRENT PICK — NO SMASH VALUE");
  });

  it("returns null with no candidates -- never fabricates a pick", () => {
    expect(findPickNow([])).toBeNull();
  });

  it("uses the backend-promoted row even when another row has a higher Pick Score", () => {
    const rows = [
      _candidate({ playerId: "a", pickScore: 40 }),
      _candidate({ playerId: "b", pickScore: 99 }),
      _candidate({ playerId: "c", pickScore: 70 }),
    ] as any;
    expect(findPickNow(rows, 3)?.row.playerId).toBe("a");
  });
});

describe("buildScarcityCounterfactual", () => {
  it("picks the position with the lowest real Make-It-Back probability as the scarce path, compared against the actual #1 recommendation", () => {
    const rows = [
      _candidate({ playerId: "rb1", playerName: "RB One", position: "RB", pickScore: 90, teamScoreAfter: 70, costOfWaiting: 2.0, makeItBackProbability: 0.7, makeItBackTrials: 200 }),
      _candidate({ playerId: "qb1", playerName: "QB One", position: "QB", pickScore: 88, teamScoreAfter: 68, costOfWaiting: 6.5, makeItBackProbability: 0.15, makeItBackTrials: 200 }),
    ] as any;
    const result = buildScarcityCounterfactual(rows);
    expect(result).not.toBeNull();
    expect(result!.scarce.playerId).toBe("qb1");
    expect(result!.alternative.playerId).toBe("rb1");
    expect(result!.survivalProbabilityIfWait).toBe(0.15);
    expect(result!.expectedCostIfWait).toBe(6.5);
  });

  it("compares against the next-best position when the scarce candidate is itself the #1 recommendation", () => {
    const rows = [
      _candidate({ playerId: "qb1", playerName: "QB One", position: "QB", pickScore: 95, makeItBackProbability: 0.1, makeItBackTrials: 200 }),
      _candidate({ playerId: "rb1", playerName: "RB One", position: "RB", pickScore: 80, makeItBackProbability: 0.8, makeItBackTrials: 200 }),
    ] as any;
    const result = buildScarcityCounterfactual(rows);
    expect(result?.scarce.playerId).toBe("qb1");
    expect(result?.alternative.playerId).toBe("rb1");
  });

  it("returns null rather than fabricating a comparison when only one position is on the board", () => {
    const rows = [
      _candidate({ playerId: "rb1", position: "RB" }),
      _candidate({ playerId: "rb2", position: "RB" }),
    ] as any;
    expect(buildScarcityCounterfactual(rows)).toBeNull();
  });

  it("returns null when no candidate has a real Make-It-Back evaluation", () => {
    const rows = [
      _candidate({ playerId: "qb1", position: "QB", makeItBackProbability: null }),
      _candidate({ playerId: "rb1", position: "RB", makeItBackProbability: null }),
    ] as any;
    expect(buildScarcityCounterfactual(rows)).toBeNull();
  });

  it("returns null with fewer than two rows", () => {
    expect(buildScarcityCounterfactual([])).toBeNull();
    expect(buildScarcityCounterfactual([_candidate()] as any)).toBeNull();
  });
});

// NWR DRAFT-DAY: ADP round.pick display (owner-requested "4.12"/"7.03"
// format) must never silently reinterpret a different-sized league's ADP
// as this room's own rounds -- the raw decimal is preserved whenever the
// source team count is unknown or doesn't match.
describe("formatAdpRoundPick", () => {
  it("converts to round.pick when the source team count matches the room", () => {
    const result = formatAdpRoundPick(69, 10, 10);
    expect(result.text).toBe("7.09");
    expect(result.title).toContain("69");
  });

  it("shows the raw decimal, not a guessed conversion, when the source team count is unknown", () => {
    const result = formatAdpRoundPick(194.4, null, 10);
    expect(result.text).toBe("194.4");
    expect(result.title.toLowerCase()).toContain("isn't known");
  });

  it("shows the raw decimal, not a silently-reinterpreted conversion, when the source team count differs from the room", () => {
    const result = formatAdpRoundPick(69, 12, 10);
    expect(result.text).toBe("69.0");
    expect(result.title).toContain("12-team");
    expect(result.title).toContain("10-team");
  });

  it("handles a missing ADP value honestly", () => {
    expect(formatAdpRoundPick(null, 10, 10).text).toBe("—");
  });
});

// NWR DRAFT-DAY: the owner's explicit 3-tier action-color mapping (Pick
// Now/Take Now = GREEN; Consider = AMBER; Wait/Queue Later = MUTED RED).
// "ready"/"review"/"deprioritized" are the tone names that resolve to
// those three colors -- see redraft.css and packages/ui/src/styles.css.
describe("actionToBadgeTone", () => {
  it("maps Take Now to the GREEN tone, not the RED 'blocked' tone", () => {
    expect(actionToBadgeTone("TAKE NOW")).toBe("ready");
    expect(actionToBadgeTone("TAKE_NOW")).toBe("ready");
  });

  it("maps Good Value to the AMBER 'review' tone", () => {
    expect(actionToBadgeTone("GOOD VALUE")).toBe("review");
  });

  it("maps Wait/Deep Target/Waiver Watch to the muted-red 'deprioritized' tone", () => {
    expect(actionToBadgeTone("WAIT")).toBe("deprioritized");
    expect(actionToBadgeTone("DEEP TARGET")).toBe("deprioritized");
    expect(actionToBadgeTone("WAIVER WATCH")).toBe("deprioritized");
    expect(actionToBadgeTone("WAIVER_WATCH")).toBe("deprioritized");
  });

  it("never silently reuses another action's tone for an unrecognized label", () => {
    expect(actionToBadgeTone("UNSCORED")).toBe("review");
  });
});

describe("resolveDisplayAction", () => {
  it("overrides a WAIT-family action to TAKE_NOW for the pick-now row on a back-to-back turn", () => {
    expect(resolveDisplayAction("WAIT", true, true)).toBe("TAKE_NOW");
    expect(resolveDisplayAction("DEEP_TARGET", true, true)).toBe("TAKE_NOW");
  });

  it("leaves TAKE_NOW itself unchanged (no-op, already consistent)", () => {
    expect(resolveDisplayAction("TAKE_NOW", true, true)).toBe("TAKE_NOW");
  });

  it("never overrides a row that is not the chosen pick-now candidate", () => {
    expect(resolveDisplayAction("WAIT", false, true)).toBe("WAIT");
  });

  // NWR OVERNIGHT V3 strategic closure: the real, reproduced banner/badge
  // mismatch. The pick-now row must ALWAYS read TAKE_NOW -- not only on a
  // back-to-back turn -- so the row directly under a green "NWR PICK NOW"
  // banner can never itself show a muted-red WAIT/DEEP_TARGET action.
  it("overrides the pick-now row to TAKE_NOW even off a back-to-back turn -- the real banner/badge mismatch", () => {
    expect(resolveDisplayAction("WAIT", true, false)).toBe("TAKE_NOW");
    expect(resolveDisplayAction("DEEP_TARGET", true, false)).toBe("TAKE_NOW");
  });

  // The other real half of the mismatch: a DIFFERENT candidate's own
  // independent cost-of-waiting label can also compute TAKE_NOW. That must
  // never render as a second, competing green "PICK NOW" badge -- there is
  // exactly one canonical current-pick authority (the banner/row-1
  // candidate). Downgraded to the existing, real GOOD_VALUE label, not a
  // new invented one; the real urgency signal is still surfaced separately
  // via the SCARCITY chip.
  it("downgrades a non-pick-now row's own TAKE_NOW label to GOOD_VALUE -- never a second green PICK NOW badge", () => {
    expect(resolveDisplayAction("TAKE_NOW", false, true)).toBe("GOOD_VALUE");
    expect(resolveDisplayAction("TAKE_NOW", false, false)).toBe("GOOD_VALUE");
  });

  it("leaves a non-pick-now row's WAIT/GOOD_VALUE/DEEP_TARGET/WAIVER_WATCH labels untouched -- only TAKE_NOW is ever downgraded", () => {
    expect(resolveDisplayAction("WAIT", false, false)).toBe("WAIT");
    expect(resolveDisplayAction("GOOD_VALUE", false, true)).toBe("GOOD_VALUE");
    expect(resolveDisplayAction("DEEP_TARGET", false, true)).toBe("DEEP_TARGET");
    expect(resolveDisplayAction("WAIVER_WATCH", false, true)).toBe("WAIVER_WATCH");
  });
});
