import { NwrApiError, type NwrApiClient } from "@nwr/api-client";
import type { DecisionTraceHistoryEvent, RedraftBootstrap } from "@nwr/contracts";
import {
  Button,
  DataTable,
  EmptyState,
  ErrorState,
  PageHeader,
  Panel,
  StatusBadge,
  type TableColumn,
} from "@nwr/ui";

import { useAsync } from "./weekly-shared";
import {
  formatDecisionType,
  formatGeneratedAt,
  formatOutcome,
  formatOwnerAction,
  statusLabel,
  statusTone,
  summarizeRecommendation,
} from "./decision-history-format";

/**
 * P1-4 (2026-09-12, Prospective Recommendation Ledger): the owner-facing
 * "What did NWR tell me?" History/Review surface -- built on TOP of the
 * existing append-only in-season decision-trace ledger
 * (in_season_decision_trace_service.py), never a second, parallel trace
 * system.
 *
 * Deliberately simple, per the governing directive: a real, honest list of
 * every recommendation this app has actually recorded for the CURRENTLY
 * active league (never cross-league -- the backend ledger is one file per
 * profile, and `redraftDecisionTraceHistory()` always resolves the active
 * profile itself; this page also renders inside `LeagueScopedPage`, which
 * keys the whole subtree by `leagueKey` so no per-page state survives a
 * league switch either). No calibration/accuracy metric is computed or
 * displayed anywhere on this page -- there is no real 2026-season outcome
 * data behind anything recorded so far, and inventing one would be
 * dishonest. "Owner action" / "Outcome" columns show the real recorded
 * value when present, and a plain, honest "Not recorded" / "No outcome
 * recorded yet" otherwise -- this app has no capture control for either
 * yet (see the facade's own `redraft_record_decision_trace_owner_action` /
 * `..._outcome` methods, real and callable, just not wired to any button
 * today).
 */

const COLUMNS: TableColumn[] = [
  {
    key: "generatedAt", label: "Date", sort: "text",
    render: (row) => <span>{formatGeneratedAt(String(row.generatedAt))}</span>,
  },
  {
    key: "decisionType", label: "Decision", sort: "text",
    render: (row) => <span>{formatDecisionType(String(row.decisionType))}</span>,
  },
  { key: "week", label: "Week", align: "right", render: (row) => (row.week == null ? "—" : String(row.week)) },
  {
    key: "recommendation", label: "Recommendation",
    render: (row) => <span>{summarizeRecommendation(row as unknown as DecisionTraceHistoryEvent)}</span>,
  },
  {
    key: "ownerAction", label: "Owner action",
    render: (row) => <span>{formatOwnerAction(row as unknown as DecisionTraceHistoryEvent)}</span>,
  },
  {
    key: "status", label: "Outcome status",
    render: (row) => (
      <div className="decision-history__status-cell">
        <StatusBadge tone={statusTone(String(row.status))} label={statusLabel(String(row.status))} />
        <span className="copy-muted">{formatOutcome(row as unknown as DecisionTraceHistoryEvent)}</span>
      </div>
    ),
  },
];

export function DecisionHistoryPage({ client, data }: { client: NwrApiClient; data: RedraftBootstrap }) {
  const loader = () => client.redraftDecisionTraceHistory();
  const { result, error, working, reload } = useAsync(loader, [client, data.activeProfileId]);

  return (
    <>
      <PageHeader
        eyebrow="League · Prospective recommendation ledger"
        title="History"
        description="What NWR has actually told you for this league, starting from when this ledger began recording -- not a retroactive reconstruction of earlier seasons. Owner action and outcome are appended separately, later, and only shown when a real one has actually been recorded."
        actions={<Button disabled={working} icon="activity" onClick={reload} variant="secondary">{working ? "Reading…" : "Refresh"}</Button>}
        status={result ? <span className="copy-muted">{result.totalCount} recorded event{result.totalCount === 1 ? "" : "s"}</span> : null}
      />
      {error ? <ErrorState message={error instanceof NwrApiError ? error.message : "History could not be read."} onRetry={reload} /> : null}
      {!result && working ? <p className="copy-muted" aria-live="polite">Reading the decision-trace ledger…</p> : null}
      {result ? (
        result.totalCount === 0 ? (
          <EmptyState
            icon="board"
            title="Nothing recorded yet"
            message="No recommendation has been recorded for this league yet. Every real Start/Sit, Waiver, FAAB, Trade, Streamer, or Trade Finder/Package Search suggestion NWR gives you from now on will show up here."
          />
        ) : (
          <Panel title="Recorded recommendations" eyebrow={`${data.activeProfile?.leagueName ?? result.leagueName}`}>
            <DataTable
              columns={COLUMNS}
              rows={result.events as unknown as Array<Record<string, unknown>>}
              rowKey={(row) => String(row.traceId)}
              emptyMessage="No recommendation has been recorded for this league yet."
            />
          </Panel>
        )
      ) : null}
      <p className="copy-muted decision-history__disclosure">
        No calibration, accuracy, or "was NWR right" metric is shown here -- real season outcomes don't yet exist for
        anything recorded so far, and this page never invents one.
      </p>
    </>
  );
}
