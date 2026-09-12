# GAP-02 implementation record

**Finding:** GAP-02, enforce the service catalog (P0).
**Controlling ADR:** FML-ADR-078. **Evidence tier:** SIMULATED.

## Defect corrected

The service catalog was empty and no validator enforced it, so a mission package
could enable any service name at all. The mission JSON schema states every
enabled service must have a catalog entry and that a separate validator would
check it; there was none.

## Changes

- `services/catalog/catalog.yml` + `catalog.schema.json`: a machine-readable
  catalog with entries for `opentakserver` and `martin`. Trade-blocked fields
  (image, resource envelope) carry `TBD` naming the trade; an image, if given,
  must be by immutable digest.
- `tools/validate-catalog.py`: validates the catalog against its schema and
  checks that every `valid-*` mission example enables only catalogued services;
  wired into `tools/validate-docs.sh` (check 23).
- `tools/gen-config.py`: `resolve()` refuses a mission that enables a service
  with no catalog entry (`_catalog_names()`), so an uncatalogued service is
  rejected at generation, not silently configured.
- `mission/examples/valid-full.json` now enables the catalogued services
  (`opentakserver`, `martin`); the dependent flat-sat and unit tests were updated
  to those names.

## Contract (FML-ADR-078)

A catalog entry is a contract -- this node may run this service -- not a claim
that its digest or resource envelope is settled. TBD-blocked fields are honest
placeholders naming the trade (TBR-COMP-01, TBR-TAK-01, TBR-MAP-01).

## Failing-first demonstration

`test_a_mission_enabling_an_uncatalogued_service_is_refused` writes a package
enabling `not-a-catalogued-service` and asserts a `ConfigError` naming it.
Against the old code generation proceeded with no error. Mutation M103 (which
defeats the catalog check) is killed.

## Reproduce

`python -m pytest test/flatsat test/unit -q` (312 tests); `python
tools/validate-catalog.py`; `bash tools/validate-docs.sh`. SIMULATED.
