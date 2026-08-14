import type { LeagueProfile } from "@nwr/contracts";

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
