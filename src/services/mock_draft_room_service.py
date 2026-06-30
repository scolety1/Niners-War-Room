from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from src.services.draft_day_runtime_state_service import (
    RuntimeState,
    create_runtime_backup,
    load_runtime_state,
    runtime_paths,
    runtime_state_path,
    save_runtime_state,
)

DEFAULT_MOCK_DRAFT_ID = "mock_default"
DEFAULT_MOCK_DRAFT_NAME = "Mock Draft 1"
MOCK_MANIFEST_FILE = "mock_draft_sessions.json"


@dataclass(frozen=True)
class MockDraftSession:
    draft_id: str
    name: str
    created_at_utc: str
    updated_at_utc: str


@dataclass(frozen=True)
class MockDraftManifestHealth:
    status: str
    message: str
    path: Path
    session_count: int


def mock_manifest_path(root: Path | None = None) -> Path:
    return runtime_paths(root).state_dir / MOCK_MANIFEST_FILE


def default_mock_draft_session() -> MockDraftSession:
    now = _now()
    return MockDraftSession(
        draft_id=DEFAULT_MOCK_DRAFT_ID,
        name=DEFAULT_MOCK_DRAFT_NAME,
        created_at_utc=now,
        updated_at_utc=now,
    )


def load_mock_draft_sessions(root: Path | None = None) -> list[MockDraftSession]:
    path = mock_manifest_path(root)
    if not path.exists():
        return [default_mock_draft_session()]
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return [default_mock_draft_session()]
    if not isinstance(raw, list):
        return [default_mock_draft_session()]
    sessions = [_session_from_raw(row) for row in raw if isinstance(row, dict)]
    return sessions or [default_mock_draft_session()]


def mock_draft_manifest_health(root: Path | None = None) -> MockDraftManifestHealth:
    path = mock_manifest_path(root)
    if not path.exists():
        return MockDraftManifestHealth(
            status="MISSING_MANIFEST_USING_DEFAULT",
            message=(
                "No saved mock manifest exists yet; using the default mock session. "
                "This does not affect live Draft Cockpit state."
            ),
            path=path,
            session_count=1,
        )
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return MockDraftManifestHealth(
            status="UNREADABLE_MANIFEST_USING_DEFAULT",
            message=(
                "Saved mock manifest is unreadable; using the default mock session. "
                "Review the local manifest before deleting or restoring mock sessions."
            ),
            path=path,
            session_count=1,
        )
    if not isinstance(raw, list):
        return MockDraftManifestHealth(
            status="INVALID_MANIFEST_USING_DEFAULT",
            message=(
                "Saved mock manifest is not a session list; using the default mock session. "
                "Live Draft Cockpit state is separate and unchanged."
            ),
            path=path,
            session_count=1,
        )
    sessions = [_session_from_raw(row) for row in raw if isinstance(row, dict)]
    if not sessions:
        return MockDraftManifestHealth(
            status="EMPTY_MANIFEST_USING_DEFAULT",
            message=(
                "Saved mock manifest has no valid sessions; using the default mock session. "
                "Mock runtime state remains local practice context only."
            ),
            path=path,
            session_count=1,
        )
    return MockDraftManifestHealth(
        status="OK",
        message=f"Saved mock manifest loaded with {len(sessions)} session(s).",
        path=path,
        session_count=len(sessions),
    )


def save_mock_draft_sessions(
    sessions: list[MockDraftSession],
    root: Path | None = None,
) -> list[MockDraftSession]:
    normalized = sessions or [default_mock_draft_session()]
    path = mock_manifest_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(f".{uuid4().hex}.tmp")
    tmp.write_text(
        json.dumps([asdict(session) for session in normalized], indent=2, sort_keys=True),
        encoding="utf-8",
    )
    tmp.replace(path)
    return normalized


