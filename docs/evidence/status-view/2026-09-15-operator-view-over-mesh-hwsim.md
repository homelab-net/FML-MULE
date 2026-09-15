# Operator status view over the mesh (hwsim)

**Tier:** `SIMULATED`. `mac80211_hwsim` models the 802.11 MAC and nothing
physical.

**Date:** 2026-09-15. **Node:** development machine (see `docs/dev-machine.md`),
`6.12.105+deb13-amd64 x86_64`, `batman-adv 2024.2` (`batctl debian-2025.0-2`).
**Configuration:** two `mac80211_hwsim` radios, two network namespaces, 802.11s
mesh at 2412 MHz, `batman-adv` `BATMAN_IV`, `bridge_loop_avoidance 0`
(`FML-ADR-056`), MTU 1560. **Procedure:** `test/bench/operator-view.sh` (which
runs `test/bench/operator-view.py` inside a node namespace). **Taken by:**
Cameron Zobrist.

## What this demonstrates

The buildable Phase-1 slice of the Status Aggregator (`FML-ADR-046`, CONOPS
section 67), unblocked when `TBR-TAK-01` closed (`FML-ADR-071`) and defined the
mission-state data model. The reasoning already existed as pure functions
(`mule/status.py:derive`, `mule/modes.py`, `FML-ADR-052`); what the component's
README said did not exist was the **collection and a local transport**, and that
is what this adds: `Observations` assembled from the node's real readings
(`mule/sysfs.py` thermal and clock, the `mule/timekeeping.py` assessment, bearer
and mesh liveness via `iw`/`batctl`, honest `None` for power), and `NodeStatus`
served as JSON over loopback.

The node is mesh-only, so the operator view correctly reports `FAULT` for the
missing required `wifi_ap` (`REQUIRED_BEARERS`) -- the point is that the view
tells the truth from real readings and shows the live mesh link, not that this
minimal node is `GREEN`.

## Run

```text
Preparing 2 virtual radios
Mesh converged; node 1 has a live peer.

=== operator view (text) ===
MULE operator view (bench, SIMULATED)
  state:        FAULT
  operational:  False
  network:      ok
  tak:          no
  fault:        RADIO_ABSENT: required bearer(s) wifi_ap
  authoritative:None  (null until TBR-HA-01)
  live mesh:    1 peer(s), 1 originator(s)
  as of:        2026-09-15T01:15:49.604018+00:00

=== operator view (JSON, the served schema) ===
{
  "status": {
    "operational": false,
    "battery_healthy": null,
    "projected_runtime_minutes": null,
    "hosting_shared_services": false,
    "hosting_reduces_runtime": null,
    "tak_available": false,
    "shared_data_authoritative": null,
    "data_stale": null,
    "network_degraded": false,
    "lora_available": false,
    "wan_available": null,
    "emcon_active": false,
    "fault": "RADIO_ABSENT: required bearer(s) wifi_ap",
    "authority_reason": "NO_SAFE_AUTHORITY",
    "state": "FAULT"
  },
  "as_of": "2026-09-15T01:15:49.689779+00:00",
  "_bench_mesh_links": {
    "peers": 1,
    "originators": 1
  }
}
```

## The reading

The operator view composes from the node's own readings and reports the truth: a
**live mesh link** (one peer, one originator, read from `iw`/`batctl` on the
hwsim mesh), the network not degraded, and a `FAULT` naming the one thing an
operator must fix first -- the required access point is absent on this mesh-only
node. The served document is exactly `mule.status.NodeStatus`; the two fields
`TBR-HA-01` governs (`shared_data_authoritative`, `data_stale`) are explicit
`null`, and the mesh-link counts ride under a separate `_bench_mesh_links` key so
the status schema invents no vocabulary. The single-step case holds first: the
mesh converged and a ping crossed before the view was trusted.

## What it is not

- **Not the fielded component.** It is a bench increment: no resource commitment
  (`TBR-COMP-01`), no remote configuration surface, loopback only. It is not a
  catalog service or a daemon.
- **Not the Service Authority Registry.** `shared_data_authoritative` and
  `data_stale` stay `null`; the peer-authority logic is `TBR-HA-01`'s and is not
  built. `authority_reason` reads `NO_SAFE_AUTHORITY` because no authority
  mechanism exists to report otherwise.
- **Not a production mesh-links reader.** The live-link counts come from a bench
  readout over `iw`/`batctl`; the production `RadioState` interface is parked in
  `test/` on `TBR-RF-01`/`TBR-RF-03`/`TBR-LINUX-01`. `hwsim` has no medium, so a
  peer count here is MAC-layer, not an RF link.
- **Not a state taxonomy invention.** It reuses the `SAD` section 22 states
  `mule/status.py` already emits (`FML-ADR-052`); with `TBR-TAK-01` closed the
  taxonomy is defined, not invented. The served schema is held to `NodeStatus`'s
  existing fields.

## Cross-references

- `test/bench/operator-view.py`, `test/bench/operator-view.sh` -- the procedure.
- `services/status-aggregator/README.md` -- the component and its remaining gates.
- `docs/adr/FML-ADR-046-status-aggregator-approved-original-software.md`,
  `FML-ADR-049`, `FML-ADR-052` -- the decisions.
- `docs/trades/TBR-TAK-01-mission-critical-state-boundary.md` (`CLOSED`,
  `FML-ADR-071`) -- the dependency whose closure unblocked this.
- `docs/ROADMAP-DEV.md` item 4.7.

Nothing real: no deployment location, member identity, callsign, credential, or
operational capture. The addresses and mesh id are bench values. See
`SECURITY.md`.
