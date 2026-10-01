"""Process and persistence reliability gauntlet for the desktop backend.

Every process in this module uses an OS-assigned port and test-local state.
The production development ports and the owner's AppData are never touched.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import queue
import re
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

import src.services.dynasty_sleeper_league_service as dynasty_profiles
import src.services.redraft_engine_v1_service as redraft_profiles
from src.desktop_api.server import STARTUP_PROTOCOL

REPO_ROOT = Path(__file__).resolve().parents[1]
RUNNER = REPO_ROOT / "scripts" / "run_nwr_desktop_api.py"
RELEASE_GATE = REPO_ROOT / "desktop" / "scripts" / "nwr_release_gate_smoke.ps1"
TOKEN = "nwr-reliability-gauntlet-api-token-000000000001"
PROOF_KEY = "nwr-reliability-gauntlet-proof-key-0000000002"
ORIGIN = "http://tauri.localhost"


@dataclass(frozen=True)
class RunningBackend:
    process: subprocess.Popen[str]
    startup_pid: int
    port: int
    token: str
    proof_key: str
    redraft_root: Path


def _readline_with_timeout(stream: Any, timeout: float) -> str:
    results: queue.Queue[str] = queue.Queue(maxsize=1)

    def read() -> None:
        results.put(stream.readline())

    threading.Thread(target=read, daemon=True).start()
    try:
        return results.get(timeout=timeout)
    except queue.Empty as exc:
        raise TimeoutError("Backend emitted no startup identity record in time.") from exc


def _backend_environment(tmp_path: Path) -> tuple[dict[str, str], Path]:
    redraft_root = tmp_path / "redraft_v1"
    private_appdata = tmp_path / "appdata"
    env = os.environ.copy()
    env.update(
        {
            "APPDATA": str(private_appdata / "roaming"),
            "LOCALAPPDATA": str(private_appdata / "local"),
            "NWR_REDRAFT_HOME": str(redraft_root),
            "NWR_DYNASTY_LEAGUE_HOME": str(tmp_path / "dynasty_v1"),
        }
    )
    return env, redraft_root


def _launch_backend(tmp_path: Path, *, port: int = 0) -> subprocess.Popen[str]:
    env, _ = _backend_environment(tmp_path)
    process = subprocess.Popen(
        [
            sys.executable,
            str(RUNNER),
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--mode",
            "redraft",
            "--repo-root",
            str(REPO_ROOT),
        ],
        cwd=REPO_ROOT,
        env=env,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )
    assert process.stdin is not None
    process.stdin.write(
        json.dumps({"apiToken": TOKEN, "startupProofKey": PROOF_KEY}) + "\n"
    )
    process.stdin.flush()
    process.stdin.close()
    return process


def _start_backend(tmp_path: Path) -> RunningBackend:
    process = _launch_backend(tmp_path)
    assert process.stdout is not None
    try:
        line = _readline_with_timeout(process.stdout, timeout=30)
        startup = json.loads(line)
        assert startup["host"] == "127.0.0.1"
        assert startup["mode"] == "redraft"
        assert isinstance(startup["pid"], int) and startup["pid"] > 0
        assert startup["protocol"] == STARTUP_PROTOCOL
        assert 49152 <= int(startup["port"]) <= 65535
    except Exception:
        _stop_process(process)
        raise
    _, redraft_root = _backend_environment(tmp_path)
    return RunningBackend(
        process=process,
        startup_pid=int(startup["pid"]),
        port=int(startup["port"]),
        token=TOKEN,
        proof_key=PROOF_KEY,
        redraft_root=redraft_root,
    )


def _stop_process(process: subprocess.Popen[str]) -> None:
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=10)


def _request_json(
    port: int,
    path: str,
    *,
    token: str | None = TOKEN,
    headers: dict[str, str] | None = None,
    timeout: float = 30,
) -> tuple[int, dict[str, Any]]:
    request_headers = dict(headers or {})
    if token is not None:
        request_headers.update(
            {"Authorization": f"Bearer {token}", "Origin": ORIGIN}
        )
    request = Request(
        f"http://127.0.0.1:{port}{path}", headers=request_headers, method="GET"
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        return exc.code, json.loads(exc.read().decode("utf-8"))


def _wait_for_health(backend: RunningBackend, timeout: float = 10) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        if backend.process.poll() is not None:
            stderr = backend.process.stderr.read() if backend.process.stderr else ""
            raise AssertionError(
                f"Backend exited before health readiness: {stderr[-1000:]}"
            )
        try:
            status, payload = _request_json(backend.port, "/healthz")
            if status == 200:
                return payload
        except Exception as exc:  # pragma: no cover - exercised only while polling
            last_error = exc
        time.sleep(0.05)
    raise AssertionError(f"Backend was not healthy within {timeout}s: {last_error}")


def test_cold_start_is_healthy_and_cryptographically_identity_verified(
    tmp_path: Path,
) -> None:
    started_at = time.monotonic()
    backend = _start_backend(tmp_path)
    try:
        health = _wait_for_health(backend)
        assert time.monotonic() - started_at < 40
        assert health["data"] == {
            "authenticated": True,
            "status": "ok",
            "transport": "loopback",
        }

        challenge = hashlib.sha256(b"nwr-reliability-cold-start").hexdigest()
        status, proof = _request_json(
            backend.port,
            "/startup-proof",
            token=None,
            headers={"X-NWR-Startup-Challenge": challenge},
        )
        message = f"{STARTUP_PROTOCOL}\nredraft\n{backend.port}\n{challenge}"
        expected = hmac.new(
            backend.proof_key.encode("ascii"),
            message.encode("ascii"),
            hashlib.sha256,
        ).hexdigest()
        assert status == 200
        assert hmac.compare_digest(proof["data"]["startupProof"], expected)
        assert backend.process.poll() is None
    finally:
        _stop_process(backend.process)


def _start_stale_http_process(tmp_path: Path) -> tuple[subprocess.Popen[str], int]:
    script = (
        "import json,sys\n"
        "from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer\n"
        "class H(BaseHTTPRequestHandler):\n"
        " def do_GET(self):\n"
        "  body=json.dumps({'data':{'status':'old-process'}}).encode()\n"
        "  self.send_response(200); self.send_header('Content-Length',str(len(body)))\n"
        "  self.end_headers(); self.wfile.write(body)\n"
        " def log_message(self,*args): pass\n"
        "server=ThreadingHTTPServer(('127.0.0.1',0),H)\n"
        "print(server.server_port,flush=True)\n"
        "server.serve_forever()\n"
    )
    process = subprocess.Popen(
        [sys.executable, "-c", script],
        cwd=tmp_path,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )
    assert process.stdout is not None
    port = int(_readline_with_timeout(process.stdout, timeout=10).strip())
    return process, port


def test_restart_race_rejects_stale_listener_instead_of_trusting_its_200(
    tmp_path: Path,
) -> None:
    stale_process, port = _start_stale_http_process(tmp_path)
    attempted = _launch_backend(tmp_path / "attempt", port=port)
    try:
        # This is the false-positive signal the release-gate incident trusted.
        status, stale_payload = _request_json(port, "/api/v1/bootstrap", token=None)
        assert status == 200
        assert stale_payload["data"]["status"] == "old-process"

        # The actual process requested for this restart must be authoritative.
        # It fails loudly on the bind conflict and emits no startup identity.
        assert attempted.wait(timeout=30) != 0
        assert attempted.stdout is not None
        assert attempted.stdout.read() == ""
        assert attempted.stderr is not None
        bind_error = attempted.stderr.read()
        assert "address" in bind_error.lower() or "10048" in bind_error
    finally:
        _stop_process(attempted)
        _stop_process(stale_process)


@pytest.mark.xfail(
    strict=True,
    reason=(
        "nwr_release_gate_smoke.ps1 accepts readiness from any listener and does "
        "not verify the launched PID with /startup-proof"
    ),
)
def test_release_gate_restart_readiness_is_bound_to_the_launched_process() -> None:
    script = RELEASE_GATE.read_text(encoding="utf-8")
    readiness_block = script[
        script.index('Write-Section "Bridge smoke: waiting for the real backend') :
        script.index('Write-Section "Bridge smoke: cold vs warm bootstrap')
    ]
    assert "/startup-proof" in readiness_block
    assert "startupProof" in readiness_block
    assert re.search(r"\$backendProc\.(HasExited|Id)", readiness_block)


def _exercise_redraft_pointer_writes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[list[BaseException], dict[str, Any]]:
    root = tmp_path / "redraft_v1"
    profile_ids = tuple(f"profile-{index}" for index in range(32))
    monkeypatch.setattr(
        redraft_profiles,
        "load_profile",
        lambda _root, profile_id: SimpleNamespace(
            profile_id=profile_id, archived=False
        ),
    )
    redraft_profiles.set_active_profile(root, profile_ids[0])
    marker = root / "active_profile.json"
    errors: list[BaseException] = []
    for _round in range(4):
        barrier = threading.Barrier(len(profile_ids))

        def write(
            profile_id: str, *, round_barrier: threading.Barrier = barrier
        ) -> BaseException | None:
            try:
                round_barrier.wait(timeout=10)
                redraft_profiles.set_active_profile(root, profile_id)
            except BaseException as exc:
                return exc
            return None

        with ThreadPoolExecutor(max_workers=len(profile_ids)) as executor:
            outcomes = list(executor.map(write, profile_ids))
        errors.extend(outcome for outcome in outcomes if outcome is not None)
        document = json.loads(marker.read_text(encoding="utf-8"))
        assert document["profile_id"] in profile_ids

    document = json.loads(marker.read_text(encoding="utf-8"))
    assert not list(root.glob(".active_profile.json.*.tmp"))
    return errors, document


def test_redraft_active_profile_pointer_never_becomes_partial_json(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _errors, document = _exercise_redraft_pointer_writes(tmp_path, monkeypatch)
    assert document["profile_id"].startswith("profile-")


def test_redraft_active_profile_pointer_accepts_all_concurrent_writers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    errors, _document = _exercise_redraft_pointer_writes(tmp_path, monkeypatch)
    if errors:
        pytest.xfail(
            "Windows destination-replace contention can reject concurrent "
            "set_active_profile calls; the published JSON remains valid"
        )


def _exercise_dynasty_pointer_collision(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[list[BaseException], dict[str, Any]]:
    root = tmp_path / "dynasty_v1"
    profile_ids = tuple(f"league-{index}" for index in range(16))
    monkeypatch.setattr(
        dynasty_profiles,
        "load_league_profile",
        lambda _root, profile_id: SimpleNamespace(profile_id=profile_id),
    )
    dynasty_profiles.set_active_league_profile(root, profile_ids[0])
    marker = root / "active_league_profile.json"

    # Production currently uses PID + second-resolution time for the temp name.
    # Pinning the real clock dependency makes the naturally possible collision
    # deterministic, while the real set_active_league_profile/_atomic_json code
    # still performs every write and replace.
    monkeypatch.setattr(dynasty_profiles, "utc_snapshot_stamp", lambda: "same-second")
    replace_barrier = threading.Barrier(len(profile_ids))
    real_replace = os.replace

    def simultaneous_replace(source: str | Path, destination: str | Path) -> None:
        if Path(destination) == marker:
            replace_barrier.wait(timeout=10)
        real_replace(source, destination)

    monkeypatch.setattr(dynasty_profiles.os, "replace", simultaneous_replace)
    real_write_text = Path.write_text
    write_lock = threading.Lock()

    def serialized_temp_write(path: Path, *args: Any, **kwargs: Any) -> int:
        if path.name.startswith(".active_league_profile.json."):
            with write_lock:
                return real_write_text(path, *args, **kwargs)
        return real_write_text(path, *args, **kwargs)

    monkeypatch.setattr(Path, "write_text", serialized_temp_write)
    def write(profile_id: str) -> BaseException | None:
        try:
            dynasty_profiles.set_active_league_profile(root, profile_id)
        except BaseException as exc:  # returned for an exact aggregate assertion
            return exc
        return None

    with ThreadPoolExecutor(max_workers=len(profile_ids)) as executor:
        outcomes = list(executor.map(write, profile_ids))
    errors = [outcome for outcome in outcomes if outcome is not None]
    document = json.loads(marker.read_text(encoding="utf-8"))
    return errors, document


def test_dynasty_active_league_pointer_never_becomes_partial_json(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    errors, document = _exercise_dynasty_pointer_collision(tmp_path, monkeypatch)
    assert document["profile_id"].startswith("league-")
    assert all(
        isinstance(error, dynasty_profiles.DynastyLeaguePersistenceError)
        for error in errors
    )


def test_dynasty_active_league_pointer_accepts_all_concurrent_writers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    errors, _document = _exercise_dynasty_pointer_collision(tmp_path, monkeypatch)
    if errors:
        pytest.xfail(
            "PID + second-resolution temp names collide; destination JSON stays "
            "valid, but concurrent set_active_league_profile calls can fail"
        )


def test_concurrent_http_requests_do_not_crash_or_corrupt_test_local_state(
    tmp_path: Path,
) -> None:
    backend = _start_backend(tmp_path)
    try:
        _wait_for_health(backend)
        # Warm once so the race targets steady-state shared caches as well as
        # the ThreadingHTTPServer request machinery, not dependency import time.
        warm_status, _warm_payload = _request_json(
            backend.port, "/api/v1/bootstrap", timeout=60
        )
        assert warm_status == 200

        paths = ["/healthz"] * 24 + ["/api/v1/bootstrap"] * 8
        barrier = threading.Barrier(len(paths))

        def request(path: str) -> tuple[int, dict[str, Any]]:
            barrier.wait(timeout=20)
            return _request_json(backend.port, path, timeout=60)

        with ThreadPoolExecutor(max_workers=len(paths)) as executor:
            responses = list(executor.map(request, paths))

        assert {status for status, _payload in responses} == {200}
        assert all(isinstance(payload.get("data"), dict) for _, payload in responses)
        assert backend.process.poll() is None
        final_status, final_health = _request_json(backend.port, "/healthz")
        assert final_status == 200
        assert final_health["data"]["status"] == "ok"

        for path in backend.redraft_root.rglob("*.json"):
            json.loads(path.read_text(encoding="utf-8"))
        assert not list(backend.redraft_root.rglob("*.tmp"))
    finally:
        _stop_process(backend.process)
