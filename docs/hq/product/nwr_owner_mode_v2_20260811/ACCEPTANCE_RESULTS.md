# Owner acceptance results

## Passed

- Owner Mode is the default and Home asks for the decision first.
- Navigation is grouped by Owner Mode, Evaluate Players, Make Decisions, Draft Tools, Team Planning,
  Advanced / Data, and Settings.
- Every primary owner page has exactly one semantic H1 and no browser traceback.
- Desktop 1440x900 checks passed with no document-level horizontal overflow.
- Mobile 390x844 checks passed on Home, Rankings, Why NWR Ranks Them, Compare, Analyze Trade, and All
  Dynasty Assets with no document-level horizontal overflow.
- A real mobile visual review caught and corrected light-on-white metric text. Final computed colors are
  `rgb(95, 107, 122)` for metric labels and `rgb(23, 32, 42)` for values.
- Eleven owner pages executed through Streamlit AppTest with zero exceptions.

## Owner acceptance failures still remaining

- The market snapshot identifies itself as stale as of 2026-07-17. Owner Mode does not disguise it as
  current.
- Analyze Trade retains several dense advanced/manual planning sections. The first decision path is
  clearer, but the whole page is not yet as light as Rankings or Compare.
- On the first cold session after a process restart, direct navigation to a bookmarked Streamlit route
  can show a dismissible framework "Page not found" dialog while the registered route renders behind
  it. Normal navigation from Home does not reproduce the dialog.
- Advanced / Data is intentionally dense and is not designed as the enjoyable default surface.
