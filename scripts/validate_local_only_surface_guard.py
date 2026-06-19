from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

SKIPPED_DIRS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "data",
    "dist",
    "build",
    "local_exports",
    "node_modules",
}

PROHIBITED_EXACT_FILES = {
    "app.yaml",
    "app.yml",
    "cloudbuild.yaml",
    "cloudbuild.yml",
    "compose.yaml",
    "compose.yml",
    "containerfile",
    "docker-compose.yaml",
    "docker-compose.yml",
    "dockerfile",
    "fly.toml",
    "helmfile.yaml",
    "helmfile.yml",
    "netlify.toml",
    "procfile",
    "railway.json",
    "railway.toml",
    "render.yaml",
    "render.yml",
    "vercel.json",
}

PROHIBITED_PATH_SEGMENTS = {
    "k8s",
    "kubernetes",
    "helm",
}

COMMAND_SURFACE_FILES = {
    "makefile",
    "package.json",
    "pyproject.toml",
    "taskfile.yaml",
    "taskfile.yml",
    "tox.ini",
}

DEPLOY_COMMAND_PATTERNS = (
    re.compile(r"^\s*deploy\s*:", re.IGNORECASE | re.MULTILINE),
    re.compile(r"\bvercel\b", re.IGNORECASE),
    re.compile(r"\bnetlify\b", re.IGNORECASE),
    re.compile(r"\brender\b", re.IGNORECASE),
    re.compile(r"\brailway\b", re.IGNORECASE),
    re.compile(r"\bflyctl\b", re.IGNORECASE),
    re.compile(r"\bgcloud\s+run\b", re.IGNORECASE),
    re.compile(r"\baz\s+webapp\b", re.IGNORECASE),
    re.compile(r"\baws\s+(ecs|elasticbeanstalk|lambda)\b", re.IGNORECASE),
    re.compile(r"\bkubectl\b", re.IGNORECASE),
    re.compile(r"\bhelm\b", re.IGNORECASE),
    re.compile(r"\bdocker\s+(build|compose|push|run)\b", re.IGNORECASE),
    re.compile(r"\bdocker-compose\b", re.IGNORECASE),
    re.compile(r"\bngrok\b", re.IGNORECASE),
    re.compile(r"\bcloudflared\s+tunnel\b", re.IGNORECASE),
    re.compile(r"\blocaltunnel\b", re.IGNORECASE),
)


@dataclass(frozen=True)
class Violation:
    path: Path
    reason: str


@dataclass(frozen=True)
class GuardReport:
    verdict: str
    root: Path
    checked_path_count: int
    checked_categories: dict[str, object]
    blocked_surface_count: int
    reason_summary: dict[str, int]
    violations: list[Violation]


def iter_repo_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        relative_parts = path.relative_to(root).parts
        if any(part in SKIPPED_DIRS for part in relative_parts):
            continue
        if path.is_file():
            files.append(path)
    return files


def path_surface_violation(root: Path, path: Path) -> Violation | None:
    relative = path.relative_to(root)
    lower_parts = tuple(part.lower() for part in relative.parts)
    lower_name = path.name.lower()

    if len(lower_parts) >= 2 and lower_parts[:2] == (".github", "workflows"):
        return Violation(relative, "CI/CD workflow file is present")

    if lower_name in PROHIBITED_EXACT_FILES:
        return Violation(relative, "hosted/container/platform manifest is present")

    for part in lower_parts:
        if part in PROHIBITED_PATH_SEGMENTS:
            return Violation(relative, f"hosted/container path segment is present: {part}")

    return None


def command_surface_violations(root: Path, path: Path) -> list[Violation]:
    relative = path.relative_to(root)
    if path.name.lower() not in COMMAND_SURFACE_FILES:
        return []

    if path.name.lower() == "package.json":
        return package_json_violations(relative, path)

    text = path.read_text(encoding="utf-8", errors="ignore")
    return [
        Violation(relative, f"deploy-oriented command pattern found: {pattern.pattern}")
        for pattern in DEPLOY_COMMAND_PATTERNS
        if pattern.search(text)
    ]


