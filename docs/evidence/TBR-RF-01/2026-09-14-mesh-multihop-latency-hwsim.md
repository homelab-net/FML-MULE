# Multi-hop mesh latency (hwsim)

**Tier:** `SIMULATED`. `mac80211_hwsim` models the 802.11 MAC and nothing
physical.

**Date:** 2026-09-14. **Node:** development machine (see `docs/dev-machine.md`),
`6.12.105+deb13-amd64 x86_64`, `batman-adv 2024.2` (`batctl debian-2025.0-2`).
**Configuration:** four `mac80211_hwsim` radios, three network namespaces in a
line (node 1 -- node 2 -- node 3), two non-overlapping channels (2412 and
2437 MHz) so node 1 cannot hear node 3, `batman-adv` `BATMAN_IV`,
`bridge_loop_avoidance 0` (`FML-ADR-056`), MTU 1560. **Procedure:**
`test/bench/mesh-traffic.sh latency`. **Taken by:** Cameron Zobrist.

## What this demonstrates

`docs/architecture/roip-voice-data-flow.md` lists "multi-hop mouth-to-ear
latency" as an open question. This is the **transport half** of it: how much
delay each mesh hop adds, isolated from any audio pipeline. The line topology is
the one `80211s-mesh.sh --line` established -- node 2 carries a radio on each
segment and relays, so node 1 reaches node 3 only through node 2 (asserted by
node 1 seeing exactly one peer). Latency is read from `ping -D` wire timestamps
over 50 samples at 200 ms, the method `.github/workflows/mesh-probe.yml` uses
rather than a polling loop that measures its own resolution.

## Run

```text
Preparing 4 virtual radios
Building a line: node 1 -- node 2 -- node 3 (node 1 cannot hear 3)
  line converged, both hops reachable, and node 1 sees exactly one peer

RTT, 50 samples at 200 ms (ping -D, wire timestamps)
  1 hop  0.066/0.087/0.109/0.008 ms  (min/avg/max/mdev)
  2 hop  0.080/0.101/0.136/0.008 ms  (min/avg/max/mdev)

Tier: SIMULATED. hwsim models the 802.11 MAC and nothing physical.
Transport only (no audio pipeline). Advances TBR-RF-01; cannot close it.
```

## The reading

The second hop adds roughly 15 microseconds of average RTT on this bench
(0.087 ms one hop, 0.101 ms two hops) -- stack and relay cost, not propagation.
The figure that matters is the **shape**, not the absolute value: hop cost here
is a small, stable stack delay, because hwsim's wire is instantaneous. On real
radios the per-hop cost is dominated by channel access, retransmission and rate
adaptation, none of which exist here, so a real two-hop figure will be orders of
magnitude larger and is a hardware measurement.

The single-step case holds before the two-hop one is trusted: node 1 reaches
node 2 (one hop) and the line is asserted real (one peer at node 1) before the
node 1 -> node 3 number is read, per CLAUDE.md.

## What it is not

- **Not an RF latency.** `hwsim` has no medium: no path loss, no contention
  window, no retransmission, no rate adaptation. Every per-hop delay these add is
  absent. This is stack and relay cost on a perfect wire.
- **Not mouth-to-ear.** The RoIP audio pipeline (DigiRig capture, Opus
  encode/decode, jitter buffer, radio keying) is unbuilt (`TBR-VOICE-01`) and
  contributes none of this. Mouth-to-ear latency adds all of that on top.
- **Not a `TBR-RF-01` closure.** `TBR-RF-01` `requires-hardware: yes`: it closes
  on measured throughput and latency between real nodes at recorded separations.
  This advances the analysis half (ITEP rig R0/R1); it does not close the trade.
- **Not a hop-count limit.** Two hops is what the four-radio line affords; it
  says nothing about how latency grows across many hops on a real mesh.

## Cross-references

- `test/bench/mesh-traffic.sh` -- the procedure.
- `test/bench/80211s-mesh.sh` -- the line topology this reuses.
- `.github/workflows/mesh-probe.yml` -- the wire-timestamp method, and the
  31.5 s bridge-loop-avoidance figure that a tens-of-seconds first reply would
  indicate (a config bug, not a finding).
- `docs/architecture/roip-voice-data-flow.md` -- the open question this answers
  the transport half of.
- `docs/trades/TBR-RF-01-high-rate-mesh-implementation.md` -- the trade.

Nothing real: no deployment location, member identity, callsign, credential, or
operational capture. The addresses, channels and mesh id are bench values. See
`SECURITY.md`.
