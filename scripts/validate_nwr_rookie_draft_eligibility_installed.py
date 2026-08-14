"""Black-box acceptance for the installed NWR Dynasty sidecar and resources."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import queue
import subprocess
import tempfile
import threading
from http.client import HTTPConnection
from pathlib import Path
from typing import Any
from urllib.parse import quote

TOKEN = "nwr-installed-acceptance-token-20260814-ABCDEF"
PROOF_KEY = "nwr-installed-acceptance-proof-20260814-FEDCBA"
STRIBLING_ASSET_ID = "blocked-rookie:dezhaun-stribling"
EXPECTED_MANUAL_REVIEW = {
    "Carson Beck",
    "Colbie Young",
    "De'Zhaun Stribling",
    "Deion Burks",
    "Joe Royer",
    "Nicholas Singleton",
    "Oscar Delp",
}
EXPECTED_LIVE_RESOURCE_SHA256 = (
    "f4ae6106f5302c59f23d83a27c006a894c5660b3058a011e5b2f16c6a2c79ff9"
)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--install-root", required=True, type=Path)
    parser.add_argument("--timeout", type=float, default=120.0)
    return parser


def _readline(stream: Any, output: queue.Queue[str]) -> None:
    output.put(stream.readline())


def _request(
    port: int,
    method: str,
    path: str,
    *,
    body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    encoded = json.dumps(body).encode("utf-8") if body is not None else None
    headers = {
        "X-NWR-Desktop-Token": TOKEN,
        "Origin": "http://tauri.localhost",
    }
    if encoded is not None:
        headers["Content-Type"] = "application/json"
    connection = HTTPConnection("127.0.0.1", port, timeout=60)
    connection.request(method, path, body=encoded, headers=headers)
    response = connection.getresponse()
    raw = response.read()
    connection.close()
    payload = json.loads(raw) if raw else {}
    if response.status != 200:
        raise AssertionError(f"{method} {path} returned {response.status}: {payload}")
    if payload.get("mode") != "dynasty" or not isinstance(payload.get("data"), dict):
        raise AssertionError(f"{method} {path} returned an invalid Dynasty envelope")
    return payload["data"]


def _stop_process_tree(
    process: subprocess.Popen[str],
    *,
    worker_pid: int | None,
) -> None:
    process_ids = [pid for pid in dict.fromkeys((worker_pid, process.pid)) if pid]
    for process_id in process_ids:
        subprocess.run(
            ["taskkill", "/PID", str(process_id), "/T", "/F"],
            check=False,
            capture_output=True,
            text=True,
        )
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=10)


def _accept(installed_root: Path, *, timeout: float) -> dict[str, Any]:
    root = installed_root.expanduser().resolve()
    sidecar = root / "nwr-desktop-api.exe"
    live_resource = (
        root
        / "docs/hq/model/nwr_redraft_2026_rookie_projection_candidate_v1_20260809"
        / "CURRENT_2026_IDENTITY_AND_ROLE.csv"
    )
    if not sidecar.is_file() or not live_resource.is_file():
        raise FileNotFoundError("Installed Dynasty sidecar or live rookie resource is missing")
    live_hash = file_sha256(live_resource)
    if live_hash != EXPECTED_LIVE_RESOURCE_SHA256:
        raise AssertionError(f"Live rookie resource hash mismatch: {live_hash}")

    with tempfile.TemporaryDirectory(prefix="nwr-installed-rookie-acceptance-") as temp:
        temp_root = Path(temp)
        environment = dict(os.environ)
        environment.update(
            {
                "NWR_DESKTOP_STATE_DIR": str(temp_root / "state"),
                "NWR_DESKTOP_LOG_DIR": str(temp_root / "logs"),
                "NWR_PERSONAL_WORKSPACE_ROOT": str(temp_root / "personal-workspace"),
                "NWR_REDRAFT_HOME": str(temp_root / "redraft"),
                "PYTHONDONTWRITEBYTECODE": "1",
                "PYTHONUNBUFFERED": "1",
            }
        )
        creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        process = subprocess.Popen(
            [
                str(sidecar),
                "--host",
                "127.0.0.1",
                "--port",
                "0",
                "--mode",
                "dynasty",
                "--repo-root",
                str(root),
            ],
            cwd=root,
            env=environment,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            creationflags=creation_flags,
        )
        worker_pid: int | None = None
        try:
            assert process.stdin is not None
            assert process.stdout is not None
            process.stdin.write(
                json.dumps({"apiToken": TOKEN, "startupProofKey": PROOF_KEY}) + "\n"
            )
            process.stdin.flush()
            process.stdin.close()

            reports: queue.Queue[str] = queue.Queue(maxsize=1)
            reader = threading.Thread(
                target=_readline,
                args=(process.stdout, reports),
                daemon=True,
            )
            reader.start()
            try:
                report_line = reports.get(timeout=timeout)
            except queue.Empty as exc:
                raise TimeoutError("Installed sidecar did not emit its startup report") from exc
            if not report_line:
                stderr = process.stderr.read() if process.stderr is not None else ""
                raise RuntimeError(f"Installed sidecar exited before startup: {stderr[-4000:]}")
            report = json.loads(report_line)
            worker_pid = int(report["pid"])
            if report.get("mode") != "dynasty" or report.get("protocol") != (
                "nwr-desktop-startup-v1"
            ):
                raise AssertionError(f"Unexpected startup report: {report}")
            port = int(report["port"])

            bootstrap = _request(port, "GET", "/api/v1/bootstrap")
            readiness = bootstrap["rookieReadiness"]
            normalized_position_counts = {
                str(key).upper(): value
                for key, value in readiness.get("positionCounts", {}).items()
            }
            expected_readiness = {
                "officialDrafted": 80,
                "exactIdentity": 80,
                "scored": 73,
                "manualReview": 7,
                "unresolved": 0,
                "missingFromRegistry": 0,
                "missingFromDraftablePool": 0,
                "duplicateAssetIds": 0,
            }
            for key, value in expected_readiness.items():
                if readiness.get(key) != value:
                    actual = readiness.get(key)
                    raise AssertionError(f"Readiness {key} was {actual!r}, not {value!r}")
            if normalized_position_counts != {"QB": 10, "RB": 12, "WR": 36, "TE": 22}:
                raise AssertionError(
                    f"Readiness position counts were {normalized_position_counts!r}"
                )
            if not readiness.get("ready"):
                raise AssertionError("Installed rookie readiness gate is not green")

            rookies = bootstrap["rookies"]
            if len(rookies) != 80:
                raise AssertionError(f"Installed Rookie Review has {len(rookies)} rows, not 80")
            if not all(
                row["searchable"] and row["selectable"] and row["draftable"]
                for row in rookies
            ):
                raise AssertionError("At least one official rookie is not owner-selectable")
            manual = [row for row in rookies if not row["modelScoreEligible"]]
            if {row["player"] for row in manual} != EXPECTED_MANUAL_REVIEW:
                raise AssertionError(
                    "Installed manual-review exception set does not match the seven"
                )
            if any(row["rank"] is not None or row["reviewScore"] is not None for row in manual):
                raise AssertionError(
                    "Installed manual-review assets received a fabricated rank or score"
                )

            options = bootstrap["assetOptions"]
            stribling = next(row for row in options if row["assetId"] == STRIBLING_ASSET_ID)
            puka = next(row for row in options if row["name"] == "Puka Nacua")
            expected_stribling = {
                "name": "De'Zhaun Stribling",
                "playerId": "00-0041035",
                "team": "SF",
                "position": "WR",
                "draftRound": 2,
                "overallPick": 33,
                "rank": None,
                "selectable": True,
                "searchable": True,
                "draftEligible": True,
                "modelScoreEligible": False,
                "blocked": False,
            }
            for key, value in expected_stribling.items():
                if stribling.get(key) != value:
                    raise AssertionError(
                        f"Installed Stribling {key} was {stribling.get(key)!r}, not {value!r}"
                    )

            detail = _request(
                port,
                "GET",
                f"/api/v1/dynasty/assets/{quote(STRIBLING_ASSET_ID, safe='')}",
            )
            comparison = _request(
                port,
                "POST",
                "/api/v1/dynasty/compare",
                body={"assetIds": [STRIBLING_ASSET_ID, puka["assetId"]]},
            )
            trade = _request(
                port,
                "POST",
                "/api/v1/dynasty/trades/evaluate",
                body={
                    "give": [STRIBLING_ASSET_ID],
                    "receive": [puka["assetId"]],
                    "teamWindow": "Balanced",
                },
            )

            if detail.get("nwrScore") is not None or detail.get("rank") is not None:
                raise AssertionError("Installed Stribling detail fabricated a score or rank")
            if detail.get("playerId") != "00-0041035" or detail.get("selectable") is not True:
                raise AssertionError("Installed Stribling detail lost exact identity/selectability")
            if not all("No admitted" in row["preferred"] for row in comparison["leans"]):
                raise AssertionError("Installed Compare fabricated a Stribling lean")
            if not any(
                "No admitted Rookie Review score" in warning
                for warning in comparison["warnings"]
            ):
                raise AssertionError("Installed Compare omitted the missing-score warning")
            if (
                trade.get("recommendation") != "INSUFFICIENT_EVIDENCE"
                or trade.get("preferredSide") != "No side"
                or trade.get("confidence") != "LOW"
                or "UNKNOWN, not zero" not in trade.get("mainUncertainty", "")
            ):
                raise AssertionError(f"Installed Trade did not fail closed: {trade}")

            return {
                "verdict": readiness["verdict"],
                "transport": "installed_sidecar_authenticated_loopback",
                "sidecarSha256": file_sha256(sidecar),
                "liveResourceSha256": live_hash,
                "officialDrafted": readiness["officialDrafted"],
                "positionCounts": normalized_position_counts,
                "scored": readiness["scored"],
                "manualReview": readiness["manualReview"],
                "missingFromDraftablePool": readiness["missingFromDraftablePool"],
                "manualReviewPlayers": sorted(EXPECTED_MANUAL_REVIEW),
                "stribling": {
                    "assetId": stribling["assetId"],
                    "playerId": stribling["playerId"],
                    "team": stribling["team"],
                    "position": stribling["position"],
                    "draftRound": stribling["draftRound"],
                    "overallPick": stribling["overallPick"],
                    "rank": stribling["rank"],
                    "selectable": stribling["selectable"],
                    "modelScoreEligible": stribling["modelScoreEligible"],
                },
                "compare": {
                    "preferred": [row["preferred"] for row in comparison["leans"]],
                    "warnings": comparison["warnings"],
                },
                "trade": {
                    "recommendation": trade["recommendation"],
                    "preferredSide": trade["preferredSide"],
                    "confidence": trade["confidence"],
                    "mainUncertainty": trade["mainUncertainty"],
                },
            }
        finally:
            _stop_process_tree(process, worker_pid=worker_pid)


def main() -> int:
    args = _parser().parse_args()
    result = _accept(args.install_root, timeout=args.timeout)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
