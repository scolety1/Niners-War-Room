import { useReducer } from "react";

import { NwrApiError, type NwrApiClient } from "@nwr/api-client";
import type { DecisionClassSummary, DecisionTraceHistoryEvent, RedraftBootstrap } from "@nwr/contracts";
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
  buildClassSummaryDisplay,
  buildOutcomeDetailSections,
  CLASS_SUMMARY_TITLE,
  evaluationStatusLabel,
  evaluationStatusTone,
  formatClassSpecificHeadline,
  formatDecisionType,
  formatGeneratedAt,
  formatOutcome,
  formatOwnerAction,
  hasOutcomeDetail,
  INITIAL_OWNER_ACTION_CELL_STATE,
  ownerActionCellReducer,
  ownerActionOptionsForDecisionType,
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
  // NWR Full Cycle V1 (Worker 6): a real live-browser walkthrough found
  // this cell's owner-action "Change" flow could get permanently stuck
  // ("Recording…", every button disabled, no error, no recovery short of
  // a full page reload) -- root cause was the old 3-independent-`useState`
  // version's success path resetting `editing` but never `submitting`.
  // Replaced with `ownerActionCellReducer` (decision-history-format.ts),
  // a single pure state machine whose `RECORD_SUCCEEDED` case always
  // resets both together -- see that function's doc for the full
  // reproduction and `decision-history-format.test.ts` for the regression
  // coverage.
  const [state, dispatch] = useReducer(ownerActionCellReducer, INITIAL_OWNER_ACTION_CELL_STATE);
  const { editing, submitting, error } = state;
  const options = ownerActionOptionsForDecisionType(event.decisionType);

  const record = async (action: string) => {
    dispatch({ type: "RECORD_STARTED" });
    try {
      await client.redraftRecordDecisionTraceOwnerAction(event.traceId, action);
      dispatch({ type: "RECORD_SUCCEEDED" });
      onRecorded();
    } catch (reason) {
      dispatch({
        type: "RECORD_FAILED",
        message: reason instanceof NwrApiError ? reason.message : "Could not record this action.",
      });
    }
  };

  if (event.ownerAction && !editing) {
    return (
      <div className="decision-history__owner-action">
        <span>{formatOwnerAction(event)}</span>
        <Button
          className="decision-history__owner-action-change"
          onClick={() => dispatch({ type: "CHANGE_CLICKED" })}
          variant="ghost"
        >
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
        <Button disabled={submitting} onClick={() => dispatch({ type: "CANCEL_CLICKED" })} variant="ghost">
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

/**
 * History UI V3 (Work Unit 13): the exact 6 columns the governing directive
 * names -- DATE / LEAGUE / DECISION TYPE / NWR RECOMMENDATION / OWNER
 * ACTION / OUTCOME STATUS. "League" is new in V3 (V2 omitted it, relying
 * solely on the page's own single-league scoping -- see the module doc
 * below); every other column is the same real data V2 already rendered,
 * unchanged in substance.
 *
 * The Outcome Status column now renders the real `OutcomeEvaluation`
 * status (`evaluationStatusLabel`/`evaluationStatusTone`, the 5-member
 * closed set the backend actually emits -- `PENDING_OUTCOME`/
 * `PENDING_WINDOW`/`EVALUATED`/`INSUFFICIENT_DECISION_CONTEXT`/
 * `NOT_APPLICABLE`) rather than V2's ledger-append status
 * (`RECOMMENDED`/`OWNER_ACTION_RECORDED`/`OUTCOME_RECORDED`, still shown
 * nowhere on this page anymore -- it answered "has this row been appended
 * to," not "could NWR's recommendation actually be evaluated," which is
 * what an owner reading this column actually wants to know). A one-line,
 * real, class-specific headline (`formatClassSpecificHeadline`) sits right
 * under the badge -- never a synthesized score, only the real metric each
 * of the 8 evaluators already computed.
 */
function buildColumns(client: NwrApiClient, onRecorded: () => void): TableColumn[] {
  return [
    {
      key: "generatedAt", label: "Date", sort: "text",
      render: (row) => <span>{formatGeneratedAt(String(row.generatedAt))}</span>,
    },
    {
      key: "league", label: "League", sort: "text",
      render: (row) => <span>{String(row.league ?? "—")}</span>,
    },
    {
      key: "decisionType", label: "Decision type", sort: "text",
      render: (row) => <span>{formatDecisionType(String(row.decisionType))}</span>,
    },
    {
      key: "recommendation", label: "NWR recommendation",
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
        const evaluationStatus = event.evaluationDetail?.evaluation.evaluationStatus;
        const headline = formatClassSpecificHeadline(event);
        return (
          <div className="decision-history__status-cell">
            {evaluationStatus ? (
              <StatusBadge tone={evaluationStatusTone(evaluationStatus)} label={evaluationStatusLabel(evaluationStatus)} />
            ) : (
              <span className="copy-muted">{formatOutcome(event)}</span>
            )}
            {headline && headline !== evaluationStatusLabel(evaluationStatus ?? "") ? (
              <span className="copy-muted decision-history__status-headline">{headline}</span>
            ) : null}
            <OutcomeDetail event={event} />
          </div>
        );
      },
    },
  ];
}

/**
 * Work Unit 14: one independent card per real decision class, gated by the
 * same preregistered minimum-sample rule the backend itself already
 * enforces (`MIN_SAMPLE_SIZE_FOR_PER_CLASS_SUMMARY` = 20) -- this component
 * renders whatever `redraft_decision_trace_outcome_summary` actually
 * returned, never recomputing a gate client-side. **No card here is ever
 * combined with another into a cross-class figure** -- each card's own
 * title (`CLASS_SUMMARY_TITLE`) and rows come from exactly one class's own
 * `summarize_*` output. Given the real production trace store is currently
 * empty (Worker 4's own confirmed finding, unchanged as of this pass),
 * every card will honestly show "NOT ENOUGH DATA YET" rows against real
 * production data today -- that is the correct, expected result, not a
 * loading/error state.
 */
function ClassSummaryPanel({ client }: { client: NwrApiClient }) {
  const loader = () => client.redraftDecisionTraceOutcomeSummary();
  const { result, error, working, reload } = useAsync(loader, [client]);

  if (!result && working) {
    return <p className="copy-muted" aria-live="polite">Reading per-class outcome summaries…</p>;
  }
  if (error) {
    return (
      <ErrorState
        message={error instanceof NwrApiError ? error.message : "Class-specific summaries could not be read."}
        onRetry={reload}
      />
    );
  }
  if (!result) return null;

  // `result.summaries` is a real LIST (each entry carries its own
  // `decisionType`), never a dict keyed by decisionType -- see
  // `DecisionTraceOutcomeSummaryResult`'s own contract comment for why (the
  // same real HTTP camelCase-key mangling bug this pass found and fixed for
  // `statusCounts`). Ordered here by the app's own preferred display order
  // (`CLASS_SUMMARY_TITLE`'s key order), not whatever order the backend
  // happened to return.
  const byType = new Map(result.summaries.map((summary) => [summary.decisionType, summary]));
  const entries = Object.keys(CLASS_SUMMARY_TITLE)
    .map((decisionType) => [decisionType, byType.get(decisionType)] as const)
    .filter((entry): entry is [string, DecisionClassSummary] => Boolean(entry[1]));

  return (
    <Panel
      title="Class-specific outcome summaries"
      eyebrow={`${result.totalTraceCount} total recorded trace${result.totalTraceCount === 1 ? "" : "s"} this league`}
    >
      <p className="copy-muted decision-history__disclosure">
        Every class below is evaluated and summarized entirely independently -- a Start/Sit point delta and a FAAB
        dollar-calibration figure are never comparable, and no card here is ever combined into one cross-class score.
      </p>
      <div className="decision-history__summary-grid">
        {entries.map(([decisionType, summary]) => {
          const display = buildClassSummaryDisplay(decisionType, summary);
          return (
            <div className="decision-history__summary-card" key={decisionType}>
              <h4>{display.title}</h4>
              <dl>
                {display.rows.map((row) => (
                  <div className="decision-history__detail-row" key={row.label}>
                    <dt>{row.label}</dt>
                    <dd>{row.value}</dd>
                  </div>
                ))}
              </dl>
            </div>
          );
        })}
      </div>
    </Panel>
  );
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
      <ClassSummaryPanel client={client} />
      <p className="copy-muted decision-history__disclosure">
        No calibration, accuracy, or "was NWR right" metric is shown here -- real season outcomes don't yet exist for
        anything recorded so far, and this page never invents one.
      </p>
    </>
  );
}
