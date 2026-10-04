# Evidence for TBR-NET-05

**Trade:** How does a node assign the EUD access-point subnet and DHCP

**Trade file:** `docs/trades/TBR-NET-05-how-does-a-node-assign-the-eud-access-point-subnet-and-dhcp.md`

**Current contents:** one written decision,
[`2026-10-03-ap-subnet-and-dhcp-decision.md`][decision]. It was independently
verified before filing, and **it is a finding that narrows the trade rather than
closure.** The trade stays `OPEN` on gate element 2: it gives a sourced basis for
the range and **no lease**, because nobody has measured one and
`os/config/dnsmasq.conf.template` says so.

What it settles in shape: the subnet is per-deployment and carried in the mission
package, and on a **meshed** node there is no separate AP subnet at all, because
SAD section 4.3 bridges EUD access into the BATMAN domain and `FML-ADR-056` puts
the AP interfaces in the mesh bridge. Per-node non-overlapping DHCP scopes are
**derived from SAD 4.3**, not discovered here -- an earlier draft asserted no
document decided it and was wrong by one blank line.

It also records a problem it does not solve: `interface=` plus `bind-interfaces`
cannot scope DHCP off the mesh once the AP is a bridge port, so the dnsmasq
template's own mitigation is void as written.

This trade was raised 2026-09-26 as the unowned AP-addressing gap (GAP-09H gap
register G6): `TBR-NET-01` is `CLOSED` on the mesh field prefix only and
`TBR-NET-02` is `CLOSED` on recipient identity, so neither owns the EUD AP subnet
or DHCP.

[decision]: 2026-10-03-ap-subnet-and-dhcp-decision.md

Read the **Closure evidence** and **Closure gate** sections of the trade file
named above. Those sections are authoritative; this file does not restate them,
so that the two cannot drift apart.

Naming and recording rules are in `docs/evidence/README.md`. Nothing real: no
deployment location, member identity, callsign, credential, or operational
capture. See `SECURITY.md`.
