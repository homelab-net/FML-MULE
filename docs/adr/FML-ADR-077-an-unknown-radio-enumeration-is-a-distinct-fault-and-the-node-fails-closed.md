---
id: FML-ADR-077
title: An unknown radio enumeration is a distinct fault and the node fails closed
status: SELECTED
date: 2026-09-11
supersedes: none
superseded-by: none
trades: []
verification: SIMULATED
---

# FML-ADR-077 An unknown radio enumeration is a distinct fault and the node fails closed

## Context

The radio-enumeration reader returns `list[Bearer] | None`: a list of the
bearers found, an empty list where none is present, or `None` where the platform
could not enumerate at all (for example the enumeration command failed to run).
The reader's own contract already treats `None` as distinct from an empty list --
"cannot tell what is present" is not "nothing is present".

The status plane did not honour that distinction. `FlatSatNode._enumerated()`
evaluated `list(self._radio.enumerated())`, which raises `TypeError` on `None`, so
an unknown enumeration crashed the node rather than being handled. Even without the
crash, collapsing `None` to an empty list would report every required bearer as
`RADIO_ABSENT` -- a confident "the access point is missing" when the truth is "the
node cannot tell what radios it has". That is the same false-certainty trap this
program has hit before, on WAN reachability (FML-ADR-076) and thermal envelopes.

Doing nothing was not an option: the reader can legitimately return `None`, and a
status view that either crashes or fabricates "absent" on that input is wrong in the
direction an operator most needs to trust.

## Decision

An unknown radio enumeration (`enumerated is None`) **shall** be reported as a
distinct fault, `RADIO_ENUMERATION_FAILED`, and the node **shall** fail closed to
`FAULT` -- it cannot confirm that a required bearer is present, so it cannot claim
it can serve users. `None`, an empty list, and a populated list are three distinct
states and **shall not** be collapsed into one another: unknown is not absent, and
absent is not present.

Concretely: `Observations.enumerated` is `list[Bearer] | None`; `_fault` returns
`RADIO_ENUMERATION_FAILED` (checked before `RADIO_ABSENT`); `_state` returns `FAULT`
when `enumerated is None`; and the missing/not-serving computations are skipped
rather than run against a value that does not exist.

## Status

SELECTED.

## Consequences

- A platform that cannot read its radios reports a truthful, distinct fault instead
  of crashing or claiming its access point is absent.
- `Observations.enumerated` becoming optional ripples to its consumers, each of which
  now guards the `None` case (`missing_required`/`required_not_serving` are skipped,
  LoRa reads unavailable, the network-degraded axis reads no inter-node bearer). These
  secondary answers are moot under the resulting `FAULT` but must not crash.
- A contributor without hardware can exercise the whole path on the flat-sat by
  constructing a radio that cannot enumerate.
- No effect on the promotion pipeline or the threat model.

## Accepted cost

`RADIO_ENUMERATION_FAILED` does not distinguish *why* enumeration failed (command
absent, permission denied, timeout); it collapses those into one operator fault. The
reader does not surface the reason today, and inventing a taxonomy of enumeration
failures ahead of a real reader that can report them would be structure ahead of
content. Someone may later argue the operator needs the specific cause; that waits
for a reader that can supply it.

## Fallback

Reversible. The change is a type widening plus guards; reverting to a non-optional
`enumerated` is mechanical, at the cost of reintroducing the crash and the
unknown-as-absent collapse this ADR removes.

## Superseded by

None.

## Verification dependency

The flat-sat scenario tests in `test/flatsat/`: a node whose radio cannot enumerate
asserts `state == "FAULT"`, `operational is False`, and a `RADIO_ENUMERATION_FAILED`
fault that is not `RADIO_ABSENT`. SIMULATED; nothing here is claimed on hardware.
