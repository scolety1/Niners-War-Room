import type {
  DataHealthReport,
  LeagueLifecycle,
  LeagueProfile,
  LeagueWorkspaceContext,
  RedraftBootstrap,
  RedraftFreeAgentsResult,
  RedraftMyRosterResult,
  RedraftOpponentRostersResult,
} from "@nwr/contracts";

import { formatRecord, formatStandingsRank, ownerStandingsRow, playoffStatusText } from "./league-summary";

/**
 * P1-2 (2026-09-12): Multi-League Attention Center -- pure orchestration +
 * derivation, same family as `league-summary.ts`/`weekly-shared.tsx`. This
 * is a READ-ONLY aggregation layer over the existing single-league
 * architecture (directive: "Do NOT mutate the single-league architecture
 * underneath it"). It never adds a backend route, never touches
 * `LeagueSnapshot`/`LeagueWorkspaceContext` semantics, and never runs the
 * Start/Sit, Waiver, Trade Finder, or K/DST Streamer engines -- every
 * per-league read below reuses an already-existing CHEAP endpoint
 * (`activateRedraftProfile`, `redraftDataHealth`, `redraftLeagueWorkspaceContext`,
 * plus, for a Sleeper league only, the already-existing roster/free-agent
 * reads that themselves only call Sleeper's own read-only roster/player
 * endpoints -- no projection/decision engine is invoked for any of them).
 *
 * THE CORE SAFETY PROPERTY (directive's own top risk item): this app's
 * backend has exactly ONE "active profile" pointer, and every per-league
 * read (data health, workspace context, my roster, free agents, opponent
 * rosters) implicitly reads whichever profile is CURRENTLY active -- there
 * is no "read profile X's data without activating it" endpoint. Building a
 * cross-league view therefore requires activating each league in turn,
 * reading its cheap facts, and then -- unconditionally, in a `finally`,
 * regardless of success/failure/partial-completion -- reactivating
 * whichever profile was active before this aggregation started. Every
 * function below that touches the client is written so that guarantee
 * cannot be skipped.
 */

export type AttentionSeverity = "URGENT" | "WATCH" | "OK" | "UNKNOWN";

const SEVERITY_ORDER: Record<AttentionSeverity, number> = { OK: 0, UNKNOWN: 1, WATCH: 2, URGENT: 3 };

export function worstSeverity(a: AttentionSeverity, b: AttentionSeverity): AttentionSeverity {
  return SEVERITY_ORDER[a] >= SEVERITY_ORDER[b] ? a : b;
}

export type AttentionFlagKind =
  | "LEAGUE_UNREACHABLE"
  | "SYNC_DEGRADED"
  | "DATA_DEGRADED"
  | "ROSTER_IDENTITY_UNRESOLVED"
  | "WAIVER_OPPORTUNITY"
  | "PLAYOFF_DEADLINE"
  | "WORKSPACE_ISSUE"
  | "LIVE_DRAFT_IN_PROGRESS";

export interface AttentionFlag {
  kind: AttentionFlagKind;
  severity: AttentionSeverity;
  summary: string;
  detail?: string;
}

export interface LeagueAttentionSummary {
  profileId: string;
  leagueName: string;
  provider: LeagueProfile["provider"];
  lifecycle: LeagueLifecycle | null;
  currentWeek: number | null;
  record: string | null;
  standingsRank: string | null;
  deadlineText: string | null;
  flags: AttentionFlag[];
  severity: AttentionSeverity;
  fetchError: string | null;
}

// ---------------------------------------------------------------------------
// Per-signal flag derivation. Each function is pure and independently
// testable; `summarizeLeagueAttention` below composes them. Every branch
// reflects a real, already-computed backend fact -- nothing here re-derives
// a recommendation or re-runs a decision engine.
// ---------------------------------------------------------------------------

const DATA_HEALTH_OK_STATUSES = new Set(["OK", "NOT_APPLICABLE", "NO_ACTIVITY"]);

