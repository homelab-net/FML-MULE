---
id: FML-ADR-051
title: Node decision logic lives in an importable package outside the test tree
status: SELECTED PRINCIPLE
date: 2026-08-27
supersedes: none
superseded-by: none
trades: []
verification: TBD
---

# FML-ADR-051 Node decision logic lives in an importable package outside the test tree

## Context

The flat-sat needs the node to make real decisions, because a decision made by
a fake is a decision nobody has tested. An adversarial review of the flat-sat
found exactly that failure: time credibility was returned by `FakeClock`
directly, so the `FML-ADR-042` fail-closed tests asserted that a fixture agreed
with itself. No code decided anything, and no test could have failed.

Splitting the decision out fixed the test. It did not fix where the decision
lives. `timekeeping.py` was written as production code and parked under
`test/flatsat/` with a note saying it would move when a production package
existed, because none did, and inventing a package layout was a larger decision
than the fix in front of it.

Leaving it there has costs that compound:

- It is exempted from production lint strictness. `pyproject.toml` relaxes
  assertion and docstring rules for everything under `test/`, so decision code
  is held to test standards.
- It reads as scaffolding. A contributor looking for what the node does has no
  reason to open a directory named after the test harness.
- The note in the file becomes a promise nobody is obliged to keep, and the
  program has already had to correct one document that claimed more than was
  true.

Against that stands the program's own sequencing rule: build system before
application code, because features need something to install onto. That rule is
about **features**, and this is not one. It is code that already exists, is
already exercised end to end, and is already depended on by a passing suite. The
question is only whether it is honest about being production code.

The alternative genuinely on the table was to leave it and accept the note. It
was rejected because the same review that prompted this found two other stale
claims, and a note whose fulfilment depends on someone remembering is the same
category of defect.

## Decision

Node-resident Python that **makes a decision** shall live in the top-level
`mule/` package, and shall be held to the same lint, type and docstring
standards as any other production code.

Fakes, recorded fixtures, scenarios and flat-sat composition scaffolding shall
remain under `test/`.

The package shall not acquire a service daemon, a process entry point, or any
of the four placeholder components in `services/`, which remain blocked on
their trades.

Code shall be admitted to `mule/` only once it is exercised end to end by the
flat-sat. The package is a home for demonstrated logic, not a staging area for
intended logic.

## Status

`SELECTED PRINCIPLE`.

It decides where decision logic lives and what standard applies to it. It
deliberately leaves to a later implementation ADR: how the package is installed
onto an image, whether it is packaged as a Debian artifact or a Python
distribution, what the node's process entry point is, and how it is versioned
against the compatibility set in `FML-ADR-040`.

The name `mule` was chosen over `node` because `node_modules/` already exists in
this repository for documentation tooling, and two top-level paths differing by
a suffix is an avoidable reading hazard.

## Consequences

Decision code stops being exempt from production lint rules, which is the point
and also immediate work: the relaxations for `test/` no longer apply to it.

`tools/mutation-check.py` mutates the package directly, so the suite is required
to detect defects in it. Six of the twenty-five mutations already target the
credibility decision.

The flat-sat imports the package rather than containing it, which strengthens
rule one in `test/flatsat/README.md`: the flat-sat runs the real artifacts. It
now does so for the time decision as well as for configuration generation.

`os/` retains ownership of installation. Nothing installs `mule/` onto anything
yet, and the promotion gate in `os/release/README.md` does not know about it.
That gap is real and is left to the implementation ADR named above.

The decision creates a place where speculative code would be easy to put. The
admission rule in the Decision section exists because of that, and the honest
consequence is that it depends on reviewers enforcing it.

For the module actually moving, nothing about the open trade changes. The
credibility decision encodes the **procedure** in `FML-ADR-042` while leaving
every **value** to `TBR-TIME-01`. `TimePolicy` has no defaults: a caller
supplies the image build time, the forward horizon and the skew tolerance, and
the module refuses to invent any of them. Relocating it neither closes the trade
nor baselines a number.

## Accepted cost

A production package now exists before there is a node to run it on. That is
the shape of structure-ahead-of-content the program warns against, and someone
will reasonably argue this was premature.

The bound accepted in exchange is the admission rule: only code already
exercised end to end by the flat-sat may move in. Today that is one module. If
`mule/` accumulates modules that no scenario exercises, this decision has failed
and the argument was right.

The second cost is smaller and certain: the interface Protocols in
`test/flatsat/interfaces.py` do **not** move, so production and test now hold
related material in two places. They stay because they overlap the radio
abstraction that `docs/interfaces/README.md` records as blocked on
`TBR-LINUX-01`, `TBR-RF-01` and `TBR-RF-03`, and promoting them would be
defining a blocked interface by relocation.

## Fallback

The package is one module and an import path. Collapsing it back under `test/`
is a file move and an import rewrite, mechanical and reversible in an afternoon.

The signal to take the fallback is the failure mode named in Accepted cost:
modules arriving in `mule/` that no flat-sat scenario exercises. If that
happens, the package has become the staging area this decision forbids, and
reverting is cheaper than policing it.

## Superseded by

None.

## Verification dependency

`TBD`. No qualification stage covers repository structure, and none should.

What does check it: `tools/mutation-check.py` requires the test suite to detect
deliberate defects introduced into `mule/`, and `test/flatsat/test_integrity.py`
asserts the flat-sat loads real artifacts rather than copies. Those are
`SIMULATED` results about software, which is the correct tier for a decision
about where software lives.
