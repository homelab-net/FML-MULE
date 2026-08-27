# Interface control

Interface control material: the boundaries between the planes, between services
within the mission-service plane, between the host and each radio bearer, and
between MULE and anything outside it.

**Nothing is defined here yet, and that is deliberate.**

## Why this directory is empty

Interfaces are the most expensive thing to get wrong and the most tempting
thing to specify early. An interface written before the trade behind it closes
becomes an obligation that the eventual design has to work around, and it is
usually easier to honour a bad interface than to renegotiate it.

The four placeholder components in `services/` are placeholders for exactly
this reason: their interfaces depend on trades that have not closed. See
`AGENTS.md`, constraint one.

Specifically:

| Interface | Blocked on |
| --- | --- |
| Status surface data model | `TBR-TAK-01`, and the status aggregator's own scope |
| Mission trust and admission | `TBR-SEC-01`, `TBR-TIME-01`, `TBR-TAK-01` |
| Service control and lifecycle | `TBR-HA-01`, `TBR-TAK-01` |
| Gateway translation between planes | `TBR-TAK-01`, `TBR-RF-02` |
| Radio abstraction for the network plane | `TBR-LINUX-01`, `TBR-RF-01`, `TBR-RF-03` |
| Mission configuration package | `TBR-NET-01`, `TBR-TAK-01` |
| Region profile consumed by config generation | stable enough to draft; see `regions/` |

## What belongs here when it starts

One document per interface, each stating:

- The two parties, named as components, not as files.
- The direction of the dependency, and which side is allowed to change without
  the other's agreement.
- The data model, with every field's meaning, units, range, and behaviour when
  absent.
- Failure behaviour: what each side does when the other is slow, absent, or
  wrong. This is the section that is always missing and always needed.
- Versioning and compatibility: how a change is made without breaking a node
  running an older compatibility set (`FML-ADR-040`).
- The ADR that authorised the interface, and the trade whose closure allowed
  it.

## The one interface rule that applies now

The **hardware abstraction rule** in `AGENTS.md` is an interface rule, and it
binds today even though nothing here is written:

> Every function that reads or controls radio, power, thermal, or time state
> **shall** sit behind a narrow interface with a fake or recorded-fixture
> implementation.

When those interfaces are written, they are written here, and their fakes live
alongside the code that implements them. An interface with no fake is not
complete, because nobody without hardware can build against it.

## Interfaces that are not this program's to define

MULE is TAK-compatible, which means it consumes an interface defined elsewhere.
The program does not redefine CoT or the TAK protocol; it records how it uses
them, which is a different document and belongs here when it exists. See
`docs/NON-GOALS.md`.
