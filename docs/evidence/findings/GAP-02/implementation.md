# GAP-02 implementation record

**Finding:** GAP-02, enforce the service catalog (P0).
**Controlling ADR:** FML-ADR-078. **Evidence tier:** SIMULATED.

## Defect corrected

The service catalog began empty and no validator enforced it, so a mission
package could enable any service name at all. The first implementation added
catalog names but treated every record as deployable, silently collapsed
duplicate names, had no alias model, and did not connect an enabled record to a
real deployment unit. An independent red-team duplicate therefore still passed
both validation and generation. This increment closes those remaining paths.

## Changes

- `services/catalog/catalog.yml` + `catalog.schema.json`: machine-readable
  contracts for `opentakserver` and `martin`, including enabled state, aliases,
  exact deployment unit, recovery, region dependency and governing ADR. Both
  contracts are disabled and carry a `TBD` unit because no loadable unit exists.
  The production valid mission therefore enables no service.
- `tools/validate-catalog.py`: validates the catalog against its schema and
  checks unique names and aliases, rejects disabled mission selections, requires
  every enabled record to name an existing `<name>.container`, and rejects a
  loadable production Quadlet without exactly one enabled catalog owner; wired
  into `tools/validate-docs.sh` (check 23).
- `tools/gen-config.py`: the runtime resolver validates the catalog schema and
  applies the same fail-closed uniqueness, enablement and deployment-unit gates
  before it canonicalizes aliases into generated configuration.
- `test/flatsat/`: the service scenarios use two explicitly synthetic stand-ins
  with their own test-only catalog and existence-marker units. This exercises
  the production resolver without representing OpenTAKServer or Martin as
  deployable.

## Contract (FML-ADR-078)

A catalog entry records a contract, not permission to deploy it. A mission may
select the contract only when `enabled` is true and its exact loadable unit
exists. Trade-blocked fields remain honest `TBD` values rather than invented
images, resource envelopes, or recovery behavior.

## Failing-first demonstration

The original uncatalogued-service test failed against the pre-GAP-02 code. For
this completion increment, the 47-test focused run against the earlier
implementation produced 11 failures: duplicate names, ambiguous aliases,
disabled selections, absent units, unowned units and malformed identifiers were
all still accepted. After the change, the focused GAP-02 and flat-sat run passes
251 tests. Mutations M103 through M107 independently defeat unknown-service,
disabled-service, missing-unit, duplicate-reference and operator-preflight
enforcement; all five are killed.

## Reproduce

`python -m pytest test/unit/test_gen_config.py test/unit/test_service_catalog.py
test/flatsat -q`; `python tools/validate-catalog.py`; `python
tools/mutation-check.py --only M103,M104,M105,M106,M107`; and `sh tools/lint.sh`.
The evidence is `SIMULATED` and establishes no physical behavior.
