# WAN gateway election: single-active versus pooled

**Trade:** `TBR-NET-04`.
**Date:** 2026-09-15.
**Taken by:** Cameron Zobrist, on the lab development machine.
**Status of this artifact:** analysis, built on a `SIMULATED` bench. It records
the single-active-versus-pooled comparison `TBR-NET-04`'s closure gate asks the
owner to make; it does not close the trade (throughput and real-radio selection
are hardware).

## The open question

`FML-ADR-069` decides WAN is a mesh-wide, ideally pooled capability and names no
mechanism. `TBR-NET-04` asks: when several MULEs hold uplinks, how does the mesh
decide which carries a WAN-less node's traffic, and are the uplinks **pooled for
capacity** or **held as failover**? The closure gate says whether pooling is
multi-active or failover-only is a comparison the owner records against the
resilience and contention observed -- which is this artifact.

## What the bench shows (batman gw_mode is single-active with failover)

`test/bench/wan-gateway-sharing.sh` runs `batman-adv` gateway mode on
`mac80211_hwsim`: two gateway nodes, one WAN-less client. Re-run 2026-09-15 with
an added assertion:

```text
  batman selected gateway 10.41.0.2; client lease: ip=10.41.2.18 router=10.41.0.2
  single-active: exactly one default route via 10.41.0.2, though two gateways are available
  ...
  client re-selected surviving gateway 10.41.0.3; lease: ip=10.41.3.18 router=10.41.0.3
```

The load-bearing observation: with **two** gateways advertised, the client
installs **exactly one** default route to **one** selected gateway. `gw_mode
client` selects a single gateway from the `gateways` table and steers DHCP to it;
it does not split traffic across both. When the serving gateway leaves, the
client re-selects the survivor and reaches its uplink; on partition it loses only
WAN, keeping local services (CONOPS 41). That is **single-active with failover**,
and it is native to batman-adv -- no mechanism above it.

## The finding: pooling is not a gw_mode feature

Multi-active **pooling** -- a WAN-less node using two uplinks at once for
capacity -- is not something `gw_mode` does. `gw_mode client` resolves to one
gateway; the default route is singular by construction. Pooling therefore needs a
**mechanism above batman-adv**: ECMP/multipath default routes across two mesh
next-hops, or policy routing that distributes flows, or a service-plane
distributor. None is designed, and each carries its own cost inside IPv4 with
per-gateway source NAT (per-flow vs per-packet balancing, and a return path that
must come back through the same NAT).

## The comparison for the owner

| | Single-active + failover | Pooled multi-active |
| --- | --- | --- |
| Mechanism | batman-adv `gw_mode`, native | a layer above batman (ECMP / policy routing / distributor), undesigned |
| Demonstrated | Yes (`SIMULATED`, this bench) | No |
| Resilience | Failover works; a brief re-selection gap when the serving gateway leaves | No single serving gateway to lose, but more moving parts to fail |
| Capacity | One uplink's bandwidth at a time | Aggregate across uplinks (its whole point) |
| Complexity / risk | Low; one decided mechanism | Higher; new mechanism, NAT return-path and fairness untested |
| CONOPS fit | The v1 baseline (section 42, one active gateway) | The `FML-ADR-069` end-state target |

**Direction, not a decision:** the v1 baseline is single-active, which batman
gives natively and this bench demonstrates; pooling is `FML-ADR-069`'s end-state
target and needs both a mechanism above batman and the hardware measurements
below before it is chosen. The owner records the comparison; the ADR for the
chosen mechanism follows.

## What still needs hardware (not in this artifact)

- **Throughput** per option, which `hwsim` cannot produce (no medium).
- **Real-radio selection stability**: which gateway a real mesh's TQ metric
  picks, and whether it flaps, versus `hwsim`'s equal-TQ tie-break.
- **Contention under load** with the network and service planes co-resident
  (`TBR-COMP-01`, `TBR-RF-01`).

## Cross-references

- `test/bench/wan-gateway-sharing.sh` -- the procedure (now asserts single-active).
- `docs/evidence/TBR-NET-04/2026-09-04-gateway-sharing-hwsim.txt` -- the original
  selection/failover/partition run.
- `docs/adr/FML-ADR-069-a-mule-shares-its-wan-uplink-across-the-mesh-and-available-uplinks-are-pooled.md`
  (WAN is a mesh-wide, pooled capability -- the target) and
  `docs/adr/FML-ADR-068-an-eud-on-the-access-point-is-forwarded-to-the-wan-uplink.md`
  (the node-local first step).
- `docs/ROADMAP-DEV.md` item 1.8.

Nothing real: no deployment location, member identity, callsign, credential, or
operational capture. The addresses and mesh id are bench values. See `SECURITY.md`.
