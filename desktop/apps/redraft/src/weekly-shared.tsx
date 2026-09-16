import { NwrApiError, type NwrApiClient } from "@nwr/api-client";
import type {
  LeagueWorkspaceContext,
  RedraftFreeAgentsResult,
  WeeklyProjectionProviderHealth,
} from "@nwr/contracts";
import { Button, StatusBadge, formatNumber, type TableColumn } from "@nwr/ui";
import { useEffect, useState, type DependencyList } from "react";

/**
 * Shared helpers for the NWR in-season UI pass (2026-09-10): Weekly Home,
 * Start/Sit, Waivers, Trade Analysis, Trade Finder (in ./in-season.tsx) AND
 * the Compare/K-DST-Streamer extensions inside ./pages.tsx. Lives in its
 * own module so neither of those two files needs to import the other.
 */

/**
 * Active-profile / stale-response adversary guard (History UI V2 pass,
 * Work Unit 15 -- targets the exact "real league-switch race condition"
 * bug class the governing directive names: a delayed/out-of-order async
 * response applied to the wrong, no-longer-active profile/league).
 *
 * `useAsync` below already protects against this using React's own effect
 * cleanup: every render's effect closes over its OWN guard, and the
 * cleanup (`return () => guard.supersede()`) fires BEFORE the next
 * render's effect runs whenever `deps` changes (e.g. `profileId`
 * switches) -- so a promise that resolves after that point is a known,
 * detectable, discarded straggler, never applied. Pulled out into this
 * small, pure, directly-testable primitive (rather than only living
 * inline inside the `useEffect` closure) specifically so the invariant
 * can be proven by a real, adversarial-ordering test
 * (`weekly-shared.test.ts`) without needing a DOM/React render harness --
 * this repo has no jsdom/@testing-library/react installed, and this pass
 * deliberately did not add either as a new dependency for one test. This
 * is a pure refactor -- the guarded behavior is byte-identical to before
 * (a closure boolean renamed/wrapped, nothing else).
 */
export function createStaleResponseGuard(): { isStale: () => boolean; supersede: () => void } {
  let active = true;
  return {
    isStale: () => !active,
    supersede: () => {
      active = false;
    },
  };
}

// ---------------------------------------------------------------------------
// Generic "fetch on dependency change" hook -- the same shape every existing
// page in this app already hand-rolls (see the old useFreeAgents below, or
// OpponentRostersPage), just reusable instead of copy-pasted per page.
// ---------------------------------------------------------------------------
export function useAsync<T>(
  loader: () => Promise<T> | null,
  deps: DependencyList,
): { result: T | null; error: NwrApiError | null; working: boolean; reload: () => void } {
  const [result, setResult] = useState<T | null>(null);
  const [error, setError] = useState<NwrApiError | null>(null);
  const [working, setWorking] = useState(false);
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    const guard = createStaleResponseGuard();
    const promise = loader();
    if (!promise) {
      setResult(null);
      setError(null);
      setWorking(false);
      return undefined;
    }
    setWorking(true);
    setError(null);
    promise
      .then((value) => {
        if (!guard.isStale()) {
          setResult(value);
          setWorking(false);
        }
      })
      .catch((reason: unknown) => {
        if (!guard.isStale()) {
          setError(reason instanceof NwrApiError ? reason : new NwrApiError("Request could not be read."));
          setWorking(false);
        }
      });
    return () => {
      guard.supersede();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, attempt]);
  return { result, error, working, reload: () => setAttempt((value) => value + 1) };
}

/**
 * Week-display race fix (2026-09-16, shared upgrade B), same bug class and
 * same structural remedy as the FAAB LIVE/SCENARIO fix
 * (`resolveFaabDisplay` in improve-team-explain.ts): a week-scoped page's
 * `WeekControl` updates local input state (`requestedWeek`) synchronously,
 * but the matching `useAsync` response -- whose OWN `week` field is the
 * only honest record of what week the currently-rendered data actually is
 * -- only lands after a real round trip. Weekly Home and Start/Sit both
 * previously put the raw input week straight into the page title/"Week"
 * chip while the body below (still the PREVIOUS response) kept rendering
 * that prior week's actions/lineup -- reproducible live by changing the
 * week: the title advances immediately, but `ProviderStatusLine` (which
 * already correctly reads its own week off the resolved
 * `WeeklyProjectionProviderHealth.week`) kept showing the OLD week for as
 * long as the new fetch was in flight, so the SAME page could show two
 * different week numbers to the owner at once.
 *
 * `resolveWeekDisplay`'s only inputs are the requested week and the
 * resolved response's own week -- it has no branch that can silently
 * relabel one response's data with a different response's week. `Display`
 * is what every week-labeled chip/title on the page should render;
 * `isStale` is true only when a resolved response exists but is for a
 * different week than what is currently requested (a structural check
 * against the response itself, not a timing/`working`-flag guess), and
 * should drive an explicit "Updating…" indicator rather than silently
 * leaving stale data unmarked.
 */
