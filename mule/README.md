# `mule/`

Node-resident decision logic. `FML-ADR-051`.

## What belongs here

Code that **makes a decision the node acts on**, and that the flat-sat already
exercises end to end. Held to production lint, docstring and typing standards,
with no test-tree relaxations.

## What does not

- Fakes, recorded fixtures, scenarios, flat-sat composition. Those are `test/`.
- Image build and configuration pipeline. That is `os/`.
- Repository tooling. That is `tools/`.
- The four placeholder components in `services/`, which stay blocked on their
  trades and must not be implemented anywhere.
- Anything no scenario exercises. The package is a home for demonstrated logic,
  not a staging area for intended logic.

## Contents

| Module | Decision it makes |
| --- | --- |
| `timekeeping.py` | Whether retained local time is trustworthy enough for trust validation. `FML-ADR-042`. Encodes the procedure; every bound is supplied by the caller and belongs to `TBR-TIME-01`. |

## Nothing installs this yet

`os/` owns installation, and the promotion gate in `os/release/README.md` does
not know this package exists. How it reaches an image, how it is packaged, and
what the node's process entry point is are left to a later implementation ADR.
`FML-ADR-051` records that gap rather than hiding it.

## Why it exists at all

An adversarial review of the flat-sat found that time credibility was returned
by a fake, so the `FML-ADR-042` fail-closed tests asserted that a fixture agreed
with itself. Splitting the decision out of the fake fixed the test. Putting the
decision somewhere honest is what this package is for: a decision parked under
`test/` is held to test standards and reads as scaffolding.
