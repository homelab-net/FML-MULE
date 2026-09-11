---
id: FML-ADR-076
title: The operator WAN answer is the undetermined-capable mode value, not a boolean
status: SELECTED
date: 2026-09-11
supersedes: none
superseded-by: none
trades: []
verification: SIMULATED
---

# FML-ADR-076 The operator WAN answer is the undetermined-capable mode value, not a boolean

## Context

CONOPS section 67 asks "Is WAN available?". `mule/status.py` answered it with
`wan_available: bool`, fed from a separate `Observations.wan_available: bool`. The
flat-sat adapter built that field with `bool(self._wan)`, so a node that genuinely
*cannot tell* whether a WAN gateway is reachable reported `False` -- indistinguishable
from a node that has confirmed there is no WAN.

This is the exact trap the rest of the node already avoids. `mule/modes.py` carries
the same fact as `ModeAssessment.wan: WanReachability | None` ("NO-WAN" /
"WAN-ENHANCED" / `None` for undetermined) and records *why* it is undetermined in its
`undetermined` set. `Observations` already carries that `ModeAssessment` (the status
module's docstring states EMCON and the capability ladder are read from modes rather
than decided again, precisely so two deciders cannot disagree). The WAN answer was the
one axis that ignored the mode value and re-collapsed `self._wan` on its own.

Leaving it a `bool` was rejected: `AGENTS.md` requires a reading a platform may be
unable to provide to be `T | None`, and a status view asserting "no WAN" when it means
"cannot tell" is a false-certainty claim in the field an operator most needs to trust
when deciding whether they are cut off.

## Decision

The operator WAN answer **shall** be the mode assessment's WAN value,
`observed.modes.wan` (`WanReachability | None`), reported unchanged: `None` means the
node cannot tell and **shall not** be presented as `NO-WAN`. The redundant
`Observations.wan_available: bool` **shall** be removed so there is one source for the
fact.

## Status

SELECTED.

## Consequences

- The status view distinguishes "no WAN" from "cannot determine WAN"; an isolated
  node and a node with broken WAN sensing no longer read the same.
- `Observations` loses a field; the status WAN answer is now literally the mode value,
  so the two cannot drift.
- `NodeStatus.wan_available` changes type from `bool` to `WanReachability | None`.
  This changes a CONOPS section 67 output field's contract. No serializer or operator
  display consumes `NodeStatus` today, so the reachable blast radius is the flat-sat
  fixtures and one scenario assertion.
- A contributor without hardware exercises it on the flat-sat by driving the WAN fake
  to its unknown state.

## Accepted cost

The field name `wan_available` now holds a reachability literal rather than a boolean,
so "available" reads slightly oddly against a `"NO-WAN"` value. Renaming the field
was declined to keep the CONOPS section 67 question wording ("Is WAN available?")
recognisable in the code; someone may later argue the field should be renamed to
`wan_reachability`. That rename is deferred, not foreclosed.

## Fallback

Reversible. The change is a type widening plus a re-source; reverting to a boolean is
a single field and its fixtures, at the cost of reintroducing the collapse this ADR
removes.

## Superseded by

None.

## Verification dependency

The flat-sat scenario tests in `test/flatsat/`: a node whose WAN reachability is
unknown asserts the operator WAN answer is `None`, not `"NO-WAN"`. SIMULATED.
