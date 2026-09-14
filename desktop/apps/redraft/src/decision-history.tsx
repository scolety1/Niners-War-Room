import { useState } from "react";

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
  buildOutcomeDetailSections,
  formatDecisionType,
  formatGeneratedAt,
  formatOutcome,
  formatOwnerAction,
  hasOutcomeDetail,
  ownerActionOptionsForDecisionType,
  statusLabel,
  statusTone,
  summarizeRecommendation,
} from "./decision-history-format";

/**
 * NWR Post-Closure Fixes V1 (Worker F): the owner-action capture control
 * for one History row. Wires directly to the already-built, already-
 * tested `record_owner_action` append-only backend write
 * (`client.redraftRecordDecisionTraceOwnerAction`) -- this component adds
 * no new backend logic, only a button.
 *
 * TASTE DECISIONS FLAGGED FOR THE OWNER:
 * 1. After a successful record, this calls the page's `reload()` (a full
 *    re-fetch of the history list) rather than optimistically patching
 *    just this one row in local state. Simpler and guaranteed-consistent
 *    with the real append-only ledger (what you see immediately after
 *    clicking is byte-for-byte what a fresh page load would show), at the
 *    cost of every row's cells re-rendering for a moment. With a few
 *    hundred events at most this is not a real performance concern; a
 *    much larger ledger might want per-row optimistic patching instead.
 * 2. "Change" is always offered once an action is recorded -- there is no
 *    hard lock-out. The backend is genuinely append-only (recording again
 *    writes a NEW ledger line, the original recommendation and the first
 *    owner-action line are never touched), so allowing a correction is
 *    honest, not a mutation of history. But this does mean an owner can
 *    record contradictory actions over time for the same recommendation;
 *    only the LATEST one displays, per the backend's own fold-to-latest
 *    read semantics.
 */
function OwnerActionCell({
  client,
  event,
  onRecorded,
}: {
  client: NwrApiClient;
  event: DecisionTraceHistoryEvent;
  onRecorded: () => void;
}) {
  const [editing, setEditing] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const options = ownerActionOptionsForDecisionType(event.decisionType);

  const record = async (action: string) => {
    setSubmitting(true);
    setError(null);
    try {
      await client.redraftRecordDecisionTraceOwnerAction(event.traceId, action);
      setEditing(false);
      onRecorded();
    } catch (reason) {
      setError(reason instanceof NwrApiError ? reason.message : "Could not record this action.");
      setSubmitting(false);
    }
  };

  if (event.ownerAction && !editing) {
    return (
      <div className="decision-history__owner-action">
        <span>{formatOwnerAction(event)}</span>
        <Button className="decision-history__owner-action-change" onClick={() => setEditing(true)} variant="ghost">
          Change
        </Button>
        {error ? <small className="copy-muted">{error}</small> : null}
      </div>
    );
  }

  return (
    <div className="decision-history__owner-action decision-history__owner-action--options">
      {options.map((option) => (
        <Button disabled={submitting} key={option} onClick={() => record(option)} variant="secondary">
          {option}
        </Button>
      ))}
      {event.ownerAction ? (
        <Button disabled={submitting} onClick={() => setEditing(false)} variant="ghost">
          Cancel
        </Button>
      ) : null}
      {submitting ? <small className="copy-muted" role="status">Recording…</small> : null}
      {error ? <small className="copy-muted">{error}</small> : null}
    </div>
  );
}

/**
 * History UI V2 (NWR Live Player Intelligence V1, Worker 6): the
 * expandable, per-decision-type "progressive detail" for one row's REAL
 * recorded outcome -- only rendered at all when `hasOutcomeDetail` is true
 * (the common case, this early in the season, is no detail at all, so
 * nothing extra renders). Uses a plain native `<details>` per row rather
 * than a new shared UI-kit disclosure component or a DataTable behavior
 * change -- keeps this additive to ONE page, and every row expands
 * independently (no shared "selected row" state to get stale on refetch).
 */
function OutcomeDetail({ event }: { event: DecisionTraceHistoryEvent }) {
  if (!hasOutcomeDetail(event)) return null;
  const sections = buildOutcomeDetailSections(event);
  if (!sections.length) return null;
  return (
    <details className="decision-history__detail">
      <summary>View outcome detail</summary>
      {sections.map((section) => (
        <div className="decision-history__detail-section" key={section.heading}>
          <h4>{section.heading}</h4>
          <dl>
            {section.rows.map((row) => (
              <div className="decision-history__detail-row" key={row.label}>
                <dt>{row.label}</dt>
                <dd>{row.value}</dd>
              </div>
            ))}
          </dl>
        </div>
      ))}
    </details>
  );
}

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
 * recorded yet" otherwise.
 *
 * NWR Post-Closure Fixes V1 (Worker F, 2026-09-13): the "Owner action"
 * column now has a real capture control (see `OwnerActionCell` above),
 * wired to the already-built `record_owner_action` backend write. The
 * "Outcome status" column deliberately still has NO capture control --
 * per the governing directive, a real "what happened" capture would need
 * real, observed 2026-season outcome data (a completed matchup, a
 * processed waiver claim, an accepted/rejected trade) that genuinely
 * does not exist yet for anything recorded so far; forcing a UI for it
 * now would mean inventing what it should look like rather than building
 * it from a real need. The existing plain "No outcome recorded yet" text
 * already says this honestly -- left as-is rather than adding a
 * "Coming soon" badge on top of an already-honest message.
 *
 * History UI V2 (Worker 6): a real "League" column is deliberately NOT
 * added here -- this page is already single-league-scoped (see the
 * cross-league note above), so `Panel`'s `eyebrow` prop (below) already
 * shows the active league's name exactly once, at the top, rather than
 * repeating the same value on every row. The "Detail" affordance
 * (`OutcomeDetail`, above) is the progressive/secondary layer for each
 * decision type's REAL schema (`lineupOpportunityCost` and eligible
 * alternatives for START_SIT, the separate player-decision-quality/
 * bid-range-calibration axes for FAAB, an accepted-only realized-roster-
 * outcome for TRADE, etc.) -- it renders nothing at all until a real
 * `outcome.detail` payload exists for that row. Still, per the governing
 * directive, **no aggregate "NWR ACCURACY: X%" score is computed or shown
 * anywhere on this page** -- see `hasSufficientSampleForRollup` in
 * decision-history-format.ts for the conservative, disclosed, unused bar a
 * future pass would need to clear before adding one.
 */

function buildColumns(client: NwrApiClient, onRecorded: () => void): TableColumn[] {
  return [
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
      render: (row) => (
        <OwnerActionCell
          client={client}
          event={row as unknown as DecisionTraceHistoryEvent}
          onRecorded={onRecorded}
        />
      ),
    },
    {
      key: "status", label: "Outcome status",
      render: (row) => {
        const event = row as unknown as DecisionTraceHistoryEvent;
        return (
          <div className="decision-history__status-cell">
            <StatusBadge tone={statusTone(String(row.status))} label={statusLabel(String(row.status))} />
            <span className="copy-muted">{formatOutcome(event)}</span>
            <OutcomeDetail event={event} />
          </div>
        );
      },
    },
  ];
}

export function DecisionHistoryPage({ client, data }: { client: NwrApiClient; data: RedraftBootstrap }) {
  const loader = () => client.redraftDecisionTraceHistory();
  const { result, error, working, reload } = useAsync(loader, [client, data.activeProfileId]);
  const columns = buildColumns(client, reload);

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
              columns={columns}
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
