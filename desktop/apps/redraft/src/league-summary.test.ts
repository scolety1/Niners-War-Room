import type { LeagueProfile, LeagueWorkspaceContext } from "@nwr/contracts";
import { describe, expect, it } from "vitest";

import {
  formatCurrentWeek,
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
