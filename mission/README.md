# Mission configuration

A **mission configuration package** is the per-deployment configuration a node
is given: what network it forms, what identities it accepts, what services it
runs, and under what emission profile.

It is the boundary between what the repository defines, which is the same for
everyone, and what a deployment defines, which is not.

## Why this exists as a package

Two independently built deployments meeting at an incident must not collide.
Values that differ between deployments cannot live in the repository:

- Network and mesh identifiers.
- Address prefix, once `TBR-NET-01` decides the scheme.
- Local domain and service names.
- Mission trust material references, never the material itself.
- Which services run, and the mission profile in force.

Putting any of these in a repository file makes every deployment built from it
identical, and collision certain. The more successful this program is, the more
likely two deployments meet.

## Directories

| Directory | Contents |
| --- | --- |
| `schema/` | The package schema. Validated in CI, with valid and deliberately invalid examples. |
| `examples/` | Example packages. **Obviously fake identities only.** |
| `profiles/` | Mission profile definitions, including exercise and EMCON. |

`mission/local/` is **git-ignored** and is where a real package goes on a
builder's machine. It is never committed.

## The publication rule

**No real mission configuration, deployment location, member identity,
callsign, credential, or operational capture is ever committed to this
repository.**

A public repository maintained by the organisation that operates the system is
itself an exposure surface. An adversary reading this repository learns the
design, which is intended. They must not also learn who participates, where
they operate, when they exercise, or what identifiers their equipment carries.

Every file in `examples/` carries a header comment saying its identities are
fake. See `SECURITY.md`.

## Validation

`mule/mission.py` is the canonical runtime loader for the declared Draft
2020-12 schema. Both `tools/gen-config.py` and the flat-sat path use it, while
`tools/validate-mission.py` adds only the publication rules for files committed
to this repository. CI exercises valid and deliberately invalid examples; a
schema that accepts everything passes every valid example and is worthless.

`tools/gen-config.py` separately validates resolved radio values against the
selected region profile. No real region profile is resolvable yet, and the tool
does not render the configuration templates.

## State

The schema is a **draft skeleton**. Fields that depend on open trades are
marked `TBD` in the schema itself rather than being guessed:

| Unknown | Trade |
| --- | --- |
| Address family, prefix source, host allocation | `TBR-NET-01` |
| What mission state is durable, and what a package must declare about it | `TBR-TAK-01` |
| How trust material is referenced and supplied | `TBR-SEC-01` |
| What an EMCON profile can actually enforce | `TBR-RF-02` |
