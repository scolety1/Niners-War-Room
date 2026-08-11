"""Narrow post-V1 acceptance helpers for Start Here and state digests.

The helpers execute the production root page selected by ``app.navigation``.  They
capture rendered structures through a small Streamlit test double, instrument
durable boundaries, and define the versioned metadata-only digest serializer.
They are test-only and are not imported by the application.
"""

from __future__ import annotations

import builtins
import csv
import hashlib
import json
import os
import re
import shutil
import sqlite3
import sys
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath, PureWindowsPath
from types import ModuleType, SimpleNamespace
from typing import Any
from unittest.mock import patch

from app.navigation import (
    DEFAULT_ROOT_PAGE,
    NavigationPageSpec,
    app_page_path,
    registered_route_spec,
)

ROUTE_AUTHORITY_PATH = Path(
    "docs/hq/master/"
    "nwr_post_v1_completeness_historical_aging_audit_v1_20260721/"
    "ROUTE_AND_PRODUCT_SURFACE_INVENTORY.csv"
)

DIGEST_NAME = "PERSISTENT_STATE_DIGEST_V1"
DIGEST_SERIALIZER = "nwr-persistent-state-json-v1"
_SHA256_RE = re.compile(r"[0-9a-f]{64}")
_FAMILY_RE = re.compile(r"[a-z0-9][a-z0-9._-]*")


@dataclass(frozen=True)
class RenderedLink:
    label: str
    target: str


@dataclass(frozen=True)
class RenderedWorkflow:
    title: str
    status: str
    detail: str
    links: tuple[RenderedLink, ...]


@dataclass(frozen=True)
class RenderedStartHere:
    route: str
    page_path: Path
    headings: tuple[tuple[str, str], ...]
    text: tuple[str, ...]
    badges: tuple[str, ...]
    links: tuple[RenderedLink, ...]
    workflows: tuple[RenderedWorkflow, ...]


@dataclass(frozen=True)
class WorkflowAuthority:
    route: str
    title: str
    classification: str


@dataclass(frozen=True)
class _RenderEvent:
    kind: str
    value: str
    target: str
    container: str


class _Column:
    def __init__(self, recorder: _StreamlitRecorder, container: str) -> None:
        self._recorder = recorder
        self._container = container

    def __enter__(self) -> _Column:
        self._recorder._containers.append(self._container)
        return self

    def __exit__(self, *_args: object) -> None:
        popped = self._recorder._containers.pop()
        assert popped == self._container

    def link_button(self, label: str, page: str, **_kwargs: object) -> None:
        self._recorder._record("link", label, target=page, container=self._container)

    def metric(self, label: str, value: object, **_kwargs: object) -> None:
        self._recorder._record("metric", f"{label}: {value}", container=self._container)


class _StreamlitRecorder(ModuleType):
    def __init__(self) -> None:
        super().__init__("streamlit")
        self.events: list[_RenderEvent] = []
        self.session_state: dict[str, object] = {}
        self._containers: list[str] = ["root"]
        self._column_group = 0

    def _record(
        self,
        kind: str,
        value: object,
        *,
        target: str = "",
        container: str | None = None,
    ) -> None:
        self.events.append(
            _RenderEvent(
                kind=kind,
                value=str(value),
                target=str(target),
                container=container or self._containers[-1],
            )
        )

    def columns(self, spec: int | Sequence[object]) -> tuple[_Column, ...]:
        count = spec if isinstance(spec, int) else len(spec)
        group = self._column_group
        self._column_group += 1
        return tuple(_Column(self, f"columns-{group}-{index}") for index in range(count))

    def markdown(self, body: object, **_kwargs: object) -> None:
        self._record("markdown", body)

    def write(self, body: object, **_kwargs: object) -> None:
        self._record("write", body)

    def info(self, body: object, **_kwargs: object) -> None:
        self._record("info", body)

    def caption(self, body: object, **_kwargs: object) -> None:
        self._record("caption", body)

    def warning(self, body: object, **_kwargs: object) -> None:
        self._record("warning", body)

    def success(self, body: object, **_kwargs: object) -> None:
        self._record("success", body)

    def error(self, body: object, **_kwargs: object) -> None:
        self._record("error", body)

    def link_button(self, label: str, page: str, **_kwargs: object) -> None:
        self._record("link", label, target=page)

    def selectbox(
        self,
        label: str,
        options: Sequence[object],
        **_kwargs: object,
    ) -> object:
        self._record("selectbox", label)
        assert options, f"selectbox {label!r} has no options"
        return options[0]

    def expander(self, label: str, **_kwargs: object) -> _Column:
        self._record("expander", label)
        return _Column(self, f"expander-{self._column_group}")