export function resolveWeekDisplay(
  requestedWeek: number,
  resolvedWeek: number | null | undefined,
): { displayWeek: number; isStale: boolean } {
  if (resolvedWeek == null) return { displayWeek: requestedWeek, isStale: false };
  return { displayWeek: resolvedWeek, isStale: resolvedWeek !== requestedWeek };
}

/**
 * Full Cycle V1, Worker 4 (Section 3C, data-age/basis labeling): NWR's
 * season-level values (Proj pts / Value over replacement / REST OF SEASON
 * marginal utility -- everything `generate_rankings()` produces, consumed
 * unchanged by Rankings, Cheat Sheet, Compare, Waivers/Add-Drop/FAAB, and
 * Trades) all come from ONE governed projection snapshot, admitted once
 * (`data.status.sourceAsOf`, already computed server-side and already shown
 * on the Data Health page) and refreshed only through a new owner-approved
 * governance admission -- never automatically reduced week to week as the
 * real season progresses and games are actually played. Traced directly:
 * `redraft_engine_v1_service.py::score_projection` sums a full stat line
 * (`receptions`, `receiving_yards`, etc.) built from a `games` figure
 * projected for the WHOLE season (see `redraft_2026_projection_model_
 * service.py`'s per-game-rate * games construction) -- the value is a full
 * 2026 SEASON total, not a games-remaining-adjusted figure, and no call
 * site in this codebase recomputes or decays it in-season. This is
 * internally CONSISTENT (every consumer reads the exact same computed
 * value, never a second independently-derived "remaining season" number),
 * but the plain `sourceAsOf` date alone doesn't say so -- this caption
 * states the actual basis so the owner isn't left to assume a `REST_OF_
 * SEASON`-labeled number has already been discounted for weeks played.
 * Weekly per-week numbers (`weeklyProjectedPoints`, Start/Sit, Weekly Home)
 * are a genuinely separate, live, week-scoped source and are NOT described
 * by this caption -- see `ProviderStatusLine`/`resolveWeekDisplay` for that
 * one's own honesty captions.
 */
export function resolveSeasonProjectionBasisCaption(
  sourceAsOf: string | null | undefined,
): string {
  return sourceAsOf
    ? `Season-level values (projected points, value over replacement, REST OF SEASON marginal utility) reflect NWR's full 2026 season model, admitted ${sourceAsOf} -- not reduced for games already played this season. Separate from any single week's live projection.`
    : "Season-level values reflect NWR's governed season model; admission date unavailable.";
}

/**
 * Weekly Home's "NWR Actions" list (`WeeklyHomeAction`) mixes categories
 * with genuinely DIFFERENT provenance bases: START_SIT / START_SIT_CLOSE_
 * CALL come from the real live weekly lineup optimizer (`weekly`
 * `providerHealth`'s own freshness note is the correct, honest label for
 * those), but WAIVER and TRADE cards are built from `redraft_waivers(mode=
 * "REST_OF_SEASON")` / `redraft_trade_finder()` -- both driven by the SAME
 * season-level governed ranking `resolveSeasonProjectionBasisCaption`
 * describes above, not by the weekly provider at all. Before this fix,
 * every action card on this page (regardless of category) was labeled with
 * the SAME weekly `providerHealth`-derived freshness note, which put a
 * "Sleeper · updated <time-today>" label on a WAIVER/TRADE recommendation
 * that is actually driven by the season snapshot (admitted `sourceAsOf`,
 * potentially days/weeks old) -- a real, reproducible display-basis
 * mismatch, not a computed-value bug (the underlying WAIVER/TRADE
 * recommendation values themselves were never wrong, only their freshness
 * caption was borrowed from an unrelated data source).
 */
export function resolveHomeActionFreshness(
  category: "START_SIT" | "START_SIT_CLOSE_CALL" | "WAIVER" | "TRADE" | "STREAMER",
  weeklyFreshnessNote: string | null,
  seasonSourceAsOf: string | null | undefined,
): string | null {
  if (category === "WAIVER" || category === "TRADE") {
    return seasonSourceAsOf
      ? `NWR season ranking · admitted ${seasonSourceAsOf}`
      : weeklyFreshnessNote;
  }
  return weeklyFreshnessNote;
}

