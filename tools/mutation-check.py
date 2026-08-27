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

**This tool edits files in place and restores them.** It restores on success,
on failure and on interrupt. If it is ever killed hard enough to skip that,
``git diff`` shows exactly one mutation to revert.

Exit codes: 0 every mutation was caught, 1 at least one survived, 2 a mutation
no longer applies and the list needs updating.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
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


def load_mutations() -> list[Mutation]:
    """Read the mutation specification."""
    with MUTATIONS.open(encoding="utf-8") as handle:
        document = yaml.safe_load(handle)
    return [
        Mutation(
            id=entry["id"],
            path=REPO_ROOT / entry["file"],
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


def run_suite() -> int:
    """Run the test suite quietly and return pytest's exit code."""
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "--no-header", "-x"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode


def apply_and_test(mutation: Mutation) -> str:
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
        code = run_suite()
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

    mutations = load_mutations()
    if args.only:
        wanted = {m.strip() for m in args.only.split(",")}
        mutations = [m for m in mutations if m.id in wanted]
    if args.list:
        for mutation in mutations:
            print(f"{mutation.id}  {mutation.describe}")
        return 0

    if run_suite() != PYTEST_ALL_PASSED:
        print("ERROR: the suite fails before any mutation is applied.", file=sys.stderr)
        return 2

    survivors: list[Mutation] = []
    stale: list[Mutation] = []
    for mutation in mutations:
        verdict = apply_and_test(mutation)
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
