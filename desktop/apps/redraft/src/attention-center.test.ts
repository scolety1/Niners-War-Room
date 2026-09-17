import type {
  DataHealthReport,
  DraftBoard,
  LeagueProfile,
  LeagueWorkspaceContext,
  RedraftBootstrap,
  RedraftFreeAgentsResult,
  RedraftMyRosterResult,
  RedraftOpponentRostersResult,
} from "@nwr/contracts";
import { describe, expect, it } from "vitest";

import {
  buildLeagueOwnershipEntries,
  dataHealthFlags,
  deadlineFlags,
  rosterIdentityFlags,
  runAttentionCenterAggregation,
  searchPlayerAcrossLeagues,
  serializeActiveProfileCall,
  summarizeLeagueAttention,
  waiverOpportunityFlags,
  workspaceFlags,
  type AttentionCenterClient,
  type LeagueOwnershipEntry,
} from "./attention-center";

function profile(overrides: Partial<LeagueProfile> = {}): LeagueProfile {
  return {
    profileId: "p1",
    leagueName: "Test League",
    season: 2026,
    teamCount: 10,
    roster: { qb: 1, rb: 2, wr: 2, te: 1, flex: 1, superflex: 0, k: 1, dst: 1, benchSize: 6 },
    scoring: {
      passingYards: 0.04, passingTd: 4, interception: -2, rushingYards: 0.1, rushingTd: 6,
      receivingYards: 0.1, reception: 1, receivingTd: 6, passingFirstDown: 0, rushingFirstDown: 0,
      receivingFirstDown: 0, returnYards: 0, returnTd: 6, fumbleLost: -2, tePremium: 0, bonuses: {},
    },
    draft: {
      draftType: "snake", draftSlot: null, rounds: 15, keeperCount: 0, auctionBudget: null,
      rosterLimits: [], adpContextEnabled: true, replacementMethod: "expected_available",
    },
    presetKey: null,
    archived: false,
    createdAtUtc: "2026-01-01T00:00:00Z",
    updatedAtUtc: "2026-01-01T00:00:00Z",
    practicalMode: false,
    nwrPureExperimental: false,
    provider: "local",
    providerLeagueId: null,
    ...overrides,
  };
}

function dataHealth(overrides: Partial<DataHealthReport> = {}): DataHealthReport {
  return { categories: [], generatedAtUtc: "2026-09-12T00:00:00Z", ...overrides };
}

function workspaceContext(overrides: Partial<LeagueWorkspaceContext> = {}): LeagueWorkspaceContext {
  return {
    profileId: "p1", provider: "sleeper", providerLeagueId: "L1", season: 2026,
    lifecycle: "IN_SEASON", lifecycleBasis: "test", currentWeek: 3,
    scoringProfileHash: "h", rosterStateHash: "r", leagueSnapshotId: "s",
    syncStatus: "LIVE", syncAsOf: "2026-09-12T00:00:00Z", issues: [],
    matchup: null, standings: null, playoff: null,
    ...overrides,
  };
}

function bootstrap(overrides: Partial<RedraftBootstrap> = {}, activeProfile: LeagueProfile = profile()): RedraftBootstrap {
  return {
    product: { title: "t", contextLabel: "c", authority: "a" },
    status: { ready: true, tone: "ready", authority: "NWR", sourceAsOf: "2026-09-12", freshness: "CURRENT", summary: "", scheduledRefresh: "", errors: [], warnings: [] },
    profiles: [activeProfile],
    presets: [],
    activeProfileId: activeProfile.profileId,
    activeProfile,
    rankings: [],
    replacementLevels: [],
    draftBoard: null,
    health: {
      status: "OK", playerUniverseAvailable: true, currentSeasonForecastAvailable: true,
      scoringProfileValid: true, replacementCalculationValid: true, rankedPlayers: 0,
      blockedPlayers: 0, lastGeneratedTimestamp: "2026-09-12T00:00:00Z", messages: [],
    },
    notices: [],
    ...overrides,
  };
}