/**
 * NWR Full Cycle V1 (Worker 7): Waivers' `unmatchedRosterSleeperPlayerIds`
 * previously rendered as a bare, unexplained list of raw Sleeper ids (e.g.
 * "Unresolved roster Sleeper IDs: 3451, NE") -- confirmed live on a real
 * league's real roster. Investigated: both entries were a real, catalog-
 * known K and DST whose position simply has zero rows in NWR's governed
 * ranking BY DESIGN (see docs/codex/waiver_night_v1/LEDGER.md), not a
 * genuine identity-resolution failure -- but the raw-id list gave no way to
 * tell that apart from a real bug. This renders the backend's now-computed
 * `unmatchedRosterSleeperPlayers` (label + reason per id) when present, and
 * honestly falls back to the raw id list (never fabricating a reason) for
 * any older/cached response shape that lacks it.
 */
export function describeUnmatchedRosterPlayers(
  ids: string[],
  players?: Array<{ sleeperId: string; label: string; reason: string; category: string }> | null,
): string[] {
  if (!ids.length) return [];
  if (players && players.length) {
    return players.map((player) => `${player.label} -- ${player.reason}`);
  }
  return ids.map((id) => `Sleeper id ${id} -- reason unavailable`);
}

export function useFreeAgents(client: NwrApiClient, profileId: string | null) {
  const loader = () => (profileId ? client.redraftFreeAgents() : null);
  // eslint-disable-next-line react-hooks/rules-of-hooks
  const { result, error, working } = useAsync<RedraftFreeAgentsResult>(loader, [client, profileId]);
  return { result, error, working };
}

/**
 * P1-1 (2026-09-12): the read-only `LeagueWorkspaceContext` fetch, shared
 * so every in-season surface that needs the provider-known current
 * week/matchup/standings/playoff context (currently Weekly Home) reads it
 * the same way instead of hand-rolling a second fetch. Re-fetches
 * whenever `profileId` changes -- switching leagues never carries a
 * previous league's context forward.
 */
export function useLeagueWorkspaceContext(client: NwrApiClient, profileId: string | null) {
  const loader = () => (profileId ? client.redraftLeagueWorkspaceContext() : null);
  // eslint-disable-next-line react-hooks/rules-of-hooks
  return useAsync<LeagueWorkspaceContext>(loader, [client, profileId]);
}

export const FREE_AGENT_COLUMNS: TableColumn[] = [
  { key: "playerName", label: "Player", sort: "text", render: (row) => <span className="player-cell"><strong>{String(row.playerName)}</strong><small>{String(row.team)} · {String(row.position)}</small></span> },
  { key: "overallRank", label: "NWR rank", sort: "number", align: "right", render: (row) => row.overallRank == null ? "Unranked" : `#${String(row.overallRank)}` },
  { key: "positionRank", label: "Pos rank", sort: "number", render: (row) => row.positionRank == null ? "—" : `${String(row.position)}${String(row.positionRank)}` },
  { key: "projectedPoints", label: "Season points", sort: "number", align: "right", render: (row) => row.projectedPoints == null ? "—" : formatNumber(Number(row.projectedPoints), 1) },
  { key: "replacementAdjustedValue", label: "Replacement value", sort: "number", align: "right", render: (row) => row.replacementAdjustedValue == null ? "—" : formatNumber(Number(row.replacementAdjustedValue), 1) },
  { key: "rosterStatus", label: "Sleeper status", sort: "text", render: () => <StatusBadge tone="safe" label="Available" /> },
];

/**
 * NWR pre-UI architecture CLOSURE pass (directive section 1): one shared
 * "append a global Player Detail 'View' trigger" column-builder, reused by
 * every table-based surface adopting the primitive this pass (Free Agents,
 * Opponent Rosters, Players/Rankings) instead of each hand-rolling its own
 * View column. `row` is the table's own already-rendered row object (its
 * real identity fields are already on it -- no extra fetch).
 */
export function appendPlayerDetailColumn(
  columns: TableColumn[],
  onView: (row: Record<string, unknown>) => void,
): TableColumn[] {
  return [
    ...columns,
    {
      key: "playerDetail",
      label: "",
      render: (row) => <Button variant="ghost" onClick={() => onView(row)}>View</Button>,
    },
  ];
}

