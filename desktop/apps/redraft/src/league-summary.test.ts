import type {
  LeaguePlayoffContext,
  LeagueProfile,
  LeagueStandingsContext,
  LeagueStandingsRow,
  LeagueWeekMatchupContext,
  LeagueWorkspaceContext,
} from "@nwr/contracts";
import { describe, expect, it } from "vitest";

import {
  describeOwnerBracketEntry,
  formatCurrentWeek,
  formatRecord,
  formatStandingsRank,
  matchupStatusText,
  ownerStandingsRow,
  playoffStatusText,
  rosterCompositionRows,
  scoringSummaryGroups,
  syncHealthLabel,
  syncHealthTone,
} from "./league-summary";

function profile(overrides: Partial<LeagueProfile> = {}): LeagueProfile {
  return {
    profileId: "p1",
    leagueName: "Test League",
    season: 2026,
    teamCount: 10,
    roster: { qb: 1, rb: 2, wr: 2, te: 1, flex: 1, superflex: 0, k: 1, dst: 1, benchSize: 6 },
    scoring: {
      passingYards: 0.04,
      passingTd: 4,
      interception: -2,
      rushingYards: 0.1,
      rushingTd: 6,
      receivingYards: 0.1,
      reception: 1,
      receivingTd: 6,
      passingFirstDown: 0,
      rushingFirstDown: 0,
      receivingFirstDown: 0,
      returnYards: 0,
      returnTd: 6,
      fumbleLost: -2,
      tePremium: 0,
      bonuses: {},
    },
    draft: {
      draftType: "snake",
      draftSlot: null,
      rounds: 15,
      keeperCount: 0,
      auctionBudget: null,
      rosterLimits: [],
      adpContextEnabled: true,
      replacementMethod: "expected_available",
    },
    presetKey: null,
    archived: false,
    createdAtUtc: "2026-01-01T00:00:00Z",
    updatedAtUtc: "2026-01-01T00:00:00Z",
    practicalMode: false,
    nwrPureExperimental: false,
    provider: "sleeper",
    providerLeagueId: "123",
    ...overrides,
  };
}

describe("syncHealthTone / syncHealthLabel", () => {
  it("maps LIVE to a safe, healthy tone and label", () => {
    expect(syncHealthTone("LIVE")).toBe("safe");
    expect(syncHealthLabel("LIVE")).toBe("Live");
  });

  it("maps DEGRADED to a review tone and label", () => {
    expect(syncHealthTone("DEGRADED")).toBe("review");
    expect(syncHealthLabel("DEGRADED")).toBe("Degraded");
  });

  it("maps NOT_APPLICABLE to an offline tone, never a fabricated failure", () => {
    expect(syncHealthTone("NOT_APPLICABLE")).toBe("offline");
    expect(syncHealthLabel("NOT_APPLICABLE")).toBe("Not applicable");
  });

  it("covers every real syncStatus value the contract declares", () => {
    const statuses: LeagueWorkspaceContext["syncStatus"][] = ["LIVE", "DEGRADED", "NOT_APPLICABLE"];
    for (const status of statuses) {
      expect(typeof syncHealthTone(status)).toBe("string");
      expect(typeof syncHealthLabel(status)).toBe("string");
    }
  });
});

describe("formatCurrentWeek", () => {
  it("formats a real week number", () => {
    expect(formatCurrentWeek(7)).toBe("Week 7");
  });

  it("is honest about a null week rather than fabricating one", () => {
    expect(formatCurrentWeek(null)).toBe("Not available");
  });
});

describe("scoringSummaryGroups", () => {
  it("includes Passing/Rushing/Receiving/Other groups with real values", () => {
    const groups = scoringSummaryGroups(profile());
    const titles = groups.map((group) => group.title);
    expect(titles).toEqual(["Passing", "Rushing", "Receiving", "Other"]);
    const passing = groups.find((group) => group.title === "Passing")!;
    expect(passing.rows).toContainEqual({ label: "Passing TD", value: "4 pts" });
    expect(passing.rows).toContainEqual({ label: "Interception", value: "-2 pts" });
  });

  it("reads an honest 'None' for TE premium when the league has none configured", () => {
    const groups = scoringSummaryGroups(profile());
    const receiving = groups.find((group) => group.title === "Receiving")!;
    expect(receiving.rows).toContainEqual({ label: "TE premium", value: "None" });
  });

  it("shows a real TE premium value when the league configures one", () => {
    const groups = scoringSummaryGroups(profile({ scoring: { ...profile().scoring, tePremium: 0.5 } }));
    const receiving = groups.find((group) => group.title === "Receiving")!;
    expect(receiving.rows).toContainEqual({ label: "TE premium", value: "+0.5 pts for a TE reception" });
  });

  it("omits the Bonuses group entirely when the league has none, never a fabricated empty section", () => {
    const groups = scoringSummaryGroups(profile());
    expect(groups.some((group) => group.title === "Bonuses")).toBe(false);
  });

  it("includes a real Bonuses group when the league configures any", () => {
    const groups = scoringSummaryGroups(
      profile({ scoring: { ...profile().scoring, bonuses: { "100+ Yard Rushing Game": 3 } } }),
    );
    const bonuses = groups.find((group) => group.title === "Bonuses");
    expect(bonuses?.rows).toEqual([{ label: "100+ Yard Rushing Game", value: "3 pts" }]);
  });
});

