import type { DraftBoard, LeagueLifecycle, LeagueProfile } from "@nwr/contracts";

/**
 * NWR pre-UI product-architecture hardening pass (2026-09-10). ONE
 * authority for league identity/lifecycle/routing, consumed by
 * RedraftApp.tsx, leagues.tsx, and the new `/league/:leagueKey/*` route
 * tree -- see LEAGUE_CONTEXT.md and PRODUCT_ARCHITECTURE.md.
 *
 * Before this pass, none of this existed: `leagues.tsx` unconditionally
 * navigated every opened league straight to `/draft-room-v2` (a real,
 * reproduced bug -- opening an in-season league dropped the owner into
 * the draft room), and no route anywhere took a league identifier as a
 * URL param (confirmed by search: zero `useParams`/`:profileId`-style
 * routes existed in RedraftApp.tsx). `profileId` is used directly as the
 * "stable league key suitable for routing" the directive asks for --
 * it is already a stable, unique, opaque id per league profile; inventing
 * a second composite key would add a mapping layer with no real benefit.
 */

export type LeagueKey = string;

export function leagueKeyFor(profile: Pick<LeagueProfile, "profileId">): LeagueKey {
  return profile.profileId;
}

/**
 * Mirrors `src/services/league_lifecycle_service.py::resolve_league_lifecycle`
 * byte-for-byte in spirit (same four inputs, same branch order) so a
 * routing decision never needs an extra network round trip while staying
 * consistent with the backend authority used everywhere else (e.g.
 * `/api/v1/redraft/league-workspace-context`). Real, disclosed
 * limitation shared with the backend: no live NFL-calendar signal exists
 * in this app, so OFFSEASON is only reachable via an archived profile.
 */
export function resolveLeagueLifecycle(
  profile: Pick<LeagueProfile, "archived" | "teamCount" | "draft">,
  draftBoard: DraftBoard | null | undefined,
): LeagueLifecycle {
  if (profile.archived) return "OFFSEASON";
  const draftedCount = draftBoard?.drafted?.length ?? 0;
  const configured = Boolean(draftBoard?.configured);
  if (!configured || draftedCount <= 0) return "PRE_DRAFT";
  const totalDraftPicks = Math.max(0, profile.teamCount) * Math.max(0, profile.draft.rounds);
  if (totalDraftPicks > 0 && draftedCount >= totalDraftPicks) return "IN_SEASON";
  return "LIVE_DRAFT";
}

/**
 * Where opening/switching to this league should land the owner (directive
 * section 2, invariant A: "opening an in-season league does not
 * automatically drop the owner into Draft Room"). PRE_DRAFT/LIVE_DRAFT go
 * to the Draft workspace (there is nothing else meaningful to show yet);
 * IN_SEASON/OFFSEASON go to League Home.
 */
/**
 * Directive invariant I ("old routes redirect correctly during
 * migration"). Pure so it's testable without rendering: given the
 * currently active league (if any) and the legacy sub-page a flat route
 * used to render directly, returns the exact compatibility-redirect
 * target. `null` activeProfileId sends the owner to the league chooser
 * rather than a broken/empty scoped route.
 */
export function legacyRedirectTarget(
  activeProfileId: string | null,
  subpath: string,
): string {
  if (!activeProfileId) return "/leagues";
  return `/league/${encodeURIComponent(activeProfileId)}/${subpath}`;
}

export function resolveLeagueHomeSubpath(
  profile: Pick<LeagueProfile, "archived" | "teamCount" | "draft">,
  draftBoard: DraftBoard | null | undefined,
  confirmedLifecycle?: LeagueLifecycle,
): string {
  const lifecycle = confirmedLifecycle ?? resolveLeagueLifecycle(profile, draftBoard);
  if (lifecycle === "IN_SEASON" || lifecycle === "OFFSEASON") return "home";
  return "draft";
}

/**
 * NWR UI foundation-propagation pass (2026-09-11, directive Phase 1 --
 * "known bug": Rankings highlighted Cheat Sheet in the left nav instead
 * of Rankings). Root cause: every sidebar nav item still points at its
 * legacy flat path (e.g. `/rankings`), but that path is now a
 * compatibility redirect (`LegacyRedirect`) into the canonical
 * `/league/:leagueKey/<subpath>` route tree -- the browser's real
 * location after redirect is `/league/<key>/rankings`, which does not
 * literally start with `/rankings`, so react-router's own NavLink
 * `isActive` (a plain prefix match against `to`) never matches ANY
 * league-scoped nav item (confirmed empirically with react-router's own
 * `matchPath` against a scoped pathname before writing this fix -- every
 * candidate returned `null`, not merely the "wrong" one). This is the ONE
 * canonical mapping from a nav item's legacy path to the route subpath it
 * ultimately renders -- consumed by nav active-state resolution below.
 * Keep in sync with the `<Route path="/x" element={<LegacyRedirect .../>}>`
 * list in RedraftApp.tsx (that list is the other, pre-existing place this
 * same mapping already existed implicitly, one entry per route).
 */
