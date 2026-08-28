---
id: FML-ADR-052
title: The boundary between node decision functions and the blocked placeholder services
status: SELECTED PRINCIPLE
date: 2026-08-28
supersedes: none
superseded-by: none
trades: [TBR-TAK-01]
verification: TBD
---

# FML-ADR-052 The boundary between node decision functions and the blocked placeholder services

## Context

Four components in `services/` are approved and deliberately unbuilt:
`status-aggregator/`, `mission-trust/`, `service-controller/` and `gateways/`.
Each holds a README naming the trade that must close first. `FML-ADR-051`
established that node decision logic lives in `mule/`, and stated that the
package shall not acquire any of those four components.

That was written as a rule about **directories**. It does not survive contact
with a rule about **subject matter**, and the gap was found the way these
things usually are: after the fact.

`mule/status.py` answers the thirteen CONOPS section 67 operator questions. It
uses the six operator states and the six authority reason codes from SAD
section 22. SAD section 22 is `FML-ADR-046`. `FML-ADR-046` is the status
aggregator, and `services/status-aggregator/README.md` says of itself:

> Approval is not permission to start. The trades that define its data model
> have not closed.

So a module in `mule/` implements behaviour that a blocked README describes,
and no rule in the repository says whether that was allowed. It merged. Nobody
noticed, including the author. The next module to be written, mode
determination for the degradation ladder, extends into the same territory,
which is what forced the question.

The genuine alternatives were three.

**Stop, and write no more node status logic until `TBR-TAK-01` closes.**
Rejected. It would also require reverting `mule/status.py`, and the reason the
aggregator is blocked does not apply to it: see the decision below. Blocking
work that the blocking rationale does not cover is how a program stops moving
for reasons nobody can restate.

**Treat the directory rule as sufficient and continue.** Rejected. It is the
rule that just failed, and "it is in a different directory" is precisely the
kind of distinction that reads as principled while checking nothing. This
repository has shipped three rules of that shape already.

**State the test the aggregator README is actually applying**, and hold new
code to it. Selected.

The README argues its own block clearly, and the argument is narrower than the
component:

> It is not shallow. It **defines the node's observable data model**, and every
> other part of the system ends up conforming to whatever it decided. An
> aggregator written before `TBR-TAK-01` closes will have invented a state
> taxonomy, and that taxonomy will be the one the program uses, because it
> works and rewriting it is expensive.

The hazard named is **invention of a taxonomy**, not reasoning about state.

## Decision

Code in `mule/` **shall** satisfy all four of the following before it may
reason about subject matter a blocked `services/` component describes. Failing
any one of them, it belongs to the blocked component and **shall not** be
written.

1. **It is a pure function of values passed to it.** It collects nothing,
   listens on nothing, serves nothing, and holds no state between calls. The
   blocked components are collectors and servers; a function that is handed its
   inputs is not one.
2. **It invents no vocabulary.** Every state name, reason code and category it
   produces is transcribed from a controlling document with the section cited,
   or is a value the caller supplied. Where no controlling document names a
   value, the value is not created here.
3. **It returns `None`, with the trade named in a comment, for anything the
   blocking trade would decide.** A function that answers the blocked question
   has answered it, whatever its file path.
4. **It defines no interface to hardware or to a peer** that a blocked trade
   governs. Narrow reading Protocols whose shape depends on an open trade stay
   in `test/`, per the location note in `test/flatsat/interfaces.py`.

A blocked component's README **shall** name, under a heading of its own, any
`mule/` module that reasons about its subject matter under this ADR, so that a
reader arriving at the blocked directory learns what does exist. `[CI]`

## Status

`SELECTED PRINCIPLE`.

It decides the property: what separates a decision function from a blocked
service is behaviour, not location, and the separation is testable against four
conditions.

It deliberately leaves to a later implementation ADR: how the status aggregator,
once `TBR-TAK-01` and `TBR-HA-01` close, consumes these functions; whether it
imports them, wraps them, or supersedes them; and what its process, transport
and schema are. Nothing here approves starting that work.

## Consequences

`mule/status.py` is in scope and stays, because it meets all four conditions.
It transcribes SAD section 22 rather than inventing it, and it returns `None`
for `shared_data_authoritative` and `data_stale`, which are exactly the two
answers `TBR-TAK-01` governs. The blocked question is the one it declines to
answer.

Mode determination for the CONOPS section 50 modes may proceed on the same
terms, and is constrained by them: it takes link and neighbour state as plain
arguments rather than defining the radio reading interface that
`TBR-LINUX-01`, `TBR-RF-01` and `TBR-RF-03` govern, and its thresholds are
caller-supplied policy with no defaults, as `TimePolicy`, `PowerModel` and
`ThermalLimits` already are.

What becomes harder: condition 1 forbids the obvious convenience. A function
that could read a value itself has to be handed it, and something outside
`mule/` has to do the reading. That cost is already being paid deliberately, and
it is the property that lets every one of these modules run on a laptop with no
radios present.

Condition 2 makes an undocumented state a stop rather than a small invention,
and CONOPS does not define entry or exit criteria for the section 50 modes, nor
say whether they are exclusive. That is now a documented gap requiring a trade
or a CONOPS change, rather than a set of thresholds somebody chose while
writing the module.

What it forecloses: `mule/` cannot grow the collection layer these functions
need. Something must eventually own that, and this ADR says only that it is not
`mule/` and not yet.

## Accepted cost

The four conditions are checkable by a reviewer, and condition 4 is partly
checkable by machine, but conditions 2 and 3 rest on someone knowing which
controlling document names a value and which trade governs an answer. A
contributor who does not know the SAD can satisfy all four conditions in good
faith and still write the aggregator's data model.

The program accepts that, because the alternative on offer was a directory rule,
which checked less and had already failed. The residual risk is recorded here
rather than argued away: this ADR narrows the failure, it does not close it.

The second cost is real and unbudgeted. Splitting reasoning from collection
means that when the aggregator is finally built, its author inherits a set of
functions whose signatures were fixed by whoever needed them first, and may find
the decomposition wrong. `TBR-COMP-01` will say what resource envelope the
component may occupy; nothing yet says what shape it wants its inputs in.

## Fallback

If `TBR-TAK-01` closes and the state taxonomy it produces contradicts SAD
section 22, the affected `mule/` modules are rewritten and this ADR is
superseded by the aggregator's implementation ADR. The cost is bounded by the
size of `mule/`, the functions are pure and fully exercised, and no persisted
data or wire format depends on them, which is the property that makes the
rewrite affordable.

The signal to take it: any `mule/` module needing a state name that no
controlling document supplies. That is condition 2 firing, and it means the
taxonomy question has arrived early.

## Superseded by

None.

## Verification dependency

`TBD`. Conditions 1 and 2 are `[review]`. Condition 3 is `[review]`. Condition 4
is partly enforced today by the production-imports-test check in
`tools/validate-docs.sh`, which prevents `mule/` importing the Protocols that
stayed in `test/`.

The cross-reference requirement in the decision is `[CI]` as of this change:
`tools/validate-docs.sh` check 18 fails when a blocked `services/` README does
not name a `mule/` module that cites its ADR.

`TBR-TAK-01` defines the verification for the rest, since it is the trade whose
closure would prove or disprove the transcription in `mule/status.py`.