describe("ownerStandingsRow / formatRecord / formatStandingsRank", () => {
  function standingsRow(overrides: Partial<LeagueStandingsRow> = {}): LeagueStandingsRow {
    return {
      rosterId: 1, teamName: "Me", wins: 5, losses: 2, ties: 0,
      pointsFor: 800, pointsAgainst: 700, isOwner: false, ...overrides,
    };
  }

  it("finds the owner's row by the isOwner flag", () => {
    const standings: LeagueStandingsContext = {
      rows: [standingsRow({ teamName: "Rival" }), standingsRow({ teamName: "Me", isOwner: true })],
      ownerRank: 2,
    };
    expect(ownerStandingsRow(standings)?.teamName).toBe("Me");
    expect(ownerStandingsRow(null)).toBeNull();
  });

  it("formats a record without ties, and with ties only when real", () => {
    expect(formatRecord(standingsRow({ wins: 5, losses: 2, ties: 0 }))).toBe("5-2");
    expect(formatRecord(standingsRow({ wins: 5, losses: 2, ties: 1 }))).toBe("5-2-1");
    expect(formatRecord(null)).toBe("Unavailable");
  });

  it("formats rank as honest text or null when standings/rank are unavailable", () => {
    expect(formatStandingsRank({ rows: [standingsRow(), standingsRow()], ownerRank: 1 })).toBe("#1 of 2");
    expect(formatStandingsRank({ rows: [standingsRow()], ownerRank: null })).toBeNull();
    expect(formatStandingsRank(null)).toBeNull();
  });
});

describe("matchupStatusText", () => {
  function matchup(overrides: Partial<LeagueWeekMatchupContext> = {}): LeagueWeekMatchupContext {
    return {
      week: 4, hasOpponent: true, ownerPoints: 100, opponentRosterId: 2,
      opponentTeamName: "Rival", opponentPoints: 90, note: null, ...overrides,
    };
  }

  it("returns null (render the real score instead) when a real opponent exists", () => {
    expect(matchupStatusText(matchup())).toBeNull();
  });

  it("surfaces the real bye-week/unavailable note instead of a blank matchup", () => {
    expect(matchupStatusText(matchup({ hasOpponent: false, note: "Bye week -- no opponent is scheduled this week." })))
      .toBe("Bye week -- no opponent is scheduled this week.");
  });

  it("is honest about a missing matchup context entirely", () => {
    expect(matchupStatusText(null)).toBeNull();
  });
});

describe("describeOwnerBracketEntry / playoffStatusText", () => {
  function playoff(overrides: Partial<LeaguePlayoffContext> = {}): LeaguePlayoffContext {
    return {
      leagueStatus: "in_season", playoffWeekStart: 15, inPlayoffs: false,
      bracketAvailable: false, bracket: [], ...overrides,
    };
  }

  it("is null for a non-playoff-state league with no generated bracket", () => {
    expect(describeOwnerBracketEntry(playoff(), 1)).toBeNull();
  });

  it("describes the owner's real in-progress bracket matchup", () => {
    const context = playoff({
      inPlayoffs: true,
      bracketAvailable: true,
      bracket: [{
        round: 1, team1RosterId: 1, team1TeamName: "Me", team2RosterId: 2, team2TeamName: "Rival",
        winnerRosterId: null, winnerTeamName: null, involvesOwner: true,
      }],
    });
    expect(describeOwnerBracketEntry(context, 1)).toBe("Playoff round 1: vs Rival.");
  });

  it("describes a real completed bracket result (won/lost), never a prediction", () => {
    const won = playoff({
      inPlayoffs: true, bracketAvailable: true,
      bracket: [{
        round: 1, team1RosterId: 1, team1TeamName: "Me", team2RosterId: 2, team2TeamName: "Rival",
        winnerRosterId: 1, winnerTeamName: "Me", involvesOwner: true,
      }],
    });
    expect(describeOwnerBracketEntry(won, 1)).toBe("Playoff round 1: won vs Rival.");

    const lost = playoff({
      inPlayoffs: true, bracketAvailable: true,
      bracket: [{
        round: 1, team1RosterId: 1, team1TeamName: "Me", team2RosterId: 2, team2TeamName: "Rival",
        winnerRosterId: 2, winnerTeamName: "Rival", involvesOwner: true,
      }],
    });
    expect(describeOwnerBracketEntry(lost, 1)).toBe("Playoff round 1: lost vs Rival.");
  });

  it("reports the real regular-season/playoff status, never a simulated odds claim", () => {
    expect(playoffStatusText(playoff({ inPlayoffs: true }))).toBe("In the playoffs.");
    expect(playoffStatusText(playoff({ inPlayoffs: false, playoffWeekStart: 15 }))).toBe("Playoffs start Week 15.");
    expect(playoffStatusText(playoff({ inPlayoffs: false, playoffWeekStart: null }))).toBeNull();
    expect(playoffStatusText(null)).toBeNull();
  });
});

describe("rosterCompositionRows", () => {
  it("omits zero-count Superflex/K/DST slots rather than showing a confusing 0", () => {
    const rows = rosterCompositionRows(profile({ roster: { qb: 1, rb: 2, wr: 2, te: 1, flex: 1, superflex: 0, k: 0, dst: 0, benchSize: 6 } }));
    expect(rows.map((row) => row.label)).toEqual(["QB", "RB", "WR", "TE", "Flex", "Bench"]);
  });

  it("includes Superflex/K/DST when the league configures them", () => {
    const rows = rosterCompositionRows(profile({ roster: { qb: 1, rb: 2, wr: 2, te: 1, flex: 1, superflex: 1, k: 1, dst: 1, benchSize: 6 } }));
    expect(rows.map((row) => row.label)).toEqual(["QB", "RB", "WR", "TE", "Flex", "Superflex", "K", "DST", "Bench"]);
  });
});
