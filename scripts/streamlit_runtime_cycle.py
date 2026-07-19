from __future__ import annotations

import argparse
import json
import os
import signal
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Protocol

FATAL_MARKERS = (
    "_PySemaphore_Wakeup",
    "ReleaseSemaphore failed",
    "ERR_CONNECTION_RESET",
)


class ProcessLike(Protocol):
    pid: int

    def poll(self) -> int | None: ...

    def send_signal(self, sig: int) -> None: ...

    def terminate(self) -> None: ...

    def kill(self) -> None: ...

    def wait(self, timeout: float | None = None) -> int: ...


@dataclass(frozen=True)
class ShutdownResult:
    exit_code: int
    forced_cleanup: bool
    signal_name: str


@dataclass(frozen=True)
class CycleResult:
    cycle: int
    pid: int
    startup_seconds: float
    shutdown_seconds: float
    exit_code: int
    forced_cleanup: bool
    port_released: bool
    fatal_markers: tuple[str, ...]
    stdout_log: str
    stderr_log: str

    @property
    def passed(self) -> bool:
        return (
            self.exit_code == 0
            and not self.forced_cleanup
            and self.port_released
            and not self.fatal_markers
        )


def build_streamlit_command(python: Path, *, host: str, port: int) -> tuple[str, ...]:
    return (
        str(python),
        "-m",
        "streamlit",
        "run",
        "app/main.py",
        "--server.address",
        host,
        "--server.port",
        str(port),
        "--server.headless",
        "true",
        "--browser.gatherUsageStats",
        "false",
    )


def port_is_listening(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=0.2):
            return True
    except OSError:
        return False


def assert_port_available(host: str, port: int) -> None:
    if port_is_listening(host, port):
        raise RuntimeError(f"Refusing to start: {host}:{port} already has a listener.")


def _creation_flags() -> int:
    if os.name != "nt":
        return 0
    return int(getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0))


def start_streamlit(
    python: Path,
    repo_root: Path,
    *,
    host: str,
    port: int,
    stdout_log: Path,
    stderr_log: Path,
) -> subprocess.Popen[str]:
    assert_port_available(host, port)
    stdout_log.parent.mkdir(parents=True, exist_ok=True)
    with stdout_log.open("w", encoding="utf-8") as stdout_handle, stderr_log.open(
        "w", encoding="utf-8"
    ) as stderr_handle:
        return subprocess.Popen(
            build_streamlit_command(python, host=host, port=port),
            cwd=repo_root,
            stdin=subprocess.DEVNULL,
            stdout=stdout_handle,
            stderr=stderr_handle,
            text=True,
            shell=False,
            creationflags=_creation_flags(),
        )


def wait_for_http(
    url: str,
    process: ProcessLike,
    *,
    timeout_seconds: float,
) -> None:
    deadline = time.monotonic() + timeout_seconds
    last_error = "not attempted"
    while time.monotonic() < deadline:
        exit_code = process.poll()
        if exit_code is not None:
            raise RuntimeError(f"Streamlit exited before readiness with code {exit_code}.")
        try:
            with urllib.request.urlopen(url, timeout=1.0) as response:
                if response.status == 200:
                    return
                last_error = f"HTTP {response.status}"
        except (OSError, urllib.error.URLError) as exc:
            last_error = str(exc)
        time.sleep(0.1)
    raise TimeoutError(f"Timed out waiting for {url}: {last_error}")


def graceful_shutdown(process: ProcessLike, *, timeout_seconds: float) -> ShutdownResult:
    existing_exit = process.poll()
    if existing_exit is not None:
        return ShutdownResult(existing_exit, False, "already-exited")

    if os.name == "nt":
        shutdown_signal = signal.CTRL_BREAK_EVENT
        signal_name = "CTRL_BREAK_EVENT"
    else:
        shutdown_signal = signal.SIGINT
        signal_name = "SIGINT"
    process.send_signal(shutdown_signal)

    try:
        return ShutdownResult(process.wait(timeout=timeout_seconds), False, signal_name)
    except subprocess.TimeoutExpired:
        process.terminate()
        try:
            exit_code = process.wait(timeout=5.0)
        except subprocess.TimeoutExpired:
            process.kill()
            exit_code = process.wait(timeout=5.0)
        return ShutdownResult(exit_code, True, signal_name)


def wait_for_port_release(host: str, port: int, *, timeout_seconds: float) -> bool:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if not port_is_listening(host, port):
            return True
        time.sleep(0.1)
    return not port_is_listening(host, port)


def wait_for_shutdown_trigger(
    path: Path,
    process: ProcessLike,
    *,
    timeout_seconds: float,
) -> None:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        exit_code = process.poll()
        if exit_code is not None:
            raise RuntimeError(
                f"Streamlit exited before the shutdown trigger with code {exit_code}."
            )
        if path.is_file():
            return
        time.sleep(0.1)
    raise TimeoutError(f"Timed out waiting for shutdown trigger: {path}")


