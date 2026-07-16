from __future__ import annotations

import ast
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from app.navigation import NavigationPageSpec, app_page_path


@dataclass(frozen=True)
class ImportedSymbol:
    module: str
    name: str


@dataclass(frozen=True)
class ResolvedRouteSource:
    route: str
    spec: NavigationPageSpec
    path: Path
    source: str


def normalized_route(route: str) -> str:
    return f"/{route.strip('/')}"


def route_spec_map(
    routes: Iterable[NavigationPageSpec],
) -> dict[str, NavigationPageSpec]:
    route_map: dict[str, NavigationPageSpec] = {}
    for spec in routes:
        route = normalized_route(spec.url_path)
        assert route not in route_map, f"duplicate route declaration for {route}"
        route_map[route] = spec
    return route_map


def resolve_route_source(
    route: str,
    *,
    routes: Iterable[NavigationPageSpec],
    repo_root: Path,
    source_overrides: Mapping[str, str] | None = None,
) -> ResolvedRouteSource:
    requested_route = normalized_route(route)
    route_map = route_spec_map(routes)
    assert requested_route in route_map, f"route {requested_route} is not declared"
    spec = route_map[requested_route]
    app_dir = (repo_root / "app").resolve()
    path = app_page_path(app_dir, spec).resolve()
    try:
        path.relative_to(app_dir)
    except ValueError as exc:
        raise AssertionError(
            f"route {requested_route} target escapes app/: {spec.file_path}"
        ) from exc
    assert path.is_file(), f"route {requested_route} target is missing: {path}"
    overrides = source_overrides or {}
    source = overrides.get(spec.file_path)
    if source is None:
        source = path.read_text(encoding="utf-8")
    return ResolvedRouteSource(
        route=requested_route,
        spec=spec,
        path=path,
        source=source,
    )


def assert_routes_resolve_to(
    route_names: Sequence[str],
    expected_file_path: str,
    *,
    routes: Iterable[NavigationPageSpec],
    repo_root: Path,
    source_overrides: Mapping[str, str] | None = None,
) -> tuple[ResolvedRouteSource, ...]:
    resolved = tuple(
        resolve_route_source(
            route,
            routes=routes,
            repo_root=repo_root,
            source_overrides=source_overrides,
        )
        for route in route_names
    )
    for item in resolved:
        assert item.spec.file_path == expected_file_path, (
            f"route {item.route} resolved to {item.spec.file_path}; "
            f"expected {expected_file_path}"
        )
    return resolved


def parse_python(source: str, source_name: str | Path) -> ast.Module:
    try:
        return ast.parse(source, filename=str(source_name))
    except SyntaxError as exc:
        raise AssertionError(f"cannot parse Python source {source_name}: {exc}") from exc


def _imported_local_names(tree: ast.AST, symbol: ImportedSymbol) -> tuple[str, ...]:
    imports = [
        alias.asname or alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module == symbol.module
        for alias in node.names
        if alias.name == symbol.name
    ]
    assert len(imports) <= 1, (
        f"ambiguous imports for {symbol.module}.{symbol.name}: {imports}"
    )
    return tuple(imports)


def imported_calls(
    source: str,
    source_name: str | Path,
    symbol: ImportedSymbol,
) -> tuple[ast.Call, ...]:
    tree = parse_python(source, source_name)
    local_names = set(_imported_local_names(tree, symbol))
    return tuple(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in local_names
    )


def assert_exact_imported_call(
    resolved: ResolvedRouteSource,
    symbol: ImportedSymbol,
    *,
    expected_count: int = 1,
) -> tuple[ast.Call, ...]:
    calls = imported_calls(resolved.source, resolved.path, symbol)
    assert len(calls) == expected_count, (
        f"route {resolved.route} expected exactly {expected_count} call(s) to "
        f"{symbol.module}.{symbol.name}, found {len(calls)} in {resolved.spec.file_path}"
    )
    return calls


def dotted_call_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if not isinstance(node, ast.Attribute):
        return None
    parent = dotted_call_name(node.value)
    if parent is None:
        return None
    return f"{parent}.{node.attr}"


def calls_by_name(tree: ast.AST, dotted_name: str) -> tuple[ast.Call, ...]:
    return tuple(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and dotted_call_name(node.func) == dotted_name
    )