/** Data Health is this app's own existing, cheap, already-composed status
 * authority (`redraft_data_health` -- see desktop_facade.py) -- reusing it
 * here is exactly the "cheap/cached read aggregation" the directive asks
 * for, instead of re-deriving a second, competing health signal. */
export function dataHealthFlags(report: DataHealthReport | null | undefined): AttentionFlag[] {
  if (!report) return [];
  const flags: AttentionFlag[] = [];
  for (const category of report.categories) {
    if (DATA_HEALTH_OK_STATUSES.has(category.status)) continue;
    // Only LEAGUE_SYNC going UNAVAILABLE is treated as URGENT here -- it
    // means the league's own provider connection is broken, a genuinely
    // "this league needs you" fact. Every other category (a missing ADP
    // import, a stale weekly-projection cache, no decision-trace activity
    // yet, ...) is real and worth surfacing, but routinely true for a
    // pre-draft or lightly-used league and would otherwise drown the
    // signal by marking every single league "urgent" -- confirmed live
    // against this worktree's own 5 real saved profiles while building
    // this page (see NWR_POST_UI_WORKDAY_LEDGER.md).
    const severity: AttentionSeverity =
      category.category === "LEAGUE_SYNC" && category.status === "UNAVAILABLE" ? "URGENT" : "WATCH";
    flags.push({
      kind: category.category === "LEAGUE_SYNC" ? "SYNC_DEGRADED" : "DATA_DEGRADED",
      severity,
      summary: `${category.category.replaceAll("_", " ")}: ${category.status.replaceAll("_", " ")}`,
      ...(category.degradationReason ? { detail: category.degradationReason } : {}),
    });
  }
  return flags;
}

/** The real, disclosed workspace facts (P1-1) -- a live draft in progress
 * is always urgent (the owner has an active clock somewhere), and any
 * non-empty `issues` array is the workspace context's own honest
 * self-report of a problem, not a heuristic invented here. */
export function workspaceFlags(context: LeagueWorkspaceContext | null | undefined): AttentionFlag[] {
  if (!context) return [];
  const flags: AttentionFlag[] = [];
  if (context.lifecycle === "LIVE_DRAFT") {
    flags.push({ kind: "LIVE_DRAFT_IN_PROGRESS", severity: "URGENT", summary: "A live draft is in progress." });
  }
  if (context.issues.length) {
    flags.push({
      kind: "WORKSPACE_ISSUE",
      severity: "WATCH",
      summary: `${context.issues.length} workspace issue${context.issues.length === 1 ? "" : "s"} reported.`,
      detail: context.issues.join("; "),
    });
  }
  return flags;
}

/** A real, existing per-row fact (`RedraftMyRosterPlayer.identityStatus`) --
 * not a new computation. An unresolved identity means NWR could not tie a
 * live Sleeper roster slot to a canonical player, which silently degrades
 * every ranked/projected view of that player for this league. */
export function rosterIdentityFlags(roster: RedraftMyRosterResult | null | undefined): AttentionFlag[] {
  if (!roster) return [];
  const unresolved = roster.roster.filter((player) => player.identityStatus === "UNMATCHED_IDENTITY");
  if (!unresolved.length) return [];
  return [
    {
      kind: "ROSTER_IDENTITY_UNRESOLVED",
      severity: "WATCH",
      summary: `${unresolved.length} rostered player${unresolved.length === 1 ? "" : "s"} could not be matched to an NWR identity.`,
      detail: unresolved.map((player) => player.playerName).join(", "),
    },
  ];
}

/** Heuristic, disclosed as such (same pattern as `statusTone` in
 * weekly-shared.tsx): a highly-ranked NWR player still sitting in the free
 * agent pool is a real, cheap "worth a look" signal -- this reads the
 * SAME ranked free-agent list the Free Agents page already fetches (a
 * ranking lookup, not the REST_OF_SEASON Waiver engine's FAAB/matchup
 * modeling), it does not run any waiver recommendation logic. */