def package_json_violations(relative: Path, path: Path) -> list[Violation]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return [Violation(relative, "package.json could not be parsed for deploy scripts")]

    scripts = data.get("scripts")
    if not isinstance(scripts, dict):
        return []

    violations: list[Violation] = []
    for name, command in scripts.items():
        if "deploy" in str(name).lower():
            violations.append(Violation(relative, f"package.json deploy script exists: {name}"))
            continue
        if not isinstance(command, str):
            continue
        for pattern in DEPLOY_COMMAND_PATTERNS:
            if pattern.search(command):
                violations.append(
                    Violation(
                        relative,
                        f"package.json script uses deploy-oriented command: {name}",
                    )
                )
                break
    return violations


def scan_repository(root: Path) -> list[Violation]:
    root = root.resolve()
    violations: list[Violation] = []

    for path in iter_repo_files(root):
        path_violation = path_surface_violation(root, path)
        if path_violation is not None:
            violations.append(path_violation)
        violations.extend(command_surface_violations(root, path))

    return sorted(violations, key=lambda violation: violation.path.as_posix())


def build_report(root: Path) -> GuardReport:
    root = root.resolve()
    files = iter_repo_files(root)
    violations: list[Violation] = []

    for path in files:
        path_violation = path_surface_violation(root, path)
        if path_violation is not None:
            violations.append(path_violation)
        violations.extend(command_surface_violations(root, path))

    violations = sorted(violations, key=lambda violation: violation.path.as_posix())
    reason_summary: dict[str, int] = {}
    for violation in violations:
        reason_summary[violation.reason] = reason_summary.get(violation.reason, 0) + 1

    return GuardReport(
        verdict="GREEN" if not violations else "RED",
        root=root,
        checked_path_count=len(files),
        checked_categories={
            "skipped_dirs": sorted(SKIPPED_DIRS),
            "prohibited_exact_files": sorted(PROHIBITED_EXACT_FILES),
            "prohibited_path_segments": sorted(PROHIBITED_PATH_SEGMENTS),
            "command_surface_files": sorted(COMMAND_SURFACE_FILES),
            "deploy_command_patterns": [pattern.pattern for pattern in DEPLOY_COMMAND_PATTERNS],
        },
        blocked_surface_count=len(violations),
        reason_summary=dict(sorted(reason_summary.items())),
        violations=violations,
    )


def report_to_json_dict(report: GuardReport) -> dict[str, object]:
    return {
        "verdict": report.verdict,
        "root": str(report.root),
        "checked_path_count": report.checked_path_count,
        "checked_categories": report.checked_categories,
        "blocked_surface_count": report.blocked_surface_count,
        "reason_summary": report.reason_summary,
        "violations": [
            {
                "path": violation.path.as_posix(),
                "reason": violation.reason,
            }
            for violation in report.violations
        ],
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate that Deployment V2 remains local-only and discovery-only."
    )
    parser.add_argument(
        "--report",
        nargs="?",
        choices=["text", "json"],
        const="json",
        default="text",
        help=(
            "Output format. Bare --report emits JSON; text preserves the original "
            "human-readable guard output."
        ),
    )
    parser.add_argument(
        "--root",
        dest="root_option",
        help="Repository root to scan. Overrides the positional root when supplied.",
    )
    parser.add_argument(
        "root_path",
        nargs="?",
        default=".",
        help="Repository root to scan. Defaults to the current working directory.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    root = Path(args.root_option or args.root_path)
    report = build_report(root)
    violations = report.violations

    if args.report == "json":
        print(json.dumps(report_to_json_dict(report), indent=2, sort_keys=True))
        return 0 if report.verdict == "GREEN" else 1

    if violations:
        print("Deployment V2 local-only surface guard failed:")
        for violation in violations:
            print(f"- {violation.path.as_posix()}: {violation.reason}")
        return 1

    print("Deployment V2 local-only surface guard passed: no deploy surfaces detected.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
