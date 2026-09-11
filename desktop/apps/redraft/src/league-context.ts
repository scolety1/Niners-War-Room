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
