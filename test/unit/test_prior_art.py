"""Tests for the machine-readable prior-art registry."""

from __future__ import annotations

import importlib.util
import shutil
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = Path("docs/prior-art/registry.yml")
SCHEMA_PATH = Path("docs/prior-art/registry.schema.json")
VALIDATOR_PATH = REPO_ROOT / "tools/validate-prior-art.py"
REFERENCE_PATHS = (
    Path("docs/verification/requirements.md"),
    Path("docs/findings/register.yml"),
)


def _load_validator() -> ModuleType:
    """Import the hyphenated validation script as a test module."""
    spec = importlib.util.spec_from_file_location("validate_prior_art", VALIDATOR_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def validator() -> ModuleType:
    """Return the prior-art validator module."""
    return _load_validator()


@pytest.fixture
def repository(tmp_path: Path) -> Path:
    """Copy the registry, schema, and registered documents into a temporary tree."""
    for relative in (REGISTRY_PATH, SCHEMA_PATH, *REFERENCE_PATHS):
        destination = tmp_path / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO_ROOT / relative, destination)
    document = _registry(tmp_path)
    paths = list(document["supporting_documents"])
    paths.extend(
        item["evaluation_document"]
        for item in document["candidates"]
        if item["evaluation_document"] is not None
    )
    for value in paths:
        relative = Path(value)
        destination = tmp_path / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO_ROOT / relative, destination)
    return tmp_path


def _registry(repository: Path) -> dict[str, Any]:
    """Load the temporary registry."""
    document = yaml.safe_load((repository / REGISTRY_PATH).read_text(encoding="utf-8"))
    assert isinstance(document, dict)
    return document


def _write_registry(repository: Path, document: dict[str, Any]) -> None:
    """Write one mutated registry fixture."""
    (repository / REGISTRY_PATH).write_text(
        yaml.safe_dump(document, sort_keys=False), encoding="utf-8"
    )


def _candidate(document: dict[str, Any], candidate_id: str) -> dict[str, Any]:
    """Return one candidate by stable identifier."""
    return next(item for item in document["candidates"] if item["id"] == candidate_id)


def _evaluate_project_nomad(repository: Path) -> dict[str, Any]:
    """Create one complete evaluated-record fixture and return the registry."""
    document = _registry(repository)
    candidate = _candidate(document, "project-nomad")
    evaluation_path = "docs/prior-art/project-nomad.md"
    candidate.update(
        {
            "state": "EVALUATED",
            "evaluation_document": evaluation_path,
            "evaluation_date": "2026-09-09",
            "evaluated_artifacts": [
                {
                    "kind": "git",
                    "source": "https://github.com/Crosstalk-Solutions/project-nomad",
                    "version": "v1.34.0",
                    "immutable_id": "1" * 40,
                    "verified_on": "2026-09-09",
                }
            ],
            "license": {
                "declared": "Apache-2.0",
                "source": "https://github.com/Crosstalk-Solutions/project-nomad/blob/main/LICENSE",
                "compatibility": "compatible",
                "bundled_dependencies": "pending",
                "notes": "Fixture license result.",
            },
            "maintenance": {
                "release_cadence": "Fixture cadence.",
                "latest_release_date": "2026-08-04",
                "last_commit_date": "2026-09-01",
                "issue_backlog": 1,
                "bus_factor": "Fixture observation.",
                "sources": ["https://github.com/Crosstalk-Solutions/project-nomad"],
            },
            "platform": {
                "hardware": [],
                "operating_systems": ["Linux"],
                "architectures": [],
                "sources": ["https://github.com/Crosstalk-Solutions/project-nomad"],
            },
            "resources": {"status": "not-measured", "measurements": []},
            "runtime": {
                "ports": [],
                "privileges": [],
                "capabilities": [],
                "mounts": [],
                "secrets": [],
                "authentication": "Fixture authentication result.",
                "update_behavior": "Fixture update result.",
                "sources": ["https://github.com/Crosstalk-Solutions/project-nomad"],
            },
            "data": {
                "formats": [],
                "persistence": "Fixture persistence result.",
                "backup": "Fixture backup result.",
                "migration": "Fixture migration result.",
                "sources": ["https://github.com/Crosstalk-Solutions/project-nomad"],
            },
            "security": {
                "reviewed_on": "2026-09-09",
                "advisory_sources": [
                    "https://github.com/Crosstalk-Solutions/project-nomad/security"
                ],
                "known_advisories": [],
                "audit_status": "Fixture audit result.",
                "sbom_status": "Fixture SBOM result.",
            },
            "mappings": {
                "requirements": ["FML-REQ-001"],
                "findings": ["OSS-01"],
            },
            "reuse": {
                "mode": "pattern-only",
                "rationale": "Fixture rationale.",
                "approval_ref": None,
            },
            "prototype": {
                "status": "not-run",
                "commands": [],
                "evidence": [],
                "gaps": [],
            },
            "exit_strategy": "Remove the reference without changing product code.",
            "decision_questions": [],
        }
    )
    target = repository / evaluation_path
    target.write_text("# Project N.O.M.A.D. fixture\n", encoding="utf-8")
    _write_registry(repository, document)
    return document