const WAIVER_OPPORTUNITY_RANK_THRESHOLD = 60;

export function waiverOpportunityFlags(freeAgents: RedraftFreeAgentsResult | null | undefined): AttentionFlag[] {
  if (!freeAgents) return [];
  const top = freeAgents.freeAgents.find(
    (agent) => agent.overallRank != null && agent.overallRank <= WAIVER_OPPORTUNITY_RANK_THRESHOLD,
  );
  if (!top) return [];
  return [
    {
      kind: "WAIVER_OPPORTUNITY",
      severity: "WATCH",
      summary: `${top.playerName} (#${top.overallRank} overall) is available as a free agent.`,
    },
  ];
}

/** The ONLY real "deadline" fact this app tracks anywhere (no trade
 * deadline is modeled in any contract) -- Sleeper's own reported playoff
 * start week, already surfaced by P1-1. Flagged only when it is imminent
 * (this week or next) so the summary list isn't cluttered by a fact that
 * is many weeks away. */
export function deadlineFlags(context: LeagueWorkspaceContext | null | undefined): AttentionFlag[] {
  const playoff = context?.playoff;
  if (!playoff || playoff.inPlayoffs || playoff.playoffWeekStart == null || context?.currentWeek == null) return [];
  const weeksUntil = playoff.playoffWeekStart - context.currentWeek;
  if (weeksUntil < 0 || weeksUntil > 1) return [];
  return [
    {
      kind: "PLAYOFF_DEADLINE",
      severity: "WATCH",
      summary: weeksUntil === 0 ? "Playoffs start this week." : "Playoffs start next week.",
    },
  ];
}

export interface LeagueAttentionInputs {
  profile: LeagueProfile;
  dataHealth: DataHealthReport | null;
  workspaceContext: LeagueWorkspaceContext | null;
  myRoster: RedraftMyRosterResult | null;
  freeAgents: RedraftFreeAgentsResult | null;
  fetchError: string | null;
}

export function summarizeLeagueAttention(inputs: LeagueAttentionInputs): LeagueAttentionSummary {
  const { profile, dataHealth, workspaceContext, myRoster, freeAgents, fetchError } = inputs;
  const flags: AttentionFlag[] = [];
  if (fetchError) {
    flags.push({
      kind: "LEAGUE_UNREACHABLE",
      severity: "URGENT",
      summary: "This league's status could not be read.",
      detail: fetchError,
    });
  } else {
    flags.push(...dataHealthFlags(dataHealth));
    flags.push(...workspaceFlags(workspaceContext));
    flags.push(...rosterIdentityFlags(myRoster));
    flags.push(...waiverOpportunityFlags(freeAgents));
    flags.push(...deadlineFlags(workspaceContext));
  }
  const severity = flags.reduce<AttentionSeverity>((worst, flag) => worstSeverity(worst, flag.severity), "OK");
  const standings = workspaceContext?.standings ?? null;
  return {
    profileId: profile.profileId,
    leagueName: profile.leagueName,
    provider: profile.provider,
    lifecycle: workspaceContext?.lifecycle ?? null,
    currentWeek: workspaceContext?.currentWeek ?? null,
    record: fetchError ? null : formatRecord(ownerStandingsRow(standings)),
    standingsRank: fetchError ? null : formatStandingsRank(standings),
    deadlineText: fetchError ? null : playoffStatusText(workspaceContext?.playoff ?? null),
    flags,
    severity,
    fetchError,
  };
}

// ---------------------------------------------------------------------------
// Cross-league player ownership/availability search.
// ---------------------------------------------------------------------------

export type PlayerOwnershipStatus = "ROSTERED_BY_YOU" | "ROSTERED_BY_OPPONENT" | "AVAILABLE";

export interface LeagueOwnershipEntry {
  playerName: string;
  status: PlayerOwnershipStatus;
  teamName: string | null;
}

