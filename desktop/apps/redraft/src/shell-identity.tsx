import type { NwrApiClient } from "@nwr/api-client";
import type { RedraftBootstrap } from "@nwr/contracts";
import { useEffect, useRef, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";

import { leagueFormat, resolveLeagueLifecycle } from "./league-context";

/**
 * NWR UI foundation pass (2026-09-10, directive Phase 3 -- league shell).
 *
 * Replaces the old full-width `ActiveLeagueSelector` content-area bar
 * (identity + Switch control + four always-visible status pills) with two
 * smaller, purpose-built pieces that consume the exact same real,
 * already-computed data:
 *
 * 1. `ShellIdentity` -- renders in the sidebar's actual top-left, under
 *    the brand lockup (directive: "Top-left: <League Name> (click ->
 *    league chooser), with secondary context... platform"). League name,
 *    lifecycle stage (from the one shared `resolveLeagueLifecycle`
 *    authority -- never a second lifecycle heuristic), format, and the
 *    Switch League control all live here now.
 * 2. `FreshnessIndicator` (in this same file) -- one compact header chip
 *    with a click-for-detail popover, replacing the four permanent
 *    Identity/ADP/Projections/Ready pills with a single quiet signal plus
 *    real detail on demand (directive Phase 3: "no raw provider
 *    diagnostics in the primary shell").
 *
 * No new data is read here -- every field below already existed on
 * `RedraftBootstrap`/`LeagueProfile`/`DraftBoard` before this pass.
 */

const LIFECYCLE_STAGE_LABEL: Record<string, string> = {
  PRE_DRAFT: "Pre-Draft",
  LIVE_DRAFT: "Live Draft",
  IN_SEASON: "In Season",
  OFFSEASON: "Offseason",
};

export function ShellIdentity({
  client,
  data,
  onUpdate,
}: {
  client: NwrApiClient;
  data: RedraftBootstrap;
  onUpdate: (data: RedraftBootstrap) => void;
}) {
  const [working, setWorking] = useState(false);
  const [error, setError] = useState("");
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement | null>(null);
  const active = data.activeProfile;
  const location = useLocation();
  const navigate = useNavigate();
  // NWR UI expansion pass, Work Unit 9 (endurance QA) -- real, reproduced
  // race found via rapid league-switch cycling: this handler navigates to
  // the new league-scoped URL BEFORE its own `activateRedraftProfile` call
  // resolves (by design, per invariant G above). If the owner then follows
  // a DIFFERENT route to another league while that request is still in
  // flight (a deep link, a bookmark, browser back/forward, or a command-
  // palette result -- any path that does not go through this same
  // `switchLeague`, which the disabled Switch-league button already blocks
  // for a second click), `LeagueScopedPage`'s own independent activation
  // effect (RedraftApp.tsx) can finish FIRST and correctly set the newer
  // league active -- only for THIS handler's now-stale response to land
  // moments later and silently clobber it back to the original target,
  // briefly (and, if the owner is not still on a route that re-triggers
  // `LeagueScopedPage`'s own self-correcting effect, indefinitely) showing
  // the wrong league's identity/roster/scoring. Confirmed live with an
  // artificially delayed mock response; `LeagueScopedPage`'s own effect
  // already guards its `onUpdate` call against exactly this kind of
  // supersession (via its `active`/cleanup flag) -- this handler had no
  // equivalent guard at all. Fixed the same way: a per-call request id,
  // so a response only ever updates shared state when it is still the
  // most recently requested switch. `setWorking(false)` stays unconditional
  // (purely local UI state, safe to reset even for a superseded request --
  // gating it too would risk leaving the Switch-league button stuck
  // disabled if a request resolved out of order).
  const switchRequestRef = useRef(0);

  const switchLeague = async (profileId: string) => {
    if (!profileId || profileId === data.activeProfileId || working) return;
    setMenuOpen(false);
    setWorking(true); setError("");
    const requestId = ++switchRequestRef.current;
    // Directive invariant G ("switching leagues cannot leak prior league
    // state"), unchanged from the prior ActiveLeagueSelector: rewrite a
    // league-scoped deep link's leagueKey segment to the new profile
    // FIRST, before activation resolves.
    const pathSegments = location.pathname.split("/");
    if (pathSegments[1] === "league" && pathSegments[2]) {
      const rest = pathSegments.slice(3).join("/");
      navigate(`/league/${encodeURIComponent(profileId)}/${rest}${location.search}`, { replace: true });
    }
    try {
      const next = await client.activateRedraftProfile(profileId);
      if (switchRequestRef.current === requestId) onUpdate(next);
    } catch {
      if (switchRequestRef.current === requestId) setError("League switch could not be saved. The current workspace remains active.");
    } finally {
      setWorking(false);
    }
  };

  useEffect(() => {
    if (!menuOpen) return undefined;
    const onOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) setMenuOpen(false);
    };
    const onEscape = (event: KeyboardEvent) => { if (event.key === "Escape") setMenuOpen(false); };
    document.addEventListener("mousedown", onOutside);
    document.addEventListener("keydown", onEscape);
    return () => {
      document.removeEventListener("mousedown", onOutside);
      document.removeEventListener("keydown", onEscape);
    };
  }, [menuOpen]);

  if (!active) {
    return (
      <div className="nwr-shell-identity">
        <span className="nwr-shell-identity__eyebrow">Active League</span>
        <Link className="nwr-shell-identity__link" to="/leagues"><strong>Choose a league</strong></Link>
        <span className="nwr-shell-identity__empty">Create or import a Redraft league profile</span>
      </div>
    );
  }

  const lifecycle = resolveLeagueLifecycle(active, data.draftBoard);
  const stageClass = lifecycle === "IN_SEASON"
    ? "nwr-shell-identity__stage--season"
    : lifecycle === "OFFSEASON"
      ? "nwr-shell-identity__stage--off"
      : "nwr-shell-identity__stage--draft";

  return (
    <div className="nwr-shell-identity" ref={menuRef}>
      <span className="nwr-shell-identity__eyebrow">Active League</span>
      <Link className="nwr-shell-identity__link" title="Open league chooser" to="/leagues">
        <strong title={active.leagueName}>{active.leagueName}</strong>
      </Link>
      <span className="nwr-shell-identity__meta">{leagueFormat(active, false)}</span>
      <span className={`nwr-shell-identity__stage ${stageClass}`}><i />{LIFECYCLE_STAGE_LABEL[lifecycle] ?? lifecycle}</span>
      {error ? <span className="nwr-shell-identity__meta" role="status" style={{ color: "#ed8b95" }}>{error}</span> : null}
      <div style={{ position: "relative" }}>
        <button
          type="button"
          className="nwr-shell-identity__switch"
          disabled={working || data.profiles.length < 2}
          aria-haspopup="listbox"
          aria-expanded={menuOpen}
          onClick={() => setMenuOpen((open) => !open)}
        >
          {working ? "Switching…" : "Switch league"}
        </button>
        {menuOpen ? (
          <ul className="active-league-selector__switch-menu" role="listbox" aria-label="Available leagues" style={{ left: 0, right: "auto", top: "calc(100% + 4px)" }}>
            {data.profiles.map((profile) => {
              const isActive = profile.profileId === data.activeProfileId;
              return (
                <li key={profile.profileId}>
                  <button
                    type="button"
                    role="option"
                    aria-selected={isActive}
                    className={isActive ? "active-league-selector__switch-option active-league-selector__switch-option--active" : "active-league-selector__switch-option"}
                    title={profile.leagueName}
                    onClick={() => void switchLeague(profile.profileId)}
                  >
                    {profile.leagueName}
                  </button>
                </li>
              );
            })}
          </ul>
        ) : null}
      </div>
    </div>
  );
}