describe("dataHealthFlags", () => {
  it("ignores OK/NOT_APPLICABLE/NO_ACTIVITY categories", () => {
    const report = dataHealth({
      categories: [
        { category: "LEAGUE_SYNC", status: "OK", source: "sleeper", lastUpdate: null, freshness: "CURRENT", degradationReason: null, impactOnRecommendations: "None." },
        { category: "MARKET_ADP", status: "NOT_APPLICABLE", source: null, lastUpdate: null, freshness: "UNKNOWN", degradationReason: null, impactOnRecommendations: "None." },
      ],
    });
    expect(dataHealthFlags(report)).toEqual([]);
  });

  it("flags LEAGUE_SYNC going UNAVAILABLE as URGENT -- the one data-health fact that means the league connection itself is broken", () => {
    const report = dataHealth({
      categories: [
        { category: "LEAGUE_SYNC", status: "UNAVAILABLE", source: null, lastUpdate: null, freshness: "UNKNOWN", degradationReason: "No active league profile.", impactOnRecommendations: "x" },
      ],
    });
    const flags = dataHealthFlags(report);
    expect(flags).toEqual([{ kind: "SYNC_DEGRADED", severity: "URGENT", summary: "LEAGUE SYNC: UNAVAILABLE", detail: "No active league profile." }]);
  });

  it("treats every other category (even UNAVAILABLE) as WATCH, not URGENT -- a missing ADP import or a stale-but-present snapshot is routine, not a fire", () => {
    const report = dataHealth({
      categories: [
        { category: "MARKET_ADP", status: "UNAVAILABLE", source: null, lastUpdate: null, freshness: "UNKNOWN", degradationReason: "No ADP snapshot is imported for this profile.", impactOnRecommendations: "x" },
        { category: "ROS_PROJECTIONS", status: "DEGRADED", source: "s", lastUpdate: null, freshness: "STALE", degradationReason: "Rankings are not ready.", impactOnRecommendations: "x" },
      ],
    });
    const flags = dataHealthFlags(report);
    expect(flags).toHaveLength(2);
    expect(flags[0]).toMatchObject({ kind: "DATA_DEGRADED", severity: "WATCH" });
    expect(flags[1]).toMatchObject({ kind: "DATA_DEGRADED", severity: "WATCH" });
  });

  it("returns no flags for a null report rather than throwing", () => {
    expect(dataHealthFlags(null)).toEqual([]);
    expect(dataHealthFlags(undefined)).toEqual([]);
  });
});

describe("workspaceFlags", () => {
  it("flags a live draft as URGENT", () => {
    const flags = workspaceFlags(workspaceContext({ lifecycle: "LIVE_DRAFT" }));
    expect(flags.some((flag) => flag.kind === "LIVE_DRAFT_IN_PROGRESS" && flag.severity === "URGENT")).toBe(true);
  });

  it("flags real reported issues as WATCH", () => {
    const flags = workspaceFlags(workspaceContext({ issues: ["Roster sync stale."] }));
    expect(flags).toEqual([{ kind: "WORKSPACE_ISSUE", severity: "WATCH", summary: "1 workspace issue reported.", detail: "Roster sync stale." }]);
  });

  it("produces no flags for a clean IN_SEASON context", () => {
    expect(workspaceFlags(workspaceContext())).toEqual([]);
  });
});

describe("rosterIdentityFlags", () => {
  function roster(overrides: Partial<RedraftMyRosterResult> = {}): RedraftMyRosterResult {
    return { leagueId: "L1", roster: [], rankingWarning: "", writeBehavior: "NO_SLEEPER_WRITES", ...overrides };
  }
  it("flags unmatched identities", () => {
    const flags = rosterIdentityFlags(roster({
      roster: [
        { sleeperPlayerId: "1", canonicalPlayerId: "c1", playerName: "Known Player", position: "WR", team: "SF", starter: true, identityStatus: "MATCHED" },
        { sleeperPlayerId: "2", canonicalPlayerId: null, playerName: "Mystery Player", position: "RB", team: "SF", starter: false, identityStatus: "UNMATCHED_IDENTITY" },
      ],
    }));
    expect(flags).toHaveLength(1);
    expect(flags[0]!.kind).toBe("ROSTER_IDENTITY_UNRESOLVED");
    expect(flags[0]!.detail).toContain("Mystery Player");
  });
  it("produces no flags when every identity matched, or roster is null", () => {
    expect(rosterIdentityFlags(null)).toEqual([]);
    expect(rosterIdentityFlags(roster({
      roster: [{ sleeperPlayerId: "1", canonicalPlayerId: "c1", playerName: "P", position: "WR", team: "SF", starter: true, identityStatus: "MATCHED" }],
    }))).toEqual([]);
  });
});

