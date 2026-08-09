from __future__ import annotations

from pathlib import Path

from scripts.build_nwr_redraft_engine_v1 import VALIDATION_SOURCE_FILES, _source_fingerprint


def test_source_fingerprint_is_checkout_line_ending_independent(tmp_path: Path) -> None:
    for index, relative in enumerate(VALIDATION_SOURCE_FILES):
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(f"source-{index}\nline-two\n".encode("utf-8"))
    lf_fingerprint = _source_fingerprint(tmp_path)

    for index, relative in enumerate(VALIDATION_SOURCE_FILES):
        (tmp_path / relative).write_bytes(
            f"source-{index}\r\nline-two\r\n".encode("utf-8")
        )

    assert _source_fingerprint(tmp_path) == lf_fingerprint
