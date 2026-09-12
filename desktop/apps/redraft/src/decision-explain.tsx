import type { ReactNode } from "react";
import { StatusBadge } from "@nwr/ui";

/**
 * NWR UI foundation pass (2026-09-10, directive Phase 6): the ONE
 * decision-explanation grammar every recommendation surface should read
 * the same way -- RECOMMENDATION -> WHY (biggest reason, second reason)
 * -> ALTERNATIVE -> UNCERTAINTY (only when meaningful) -> DATA (freshness)
 * -> ADVANCED (collapsed by default). This pass wires it into Weekly
 * Home's "NWR Actions" cards (`in-season.tsx`); it is written generically
 * so a later pass can adopt it for Lineup/Waivers/Trades without a second
 * competing explanation layout.
 *
 * Purely presentational: every field is a caller-supplied string/node
 * already derived from real, already-computed data (see
 * `home-action-explain.ts` for Home's own derivation) -- this component
 * invents no new numbers or claims.
 */

// NWR UI expansion pass (2026-09-12, Trades surface): "negative" is
// additive -- a genuine fourth outcome (Home/Lineup/Improve Team's own
// recommendations are always NWR's own top pick, so they never needed a
// "this is a bad idea" tone; a trade the owner is evaluating can
// genuinely score as one). Maps to the design system's existing
// `--nwr-unavailable` token (crimson family, "blocked / cannot compute")
// rather than inventing a new color.
export type DecisionExplainTone = "recommended" | "warning" | "alternative" | "neutral" | "negative";
export type DecisionExplainConfidence = "HIGH" | "NOMINAL" | "LOW" | "UNAVAILABLE";

const CONFIDENCE_TONE: Record<DecisionExplainConfidence, "safe" | "review" | "blocked" | "offline"> = {
  HIGH: "safe",
  NOMINAL: "safe",
  LOW: "review",
  UNAVAILABLE: "offline",
};

const CONFIDENCE_LABEL: Record<DecisionExplainConfidence, string> = {
  HIGH: "High confidence",
  NOMINAL: "Confident",
  LOW: "Low confidence — close call",
  UNAVAILABLE: "Confidence unavailable",
};