def test_prior_art_validator_exists() -> None:
    """OSS-01 shall provide an executable registry validator."""
    assert VALIDATOR_PATH.is_file()


def test_repository_registry_is_valid(validator: ModuleType) -> None:
    """The committed candidate corpus shall be schema-valid and complete."""
    assert validator.validate_repository(REPO_ROOT) == []


def test_complete_evaluated_candidate_is_accepted(
    repository: Path, validator: ModuleType
) -> None:
    """A complete immutable, evidence-linked intake record shall pass."""
    _evaluate_project_nomad(repository)
    assert validator.validate_repository(repository) == []


def test_missing_and_duplicate_candidates_are_rejected(
    repository: Path, validator: ModuleType
) -> None:
    """The approved corpus cannot shrink or duplicate an identifier."""
    document = _registry(repository)
    duplicate = dict(_candidate(document, "reticulum"))
    document["candidates"] = [
        item for item in document["candidates"] if item["id"] != "nomadnet"
    ]
    document["candidates"].append(duplicate)
    _write_registry(repository, document)

    errors = validator.validate_repository(repository)
    assert "required prior-art candidate is missing: nomadnet" in errors
    assert "prior-art registry repeats candidate reticulum" in errors


def test_incomplete_evaluation_is_rejected(
    repository: Path, validator: ModuleType
) -> None:
    """Changing only the state word cannot create an evaluated intake."""
    document = _registry(repository)
    _candidate(document, "kiwix")["state"] = "EVALUATED"
    _write_registry(repository, document)

    assert any(
        "evaluated_artifacts" in error and "required property" in error
        for error in validator.validate_repository(repository)
    )


def test_floating_git_reference_is_rejected(
    repository: Path, validator: ModuleType
) -> None:
    """A tag or branch name cannot stand in for an immutable commit."""
    document = _evaluate_project_nomad(repository)
    artifact = _candidate(document, "project-nomad")["evaluated_artifacts"][0]
    artifact["immutable_id"] = "main"
    _write_registry(repository, document)

    assert (
        "project-nomad evaluated_artifacts[0] git immutable_id is not a 40-hex commit"
        in validator.validate_repository(repository)
    )


def test_impossible_intake_dates_are_rejected(
    repository: Path, validator: ModuleType
) -> None:
    """Date-shaped strings shall still name real calendar dates."""
    document = _evaluate_project_nomad(repository)
    candidate = _candidate(document, "project-nomad")
    candidate["evaluated_artifacts"][0]["verified_on"] = "2026-99-99"
    candidate["maintenance"]["latest_release_date"] = "2026-02-30"
    candidate["maintenance"]["last_commit_date"] = "2026-13-01"
    candidate["security"]["reviewed_on"] = "2026-00-10"
    _write_registry(repository, document)

    errors = validator.validate_repository(repository)
    for field in (
        "evaluated_artifacts[0] verified_on",
        "maintenance.latest_release_date",
        "maintenance.last_commit_date",
        "security.reviewed_on",
    ):
        assert any(
            field in error and "is not a calendar date" in error for error in errors
        )


def test_evaluated_claims_require_sources_and_requirement_mapping(
    repository: Path, validator: ModuleType
) -> None:
    """An evaluated record cannot omit its evidence or FML requirement."""
    document = _evaluate_project_nomad(repository)
    candidate = _candidate(document, "project-nomad")
    for section in ("maintenance", "platform", "runtime", "data"):
        candidate[section]["sources"] = []
    candidate["security"]["advisory_sources"] = []
    candidate["mappings"]["requirements"] = []
    _write_registry(repository, document)

    errors = validator.validate_repository(repository)
    for field in (
        "maintenance.sources",
        "platform.sources",
        "runtime.sources",
        "data.sources",
        "security.advisory_sources",
        "mappings.requirements",
    ):
        assert any(
            field in error and "should be non-empty" in error for error in errors
        )