@dataclass(frozen=True)
class _HTMLItem:
    kind: str
    tag: str
    text: str


class _StructuredHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.items: list[_HTMLItem] = []
        self._captures: list[tuple[str, str, list[str]]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key: value or "" for key, value in attrs}
        classes = frozenset(values.get("class", "").split())
        kind = ""
        if tag in {"h1", "h2", "h3", "h4"}:
            kind = "heading"
        elif tag == "span" and "nwr-pill" in classes:
            kind = "badge"
        elif tag == "p":
            kind = "paragraph"
        elif tag == "div" and "nwr-eyebrow" in classes:
            kind = "eyebrow"
        elif tag == "div" and "nwr-section-label" in classes:
            kind = "section"
        if kind:
            self._captures.append((tag, kind, []))

    def handle_data(self, data: str) -> None:
        for _tag, _kind, chunks in self._captures:
            chunks.append(data)

    def handle_endtag(self, tag: str) -> None:
        if not self._captures or self._captures[-1][0] != tag:
            return
        capture_tag, kind, chunks = self._captures.pop()
        text = " ".join("".join(chunks).split())
        if text:
            self.items.append(_HTMLItem(kind, capture_tag, text))


def resolve_production_route(
    route: str,
    *,
    app_dir: Path = Path("app"),
) -> tuple[NavigationPageSpec, Path]:
    normalized = "/" if route.strip() in {"", "/"} else f"/{route.strip('/')}"
    if normalized == "/":
        spec = DEFAULT_ROOT_PAGE
        assert spec.default and spec.url_path == ""
    else:
        spec = registered_route_spec(normalized.strip("/"))
    path = app_page_path(app_dir, spec)
    assert path.is_file(), f"route {normalized} target is missing: {path}"
    return spec, path


def render_start_here(
    *,
    repo_root: Path = Path("."),
    source_transform: Callable[[str], str] | None = None,
    execution_globals: Mapping[str, object] | None = None,
) -> RenderedStartHere:
    """Resolve ``/`` through production routing and execute its actual page module."""
    app_dir = repo_root / "app"
    spec, page_path = resolve_production_route("/", app_dir=app_dir)
    assert spec is DEFAULT_ROOT_PAGE
    source = page_path.read_text(encoding="utf-8")
    if source_transform is not None:
        source = source_transform(source)

    recorder = _StreamlitRecorder()
    owner_data = ModuleType("app.components.owner_data")
    owner_data.load_owner_data = lambda _repo_root: SimpleNamespace(
        evidence=SimpleNamespace(
            rows=(
                {
                    "asset_id": "current:1",
                    "asset_type": "Current Player",
                    "asset_name": "Alpha Receiver",
                    "dynasty_rank": "1",
                },
                {
                    "asset_id": "rookie:2",
                    "asset_type": "Rookie Review",
                    "asset_name": "Beta Rookie",
                    "dynasty_rank": "",
                },
            )
        )
    )
    workspace_service = ModuleType("src.services.personal_workspace_service")
    workspace_service.load_store = lambda _store_name: SimpleNamespace(records=())
    workspace_service.summarize_workspace = lambda: {
        "watchlist": 0,
        "targets": 0,
        "avoid": 0,
        "open_decisions": 0,
        "saved_scenarios": 0,
    }
    import app.components.owner_mode as owner_mode
    import app.components.ui_framework as ui_framework

    namespace: dict[str, object] = {
        "__builtins__": builtins.__dict__,
        "__file__": str(page_path.resolve()),
        "__name__": "__nwr_start_here_acceptance__",
        "__package__": None,
    }
    namespace.update(execution_globals or {})
    with (
        patch.dict(
            sys.modules,
            {
                "streamlit": recorder,
                "app.components.owner_data": owner_data,
                "src.services.personal_workspace_service": workspace_service,
            },
        ),
        patch.object(owner_mode, "st", recorder),
        patch.object(ui_framework, "st", recorder),
    ):
        exec(compile(source, str(page_path), "exec"), namespace)
    return _rendered_snapshot(page_path, recorder.events)