/**
 * Live Sleeper leagues: built from the SAME three already-existing,
 * read-only Sleeper endpoints the League/Free Agents pages already use
 * (my roster, opponent rosters, free agents) -- each is a plain roster/
 * player-pool read, not a decision engine.
 *
 * Local/manual (non-Sleeper) leagues have no live provider to read, so
 * ownership is derived from the SAME bootstrap `rankings` this profile's
 * own `activateRedraftProfile` call already returned (`drafted`/
 * `draftedBy`) plus the draft board's own per-team roster (to tell "you"
 * apart from "an opponent") -- no extra network call, no re-derivation.
 */
export function buildLeagueOwnershipEntries(
  profile: LeagueProfile,
  bootstrap: RedraftBootstrap,
  myRoster: RedraftMyRosterResult | null,
  freeAgents: RedraftFreeAgentsResult | null,
  opponents: RedraftOpponentRostersResult | null,
): LeagueOwnershipEntry[] {
  const entries: LeagueOwnershipEntry[] = [];
  if (profile.provider === "sleeper") {
    for (const player of myRoster?.roster ?? []) {
      entries.push({ playerName: player.playerName, status: "ROSTERED_BY_YOU", teamName: null });
    }
    for (const opponent of opponents?.opponents ?? []) {
      for (const player of opponent.players) {
        entries.push({ playerName: player.playerName, status: "ROSTERED_BY_OPPONENT", teamName: opponent.teamName || null });
      }
    }
    for (const agent of freeAgents?.freeAgents ?? []) {
      entries.push({ playerName: agent.playerName, status: "AVAILABLE", teamName: null });
    }
    return entries;
  }
  const ownerTeam = bootstrap.draftBoard?.teams?.find((team) => team.owner) ?? null;
  const ownerPlayerIds = new Set((ownerTeam?.roster ?? []).map((player) => player.playerId));
  for (const ranking of bootstrap.rankings) {
    if (!ranking.drafted) {
      entries.push({ playerName: ranking.playerName, status: "AVAILABLE", teamName: null });
    } else if (ownerPlayerIds.has(ranking.playerId)) {
      entries.push({ playerName: ranking.playerName, status: "ROSTERED_BY_YOU", teamName: null });
    } else {
      entries.push({ playerName: ranking.playerName, status: "ROSTERED_BY_OPPONENT", teamName: ranking.draftedBy || null });
    }
  }
  return entries;
}

export interface PlayerSearchRow {
  profileId: string;
  leagueName: string;
  status: PlayerOwnershipStatus | "UNKNOWN";
  teamName: string | null;
  matchedName: string | null;
}

/**
 * Case-insensitive substring match against whatever ownership facts were
 * actually read for each league. A league that could not be read at all
 * (see `LeagueAttentionSummary.fetchError`) or a query that matches
 * nothing in a league that WAS read both honestly resolve to `UNKNOWN`
 * (directive: "League D: unavailable/unknown") rather than a false
 * "available" default.
 */
export function searchPlayerAcrossLeagues(
  leagues: LeagueAttentionSummary[],
  ownershipByProfile: Record<string, LeagueOwnershipEntry[]>,
  query: string,
): PlayerSearchRow[] {
  const trimmed = query.trim().toLowerCase();
  if (!trimmed) return [];
  return leagues.map((league) => {
    const entries = ownershipByProfile[league.profileId] ?? [];
    const match = entries.find((entry) => entry.playerName.toLowerCase().includes(trimmed));
    if (!match) {
      return { profileId: league.profileId, leagueName: league.leagueName, status: "UNKNOWN", teamName: null, matchedName: null };
    }
    return {
      profileId: league.profileId,
      leagueName: league.leagueName,
      status: match.status,
      teamName: match.teamName,
      matchedName: match.playerName,
    };
  });
}

// ---------------------------------------------------------------------------
// Orchestration: the one place that actually calls the shared-state client.
// ---------------------------------------------------------------------------

