import type { Notice, RedraftBootstrap } from "@nwr/contracts";

/**
 * P2-1 (Data Notice Strip, 2026-09-12/13): pure derivation for the shell-
 * level "how healthy is my data right now" summary shown in the header
 * status bar (`FreshnessIndicator` in shell-identity.tsx), which links, on
 * click, into the existing full Data Health page (`pages.tsx`,
 * `DataHealthPage`). Same family/testing convention as
 * `attention-center.ts`/`league-summary.ts`: pure logic here, unit-tested
 * directly; the presentation component just renders this result.
 *
 * Two REAL, already-computed sources are combined -- this module computes
 * zero new business data and never touches the backend:
 *
 * 1. `RedraftBootstrap.notices` -- the exact same array
 *    `DesktopBackendFacade.redraft_bootstrap` already returns and Data
 *    Health already renders unmodified (`src/application/desktop_facade.py`,
 *    the `notices = [...]` block). A handful of its entries are permanent,
 *    always-present product-boundary disclosures -- they explain what NWR
 *    does or does not model, every single time, regardless of whether
 *    anything is actually wrong -- rather than genuine, conditional
 *    data-health issues. Counting those as "issues" would mean this shell
 *    signal could never reach a calm "Current" state for anyone, so they
 *    are excluded here (see ALWAYS_PRESENT_DISCLOSURE_TITLES). The K/DST
 *    external-consensus boundary notice is excluded for the same
 *    always-present reason, and because it is provider plumbing (an
 *    optional external FantasyPros API-key boundary) -- exactly the kind
 *    of internal detail this compact signal is directed not to surface.
 *    Every other notice this function sees (i.e. anything conditionally
 *    appended -- unsupported Sleeper scoring fields, practical-scoring
 *    mode, a draft-rounds/roster-capacity mismatch, blocked rookie rows)
 *    is treated as a real, owner-relevant issue.
 * 2. The player-identity / market-ADP / draft-board-readiness signals the
 *    header chip already read before this pass -- real, owner-relevant
 *    gaps `data.notices` does not itself carry as notice rows.
 *
 * This file adds no new field to any backend payload and computes no new
 * notice content -- it only classifies and summarizes what already exists.
 */

// Exact titles `desktop_facade.py`'s `redraft_bootstrap()` always appends
// to `notices`, verbatim, regardless of data health. Kept as a small,
// explicit, documented set rather than a heuristic -- a real, disclosed
// fragility: a future backend wording change to any of these four titles
// would need this list updated too, not silently drift.
const ALWAYS_PRESENT_DISCLOSURE_TITLES = new Set<string>([
  "Redraft is isolated from Dynasty",
  "Current-season evidence only",
  "Role-change context is not yet modeled",
  "External K/DST consensus boundary",
]);

function isActionableNotice(notice: Notice): boolean {
  return notice.tone !== "ready" && !ALWAYS_PRESENT_DISCLOSURE_TITLES.has(notice.title);
}

export interface ShellNoticeItem {
  title: string;
  message: string;
  blocked: boolean;
}

export type ShellNoticeTone = "healthy" | "warning" | "unavailable";

export interface ShellNoticeSummary {
  count: number;
  label: string;
  tone: ShellNoticeTone;
  items: ShellNoticeItem[];
}

/** No active league yet -- nothing to summarize. Kept as an explicit,
 * stable result (rather than letting callers guess) even though the
 * presentation component today chooses not to render a chip at all in
 * this state. */
const NO_ACTIVE_LEAGUE_SUMMARY: ShellNoticeSummary = { count: 0, label: "Current", tone: "healthy", items: [] };

export function summarizeShellNotices(data: RedraftBootstrap): ShellNoticeSummary {
  if (!data.activeProfile) return NO_ACTIVE_LEAGUE_SUMMARY;

  const items: ShellNoticeItem[] = [];

  if (data.health && data.health.playerUniverseAvailable === false) {
    items.push({
      title: "Player identity unavailable",
      message: "The governed player-identity registry could not be read for this profile.",
      blocked: true,
    });
  }
  if (data.draftBoard?.adp && data.draftBoard.adp.available === false) {
    items.push({
      title: "Market ADP unavailable",
      message: "No ADP snapshot is available for this league yet.",
      blocked: false,
    });
  }
  if (!data.status.ready) {
    items.push({
      title: data.status.tone === "blocked" ? "Projections blocked" : "Review required",
      message: data.status.summary,
      blocked: data.status.tone === "blocked",
    });
  }

  for (const notice of data.notices ?? []) {
    if (!isActionableNotice(notice)) continue;
    items.push({ title: notice.title, message: notice.message, blocked: notice.tone === "blocked" });
  }

  const count = items.length;
  const anyBlocked = items.some((item) => item.blocked);
  const tone: ShellNoticeTone = count === 0 ? "healthy" : anyBlocked ? "unavailable" : "warning";
  const label = count === 0 ? "Current" : count === 1 ? items[0]!.title : `${count} data issues`;

  return { count, label, tone, items };
}