def literal_string(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def assert_call_keyword(call: ast.Call, keyword: str, expected: str) -> None:
    matches = [item for item in call.keywords if item.arg == keyword]
    assert len(matches) == 1, f"expected one {keyword}= keyword on component call"
    actual = literal_string(matches[0].value)
    assert actual == expected, f"expected {keyword}={expected!r}, found {actual!r}"


def assert_page_header_title(resolved: ResolvedRouteSource, expected_title: str) -> None:
    page_header = ImportedSymbol("app.components.ui_framework", "page_header")
    calls = assert_exact_imported_call(resolved, page_header)
    call = calls[0]
    assert call.args, f"route {resolved.route} page_header call has no title argument"
    actual_title = literal_string(call.args[0])
    assert actual_title == expected_title, (
        f"route {resolved.route} page_header title is {actual_title!r}; "
        f"expected {expected_title!r}"
    )


def module_string_literals(resolved: ResolvedRouteSource) -> frozenset[str]:
    tree = parse_python(resolved.source, resolved.path)
    return frozenset(
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    )


def assert_imported_value_passed_to_call(
    resolved: ResolvedRouteSource,
    symbol: ImportedSymbol,
    call_name: str,
    *,
    expected_count: int = 1,
) -> None:
    tree = parse_python(resolved.source, resolved.path)
    local_names = set(_imported_local_names(tree, symbol))
    matching_calls = [
        call
        for call in calls_by_name(tree, call_name)
        if call.args
        and isinstance(call.args[0], ast.Name)
        and call.args[0].id in local_names
    ]
    assert len(matching_calls) == expected_count, (
        f"route {resolved.route} expected exactly {expected_count} {call_name} call(s) "
        f"using {symbol.module}.{symbol.name}, found {len(matching_calls)}"
    )


def assert_call_contains_text(
    resolved: ResolvedRouteSource,
    call_name: str,
    required_text: Sequence[str],
    *,
    expected_count: int = 1,
) -> None:
    tree = parse_python(resolved.source, resolved.path)
    matches = []
    for call in calls_by_name(tree, call_name):
        if not call.args:
            continue
        text = literal_string(call.args[0])
        if text is not None and all(term in text for term in required_text):
            matches.append(call)
    assert len(matches) == expected_count, (
        f"route {resolved.route} expected exactly {expected_count} {call_name} call(s) "
        f"containing {tuple(required_text)!r}, found {len(matches)}"
    )


def assigned_string(tree: ast.AST, name: str) -> str | None:
    values = [
        literal_string(node.value)
        for node in tree.body
        if isinstance(node, (ast.Assign, ast.AnnAssign))
        and any(
            isinstance(target, ast.Name) and target.id == name
            for target in (
                node.targets if isinstance(node, ast.Assign) else [node.target]
            )
        )
    ]
    assert len(values) <= 1, f"ambiguous assignments for {name}"
    return values[0] if values else None


def function_definition(tree: ast.AST, name: str) -> ast.FunctionDef:
    matches = [
        node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name
    ]
    assert len(matches) == 1, f"expected exactly one function definition for {name}"
    return matches[0]


def replace_ast_node(source: str, node: ast.AST, replacement: str) -> str:
    assert hasattr(node, "end_lineno") and node.end_lineno is not None
    assert hasattr(node, "end_col_offset") and node.end_col_offset is not None
    lines = source.splitlines(keepends=True)
    start = sum(len(line) for line in lines[: node.lineno - 1]) + node.col_offset
    end = sum(len(line) for line in lines[: node.end_lineno - 1]) + node.end_col_offset
    return f"{source[:start]}{replacement}{source[end:]}"


def replace_only_imported_call(
    source: str,
    source_name: str | Path,
    symbol: ImportedSymbol,
    replacement: str,
) -> str:
    calls = imported_calls(source, source_name, symbol)
    assert len(calls) == 1, (
        f"mutation requires exactly one {symbol.module}.{symbol.name} call, "
        f"found {len(calls)}"
    )
    return replace_ast_node(source, calls[0], replacement)


def replace_only_imported_call_argument(
    source: str,
    source_name: str | Path,
    symbol: ImportedSymbol,
    argument_index: int,
    replacement: str,
) -> str:
    calls = imported_calls(source, source_name, symbol)
    assert len(calls) == 1, (
        f"mutation requires exactly one {symbol.module}.{symbol.name} call, "
        f"found {len(calls)}"
    )
    call = calls[0]
    assert len(call.args) > argument_index, (
        f"mutation requires argument {argument_index} on {symbol.name}"
    )
    return replace_ast_node(source, call.args[argument_index], replacement)