/** Compact header freshness indicator (directive Phase 3): one chip, one
 * word of urgency, click for the real detail -- Identity/ADP/Projections/
 * Draft-board-ready, the exact same four already-computed signals the old
 * `ActiveLeagueSelector` badges showed, just no longer permanently
 * occupying primary shell space. */
export function FreshnessIndicator({ data }: { data: RedraftBootstrap }) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement | null>(null);
  useEffect(() => {
    if (!open) return undefined;
    const onOutside = (event: MouseEvent) => {
      if (ref.current && !ref.current.contains(event.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", onOutside);
    return () => document.removeEventListener("mousedown", onOutside);
  }, [open]);

  if (!data.activeProfile) return null;

  const adp = data.draftBoard?.adp;
  const adpLabel = adp?.available ? `ADP: ${adp.source.replace(/^Owner-imported /i, "Owner ")} · ${adp.freshness ?? "cached"}` : "ADP: unavailable";
  const projectionsLabel = data.status.sourceAsOf ? `Projections: ${data.status.sourceAsOf}` : "Projections: unavailable";
  const readyLabel = data.status.ready ? "Draft board ready" : data.status.tone === "blocked" ? "Projections blocked" : "Review required";
  const identityLabel = data.health?.playerUniverseAvailable
    ? `Identity: ${data.health.lastGeneratedTimestamp || "current"}`
    : "Identity: unavailable";

  const issueCount = [adp?.available, data.status.ready, data.health?.playerUniverseAvailable]
    .filter((value) => value === false).length;
  const chipTone = data.status.tone === "blocked" ? "unavailable" : issueCount > 0 ? "warning" : "healthy";
  const chipLabel = issueCount === 0 ? "Current" : `${issueCount} data issue${issueCount === 1 ? "" : "s"}`;

  return (
    <div className="nwr-freshness" ref={ref}>
      <button
        type="button"
        className={`nwr-freshness__chip nwr-freshness__chip--${chipTone}`}
        aria-haspopup="dialog"
        aria-expanded={open}
        onClick={() => setOpen((value) => !value)}
        title="Data freshness -- click for detail"
      >
        <i />{chipTone === "healthy" ? "● " : "⚠ "}{chipLabel}
      </button>
      {open ? (
        <div className="nwr-freshness__panel" role="dialog" aria-label="Data freshness detail">
          <dl>
            <div><dt>Identity</dt><dd>{identityLabel.replace(/^Identity: /, "")}</dd></div>
            <div><dt>Market ADP</dt><dd>{adpLabel.replace(/^ADP: /, "")}</dd></div>
            <div><dt>Projections</dt><dd>{projectionsLabel.replace(/^Projections: /, "")}</dd></div>
            <div><dt>Draft board</dt><dd>{readyLabel}</dd></div>
          </dl>
        </div>
      ) : null}
    </div>
  );
}
