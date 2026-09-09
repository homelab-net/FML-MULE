"""Tests for the machine-readable remediation findings register."""

from __future__ import annotations

import hashlib
import importlib.util
import re
import shutil
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
PLAN_NAME = "REMEDIATION-AND-CLOSURE-PLAN-2026-09-08.md"
REGISTER_PATH = Path("docs/findings/register.yml")
VALIDATOR_PATH = REPO_ROOT / "tools" / "validate-findings.py"


def _load_validator() -> ModuleType:
    """Import the hyphenated validation script as a test module."""
    spec = importlib.util.spec_from_file_location("validate_findings", VALIDATOR_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def validator() -> ModuleType:
    """Return the findings validator module."""
    return _load_validator()


@pytest.fixture
def repository(tmp_path: Path) -> Path:
    """Copy an open-state register fixture into a temporary tree.

    These tests exercise BASE-01 closure rules. Findings that close later in
    the remediation campaign must not make this isolated fixture depend on
    their evidence packets or Git history.
    """
    files = (
        Path(PLAN_NAME),
        REGISTER_PATH,
        Path("docs/findings/register.schema.json"),
        Path("docs/findings/closure-packet.schema.json"),
    )
    for relative in files:
        destination = tmp_path / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO_ROOT / relative, destination)
    document = _register(tmp_path)
    for finding in document["findings"]:
        finding["evidence"] = []
        if finding["state"] == "CLOSED":
            finding["state"] = "RED-TEAMED"
            if finding["parent"] is None:
                _set_plan_state(tmp_path, finding["id"], "RED-TEAMED")
    base = _finding(document, "BASE-01")
    base["reviewer"] = "Independent agent pending"
    _write_register(tmp_path, document)
    return tmp_path


def _register(repository: Path) -> dict[str, Any]:
    """Load the temporary findings register."""
    document = yaml.safe_load((repository / REGISTER_PATH).read_text(encoding="utf-8"))
    assert isinstance(document, dict)
    return document


def _write_register(repository: Path, document: dict[str, Any]) -> None:
    """Write a mutated temporary findings register."""
    (repository / REGISTER_PATH).write_text(
        yaml.safe_dump(document, sort_keys=False), encoding="utf-8"
    )


def _finding(document: dict[str, Any], finding_id: str) -> dict[str, Any]:
    """Return one finding from a loaded register."""
    return next(item for item in document["findings"] if item["id"] == finding_id)


def _set_plan_state(repository: Path, finding_id: str, state: str) -> None:
    """Set one parent state in the temporary plan execution table."""
    path = repository / PLAN_NAME
    raw = path.read_text(encoding="utf-8")
    pattern = re.compile(
        rf"(^\| {re.escape(finding_id)}\s*\|\s*P[0-3]\s*\|\s*)"
        r"[A-Z][A-Z _-]+?(\s*\|)",
        re.MULTILINE,
    )
    updated, count = pattern.subn(rf"\g<1>{state}\g<2>", raw)
    assert count == 1
    path.write_text(updated, encoding="utf-8")


def _close_base_01(repository: Path) -> Path:
    """Create a complete, internally consistent BASE-01 closure fixture."""
    document = _register(repository)
    finding = _finding(document, "BASE-01")
    finding["state"] = "CLOSED"
    finding["reviewer"] = "independent-reviewer"

    evidence_dir = repository / "docs/evidence/findings/BASE-01"
    evidence_dir.mkdir(parents=True)
    artifact = evidence_dir / "verification.txt"
    artifact.write_text("all checks passed\n", encoding="utf-8")
    artifact_path = "docs/evidence/findings/BASE-01/verification.txt"
    closure_path = "docs/evidence/findings/BASE-01/closure.md"
    finding["evidence"] = [closure_path, artifact_path]
    _write_register(repository, document)
    _set_plan_state(repository, "BASE-01", "CLOSED")

    packet = {
        "schema_version": "1.0",
        "finding_id": "BASE-01",
        "scope": "Machine-readable findings register and closure enforcement.",
        "governing_refs": [PLAN_NAME],
        "pre_fix_reproduction": "Validator was absent before the increment.",
        "expected_failure": "A missing validator shall fail the unit test.",
        "implementation_commit": "0" * 40,
        "files_changed": ["tools/validate-findings.py"],
        "tests": [
            {
                "name": "findings unit tests",
                "command": "pytest -q test/unit/test_findings.py",
                "exit_code": 0,
            }
        ],
        "environment": {
            "os": "test operating system",
            "python": "3.test",
            "tools": ["pytest"],
        },
        "artifacts": [
            {
                "path": artifact_path,
                "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
            }
        ],
        "date": "2026-09-09",
        "operator": "Codex",
        "reviewer": "independent-reviewer",
        "classification": "SIMULATED",
        "red_team_attempts": [
            {
                "attempt": "Removed a plan finding from the register.",
                "outcome": "Validator rejected the incomplete register.",
            }
        ],
        "residual_risks": [],
        "deferred_work": [],
        "closure_approved_by": "independent-approver",
        "redaction_statement": "Contains no credentials or deployment data.",
        "owner_approval_refs": ["Project owner approval on 2026-09-09"],
    }
    closure = evidence_dir / "closure.md"
    closure.write_text(
        "---\n"
        + yaml.safe_dump(packet, sort_keys=False)
        + "---\n\n## Summary\n\nFixture.\n\n"
        + "## Closure rationale\n\nAll machine checks pass.\n",
        encoding="utf-8",
    )
    return closure


