#!/usr/bin/env python3
"""Validate the remediation register and finding closure packets.

Usage:
    tools/validate-findings.py [REPOSITORY_ROOT]

The remediation plan owns finding scope and parent state. The YAML register
adds machine-checkable ownership, dependencies, child state, and evidence
links. A finding cannot become CLOSED by changing one word: its closure packet,
artifact hashes, and independent review must all validate in the same tree.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import sys
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import cast

import yaml
from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError

REPO_ROOT = Path(__file__).resolve().parent.parent
PLAN_NAME = "REMEDIATION-AND-CLOSURE-PLAN-2026-09-08.md"
REGISTER_RELATIVE = Path("docs/findings/register.yml")
REGISTER_SCHEMA_RELATIVE = Path("docs/findings/register.schema.json")
CLOSURE_SCHEMA_RELATIVE = Path("docs/findings/closure-packet.schema.json")
EVIDENCE_RELATIVE = Path("docs/evidence/findings")

PARENT_HEADING = re.compile(
    r"^### ((?:BASE|OSS|GAP|ENV|HW)-[0-9]{2}) — (.+)$", re.MULTILINE
)
CHILD_HEADING = re.compile(
    r"^- \*\*((?:GAP|HW)-[0-9]{2}[A-Z]) — ([^:]+):\*\*", re.MULTILINE
)
EXECUTION_ROW = re.compile(
    r"^\| ((?:BASE|OSS|GAP|ENV|HW)-[0-9]{2})\s*"
    r"\|\s*(P[0-3])\s*\|\s*([A-Z][A-Z _-]+?)\s*\|",
    re.MULTILINE,
)


@dataclass(frozen=True)
class PlanFinding:
    """One finding definition extracted from the approved plan."""

    title: str
    severity: str
    parent: str | None
    state: str


def _json_path(parts: Sequence[str | int]) -> str:
    """Render a deterministic path into a JSON-compatible document."""
    rendered = "$"
    for part in parts:
        rendered += f"[{part}]" if isinstance(part, int) else f".{part}"
    return rendered


def _read_text(path: Path, label: str, errors: list[str]) -> str | None:
    """Read UTF-8 text or append one stable diagnostic."""
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        errors.append(f"{label} is not UTF-8 at byte {exc.start}: {path}")
    except OSError as exc:
        errors.append(f"cannot read {label}: {path}: {exc}")
    return None


def _load_yaml(path: Path, label: str, errors: list[str]) -> object | None:
    """Load one YAML document without turning malformed input into a traceback."""
    raw = _read_text(path, label, errors)
    if raw is None:
        return None
    try:
        return yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        errors.append(f"{label} is not valid YAML: {path}: {exc}")
        return None


def _load_schema(path: Path, label: str, errors: list[str]) -> dict[str, object] | None:
    """Load and check one declared Draft 2020-12 JSON Schema."""
    raw = _read_text(path, label, errors)
    if raw is None:
        return None
    try:
        document = json.loads(raw)
    except json.JSONDecodeError as exc:
        errors.append(
            f"{label} is not valid JSON at line {exc.lineno}, "
            f"column {exc.colno}: {path}: {exc.msg}"
        )
        return None
    if not isinstance(document, dict):
        errors.append(f"{label} is not a JSON object: {path}")
        return None
    try:
        Draft202012Validator.check_schema(document)
    except SchemaError as exc:
        errors.append(f"{label} is not a valid schema: {path}: {exc.message}")
        return None
    return cast(dict[str, object], document)


def _schema_errors(
    document: object, schema: dict[str, object], label: str
) -> list[str]:
    """Return stable, path-addressed schema diagnostics."""
    found = sorted(
        Draft202012Validator(schema).iter_errors(document),
        key=lambda error: (_json_path(tuple(error.absolute_path)), error.message),
    )
    return [
        f"{label} {_json_path(tuple(error.absolute_path))}: {error.message}"
        for error in found
    ]


def _plan_findings(plan: str, errors: list[str]) -> dict[str, PlanFinding]:
    """Extract the authoritative parent and child finding set from the plan."""
    rows: dict[str, tuple[str, str]] = {}
    for finding_id, severity, state in EXECUTION_ROW.findall(plan):
        if finding_id in rows:
            errors.append(f"plan execution table repeats {finding_id}")
        rows[finding_id] = (severity, state.strip())

    findings: dict[str, PlanFinding] = {}
    for finding_id, title in PARENT_HEADING.findall(plan):
        if finding_id in findings:
            errors.append(f"plan defines {finding_id} more than once")
            continue
        if finding_id not in rows:
            errors.append(f"plan heading {finding_id} has no execution-register row")
            continue
        severity, state = rows[finding_id]
        findings[finding_id] = PlanFinding(title.strip(), severity, None, state)

    for finding_id, title in CHILD_HEADING.findall(plan):
        if finding_id in findings:
            errors.append(f"plan defines {finding_id} more than once")
            continue
        parent = finding_id[:-1]
        if parent not in rows:
            errors.append(f"plan child {finding_id} has no registered parent {parent}")
            continue
        findings[finding_id] = PlanFinding(
            title.strip(), rows[parent][0], parent, "OPEN"
        )

    for finding_id in sorted(set(rows) - set(findings)):
        errors.append(f"plan execution row {finding_id} has no finding heading")
    return findings


def _resolve_local_path(
    root: Path, value: str, label: str, errors: list[str]
) -> Path | None:
    """Resolve a repository-relative path without allowing it to escape."""
    candidate = Path(value)
    if candidate.is_absolute():
        errors.append(f"{label} must be repository-relative: {value}")
        return None
    resolved_root = root.resolve()
    resolved = (root / candidate).resolve()
    if not resolved.is_relative_to(resolved_root):
        errors.append(f"{label} escapes the repository: {value}")
        return None
    return resolved


def _frontmatter(path: Path, errors: list[str]) -> tuple[object | None, str]:
    """Return YAML frontmatter and Markdown body from one closure packet."""
    raw = _read_text(path, "closure packet", errors)
    if raw is None:
        return None, ""
    lines = raw.splitlines()
    if not lines or lines[0] != "---":
        errors.append(f"closure packet has no YAML frontmatter: {path}")
        return None, raw
    try:
        end = lines.index("---", 1)
    except ValueError:
        errors.append(f"closure packet frontmatter is not terminated: {path}")
        return None, raw
    try:
        document = yaml.safe_load("\n".join(lines[1:end]))
    except yaml.YAMLError as exc:
        errors.append(f"closure packet frontmatter is invalid YAML: {path}: {exc}")
        return None, "\n".join(lines[end + 1 :])
    return document, "\n".join(lines[end + 1 :])


def _high_impact(finding: dict[str, object]) -> bool:
    """Whether plan policy requires review separate from the implementer."""
    finding_id = cast(str, finding["id"])
    return (
        finding["severity"] == "P0"
        or finding_id.startswith("HW-")
        or finding_id.startswith("GAP-09")
        or finding_id.startswith("GAP-10")
    )


def _identity_is_placeholder(value: str) -> bool:
    """Reject generic identities that do not name an accountable person or agent."""
    normalized = " ".join(value.casefold().split())
    if not normalized:
        return True
    placeholders = {"agent", "independent agent", "pending", "tbd", "unassigned"}
    return normalized in placeholders or any(
        marker in normalized for marker in (" pending", "tbd", "unassigned")
    )


def _verify_commit(root: Path, commit: str, label: str, errors: list[str]) -> None:
    """Require the implementation commit to resolve when Git is present."""
    if not (root / ".git").exists():
        return
    git = shutil.which("git")
    if git is None:
        errors.append(f"{label} cannot verify its commit because git is unavailable")
        return
    result = subprocess.run(  # noqa: S603
        [git, "cat-file", "-e", f"{commit}^{{commit}}"],
        cwd=root,
        capture_output=True,
        check=False,
        text=True,
    )
    if result.returncode != 0:
        errors.append(
            f"{label} names implementation commit {commit}, which does not resolve"
        )


def _verify_closure(
    root: Path,
    finding: dict[str, object],
    path: Path,
    schema: dict[str, object],
    evidence_values: list[str],
    errors: list[str],
) -> None:
    """Validate a closed finding's packet, hashes, and reviewer separation."""
    finding_id = cast(str, finding["id"])
    document, body = _frontmatter(path, errors)
    if document is None:
        return
    packet_errors = _schema_errors(document, schema, f"{finding_id} closure")
    errors.extend(packet_errors)
    if packet_errors or not isinstance(document, dict):
        return
    packet = cast(dict[str, object], document)
    if packet["finding_id"] != finding_id:
        errors.append(
            f"{finding_id} closure packet identifies {packet['finding_id']!r} instead"
        )
    if packet["reviewer"] != finding["reviewer"]:
        errors.append(
            f"{finding_id} reviewer differs between register and closure packet"
        )
    if packet["operator"] != finding["owner"]:
        errors.append(f"{finding_id} operator differs from the registered owner")
    if "## Summary" not in body or "## Closure rationale" not in body:
        errors.append(
            f"{finding_id} closure packet needs '## Summary' and "
            "'## Closure rationale' sections"
        )

    if _high_impact(finding):
        operator = cast(str, packet["operator"])
        reviewer = cast(str, packet["reviewer"])
        approver = cast(str, packet["closure_approved_by"])
        if reviewer == operator:
            errors.append(f"{finding_id} high-impact closure is self-reviewed")
        if approver == operator:
            errors.append(f"{finding_id} high-impact closure is self-approved")
        if _identity_is_placeholder(reviewer):
            errors.append(f"{finding_id} closure packet does not name its reviewer")
        if _identity_is_placeholder(approver):
            errors.append(f"{finding_id} closure packet does not name its approver")

    _verify_commit(
        root,
        cast(str, packet["implementation_commit"]),
        f"{finding_id} closure",
        errors,
    )

    evidence_root = (root / EVIDENCE_RELATIVE / finding_id).resolve()
    for artifact_value in cast(list[dict[str, object]], packet["artifacts"]):
        value = cast(str, artifact_value["path"])
        if value not in evidence_values:
            errors.append(
                f"{finding_id} closure artifact is not linked from the register: "
                f"{value}"
            )
        artifact = _resolve_local_path(root, value, f"{finding_id} artifact", errors)
        if artifact is None:
            continue
        if not artifact.is_relative_to(evidence_root):
            errors.append(
                f"{finding_id} artifact is outside its evidence directory: {value}"
            )
            continue
        if not artifact.is_file():
            errors.append(f"{finding_id} artifact does not exist: {value}")
            continue
        actual = hashlib.sha256(artifact.read_bytes()).hexdigest()
        expected = cast(str, artifact_value["sha256"])
        if actual != expected:
            errors.append(
                f"{finding_id} artifact hash mismatch for {value}: "
                f"expected {expected}, got {actual}"
            )


