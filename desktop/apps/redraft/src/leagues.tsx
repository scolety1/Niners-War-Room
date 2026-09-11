import { NwrApiError, type NwrApiClient } from "@nwr/api-client";
import type { LeagueProfile, RedraftBootstrap } from "@nwr/contracts";
import { Button, EmptyState, ErrorState, Icon, PageHeader } from "@nwr/ui";
import { useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

import { leagueFormat, leagueIdentityFormat, resolveLeagueHomeSubpath } from "./league-context";

export function LeaguesPage({
  client,
  data,
  onUpdate,
}: {
  client: NwrApiClient;
  data: RedraftBootstrap;
  onUpdate: (data: RedraftBootstrap) => void;
}) {
  const navigate = useNavigate();
  const activationInFlight = useRef(false);
  const [workingProfileId, setWorkingProfileId] = useState<string | null>(null);
  const [error, setError] = useState<NwrApiError | null>(null);

  const activate = async (profile: LeagueProfile) => {
    if (activationInFlight.current) return;
    activationInFlight.current = true;
    setWorkingProfileId(profile.profileId);
    setError(null);
    try {
      const next = await client.activateRedraftProfile(profile.profileId);
      onUpdate(next);
      // NWR pre-UI architecture pass (directive section 2, invariant A):
      // this used to unconditionally navigate every opened league to
      // /draft-room-v2 -- a real, reproduced bug that dropped the owner
      // into the Draft Room even for an already-in-season league. Now
      // resolved by the ONE lifecycle authority, using the FRESH bootstrap
      // this same activation call just returned (so it reflects the
      // league that was just opened, not whatever was active before).
      const activatedProfile = next.activeProfile ?? profile;
      const subpath = resolveLeagueHomeSubpath(activatedProfile, next.draftBoard);
      navigate(`/league/${encodeURIComponent(profile.profileId)}/${subpath}`);
    } catch (reason) {
      setError(reason instanceof NwrApiError
        ? reason
        : new NwrApiError(`${profile.leagueName} could not be opened.`));
    } finally {
      activationInFlight.current = false;
      setWorkingProfileId(null);
    }
  };

  return <div className="league-chooser">
    <PageHeader
      eyebrow="League chooser · local profiles"
      title="Niners War Room — Which league do you want to work on?"
      description="Choose a league to open its isolated draft workspace."
    />
    {error ? <ErrorState message={error.message} recovery={error.recoveryAction} /> : null}
    {data.profiles.length ? (
      <div className="league-chooser__grid" aria-label="Available leagues">
        {data.profiles.map((profile) => {
          const isActive = profile.profileId === data.activeProfileId;
          const isWorking = profile.profileId === workingProfileId;
          return (
            <button
              aria-pressed={isActive}
              className={`league-card ${isActive ? "league-card--active" : ""}`}
              disabled={workingProfileId !== null}
              key={profile.profileId}
              onClick={() => void activate(profile)}
              type="button"
            >
              <span className="league-card__icon"><Icon name="trophy" size={22} /></span>
              <span className="league-card__body">
                <span className="league-card__heading">
                  <strong title={profile.leagueName}>{profile.leagueName}</strong>
                  {isActive ? <em>Active</em> : null}
                </span>
                <small>{leagueFormat(profile)}</small>
                <small>{leagueIdentityFormat(profile)}</small>
              </span>
              <span className="league-card__action">
                {isWorking ? "Opening…" : "Open workspace"}
                <Icon name="chevron" size={14} />
              </span>
            </button>
          );
        })}
      </div>
    ) : (
      <EmptyState
        icon="profile"
        title="No leagues yet"
        message="Create a local league from a validated preset, or import your Sleeper league, before opening a workspace."
        action={<Button icon="profile" onClick={() => navigate("/profile")}>Set up a league</Button>}
      />
    )}
  </div>;
}
