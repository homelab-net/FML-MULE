---
id: FML-ADR-074
title: A node that cannot serve users is reported FAULT and not operational
status: SELECTED
date: 2026-09-11
supersedes: none
superseded-by: none
trades: []
verification: SIMULATED
---

# FML-ADR-074 A node that cannot serve users is reported FAULT and not operational

## Context

The operator status view (CONOPS section 67, `mule/status.py`, under `FML-ADR-046`
and `FML-ADR-052`) answers "Is the node operational?" and reduces the node to one
`OperatorState` word. Two related things were wrong.

`operational` was set to `observed.booted` alone, while `_state()` returns `FAULT`
for a booted node with a missing required bearer. So a booted node with no access
point reported `operational=True` **and** `state=FAULT` at once, contradicting the
rule `_state()` already states: "a node that cannot serve users is `FAULT`,
whatever else is true".

Separately, `_fault()`/`_state()` keyed only off `missing_required` -- required
bearer hardware *absent*. They ignored `required_not_serving` -- required hardware
*present but not linked*. `mule/bearers.py` already distinguishes the two, and
`mule/admission.py` already fails closed when a required bearer is not serving
(CONOPS section 82 puts "connect approved EUD" before everything after it). But
`status.py` reported such a node `GREEN`/`operational=True`: the status view called
a node healthy while it admitted no one. `Observations` already carries
`associated`, so the data to tell the difference was present and unused.

The alternative -- leaving `operational` as `booted` and documenting the
divergence -- was rejected: a status view that reports healthy for a node that
cannot serve its one user-facing function is the class of false-confidence display
this program has been burned by before.

## Decision

A node that cannot serve users **shall** be reported `FAULT`, and `operational`
**shall** be false whenever the state is `FAULT`.

Concretely: a required bearer that is present but not serving
(`bearers.required_not_serving(observed.associated)` non-empty) is a fault on the
same footing as an absent one, so `_state()` returns `FAULT`; and
`operational = observed.booted and state != "FAULT"`.

This restores `mule/status.py`'s own rule 1. It aligns status with `admission` on
the required-bearer axis only; the two planes deliberately still differ elsewhere
(a time-degraded node fails admission yet reports `DEGRADED`/operational), and this
ADR does not change that.

## Status

SELECTED.

## Consequences

- The status view stops reporting a non-serving node as healthy, which is the
  point. A node whose access point is fitted but has not come up now reads
  `FAULT`, matching what the admission path already does to arriving devices.
- `status.py` gains a use of `required_not_serving` and of `observed.associated`;
  the two planes now share one reading of "required bearer serving".
- A contributor without hardware can exercise the whole change on the flat-sat:
  the enumerated/associated distinction is fake-driven.
- No effect on the promotion pipeline or the threat model.
- What becomes harder: the truth table now has a new `FAULT` trigger, so any future
  axis that wants to report through it must decide where it sits in the precedence
  `_state()` documents.

## Accepted cost

`FAULT` does not distinguish "access point absent" from "access point present but
not serving"; both collapse to one operator word (the `fault` string carries the
difference, the state does not). Someone will argue a present-but-not-serving AP
deserves its own colour so an operator knows a reboot may fix it rather than a
missing radio. That distinction is deliberately left to the `fault` reason string
until an operator study says the state word needs to carry it.

## Fallback

Reversible. If reporting present-but-not-serving as `FAULT` proves too blunt in the
field, a later ADR can move it to `DEGRADED` or a dedicated state; the change is a
single branch in `_state()` and its tests. The signal to do so would be operators
reporting that a transient association gap during bring-up shows as `FAULT` often
enough to be noise.

## Superseded by

None.

## Verification dependency

The flat-sat scenario tests in `test/flatsat/`: a booted node with `wifi_ap`
enumerated but not associated asserts `state=="FAULT"` and `operational is False`,
and matches `admission`'s refusal for the same node. SIMULATED; nothing here is
claimed against hardware.