def _parse_html(value: str) -> tuple[_HTMLItem, ...]:
    parser = _StructuredHTMLParser()
    parser.feed(value)
    parser.close()
    return tuple(parser.items)


def _rendered_snapshot(page_path: Path, events: Sequence[_RenderEvent]) -> RenderedStartHere:
    headings: list[tuple[str, str]] = []
    badges: list[str] = []
    text: list[str] = []
    links: list[RenderedLink] = []
    by_container: dict[str, list[_RenderEvent]] = {}
    for event in events:
        by_container.setdefault(event.container, []).append(event)
        if event.kind == "link":
            links.append(RenderedLink(event.value, event.target))
            continue
        if event.kind != "markdown":
            value = " ".join(event.value.split())
            if value:
                text.append(value)
            continue
        for item in _parse_html(event.value):
            text.append(item.text)
            if item.kind == "heading":
                headings.append((item.tag, item.text))
            elif item.kind == "badge":
                badges.append(item.text)

    workflows: list[RenderedWorkflow] = []
    for container_events in by_container.values():
        items = tuple(
            item
            for event in container_events
            if event.kind == "markdown"
            for item in _parse_html(event.value)
        )
        titles = tuple(item.text for item in items if item.kind == "heading" and item.tag == "h3")
        if not titles:
            continue
        statuses = tuple(item.text for item in items if item.kind == "badge")
        details = tuple(item.text for item in items if item.kind == "paragraph")
        tile_links = tuple(
            RenderedLink(event.value, event.target)
            for event in container_events
            if event.kind == "link"
        )
        workflows.append(
            RenderedWorkflow(
                title=titles[0],
                status=statuses[0] if len(statuses) == 1 else " / ".join(statuses),
                detail=details[0] if len(details) == 1 else " / ".join(details),
                links=tile_links,
            )
        )
    return RenderedStartHere(
        route="/",
        page_path=page_path,
        headings=tuple(headings),
        text=tuple(text),
        badges=tuple(badges),
        links=tuple(links),
        workflows=tuple(workflows),
    )


def load_workflow_authority(repo_root: Path = Path(".")) -> dict[str, WorkflowAuthority]:
    """Load the pre-existing audit authority; do not duplicate a route/status table."""
    path = repo_root / ROUTE_AUTHORITY_PATH
    rows: dict[str, WorkflowAuthority] = {}
    with path.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            raw_route = str(row["url_path"]).strip()
            route = "/" if raw_route in {"", "/"} else f"/{raw_route.strip('/')}"
            assert route not in rows, f"duplicate workflow authority route: {route}"
            rows[route] = WorkflowAuthority(
                route=route,
                title=str(row["title"]).strip(),
                classification=str(row["classification"]).strip(),
            )
    assert rows, f"workflow authority is empty: {path}"
    for route, authority in rows.items():
        spec, _path = resolve_production_route(route, app_dir=repo_root / "app")
        assert spec.title == authority.title, f"authority title drift for {route}"
    return rows


_CLASSIFICATION_CATEGORY = {
    "COMPLETE_CANONICAL_DATA": "canonical",
    "COMPLETE_READ_ONLY": "read_only",
    "COMPLETE_MANUAL_DECISION_AID": "manual",
    "COMPLETE_MANUAL_STATE": "manual_state",
    "GATED_ADMIN": "gated",
    "REVIEW_ONLY_BY_DESIGN": "review_only",
    "POST_V1_PARKED": "parked",
}

