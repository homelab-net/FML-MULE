# Unit tests

Tests that run in CI, on an ordinary machine, with no hardware.

| Language | Framework | Files |
| --- | --- | --- |
| Shell | `bats` | `*.bats` |
| Python | `pytest` | `test_*.py` |

```sh
bats test/unit
pytest
```

## What is tested here

The repository's own tooling and rules, since there is no application code yet:

- `test_mission_schema.py` exercises the mission package validator against
  every example, valid and deliberately invalid, and asserts that each behaves
  as its filename says it should.
- `validate_docs.bats` exercises `tools/validate-docs.sh`, including that it
  **detects** a planted violation. A validator that has never been shown to
  fail has not been tested.

## Testing a checker

A test that only confirms a checker passes on a clean tree tells you nothing:
a script that exits zero unconditionally would pass it. Every check in
`tools/` gets a test that plants a violation in a temporary copy and asserts
the check catches it.

This matters more than usual here, because these checks are the only thing
enforcing several rules that are otherwise a matter of discipline: identifier
permanence, evidence-backed closure, the fork ledger, and digest-pinned images.

## When application code arrives

The hardware abstraction rule applies. Service-plane and status code runs and
is tested against **fakes**, on a laptop, with no radios. A test that requires
hardware belongs to a qualification stage, not here. See `test/README.md`.