/** The narrow slice of `NwrApiClient` this module needs -- `NwrApiClient`
 * itself satisfies this structurally, and tests can pass a plain fake
 * object instead of standing up the real client. */
export interface AttentionCenterClient {
  activateRedraftProfile(profileId: string): Promise<RedraftBootstrap>;
  redraftDataHealth(): Promise<DataHealthReport>;
  redraftLeagueWorkspaceContext(): Promise<LeagueWorkspaceContext>;
  redraftMyRoster(): Promise<RedraftMyRosterResult>;
  redraftFreeAgents(): Promise<RedraftFreeAgentsResult>;
  redraftOpponentRosters(): Promise<RedraftOpponentRostersResult>;
}

interface LeagueFetchResult {
  summary: LeagueAttentionSummary;
  ownership: LeagueOwnershipEntry[];
}

async function fetchLeagueAttention(
  client: AttentionCenterClient,
  profile: LeagueProfile,
): Promise<LeagueFetchResult> {
  try {
    const bootstrap = await client.activateRedraftProfile(profile.profileId);
    const isSleeper = (bootstrap.activeProfile ?? profile).provider === "sleeper";
    const [dataHealth, workspaceContext] = await Promise.all([
      client.redraftDataHealth().catch(() => null),
      client.redraftLeagueWorkspaceContext().catch(() => null),
    ]);
    let myRoster: RedraftMyRosterResult | null = null;
    let freeAgents: RedraftFreeAgentsResult | null = null;
    let opponents: RedraftOpponentRostersResult | null = null;
    if (isSleeper) {
      [myRoster, freeAgents, opponents] = await Promise.all([
        client.redraftMyRoster().catch(() => null),
        client.redraftFreeAgents().catch(() => null),
        client.redraftOpponentRosters().catch(() => null),
      ]);
    }
    const summary = summarizeLeagueAttention({
      profile, dataHealth, workspaceContext, myRoster, freeAgents, fetchError: null,
    });
    const ownership = buildLeagueOwnershipEntries(profile, bootstrap, myRoster, freeAgents, opponents);
    return { summary, ownership };
  } catch (reason) {
    const message = reason instanceof Error ? reason.message : "This league could not be opened.";
    const summary = summarizeLeagueAttention({
      profile, dataHealth: null, workspaceContext: null, myRoster: null, freeAgents: null, fetchError: message,
    });
    return { summary, ownership: [] };
  }
}

export interface AttentionCenterResult {
  leagues: LeagueAttentionSummary[];
  ownershipByProfile: Record<string, LeagueOwnershipEntry[]>;
  /** The confirmed-fresh bootstrap for whichever profile was active BEFORE
   * this aggregation started, read back from the restore call's own
   * response -- never a value observed mid-loop. `null` when there was
   * nothing to restore (no profile was active beforehand) or the restore
   * itself failed (see `restoreError`). */
  restoredBootstrap: RedraftBootstrap | null;
  restoreError: string | null;
}

async function runAttentionCenterAggregationUnserialized(
  client: AttentionCenterClient,
  profiles: LeagueProfile[],
  originalActiveProfileId: string | null,
): Promise<AttentionCenterResult> {
  const leagues: LeagueAttentionSummary[] = [];
  const ownershipByProfile: Record<string, LeagueOwnershipEntry[]> = {};
  let restoredBootstrap: RedraftBootstrap | null = null;
  let restoreError: string | null = null;
  try {
    for (const profile of profiles) {
      // Sequential, on purpose: only ONE profile is ever active on the
      // backend at a time, so reading league B before league A's read has
      // fully resolved would risk attributing league A's read to league B
      // (or vice-versa). This is the direct mechanical cause of the
      // state-leakage bug class this whole shift keeps finding -- see
      // attention-center.test.ts's dedicated regression coverage.
      // eslint-disable-next-line no-await-in-loop
      const { summary, ownership } = await fetchLeagueAttention(client, profile);
      leagues.push(summary);
      ownershipByProfile[profile.profileId] = ownership;
    }
  } finally {
    // Unconditional restore -- runs whether the loop above completed
    // cleanly, was empty, or (structurally impossible today since every
    // per-league read is already try/caught inside `fetchLeagueAttention`,
    // but kept as a second, structural guarantee) threw. This is the one
    // property that makes "read league B while league A is active" safe:
    // by the time ANY caller observes this promise's result, the backend's
    // active-profile pointer is back to exactly what it was before this
    // aggregation began.
    if (originalActiveProfileId) {
      try {
        restoredBootstrap = await client.activateRedraftProfile(originalActiveProfileId);
      } catch (reason) {
        restoreError = reason instanceof Error
          ? reason.message
          : "The originally active league could not be restored.";
      }
    }
  }
  return { leagues, ownershipByProfile, restoredBootstrap, restoreError };
}

