# Status aggregator

**APPROVED. The fielded component is still `NOT YET IMPLEMENTABLE` -- it is gated
on `TBR-HA-01` and `TBR-COMP-01` -- but its hard dependency has closed and the
operator status roll-up is now buildable as a bench increment. This directory
contains this `README.md` and nothing else.**

`TBR-TAK-01` -- the hard dependency below -- closed 2026-09-06 on `FML-ADR-071`,
which classified all mission state and so defines the data model this component
aggregates. With that retired, the host/RF/network/time/thermal/power operator
roll-up can be built as a **bench increment** that reuses `mule/status.py` (the
"what can be done now" section says how), verified 2026-09-14 by an independent
agent. What is still gated: the Service Authority Registry (`TBR-HA-01`), the
resource envelope for a fielded daemon (`TBR-COMP-01`), a **production**
mesh-links reader (parked in `test/` on `TBR-RF-01`/`TBR-RF-03`/`TBR-LINUX-01`,
so live mesh links are a bench demonstration only), and the I2C display
(hardware).

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
| What mission state exists, and which of it is durable | `TBR-TAK-01` | 9, `CRITICAL` -- **CLOSED 2026-09-06 (`FML-ADR-071`)** |
| What "failed" and "given up" mean for a service | `TBR-HA-01` | 12 -- OPEN |
| The resource envelope this component may occupy | `TBR-COMP-01` | 2, `CRITICAL` -- OPEN |

`TBR-TAK-01` was the hard dependency, and it has closed: the state inventory
exists and is classified into the CONOPS section 26 classes (`FML-ADR-071`), so
the data model this component aggregates is now defined. The operator status
roll-up is therefore buildable as a bench increment. The remaining two gates are
narrower than the whole component: `TBR-HA-01` governs the Service Authority
Registry (peer authority, the `shared_data_authoritative`/`data_stale` fields,
which stay `None` until it closes), and `TBR-COMP-01` sizes a fielded daemon, not
a bench increment.

## Why not build it anyway

It is tempting: a status page looks shallow, useful immediately, and unlikely to
constrain anything.

It is not shallow. It **defines the node's observable data model**, and every
other part of the system ends up conforming to whatever it decided. That was the
reason to wait for `TBR-TAK-01`, and with it closed (`FML-ADR-071`) the state
taxonomy is defined rather than invented -- so a bench increment that only reuses
`mule/status.py`/`mule/modes.py` and adds collection plus a local transport
invents no taxonomy.

The hazard now re-enters at **the served schema**, and the trade that owns it is
`TBR-HA-01`, not `TBR-TAK-01`: if the schema grows authority, freshness or
Service-Authority-Registry vocabulary with wire semantics no closed document
fixes, it invents the taxonomy `TBR-HA-01` will later own. Keep the served schema
to exactly the fields `NodeStatus` already carries, emit
`shared_data_authoritative` and `data_stale` as explicit `null`, and name
`TBR-HA-01` in the schema comment.

## What can be done now

- **Build the operator status roll-up as a bench increment.** `TBR-TAK-01` is
  closed, so this is now the most useful thing anyone can do here. Assemble
  `Observations` from the existing readers (`mule/sysfs.py` thermal, the
  `mule/timekeeping.py` assessment, bearer and mesh liveness via the `test/`
  `CommandRadio` over `iw`/`batctl`, honest `None` for power), call
  `mule/status.py:derive`, and serve `NodeStatus` as JSON over loopback or a
  Unix socket with a freshness timestamp and no remote configuration surface --
  keeping the schema to the fields `NodeStatus` already carries. Exercise it on
  the `mac80211_hwsim` mesh bench; do not promote a production mesh-links reader
  (still parked on the RF/LINUX trades) or a fielded daemon (`TBR-COMP-01`).
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