def fatal_markers_in_logs(*paths: Path) -> tuple[str, ...]:
    text = "\n".join(
        path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""
        for path in paths
    )
    return tuple(marker for marker in FATAL_MARKERS if marker in text)


def run_cycle(
    cycle: int,
    *,
    python: Path,
    repo_root: Path,
    host: str,
    port: int,
    evidence_dir: Path,
    startup_timeout: float,
    shutdown_timeout: float,
    ready_file: Path | None = None,
    shutdown_trigger: Path | None = None,
    interaction_timeout: float = 300.0,
) -> CycleResult:
    stdout_log = evidence_dir / f"cycle-{cycle}.stdout.log"
    stderr_log = evidence_dir / f"cycle-{cycle}.stderr.log"
    startup_started = time.monotonic()
    process = start_streamlit(
        python,
        repo_root,
        host=host,
        port=port,
        stdout_log=stdout_log,
        stderr_log=stderr_log,
    )
    try:
        wait_for_http(
            f"http://{host}:{port}/",
            process,
            timeout_seconds=startup_timeout,
        )
        startup_seconds = time.monotonic() - startup_started
        if ready_file is not None:
            ready_file.parent.mkdir(parents=True, exist_ok=True)
            ready_file.write_text(
                json.dumps(
                    {
                        "pid": process.pid,
                        "url": f"http://{host}:{port}/",
                        "cycle": cycle,
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
        if shutdown_trigger is not None:
            wait_for_shutdown_trigger(
                shutdown_trigger,
                process,
                timeout_seconds=interaction_timeout,
            )
    except BaseException:
        graceful_shutdown(process, timeout_seconds=shutdown_timeout)
        raise

    shutdown_started = time.monotonic()
    shutdown = graceful_shutdown(process, timeout_seconds=shutdown_timeout)
    shutdown_seconds = time.monotonic() - shutdown_started
    port_released = wait_for_port_release(host, port, timeout_seconds=5.0)
    markers = fatal_markers_in_logs(stdout_log, stderr_log)
    return CycleResult(
        cycle=cycle,
        pid=process.pid,
        startup_seconds=round(startup_seconds, 3),
        shutdown_seconds=round(shutdown_seconds, 3),
        exit_code=shutdown.exit_code,
        forced_cleanup=shutdown.forced_cleanup,
        port_released=port_released,
        fatal_markers=markers,
        stdout_log=str(stdout_log),
        stderr_log=str(stderr_log),
    )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify owned Windows Streamlit startup and graceful shutdown cycles."
    )
    parser.add_argument("--python", type=Path, default=Path(sys.executable))
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8520)
    parser.add_argument("--cycles", type=int, default=2)
    parser.add_argument("--startup-timeout", type=float, default=30.0)
    parser.add_argument("--shutdown-timeout", type=float, default=15.0)
    parser.add_argument("--ready-file", type=Path)
    parser.add_argument("--shutdown-trigger", type=Path)
    parser.add_argument("--interaction-timeout", type=float, default=300.0)
    parser.add_argument("--evidence-dir", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    python = args.python.resolve()
    repo_root = args.repo_root.resolve()
    if not python.is_file():
        raise FileNotFoundError(python)
    if not (repo_root / "app" / "main.py").is_file():
        raise FileNotFoundError(repo_root / "app" / "main.py")
    if args.cycles < 1:
        raise ValueError("--cycles must be at least 1.")
    if (args.ready_file is None) != (args.shutdown_trigger is None):
        raise ValueError("--ready-file and --shutdown-trigger must be supplied together.")
    if args.cycles != 1 and args.ready_file is not None:
        raise ValueError("Interactive ready/trigger orchestration supports exactly one cycle.")

    results = [
        run_cycle(
            cycle,
            python=python,
            repo_root=repo_root,
            host=args.host,
            port=args.port,
            evidence_dir=args.evidence_dir,
            startup_timeout=args.startup_timeout,
            shutdown_timeout=args.shutdown_timeout,
            ready_file=args.ready_file.resolve() if args.ready_file else None,
            shutdown_trigger=(
                args.shutdown_trigger.resolve() if args.shutdown_trigger else None
            ),
            interaction_timeout=args.interaction_timeout,
        )
        for cycle in range(1, args.cycles + 1)
    ]
    payload = {
        "command": "direct-python-module",
        "python": str(python),
        "repo_root": str(repo_root),
        "host": args.host,
        "port": args.port,
        "cycles": [asdict(result) | {"passed": result.passed} for result in results],
        "passed": all(result.passed for result in results),
    }
    print(json.dumps(payload, indent=2))
    return 0 if payload["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