describe("waiverOpportunityFlags", () => {
  function freeAgents(overrides: Partial<RedraftFreeAgentsResult> = {}): RedraftFreeAgentsResult {
    return { leagueId: "L1", freeAgents: [], rankingWarning: "", writeBehavior: "NO_SLEEPER_WRITES", ...overrides };
  }
  it("flags a highly ranked free agent", () => {
    const flags = waiverOpportunityFlags(freeAgents({
      freeAgents: [{ sleeperPlayerId: "9", playerId: "9", playerName: "Waiver Gem", position: "WR", team: "SF", overallRank: 40, positionRank: 10, projectedPoints: 8, replacementAdjustedValue: 3, valueLabel: "value", rankingAuthority: "NWR REDRAFT RANKING", rosterStatus: "AVAILABLE" }],
    }));
    expect(flags).toHaveLength(1);
    expect(flags[0]!.summary).toContain("Waiver Gem");
  });
  it("does not flag when the best free agent is a deep bench/unranked player", () => {
    const flags = waiverOpportunityFlags(freeAgents({
      freeAgents: [{ sleeperPlayerId: "9", playerId: "9", playerName: "Deep Bench", position: "WR", team: "SF", overallRank: 250, positionRank: 80, projectedPoints: 1, replacementAdjustedValue: 0, valueLabel: "v", rankingAuthority: "NWR REDRAFT RANKING", rosterStatus: "AVAILABLE" }],
    }));
    expect(flags).toEqual([]);
  });
});

describe("deadlineFlags", () => {
  it("flags an imminent (this-week/next-week) playoff start", () => {
    const context = workspaceContext({ currentWeek: 14, playoff: { leagueStatus: "in_season", playoffWeekStart: 15, inPlayoffs: false, bracketAvailable: false, bracket: [] } });
    expect(deadlineFlags(context)[0]?.summary).toBe("Playoffs start next week.");
  });
  it("does not flag a distant playoff start, or a league already in the playoffs", () => {
    expect(deadlineFlags(workspaceContext({ currentWeek: 3, playoff: { leagueStatus: "in_season", playoffWeekStart: 15, inPlayoffs: false, bracketAvailable: false, bracket: [] } }))).toEqual([]);
    expect(deadlineFlags(workspaceContext({ currentWeek: 15, playoff: { leagueStatus: "in_season", playoffWeekStart: 15, inPlayoffs: true, bracketAvailable: true, bracket: [] } }))).toEqual([]);
  });
});

describe("summarizeLeagueAttention", () => {
  it("marks a league whose read failed as URGENT/LEAGUE_UNREACHABLE and blanks out its derived text fields", () => {
    const summary = summarizeLeagueAttention({
      profile: profile(), dataHealth: null, workspaceContext: null, myRoster: null, freeAgents: null,
      fetchError: "Sleeper roster data unavailable.",
    });
    expect(summary.severity).toBe("URGENT");
    expect(summary.flags).toHaveLength(1);
    expect(summary.flags[0]!.kind).toBe("LEAGUE_UNREACHABLE");
    expect(summary.record).toBeNull();
    expect(summary.standingsRank).toBeNull();
    expect(summary.deadlineText).toBeNull();
  });

  it("is OK severity for a clean league with no flags", () => {
    const summary = summarizeLeagueAttention({
      profile: profile(), dataHealth: dataHealth(), workspaceContext: workspaceContext(), myRoster: null, freeAgents: null,
      fetchError: null,
    });
    expect(summary.severity).toBe("OK");
    expect(summary.flags).toEqual([]);
  });

  it("takes the worst severity across multiple real flags", () => {
    const summary = summarizeLeagueAttention({
      profile: profile(),
      dataHealth: dataHealth({ categories: [{ category: "MARKET_ADP", status: "DEGRADED", source: null, lastUpdate: null, freshness: "STALE", degradationReason: "x", impactOnRecommendations: "x" }] }),
      workspaceContext: workspaceContext({ lifecycle: "LIVE_DRAFT" }),
      myRoster: null, freeAgents: null, fetchError: null,
    });
    expect(summary.severity).toBe("URGENT"); // LIVE_DRAFT_IN_PROGRESS beats the WATCH-level data flag
  });
});

