from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

DEFAULT_DOCS_DIR = Path("docs/hq/parallel_lanes")
CURRENT_OPERATOR_PATH = r"C:\NWR\Niners-War-Room-outcome"
LEGACY_OPERATOR_PATH = r"C:\Users\smcol\Documents\Vacation\Niners-War-Room-outcome"
DEPLOYMENT_V2_PATH = r"C:\NWR\Niners-War-Room-deploy-v2"
NORMAL_OPERATOR_BRANCH = "main"
LEGACY_HISTORICAL_CONTEXTS = (
    "historical",
    "legacy",
    "former",
    "no longer",
    "do not use",
    "not use",
    "source baseline",
    "source worktree",
)
CURRENT_INSTRUCTION_CONTEXTS = (
    "normal operator path",
    "run from",
    "set-location",
    "recommended",
    "use ",
    "current",
)
HOSTED_TERMS = (
    "hosted deployment",
    "hosted target",
    "hosting",
    "public routing",
)
HOSTED_READY_TERMS = (
    "ready",
    "enabled",
    "available",
    "approved",
    "unblocked",
)
HOSTED_READY_ALLOWED_CONTEXTS = (
    "blocked",
    "blocklist",
    "forbidden",
    "do not",
    "does not",
    "not ",
    "no ",
    "without",
    "pending",
    "until",
    "yet",
    "later",
    "previous",
    "non-green",
    "violation",
    "example",
    "request",
    "policy",
    "?",
)
REQUIRED_PATTERNS = [
    ("local_only", "V1 remains `local_only`", "local_only"),
    ("hosted_blocked", "hosted deployment remains blocked", "hosted deployment"),
    ("no_deploy_command", "no deploy command", "deploy command"),
    ("current_operator_path", CURRENT_OPERATOR_PATH, CURRENT_OPERATOR_PATH),
    ("normal_operator_branch", "normal operator branch", "normal operator branch"),
    (
        "deployment_v2_not_operator_path",
        "not the operator app path",
        "not the operator app path",
    ),
]


@dataclass(frozen=True)
class Finding:
    status: str
    check: str
    detail: str


def read_docs(docs_dir: Path) -> dict[Path, str]:
    return {
        path: path.read_text(encoding="utf-8", errors="ignore")
        for path in sorted(docs_dir.glob("DEPLOYMENT_V2*.md"))
        if path.is_file()
    }


def audit_docs(docs_dir: Path) -> list[Finding]:
    docs = read_docs(docs_dir)
    joined = "\n".join(docs.values())
    lower_joined = joined.lower()
    findings: list[Finding] = []

    if not docs:
        return [Finding("RED", "docs_present", f"no Deployment V2 docs found in {docs_dir}")]

    for check, pattern, detail in REQUIRED_PATTERNS:
        if pattern.lower() not in lower_joined:
            findings.append(Finding("RED", check, f"missing required docs language: {detail}"))

    if LEGACY_OPERATOR_PATH in joined:
        findings.append(
            Finding(
                "NOTE",
                "legacy_operator_path_note",
                "legacy Vacation operator path appears in historical docs; D23 marks it historical",
            )
        )

    for path, text in docs.items():
        if has_affirmative_hosted_ready_language(text):
            findings.append(
                Finding(
                    "RED",
                    "hosted_ready_language",
                    f"hosted-ready language found in {path.as_posix()}",
                )
            )
        if LEGACY_OPERATOR_PATH in text and CURRENT_OPERATOR_PATH not in joined:
            findings.append(
                Finding(
                    "RED",
                    "current_operator_path_mismatch",
                    f"legacy path appears without current desktop path in {path.as_posix()}",
                )
            )
        legacy_current_instruction = legacy_current_instruction_detail(path, text)
        if legacy_current_instruction:
            findings.append(
                Finding(
                    "RED",
                    "legacy_operator_path_current_instruction",
                    legacy_current_instruction,
                )
            )

    if not findings:
        findings.append(Finding("GREEN", "docs_consistency", "Deployment V2 docs are consistent"))

    findings.append(operator_path_summary(docs))

    return findings


