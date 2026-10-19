# A third mesh node over a VXLAN tunnel, and TAK chat across three IP bearers

**Tier: real-hardware bench result; formal `HARDWARE-VERIFIED` held.** **Every
figure involving the tunnel is an EMULATED bearer.** The bench mule's two Wi-Fi
radios cannot be 802.11s mesh points, so it joins the batman-adv mesh through a
unicast VXLAN tunnel carried over the home Wi-Fi. That is an IP tunnel, not the
selected mesh, and it does not count toward M2's selected mesh. Both Pi nodes
read `0x50005` (under-voltage, throttled), so timings are provisional.

| Item | Value |
| --- | --- |
| Date | 2026-10-18, about 20:35 to 20:45 local |
| Taken by | Cameron Zobrist (the Program Owner) on the phone and at the bench, with Claude Code operating the bench at his direction |
| Procedure | `test/bench/mesh-vxlan-node.sh` (`mule1-up` and `pi-up`; `*-down` removes everything) |

## Topology

pi-mule-1 —802.11s, 5745 MHz— pi-mule-2 —VXLAN over home Wi-Fi— bench mule

- The bench mule joined `bat0` as 10.42.0.3. Settings matched the Pis: BATMAN_IV,
  `bridge_loop_avoidance` off (FML-ADR-056), multicast mode off, fragmentation on.
- Its only batman-adv neighbour was pi-mule-2. Its originator table reached
  pi-mule-1 **with pi-mule-2 as next hop**, so pi-mule-1 was two hops away: the
  tunnel, then 802.11s.

| Hop | RTT, 5 pings, avg (min-max) |
| --- | --- |
| bench mule -> pi-mule-2, 1 hop | 30.9 ms (1.5-70.8) |
| bench mule -> pi-mule-1, 2 hops | 19.0 ms (5.4-35.2) |

The spread and the inversion are what throttled nodes produce. No capacity
figure is claimed.

**Safety on a shared host.** The bench mule also hosts a live server. A guard in
its own tables admitted **only** the bench access point's clients to the bench
TAK servers' port 8089 across the mesh, masqueraded, and admitted nothing from
the mesh to the host's own services. The live server's TAK listener was checked
untouched before and after.

## Multi-bearer TAK chat between two real clients

- **iTAK on iOS** joined the bench mule's access point and connected to
  pi-mule-1's TAK Server **by its mesh address**. pi-mule-1 saw the session
  arrive from 10.42.0.3, the bench mule's mesh address. So the path was:
  2.4 GHz AP -> bench mule -> VXLAN over home Wi-Fi -> pi-mule-2 -> 802.11s ->
  pi-mule-1.
- **WinTAK** connected to the same server over the home LAN.
- The LoRa gateways were **stopped**, so nothing crossed RF on sub-GHz.

| Direction | Result |
| --- | --- |
| WinTAK -> iTAK, a direct message | delivered |
| iTAK -> WinTAK, the reply | **delivered** (WinTAK showed it received about 48 s after its own send, including the time for the owner to read and type) |

## What this does not establish

- The selected mesh's behaviour on this path: the tunnel is emulated.
- Capacity, latency under load, or failover around a lost relay. The topology
  supports that test, but it was not run.
- Anything without the live host. The bench mule's access point and routing
  belong to a host with other duties; that is a bench arrangement, not a design.

## Procedures

`test/bench/mesh-vxlan-node.sh`, with addresses and interface names read from an
uncommitted `/etc/fml/mesh.env`.