describe("buildLeagueOwnershipEntries", () => {
  it("builds a Sleeper league's ownership from my-roster/opponent-rosters/free-agents", () => {
    const sleeperProfile = profile({ provider: "sleeper", providerLeagueId: "L1" });
    const myRoster: RedraftMyRosterResult = {
      leagueId: "L1", rankingWarning: "", writeBehavior: "NO_SLEEPER_WRITES",
      roster: [{ sleeperPlayerId: "1", canonicalPlayerId: "c1", playerName: "Owner Player", position: "WR", team: "SF", starter: true, identityStatus: "MATCHED" }],
    };
    const opponents: RedraftOpponentRostersResult = {
      leagueId: "L1", writeBehavior: "NO_SLEEPER_WRITES", rankingWarning: "",
      opponents: [{ rosterId: "2", ownerUserId: "u2", teamName: "Rival Team", players: [{ sleeperPlayerId: "5", canonicalPlayerId: "c5", identityStatus: "MATCHED", playerName: "Rival Player", position: "RB", team: "KC", starter: true }], unresolvedSleeperPlayerIds: [] }],
    };
    const freeAgents: RedraftFreeAgentsResult = {
      leagueId: "L1", rankingWarning: "", writeBehavior: "NO_SLEEPER_WRITES",
      freeAgents: [{ sleeperPlayerId: "9", playerId: "9", playerName: "Open Player", position: "TE", team: "DAL", overallRank: 80, positionRank: 12, projectedPoints: 4, replacementAdjustedValue: 1, valueLabel: "v", rankingAuthority: "NWR REDRAFT RANKING", rosterStatus: "AVAILABLE" }],
    };
    const entries = buildLeagueOwnershipEntries(sleeperProfile, bootstrap({}, sleeperProfile), myRoster, freeAgents, opponents);
    expect(entries).toEqual([
      { playerName: "Owner Player", status: "ROSTERED_BY_YOU", teamName: null },
      { playerName: "Rival Player", status: "ROSTERED_BY_OPPONENT", teamName: "Rival Team" },
      { playerName: "Open Player", status: "AVAILABLE", teamName: null },
    ]);
  });

  it("builds a local league's ownership from the bootstrap's own rankings + draft board (no Sleeper reads)", () => {
    const localProfile = profile({ provider: "local" });
    const draftBoard: DraftBoard = {
      schemaVersion: 1, profileId: "p1", drafted: ["a", "b"], configured: true,
      teams: [
        { teamSlot: 1, name: "You", owner: true, roster: [{ playerId: "a", playerName: "My Guy", position: "WR", team: "SF", pickNumber: 1 }], picks: [] },
        { teamSlot: 2, name: "Rival", owner: false, roster: [{ playerId: "b", playerName: "Their Guy", position: "RB", team: "KC", pickNumber: 2 }], picks: [] },
      ],
    };
    const localBootstrap = bootstrap({
      draftBoard,
      rankings: [
        { overallRank: 1, positionRank: 1, playerId: "a", playerName: "My Guy", position: "WR", team: "SF", projectedPoints: 200, replacementPoints: 100, replacementAdjustedValue: 100, starterGap: 0, confidence: "HIGH", tier: 1, positionTier: 1, overallTierLabel: "1", positionTierLabel: "1", sourceAsOf: "x", rookie: false, overallAdp: null, expectedPick: null, adpSource: "none", drafted: true, draftedBy: "You", pickNumber: 1, rosterLegal: true, legalityCode: "OK", legalityReason: "" },
        { overallRank: 2, positionRank: 1, playerId: "b", playerName: "Their Guy", position: "RB", team: "KC", projectedPoints: 190, replacementPoints: 90, replacementAdjustedValue: 90, starterGap: 0, confidence: "HIGH", tier: 1, positionTier: 1, overallTierLabel: "1", positionTierLabel: "1", sourceAsOf: "x", rookie: false, overallAdp: null, expectedPick: null, adpSource: "none", drafted: true, draftedBy: "Rival", pickNumber: 2, rosterLegal: true, legalityCode: "OK", legalityReason: "" },
        { overallRank: 3, positionRank: 2, playerId: "c", playerName: "Undrafted Guy", position: "WR", team: "DAL", projectedPoints: 100, replacementPoints: 50, replacementAdjustedValue: 50, starterGap: 0, confidence: "MED", tier: 2, positionTier: 2, overallTierLabel: "2", positionTierLabel: "2", sourceAsOf: "x", rookie: false, overallAdp: null, expectedPick: null, adpSource: "none", drafted: false, draftedBy: "", pickNumber: null, rosterLegal: true, legalityCode: "OK", legalityReason: "" },
      ],
    }, localProfile);
    const entries = buildLeagueOwnershipEntries(localProfile, localBootstrap, null, null, null);
    expect(entries).toEqual([
      { playerName: "My Guy", status: "ROSTERED_BY_YOU", teamName: null },
      { playerName: "Their Guy", status: "ROSTERED_BY_OPPONENT", teamName: "Rival" },
      { playerName: "Undrafted Guy", status: "AVAILABLE", teamName: null },
    ]);
  });
});

