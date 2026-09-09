// NWR CHEAT SHEET -- COMBINED NWR + MARKET + BALLERS VIEW (2026-09-08,
// directive section 10, "audit all ADP formatting"): the real round.pick
// formatter and its "known team count only" guard were already built in
// draft-room-v2.tsx for Suggestions/Compare/Player Drawer -- extracted here
// (no logic changed) so Cheat Sheets' new Combined view can reuse the exact
// same safe formatting instead of a second, divergent implementation. This
// is the one and only place any screen turns a raw overall-ADP number into
// a round.pick string; nothing here ever concatenates two formatted values
// or interpolates a raw float directly into a round.pick-shaped string.
import { formatNumber } from "@nwr/ui";

// NWR CHEAT SHEET -- COMBINED NWR + MARKET + BALLERS VIEW (2026-09-08,
// directive section 10, real bug found while building the Combined view):
// a real market ADP value is frequently NOT a whole number (e.g. a
// consensus/averaged overall ADP of 13.3, or Sleeper's own 168.6) -- the
// previous version ran the modulo arithmetic directly on that fractional
// value, so `pickInRound` came out fractional too (with real floating-
// point error, e.g. 3.3000000000000007), and `String(...).padStart(2,
// "0")` stringified that mess verbatim instead of a clean two-digit pick
// number. That produced exactly the "2.2.3000000000000007"-style values
// the owner's directive quoted -- reproduced and confirmed live in this
// session's own render before this fix, not a hypothetical. Every prior
// caller passed a real integer pick (draft board current pick, recent
// picks), so `Math.round` here is a no-op for them and changes nothing;
// the existing formatRoundPick/formatAdpRoundPick unit tests (all
// integer inputs) still pass unchanged.
export function formatRoundPick(overallPick: number, teamCount: number): string {
  const n = Math.max(1, teamCount);
  const roundedPick = Math.round(overallPick);
  const round = Math.floor((roundedPick - 1) / n) + 1;
  const pickInRound = ((roundedPick - 1) % n) + 1;
  return `${round}.${String(pickInRound).padStart(2, "0")}`;
}

/**
 * NWR DRAFT-DAY (ADP round.pick display, owner-requested "4.12"/"7.03"
 * format): the exact raw numeric ADP value is ALWAYS preserved (in the
 * tooltip, and untouched wherever the caller sorts/computes on it) --
 * this only changes what's DISPLAYED. A round.pick conversion is only
 * computed when the ADP source's own reported team count (`sourceTeamCount`,
 * e.g. a 12-team consensus) matches the room's actual team count; when it
 * doesn't (or isn't known), the raw decimal is shown instead of silently
 * reinterpreting a different-sized league's pick numbers as this room's
 * own rounds -- the exact "never parse notation as a decimal or silently
 * convert source context" the owner's directive names.
 */
export function formatAdpRoundPick(
  overallAdp: number | null,
  sourceTeamCount: number | null | undefined,
  roomTeamCount: number | null,
): { text: string; title: string } {
  if (overallAdp == null) return { text: "—", title: "No market ADP available." };
  const raw = formatNumber(overallAdp, 1);
  if (sourceTeamCount == null || roomTeamCount == null || sourceTeamCount !== roomTeamCount) {
    const mismatch = sourceTeamCount != null && roomTeamCount != null;
    return {
      text: raw,
      title: mismatch
        ? `Raw overall ADP ${raw} from a ${sourceTeamCount}-team source -- this room is ${roomTeamCount}-team, so round.pick is not shown here rather than silently reinterpreted.`
        : `Raw overall ADP ${raw} -- the source's own team count isn't known, so round.pick is not shown here rather than guessed.`,
    };
  }
  return {
    text: formatRoundPick(overallAdp, roomTeamCount),
    title: `Raw overall ADP ${raw} (${sourceTeamCount}-team source, matches this room).`,
  };
}
