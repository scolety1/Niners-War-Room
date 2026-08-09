from __future__ import annotations

from pathlib import Path

from scripts.validate_admitted_redraft_2026 import _sanity


def test_validation_script_exists_and_sanity_contract_is_callable() -> None:
    assert Path("scripts/validate_admitted_redraft_2026.py").is_file()
    assert callable(_sanity)
