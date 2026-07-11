# Representative Render Review

All PNG captures are actual local Streamlit renders. Runtime/player data visible in those captures is local existing data, not a synthetic production-data change. Synthetic state-only cases are separately marked in `fixtures/representative_draft_states.json`.

| Capture | Viewport | Result |
|---|---:|---|
| `rendered_evidence/desktop_live_draft.png` | 1440×1000 | Live route rendered; current metrics and workflow present; no horizontal overflow. |
| `rendered_evidence/compact_live_draft.png` | 390×844 | Current-pick metrics elevated; page overflow false; disclosure and primary action present. |
| `rendered_evidence/desktop_mock_draft.png` | 1440×1000 | Mock route rendered with practice-state semantics and shared labels. |
| `rendered_evidence/compact_mock_draft.png` | 390×844 | Page overflow false; assign button 356px wide within x=12..368. |
| `rendered_evidence/compact_mock_expanded_secondary_details.png` | 390×844 | Secondary mock management disclosure expanded; destructive action remains separated. |

The state matrix additionally covers player selected, no player selected, drafted player, current pick, disabled assign, undo available/unavailable, draft complete, empty table, and expanded details. Render evidence supplements but does not replace tests.