// Module-level serialization: every call that touches the backend's single
// shared active-profile pointer -- not just Attention Center's own sweep --
// is forced to run strictly after the previous such call has fully settled
// before starting. This began as an Attention-Center-only guard (only
// `runAttentionCenterAggregation` calls could never interleave with each
// other), but that left a real residual gap: a background sweep and an
// UNRELATED in-app league navigation (the header quick-switcher in
// shell-identity.tsx, the deep-link/bookmark activation gate in
// RedraftApp.tsx's `LeagueScopedPage`, Manage Leagues in leagues.tsx, and
// Profile's activate/create/duplicate actions in profile.tsx) each called
// `client.activateRedraftProfile` directly, entirely outside this queue.
// Concretely: if the owner opens Attention Center (which activates League
// A, reads it, activates League B, reads it, ... then restores whatever was
// active before the sweep started) and, WHILE that sweep is still mid-flight,
// follows a direct link/bookmark/header-switcher to a different league, that
// navigation's own `activateRedraftProfile` call and the sweep's next
// `activateRedraftProfile` call race against the SAME server-side pointer
// with no ordering guarantee -- the sweep could attribute one league's data
// to another, or its own unconditional `finally` restore could silently
// clobber the league the owner just navigated to back to whatever was
// active before Attention Center ran (confirmed by inspection: none of
// those 4 other call sites referenced `attentionCenterQueue` before this
// fix; each guards only against a second call from ITSELF, e.g.
// `switchRequestRef`/`inFlightFor`/`activationInFlight`, never against a
// concurrent call from a wholly different surface). `serializeActiveProfileCall`
// is the fix: the SAME queue, now used by every direct
// `activateRedraftProfile` call site in the app, so two calls from any
// combination of surfaces can never interleave against the shared pointer --
// each caller's own existing local guard still decides whether ITS response
// is still wanted once its turn comes up; this queue only decides ordering
// against the shared backend pointer itself. See attention-center.test.ts's
// dedicated no-interleave regression tests (both the original
// sweep-vs-sweep case and the new sweep-vs-unrelated-call case).
let activeProfileQueue: Promise<unknown> = Promise.resolve();

/** Queues `run` behind every other in-flight `activateRedraftProfile`-class
 * call (from ANY caller/surface) so the backend's single active-profile
 * pointer is never targeted by two overlapping requests. Swallows the
 * queued slot's own outcome (not `run`'s real result) so one failed/rejected
 * call never permanently jams the queue for the next caller. */
export function serializeActiveProfileCall<T>(run: () => Promise<T>): Promise<T> {
  const result = activeProfileQueue.then(run, run);
  activeProfileQueue = result.then(
    () => undefined,
    () => undefined,
  );
  return result;
}

export function runAttentionCenterAggregation(
  client: AttentionCenterClient,
  profiles: LeagueProfile[],
  originalActiveProfileId: string | null,
): Promise<AttentionCenterResult> {
  return serializeActiveProfileCall(() =>
    runAttentionCenterAggregationUnserialized(client, profiles, originalActiveProfileId),
  );
}
