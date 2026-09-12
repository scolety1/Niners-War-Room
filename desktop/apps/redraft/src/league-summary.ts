import type { LeagueProfile, LeagueWorkspaceContext } from "@nwr/contracts";

/**
 * NWR UI expansion pass (2026-09-12, League surface): pure derivation, same
 * family as `lineup-explain.ts`/`improve-team-explain.ts`/`trades-explain.ts`
 * -- dependency-free, unit-tested, no JSX. The League workspace (league.tsx)
 * only renders what these functions compute; no new data or scoring math --
 * every field read here already exists on `LeagueProfile`/
 * `LeagueWorkspaceContext` (the latter previously fetched by NO frontend
 * surface at all -- confirmed by a whole-repo search before writing this --
 * a real, disclosed wiring gap this pass closes for `currentWeek`/
 * `syncStatus`/`syncAsOf`/`issues`, the same class of "real backend field,
 * never surfaced" finding the Players pass made for the ADP-preview `View`
 * action).
 */

export type SyncHealthTone = "safe" | "review" | "offline";

const SYNC_STATUS_TONE: Record<LeagueWorkspaceContext["syncStatus"], SyncHealthTone> = {
  LIVE: "safe",
  DEGRADED: "review",
  NOT_APPLICABLE: "offline",
};

const SYNC_STATUS_LABEL: Record<LeagueWorkspaceContext["syncStatus"], string> = {
  LIVE: "Live",
  DEGRADED: "Degraded",
  NOT_APPLICABLE: "Not applicable",
};

export function syncHealthTone(status: LeagueWorkspaceContext["syncStatus"]): SyncHealthTone {
  return SYNC_STATUS_TONE[status] ?? "review";
}

export function syncHealthLabel(status: LeagueWorkspaceContext["syncStatus"]): string {
  return SYNC_STATUS_LABEL[status] ?? status;
}

export function formatCurrentWeek(week: number | null): string {
  return week === null ? "Not available" : `Week ${week}`;
}

export interface LeagueSummaryRow {
  label: string;
  value: string;
}

export interface LeagueSummaryGroup {
  title: string;
  rows: LeagueSummaryRow[];
}

function points(value: number): string {
  return `${value} pt${value === 1 || value === -1 ? "" : "s"}`;
}

/**
 * Every real scoring rule on the active profile, grouped for a compact
 * read-only display -- including fields the roster/scoring EDIT form
 * (`profile.tsx`'s `ProfileEditor`) never exposed (yards-per-point
 * thresholds, first-down/return/fumble rules, bonuses), so the owner can
 * see the FULL real rule set this league scores against, not only the four
 * fields that happen to be editable. Presentation only -- no new
 * computation, every value is read directly off `LeagueProfile.scoring`.
 */
export function scoringSummaryGroups(profile: LeagueProfile): LeagueSummaryGroup[] {
  const scoring = profile.scoring;
  const groups: LeagueSummaryGroup[] = [
    {
      title: "Passing",
      rows: [
        { label: "Per passing yard", value: points(scoring.passingYards) },
        { label: "Passing TD", value: points(scoring.passingTd) },
        { label: "Interception", value: points(scoring.interception) },
        { label: "First down", value: points(scoring.passingFirstDown) },
      ],
    },
    {
      title: "Rushing",
      rows: [
        { label: "Per rushing yard", value: points(scoring.rushingYards) },
        { label: "Rushing TD", value: points(scoring.rushingTd) },
        { label: "First down", value: points(scoring.rushingFirstDown) },
      ],
    },
    {
      title: "Receiving",
      rows: [
        { label: "Reception", value: points(scoring.reception) },
        { label: "Per receiving yard", value: points(scoring.receivingYards) },
        { label: "Receiving TD", value: points(scoring.receivingTd) },
        { label: "First down", value: points(scoring.receivingFirstDown) },
        { label: "TE premium", value: scoring.tePremium ? `+${points(scoring.tePremium)} for a TE reception` : "None" },
      ],
    },
    {
      title: "Other",
      rows: [
        { label: "Return yard", value: points(scoring.returnYards) },
        { label: "Return TD", value: points(scoring.returnTd) },
        { label: "Fumble lost", value: points(scoring.fumbleLost) },
      ],
    },
  ];
  const bonusEntries = Object.entries(scoring.bonuses ?? {});
  if (bonusEntries.length) {
    groups.push({
      title: "Bonuses",
      rows: bonusEntries.map(([key, value]) => ({ label: key, value: points(value) })),
    });
  }
  return groups;
}

/** Roster construction, compact and read-only -- zero-count positions
 * (e.g. no Superflex slot configured) are omitted rather than shown as a
 * confusing "0". */
export function rosterCompositionRows(profile: LeagueProfile): LeagueSummaryRow[] {
  const roster = profile.roster;
  const rows: LeagueSummaryRow[] = [
    { label: "QB", value: String(roster.qb) },
    { label: "RB", value: String(roster.rb) },
    { label: "WR", value: String(roster.wr) },
    { label: "TE", value: String(roster.te) },
    { label: "Flex", value: String(roster.flex) },
  ];
  if (roster.superflex > 0) rows.push({ label: "Superflex", value: String(roster.superflex) });
  if (roster.k > 0) rows.push({ label: "K", value: String(roster.k) });
  if (roster.dst > 0) rows.push({ label: "DST", value: String(roster.dst) });
  rows.push({ label: "Bench", value: String(roster.benchSize) });
  return rows;
}
