export interface OwnerDisplayValue {
  label: string;
  title?: string;
}

const GOVERNED_COPY: Record<string, OwnerDisplayValue> = {
  capped_review_required: {
    label: "Review capped",
    title: "Use with review: governed evidence gaps cap confidence.",
  },
  usable_with_confidence_cap: {
    label: "Usable · capped",
    title: "Usable for owner decisions, with confidence capped by governed evidence gaps.",
  },
  review_only_source_limited: {
    label: "Review only · limited source",
    title: "Context only: the available governed source is limited.",
  },
  blocked: {
    label: "Blocked",
    title: "Governed evidence does not support using this value.",
  },
  blocked_rookie: {
    label: "Manual Review Rookie",
    title: "Official draft asset; the frozen Rookie Review did not admit a score.",
  },
  unscored_manual_review: {
    label: "Unscored · Manual Review",
    title: "Draft eligible and selectable; no admitted Rookie Review score.",
  },
  unassigned: {
    label: "—",
    title: "No governed label is assigned.",
  },
};

const RESEARCH_BANDS: Record<string, string> = {
  "1": "Top research band",
  "2": "Upper research band",
  "3": "Middle research band",
  "4": "Lower research band",
  "5": "Deep research band",
};

const PLACEHOLDERS = new Set(["", "nan", "none", "null", "<na>"]);

function keyFor(value: string) {
  return value.trim().toLowerCase().replaceAll(/[^a-z0-9]+/g, "_").replaceAll(/^_+|_+$/g, "");
}

function researchBandNumber(value: string) {
  const normalized = value.trim().replaceAll("_", " ");
  return normalized.match(/^research (?:neighborhood|tier)\s+(\d+)$/i)?.[1];
}

function sentenceCaseToken(value: string) {
  const words = value.replaceAll(/[_-]+/g, " ").trim().toLowerCase();
  if (!words) return "—";
  return words.charAt(0).toUpperCase() + words.slice(1);
}

/**
 * Translates display-only backend vocabulary without mutating the governed value.
 * Unknown prose is preserved; unknown machine tokens are made readable.
 */
export function ownerDisplay(value: unknown, fallback = "—"): OwnerDisplayValue {
  if (value == null) return { label: fallback };
  const text = String(value).trim();
  if (PLACEHOLDERS.has(text.toLowerCase())) return { label: fallback };

  const researchBand = researchBandNumber(text);
  if (researchBand) {
    return {
      label: RESEARCH_BANDS[researchBand] ?? `Research band ${researchBand}`,
      title: "Frozen research grouping only; it does not change NWR rank or trade authority.",
    };
  }

  const governed = GOVERNED_COPY[keyFor(text)];
  if (governed) return governed;

  if (/^[A-Za-z0-9]+(?:[_-][A-Za-z0-9/]+)+$/.test(text)) {
    return { label: sentenceCaseToken(text) };
  }
  return { label: text };
}

export function ownerLabel(value: unknown, fallback = "—") {
  return ownerDisplay(value, fallback).label;
}

export function ownerFieldLabel(value: string) {
  const label = sentenceCaseToken(value);
  return label
    .replace(/^Nwr\b/, "NWR")
    .replace(/^Nfl\b/, "NFL")
    .replace(/\bId\b/g, "ID");
}

export function ownerResearchValue(key: string, value: unknown) {
  const numeric = typeof value === "number" ? value : Number(value);
  if (Number.isFinite(numeric)) {
    if (["confidence", "ceilingSignal", "downsideSignal"].includes(key)) {
      return `${(numeric * 100).toFixed(1)}%`;
    }
    if (["outlook3y", "outlook5y"].includes(key)) return numeric.toFixed(2);
  }
  return ownerLabel(value);
}

export function ownerAge(value: unknown) {
  if (value == null || String(value).trim() === "") return "—";
  const numeric = typeof value === "number" ? value : Number(value);
  return Number.isFinite(numeric) ? numeric.toFixed(1) : "—";
}
