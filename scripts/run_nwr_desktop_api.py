"""Run the authenticated loopback API used by the NWR desktop shell."""

from __future__ import annotations

import argparse
import hmac
import json
import os
import sys
from collections.abc import Sequence
from io import TextIOBase
from pathlib import Path

SCRIPT_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(SCRIPT_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_REPO_ROOT))

from src.application.desktop_facade import DesktopBackendFacade  # noqa: E402
from src.desktop_api.server import (  # noqa: E402
    STARTUP_PROTOCOL,
    create_desktop_api_server,
    validate_startup_proof_key,
    validate_token,
)

MAX_STARTUP_CREDENTIAL_BYTES = 4096
_CREDENTIAL_KEYS = frozenset({"apiToken", "startupProofKey"})


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the local Niners War Room desktop API.",
    )
    parser.add_argument("--host", default="127.0.0.1", help="Explicit loopback IP address.")
    parser.add_argument("--port", required=True, type=int, help="Loopback TCP port (0-65535).")
    parser.add_argument("--mode", required=True, choices=("dynasty", "redraft"))
    parser.add_argument("--repo-root", required=True, type=Path)
    return parser


def read_startup_credentials(stream: TextIOBase) -> tuple[str, str]:
    """Read one bounded private JSON line inherited from the desktop parent."""

    line = stream.readline(MAX_STARTUP_CREDENTIAL_BYTES + 1)
    if not line or len(line.encode("utf-8")) > MAX_STARTUP_CREDENTIAL_BYTES:
        raise ValueError("Desktop startup credentials are missing or too large.")
    if not line.endswith("\n"):
        raise ValueError("Desktop startup credentials must be a single newline-terminated record.")
    try:
        value = json.loads(line)
    except json.JSONDecodeError as exc:
        raise ValueError("Desktop startup credentials are invalid JSON.") from exc
    if not isinstance(value, dict) or set(value) != _CREDENTIAL_KEYS:
        raise ValueError("Desktop startup credentials have an invalid schema.")
    if not isinstance(value.get("apiToken"), str) or not isinstance(
        value.get("startupProofKey"), str
    ):
        raise ValueError("Desktop startup credentials must be strings.")
    api_token = validate_token(value.get("apiToken"))
    startup_proof_key = validate_startup_proof_key(value.get("startupProofKey"))
    if hmac.compare_digest(api_token, startup_proof_key):
        raise ValueError("Desktop API token and startup proof key must be distinct.")
    return api_token, startup_proof_key


def validate_repo_root(
    value: str | Path,
    *,
    frozen: bool | None = None,
) -> Path:
    """Validate a source checkout or the immutable resource root of a frozen build."""

    repo_root = Path(value).expanduser().resolve()
    if not repo_root.is_dir():
        raise ValueError("--repo-root must be an existing directory.")
    is_frozen = bool(getattr(sys, "frozen", False)) if frozen is None else frozen
    if is_frozen:
        if not (repo_root / "docs").is_dir():
            raise ValueError("--repo-root must contain bundled NWR resources.")
    elif not (repo_root / "src" / "services").is_dir():
        raise ValueError("--repo-root must be a Niners War Room repository checkout.")
    return repo_root


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        repo_root = validate_repo_root(args.repo_root)
        api_token, startup_proof_key = read_startup_credentials(sys.stdin)
        facade = DesktopBackendFacade(repo_root=repo_root, mode=args.mode)
        server = create_desktop_api_server(
            host=args.host,
            port=args.port,
            token=api_token,
            startup_proof_key=startup_proof_key,
            facade=facade,
        )
    except ValueError as exc:
        parser.error(str(exc))

    bound_host, bound_port = server.server_address[:2]
    print(
        json.dumps(
            {
                "host": str(bound_host),
                "mode": args.mode,
                "pid": os.getpid(),
                "port": int(bound_port),
                "protocol": STARTUP_PROTOCOL,
            },
            separators=(",", ":"),
            sort_keys=True,
        ),
        flush=True,
    )
    try:
        server.serve_forever(poll_interval=0.25)
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
