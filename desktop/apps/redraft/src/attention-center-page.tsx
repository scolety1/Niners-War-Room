import { NwrApiError, type NwrApiClient } from "@nwr/api-client";
import type { RedraftBootstrap } from "@nwr/contracts";
import {
  Button,
  DataTable,
  EmptyState,
  ErrorState,
  Icon,
  PageHeader,
  Panel,
  SearchInput,
  StatusBadge,
  type TableColumn,
} from "@nwr/ui";
import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

import { leagueFormat } from "./league-context";
import {
  runAttentionCenterAggregation,
  searchPlayerAcrossLeagues,
  type AttentionSeverity,
  type LeagueAttentionSummary,
  type LeagueOwnershipEntry,
  type PlayerSearchRow,
} from "./attention-center";

/**
 * P1-2 (2026-09-12): Multi-League Attention Center -- a READ-ONLY overview
 * layer answering "which of my leagues needs me?" across every saved
 * profile, built strictly on top of the existing single-league
 * architecture (see attention-center.ts for the full read-only/no-
 * state-leak design rationale). This page never renders as part of any
 * `/league/:leagueKey/*` scoped route -- it deliberately sits alongside
 * `/leagues` (the league chooser) as a global, non-league-scoped surface.
 */

const SEVERITY_TONE: Record<AttentionSeverity, "safe" | "review" | "blocked"> = {
  OK: "safe",
  UNKNOWN: "review",
  WATCH: "review",
  URGENT: "blocked",
};

const SEVERITY_LABEL: Record<AttentionSeverity, string> = {
  OK: "OK",
  UNKNOWN: "Unknown",
  WATCH: "Needs a look",
  URGENT: "Needs you now",
};

const SEVERITY_RANK: Record<AttentionSeverity, number> = { URGENT: 0, WATCH: 1, UNKNOWN: 2, OK: 3 };

const OWNERSHIP_LABEL: Record<PlayerSearchRow["status"], string> = {
  ROSTERED_BY_YOU: "Rostered by you",
  ROSTERED_BY_OPPONENT: "Rostered by an opponent",
  AVAILABLE: "Available",
  UNKNOWN: "Unavailable / unknown",
};

const OWNERSHIP_TONE: Record<PlayerSearchRow["status"], "safe" | "review" | "blocked"> = {
  ROSTERED_BY_YOU: "safe",
  ROSTERED_BY_OPPONENT: "blocked",
  AVAILABLE: "safe",
  UNKNOWN: "review",
};

const LEAGUE_COLUMNS: TableColumn[] = [
  {
    key: "leagueName", label: "League", sort: "text",
    render: (row) => <span><strong>{String(row.leagueName)}</strong></span>,
  },
  {
    key: "severity", label: "Status", sort: "text",
    render: (row) => {
      const severity = row.severity as AttentionSeverity;
      return <StatusBadge tone={SEVERITY_TONE[severity]} label={SEVERITY_LABEL[severity]} />;
    },
  },
  {
    key: "flagSummary", label: "Why", render: (row) => {
      const flags = row.flags as LeagueAttentionSummary["flags"];
      if (!flags.length) return <span className="copy-muted">No open issues.</span>;
      return <ul className="attention-center__flag-list">{flags.map((flag, index) => (
        <li key={`${flag.kind}-${index}`} title={flag.detail ?? undefined}>{flag.summary}</li>
      ))}</ul>;
    },
  },
  { key: "currentWeek", label: "Week", align: "right", render: (row) => row.currentWeek == null ? "—" : String(row.currentWeek) },
  { key: "record", label: "Record", render: (row) => String(row.record ?? "Unavailable") },
  { key: "standingsRank", label: "Rank", render: (row) => String(row.standingsRank ?? "—") },
  { key: "deadlineText", label: "Deadline", render: (row) => String(row.deadlineText ?? "—") },
];

const SEARCH_COLUMNS: TableColumn[] = [
  { key: "leagueName", label: "League", sort: "text" },
  {
    key: "status", label: "Status", sort: "text",
    render: (row) => {
      const status = row.status as PlayerSearchRow["status"];
      return <StatusBadge tone={OWNERSHIP_TONE[status]} label={OWNERSHIP_LABEL[status]} />;
    },
  },
  { key: "teamName", label: "Team", render: (row) => String(row.teamName ?? "—") },
  { key: "matchedName", label: "Matched player", render: (row) => String(row.matchedName ?? "—") },
];