export function formatClock(iso: string | null | undefined): string {
  if (!iso) return "unavailable";
  const parsed = new Date(iso);
  if (Number.isNaN(parsed.getTime())) return iso;
  return parsed.toLocaleString(undefined, { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" });
}

export function WeekControl({ week, onChange, label = "NFL week" }: { week: number; onChange: (week: number) => void; label?: string }) {
  return (
    <label className="form-field">
      <span>{label}</span>
      <input
        min={1}
        max={18}
        type="number"
        value={week}
        onChange={(event) => {
          const next = Number(event.target.value);
          if (Number.isFinite(next)) onChange(Math.min(18, Math.max(1, Math.round(next))));
        }}
      />
    </label>
  );
}

/** Compact "Weekly projections: Sleeper · Week 1 · updated <time>" line with
 * an expandable honest detail panel (directive section 3): provider,
 * integration status, source endpoint, last successful refresh, coverage,
 * freshness, and any real issues recorded by the fail-safe layer. Never
 * hides that the underlying dependency is experimental/external. */
export function ProviderStatusLine({ health }: { health: WeeklyProjectionProviderHealth | null | undefined }) {
  const [expanded, setExpanded] = useState(false);
  if (!health) {
    return <p className="copy-muted provider-status-line provider-status-line--unavailable">Weekly projections unavailable.</p>;
  }
  const tone = health.freshness === "STALE" ? "review" : health.status === "OK" ? "safe" : "blocked";
  return (
    <div className="provider-status-line">
      <button type="button" className="provider-status-line__toggle" onClick={() => setExpanded((value) => !value)} aria-expanded={expanded}>
        <StatusBadge tone={tone} label={health.freshness === "STALE" ? "STALE" : "LIVE"} />
        <span>Weekly projections: {health.provider} · Week {health.week} · updated {formatClock(health.retrievedAt)}{health.servedFromCache ? " (cached)" : ""}</span>
        <span aria-hidden="true">{expanded ? "▴" : "▾"}</span>
      </button>
      {expanded ? (
        <dl className="health-list provider-status-line__detail">
          <div><dt>Provider</dt><dd>{health.provider}</dd></div>
          <div><dt>Integration status</dt><dd>{health.integrationStatus === "EXPERIMENTAL_EXTERNAL" ? "Experimental / external — undocumented endpoint, no API-stability guarantee" : health.integrationStatus}</dd></div>
          <div><dt>Source endpoint</dt><dd>{health.sourceEndpoint}</dd></div>
          <div><dt>Last successful refresh</dt><dd>{formatClock(health.retrievedAt)}</dd></div>
          <div><dt>Coverage</dt><dd>{formatNumber(health.totalRows)} players · {formatNumber(health.nonzeroProjectionRows)} nonzero projections</dd></div>
          <div><dt>Freshness</dt><dd>{health.freshness}{health.freshness === "STALE" ? " — live fetch failed; showing the last known-good snapshot" : ""}</dd></div>
          {health.issues.length ? <div><dt>Issues</dt><dd>{health.issues.join("; ")}</dd></div> : null}
        </dl>
      ) : null}
    </div>
  );
}

export function RefreshProjectionsButton({ onRefresh, working }: { onRefresh: () => void; working: boolean }) {
  return <Button icon="activity" variant="secondary" onClick={onRefresh} disabled={working}>{working ? "Refreshing…" : "Refresh weekly projections"}</Button>;
}

export const ACTION_CATEGORY_LABEL: Record<string, string> = {
  START_SIT: "Start/Sit",
  START_SIT_CLOSE_CALL: "Start/Sit — close call",
  WAIVER: "Waiver",
  TRADE: "Trade opportunity",
  STREAMER: "Streamer",
};

// NWR UI expansion pass (2026-09-12, Improve Team + Trades surfaces):
// WAIVER/STREAMER land inside the unified Improve Team workspace and
// TRADE lands inside the unified Trades workspace (FIND TRADES tab),
// instead of separate single-purpose pages -- see `improve-team.tsx` /
// `trades.tsx`. `LegacyRedirect` (RedraftApp.tsx) preserves the query
// string through the compat redirect so `?tab=...` survives the
// `/waivers` -> `/league/:leagueKey/waivers` (and `/trade-analysis` ->
// `/league/:leagueKey/trade-analysis`) hop.
export const ACTION_CATEGORY_LINK: Record<string, string> = {
  START_SIT: "/lineup",
  START_SIT_CLOSE_CALL: "/lineup",
  WAIVER: "/waivers?tab=targets",
  TRADE: "/trade-analysis?tab=find",
  STREAMER: "/waivers?tab=streamers",
};

/** Heuristic status/risk tone -- disclosed as a heuristic, not a validated
 * severity model. OK/AVAILABLE reads safe; OUT/IR/SUSPENDED reads blocked;
 * everything uncertain (questionable, doubtful, unprojected, unknown, an
 * empty slot) reads review. */
export function statusTone(status: string | null | undefined): "safe" | "review" | "blocked" {
  const upper = (status ?? "").toUpperCase();
  if (!upper || upper === "EMPTY" || upper === "UNPROJECTED" || upper.includes("QUESTIONABLE") || upper.includes("DOUBTFUL") || upper.includes("UNKNOWN")) return "review";
  if (upper.includes("OUT") || upper.includes("IR") || upper.includes("SUSPEND")) return "blocked";
  return "safe";
}

export const FAAB_URGENCY_TONE: Record<string, "safe" | "review" | "blocked"> = {
  HIGH: "blocked",
  MEDIUM: "review",
  LOW: "safe",
};
