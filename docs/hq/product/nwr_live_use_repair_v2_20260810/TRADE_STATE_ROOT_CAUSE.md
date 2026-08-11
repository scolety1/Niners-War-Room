# Trade State Root Cause

The previous page maintained multiple selection concepts: side widgets, package state, prior scenario state, and separate brief selectors. Unknown keys were converted into placeholder evidence rows instead of being rejected. A stale key could therefore survive a rerender and appear in the mixed package list even when neither visible side contained the asset.

The repair versions and migrates the page session, atomically replaces analyzed state from the two visible selectors, de-duplicates across both sides, and only renders keys present in the current governed lookup. Clear resets both the canonical state and widget values. Reopen synchronizes the saved sides back to the same widgets. The standalone duplicate brief selectors were removed; Markdown and JSON derive from the exact analyzed state.

Invariant: `selected evidence == unique governed assets currently in You give or You receive`.
