# Accessibility Tree and Keyboard Review

Result: PASS, with the manual assistive-technology recommendation stated below.

The real route exposes unique accessible combobox names Player A selector and Player B selector. Optional extra players retains its existing accessible name. Headings label Choose players, Selected-player context, Visible Context Summary, Evidence caveats and trust context, How to use this comparison, and Secondary comparison details. Per-player disclosures are uniquely named Evidence details — player name. Existing native dataframes retain table/tool labels.

Player A and Player B are stated in text, including selected/not-selected text, so slot identity never depends on color. Missing, stale, gated, unavailable, identity-exception, source-exception, and not-enough-information states are text labels; any marker/color is supplemental.

Controls remain native Streamlit comboboxes, multiselect, tabs, buttons, dataframe tools, and details/summary disclosures. Source inspection found no keydown/keypress handler, custom shortcut, hover-only action, focus loop, focus trap, or keyboard interception. No unsupported shortcut was added.

At 375x812, a focused Player A combobox and focused evidence summary both computed to a 3px solid rgb(0, 95, 204) outline with a 2px offset. Focus remains visible at compact width.

The real disclosure was uniquely addressed and expanded by its native summary; the canonical table appeared within the page container. Synthesized Enter/Space events from the in-app browser backend did not provide a reliable toggle trace. Acceptance therefore rests on unchanged native details/summary semantics, native focusability, visible focus, no interception code, and focused tests. A manual screen-reader and physical-keyboard pass remains recommended for assistive-technology behavior.

No programmatic focus restoration was implemented or claimed.
