import type { LeagueStateProvenance } from "@nwr/contracts";

export function SnapshotProvenanceNotice({
  provenance,
}: {
  provenance: LeagueStateProvenance | undefined;
}) {
  if (!provenance) return null;
  const retrieved = provenance.retrievedAtUtc ?? "unknown time";
  return (
    <div className={`alert-strip${provenance.stale ? " alert-strip--pending" : ""}`} role="status">
      <strong>{provenance.stale ? "ESPN snapshot stale" : "ESPN snapshot"}</strong>
      <span>
        {provenance.warning || `Point-in-time read retrieved ${retrieved}; no live ESPN refresh ran for this view.`}
      </span>
    </div>
  );
}
