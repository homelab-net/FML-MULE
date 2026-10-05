#!/usr/bin/env python3
"""Check that the test suite can actually detect a broken node.

Usage:
    tools/mutation-check.py [--list] [--only M07,M12] [--jobs N]

A passing test suite proves the tests agree with the code. It does not prove
the tests would notice if the code were wrong, and those are different claims.
This tool checks the second one: it breaks the node in one specific way, runs
the suite, and expects it to fail. A mutation the suite still passes is a
**survivor** - a defect the tests cannot see.

The mutations live in ``test/digital_twin/mutations.yml``, not in this file. They are
the specification of what the suite must detect, so they are reviewable data
rather than literals buried in a script.

**This tool never touches the working tree.** It copies the tracked files into
a temporary directory and mutates the copy, the same way ``test/unit`` plants
its violations. An earlier version edited in place and restored afterwards,
which was correct but made ``git status`` report phantom modifications for the
length of a run: a stop hook and a concurrent test run were both misled by it
before this changed.

Mutations run in parallel, one worker per CPU unless ``--jobs`` says otherwise.
Each worker owns its own copy of the tree and its own pytest temporary
directory, so no two suite runs can see each other's mutation or files, and the
report is printed in specification order whatever order the runs finish in. A
mutation is still applied, tested and restored inside one copy; parallelism
changes only how many copies there are.

Exit codes: 0 every mutation was caught, 1 at least one survived, 2 a mutation
no longer applies and the list needs updating.
"""

from __future__ import annotations

import argparse
import os
import queue
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Callable, Iterator
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
MUTATIONS = REPO_ROOT / "test" / "digital_twin" / "mutations.yml"


@dataclass(frozen=True)
class Mutation:
    """One deliberate break, and what it simulates."""

    id: str
    #: Relative to a tree root, so one mutation can be applied in any copy.
    path: Path
    find: str
    replace: str
    describe: str


@contextmanager
def tracked_copies(count: int) -> Iterator[list[Path]]:
    """Yield `count` temporary copies of the tracked tree, removed on the way out.

    Tracked files only, so a stray build artifact or a half-finished scratch
    file cannot change what the suite sees. The mutation run then has trees of
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
    names = [name for name in listing.stdout.split("\0") if name]
    with tempfile.TemporaryDirectory(prefix="fml-mutation-") as tmp:
        roots = []
        for index in range(count):
            root = Path(tmp) / f"worker-{index}" / "tree"
            for name in names:
                destination = root / name
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(REPO_ROOT / name, destination)
            roots.append(root)
        yield roots


def load_mutations() -> list[Mutation]:
    """Read the mutation specification. Paths stay relative to a tree root."""
    with MUTATIONS.open(encoding="utf-8") as handle:
        document = yaml.safe_load(handle)
    return [
        Mutation(
            id=entry["id"],
            path=Path(entry["file"]),
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
    """Run the test suite quietly in `root` and return pytest's exit code.

    pytest's default temporary directory is shared by every run as the same
    user, and each run prunes the older numbered entries in it, so concurrent
    runs could remove a directory another run is using. `--basetemp` gives each
    copy its own, beside the tree rather than inside it; pytest documents that
    it clears that directory at the start of every run, which is safe because a
    copy runs one suite at a time.
    """
    basetemp = root.parent / "pytest-tmp"
    # S603 flags the non-literal --basetemp argument. It is a path this tool
    # created under its own temporary directory, not untrusted input.
    result = subprocess.run(  # noqa: S603
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "--no-header",
            "-x",
            f"--basetemp={basetemp}",
        ],
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
    target = root / mutation.path
    original = target.read_text(encoding="utf-8")
    if mutation.find not in original:
        return "NOT-APPLIED"
    try:
        target.write_text(
            original.replace(mutation.find, mutation.replace, 1), encoding="utf-8"
        )
        code = run_suite(root)
    finally:
        target.write_text(original, encoding="utf-8")

    if code == PYTEST_TESTS_FAILED:
        return "killed"
    if code == PYTEST_ALL_PASSED:
        return "SURVIVED"
    # Any other code means pytest could not run the suite - a collection error,
    # an import failure, no tests found. That is not a test noticing a defect,
    # and scoring it as one would let a mutation that merely breaks a module
    # inflate the result. It is reported as broken so the mutation gets fixed.
    return "BROKE-SUITE"


def run_all(
    mutations: list[Mutation],
    roots: list[Path],
    test: Callable[[Mutation, Path], str],
) -> Iterator[str]:
    """Yield each mutation's verdict, in order, running one per root at a time.

    A root is checked out of a pool for the length of one `test` call and
    returned afterwards, so no two calls ever share a tree. The pool holds one
    root per worker thread; threads suffice because the work is a pytest
    subprocess, not Python.
    """
    pool: queue.Queue[Path] = queue.Queue()
    for root in roots:
        pool.put(root)

    def one(mutation: Mutation) -> str:
        root = pool.get()
        try:
            return test(mutation, root)
        finally:
            pool.put(root)

    with ThreadPoolExecutor(max_workers=len(roots)) as executor:
        # map() yields in input order, whatever order the runs finish in.
        yield from executor.map(one, mutations)


def main(argv: list[str]) -> int:
    """Run every mutation and report the survivors."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--list", action="store_true", help="list the mutations and exit"
    )
    parser.add_argument(
        "--only", default=None, help="comma-separated mutation ids to run"
    )
    parser.add_argument(
        "--jobs",
        type=int,
        default=os.cpu_count() or 1,
        help="mutations to run at once (default: the CPU count)",
    )
    args = parser.parse_args(argv)
    if args.jobs < 1:
        parser.error("--jobs must be at least 1")

    # Listing needs no copy: it reads the specification and nothing else.
    if args.list:
        for mutation in load_mutations():
            if not args.only or mutation.id in {
                m.strip() for m in args.only.split(",")
            }:
                print(f"{mutation.id}  {mutation.describe}")
        return 0

    mutations = load_mutations()
    if args.only:
        wanted = {m.strip() for m in args.only.split(",")}
        mutations = [m for m in mutations if m.id in wanted]

    with tracked_copies(max(1, min(args.jobs, len(mutations)))) as roots:
        if run_suite(roots[0]) != PYTEST_ALL_PASSED:
            print(
                "ERROR: the suite fails before any mutation is applied.",
                file=sys.stderr,
            )
            return 2

        survivors: list[Mutation] = []
        stale: list[Mutation] = []
        verdicts = run_all(mutations, roots, apply_and_test)
        for mutation, verdict in zip(mutations, verdicts, strict=True):
            print(f"  {mutation.id} {verdict:11s} {mutation.describe}", flush=True)
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
            print(f"  {mutation.id} in {mutation.path}", file=sys.stderr)
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