describe("searchPlayerAcrossLeagues", () => {
  const leagues = [
    summarizeLeagueAttention({ profile: profile({ profileId: "a", leagueName: "League A" }), dataHealth: null, workspaceContext: null, myRoster: null, freeAgents: null, fetchError: null }),
    summarizeLeagueAttention({ profile: profile({ profileId: "b", leagueName: "League B" }), dataHealth: null, workspaceContext: null, myRoster: null, freeAgents: null, fetchError: null }),
    summarizeLeagueAttention({ profile: profile({ profileId: "c", leagueName: "League C" }), dataHealth: null, workspaceContext: null, myRoster: null, freeAgents: null, fetchError: null }),
    summarizeLeagueAttention({ profile: profile({ profileId: "d", leagueName: "League D" }), dataHealth: null, workspaceContext: null, myRoster: null, freeAgents: null, fetchError: "unreachable" }),
  ];
  const ownership: Record<string, LeagueOwnershipEntry[]> = {
    a: [{ playerName: "Star Player", status: "ROSTERED_BY_YOU", teamName: null }],
    b: [{ playerName: "Star Player", status: "AVAILABLE", teamName: null }],
    c: [{ playerName: "Star Player", status: "ROSTERED_BY_OPPONENT", teamName: "Rival Squad" }],
    d: [],
  };

  it("answers 'League A: rostered by you / League B: available / League C: rostered by opponent / League D: unknown'", () => {
    const rows = searchPlayerAcrossLeagues(leagues, ownership, "Star Player");
    expect(rows).toEqual([
      { profileId: "a", leagueName: "League A", status: "ROSTERED_BY_YOU", teamName: null, matchedName: "Star Player" },
      { profileId: "b", leagueName: "League B", status: "AVAILABLE", teamName: null, matchedName: "Star Player" },
      { profileId: "c", leagueName: "League C", status: "ROSTERED_BY_OPPONENT", teamName: "Rival Squad", matchedName: "Star Player" },
      { profileId: "d", leagueName: "League D", status: "UNKNOWN", teamName: null, matchedName: null },
    ]);
  });

  it("matches case-insensitively and by substring", () => {
    const rows = searchPlayerAcrossLeagues(leagues, ownership, "star");
    expect(rows.filter((row) => row.status !== "UNKNOWN")).toHaveLength(3);
  });

  it("resolves a query with no match anywhere to UNKNOWN for every league, never a fabricated AVAILABLE", () => {
    const rows = searchPlayerAcrossLeagues(leagues, ownership, "Nobody Real");
    expect(rows.every((row) => row.status === "UNKNOWN")).toBe(true);
  });

  it("returns no rows for an empty query", () => {
    expect(searchPlayerAcrossLeagues(leagues, ownership, "   ")).toEqual([]);
  });
});

