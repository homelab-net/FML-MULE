# Per-peer capability tier over the mesh (hwsim)

**Tier:** `SIMULATED`. `mac80211_hwsim` models the 802.11 MAC and nothing
physical.

**Date:** 2026-09-18. **Node:** development machine (see `docs/dev-machine.md`),
`6.12.105+deb13-amd64 x86_64`, `batman-adv 2024.2` (`batctl debian-2025.0-2`).
**Configuration:** two `mac80211_hwsim` radios, two network namespaces, 802.11s
mesh at 2412 MHz, `batman-adv` `BATMAN_IV`, `bridge_loop_avoidance 0`
(`FML-ADR-056`), MTU 1560. **Procedure:** `test/bench/operator-view.sh` (which
runs `test/bench/operator-view.py` inside a node namespace). **Taken by:**
Cameron Zobrist.

## What this demonstrates

The operator view now derives a **per-peer capability tier** and shows it, over a
live mesh. The tier vocabulary is `FML-ADR-080`
(`VIDEO`/`VOICE`/`TEXT`/`NONE`/`UNKNOWN`, the per-link view of the CONOPS section
50 ladder); the derivation is the pure `mule/capability.py:capability_tier`,
transcribing those tiers under `FML-ADR-052`; the signals are the passive ones
the flat-sat parser extracts (`test/flatsat/radio_parse.py`:
`station_bitrates_mbps` for the `iw` PHY-rate ceiling, `originator_tqs` for
batman-adv TQ). The tier rides as bench telemetry alongside the status, under
`_bench_peer_capability`, **not** inside `NodeStatus` -- the same discipline the
mesh-link counts follow, because the production per-peer reader is still parked on
`TBR-RF-01`/`TBR-RF-03`/`TBR-LINUX-01`.

The single mesh peer resolved to **`TEXT`**, and the telemetry shows why: the
`2.0` Mb/s PHY-rate ceiling on its own would clear `VOICE`, but the
freshly-converged link's TQ of `12` caps it at `TEXT`. That is exactly the
`FML-ADR-080` discipline -- a loss-derived metric, not the raw rate, sets the
ceiling (`FML-ADR-053`: TQ is not throughput), and the tier is the most
restrictive signal, a **ceiling not an end-to-end guarantee**. Confirming a tier
*in* is the job of item 1.9's paced probe, not this passive readout.

The node is mesh-only, so the view still correctly reports `FAULT` for the missing
required `wifi_ap` (`REQUIRED_BEARERS`); the new thing here is the per-peer tier
line, not the node state.

## Caveats

- `SIMULATED`: hwsim rates and TQ are stack behaviour, not RF. TQ in particular
  varies run to run as the mesh converges; this run caught a low, early TQ, which
  is why the ceiling landed at `TEXT` rather than higher.
- The thresholds are the illustrative `BENCH_POLICY` in the bench, **not**
  `TBR-RF-01`'s values, which `FML-ADR-080` keeps out of the code. Different
  thresholds would move the tier boundaries; the logic, not the numbers, is what
  this shows.
- A tier is a ceiling. Whether the peer can actually sustain that tier end to end
  is `TBR-RF-01` / hardware, via item 1.9's probe.

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
  peer tiers:   66:a2:0b:f5:8d:32 TEXT (2.0 Mb/s, TQ 12)  (ceiling, not a guarantee)
  as of:        2026-09-18T16:53:10.944911+00:00

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
  "as_of": "2026-09-18T16:53:11.035418+00:00",
  "_bench_mesh_links": {
    "peers": 1,
    "originators": 1
  },
  "_bench_peer_capability": {
    "66:a2:0b:f5:8d:32": {
      "tier": "TEXT",
      "mbps": 2.0,
      "tq": 12
    }
  }
}

Tier: SIMULATED. hwsim models the 802.11 MAC and nothing physical.
```
