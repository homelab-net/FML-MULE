# Mission package schema

The schema for a mission configuration package.

**Status: draft skeleton.** Several fields depend on trades that have not
closed and are marked `TBD` in the schema rather than guessed.

## Files

| File | Contents |
| --- | --- |
| `mission-package.schema.json` | JSON Schema for a mission configuration package. |

## Validation

Validated in CI against every example in `mission/examples/`, both the valid
ones and the deliberately invalid ones.

**Invalid examples matter as much as valid ones.** A schema that accepts
everything passes every valid example and catches nothing. Each invalid example
names, in its own header, exactly which rule it is intended to violate, so that
a schema change which stops catching it is visible as a regression rather than
as a test that quietly started passing.

## What the schema cannot check

- **Whether a value is lawful in the deployment's region.** A channel outside
  the region's permitted set is a regulatory problem, and checking it requires
  the region profile, not the schema. That validator does not exist yet. See
  `regions/README.md`.
- **Whether identities are real.** The publication rule is enforced by secret
  scanning and by reviewers, not by a schema. See `SECURITY.md`.
- **Whether two deployments would collide.** That needs both packages.
  `TBR-NET-01`.

## Versioning

The package format is versioned, and a node states which versions it accepts. A
node that has rolled back to the known-good path (`FML-ADR-041`) may be running
an older image that does not understand the current package format. `TBR-REC-01`
records that keeping the known-good path current is the part usually skipped;
this is one of the reasons it matters.

## Open questions

| Field area | Trade |
| --- | --- |
| Addressing: family, prefix source, host allocation | `TBR-NET-01` |
| Durable mission state a package must declare | `TBR-TAK-01` |
| How trust material is referenced, never included | `TBR-SEC-01` |
| What an EMCON profile can enforce | `TBR-RF-02` |