// ---------------------------------------------------------------------------
// State-leakage regression coverage -- this directive's own highest-risk
// item. Each test uses a fake client that tracks a single mutable
// "currently active on the backend" variable, exactly mirroring the real
// backend's one-active-profile-pointer architecture, so a bug that let two
// leagues' reads interleave or a bug that failed to restore the original
// league would be caught here without needing a live backend.
// ---------------------------------------------------------------------------

function buildFakeClient(profileIds: string[]) {
  let currentActive: string | null = null;
  const activateCalls: string[] = [];
  const readsSeenDuring: Record<string, string[]> = {};
  const failingProfileIds = new Set<string>();

  function recordRead(kind: string) {
    const key = currentActive ?? "NONE";
    (readsSeenDuring[key] ??= []).push(kind);
  }

  const client: AttentionCenterClient = {
    async activateRedraftProfile(profileId: string): Promise<RedraftBootstrap> {
      if (!profileIds.includes(profileId)) throw new Error(`Unknown profile ${profileId}`);
      currentActive = profileId;
      activateCalls.push(profileId);
      const activeProfile = profile({ profileId, leagueName: `League ${profileId}`, provider: "sleeper", providerLeagueId: profileId });
      return bootstrap({ activeProfileId: profileId, profiles: profileIds.map((id) => profile({ profileId: id })) }, activeProfile);
    },
    async redraftDataHealth(): Promise<DataHealthReport> {
      recordRead("dataHealth");
      if (currentActive && failingProfileIds.has(currentActive)) throw new Error("data health failed");
      return dataHealth({
        categories: [{ category: "LEAGUE_SYNC", status: "OK", source: currentActive, lastUpdate: null, freshness: "CURRENT", degradationReason: null, impactOnRecommendations: "None." }],
      });
    },
    async redraftLeagueWorkspaceContext(): Promise<LeagueWorkspaceContext> {
      recordRead("workspaceContext");
      return workspaceContext({ profileId: currentActive ?? "" });
    },
    async redraftMyRoster(): Promise<RedraftMyRosterResult> {
      recordRead("myRoster");
      return { leagueId: currentActive ?? "", roster: [], rankingWarning: "", writeBehavior: "NO_SLEEPER_WRITES" };
    },
    async redraftFreeAgents(): Promise<RedraftFreeAgentsResult> {
      recordRead("freeAgents");
      return { leagueId: currentActive ?? "", freeAgents: [], rankingWarning: "", writeBehavior: "NO_SLEEPER_WRITES" };
    },
    async redraftOpponentRosters(): Promise<RedraftOpponentRostersResult> {
      recordRead("opponentRosters");
      return { leagueId: currentActive ?? "", opponents: [], rankingWarning: "", writeBehavior: "NO_SLEEPER_WRITES" };
    },
  };
  return {
    client,
    activateCalls,
    readsSeenDuring,
    getCurrentActive: () => currentActive,
    failProfile: (id: string) => failingProfileIds.add(id),
  };
}

