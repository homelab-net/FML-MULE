# Status aggregator

**APPROVED, NOT YET IMPLEMENTABLE. This directory contains this `README.md` and
nothing else.**

Part of the reasoning this component would do already exists as a pure
function in `mule/`, under `FML-ADR-052`. See "what already exists in
`mule/`" below before concluding that nothing has been written.

`FML-ADR-046` approves the MULE Status Aggregator as **thin original software**.
`FML-ADR-049` folds the Service Authority Registry into it rather than creating a
sixth standalone daemon.

Approval is not permission to start. The trades that define its data model have
not closed. See below.

## What it does

**Source:** SAD v0.31 sections 22 and 12.

Combines host, RF, network, mission-service, trust, time, storage and power
state into the simplified operator view CONOPS section 67 requires. It must not
require users to interpret BATMAN tables, Linux namespaces or container status.

**Operator states:** `GREEN`, `DEGRADED`, `LOW-BANDWIDTH`, `NON-AUTHORITATIVE`,
`EMCON`, `FAULT`.

**Reason codes** when shared data is not authoritative: `PARTITION`,
`STATE_LAG`, `HOST_RECOVERY`, `NO_SAFE_AUTHORITY`, `UNSYNCHRONIZED`, `UNKNOWN`.

Where available it also reports time since last authoritative synchronization,
the current shared-service host, and whether this node is carrying elevated
service-host power burden (CONOPS section 31).

### Service Authority Registry

A module of this component, not a separate daemon (`FML-ADR-049`). It collects
local service health and authority state, receives approved peer records over
the field IP network, validates their freshness and trust, maintains the local
view of eligible and authoritative hosts, exposes a stable local interface to
HAProxy ingress, marks stale or untrusted records unusable, and reports
disagreement or no-safe-authority conditions.

**It does not elect an authoritative TAK primary.** Authority is determined by
the service-specific continuity mechanism under SAD section 14; the registry
reports and consumes that decision.

Preferred local interface: HTTP/JSON over loopback or a Unix-domain socket, with
an explicit schema and freshness timestamp, and **no general remote
configuration surface**.

## Scope limit

From the MULE-original software inventory, SAD section 29.5:

> Read-mostly normalization and local service-host registry; does not elect TAK
> authority or provide broad configuration authority.

**Owner:** Platform / Field UX / SRE.

## What already exists in `mule/`

`mule/status.py` answers the thirteen CONOPS section 67 questions and uses the
operator states and authority reason codes named above. It is a pure function:
it is handed everything it reasons about, collects nothing, serves nothing, and
holds no state.

`mule/modes.py` sits beside it and places the node on the nine CONOPS section
50 operating-mode axes, per `CCR-01`. `mule/status.py` reads EMCON and the
capability ladder from it rather than deciding either a second time.

`FML-ADR-052` sets out the four conditions that permit both, and why they leave
the reason for this block intact. The short version is that the hazard named
under "why not build it anyway" is **inventing a state taxonomy**, and that
module invents none. It transcribes SAD section 22, and it returns `None`, not
a guess, for `shared_data_authoritative` and `data_stale` - the two answers
`TBR-TAK-01` governs.

So the reasoning exists and is exercised. What does not exist, and what this
directory still means, is everything else: the collection of host, RF, network,
mission-service, trust, storage and power state from the subsystems that hold
it; the local HTTP/JSON or Unix-socket interface; the schema and freshness
timestamp; the Service Authority Registry; and the I2C display module. Those
are the component. A function that reasons about values somebody else gathered
is not.

Whoever builds this should expect to own `mule/status.py` and `mule/modes.py`,
and may find their signatures wrong for their purposes. `FML-ADR-052` records
that cost.

## What must close before implementation starts

| Question | Trade | Priority |
| --- | --- | ---: |
| What mission state exists, and which of it is durable | `TBR-TAK-01` | 9, `CRITICAL` |
| What "failed" and "given up" mean for a service | `TBR-HA-01` | 12 |
| The resource envelope this component may occupy | `TBR-COMP-01` | 2, `CRITICAL` |

`TBR-TAK-01` is the hard dependency. The status surface reports on mission
state, and until the state inventory exists and is classified into the CONOPS
section 26 classes, the data model this component would aggregate is undefined.

## Why not build it anyway

It is tempting: a status page looks shallow, useful immediately, and unlikely to
constrain anything.

It is not shallow. It **defines the node's observable data model**, and every
other part of the system ends up conforming to whatever it decided. An
aggregator written before `TBR-TAK-01` closes will have invented a state
taxonomy, and that taxonomy will be the one the program uses, because it works
and rewriting it is expensive.

## What can be done now

- **Close `TBR-TAK-01`.** It needs no hardware and is `CRITICAL`. The single
  most useful thing anyone can do for this component.
- **Capture fixtures.** Recorded `batctl`, `iw`, Morse Micro driver, nftables,
  hostapd, systemd, power and thermal output, stored in `test/fixtures/` with
  the node, date and image build. Only someone with hardware can produce them,
  and whoever eventually builds this needs them.
- **Write the fakes**, once the interfaces are defined.

## Hardware note

The prototype BOM adds a monochrome I2C display and a sealed momentary
pushbutton, recorded as a **module of this component, not a new daemon**. Dark
by default, momentary wake, roughly 20 mW when lit and zero when off. It gives
EMCON a confirmation path that does not require opening a browser, per CONOPS
sections 65 and 67.
