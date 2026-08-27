# Acceptance

The procedure that qualifies a built node as a member of this block.

**Status: `TBD`. No acceptance procedure exists, because no block is
qualified.** See `TBR-HW-01`.

## What acceptance is for

The program promises that a **spare node replaces any node within the same
block**. Acceptance is what makes that promise true. A node that has not passed
acceptance is a node someone built, not a member of the block.

Acceptance is distinct from two things it is often confused with:

- **Build acceptance** (`../assembly/BUILD-ACCEPTANCE.md`) asks whether the
  *documentation* worked for a first-time builder. It tests the instructions.
- **Qualification stages** (`test/stages/`) ask whether the *design* meets the
  operational requirements. They test the design.

This procedure asks whether *this particular built node* is equivalent to the
others. It tests the unit.

## What the procedure must contain

- **Preconditions**: the image build the node is running, the region profile
  configured, the equipment the tester needs.
- **Steps**, each with an explicit pass criterion. Not "check the radios work";
  a stated command, a stated expected output.
- **Measurements**, with the instrument and the acceptable range. A range
  requires `TBR-HW-01` and the trades feeding it to have closed.
- **A record form**: what the tester writes down, including serial numbers, the
  date, and who performed it.
- **Failure handling**: what happens to a node that fails, and whether a retest
  after rework is a full retest.

## Minimum content, once a block exists

Derived from the promotion gate in `os/release/README.md`, which is the closest
thing the program has to an acceptance procedure today:

- Boots to a known state.
- **Enumerates every radio.** This is the check the compatibility-set rule in
  `FML-ADR-040` exists to protect.
- Forms a mesh with a known-good reference node.
- Serves the access point, and a client associates.
- Passes a traffic smoke test across each bearer.
- Retains time across a power cycle, and refuses validation with a dead clock
  backup cell, per `FML-ADR-042`.
- Demonstrates rollback to the known-good path, per `FML-ADR-041`.
- Records power draw at idle and at a representative load, against the range
  from `TBR-PWR-01`.

## Records

Completed acceptance records go in `test/results/`, not here. This directory
holds the procedure; the results are evidence of a run.