describe("runAttentionCenterAggregation -- state-leakage regressions", () => {
  it("activates every league exactly once, in order, then restores the ORIGINAL active league last", async () => {
    const { client, activateCalls, getCurrentActive } = buildFakeClient(["A", "B", "C"]);
    const result = await runAttentionCenterAggregation(client, [profile({ profileId: "A" }), profile({ profileId: "B" }), profile({ profileId: "C" })], "B");
    expect(activateCalls).toEqual(["A", "B", "C", "B"]);
    expect(getCurrentActive()).toBe("B");
    expect(result.restoredBootstrap?.activeProfileId).toBe("B");
    expect(result.restoreError).toBeNull();
    expect(result.leagues.map((league) => league.profileId)).toEqual(["A", "B", "C"]);
  });

  it("every read for a given league happened while THAT league (and only that league) was active -- no cross-league contamination", async () => {
    const { client, readsSeenDuring } = buildFakeClient(["A", "B", "C"]);
    await runAttentionCenterAggregation(client, [profile({ profileId: "A" }), profile({ profileId: "B" }), profile({ profileId: "C" })], "A");
    // Every one of the 5 reads-per-Sleeper-league happened while exactly
    // that profile was the recorded "currently active" one -- if any read
    // had run while a DIFFERENT profile was active (the leakage bug class),
    // it would show up bucketed under the wrong key here.
    for (const id of ["A", "B", "C"]) {
      expect(readsSeenDuring[id]).toEqual(
        expect.arrayContaining(["dataHealth", "workspaceContext", "myRoster", "freeAgents", "opponentRosters"]),
      );
    }
    expect(readsSeenDuring.NONE).toBeUndefined();
  });

  it("still restores the original league when one league's read fails outright", async () => {
    const { client, failProfile, activateCalls } = buildFakeClient(["A", "B", "C"]);
    failProfile("B");
    const result = await runAttentionCenterAggregation(client, [profile({ profileId: "A" }), profile({ profileId: "B" }), profile({ profileId: "C" })], "A");
    expect(activateCalls).toEqual(["A", "B", "C", "A"]);
    expect(result.restoredBootstrap?.activeProfileId).toBe("A");
    // B's failure degrades honestly to a null dataHealth read (caught
    // per-call), not a thrown/aborted aggregation -- A and C are unaffected.
    const byId = Object.fromEntries(result.leagues.map((league) => [league.profileId, league]));
    expect(byId.A!.severity).toBe("OK");
    expect(byId.C!.severity).toBe("OK");
  });

  it("still restores the original league when activating one profile fails outright (e.g. a since-removed league)", async () => {
    const { client, activateCalls } = buildFakeClient(["A", "C"]); // "B" is not a real profile on this fake backend
    const result = await runAttentionCenterAggregation(client, [profile({ profileId: "A" }), profile({ profileId: "B" }), profile({ profileId: "C" })], "A");
    expect(activateCalls).toEqual(["A", "C", "A"]); // "B" never activated (its own activate call throws) -- not left active
    const byId = Object.fromEntries(result.leagues.map((league) => [league.profileId, league]));
    expect(byId.B!.fetchError).toBeTruthy();
    expect(byId.B!.severity).toBe("URGENT");
    expect(result.restoredBootstrap?.activeProfileId).toBe("A");
  });

  it("does nothing destructive and attempts no restore when there was no originally-active profile", async () => {
    const { client, activateCalls } = buildFakeClient(["A"]);
    const result = await runAttentionCenterAggregation(client, [profile({ profileId: "A" })], null);
    expect(activateCalls).toEqual(["A"]); // no trailing restore call
    expect(result.restoredBootstrap).toBeNull();
    expect(result.restoreError).toBeNull();
  });

  it("never interleaves two concurrent aggregation runs against the single shared active-profile pointer (rapid-switching guard)", async () => {
    const { client, activateCalls } = buildFakeClient(["A", "B", "X", "Y"]);
    // Simulate a UI double-trigger: two runs fired back to back before
    // either has resolved, over two DIFFERENT league sets with two
    // DIFFERENT original-active profiles.
    const first = runAttentionCenterAggregation(client, [profile({ profileId: "A" }), profile({ profileId: "B" })], "A");
    const second = runAttentionCenterAggregation(client, [profile({ profileId: "X" }), profile({ profileId: "Y" })], "X");
    const [firstResult, secondResult] = await Promise.all([first, second]);
    // If the two runs had interleaved, the recorded call sequence could
    // show e.g. ["A", "X", "B", "Y", ...] -- instead the WHOLE first run's
    // sequence (including its own restore) must appear contiguously
    // before the second run's sequence begins.
    expect(activateCalls).toEqual(["A", "B", "A", "X", "Y", "X"]);
    expect(firstResult.restoredBootstrap?.activeProfileId).toBe("A");
    expect(secondResult.restoredBootstrap?.activeProfileId).toBe("X");
  });

  it("never interleaves a sweep with an UNRELATED direct activateRedraftProfile call routed through the same shared queue (the residual cross-surface race Worker 3 flagged and this pass closed)", async () => {
    const { client, activateCalls, getCurrentActive } = buildFakeClient(["A", "B", "C", "Z"]);
    // Simulate: the owner opens Attention Center (a 3-league sweep,
    // originally-active "A"), and WHILE it is still mid-flight, follows a
    // direct link/bookmark/header-switch to league "Z" -- a call that goes
    // through `serializeActiveProfileCall` exactly the way
    // RedraftApp.tsx's `LeagueScopedPage`, shell-identity.tsx's
    // `switchLeague`, leagues.tsx's `activate`, and profile.tsx's
    // `activate` all now do (see those files). Before this pass, that
    // navigation call bypassed the queue entirely and could land in the
    // middle of the sweep's own activate/read sequence.
    const sweep = runAttentionCenterAggregation(
      client,
      [profile({ profileId: "A" }), profile({ profileId: "B" }), profile({ profileId: "C" })],
      "A",
    );
    const navigation = serializeActiveProfileCall(() => client.activateRedraftProfile("Z"));
    const [sweepResult, navigationBootstrap] = await Promise.all([sweep, navigation]);
    // The sweep's own activate sequence (A, B, C, then restore-to-A) must
    // appear fully contiguous, with the unrelated navigation's activate("Z")
    // queued strictly AFTER it -- never interleaved in between.
    expect(activateCalls).toEqual(["A", "B", "C", "A", "Z"]);
    expect(sweepResult.restoredBootstrap?.activeProfileId).toBe("A");
    // The navigation call's own response is honored last, since it was
    // queued after the sweep's restore -- the backend pointer ends on "Z",
    // matching where the owner actually navigated, not silently clobbered
    // back to "A" by the sweep's restore (which already happened earlier).
    expect(navigationBootstrap.activeProfileId).toBe("Z");
    expect(getCurrentActive()).toBe("Z");
  });

  it("never interleaves a sweep with a create/duplicate/import-style call that also activates its result server-side (dogfood_v1 cycle, Worker 3: reproduced live against the real running app before this fix -- see profile.tsx's create/duplicate/importSleeper and league.tsx's Settings-tab duplicate)", async () => {
    const { client, activateCalls, getCurrentActive } = buildFakeClient(["A", "B", "C", "NEW"]);
    // `createRedraftProfile`/`duplicateRedraftProfile`/`importSleeperRedraftProfile`
    // each activate their result as part of the SAME backend request/response
    // (see desktop_api/server.py's POST /api/v1/redraft/profiles handler and
    // desktop_facade.py's duplicate_redraft_profile/import_sleeper_redraft_profile,
    // both of which call set_active_profile). From the shared queue's point of
    // view that is indistinguishable from a direct `activateRedraftProfile`
    // call, so `client.activateRedraftProfile("NEW")` stands in for it here --
    // the real, live-reproduced bug was that profile.tsx's create/duplicate/
    // importSleeper (and league.tsx's own duplicate) called their contract
    // methods directly, entirely outside `serializeActiveProfileCall`, so a
    // sweep's own unconditional restore-to-original could fire AFTER the
    // create/duplicate/import's own activation and silently clobber the
    // brand-new profile's active status back to whatever league was active
    // before the sweep started -- reproduced live via a raw fetch race
    // against a simulated sweep, confirmed by re-reading the backend's own
    // bootstrap endpoint afterward.
    const sweep = runAttentionCenterAggregation(
      client,
      [profile({ profileId: "A" }), profile({ profileId: "B" }), profile({ profileId: "C" })],
      "A",
    );
    const createLikeCall = serializeActiveProfileCall(() => client.activateRedraftProfile("NEW"));
    const [sweepResult, createBootstrap] = await Promise.all([sweep, createLikeCall]);
    expect(activateCalls).toEqual(["A", "B", "C", "A", "NEW"]);
    expect(sweepResult.restoredBootstrap?.activeProfileId).toBe("A");
    // The create/duplicate/import call is honored LAST (queued strictly after
    // the sweep's own restore), so the backend pointer ends on the new
    // profile, matching what the owner actually just created/duplicated/
    // imported -- never silently reverted to whatever was active before the
    // sweep began.
    expect(createBootstrap.activeProfileId).toBe("NEW");
    expect(getCurrentActive()).toBe("NEW");
  });
});
