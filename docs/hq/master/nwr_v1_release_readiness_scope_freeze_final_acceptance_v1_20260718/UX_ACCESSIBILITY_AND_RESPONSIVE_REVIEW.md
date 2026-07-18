# UX, accessibility, and responsive review

## Automated browser matrix

The local in-app browser and repository/CDP tooling tested 59 registered routes plus the default root alias at:

- 375 Ã— 812;
- 768 Ã— 1024;
- 1440 Ã— 1000.

Each viewport passed 60/60 endpoints. Across 180 results there were zero missing expected primary surfaces, page-not-found states, DOM-visible tracebacks, uncaught Streamlit exceptions, root-level horizontal overflows, or missing semantic primary headings. Slowest endpoint observations were 3.659 s mobile, 3.973 s tablet, and 4.097 s desktop.

Navigation remains usable, primary actions remain present, and dense content stays bounded rather than widening the root. Trust, failure, gated, stale, review-only, and unavailable context remains textual at compact width.

## Accessibility

The shared page header now emits a semantic `h1`; Player Compare's redundant screen-reader-only heading was removed. Evidence Review's navigation and page title agree. A compact-width audit of all 18 visible routes found exactly one primary heading per route, no visible unnamed buttons, and no unnamed disclosure controls. The only raw unnamed input was Streamlit's visually clipped, `tabindex=-1` file-input implementation behind its named uploader control.

Existing focused tests cover Player Compare and Live/Mock Draft keyboard and compact behavior. State is presented in text and not only color. No duplicate primary action or trust banner was observed.

This is automated release-critical acceptance, not full screen-reader certification. Recommended manual follow-up: keyboard-only traversal with the supported browser, NVDA/JAWS announcement checks for Streamlit data tables and upload controls, focus-return checks after reruns, and contrast inspection under user display settings.
