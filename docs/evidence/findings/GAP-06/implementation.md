# GAP-06 implementation record

**Finding:** GAP-06, define consistent operator-status semantics (P0).
**Controlling ADRs:** FML-ADR-074, FML-ADR-076. **Evidence tier:** SIMULATED.

## Defects corrected

1. `mule/status.py` set `operational=observed.booted`, so a booted node in
   `state=FAULT` reported `operational=True` at the same time -- against the
   `_state` docstring rule "a node that cannot serve users is FAULT, whatever
   else is true".
2. `_fault`/`_state` keyed only off `missing_required` (hardware absent) and
   ignored `required_not_serving` (hardware present but not linked), which
   `admission.py` already fails closed on. A booted node with `wifi_ap`
   enumerated but not associated reported GREEN/operational while admitting
   nobody.
3. `NodeStatus.wan_available` was a `bool` fed a `bool(self._wan)` collapse, so
   an unknown WAN read as `NO-WAN` -- although `mule/modes.py` already carries
   the honest `wan: WanReachability | None`.

## Changes

- `mule/status.py`: `operational = observed.booted and state != "FAULT"`;
  `required_not_serving(observed.associated)` folded into `_fault`
  (`RADIO_NOT_SERVING`) and `_state` (FAULT); `wan_available` retyped to
  `WanReachability | None` and sourced from `observed.modes.wan`; redundant
  `Observations.wan_available` removed.
- `test/flatsat/node.py`: dropped the `wan_available=bool(self._wan)` collapse.
- `test/flatsat/scenarios/test_v001_flow.py`: question 11 now asserts the honest
  undetermined value (`None`) rather than silently passing on it.

## Failing-first demonstration

Reverting the two logic lines (`operational` and the `_state` not-serving
branch) makes the new tests fail:

- `test_a_node_with_no_access_point_is_faulted_not_green` fails its new
  `operational is False` assertion.
- `test_a_required_bearer_present_but_not_serving_is_faulted_not_green` reports
  `DEGRADED` instead of `FAULT`.
- `test_wan_answer_reports_unknown_distinctly_from_no_wan` fails against the old
  `bool(self._wan)` collapse for all three of unknown/known-up/known-down.

## Reproduce

`python -m pytest test/flatsat test/unit` (308 tests). `mule/` coverage held at
100%. SIMULATED against the flat-sat fakes; nothing here is claimed on hardware.
