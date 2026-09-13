"""Real packaging-content scans for the privacy-safe governance-receipt
architecture (NWR Post-UI Product V1, Worker B).

These tests do not merely assert "the private receipt is excluded" as
logic -- they run the actual privacy guard as a subprocess, load the actual
Tauri resource map that decides what ships inside the distributable
installer, and read the actual bytes of every file that map points at.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

from src.services.governance_release_summary_service import OWNER_MARKERS

REPO_ROOT = Path(__file__).resolve().parents[1]
DESKTOP_ROOT = REPO_ROOT / "desktop"
REDRAFT_TAURI_ROOT = DESKTOP_ROOT / "apps" / "redraft" / "src-tauri"
LIB_RS = DESKTOP_ROOT / "crates" / "nwr-desktop-runtime" / "src" / "lib.rs"
CHECK_SCRIPT = DESKTOP_ROOT / "scripts" / "check-resource-allowlists.mjs"

PRIVATE_RECEIPT_RELATIVE = (
    "docs/hq/model/nwr_redraft_2026_freeze_v7_bundled_seed_v1_20260912/NWR_DATA_GOVERNANCE.json"
)
RELEASE_SUMMARY_RELATIVE = (
    "docs/hq/model/nwr_redraft_2026_freeze_v7_bundled_seed_v1_20260912/"
    "NWR_DATA_GOVERNANCE_RELEASE_SUMMARY.json"
)


def _node_available() -> bool:
    try:
        subprocess.run(["node", "--version"], capture_output=True, check=True)
        return True
    except (OSError, subprocess.CalledProcessError):
        return False


def _redraft_windows_resource_map() -> dict[str, str]:
    conf = json.loads((REDRAFT_TAURI_ROOT / "tauri.windows.conf.json").read_text(encoding="utf-8"))
    return conf["bundle"]["resources"]


def _resolve_resource_source(source_relative: str) -> Path:
    # Sources are declared relative to the src-tauri directory, e.g.
    # "../../../../docs/hq/...". Mirrors check-resource-allowlists.mjs's own
    # resolution exactly.
    return (REDRAFT_TAURI_ROOT / source_relative).resolve()


# ---------------------------------------------------------------------------
# 1. The private receipt is never included in the packaging allowlist/bundle
#    contents -- a real content scan, not "should be excluded" logic.
# ---------------------------------------------------------------------------


def test_tauri_windows_resource_map_excludes_private_receipt_and_includes_summary() -> None:
    resources = _redraft_windows_resource_map()
    destinations = set(resources.values())
    assert PRIVATE_RECEIPT_RELATIVE not in destinations, (
        "the full private governance receipt must never be a bundled Windows resource"
    )
    assert RELEASE_SUMMARY_RELATIVE in destinations, (
        "the release-safe summary must be the bundled governance resource instead"
    )


def test_every_bundled_redraft_resource_file_contains_no_owner_marker() -> None:
    """The real content scan: read the actual bytes of every file the
    Windows bundle will package for `redraft`, and assert none contain any
    known owner-identity marker string."""

    resources = _redraft_windows_resource_map()
    assert resources, "redraft resource map must not be empty"
    for source_relative in resources:
        resolved = _resolve_resource_source(source_relative)
        assert resolved.is_file(), f"declared bundled resource does not exist: {resolved}"
        body = resolved.read_bytes()
        for marker in OWNER_MARKERS:
            assert marker.encode("utf-8") not in body, (
                f"bundled resource {resolved} contains owner marker {marker!r}"
            )


def test_release_summary_resource_file_itself_has_no_owner_marker() -> None:
    resolved = REPO_ROOT / RELEASE_SUMMARY_RELATIVE
    assert resolved.is_file()
    body = resolved.read_text(encoding="utf-8")
    for marker in OWNER_MARKERS:
        assert marker not in body


@pytest.mark.skipif(not _node_available(), reason="node is required to run the real privacy guard")
def test_real_check_resources_guard_passes_via_subprocess() -> None:
    """Runs the ACTUAL `npm run check:resources` script (unmodified) as a
    subprocess -- the strongest available proof that the real, unweakened
    guard accepts the current bundle."""

    result = subprocess.run(
        ["node", str(CHECK_SCRIPT)],
        cwd=str(DESKTOP_ROOT),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"check-resource-allowlists.mjs failed:\nstdout={result.stdout}\nstderr={result.stderr}"
    )
    assert "exact and privacy-bounded" in result.stdout


def test_check_resource_allowlists_script_itself_is_unmodified_in_logic() -> None:
    """Guards against a future pass silently weakening the guard (e.g. an
    exception/whitelist for one file) instead of fixing the architecture.
    Asserts the guard's own owner-marker list still matches this module's
    copy, and that it still contains no per-file exception mechanism."""

    source = CHECK_SCRIPT.read_text(encoding="utf-8")
    match = re.search(r'const ownerMarkers = \[(.*?)\];', source, re.DOTALL)
    assert match, "could not locate ownerMarkers in check-resource-allowlists.mjs"
    markers_in_script = tuple(
        literal.strip('"')
        for literal in re.findall(r'"([^"]+)"', match.group(1))
    )
    assert markers_in_script == OWNER_MARKERS, (
        "check-resource-allowlists.mjs's ownerMarkers list has diverged from "
        "governance_release_summary_service.OWNER_MARKERS"
    )
    assert "assertNoOwnerMarkers" in source, "the guard must still scan every allowlisted file's bytes"
    redraft_block = re.search(r'redraft: \[(.*?)\],\n\};', source, re.DOTALL)
    assert redraft_block, "could not locate the redraft allowlist block"
    assert "NWR_DATA_GOVERNANCE.json\"" not in redraft_block.group(1), (
        "the redraft allowlist must not name the full private receipt"
    )
    assert "NWR_DATA_GOVERNANCE_RELEASE_SUMMARY.json" in redraft_block.group(1)


# ---------------------------------------------------------------------------
# 2. The Rust release-build startup gate must name the exact same file set
#    as the npm allowlist / tauri.windows.conf.json -- the class of bug that
#    caused a real, previously-undiscovered stale-path drift (see the design
#    doc), fixed as part of this same pass. This test prevents recurrence.
# ---------------------------------------------------------------------------


def test_rust_required_resource_files_match_the_npm_allowlist() -> None:
    rust_source = LIB_RS.read_text(encoding="utf-8")
    match = re.search(
        r'const REDRAFT_RESOURCE_FILES: \[&str; \d+\] = \[(.*?)\];',
        rust_source,
        re.DOTALL,
    )
    assert match, "could not locate REDRAFT_RESOURCE_FILES in lib.rs"
    rust_files = set(re.findall(r'"([^"]+)"', match.group(1)))

    resources = _redraft_windows_resource_map()
    npm_files = set(resources.values())

    assert rust_files == npm_files, (
        "Rust release-build resource gate and the npm resource allowlist have "
        f"drifted apart.\nRust only: {rust_files - npm_files}\n"
        f"npm only: {npm_files - rust_files}"
    )
    assert PRIVATE_RECEIPT_RELATIVE not in rust_files
    assert RELEASE_SUMMARY_RELATIVE in rust_files