_STATUS_CATEGORY = {
    "Canonical board": "canonical",
    "Read-only": "read_only",
    "Manual decision aid": "manual",
    "Live local state": "manual_state",
    "Gated": "gated",
    "Gated admin": "gated",
    "Review-only": "review_only",
    "Parked": "parked",
    "Roadmap only": "parked",
    # Explicit unsafe mutations remain named so failures explain the mismatch.
    "Automated": "automated",
    "Automated decision aid": "automated",
    "Live": "live",
    "Production": "production",
    "Available": "available",
}


def validate_start_here_contract(
    rendered: RenderedStartHere,
    *,
    authority: Mapping[str, WorkflowAuthority],
) -> None:
    assert rendered.route == "/"
    spec, expected_page = resolve_production_route("/", app_dir=rendered.page_path.parents[1])
    assert spec.default and rendered.page_path.resolve() == expected_page.resolve()
    assert tuple(value for level, value in rendered.headings if level == "h1") == (
        "Niners War Room",
    )
    assert len(rendered.workflows) == 4, "Start Here must render four primary workflow tiles"
    assert len(rendered.links) == 11, "Start Here must render eleven unique workflow links"
    targets = tuple(link.target for link in rendered.links)
    assert len(targets) == len(set(targets)), "Start Here contains duplicate route targets"
    for link in rendered.links:
        resolve_production_route(link.target, app_dir=rendered.page_path.parents[1])

    seen_titles: set[str] = set()
    for workflow in rendered.workflows:
        assert workflow.title not in seen_titles, f"duplicate workflow tile: {workflow.title}"
        seen_titles.add(workflow.title)
        assert len(workflow.links) == 1, f"{workflow.title} must render exactly one primary link"
        link = workflow.links[0]
        target_spec, _target = resolve_production_route(
            link.target, app_dir=rendered.page_path.parents[1]
        )
        assert target_spec.title == workflow.title, (
            f"{workflow.title} links to {link.target}, owned by {target_spec.title}"
        )
        canonical = authority.get(link.target)
        assert canonical is not None, f"no workflow authority for {link.target}"
        assert canonical.title == workflow.title
        expected_category = _CLASSIFICATION_CATEGORY.get(canonical.classification)
        assert expected_category is not None, (
            f"unsupported primary workflow classification: {canonical.classification}"
        )
        rendered_category = _STATUS_CATEGORY.get(workflow.status)
        assert rendered_category is not None, (
            f"unknown or contradictory rendered disposition for {workflow.title}: "
            f"{workflow.status!r}"
        )
        assert rendered_category == expected_category, (
            f"{workflow.title} rendered {workflow.status!r} ({rendered_category}) but "
            f"authority is {canonical.classification} ({expected_category})"
        )


@dataclass(frozen=True)
class FileInventoryRecord:
    path: str
    size: int
    sha256: str


@dataclass(frozen=True)
class TreeInventory:
    directories: tuple[str, ...]
    files: tuple[FileInventoryRecord, ...]


@dataclass(frozen=True)
class DurableMutation:
    boundary: str
    target: str


@dataclass(frozen=True)
class DurableRenderResult:
    rendered: RenderedStartHere
    mutations: tuple[DurableMutation, ...]
    before: TreeInventory
    after: TreeInventory

    @property
    def durable_mutation_count(self) -> int:
        return len(self.mutations)