def _dependency_errors(findings: list[dict[str, object]]) -> list[str]:
    """Reject unresolved, self-referential, or cyclic dependencies."""
    errors: list[str] = []
    by_id = {cast(str, finding["id"]): finding for finding in findings}
    for finding_id, finding in by_id.items():
        for dependency in cast(list[str], finding["dependencies"]):
            if dependency == finding_id:
                errors.append(f"{finding_id} depends on itself")
            elif dependency not in by_id:
                errors.append(f"{finding_id} depends on unknown finding {dependency}")

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(finding_id: str, trail: tuple[str, ...]) -> None:
        if finding_id in visiting:
            cycle = " -> ".join((*trail, finding_id))
            errors.append(f"finding dependency cycle: {cycle}")
            return
        if finding_id in visited or finding_id not in by_id:
            return
        visiting.add(finding_id)
        for dependency in cast(list[str], by_id[finding_id]["dependencies"]):
            visit(dependency, (*trail, finding_id))
        visiting.remove(finding_id)
        visited.add(finding_id)

    for finding_id in by_id:
        visit(finding_id, ())
    return errors


def validate_repository(root: Path) -> list[str]:
    """Return every findings-register defect in one repository tree."""
    errors: list[str] = []
    plan_path = root / PLAN_NAME
    register_path = root / REGISTER_RELATIVE
    plan = _read_text(plan_path, "remediation plan", errors)
    register = _load_yaml(register_path, "findings register", errors)
    register_schema = _load_schema(
        root / REGISTER_SCHEMA_RELATIVE, "findings register schema", errors
    )
    closure_schema = _load_schema(
        root / CLOSURE_SCHEMA_RELATIVE, "closure packet schema", errors
    )
    if (
        plan is None
        or register is None
        or register_schema is None
        or closure_schema is None
    ):
        return errors

    register_errors = _schema_errors(register, register_schema, "findings register")
    errors.extend(register_errors)
    if register_errors or not isinstance(register, dict):
        return errors
    raw_findings = register.get("findings")
    if not isinstance(raw_findings, list):
        return errors
    findings = [
        cast(dict[str, object], finding)
        for finding in raw_findings
        if isinstance(finding, dict)
    ]

    plan_findings = _plan_findings(plan, errors)
    ids = [cast(str, finding["id"]) for finding in findings]
    counts = Counter(ids)
    for finding_id in sorted(
        finding_id for finding_id, count in counts.items() if count > 1
    ):
        errors.append(f"findings register repeats {finding_id}")
    register_ids = set(ids)
    plan_ids = set(plan_findings)
    missing = plan_ids - register_ids
    extra = register_ids - plan_ids
    for finding_id in sorted(missing):
        errors.append(f"plan finding {finding_id} is missing from the register")
    for finding_id in sorted(extra):
        errors.append(f"register finding {finding_id} does not exist in the plan")

    by_id = {cast(str, finding["id"]): finding for finding in findings}
    for finding_id in sorted(plan_ids & register_ids):
        finding = by_id[finding_id]
        expected = plan_findings[finding_id]
        if finding["title"] != expected.title:
            errors.append(f"{finding_id} title differs between plan and register")
        if finding["severity"] != expected.severity:
            errors.append(f"{finding_id} severity differs between plan and register")
        if finding["parent"] != expected.parent:
            errors.append(f"{finding_id} parent differs between plan and register")
        if expected.parent is None and finding["state"] != expected.state:
            errors.append(f"{finding_id} state differs between plan and register")

    errors.extend(_dependency_errors(findings))
    for finding in findings:
        finding_id = cast(str, finding["id"])
        evidence_values = cast(list[str], finding["evidence"])
        expected_closure = root / EVIDENCE_RELATIVE / finding_id / "closure.md"
        closure_paths: list[Path] = []
        for value in evidence_values:
            resolved = _resolve_local_path(
                root, value, f"{finding_id} evidence link", errors
            )
            if resolved is None:
                continue
            evidence_root = (root / EVIDENCE_RELATIVE / finding_id).resolve()
            if not resolved.is_relative_to(evidence_root):
                errors.append(
                    f"{finding_id} evidence is outside its finding directory: {value}"
                )
                continue
            if not resolved.is_file():
                errors.append(f"{finding_id} evidence link does not resolve: {value}")
                continue
            if resolved.name == "closure.md":
                closure_paths.append(resolved)

        state = cast(str, finding["state"])
        if state == "CLOSED" and closure_paths != [expected_closure.resolve()]:
            errors.append(
                f"{finding_id} is CLOSED without exactly "
                f"{expected_closure.relative_to(root)}"
            )
        if state != "CLOSED" and closure_paths:
            errors.append(f"{finding_id} is not CLOSED but links a closure packet")
        if state == "CLOSED" and closure_paths == [expected_closure.resolve()]:
            _verify_closure(
                root,
                finding,
                closure_paths[0],
                closure_schema,
                evidence_values,
                errors,
            )
        if state == "CLOSED":
            open_dependencies = sorted(
                dependency
                for dependency in cast(list[str], finding["dependencies"])
                if dependency in by_id and by_id[dependency]["state"] != "CLOSED"
            )
            if open_dependencies:
                errors.append(
                    f"{finding_id} is CLOSED while dependencies remain open: "
                    + ", ".join(open_dependencies)
                )

    for parent_id, parent in by_id.items():
        if parent["state"] != "CLOSED":
            continue
        open_children = sorted(
            cast(str, child["id"])
            for child in findings
            if child["parent"] == parent_id and child["state"] != "CLOSED"
        )
        if open_children:
            errors.append(
                f"{parent_id} is CLOSED while child findings remain open: "
                + ", ".join(open_children)
            )
    return errors


def main(argv: list[str]) -> int:
    """Validate one repository root and return a process exit status."""
    if len(argv) > 1:
        print("Usage: tools/validate-findings.py [REPOSITORY_ROOT]", file=sys.stderr)
        return 2
    root = Path(argv[0]) if argv else REPO_ROOT
    errors = validate_repository(root)
    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        print(f"Findings register: {len(errors)} defect(s).", file=sys.stderr)
        return 1

    register = cast(
        dict[str, object],
        yaml.safe_load((root / REGISTER_RELATIVE).read_text(encoding="utf-8")),
    )
    count = len(cast(list[object], register["findings"]))
    print(f"Findings register: {count} finding(s), 0 defects.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
