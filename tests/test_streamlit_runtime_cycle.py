from __future__ import annotations

import os
import signal
import socket
import subprocess
from pathlib import Path

import pytest

from scripts.streamlit_runtime_cycle import (
    FATAL_MARKERS,
    CycleResult,
    assert_port_available,
    build_streamlit_command,
    fatal_markers_in_logs,
    graceful_shutdown,
    wait_for_shutdown_trigger,
)


class _Process:
    pid = 1234

    def __init__(self, *, timeout: bool = False) -> None:
        self.timeout = timeout
        self.signals: list[int] = []
        self.terminated = False
        self.killed = False

    def poll(self) -> int | None:
        return None

    def send_signal(self, sig: int) -> None:
        self.signals.append(sig)

    def terminate(self) -> None:
        self.terminated = True

    def kill(self) -> None:
        self.killed = True

    def wait(self, timeout: float | None = None) -> int:
        if self.timeout and not self.terminated:
            raise subprocess.TimeoutExpired("streamlit", timeout)
        return 0


def _cycle_result(*, exit_code: int = 0) -> CycleResult:
    return CycleResult(
        cycle=1,
        pid=1234,
        startup_seconds=0.1,
        shutdown_seconds=0.1,
        exit_code=exit_code,
        forced_cleanup=False,
        port_released=True,
        fatal_markers=(),
        stdout_log="stdout.log",
        stderr_log="stderr.log",
    )


def test_command_uses_direct_python_module_without_a_shell_wrapper() -> None:
    python = Path("C:/NWR/rtv/Scripts/python.exe")
    command = build_streamlit_command(python, host="127.0.0.1", port=8520)

    assert Path(command[0]).as_posix().lower().endswith("/nwr/rtv/scripts/python.exe")
    assert command[1:4] == ("-m", "streamlit", "run")
    assert "uv" not in " ".join(command).lower()
    assert "--server.address" in command
    assert "127.0.0.1" in command
    assert "8520" in command


def test_occupied_port_is_rejected_before_start() -> None:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        listener.listen()
        port = listener.getsockname()[1]

        with pytest.raises(RuntimeError, match="already has a listener"):
            assert_port_available("127.0.0.1", port)


def test_graceful_shutdown_uses_a_console_signal_without_forcing() -> None:
    process = _Process()

    result = graceful_shutdown(process, timeout_seconds=1.0)

    expected_signal = signal.CTRL_BREAK_EVENT if os.name == "nt" else signal.SIGINT
    assert process.signals == [expected_signal]
    assert not process.terminated
    assert not process.killed
    assert not result.forced_cleanup


def test_timeout_cleanup_is_visible_and_fails_the_reliability_contract() -> None:
    process = _Process(timeout=True)

    result = graceful_shutdown(process, timeout_seconds=0.01)

    assert process.terminated
    assert result.forced_cleanup


def test_nonzero_graceful_exit_fails_the_reliability_contract() -> None:
    assert _cycle_result().passed
    assert not _cycle_result(exit_code=1).passed


def test_interactive_cycle_waits_for_an_explicit_shutdown_trigger(tmp_path: Path) -> None:
    trigger = tmp_path / "shutdown.trigger"
    trigger.write_text("complete", encoding="utf-8")

    wait_for_shutdown_trigger(trigger, _Process(), timeout_seconds=0.1)


def test_interactive_cycle_rejects_an_early_process_exit(tmp_path: Path) -> None:
    process = _Process()
    process.poll = lambda: 7  # type: ignore[method-assign]

    with pytest.raises(RuntimeError, match="exited before the shutdown trigger"):
        wait_for_shutdown_trigger(
            tmp_path / "missing.trigger",
            process,
            timeout_seconds=0.1,
        )


def test_fatal_stderr_markers_are_never_suppressed(tmp_path: Path) -> None:
    stdout = tmp_path / "stdout.log"
    stderr = tmp_path / "stderr.log"
    stdout.write_text("normal output", encoding="utf-8")
    stderr.write_text("\n".join(FATAL_MARKERS), encoding="utf-8")

    assert fatal_markers_in_logs(stdout, stderr) == FATAL_MARKERS