def create_mock_draft_session(
    name: str,
    *,
    root: Path | None = None,
) -> list[MockDraftSession]:
    sessions = load_mock_draft_sessions(root)
    now = _now()
    sessions.append(
        MockDraftSession(
            draft_id=f"mock_{uuid4().hex[:12]}",
            name=_clean_name(name) or f"Mock Draft {len(sessions) + 1}",
            created_at_utc=now,
            updated_at_utc=now,
        )
    )
    return save_mock_draft_sessions(sessions, root)


def rename_mock_draft_session(
    draft_id: str,
    name: str,
    *,
    root: Path | None = None,
) -> list[MockDraftSession]:
    cleaned = _clean_name(name)
    if not cleaned:
        return load_mock_draft_sessions(root)
    now = _now()
    sessions = [
        MockDraftSession(
            draft_id=session.draft_id,
            name=cleaned if session.draft_id == draft_id else session.name,
            created_at_utc=session.created_at_utc,
            updated_at_utc=now if session.draft_id == draft_id else session.updated_at_utc,
        )
        for session in load_mock_draft_sessions(root)
    ]
    return save_mock_draft_sessions(sessions, root)


def duplicate_mock_draft_session(
    draft_id: str,
    name: str,
    *,
    root: Path | None = None,
) -> list[MockDraftSession]:
    sessions = load_mock_draft_sessions(root)
    source = next((session for session in sessions if session.draft_id == draft_id), None)
    if source is None:
        return sessions
    new_id = f"mock_{uuid4().hex[:12]}"
    now = _now()
    duplicate_name = _clean_name(name) or f"{source.name} Copy"
    source_state = load_runtime_state(mode="mock", draft_id=source.draft_id, root=root)
    copied_state = _retarget_runtime_state(source_state, new_id)
    save_runtime_state(
        copied_state,
        event_type="mock_draft_duplicated",
        event_detail={"source_draft_id": source.draft_id, "new_draft_id": new_id},
        root=root,
    )
    sessions.append(
        MockDraftSession(
            draft_id=new_id,
            name=duplicate_name,
            created_at_utc=now,
            updated_at_utc=now,
        )
    )
    return save_mock_draft_sessions(sessions, root)


def delete_mock_draft_session(
    draft_id: str,
    *,
    root: Path | None = None,
) -> list[MockDraftSession]:
    sessions = [
        session for session in load_mock_draft_sessions(root) if session.draft_id != draft_id
    ]
    path = runtime_state_path(mode="mock", draft_id=draft_id, root=root)
    if path.exists():
        state = load_runtime_state(mode="mock", draft_id=draft_id, root=root)
        create_runtime_backup(state, root=root, reason="before_mock_delete")
        path.unlink()
    return save_mock_draft_sessions(sessions or [default_mock_draft_session()], root)


def selected_mock_draft_session(
    sessions: list[MockDraftSession],
    draft_id: str | None,
) -> MockDraftSession:
    return next(
        (session for session in sessions if session.draft_id == draft_id),
        sessions[0] if sessions else default_mock_draft_session(),
    )


def session_options(sessions: list[MockDraftSession]) -> dict[str, str]:
    return {f"{session.name} ({session.draft_id})": session.draft_id for session in sessions}


def _session_from_raw(raw: dict[str, object]) -> MockDraftSession:
    now = _now()
    draft_id = _safe_token(str(raw.get("draft_id") or DEFAULT_MOCK_DRAFT_ID))
    return MockDraftSession(
        draft_id=draft_id or DEFAULT_MOCK_DRAFT_ID,
        name=_clean_name(str(raw.get("name") or DEFAULT_MOCK_DRAFT_NAME))
        or DEFAULT_MOCK_DRAFT_NAME,
        created_at_utc=str(raw.get("created_at_utc") or now),
        updated_at_utc=str(raw.get("updated_at_utc") or now),
    )


def _retarget_runtime_state(state: RuntimeState, draft_id: str) -> RuntimeState:
    copied = dict(state)
    copied["draft_id"] = draft_id
    copied["draft_session_id"] = draft_id
    copied["mode"] = "mock"
    return copied


def _clean_name(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()[:80]


def _safe_token(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value.strip())[:80]


def _now() -> str:
    return datetime.now(UTC).isoformat()