def test_repository_register_is_valid(validator: ModuleType) -> None:
    """The committed register shall agree with every finding in the plan."""
    assert validator.validate_repository(REPO_ROOT) == []


def test_missing_plan_finding_is_rejected(
    repository: Path, validator: ModuleType
) -> None:
    """The register cannot silently omit a plan finding."""
    document = _register(repository)
    document["findings"] = [
        item for item in document["findings"] if item["id"] != "GAP-06"
    ]
    _write_register(repository, document)

    assert (
        "plan finding GAP-06 is missing from the register"
        in validator.validate_repository(repository)
    )


def test_duplicate_and_extra_finding_ids_are_rejected(
    repository: Path, validator: ModuleType
) -> None:
    """Every registered identifier shall be unique and originate in the plan."""
    document = _register(repository)
    duplicate = dict(_finding(document, "BASE-01"))
    extra = dict(_finding(document, "BASE-01"), id="GAP-99", title="Invented")
    document["findings"].extend([duplicate, extra])
    _write_register(repository, document)

    errors = validator.validate_repository(repository)
    assert "findings register repeats BASE-01" in errors
    assert "register finding GAP-99 does not exist in the plan" in errors


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("title", "Different title", "BASE-01 title differs between plan and register"),
        ("severity", "P1", "BASE-01 severity differs between plan and register"),
        ("state", "OPEN", "BASE-01 state differs between plan and register"),
    ],
)
def test_parent_plan_drift_is_rejected(
    repository: Path,
    validator: ModuleType,
    field: str,
    value: str,
    message: str,
) -> None:
    """Parent title, severity, and state shall remain synchronized with the plan."""
    document = _register(repository)
    _finding(document, "BASE-01")[field] = value
    _write_register(repository, document)

    assert message in validator.validate_repository(repository)


@pytest.mark.parametrize(
    ("dependencies", "message"),
    [
        (["GAP-99"], "BASE-01 depends on unknown finding GAP-99"),
        (["BASE-01"], "BASE-01 depends on itself"),
        (["BASE-02"], "finding dependency cycle: BASE-01 -> BASE-02 -> BASE-01"),
    ],
)
def test_invalid_dependencies_are_rejected(
    repository: Path,
    validator: ModuleType,
    dependencies: list[str],
    message: str,
) -> None:
    """Dependencies shall resolve without self-reference or cycles."""
    document = _register(repository)
    _finding(document, "BASE-01")["dependencies"] = dependencies
    _write_register(repository, document)

    assert message in validator.validate_repository(repository)


def test_evidence_escape_and_missing_file_are_rejected(
    repository: Path, validator: ModuleType
) -> None:
    """Evidence links shall stay in the finding directory and name real files."""
    document = _register(repository)
    _finding(document, "BASE-01")["evidence"] = [
        "../outside.txt",
        "docs/evidence/findings/BASE-01/missing.txt",
    ]
    _write_register(repository, document)

    errors = validator.validate_repository(repository)
    assert "BASE-01 evidence link escapes the repository: ../outside.txt" in errors
    assert (
        "BASE-01 evidence link does not resolve: "
        "docs/evidence/findings/BASE-01/missing.txt"
    ) in errors


def test_closed_finding_requires_exact_closure_packet(
    repository: Path, validator: ModuleType
) -> None:
    """Changing only the state word cannot close a finding."""
    document = _register(repository)
    _finding(document, "BASE-01")["state"] = "CLOSED"
    _write_register(repository, document)
    _set_plan_state(repository, "BASE-01", "CLOSED")

    errors = validator.validate_repository(repository)
    assert (
        "BASE-01 is CLOSED without exactly docs/evidence/findings/BASE-01/closure.md"
    ) in errors


def test_open_finding_cannot_link_closure_packet(
    repository: Path, validator: ModuleType
) -> None:
    """A closure packet cannot be linked before the finding is CLOSED."""
    closure = repository / "docs/evidence/findings/BASE-01/closure.md"
    closure.parent.mkdir(parents=True)
    closure.write_text("not yet closed\n", encoding="utf-8")
    document = _register(repository)
    _finding(document, "BASE-01")["evidence"] = [
        "docs/evidence/findings/BASE-01/closure.md"
    ]
    _write_register(repository, document)

    assert "BASE-01 is not CLOSED but links a closure packet" in (
        validator.validate_repository(repository)
    )


def test_complete_closure_packet_is_accepted(
    repository: Path, validator: ModuleType
) -> None:
    """A complete independently reviewed closure packet shall validate."""
    _close_base_01(repository)

    assert validator.validate_repository(repository) == []


