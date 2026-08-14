# Live companion status

The existing client can safely GET `draft/{draft_id}/picks`; the new `load_sleeper_draft_picks` wrapper validates only a list of pick objects. This supports a smallest safe future companion: poll reads → map exact player IDs → locally deplete NWR board → refresh recommendations.

It is not wired as a timer or real-time mode in this lane. There is no Sleeper selection, transaction, roster edit, league edit, or unofficial browser automation.
