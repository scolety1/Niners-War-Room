import { NwrApiError, type NwrApiClient } from "@nwr/api-client";
import type { DynastyWaiverCandidate, DynastyWaiversResult } from "@nwr/contracts";
import { Button, ErrorState, PageHeader, Panel, StatusBadge, formatNumber } from "@nwr/ui";
import { useEffect, useMemo, useState } from "react";

function faabLabel(row: DynastyWaiverCandidate): string {
  if (row.faabBidLow == null || row.faabBidHigh == null) return "Unavailable";
  if (row.faabBidLow === row.faabBidHigh) return `$${row.faabBidLow}`;
  return `$${row.faabBidLow}–$${row.faabBidHigh}`;
}

function dropLabel(row: DynastyWaiverCandidate): string {
  if (row.dropRequired === false) return "Open slot";
  if (!row.dropCandidate) return "No safe drop found";
  return `${row.dropCandidate.playerName} (${row.dropCandidate.position})`;
}

export function WaiverWirePage({ client }: { client: NwrApiClient }) {
  const [result, setResult] = useState<DynastyWaiversResult | null>(null);
  const [error, setError] = useState<NwrApiError | null>(null);
  const [working, setWorking] = useState(true);
  const [revision, setRevision] = useState(0);
  const [position, setPosition] = useState("ALL");

  useEffect(() => {
    let active = true;
    setWorking(true);
    setError(null);
    void client.dynastyWaivers()
      .then((value) => { if (active) setResult(value); })
      .catch((reason: unknown) => {
        if (!active) return;
        setError(reason instanceof NwrApiError
          ? reason
          : new NwrApiError("Dynasty Waiver Wire could not be loaded."));
      })
      .finally(() => { if (active) setWorking(false); });
    return () => { active = false; };
  }, [client, revision]);

  const positions = useMemo(
    () => ["ALL", ...new Set((result?.candidates ?? []).map((row) => row.position))],
    [result],
  );
  const rows = useMemo(
    () => (result?.candidates ?? []).filter(
      (row) => position === "ALL" || row.position === position,
    ),
    [position, result],
  );

  return <>
    <PageHeader
      eyebrow="This week · Dynasty roster building"
      title="Dynasty Waiver Wire"
      description="Real league availability ranked through long-term NWR value, roster fit, age/upside, stash value, and protected-slot-aware drop context."
      status={<>
        <StatusBadge
          tone={result?.source === "SLEEPER_LIVE" ? "safe" : "review"}
          label={result?.source === "SLEEPER_LIVE" ? "Live Sleeper availability" : "Dated local snapshot"}
        />
        {result?.faabContext.remainingBudgetDollars != null ? <StatusBadge
          tone="safe"
          label={`$${result.faabContext.remainingBudgetDollars} FAAB left`}
        /> : null}
        <StatusBadge tone="review" label="Read only" />
      </>}
      actions={<Button
        disabled={working}
        icon="activity"
        onClick={() => setRevision((value) => value + 1)}
        variant="secondary"
      >{working ? "Refreshing…" : "Refresh"}</Button>}
    />
    {result?.source === "SLEEPER_SNAPSHOT" ? <div className="alert-strip">
      <strong>Live availability unavailable</strong>
      <span>Showing the local snapshot from {result.retrievedAtUtc}. Verify availability in Sleeper; no FAAB balance is guessed.</span>
    </div> : null}
    {error ? <ErrorState message={error.message} recovery={error.recoveryAction} /> : null}
    <Panel
      title="Available dynasty targets"
      eyebrow={`${result?.leagueName ?? "Connected league"} · ${result?.candidates.length ?? 0} candidates`}
      action={<label className="compact-filter"><span>Position</span><select
        value={position}
        onChange={(event) => setPosition(event.target.value)}
      >{positions.map((value) => <option key={value} value={value}>{value}</option>)}</select></label>}
    >
      {working && !result ? <p className="copy-muted">Reading real league availability…</p> : null}
      {result && !rows.length ? <p className="copy-muted">No governed, unrostered candidates match this filter.</p> : null}
      {rows.length ? <div className="table-wrap"><table>
        <thead><tr>
          <th>Player</th><th>NWR</th><th>Age / upside</th><th>Roster fit</th>
          <th>Stash</th><th>FAAB</th><th>Drop / net</th>
        </tr></thead>
        <tbody>{rows.map((row) => <tr key={row.assetId}>
          <td><strong>{row.playerName}</strong><small>{row.team || "FA"} · {row.position} · unrostered</small>
            {row.currentStatusOverride ? <StatusBadge tone="blocked" label={row.currentStatusOverride.kind.replaceAll("_", " ")} /> : null}
          </td>
          <td><strong>#{row.dynastyRank ?? "—"}</strong><small>{formatNumber(row.dynastyScore, 1)} value</small></td>
          <td><strong>{row.age == null ? "—" : formatNumber(row.age, 1)}</strong><small>{row.ageUpside} upside</small></td>
          <td title={row.rosterFitReason}><strong>{row.rosterFit.replaceAll("_", " ")}</strong><small>Priority {formatNumber(row.priorityScore, 1)}</small></td>
          <td><strong>{row.stashValue}</strong></td>
          <td title={row.faabRationale}><strong>{faabLabel(row)}</strong><small>Relative range</small></td>
          <td><strong>{dropLabel(row)}</strong><small>{row.transactionNetValue == null
            ? "Net unavailable"
            : `${row.transactionNetValue >= 0 ? "+" : ""}${formatNumber(row.transactionNetValue, 1)} value`}</small></td>
        </tr>)}</tbody>
      </table></div> : null}
    </Panel>
    {result ? <p className="copy-muted">
      Governed Dynasty value is unchanged. FAAB is a relative heuristic, not a predicted winning bid.
      Not scored yet: {result.method.notScored.join(", ")}. Reserve and taxi players are never suggested as drops.
      NWR never submits a claim.
    </p> : null}
  </>;
}
