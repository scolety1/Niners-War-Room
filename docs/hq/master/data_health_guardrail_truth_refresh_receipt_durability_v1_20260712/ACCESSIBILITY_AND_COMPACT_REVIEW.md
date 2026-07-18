# Accessibility and Compact Review

The receipt panel uses native Streamlit headings, status callouts, tables, and disclosures. Every state has explicit text; color is supplemental. “Latest refresh attempt” and “Validated prior receipt (not latest)” are separate role labels. Receipt creation, refresh start, refresh finish, latest-success, retained-data, and last-known-good fields have understandable column labels.

Recovery and lifecycle disclosures are native keyboard-operable expanders. The recovery disclosure repeats that it is passive guidance and distinguishes available actions, review links, information-only rows, and unavailable actions. No diagnostic path is rendered as a clickable link. Informational content is not styled or labeled as an automatic action.

At 375 by 812 pixels, the controlled render keeps the validation callout, latest-attempt label, receipt identifier, expanded recovery disclosure, passive-guidance warning, and source-state rows visible. Wide tables use native horizontal overflow; failure/stale state text is not removed at compact width. Long source labels remain readable through table scrolling rather than being silently elided from the data model.

The desktop Data Health render keeps the overall blocked/review signal, safe-loader controls, and receipt-health heading in the visual hierarchy. The controlled matrix render clearly labels every source as a synthetic fixture.

Known compact caveat: Streamlit data tables may require horizontal scrolling to see all timestamps and relationship columns. The explicit validation/status callout and recovery state remain visible before that scroll.