export function AttentionCenterPage({
  client,
  data,
  onUpdate,
}: {
  client: NwrApiClient;
  data: RedraftBootstrap;
  onUpdate: (data: RedraftBootstrap) => void;
}) {
  const navigate = useNavigate();
  const [leagues, setLeagues] = useState<LeagueAttentionSummary[] | null>(null);
  const [ownershipByProfile, setOwnershipByProfile] = useState<Record<string, LeagueOwnershipEntry[]>>({});
  const [error, setError] = useState<string | null>(null);
  const [working, setWorking] = useState(false);
  const [elapsedMs, setElapsedMs] = useState<number | null>(null);
  const [query, setQuery] = useState("");
  // Component-level in-flight guard (belt): ignore a re-trigger while a run
  // is already active, and only ever apply the result of the MOST RECENT
  // trigger to this component's own state (a stale run superseded by a
  // newer one still runs to completion -- see attention-center.ts's own
  // module-level serialization queue, the suspenders -- but its result is
  // simply discarded here rather than clobbering a newer, already-applied
  // view).
  const generation = useRef(0);
  const inFlight = useRef(false);
  const profiles = data.profiles;
  const originalActiveProfileId = data.activeProfileId;

  const run = useCallback(() => {
    if (inFlight.current) return;
    inFlight.current = true;
    const myGeneration = ++generation.current;
    setWorking(true);
    setError(null);
    const startedAt = typeof performance !== "undefined" ? performance.now() : Date.now();
    void runAttentionCenterAggregation(client, profiles, originalActiveProfileId)
      .then((result) => {
        if (generation.current !== myGeneration) return;
        setLeagues(result.leagues);
        setOwnershipByProfile(result.ownershipByProfile);
        const finishedAt = typeof performance !== "undefined" ? performance.now() : Date.now();
        setElapsedMs(finishedAt - startedAt);
        if (result.restoreError) {
          setError(
            `Every league's status was read, but the league you started on could not be reactivated: ${result.restoreError}. Reopen it from the league chooser to be safe.`,
          );
        } else if (result.restoredBootstrap) {
          // The ONE point this page ever calls `onUpdate` -- with the
          // CONFIRMED-restored bootstrap for the SAME league that was
          // active before this run started, never an intermediate league
          // observed mid-loop. Keeps the app-wide `data` state (and every
          // other open surface reading it) exactly consistent with what
          // was active before the owner opened this page.
          onUpdate(result.restoredBootstrap);
        }
      })
      .catch((reason: unknown) => {
        if (generation.current !== myGeneration) return;
        setError(reason instanceof NwrApiError ? reason.message : "Leagues could not be summarized.");
      })
      .finally(() => {
        if (generation.current === myGeneration) setWorking(false);
        inFlight.current = false;
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [client, profiles, originalActiveProfileId]);

  useEffect(() => {
    run();
    // Intentionally run once on mount only -- re-running automatically
    // whenever `data` changes (e.g. from an unrelated page's own `onUpdate`)
    // would re-trigger a full multi-league sweep far more often than the
    // owner asked for; use the Refresh button instead.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const searchResults = leagues && query.trim() ? searchPlayerAcrossLeagues(leagues, ownershipByProfile, query) : [];
  const sortedLeagues = leagues
    ? [...leagues].sort((a, b) => SEVERITY_RANK[a.severity] - SEVERITY_RANK[b.severity])
    : [];
  const urgentCount = leagues?.filter((league) => league.severity === "URGENT").length ?? 0;
  const watchCount = leagues?.filter((league) => league.severity === "WATCH").length ?? 0;

  if (!profiles.length) {
    return (
      <EmptyState
        icon="trophy"
        title="No leagues yet"
        message="Create a local league from a validated preset, or import your Sleeper league, before checking a multi-league overview."
        action={<Button icon="profile" onClick={() => navigate("/leagues")}>Set up a league</Button>}
      />
    );
  }

  return (
    <div className="attention-center">
      <PageHeader
        eyebrow="Multi-league overview · read-only"
        title="Attention Center"
        description="Every saved league, summarized from cheap already-available status reads (Data Health, league sync, standings) -- never a full Start/Sit or Waiver run per league."
        actions={<Button disabled={working} icon="activity" onClick={run} variant="secondary">{working ? "Checking leagues…" : "Refresh"}</Button>}
        status={leagues ? <span className="copy-muted">{urgentCount} need you now · {watchCount} worth a look{elapsedMs != null ? ` · ${(elapsedMs / 1000).toFixed(1)}s` : ""}</span> : null}
      />
      {error ? <ErrorState message={error} onRetry={run} /> : null}
      {!leagues && working ? <p className="copy-muted" aria-live="polite">Checking every league's status…</p> : null}
      {leagues ? (
        <Panel title="Leagues" eyebrow={`${leagues.length} saved league${leagues.length === 1 ? "" : "s"}`}>
          <DataTable
            columns={LEAGUE_COLUMNS}
            rows={sortedLeagues as unknown as Array<Record<string, unknown>>}
            rowKey={(row) => String(row.profileId)}
            onRowClick={(row) => navigate(`/league/${encodeURIComponent(String(row.profileId))}/home`)}
            emptyMessage="No leagues to summarize."
          />
        </Panel>
      ) : null}
      <Panel title="Player search across leagues" eyebrow="Cross-league ownership/availability">
        <SearchInput placeholder="Search a player name…" value={query} onChange={setQuery} />
        {query.trim() ? (
          <DataTable
            columns={SEARCH_COLUMNS}
            rows={searchResults as unknown as Array<Record<string, unknown>>}
            rowKey={(row) => String(row.profileId)}
            emptyMessage="No leagues to search yet."
          />
        ) : (
          <p className="copy-muted"><Icon name="search" size={14} /> Enter a player name to see who owns them in each of your leagues.</p>
        )}
      </Panel>
    </div>
  );
}
