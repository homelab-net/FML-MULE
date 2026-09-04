# The mission schema validates a deployment's addressing configuration

**Trade:** `TBR-NET-01`.
**Date:** 2026-09-04.
**Taken by:** Cameron Zobrist, with Claude Code, on the lab development machine.
**Status of this artifact:** `SIMULATED`. A schema and its validator on an
ordinary machine; no radio, no node.

## What this answers

`TBR-NET-01`'s closure gate has three items. Two were already supplied: the
prefix decision with its collision analysis (`FML-ADR-063`,
`2026-08-31-external-network-collision-analysis.md`,
`2026-08-30-collision-exercise.md`) and the demonstration that two independently
configured deployments do not collide (`2026-08-30-distinct-prefix-exercise.md`,
`2026-08-30-mesh-id-separates-deployments.md`).

The third -- **the mission package schema validates a deployment's addressing
configuration** -- was not met. `FML-ADR-063` itself says so: it requires
`network.address_prefix` "tightened from a bare `string` whose description says
everything is open. That is a schema change this ADR requires and does not itself
make." Until 2026-09-04 the field was `"type": "string"` with a `TBD` description,
so any string validated and the schema checked nothing about addressing.

## What changed

`mission/schema/mission-package.schema.json` now constrains
`network.address_prefix` to a well-formed IPv4 CIDR (the per-deployment,
generated prefix `FML-ADR-063` selects) with a `pattern`, and its description
records the `FML-ADR-063` decision -- per-deployment, generated not derived,
overlap reported -- rather than `TBD`. `mission/examples/valid-full.json` now
carries an illustrative IPv4 prefix (`10.83.0.0/16`, an example value, not the
retired program-wide constant), and a new counter-example
`mission/examples/invalid-bad-address-prefix.json` carries a non-IPv4 prefix that
must not validate.

## The demonstration

`tools/validate-mission.py` checks every example against the schema and asserts
the expectation encoded in each filename: `valid-*` must pass, `invalid-*` must
fail. `test/unit/test_mission_schema.py` runs the same assertion in CI.

```text
OK   invalid-bad-address-prefix.json (correctly rejected)
OK   invalid-bad-profile.json (correctly rejected)
OK   invalid-missing-required.json (correctly rejected)
OK   invalid-real-flag.json (correctly rejected)
OK   invalid-unknown-field.json (correctly rejected)
OK   valid-full.json (valid)
OK   valid-minimal.json (valid)
All 7 package(s) behaved as expected.
```

And it genuinely fires. With the `pattern` removed, the counter-example
validates and the harness reports the regression rather than passing quietly:

```text
FAIL invalid-bad-address-prefix.json: expected to be REJECTED, but validated.
     A counter-example that stops being caught is a regression.
```

So the schema now validates an addressing configuration: a per-deployment IPv4
prefix is accepted and a malformed one is rejected, checked in CI.

## What this does not do

It validates the **shape** of the prefix, not its **suitability**: it does not
and cannot check that a deployment's generated prefix avoids a particular venue's
uplink range, because `FML-ADR-063` establishes that overlap cannot be solved
inside IPv4 and is handled by detection-and-report at run time, not by the
package schema. The overlap-reporting behaviour is a node runtime concern
(`FML-ADR-063`), separate from this schema check.

## Bearing on closure

This supplies closure-gate item (c). With all three items now present, what
remains for `TBR-NET-01` is the named owner's acceptance (SAD section 30.2), and
the ordering the dependency implies: `TBR-NET-03`'s acceptance follows
`TBR-NET-01`'s closure, not the reverse (`FML-ADR-063` is unconditional and was
taken accounting for `TBR-NET-03`).