export const NAV_LEGACY_PATH_SUBPATH: Record<string, string> = {
  "/league-home": "home",
  "/lineup": "lineup",
  "/waivers": "waivers",
  "/my-roster": "my-roster",
  "/trade-analysis": "trade-analysis",
  "/trade-finder": "trade-finder",
  "/free-agents": "free-agents",
  "/opponent-rosters": "opponent-rosters",
  "/draft-room-v2": "draft",
  "/rankings": "rankings",
  "/tiers": "tiers",
  "/compare": "compare",
  "/cheat-sheet": "cheat-sheet",
  "/profile": "profile",
  "/adp": "adp",
  "/weekly-tools": "weekly-tools",
  "/data-health": "data-health",
};

/**
 * The canonical owner-task-map route aliases (`/league/:key/league`,
 * `/improve`, `/players`, `/trades`) render the SAME page as an existing
 * concrete subpath (see RedraftApp.tsx) but are not any nav item's own
 * legacy path -- map each alias back to the concrete subpath it shares a
 * page with so a deep link to an alias URL still highlights the matching
 * nav item instead of nothing.
 */
export const ROUTE_ALIAS_SUBPATH: Record<string, string> = {
  league: "my-roster",
  improve: "waivers",
  players: "rankings",
  trades: "trade-analysis",
  // NWR UI expansion pass (2026-09-12, Trades surface): `/trade-finder`
  // now shares the SAME page as `/trade-analysis` (the unified
  // `TradesPage`, opened to its FIND TRADES tab) rather than a separate
  // standalone page -- same reasoning as `improve` -> `waivers` above, so
  // a deep link or bookmark to `/trade-finder` still highlights the one
  // "Trades" nav item instead of nothing.
  "trade-finder": "trade-analysis",
};

/**
 * The one canonical resolver behind sidebar nav active-state: given the
 * browser's real current pathname and the full set of nav item paths,
 * returns whichever nav item path should render as active, or `null` if
 * none apply (e.g. the league chooser). Pure and independent of
 * react-router's own matching so it is correct for BOTH a literal,
 * non-redirected path (`/leagues`, `/profile` with no active league) and
 * a post-redirect scoped path (`/league/<key>/rankings`) -- replaces
 * relying on NavLink's own prefix match, which cannot see past the
 * redirect (see the mapping above for why).
 */
export function resolveActiveNavPath(pathname: string, navPaths: readonly string[]): string | null {
  const literal = navPaths.find((path) => pathname === path || pathname.startsWith(`${path}/`));
  if (literal) return literal;
  const scoped = /^\/league\/[^/]+\/([^/]+)/.exec(pathname);
  const rawSubpath = scoped?.[1];
  if (!rawSubpath) return null;
  const subpath = ROUTE_ALIAS_SUBPATH[rawSubpath] ?? rawSubpath;
  return navPaths.find((path) => NAV_LEGACY_PATH_SUBPATH[path] === subpath) ?? null;
}

export function scoringFormat(profile: LeagueProfile): string {
  if (profile.scoring.reception === 1) return "PPR";
  if (profile.scoring.reception === 0.5) return "Half-PPR";
  if (profile.scoring.reception === 0) return "Standard";
  return `Custom (${profile.scoring.reception} per reception)`;
}

export function rosterFormat(profile: LeagueProfile): string {
  return profile.roster.superflex ? "Superflex" : "1QB";
}

export function providerFormat(profile: LeagueProfile): string {
  return profile.provider === "sleeper" ? "Sleeper" : "Local";
}

export function leagueFormat(profile: LeagueProfile, includeProvider = true): string {
  const parts = [
    ...(includeProvider ? [providerFormat(profile)] : []),
    String(profile.season),
    `${profile.teamCount}-Team ${scoringFormat(profile)}`,
    rosterFormat(profile),
  ];
  return parts.join(" · ");
}

export function leagueIdentityFormat(profile: LeagueProfile): string {
  return profile.provider === "sleeper" && profile.providerLeagueId
    ? `Sleeper · League ID ${profile.providerLeagueId}`
    : "Local Redraft profile";
}

export function draftFormat(profile: LeagueProfile): string {
  const draftType = profile.draft.draftType === "snake" ? "Snake" : "Auction";
  const slot = profile.draft.draftSlot === null
    ? "Temporary slot unassigned"
    : `Temporary Pick ${profile.draft.draftSlot}`;
  return `${leagueFormat(profile, false)} · ${draftType} · ${slot}`;
}
