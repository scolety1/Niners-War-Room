# Validation Results

Result: PASS.

## Source and Git gates

- Fetch all remotes/prune: PASS.
- Live HQ resolved to e949c5647001f84dba29195c589e27d923722ea1: PASS.
- Remote advance from expected HQ: none.
- Source ref equals d8520f2056aedb3870406295e678610769b3c681: PASS.
- Source parent equals live HQ; one ahead/zero behind: PASS.
- Source worktree clean: PASS.
- Exact inventory: 31 paths; 1 modified, 30 added; no unrelated path.
- Git diff --check baseline/source: PASS.
- Source packet Git-blob manifest: 26/26 entries pass.

## Semantic and static gates

- Canonical semantic SHA-256 reproduced baseline/source: PASS.
- Records/fields: 2/84 in both.
- Full canonical payload equality: PASS.
- Helper presentational-only review: PASS.
- Page selection/data/field behavior review: PASS.
- Decision Trust Strip component/service/glossary object equality: PASS.
- Trading Lab/navigation/protected/frozen object checks: PASS.
- Read-only compile of app/pages/22_player_compare_v1.py, app/components/player_compare_accessibility.py, tests/fixtures/player_compare_accessibility_fixture.py, and tests/test_player_compare_accessibility_compact.py: PASS.
- Ruff --no-cache on the same four files: PASS.

## Tests

Focused command: pytest tests/test_player_compare_accessibility_compact.py.

Focused result: 22 passed.

Scoped regression command covered:

- test_player_compare_safe_context_upgrade.py
- test_player_compare_nflverse_context.py
- test_player_compare_display_only_ngs.py
- test_player_compare_decision_service.py
- test_player_comparison_service.py
- test_decision_trust_strip_surfaces.py
- test_decision_trust_strip_service.py
- test_decision_trust_strip_render.py
- test_injury_availability_context_service.py
- test_navigation_compression.py
- test_original_doc_remaining_ux_tools.py
- test_drafting_mode_cockpit_page.py
- test_import_validation.py

Scoped result: 94 passed in 8.47 seconds. No test was skipped, weakened, changed, marked xfail, or deselected.

The first scoped attempt produced 93 passes and one environmental failure because explicit py_compile attempted to write __pycache__ in the read-only worktree. A retry with a short writable PYTHONPYCACHEPREFIX and pytest basetemp passed all 94 tests; a separate read-only compile() gate also passed. This was not an application/test failure.

## Browser and render gates

- Real route smoke: PASS at 320x700, 375x812, 768x1024, and 1440x1000.
- Document/main horizontal overflow: none at every viewport.
- Desktop two-column selectors: PASS.
- Compact 44px touch targets: PASS.
- Accessible names/roles and A/B text distinction: PASS.
- DOM/reading order: PASS.
- Visible focus: 3px solid rgb(0, 95, 204), offset 2px.
- Native disclosure expansion/containment: PASS.
- No trap, hover-only action, custom shortcut, or interception code: PASS.
- Source JPEG validity/dimensions/classification: PASS with documented desktop storage caveat.
- Representative required states: PASS through real route plus clearly marked test-only fixtures/unit cases.

Pre-existing warnings/caveats are separated in KNOWN_CAVEAT_DIFFERENTIAL.md. No unrelated warning or route behavior was repaired.
