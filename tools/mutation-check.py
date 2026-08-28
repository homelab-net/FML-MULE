#!/usr/bin/env python3
"""Check that the test suite can actually detect a broken node.

Usage:
    tools/mutation-check.py [--list] [--only M07,M12]

A passing test suite proves the tests agree with the code. It does not prove
the tests would notice if the code were wrong, and those are different claims.
This tool checks the second one: it breaks the node in one specific way, runs
the suite, and expects it to fail. A mutation the suite still passes is a
**survivor** - a defect the tests cannot see.

The mutations live in ``test/flatsat/mutations.yml``, not in this file. They are
the specification of what the suite must detect, so they are reviewable data
rather than literals buried in a script.

**This tool never touches the working tree.** It copies the tracked files into
a temporary directory and mutates the copy, the same way ``test/unit`` plants
its violations. An earlier version edited in place and restored afterwards,
which was correct but made ``git status`` report phantom modifications for the
length of a run: a stop hook and a concurrent test run were both misled by it
before this changed.

Exit codes: 0 every mutation was caught, 1 at least one survived, 2 a mutation
no longer applies and the list needs updating.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
MUTATIONS = REPO_ROOT / "test" / "flatsat" / "mutations.yml"


@dataclass(frozen=True)
class Mutation:
    """One deliberate break, and what it simulates."""

    id: str
    path: Path
    find: str
    replace: str
    describe: str


@contextmanager
def tracked_copy() -> Iterator[Path]:
    """Yield a temporary copy of the tracked tree, removed on the way out.

    Tracked files only, so a stray build artifact or a half-finished scratch
    file cannot change what the suite sees. The mutation run then has a tree of
    its own and the real one stays readable by anything else looking at it.
    """
    # Resolved rather than spelled "git", so the subprocess cannot pick up
    # something else named git from a caller's PATH.
    git = shutil.which("git")
    if git is None:
        message = "git is not on PATH, so the tracked file list cannot be read."
        raise RuntimeError(message)

    # S603 flags any subprocess whose executable is not a literal. Here it is
    # the resolved path of git and the arguments are constants, so there is no
    # untrusted input to check. Suppressed on this line only.
    listing = subprocess.run(  # noqa: S603
        [git, "ls-files", "-z"],
        cwd=REPO_ROOT,
        capture_output=True,
        check=True,
        text=True,
    )
    with tempfile.TemporaryDirectory(prefix="fml-mutation-") as tmp:
        root = Path(tmp)
        for name in listing.stdout.split("\0"):
            if not name:
                continue
            destination = root / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(REPO_ROOT / name, destination)
        yield root


def load_mutations(root: Path) -> list[Mutation]:
    """Read the mutation specification, resolving paths against `root`."""
    with MUTATIONS.open(encoding="utf-8") as handle:
        document = yaml.safe_load(handle)
    return [
        Mutation(
            id=entry["id"],
            path=root / entry["file"],
            # Block scalars carry a trailing newline that is an artifact of the
            # YAML, not part of the code being matched.
            find=entry["find"].rstrip("\n"),
            replace=entry["replace"].rstrip("\n"),
            describe=entry["describe"],
        )
        for entry in document["mutations"]
    ]


#: pytest's own exit codes. Only these two are meaningful here: anything else
#: means the suite could not run, which is not the same as noticing a defect.
PYTEST_ALL_PASSED = 0
PYTEST_TESTS_FAILED = 1


def run_suite(root: Path) -> int:
    """Run the test suite quietly in `root` and return pytest's exit code."""
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "--no-header", "-x"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode


def apply_and_test(mutation: Mutation, root: Path) -> str:
    """Apply one mutation, run the suite, restore the file, report the verdict.

    Returns "killed" when a test failed, "SURVIVED" when the suite still
    passed, "NOT-APPLIED" when the mutation no longer matches the source it was
    written against, and "BROKE-SUITE" when pytest could not run at all.
    """
    original = mutation.path.read_text(encoding="utf-8")
    if mutation.find not in original:
        return "NOT-APPLIED"
    try:
        mutation.path.write_text(
            original.replace(mutation.find, mutation.replace, 1), encoding="utf-8"
        )
        code = run_suite(root)
    finally:
        mutation.path.write_text(original, encoding="utf-8")

    if code == PYTEST_TESTS_FAILED:
        return "killed"
    if code == PYTEST_ALL_PASSED:
        return "SURVIVED"
    # Any other code means pytest could not run the suite - a collection error,
    # an import failure, no tests found. That is not a test noticing a defect,
    # and scoring it as one would let a mutation that merely breaks a module
    # inflate the result. It is reported as broken so the mutation gets fixed.
    return "BROKE-SUITE"


def main(argv: list[str]) -> int:
    """Run every mutation and report the survivors."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--list", action="store_true", help="list the mutations and exit"
    )
    parser.add_argument(
        "--only", default=None, help="comma-separated mutation ids to run"
    )
    args = parser.parse_args(argv)

    # Listing needs no copy: it reads the specification and nothing else.
    if args.list:
        for mutation in load_mutations(REPO_ROOT):
            if not args.only or mutation.id in {
                m.strip() for m in args.only.split(",")
            }:
                print(f"{mutation.id}  {mutation.describe}")
        return 0

    with tracked_copy() as root:
        mutations = load_mutations(root)
        if args.only:
            wanted = {m.strip() for m in args.only.split(",")}
            mutations = [m for m in mutations if m.id in wanted]

        if run_suite(root) != PYTEST_ALL_PASSED:
            print(
                "ERROR: the suite fails before any mutation is applied.",
                file=sys.stderr,
            )
            return 2

        survivors: list[Mutation] = []
        stale: list[Mutation] = []
        for mutation in mutations:
            verdict = apply_and_test(mutation, root)
            print(f"  {mutation.id} {verdict:11s} {mutation.describe}")
            if verdict == "SURVIVED":
                survivors.append(mutation)
            elif verdict in {"NOT-APPLIED", "BROKE-SUITE"}:
                stale.append(mutation)

    caught = len(mutations) - len(survivors) - len(stale)
    print(f"\n{caught}/{len(mutations)} mutations caught.")

    if stale:
        print(
            "\nThese mutations did not produce a test failure the suite could "
            "report: they no longer match their source, or they broke the "
            "suite outright. Either way they are not evidence of anything. "
            "Update or remove them:",
            file=sys.stderr,
        )
        for mutation in stale:
            relative = mutation.path.relative_to(root)
            print(f"  {mutation.id} in {relative}", file=sys.stderr)
        return 2

    if survivors:
        print(
            "\nSURVIVORS. The suite passes with each of these breaks in place, "
            "so it cannot detect them:",
            file=sys.stderr,
        )
        for mutation in survivors:
            print(f"  {mutation.id} {mutation.describe}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