def test_closure_identity_and_reviewer_separation_are_enforced(
    repository: Path, validator: ModuleType
) -> None:
    """High-impact closure cannot identify another finding or review itself."""
    closure = _close_base_01(repository)
    raw = closure.read_text(encoding="utf-8")
    raw = raw.replace("finding_id: BASE-01", "finding_id: BASE-02")
    raw = raw.replace("reviewer: independent-reviewer", "reviewer: Codex")
    raw = raw.replace(
        "closure_approved_by: independent-approver",
        "closure_approved_by: Codex",
    )
    closure.write_text(raw, encoding="utf-8")
    document = _register(repository)
    _finding(document, "BASE-01")["reviewer"] = "Codex"
    _write_register(repository, document)

    errors = validator.validate_repository(repository)
    assert "BASE-01 closure packet identifies 'BASE-02' instead" in errors
    assert "BASE-01 high-impact closure is self-reviewed" in errors
    assert "BASE-01 high-impact closure is self-approved" in errors


def test_failing_test_result_prevents_closure(
    repository: Path, validator: ModuleType
) -> None:
    """A packet cannot close a finding while any recorded test is failing."""
    closure = _close_base_01(repository)
    closure.write_text(
        closure.read_text(encoding="utf-8").replace("exit_code: 0", "exit_code: 1"),
        encoding="utf-8",
    )

    assert any(
        "BASE-01 closure $.tests[0].exit_code" in error and "0 was expected" in error
        for error in validator.validate_repository(repository)
    )


def test_closed_finding_requires_closed_dependencies(
    repository: Path, validator: ModuleType
) -> None:
    """A finding cannot close before each declared prerequisite closes."""
    document = _register(repository)
    _finding(document, "BASE-02")["state"] = "CLOSED"
    _write_register(repository, document)
    _set_plan_state(repository, "BASE-02", "CLOSED")

    assert "BASE-02 is CLOSED while dependencies remain open: BASE-01" in (
        validator.validate_repository(repository)
    )


def test_placeholder_reviewer_and_mismatched_operator_are_rejected(
    repository: Path, validator: ModuleType
) -> None:
    """Closure identities shall name the registered independent participants."""
    closure = _close_base_01(repository)
    raw = closure.read_text(encoding="utf-8")
    raw = raw.replace("operator: Codex", "operator: different-operator")
    raw = raw.replace(
        "reviewer: independent-reviewer", "reviewer: Independent agent pending"
    )
    closure.write_text(raw, encoding="utf-8")
    document = _register(repository)
    _finding(document, "BASE-01")["reviewer"] = "Independent agent pending"
    _write_register(repository, document)

    errors = validator.validate_repository(repository)
    assert "BASE-01 operator differs from the registered owner" in errors
    assert "BASE-01 closure packet does not name its reviewer" in errors


def test_whitespace_only_identity_is_rejected(
    repository: Path, validator: ModuleType
) -> None:
    """Whitespace cannot satisfy a named-reviewer closure requirement."""
    closure = _close_base_01(repository)
    closure.write_text(
        closure.read_text(encoding="utf-8").replace(
            "reviewer: independent-reviewer", "reviewer: ' '"
        ),
        encoding="utf-8",
    )
    document = _register(repository)
    _finding(document, "BASE-01")["reviewer"] = " "
    _write_register(repository, document)

    errors = validator.validate_repository(repository)
    assert any("findings register $.findings[0].reviewer" in error for error in errors)
    assert validator._identity_is_placeholder(" ")


def test_closure_artifact_link_and_hash_are_enforced(
    repository: Path, validator: ModuleType
) -> None:
    """Closure artifacts shall be registered and retain their recorded bytes."""
    _close_base_01(repository)
    document = _register(repository)
    _finding(document, "BASE-01")["evidence"] = [
        "docs/evidence/findings/BASE-01/closure.md"
    ]
    _write_register(repository, document)
    artifact = repository / "docs/evidence/findings/BASE-01/verification.txt"
    artifact.write_text("changed after hashing\n", encoding="utf-8")

    errors = validator.validate_repository(repository)
    assert (
        "BASE-01 closure artifact is not linked from the register: "
        "docs/evidence/findings/BASE-01/verification.txt"
    ) in errors
    assert any("BASE-01 artifact hash mismatch" in error for error in errors)


def test_closed_parent_cannot_have_open_children(
    repository: Path, validator: ModuleType
) -> None:
    """A parent cannot close while any of its child findings remains open."""
    document = _register(repository)
    _finding(document, "GAP-09")["state"] = "CLOSED"
    _write_register(repository, document)
    _set_plan_state(repository, "GAP-09", "CLOSED")

    assert any(
        error.startswith("GAP-09 is CLOSED while child findings remain open:")
        for error in validator.validate_repository(repository)
    )


def test_main_reports_defects_without_traceback(
    repository: Path, validator: ModuleType, capsys: pytest.CaptureFixture[str]
) -> None:
    """The command-line interface shall return stable actionable diagnostics."""
    (repository / REGISTER_PATH).unlink()

    assert validator.main([str(repository)]) == 1
    captured = capsys.readouterr()
    assert "FAIL: cannot read findings register:" in captured.err
    assert "Findings register: 1 defect(s)." in captured.err
