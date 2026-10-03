"""Tests for tools/validate-identifiers.py.

The check exists so a capture filed without scrubbing is refused rather than
published. These assert both directions: it fires on what a real arm64 article
would actually leak, and it stays silent on the synthetic addresses that make up
most of the committed evidence base.
"""

from __future__ import annotations

import importlib.util
import shutil
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
_SPEC = importlib.util.spec_from_file_location(
    "validate_identifiers", REPO / "tools" / "validate-identifiers.py"
)
assert _SPEC is not None and _SPEC.loader is not None
checker = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(checker)


def _sandbox(tmp_path: Path) -> Path:
    """Build a minimal tree the checker can scan: the tool it imports, plus evidence."""
    (tmp_path / "tools").mkdir()
    shutil.copy(REPO / "tools" / "scrub-telemetry.py", tmp_path / "tools")
    (tmp_path / "docs" / "evidence" / "TBR-X").mkdir(parents=True)
    return tmp_path


def test_the_committed_tree_is_clean(tmp_path: Path) -> None:
    """The real repository must pass, or the check is unlandable."""
    assert checker.findings(REPO) == []


def test_equipment_mac_is_refused(tmp_path: Path) -> None:
    """A Raspberry Pi OUI is a real part's address."""
    root = _sandbox(tmp_path)
    (root / "docs/evidence/TBR-X/capture.txt").write_text("Station dc:a6:32:aa:bb:cc\n")
    found = checker.findings(root)
    assert len(found) == 1
    assert "equipment MAC" in found[0]


def test_link_local_encoding_an_equipment_mac_is_refused(tmp_path: Path) -> None:
    """The leak a MAC-only check misses: fe80:: carries no MAC-shaped text."""
    root = _sandbox(tmp_path)
    (root / "docs/evidence/TBR-X/addr.txt").write_text(
        "inet6 fe80::dea6:32ff:feaa:bbcc/64\n"
    )
    found = checker.findings(root)
    assert len(found) == 1
    assert "dc:a6:32:aa:bb:cc" in found[0]


def test_virtual_addresses_are_not_refused(tmp_path: Path) -> None:
    """hwsim, veth, broadcast and a certificate fingerprint are all fine."""
    root = _sandbox(tmp_path)
    (root / "docs/evidence/TBR-X/hwsim.txt").write_text(
        "orig 1e:fa:23:ea:fb:69\nbroadcast ff:ff:ff:ff:ff:ff\n"
        "fingerprint F7:8C:72:75:9B:4C:D7:41:71:BC\n"
        "inet6 fe80::4c59:ecff:fee3:6716/64\n"
    )
    assert checker.findings(root) == []


def test_archived_upstream_source_is_skipped(tmp_path: Path) -> None:
    """A vendor .proto carries documentation addresses, not this deployment's."""
    root = _sandbox(tmp_path)
    (root / "docs/evidence/TBR-X/upstream.proto").write_text("// dc:a6:32:aa:bb:cc\n")
    assert checker.findings(root) == []


def test_a_working_file_outside_evidence_is_not_scanned(tmp_path: Path) -> None:
    """The check governs what is published, not what is on somebody's disk."""
    root = _sandbox(tmp_path)
    (root / "scratch").mkdir()
    (root / "scratch" / "capture.json").write_text("dc:a6:32:aa:bb:cc")
    assert checker.findings(root) == []


def test_exit_code_is_non_zero_when_something_is_found(tmp_path: Path) -> None:
    """A check that reports and exits zero is the failure this repository knows."""
    root = _sandbox(tmp_path)
    (root / "docs/evidence/TBR-X/capture.txt").write_text("dc:a6:32:aa:bb:cc\n")
    assert checker.main([str(root)]) == 1
    assert checker.main([str(REPO)]) == 0
