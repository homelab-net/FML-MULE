# Evidence for TBR-NET-04

**Trade:** How does the mesh elect and pool WAN gateways across multiple uplinks

**Trade file:** `docs/trades/TBR-NET-04-how-does-the-mesh-elect-and-pool-wan-gateways-across-multiple-uplinks.md`

**Current contents:** one `SIMULATED` routing-logic demonstration. This trade is
still `OPEN`: the demonstration covers the parts `mac80211_hwsim` can reach and
none of the hardware or decision parts the closure gate demands.

- `2026-09-04-gateway-sharing-hwsim.txt` -- a run of
  `test/bench/wan-gateway-sharing.sh` (two gateway nodes, one WAN-less node)
  recording gateway election, reachability through a peer's uplink, failover
  when the serving gateway leaves, and the default-route state across an induced
  partition, with an explicit list of what it is **not** (not the
  pooling-vs-failover decision, not a throughput number, not real-radio
  selection, not the overlay-boundary proof).

What remains for closure is in that run record and in the trade's **Bench
progress** section: the pooling-vs-failover decision and its `GatewayMode` ADR,
the hardware measurements, and named-owner acceptance.

Read the **Closure evidence** and **Closure gate** sections of the trade file
named above. Those sections are authoritative; this file does not restate them,
so that the two cannot drift apart.

Naming and recording rules are in `docs/evidence/README.md`. Nothing real: no
deployment location, member identity, callsign, credential, or operational
capture. See `SECURITY.md`.
