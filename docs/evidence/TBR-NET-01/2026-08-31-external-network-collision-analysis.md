# Collision with expected external networks, and why the prefix cannot fix it

**Trade:** `TBR-NET-01`.
**Date:** 2026-08-31.
**Taken by:** Cameron Zobrist, on the lab development machine.
**Status of this artifact:** `SIMULATED`. `batman-adv` over `veth` in network
namespaces, the same construction `.github/workflows/mesh-probe.yml` uses. **No
radio was involved.**

## What this supplies

The last of `TBR-NET-01`'s three closure-evidence items:

> Whether retaining `10.41.0.0/16` creates unacceptable collision risk with
> **expected external networks**.

The other two are supplied by the three artifacts dated 2026-08-30.

## What counts as an expected external network

From the architecture rather than from imagination:

- **The parent Homelab**, `10.77.0.0/16` and `10.78.0.0/16`. SAD section 4.2
  cites non-conflict with these as a reason to retain `10.41.0.0/16`.
- **A WAN overlay.** SAD section 18 and `FML-ADR-039` put Tailscale, or an
  equivalent, on MULE infrastructure. Tailscale's own device addresses are
  drawn from the `100.64.0.0/10` CGNAT range, so they cannot collide with
  `10.41.0.0/16`. **Its subnet routers can**: Tailscale documents support for
  "overlapping routes with different prefix lengths from multiple subnet
  routers", which is the mechanism below.
- **A wired uplink to whatever is at the incident.** SAD section 179 lists
  Ethernet among the external interfaces. A venue, a partner organization or an
  agency network is not under this program's control and RFC 1918 gives it all
  of `10.0.0.0/8` to choose from.

**SAD section 4.2's claim is correct and is not sufficient.** `10.41.0.0/16`
genuinely does not overlap `10.77.0.0/16` or `10.78.0.0/16`. Those are the two
external networks the program controls, and they are not the ones that matter.

## The result: a more specific route takes the mesh away, silently

A node with `10.41.0.0/16` on `bat0` and two mesh peers, `10.41.5.7` and
`10.41.9.9`. Both reachable, 0% loss. Then it is plugged into a venue LAN that
happens to use `10.41.5.0/24`, and takes the lease that LAN offers:

```text
routing table
  10.41.0.0/16 dev bat0 proto kernel scope link src 10.41.0.1
  10.41.5.0/24 dev u1   proto kernel scope link src 10.41.5.20

mule -> 10.41.5.7  (MESH node, inside the venue range) : 100% packet loss
mule -> 10.41.9.9  (MESH node, outside it)             :   0% packet loss

route chosen for 10.41.5.7 : dev u1   src 10.41.5.20
route chosen for 10.41.9.9 : dev bat0 src 10.41.0.1
```

**Part of the mesh disappears and the rest keeps working.** Longest-prefix match
sends everything in the venue's `/24` out of the Ethernet port. The mesh nodes
in that range are gone; every other mesh node is fine.

That is worse than total failure. A node that loses the whole mesh is
diagnosed in a minute. A node that loses seven of its peers and keeps twenty is
diagnosed as a radio problem, and the artifacts under this trade already show
how much time that costs.

**Nothing reports it.** The kernel ring contains only `batman-adv` interface
messages. There is no duplicate-address warning and no route-conflict warning,
because nothing is wrong: the kernel is doing exactly what longest-prefix match
says it must.

### The overlay case is larger

The same node, with a `/17` reaching it the way a Tailscale subnet router
advertises a route:

```text
route chosen for 10.41.5.7 : via 10.99.0.1 dev u1
route chosen for 10.41.9.9 : via 10.99.0.1 dev u1
mule -> 10.41.5.7 : 100% packet loss
mule -> 10.41.9.9 : 100% packet loss
```

**One `/17` advertised by any node in the tailnet takes half the field prefix
away from the mesh**, on every MULE that accepts the route. `FML-ADR-039` keeps
EUDs off the tailnet; it does not keep tailnet routes off the MULE.

## Why choosing a different prefix does not fix this

**The failure is not a property of `10.41.0.0/16`.** It is a property of holding
the field mesh in a routed prefix while the same node also routes an uplink. Any
fixed prefix behaves identically; a different `/16` only changes which venues
trigger it. A larger prefix is worse, because it overlaps more. A smaller one is
better only until it collides, and then loses proportionally more of itself.

So the trade's question as written -- "Retain `10.41.0.0/16` or select another
field prefix?" -- **cannot be answered in a way that removes this risk.** Prefix
selection is the wrong instrument. What the evidence asks for is a rule about
how the node routes, not about what it is numbered.

That is a finding about the question, not an answer to it, and this artifact
does not rewrite the trade.

## Candidate mechanisms, none tested here

Recorded so the trade has somewhere to start, and explicitly **not** measured:

- **Policy routing.** A separate routing table for mesh destinations, selected
  by an `ip rule`, so the mesh is not in competition with uplink routes at all.
- **A VRF** holding the mesh interface, which is the same idea with a stronger
  boundary and more moving parts.
- **Refusing overlapping routes from the overlay**, which Tailscale exposes as
  an option on the accepting node, and which turns a silent partial outage into
  a route that is simply not installed.
- **Not accepting a lease on the uplink at all**, which is plausible for a node
  whose uplink exists only to reach an overlay, and which `TBR-NET-02`'s
  addressing work would need to agree with.

Each of these is a decision with its own consequences and none is free. Picking
one is the trade's job.

## What this does not establish

**No survey of what prefixes real organizations use, and none is offered.** The
result above does not depend on how common `10.41.0.0/16` is, which is the
question the trade's wording implies and which this artifact argues is the wrong
one. Anyone wanting that number would have to gather it from real networks, and
it would not change the mechanism.

**None of the candidate mechanisms was tested.** They are named from the
architecture, not measured, and at least one of them may fail for a reason that
only appears on a bench.

**No IPv6.** CONOPS section 5.4 and SAD section 4.4 make v1 IPv4-first. The
link-local result in `docs/evidence/TBR-NET-03/2026-08-30-what-happens-with-no-configuration.md`
is relevant here -- link-local addresses cannot be taken away by an uplink route
-- and nothing in this artifact tests that.

**`veth`, not radios**, and one uplink, one venue, two mesh peers. A real
incident has more of everything.

**Nothing about what the venue sees.** The MULE sending mesh-destined traffic
onto a venue LAN is a disclosure question as well as a delivery one, and
`THREAT_MODEL.md` was not consulted for this artifact.