class DurableBoundaryRecorder:
    """Record write-capable boundaries and confine mutations to one temp root."""

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.mutations: list[DurableMutation] = []

    def _record(self, boundary: str, target: object = "") -> None:
        self.mutations.append(DurableMutation(boundary, str(target)))

    def _scoped(self, value: object, *, boundary: str) -> Path:
        path = Path(os.fspath(value)).resolve()
        self._record(boundary, path)
        try:
            path.relative_to(self.root)
        except ValueError as exc:
            raise AssertionError(f"durable mutation escaped isolated root: {path}") from exc
        return path

    def install(self, monkeypatch: Any) -> None:
        # Import production boundaries before filesystem methods are patched so imports
        # themselves cannot be confused with page-render persistence.
        import pandas as pd

        import src.launcher.windows_desktop as launcher
        import src.services.data_refresh_orchestrator_service as refresh
        import src.services.development_lab_state_service as lab_state
        import src.services.draft_day_runtime_state_service as runtime_state
        import src.services.refresh_receipt_store_service as receipts

        original_path_open = Path.open
        original_touch = Path.touch
        original_mkdir = Path.mkdir
        original_unlink = Path.unlink
        original_rename = Path.rename
        original_replace = Path.replace
        original_builtin_open = builtins.open
        original_os_open = os.open
        original_os_remove = os.remove
        original_os_unlink = os.unlink
        original_os_rename = os.rename
        original_os_replace = os.replace
        original_os_mkdir = os.mkdir
        original_os_makedirs = os.makedirs
        original_copy = shutil.copy
        original_copy2 = shutil.copy2
        original_copyfile = shutil.copyfile
        original_move = shutil.move
        original_rmtree = shutil.rmtree
        original_connect = sqlite3.connect

        recorder = self

        def path_open(path: Path, mode: str = "r", *args: object, **kwargs: object):
            if any(flag in mode for flag in ("w", "a", "x", "+")):
                recorder._scoped(path, boundary=f"pathlib.Path.open:{mode}")
            return original_path_open(path, mode, *args, **kwargs)

        def path_touch(path: Path, *args: object, **kwargs: object):
            recorder._scoped(path, boundary="pathlib.Path.touch")
            return original_touch(path, *args, **kwargs)

        def path_mkdir(path: Path, *args: object, **kwargs: object):
            recorder._scoped(path, boundary="pathlib.Path.mkdir")
            return original_mkdir(path, *args, **kwargs)

        def path_unlink(path: Path, *args: object, **kwargs: object):
            recorder._scoped(path, boundary="pathlib.Path.unlink")
            return original_unlink(path, *args, **kwargs)

        def path_rename(path: Path, target: object):
            recorder._scoped(path, boundary="pathlib.Path.rename:source")
            recorder._scoped(target, boundary="pathlib.Path.rename:target")
            return original_rename(path, target)

        def path_replace(path: Path, target: object):
            recorder._scoped(path, boundary="pathlib.Path.replace:source")
            recorder._scoped(target, boundary="pathlib.Path.replace:target")
            return original_replace(path, target)

        def builtin_open(file: object, mode: str = "r", *args: object, **kwargs: object):
            if not isinstance(file, int) and any(flag in mode for flag in ("w", "a", "x", "+")):
                recorder._scoped(file, boundary=f"builtins.open:{mode}")
            return original_builtin_open(file, mode, *args, **kwargs)

        def os_open(path: object, flags: int, *args: object, **kwargs: object):
            write_flags = os.O_WRONLY | os.O_RDWR | os.O_APPEND | os.O_CREAT | os.O_TRUNC
            if flags & write_flags:
                recorder._scoped(path, boundary=f"os.open:{flags}")
            return original_os_open(path, flags, *args, **kwargs)

        def single_path(original: Callable[..., Any], boundary: str):
            def wrapped(path: object, *args: object, **kwargs: object):
                recorder._scoped(path, boundary=boundary)
                return original(path, *args, **kwargs)

            return wrapped

        def two_paths(original: Callable[..., Any], boundary: str):
            def wrapped(source: object, target: object, *args: object, **kwargs: object):
                recorder._scoped(source, boundary=f"{boundary}:source")
                recorder._scoped(target, boundary=f"{boundary}:target")
                return original(source, target, *args, **kwargs)

            return wrapped

        monkeypatch.setattr(Path, "open", path_open)
        monkeypatch.setattr(Path, "touch", path_touch)
        monkeypatch.setattr(Path, "mkdir", path_mkdir)
        monkeypatch.setattr(Path, "unlink", path_unlink)
        monkeypatch.setattr(Path, "rename", path_rename)
        monkeypatch.setattr(Path, "replace", path_replace)
        monkeypatch.setattr(builtins, "open", builtin_open)
        monkeypatch.setattr(os, "open", os_open)
        monkeypatch.setattr(os, "remove", single_path(original_os_remove, "os.remove"))
        monkeypatch.setattr(os, "unlink", single_path(original_os_unlink, "os.unlink"))
        monkeypatch.setattr(os, "rename", two_paths(original_os_rename, "os.rename"))
        monkeypatch.setattr(os, "replace", two_paths(original_os_replace, "os.replace"))
        monkeypatch.setattr(os, "mkdir", single_path(original_os_mkdir, "os.mkdir"))
        monkeypatch.setattr(os, "makedirs", single_path(original_os_makedirs, "os.makedirs"))
        monkeypatch.setattr(shutil, "copy", two_paths(original_copy, "shutil.copy"))
        monkeypatch.setattr(shutil, "copy2", two_paths(original_copy2, "shutil.copy2"))
        monkeypatch.setattr(shutil, "copyfile", two_paths(original_copyfile, "shutil.copyfile"))
        monkeypatch.setattr(shutil, "move", two_paths(original_move, "shutil.move"))
        monkeypatch.setattr(shutil, "rmtree", single_path(original_rmtree, "shutil.rmtree"))

        def sqlite_connect(database: object, *args: object, **kwargs: object):
            if str(database) != ":memory:":
                recorder._scoped(database, boundary="sqlite3.connect")
            return original_connect(database, *args, **kwargs)

        monkeypatch.setattr(sqlite3, "connect", sqlite_connect)

        for name in ("to_csv", "to_json", "to_pickle", "to_parquet", "to_excel"):
            original = getattr(pd.DataFrame, name)

            def dataframe_export(
                frame: Any,
                path_or_buf: object = None,
                *args: object,
                _name: str = name,
                _original: Callable[..., Any] = original,
                **kwargs: object,
            ):
                if path_or_buf is not None and isinstance(path_or_buf, (str, os.PathLike)):
                    recorder._scoped(path_or_buf, boundary=f"pandas.DataFrame.{_name}")
                return _original(frame, path_or_buf, *args, **kwargs)

            monkeypatch.setattr(pd.DataFrame, name, dataframe_export)

        original_receipt = receipts.write_refresh_receipt
        original_runtime = runtime_state.save_runtime_state
        original_lab = lab_state.save_tool_state

        def receipt_write(payload: dict[str, Any], **kwargs: object):
            recorder._scoped(kwargs["status_root"], boundary="receipt.write_refresh_receipt")
            return original_receipt(payload, **kwargs)

        def runtime_write(state: dict[str, Any], **kwargs: object):
            recorder._scoped(kwargs["root"], boundary="runtime.save_runtime_state")
            return original_runtime(state, **kwargs)

        def lab_write(tool_key: str, payload: dict[str, Any], **kwargs: object):
            root = kwargs.get("root")
            assert root is not None
            recorder._scoped(root, boundary="development_lab.save_tool_state")
            return original_lab(tool_key, payload, **kwargs)

        monkeypatch.setattr(receipts, "write_refresh_receipt", receipt_write)
        monkeypatch.setattr(runtime_state, "save_runtime_state", runtime_write)
        monkeypatch.setattr(lab_state, "save_tool_state", lab_write)

        def refresh_dispatch(*_args: object, **_kwargs: object) -> None:
            recorder._record("refresh.dispatch", "blocked test dispatch")

        for name in (
            "run_quick_refresh",
            "run_full_safe_refresh",
            "run_check_protected_artifacts",
            "run_manual_sources_checklist",
            "run_data_refresh",
            "run_data_loader",
            "write_refresh_status",
        ):
            monkeypatch.setattr(refresh, name, refresh_dispatch)

        def launcher_write(*_args: object, **_kwargs: object) -> None:
            recorder._record("launcher.persistence", "blocked test launcher write")

        for name in (
            "create_data_health_recovery_backup",
            "create_backup",
            "create_manual_backup",
            "restore_backup",
        ):
            monkeypatch.setattr(launcher, name, launcher_write)