def operator_path_summary(docs: dict[Path, str]) -> Finding:
    current_hits = sum(text.count(CURRENT_OPERATOR_PATH) for text in docs.values())
    legacy_hits = sum(text.count(LEGACY_OPERATOR_PATH) for text in docs.values())
    return Finding(
        "NOTE",
        "operator_path_reference_summary",
        (
            f"current desktop operator path references={current_hits}; "
            f"legacy Vacation path references={legacy_hits}"
        ),
    )


def legacy_current_instruction_detail(path: Path, text: str) -> str:
    if not is_current_generation_doc(path):
        return ""
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if LEGACY_OPERATOR_PATH not in line:
            continue
        context_lines = lines[max(0, index - 2) : min(len(lines), index + 3)]
        context = " ".join(context_lines).lower()
        if any(marker in context for marker in LEGACY_HISTORICAL_CONTEXTS):
            continue
        if any(marker in context for marker in CURRENT_INSTRUCTION_CONTEXTS):
            return f"legacy operator path appears as current instruction in {path.as_posix()}"
    return ""


def is_current_generation_doc(path: Path) -> bool:
    match = re.search(r"DEPLOYMENT_V2_D(\d+)_", path.name)
    if match:
        return int(match.group(1)) >= 23
    return False


def has_affirmative_hosted_ready_language(text: str) -> bool:
    for line in text.splitlines():
        lower = line.lower()
        if not any(term in lower for term in HOSTED_TERMS):
            continue
        if not any(term in lower for term in HOSTED_READY_TERMS):
            continue
        if any(allowed in lower for allowed in HOSTED_READY_ALLOWED_CONTEXTS):
            continue
        return True
    return False


def verdict(findings: list[Finding]) -> str:
    statuses = {finding.status for finding in findings}
    if "RED" in statuses:
        return "RED"
    if "YELLOW" in statuses:
        return "YELLOW"
    return "GREEN"


def findings_to_dict(findings: list[Finding]) -> dict[str, object]:
    missing_phrases = [
        finding for finding in findings if finding.status == "RED" and finding.check in {
            check for check, _pattern, _detail in REQUIRED_PATTERNS
        }
    ]
    notes = [finding for finding in findings if finding.status == "NOTE"]
    blocked_language_hits = [
        finding for finding in findings if finding.check == "hosted_ready_language"
    ]
    historical_path_notes = [
        finding for finding in findings if finding.check == "legacy_operator_path_note"
    ]

    return {
        "verdict": verdict(findings),
        "required_phrases": [
            {"check": check, "pattern": pattern, "detail": detail}
            for check, pattern, detail in REQUIRED_PATTERNS
        ],
        "missing_phrases": [
            {
                "status": finding.status,
                "check": finding.check,
                "detail": finding.detail,
            }
            for finding in missing_phrases
        ],
        "notes": [
            {
                "status": finding.status,
                "check": finding.check,
                "detail": finding.detail,
            }
            for finding in notes
        ],
        "blocked_language_hits": [
            {
                "status": finding.status,
                "check": finding.check,
                "detail": finding.detail,
            }
            for finding in blocked_language_hits
        ],
        "historical_path_notes": [
            {
                "status": finding.status,
                "check": finding.check,
                "detail": finding.detail,
            }
            for finding in historical_path_notes
        ],
        "findings": [
            {
                "status": finding.status,
                "check": finding.check,
                "detail": finding.detail,
            }
            for finding in findings
        ],
    }


def print_text(findings: list[Finding]) -> None:
    print(f"Deployment V2 docs consistency verdict: {verdict(findings)}")
    for finding in findings:
        print(f"- {finding.check}: {finding.status} - {finding.detail}")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit Deployment V2 docs for local-only consistency."
    )
    parser.add_argument(
        "--docs-dir",
        default=str(DEFAULT_DOCS_DIR),
        help="Deployment V2 docs directory to scan.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON validation output.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    findings = audit_docs(Path(args.docs_dir))
    if args.json:
        print(json.dumps(findings_to_dict(findings), indent=2, sort_keys=True))
    else:
        print_text(findings)
    result = verdict(findings)
    if result == "GREEN":
        return 0
    if result == "YELLOW":
        return 2
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
