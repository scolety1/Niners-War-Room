import type { DraftBoard } from "@nwr/contracts";
import { describe, expect, it } from "vitest";

import {
  draftFormat,
  leagueFormat,
  leagueKeyFor,
  legacyRedirectTarget,
  resolveLeagueHomeSubpath,
  resolveLeagueLifecycle,
} from "./league-context";

const fantasyGamers = {
  profileId: "profile-fantasy-gamers",
  leagueName: "Fantasy Gamers",
  season: 2026,
  teamCount: 10,
  roster: { qb: 1, rb: 2, wr: 2, te: 1, flex: 1, superflex: 0, k: 1, dst: 1, benchSize: 6 },
  scoring: { passingYards: 0.04, passingTd: 4, interception: -2, rushingYards: 0.1, rushingTd: 6, receivingYards: 0.1, reception: 1, receivingTd: 6, passingFirstDown: 0, rushingFirstDown: 0, receivingFirstDown: 0, returnYards: 0, returnTd: 0, fumbleLost: -2, tePremium: 0, bonuses: {} },
  draft: { draftType: "snake" as const, draftSlot: 5, rounds: 15, keeperCount: 0, auctionBudget: null, rosterLimits: [{ position: "K", maximum: 1 }, { position: "DST", maximum: 1 }], adpContextEnabled: false, replacementMethod: "expected_available" as const },
  presetKey: null,
  archived: false,
  createdAtUtc: "",
  updatedAtUtc: "",
  practicalMode: true,
  nwrPureExperimental: false,
  provider: "sleeper" as const,
  providerLeagueId: "1312983576827920384",
};

describe("Redraft league context", () => {
  it("keeps Fantasy Gamers visibly PPR and tied to its Sleeper workspace", () => {
    expect(leagueFormat(fantasyGamers)).toBe("Sleeper · 2026 · 10-Team PPR · 1QB");
    expect(draftFormat(fantasyGamers)).toBe("2026 · 10-Team PPR · 1QB · Snake · Temporary Pick 5");
  });

  it("uses profileId as the stable league key", () => {
    expect(leagueKeyFor(fantasyGamers)).toBe("profile-fantasy-gamers");
  });
});

function board(overrides: Partial<DraftBoard>): DraftBoard {
  return {
    schemaVersion: 1,
    profileId: fantasyGamers.profileId,
    drafted: [],
    configured: false,
    ...overrides,
  } as DraftBoard;
}

describe("resolveLeagueLifecycle", () => {
  it("is PRE_DRAFT when the draft board was never configured", () => {
    expect(resolveLeagueLifecycle(fantasyGamers, null)).toBe("PRE_DRAFT");
    expect(resolveLeagueLifecycle(fantasyGamers, board({ configured: false }))).toBe("PRE_DRAFT");
  });

  it("is LIVE_DRAFT once picks exist but the board is not yet complete", () => {
    const partial = board({ configured: true, drafted: new Array(42).fill("p") });
    expect(resolveLeagueLifecycle(fantasyGamers, partial)).toBe("LIVE_DRAFT");
  });

  it("is IN_SEASON once drafted count reaches teamCount * rounds", () => {
    // fantasyGamers: teamCount 10, draft.rounds 15 -> 150 total picks
    const complete = board({ configured: true, drafted: new Array(150).fill("p") });
    expect(resolveLeagueLifecycle(fantasyGamers, complete)).toBe("IN_SEASON");
  });

  it("is OFFSEASON when the profile is archived, regardless of draft state", () => {
    const archived = { ...fantasyGamers, archived: true };
    const complete = board({ configured: true, drafted: new Array(150).fill("p") });
    expect(resolveLeagueLifecycle(archived, complete)).toBe("OFFSEASON");
  });
});

describe("resolveLeagueHomeSubpath", () => {
  it("sends a pre-draft or live-draft league to the Draft workspace", () => {
    expect(resolveLeagueHomeSubpath(fantasyGamers, null)).toBe("draft");
    expect(
      resolveLeagueHomeSubpath(fantasyGamers, board({ configured: true, drafted: ["p"] })),
    ).toBe("draft");
  });

  it("sends an in-season league to League Home, not the Draft Room", () => {
    // This is the exact real bug this pass fixed: leagues.tsx used to
    // unconditionally navigate every opened league to /draft-room-v2.
    const complete = board({ configured: true, drafted: new Array(150).fill("p") });
    expect(resolveLeagueHomeSubpath(fantasyGamers, complete)).toBe("home");
  });

  it("an explicit confirmedLifecycle always wins over the client-side guess", () => {
    expect(resolveLeagueHomeSubpath(fantasyGamers, null, "IN_SEASON")).toBe("home");
    const complete = board({ configured: true, drafted: new Array(150).fill("p") });
    expect(resolveLeagueHomeSubpath(fantasyGamers, complete, "PRE_DRAFT")).toBe("draft");
  });
});

// Directive invariant I: "old routes redirect correctly during migration".
describe("legacyRedirectTarget", () => {
  it("sends an old flat path into the active league's scoped route, same subpage", () => {
    expect(legacyRedirectTarget("profile-fantasy-gamers", "lineup")).toBe(
      "/league/profile-fantasy-gamers/lineup",
    );
    expect(legacyRedirectTarget("profile-fantasy-gamers", "tiers")).toBe(
      "/league/profile-fantasy-gamers/tiers",
    );
  });

  it("sends to the league chooser when no league is active", () => {
    expect(legacyRedirectTarget(null, "lineup")).toBe("/leagues");
  });

  it("URL-encodes the active profile id", () => {
    expect(legacyRedirectTarget("id with spaces", "waivers")).toBe(
      "/league/id%20with%20spaces/waivers",
    );
  });
});
