import { NwrApiError, type NwrApiClient } from "@nwr/api-client";
import type { RedraftFreeAgentsResult, WeeklyProjectionProviderHealth } from "@nwr/contracts";
import { Button, StatusBadge, formatNumber, type TableColumn } from "@nwr/ui";
import { useEffect, useState, type DependencyList } from "react";

/**
 * Shared helpers for the NWR in-season UI pass (2026-09-10): Weekly Home,
 * Start/Sit, Waivers, Trade Analysis, Trade Finder (in ./in-season.tsx) AND
 * the Compare/K-DST-Streamer extensions inside ./pages.tsx. Lives in its
 * own module so neither of those two files needs to import the other.
 */

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
    let active = true;
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
        if (active) {
          setResult(value);
          setWorking(false);
        }
      })
      .catch((reason: unknown) => {
        if (active) {
          setError(reason instanceof NwrApiError ? reason : new NwrApiError("Request could not be read."));
          setWorking(false);
        }
      });
    return () => {
      active = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, attempt]);
  return { result, error, working, reload: () => setAttempt((value) => value + 1) };
}

export function useFreeAgents(client: NwrApiClient, profileId: string | null) {
  const loader = () => (profileId ? client.redraftFreeAgents() : null);
  // eslint-disable-next-line react-hooks/rules-of-hooks
  const { result, error, working } = useAsync<RedraftFreeAgentsResult>(loader, [client, profileId]);
  return { result, error, working };
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

// NWR UI expansion pass (2026-09-12, Improve Team surface): WAIVER and
// STREAMER now land inside the unified Improve Team workspace at the
// matching tab, instead of two separate single-purpose pages -- see
// `improve-team.tsx`. `LegacyRedirect` (RedraftApp.tsx) now preserves the
// query string through the compat redirect so `?tab=...` survives the
// `/waivers` -> `/league/:leagueKey/waivers` hop.
export const ACTION_CATEGORY_LINK: Record<string, string> = {
  START_SIT: "/lineup",
  START_SIT_CLOSE_CALL: "/lineup",
  WAIVER: "/waivers?tab=targets",
  TRADE: "/trade-finder",
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
