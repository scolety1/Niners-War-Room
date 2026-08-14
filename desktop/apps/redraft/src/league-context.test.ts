import { describe, expect, it } from "vitest";

import { draftFormat, leagueFormat } from "./league-context";

const fantasyGamers = {
  profileId: "profile-fantasy-gamers",
  leagueName: "Fantasy Gamers",
  season: 2026,
  teamCount: 10,
  roster: { qb: 1, rb: 2, wr: 2, te: 1, flex: 1, superflex: 0, k: 1, dst: 1, benchSize: 6 },
  scoring: { passingYards: 0.04, passingTd: 4, interception: -2, rushingYards: 0.1, rushingTd: 6, receivingYards: 0.1, reception: 1, receivingTd: 6, passingFirstDown: 0, rushingFirstDown: 0, receivingFirstDown: 0, returnYards: 0, returnTd: 0, fumbleLost: -2, tePremium: 0, bonuses: {} },
  draft: { draftType: "snake" as const, draftSlot: 5, rounds: 15, keeperCount: 0, auctionBudget: null, rosterLimits: { K: 1, DST: 1 }, adpContextEnabled: false, replacementMethod: "expected_available" as const },
  presetKey: null,
  archived: false,
  createdAtUtc: "",
  updatedAtUtc: "",
  practicalMode: true,
  provider: "sleeper" as const,
  providerLeagueId: "1312983576827920384",
};

describe("Redraft league context", () => {
  it("keeps Fantasy Gamers visibly PPR and tied to its Sleeper workspace", () => {
    expect(leagueFormat(fantasyGamers)).toBe("Sleeper · 2026 · 10-Team PPR · 1QB");
    expect(draftFormat(fantasyGamers)).toBe("2026 · 10-Team PPR · 1QB · Snake · Temporary Pick 5");
  });
});
