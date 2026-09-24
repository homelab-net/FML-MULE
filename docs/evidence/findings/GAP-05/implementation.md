# GAP-05 implementation record

**Finding:** GAP-05, handle unknown radio enumeration safely (P0).
**Controlling ADR:** FML-ADR-077. **Evidence tier:** SIMULATED.

## Defect corrected

The radio reader returns `list[Bearer] | None`, where `None` means the platform
could not enumerate at all (distinct from an empty list). `FlatSatNode._enumerated()`
evaluated `list(self._radio.enumerated())`, raising `TypeError` on `None`. Even
without the crash, collapsing `None` to an empty list would report every required
bearer as `RADIO_ABSENT` -- a confident "absent" where the truth is "cannot tell".

## Changes

- `mule/status.py`: `Observations.enumerated` is `list[Bearer] | None`; `_fault`
  returns a distinct `RADIO_ENUMERATION_FAILED` (before `RADIO_ABSENT`); `_state`
  returns `FAULT` when `enumerated is None`; the missing/not-serving computations
  are skipped rather than run against a value that does not exist; the LoRa and
  network-degraded axes guard `None`.
- `test/flatsat/node.py`: `_enumerated` propagates `None` instead of crashing;
  `_associated` and the boot report handle it; `BootResult.radios_enumerated`
  is `list[str] | None`.
- `test/flatsat/fakes.py`: `FakeRadio(enumerable=False)` models a platform that
  cannot enumerate.

## Semantics (FML-ADR-077)

`None` (cannot tell), `[]` (enumerated, none present) and a populated list are
three distinct states and are never collapsed. Unknown fails closed to FAULT.

## Failing-first demonstration

`test_a_node_that_cannot_enumerate_its_radios_fails_closed` asserts FAULT,
`operational is False`, and a `RADIO_ENUMERATION_FAILED` fault that is not
`RADIO_ABSENT`. Against the old code the node raised `TypeError` at `list(None)`.
Mutations M23/M97/M98/M102 on the state logic are all killed.

## Reproduce

`python -m pytest test/flatsat test/unit -q`; `mule/` coverage 100%. SIMULATED.
