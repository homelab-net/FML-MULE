# GAP-03 implementation record

**Finding:** GAP-03, preserve and validate `address_prefix` (P0).
**Governing record:** FML-ADR-063. **Evidence tier:** SIMULATED.

## Defect corrected

`tools/gen-config.py` built the resolved `network` block with `mesh_id`,
`local_domain` and `ap_ssid`, but not `address_prefix`. A mission package's valid
per-deployment IPv4 prefix therefore never reached the generated configuration.

## Change

- `tools/gen-config.py`: the resolved `network` block now carries
  `address_prefix` from the mission package. The mission schema validates its
  CIDR form on load (`load_mission`), so a present value is well-formed; a
  package that omits it yields `None`, the honest absence.

## Failing-first demonstration

`test_the_mission_package_supplies_the_address_prefix` asserts the resolved value
equals the package's own prefix. Against the old code the generated `network`
block has no `address_prefix` key, so the assertion raises `KeyError`.

## Reproduce

`python -m pytest test/unit/test_gen_config.py -q`. SIMULATED.
