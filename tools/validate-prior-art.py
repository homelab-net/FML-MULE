#!/usr/bin/env python3
"""Validate the OSS-01 prior-art registry.

Usage:
    tools/validate-prior-art.py [REPOSITORY_ROOT]

The registry may baseline a candidate before its research is complete. Once a
candidate advances, the full intake record, immutable evaluated artifacts, and
evaluation document become mandatory. Architecture-changing reuse modes also
require a named project-owner approval reference.
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from collections.abc import Sequence
from datetime import date
from pathlib import Path
from typing import cast

import yaml
from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError

REPO_ROOT = Path(__file__).resolve().parent.parent
REGISTRY_RELATIVE = Path("docs/prior-art/registry.yml")
SCHEMA_RELATIVE = Path("docs/prior-art/registry.schema.json")
PRIOR_ART_RELATIVE = Path("docs/prior-art")
REQUIREMENTS_RELATIVE = Path("docs/verification/requirements.md")
FINDINGS_RELATIVE = Path("docs/findings/register.yml")

# OSS-01 execution-card version 1. Adding a directly selected component expands
# this finite corpus in the same change that proposes it.
REQUIRED_CANDIDATES = (
    "batman-adv",
    "chrony",
    "dnsmasq",
    "haproxy",
    "hostapd",
    "kiwix",
    "kolibri",
    "martin",
    "meshtastic",
    "morse-micro-driver",
    "morse-micro-firmware",
    "nftables",
    "nomadnet",
    "openssh-server",
    "openmanet-firmware",
    "openmanetd",
    "opentakserver",
    "pmtiles",
    "podman-quadlet",
    "postgresql",
    "project-nomad",
    "protomaps",
    "pytak",
    "reticulum",
    "step-ca",
    "systemd-networkd",
    "tailscale-client",
    "wpa-supplicant",
)

GIT_COMMIT = re.compile(r"^[0-9a-f]{40}$")
OCI_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
FLOATING_WORDS = {"head", "latest", "main", "master", "stable", "tip", "trunk"}
REUSE_REQUIRES_APPROVAL = {"adopt", "port", "wrap"}
PLACEHOLDER_WORDS = {"none", "pending", "tbd", "todo", "unapproved", "unknown"}


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
    """Load one YAML document without exposing a parser traceback."""
    raw = _read_text(path, label, errors)
    if raw is None:
        return None
    try:
        return yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        errors.append(f"{label} is not valid YAML: {path}: {exc}")
        return None


def _load_schema(path: Path, label: str, errors: list[str]) -> dict[str, object] | None:
    """Load and check one Draft 2020-12 JSON Schema."""
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
    """Return stable path-addressed schema diagnostics."""
    found = sorted(
        Draft202012Validator(schema).iter_errors(document),
        key=lambda error: (_json_path(tuple(error.absolute_path)), error.message),
    )
    return [
        f"{label} {_json_path(tuple(error.absolute_path))}: {error.message}"
        for error in found
    ]


def _resolve_prior_art_path(
    root: Path, value: str, label: str, errors: list[str]
) -> Path | None:
    """Resolve a prior-art path without permitting repository escape."""
    candidate = Path(value)
    expected = (root / PRIOR_ART_RELATIVE).resolve()
    resolved = (root / candidate).resolve()
    if candidate.is_absolute() or not resolved.is_relative_to(expected):
        errors.append(f"{label} escapes docs/prior-art: {value}")
        return None
    return resolved


def _placeholder(value: object) -> bool:
    """Whether an approval-like value fails to identify a real reference."""
    if not isinstance(value, str):
        return True
    normalized = " ".join(value.casefold().split())
    words = set(re.findall(r"[a-z0-9]+", normalized))
    return not normalized or bool(words & PLACEHOLDER_WORDS)


def _parse_date(value: object, label: str, errors: list[str]) -> date | None:
    """Parse a schema-shaped ISO date and retain an actionable diagnostic."""
    if not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        errors.append(f"{label} is not a calendar date: {value}")
        return None


def _requirement_ids(root: Path, errors: list[str]) -> set[str]:
    """Read the generated requirement identifiers from Markdown frontmatter."""
    raw = _read_text(root / REQUIREMENTS_RELATIVE, "requirements register", errors)
    if raw is None:
        return set()
    identifiers = set(re.findall(r"^  - id: (FML-REQ-[0-9]{3})$", raw, re.MULTILINE))
    if not identifiers:
        errors.append("requirements register contains no FML requirement identifiers")
    return identifiers


def _finding_ids(root: Path, errors: list[str]) -> set[str]:
    """Read finding identifiers from the machine-readable findings register."""
    document = _load_yaml(root / FINDINGS_RELATIVE, "findings register", errors)
    if not isinstance(document, dict) or not isinstance(document.get("findings"), list):
        if document is not None:
            errors.append("findings register has no findings list")
        return set()
    return {
        finding["id"]
        for finding in document["findings"]
        if isinstance(finding, dict) and isinstance(finding.get("id"), str)
    }


def _validate_artifact(
    candidate_id: str, index: int, artifact: dict[str, object], errors: list[str]
) -> None:
    """Reject mutable or ambiguous evaluated artifact identifiers."""
    kind = artifact.get("kind")
    immutable_id = artifact.get("immutable_id")
    version = artifact.get("version")
    label = f"{candidate_id} evaluated_artifacts[{index}]"
    if not isinstance(immutable_id, str) or not isinstance(version, str):
        return
    _parse_date(artifact.get("verified_on"), f"{label} verified_on", errors)
    if kind == "git" and not GIT_COMMIT.fullmatch(immutable_id):
        errors.append(f"{label} git immutable_id is not a 40-hex commit")
    elif kind == "oci" and not OCI_DIGEST.fullmatch(immutable_id):
        errors.append(f"{label} OCI immutable_id is not a sha256 digest")
    elif kind == "package":
        words = {part for part in re.split(r"[^a-z0-9]+", version.casefold()) if part}
        if words & FLOATING_WORDS or any(char in version for char in "*<>=~^"):
            errors.append(f"{label} package version is floating: {version}")
        if immutable_id != version:
            errors.append(f"{label} package immutable_id must equal its exact version")


def _validate_candidate(
    root: Path,
    candidate: dict[str, object],
    verification_date: date | None,
    requirement_ids: set[str],
    finding_ids: set[str],
    registered_documents: set[str],
    errors: list[str],
) -> None:
    """Apply cross-field OSS-01 controls to one schema-valid candidate."""
    candidate_id = cast(str, candidate["id"])
    document = candidate.get("evaluation_document")
    if isinstance(document, str):
        registered_documents.add(document)
        resolved = _resolve_prior_art_path(
            root, document, f"{candidate_id} evaluation_document", errors
        )
        if resolved is not None and not resolved.is_file():
            errors.append(
                f"{candidate_id} evaluation document does not resolve: {document}"
            )

    if candidate.get("state") == "BASELINED":
        return

    evaluated_on = _parse_date(
        candidate.get("evaluation_date"), f"{candidate_id} evaluation_date", errors
    )
    if evaluated_on is not None and verification_date is not None:
        age = (verification_date - evaluated_on).days
        if age < 0:
            errors.append(f"{candidate_id} evaluation date is in the future")
        elif age > 90:
            errors.append(f"{candidate_id} evaluation is stale at {age} days")

    artifacts = candidate.get("evaluated_artifacts")
    if isinstance(artifacts, list):
        for index, artifact in enumerate(artifacts):
            if isinstance(artifact, dict):
                _validate_artifact(candidate_id, index, artifact, errors)

    maintenance = candidate.get("maintenance")
    if isinstance(maintenance, dict):
        for field in ("latest_release_date", "last_commit_date"):
            _parse_date(
                maintenance.get(field), f"{candidate_id} maintenance.{field}", errors
            )

    security = candidate.get("security")
    if isinstance(security, dict):
        _parse_date(
            security.get("reviewed_on"),
            f"{candidate_id} security.reviewed_on",
            errors,
        )

    mappings = candidate.get("mappings")
    if isinstance(mappings, dict):
        requirements = mappings.get("requirements")
        if isinstance(requirements, list):
            for reference in requirements:
                if isinstance(reference, str) and reference not in requirement_ids:
                    errors.append(
                        f"{candidate_id} maps unknown requirement {reference}"
                    )
        findings = mappings.get("findings")
        if isinstance(findings, list):
            for reference in findings:
                if isinstance(reference, str) and reference not in finding_ids:
                    errors.append(f"{candidate_id} maps unknown finding {reference}")

    reuse = candidate.get("reuse")
    license_record = candidate.get("license")
    if not isinstance(reuse, dict) or not isinstance(license_record, dict):
        return
    mode = reuse.get("mode")
    compatibility = license_record.get("compatibility")
    if compatibility == "incompatible" and mode in REUSE_REQUIRES_APPROVAL:
        errors.append(f"{candidate_id} requests {mode} with an incompatible license")
    if mode in REUSE_REQUIRES_APPROVAL and _placeholder(reuse.get("approval_ref")):
        errors.append(f"{candidate_id} requests {mode} without owner approval")


def validate_repository(root: Path) -> list[str]:
    """Return every prior-art registry defect found below ``root``."""
    errors: list[str] = []
    document = _load_yaml(root / REGISTRY_RELATIVE, "prior-art registry", errors)
    schema = _load_schema(root / SCHEMA_RELATIVE, "prior-art schema", errors)
    if document is None or schema is None:
        return errors

    errors.extend(_schema_errors(document, schema, "prior-art registry"))
    if not isinstance(document, dict):
        return errors
    candidates = document.get("candidates")
    if not isinstance(candidates, list):
        return errors

    shaped = [item for item in candidates if isinstance(item, dict)]
    identifiers = [item.get("id") for item in shaped if isinstance(item.get("id"), str)]
    for candidate_id, count in sorted(Counter(identifiers).items()):
        if count > 1:
            errors.append(f"prior-art registry repeats candidate {candidate_id}")

    found = set(identifiers)
    for candidate_id in sorted(set(REQUIRED_CANDIDATES) - found):
        errors.append(f"required prior-art candidate is missing: {candidate_id}")
    for candidate_id in sorted(found - set(REQUIRED_CANDIDATES)):
        errors.append(f"unapproved prior-art candidate is registered: {candidate_id}")

    verification_date = _parse_date(
        document.get("verification_date"), "registry verification_date", errors
    )
    requirement_ids = _requirement_ids(root, errors)
    finding_ids = _finding_ids(root, errors)
    registered_documents: set[str] = set()
    for candidate in shaped:
        if isinstance(candidate.get("id"), str):
            _validate_candidate(
                root,
                candidate,
                verification_date,
                requirement_ids,
                finding_ids,
                registered_documents,
                errors,
            )

    supporting = document.get("supporting_documents")
    if isinstance(supporting, list):
        for value in supporting:
            if not isinstance(value, str):
                continue
            registered_documents.add(value)
            resolved = _resolve_prior_art_path(
                root, value, "supporting document", errors
            )
            if resolved is not None and not resolved.is_file():
                errors.append(f"supporting document does not resolve: {value}")

    directory = root / PRIOR_ART_RELATIVE
    if directory.is_dir():
        actual_documents = {
            path.relative_to(root).as_posix()
            for path in directory.rglob("*.md")
            if path.name != "README.md"
        }
        for value in sorted(actual_documents - registered_documents):
            errors.append(f"prior-art document is not registered: {value}")
    return errors


def main(argv: Sequence[str] | None = None) -> int:
    """Validate the selected repository and return a process exit code."""
    arguments = list(sys.argv[1:] if argv is None else argv)
    if len(arguments) > 1:
        print("usage: validate-prior-art.py [REPOSITORY_ROOT]", file=sys.stderr)
        return 2
    root = Path(arguments[0]) if arguments else REPO_ROOT
    errors = validate_repository(root)
    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        print(f"Prior-art registry: {len(errors)} defect(s).", file=sys.stderr)
        return 1
    print(f"Prior-art registry: {len(REQUIRED_CANDIDATES)} candidate(s), 0 defects.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