def tree_inventory(root: Path) -> TreeInventory:
    if not root.exists():
        return TreeInventory((), ())
    directories = tuple(
        sorted(path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_dir())
    )
    files = tuple(
        FileInventoryRecord(
            path=path.relative_to(root).as_posix(),
            size=path.stat().st_size,
            sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        )
        for path in sorted(
            (item for item in root.rglob("*") if item.is_file()),
            key=lambda item: item.relative_to(root).as_posix(),
        )
    )
    return TreeInventory(directories, files)


def render_start_here_with_durable_monitor(
    monkeypatch: Any,
    isolated_root: Path,
    *,
    source_transform: Callable[[str], str] | None = None,
    execution_globals: Mapping[str, object] | None = None,
) -> DurableRenderResult:
    isolated_root.mkdir(parents=True, exist_ok=True)
    before = tree_inventory(isolated_root)
    recorder = DurableBoundaryRecorder(isolated_root)
    recorder.install(monkeypatch)
    rendered = render_start_here(
        source_transform=source_transform,
        execution_globals=execution_globals,
    )
    after = tree_inventory(isolated_root)
    return DurableRenderResult(rendered, tuple(recorder.mutations), before, after)


@dataclass(frozen=True)
class DigestInventoryRecord:
    path: str
    bytes: int
    sha256: str
    timestamp: str = ""


