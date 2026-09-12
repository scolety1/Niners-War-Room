import type { DraftBoard } from "@nwr/contracts";
import { describe, expect, it } from "vitest";

import {
  draftFormat,
  leagueFormat,
  leagueKeyFor,
  legacyRedirectTarget,
  resolveActiveNavPath,
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

// NWR UI foundation-propagation pass (2026-09-11, directive Phase 1):
// the known bug -- Rankings highlighted Cheat Sheet in the left nav
// instead of Rankings. Root cause was NavLink's own prefix match against
// a legacy flat nav path (`/rankings`) never seeing past the
// `/league/:leagueKey/...` redirect every one of those paths now goes
// through (confirmed with react-router's own `matchPath`: every legacy
// nav path returned `null` against a scoped pathname, not merely the
// wrong one). This exercises the canonical fix directly, independent of
// react-router or any rendering.
describe("resolveActiveNavPath", () => {
  const playersNavPaths = ["/rankings", "/tiers", "/compare", "/cheat-sheet", "/adp"];

  it("resolves Rankings active on the scoped Rankings route, not Cheat Sheet or any sibling", () => {
    expect(resolveActiveNavPath("/league/profile-fantasy-gamers/rankings", playersNavPaths)).toBe("/rankings");
  });

  // NWR UI expansion pass (2026-09-12, Players surface): this used to read
  // "resolves Tiers, Compare, and Market (adp) each to their own nav item"
  // and assert each resolved to itself -- true when Rankings/Tiers &
  // Positions/Compare/Market Data were four separate nav items. That real
  // nav item no longer exists (all four collapsed into one "Players" item,
  // path "/rankings", unified into one PlayersPage -- same consolidation
  // shape as Improve Team/Trades); `ROUTE_ALIAS_SUBPATH` now aliases
  // tiers/compare/adp back to "rankings" UNCONDITIONALLY (independent of
  // which navPaths list is passed in, same as the pre-existing `improve`/
  // `trade-finder` aliases), so this fixture -- which still lists "/tiers",
  // "/compare", "/adp" as if they were still real, separate nav items --
  // now correctly resolves all three to "/rankings" instead. This is the
  // intended, current product behavior, not a regression.
  it("resolves Tiers, Compare, and Market (adp) to the one Players nav item, not to separate items (Players surface, unified into one PlayersPage)", () => {
    expect(resolveActiveNavPath("/league/profile-fantasy-gamers/tiers", playersNavPaths)).toBe("/rankings");
    expect(resolveActiveNavPath("/league/profile-fantasy-gamers/compare", playersNavPaths)).toBe("/rankings");
    expect(resolveActiveNavPath("/league/profile-fantasy-gamers/adp", playersNavPaths)).toBe("/rankings");
  });

  it("resolves Cheat Sheet active only on its own scoped route", () => {
    expect(resolveActiveNavPath("/league/profile-fantasy-gamers/cheat-sheet", playersNavPaths)).toBe("/cheat-sheet");
  });

  it("still matches a literal, non-redirected path (no active league yet)", () => {
    expect(resolveActiveNavPath("/profile", ["/profile", "/rankings"])).toBe("/profile");
  });

  it("maps a canonical task-map alias route back to the nav item sharing its page", () => {
    // /league/:key/players renders the same RankingsPage as /rankings (see RedraftApp.tsx).
    expect(resolveActiveNavPath("/league/profile-fantasy-gamers/players", playersNavPaths)).toBe("/rankings");
    // /league/:key/improve and /league/:key/league and /league/:key/trades similarly alias.
    expect(resolveActiveNavPath("/league/profile-fantasy-gamers/improve", ["/waivers"])).toBe("/waivers");
    expect(resolveActiveNavPath("/league/profile-fantasy-gamers/league", ["/my-roster"])).toBe("/my-roster");
    expect(resolveActiveNavPath("/league/profile-fantasy-gamers/trades", ["/trade-analysis"])).toBe("/trade-analysis");
  });

  it("resolves the legacy /trade-finder subpath to the same Trades nav item (Trades surface, unified into one TradesPage)", () => {
    expect(resolveActiveNavPath("/league/profile-fantasy-gamers/trade-finder", ["/trade-analysis"])).toBe("/trade-analysis");
  });

  // NWR UI expansion pass (2026-09-12, League surface): My Roster/Opponent
  // Rosters collapsed into one "League" nav item (path "/my-roster"),
  // unified into one LeagueWorkspacePage. Exercised against the REAL
  // post-consolidation League nav path list -- same precedent as the
  // Players-surface test above for /tiers, /compare, /adp.
  it("resolves the legacy /opponent-rosters subpath to the one League nav item (League surface, unified into one LeagueWorkspacePage)", () => {
    const leagueNavPaths = ["/my-roster", "/profile", "/data-health"];
    expect(resolveActiveNavPath("/league/profile-fantasy-gamers/my-roster", leagueNavPaths)).toBe("/my-roster");
    expect(resolveActiveNavPath("/league/profile-fantasy-gamers/opponent-rosters", leagueNavPaths)).toBe("/my-roster");
    expect(resolveActiveNavPath("/league/profile-fantasy-gamers/league", leagueNavPaths)).toBe("/my-roster");
    expect(resolveActiveNavPath("/league/profile-fantasy-gamers/profile", leagueNavPaths)).toBe("/profile");
    expect(resolveActiveNavPath("/league/profile-fantasy-gamers/data-health", leagueNavPaths)).toBe("/data-health");
  });

  // NWR UI expansion pass (2026-09-12, Players surface): Rankings/Tiers &
  // Positions/Compare/Market Data collapsed into one "Players" nav item
  // (path "/rankings"), unified into one PlayersPage. Exercised against
  // the REAL post-consolidation nav path list (just "/rankings" and
  // "/cheat-sheet" -- not the pre-consolidation five-item list the earlier
  // tests above still use to prove the resolver's general behavior).
  it("resolves the legacy /tiers, /compare, and /adp subpaths to the one Players nav item (Players surface, unified into one PlayersPage)", () => {
    const consolidatedPlayersNavPaths = ["/rankings", "/cheat-sheet"];
    expect(resolveActiveNavPath("/league/profile-fantasy-gamers/rankings", consolidatedPlayersNavPaths)).toBe("/rankings");
    expect(resolveActiveNavPath("/league/profile-fantasy-gamers/tiers", consolidatedPlayersNavPaths)).toBe("/rankings");
    expect(resolveActiveNavPath("/league/profile-fantasy-gamers/compare", consolidatedPlayersNavPaths)).toBe("/rankings");
    expect(resolveActiveNavPath("/league/profile-fantasy-gamers/adp", consolidatedPlayersNavPaths)).toBe("/rankings");
    expect(resolveActiveNavPath("/league/profile-fantasy-gamers/players", consolidatedPlayersNavPaths)).toBe("/rankings");
    expect(resolveActiveNavPath("/league/profile-fantasy-gamers/cheat-sheet", consolidatedPlayersNavPaths)).toBe("/cheat-sheet");
  });

  it("returns null on the league chooser, where no nav item should be active", () => {
    expect(resolveActiveNavPath("/leagues", playersNavPaths)).toBeNull();
  });

  it("returns null for a scoped subpath no nav item maps to", () => {
    expect(resolveActiveNavPath("/league/profile-fantasy-gamers/unknown-subpath", playersNavPaths)).toBeNull();
  });
});
