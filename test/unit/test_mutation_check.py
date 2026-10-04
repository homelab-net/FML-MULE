"""Tests for the parallel scheduling in tools/mutation-check.py.

The tool's own subject, whether the suite catches each mutation, is exercised
by running it in tools/lint.sh. These tests cover only what running it in
parallel could break: the report order, and two suite runs sharing a tree. They
use a fake test function, because running the real suite from inside the suite
would recurse through every mutation.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
import threading
import time
from pathlib import Path
from types import ModuleType
from typing import Any, Protocol

import pytest


class _Identified(Protocol):
    id: str


REPO_ROOT = Path(__file__).resolve().parents[2]
TOOL_PATH = REPO_ROOT / "tools" / "mutation-check.py"


@pytest.fixture
def tool() -> ModuleType:
    """Import the hyphenated mutation-check script as a module."""
    spec = importlib.util.spec_from_file_location("mutation_check", TOOL_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _mutations(tool: ModuleType, count: int) -> list[Any]:
    return [
        tool.Mutation(
            id=f"M{index:02d}",
            path=Path("x.py"),
            find="a",
            replace="b",
            describe="",
        )
        for index in range(count)
    ]


def test_verdicts_come_back_in_specification_order(
    tool: ModuleType, tmp_path: Path
) -> None:
    """A run that finishes early does not move its verdict up the report."""
    mutations = _mutations(tool, 8)
    roots = [tmp_path / f"r{index}" for index in range(4)]

    def fake(mutation: _Identified, _root: Path) -> str:
        # Earlier mutations take longer, so completion order is reversed.
        time.sleep(0.01 * (len(mutations) - int(mutation.id[1:])))
        return mutation.id

    assert list(tool.run_all(mutations, roots, fake)) == [m.id for m in mutations]


def test_no_two_runs_share_a_tree_and_every_tree_is_used(
    tool: ModuleType, tmp_path: Path
) -> None:
    """Each concurrent run holds a tree of its own, and the work is spread."""
    mutations = _mutations(tool, 12)
    roots = [tmp_path / f"r{index}" for index in range(3)]
    in_use: set[Path] = set()
    used: set[Path] = set()
    lock = threading.Lock()
    collisions: list[Path] = []

    def fake(_mutation: object, root: Path) -> str:
        with lock:
            if root in in_use:
                collisions.append(root)
            in_use.add(root)
            used.add(root)
        time.sleep(0.02)
        with lock:
            in_use.discard(root)
        return "killed"

    list(tool.run_all(mutations, roots, fake))
    assert collisions == []
    assert used == set(roots)


def test_each_tree_gets_its_own_pytest_temporary_directory(
    tool: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Runs do not share pytest's default basetemp, and it is not in the tree."""
    seen: list[list[str]] = []

    def fake_run(args: list[str], **_kwargs: object) -> subprocess.CompletedProcess:
        seen.append(args)
        return subprocess.CompletedProcess(args, 0)

    monkeypatch.setattr(tool.subprocess, "run", fake_run)
    first, second = tmp_path / "w0" / "tree", tmp_path / "w1" / "tree"
    tool.run_suite(first)
    tool.run_suite(second)

    basetemps = [
        Path(arg.split("=", 1)[1])
        for args in seen
        for arg in args
        if arg.startswith("--basetemp=")
    ]
    assert len(basetemps) == 2
    assert basetemps[0] != basetemps[1]
    assert not basetemps[0].is_relative_to(first)
    assert not basetemps[1].is_relative_to(second)