def normalize_digest_path(value: str) -> str:
    raw = str(value)
    assert raw and "\x00" not in raw, "inventory path is empty or contains NUL"
    assert not PurePosixPath(raw).is_absolute(), f"absolute path rejected: {raw}"
    assert not PureWindowsPath(raw).is_absolute(), f"absolute path rejected: {raw}"
    assert not re.match(r"^[A-Za-z]:", raw), f"drive path rejected: {raw}"
    normalized = raw.replace("\\", "/")
    parts = normalized.split("/")
    assert all(part not in {"", ".", ".."} for part in parts), (
        f"unsafe or ambiguous inventory path: {raw}"
    )
    return "/".join(parts)


def canonical_digest_bytes(
    records: Iterable[DigestInventoryRecord],
    *,
    family: str,
) -> bytes:
    assert _FAMILY_RE.fullmatch(family), f"invalid digest family: {family!r}"
    normalized: list[dict[str, object]] = []
    seen: set[str] = set()
    for record in records:
        path = normalize_digest_path(record.path)
        assert path not in seen, f"duplicate normalized path: {path}"
        seen.add(path)
        assert isinstance(record.bytes, int) and record.bytes >= 0
        assert _SHA256_RE.fullmatch(record.sha256), (
            f"SHA-256 must be lowercase hexadecimal for {path}"
        )
        normalized.append(
            {
                "path": path,
                "bytes": record.bytes,
                "sha256": record.sha256,
            }
        )
    normalized.sort(key=lambda item: str(item["path"]))
    document = {
        "version": DIGEST_NAME,
        "serializer": DIGEST_SERIALIZER,
        "family": family,
        "records": normalized,
    }
    return json.dumps(
        document,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("utf-8")


def persistent_state_digest_v1(
    records: Iterable[DigestInventoryRecord],
    *,
    family: str,
) -> str:
    return hashlib.sha256(canonical_digest_bytes(records, family=family)).hexdigest()


def digest_records_from_csv(path: Path, *, family: str) -> tuple[DigestInventoryRecord, ...]:
    records: list[DigestInventoryRecord] = []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            if row.get("record_type") != "INVENTORY" or row.get("family") != family:
                continue
            records.append(
                DigestInventoryRecord(
                    path=str(row["path"]),
                    bytes=int(row["bytes"]),
                    sha256=str(row["sha256"]),
                    timestamp=str(row.get("timestamp_utc", "")),
                )
            )
    return tuple(records)
