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

export type DecisionExplainTone = "recommended" | "warning" | "alternative" | "neutral";
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
      {(impact || alternative || freshness) ? (
        <dl className="nwr-explain__facts">
          {impact ? <div><dt>Expected impact</dt><dd>{impact}</dd></div> : null}
          {alternative ? <div><dt>Alternative</dt><dd>{alternative}</dd></div> : null}
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