export function DecisionExplain({
  eyebrow,
  headline,
  why,
  secondaryWhy,
  alternative,
  confidence,
  impact,
  bid,
  thisWeekImpact,
  rosImpact,
  depth,
  positionEffect,
  risk,
  waitAvailability,
  rosterEffect,
  status,
  freshness,
  advanced,
  actions,
  tone = "neutral",
}: {
  eyebrow?: ReactNode;
  headline: ReactNode;
  why: string;
  secondaryWhy?: string | null;
  alternative?: string | null;
  confidence?: DecisionExplainConfidence | null;
  impact?: string | null;
  /** A suggested-bid fact (e.g. FAAB), distinct from `impact` -- Improve
   * Team's own "BID $X-Y" grammar. Optional and additive: existing callers
   * (Home, Lineup) never pass this and render byte-for-byte as before. */
  bid?: string | null;
  /** Split week-scoped vs. season-scoped impact, for surfaces where both
   * are real and distinct (Improve Team's "THIS WEEK <impact> / ROS
   * <impact>" grammar) -- rendered as two separate fact rows instead of
   * the generic `impact` row when present. Optional and additive. */
  thisWeekImpact?: string | null;
  rosImpact?: string | null;
  /** Trades' own "DEPTH" fact -- bench contingency value before/after a
   * proposed trade. Optional and additive: existing callers (Home,
   * Lineup, Improve Team) never pass this and render byte-for-byte as
   * before. */
  depth?: string | null;
  /** Trades' own "POSITION EFFECT" fact -- starter holes and position
   * redundancy before/after. Optional and additive, same as `depth`. */
  positionEffect?: string | null;
  /** Draft Room's own "WAIT / AVAILABILITY" fact -- the real Cost of
   * Waiting / Make-It-Back read for the recommended candidate (should the
   * owner wait, will this player still be there?). Optional and additive:
   * existing callers (Home, Lineup, Improve Team, Trades) never pass this
   * and render byte-for-byte as before. */
  waitAvailability?: string | null;
  /** Draft Room's own "ROSTER EFFECT" fact -- the real Team Score
   * before/after (full-draft-completion horizon, same one the candidate
   * table already shows) plus a real starter/bench-depth note from the
   * backend's own `marginalRosterUtility`, when available. Optional and
   * additive, same as `waitAvailability`. */
  rosterEffect?: string | null;
  /** A real, backend-supplied risk-flag summary, distinct from `status`
   * (a single player's health/availability) -- e.g. Trade Analysis's own
   * `riskFlags`. `null` is an honest "no risk flags recorded", never a
   * fabricated "no risk" claim. Optional and additive. */
  risk?: string | null;
  /** A player/roster health-status fact, distinct from `confidence`
   * (which is NWR's own certainty about the recommendation) -- e.g. the
   * recommended starter's real injury/availability status. Optional and
   * additive: callers that don't pass it (Home) render byte-for-byte as
   * before. */
  status?: { tone: "safe" | "review" | "blocked" | "offline"; label: string } | null;
  freshness?: string | null;
  advanced?: ReactNode;
  actions?: ReactNode;
  tone?: DecisionExplainTone;
}) {
  return (
    <article className={`nwr-explain nwr-explain--${tone}`}>
      <header className="nwr-explain__head">
        <div className="nwr-explain__headline-block">
          {eyebrow ? <span className="nwr-explain__eyebrow">{eyebrow}</span> : null}
          <p className="nwr-explain__headline">{headline}</p>
        </div>
        {confidence ? (
          <StatusBadge tone={CONFIDENCE_TONE[confidence]} label={CONFIDENCE_LABEL[confidence]} />
        ) : null}
      </header>
      <p className="nwr-explain__why">{why}</p>
      {secondaryWhy ? <p className="nwr-explain__why nwr-explain__why--secondary">{secondaryWhy}</p> : null}
      {(impact || bid || thisWeekImpact || rosImpact || depth || positionEffect || risk || alternative || waitAvailability || rosterEffect || status || freshness) ? (
        <dl className="nwr-explain__facts">
          {bid ? <div><dt>Suggested bid</dt><dd>{bid}</dd></div> : null}
          {thisWeekImpact ? <div><dt>This week</dt><dd>{thisWeekImpact}</dd></div> : null}
          {rosImpact ? <div><dt>Rest of season</dt><dd>{rosImpact}</dd></div> : null}
          {depth ? <div><dt>Depth</dt><dd>{depth}</dd></div> : null}
          {positionEffect ? <div><dt>Position effect</dt><dd>{positionEffect}</dd></div> : null}
          {impact ? <div><dt>Expected impact</dt><dd>{impact}</dd></div> : null}
          {alternative ? <div><dt>Alternative</dt><dd>{alternative}</dd></div> : null}
          {waitAvailability ? <div><dt>Wait / availability</dt><dd>{waitAvailability}</dd></div> : null}
          {rosterEffect ? <div><dt>Roster effect</dt><dd>{rosterEffect}</dd></div> : null}
          {risk ? <div><dt>Risk</dt><dd>{risk}</dd></div> : null}
          {status ? <div><dt>Status</dt><dd><StatusBadge tone={status.tone} label={status.label} /></dd></div> : null}
          {freshness ? <div><dt>Data</dt><dd>{freshness}</dd></div> : null}
        </dl>
      ) : null}
      {advanced ? (
        <details className="nwr-explain__advanced">
          <summary>Advanced</summary>
          <div className="nwr-explain__advanced-body">{advanced}</div>
        </details>
      ) : null}
      {actions ? <div className="nwr-explain__actions">{actions}</div> : null}
    </article>
  );
}