def test_evaluated_sources_cannot_be_whitespace(
    repository: Path, validator: ModuleType
) -> None:
    """Whitespace cannot stand in for a source-backed intake claim."""
    document = _evaluate_project_nomad(repository)
    candidate = _candidate(document, "project-nomad")
    for section in ("maintenance", "platform", "runtime", "data"):
        candidate[section]["sources"] = [" "]
    candidate["security"]["advisory_sources"] = [" "]
    _write_registry(repository, document)

    errors = validator.validate_repository(repository)
    for field in (
        "maintenance.sources[0]",
        "platform.sources[0]",
        "runtime.sources[0]",
        "data.sources[0]",
        "security.advisory_sources[0]",
    ):
        assert any(field in error and "does not match" in error for error in errors)


def test_mapped_requirements_and_findings_must_resolve(
    repository: Path, validator: ModuleType
) -> None:
    """Pattern-shaped identifiers cannot point outside the governed registers."""
    document = _evaluate_project_nomad(repository)
    candidate = _candidate(document, "project-nomad")
    candidate["mappings"] = {
        "requirements": ["FML-REQ-999"],
        "findings": ["GAP-99"],
    }
    _write_registry(repository, document)

    errors = validator.validate_repository(repository)
    assert "project-nomad maps unknown requirement FML-REQ-999" in errors
    assert "project-nomad maps unknown finding GAP-99" in errors


def test_required_narratives_cannot_be_whitespace(
    repository: Path, validator: ModuleType
) -> None:
    """Whitespace cannot satisfy any required narrative intake field."""
    document = _evaluate_project_nomad(repository)
    candidate = _candidate(document, "project-nomad")
    candidate["project"] = " "
    for section, fields in {
        "license": ("declared", "notes"),
        "maintenance": ("release_cadence", "bus_factor"),
        "runtime": ("authentication", "update_behavior"),
        "data": ("persistence", "backup", "migration"),
        "security": ("audit_status", "sbom_status"),
        "reuse": ("rationale",),
    }.items():
        for field in fields:
            candidate[section][field] = " "
    candidate["exit_strategy"] = " "
    _write_registry(repository, document)

    errors = validator.validate_repository(repository)
    for field in (
        "project",
        "license.declared",
        "license.notes",
        "maintenance.release_cadence",
        "maintenance.bus_factor",
        "runtime.authentication",
        "runtime.update_behavior",
        "data.persistence",
        "data.backup",
        "data.migration",
        "security.audit_status",
        "security.sbom_status",
        "reuse.rationale",
        "exit_strategy",
    ):
        assert any(field in error and "does not match" in error for error in errors)


def test_missing_escaping_and_unregistered_documents_are_rejected(
    repository: Path, validator: ModuleType
) -> None:
    """Every prior-art document shall resolve inside and from the registry."""
    document = _registry(repository)
    _candidate(document, "reticulum")["evaluation_document"] = (
        "docs/prior-art/missing.md"
    )
    _candidate(document, "nomadnet")["evaluation_document"] = "../outside.md"
    _write_registry(repository, document)
    orphan = repository / "docs/prior-art/nested/orphan.md"
    orphan.parent.mkdir()
    orphan.write_text("# Orphan\n", encoding="utf-8")

    errors = validator.validate_repository(repository)
    assert (
        "reticulum evaluation document does not resolve: docs/prior-art/missing.md"
        in errors
    )
    assert (
        "nomadnet evaluation_document escapes docs/prior-art: ../outside.md" in errors
    )
    assert (
        "prior-art document is not registered: docs/prior-art/nested/orphan.md"
        in errors
    )


def test_incompatible_license_cannot_request_adoption(
    repository: Path, validator: ModuleType
) -> None:
    """Owner approval cannot override a recorded incompatible license."""
    document = _evaluate_project_nomad(repository)
    candidate = _candidate(document, "project-nomad")
    candidate["license"]["compatibility"] = "incompatible"
    candidate["reuse"] = {
        "mode": "adopt",
        "rationale": "Fixture adoption request.",
        "approval_ref": "Project owner approval fixture.",
    }
    _write_registry(repository, document)

    assert "project-nomad requests adopt with an incompatible license" in (
        validator.validate_repository(repository)
    )


def test_architecture_reuse_requires_owner_approval(
    repository: Path, validator: ModuleType
) -> None:
    """Adopt, wrap, and port modes shall carry a named owner approval."""
    document = _evaluate_project_nomad(repository)
    candidate = _candidate(document, "project-nomad")
    candidate["reuse"] = {
        "mode": "wrap",
        "rationale": "Fixture wrapper request.",
        "approval_ref": "Project owner approval pending",
    }
    _write_registry(repository, document)

    assert "project-nomad requests wrap without owner approval" in (
        validator.validate_repository(repository)
    )
