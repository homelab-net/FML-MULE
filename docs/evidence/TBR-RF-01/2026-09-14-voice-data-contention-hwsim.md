# Voice-versus-data contention on one bearer (hwsim)

**Tier:** `SIMULATED`. `mac80211_hwsim` models the 802.11 MAC and nothing
physical, and the bottleneck below is imposed, not measured.

**Date:** 2026-09-14. **Node:** development machine (see `docs/dev-machine.md`),
`6.12.105+deb13-amd64 x86_64`, `batman-adv 2024.2` (`batctl debian-2025.0-2`).
**Configuration:** two `mac80211_hwsim` radios, two network namespaces, 802.11s
mesh at 2412 MHz, `batman-adv` `BATMAN_IV`, `bridge_loop_avoidance 0`
(`FML-ADR-056`), MTU 1560; a `tc` bottleneck of 5 Mbit imposed on node 1's
`bat0` egress (see below). **Procedure:** `test/bench/mesh-traffic.sh
contention`. **Taken by:** Cameron Zobrist.

## What this demonstrates

`docs/architecture/roip-voice-data-flow.md` lists "voice and data QoS contention
on one bearer under load" as an open question, and CONOPS section 40 requires
that "traffic policy shall preserve mission-critical communications before
bandwidth-intensive services." `FML-ADR-021`'s standing warning is the failure
mode: on one compute element a bulk flow starves the real-time flow, and the node
looks like it has a radio fault when it has a scheduling fault.

A voice-profile flow (~160-byte packets every 20 ms, an Opus-like cadence) runs
node 1 -> node 2 in three conditions: alone; alongside a saturating bulk flow in
one FIFO; and alongside the same bulk flow with the voice class (DSCP EF)
protected. One-way latency and jitter are meaningful because both namespaces read
one host clock -- a property of the bench, stated in `test/bench/udpflow.py`.

**Why a bottleneck is imposed.** hwsim's wire has no capacity of its own, so
without a rate limit a bulk flow cannot contend for bandwidth and nothing
degrades (measured: idle and loaded were indistinguishable). A 5 Mbit `tc`
bottleneck on the egress models a constrained bearer so the **scheduling**
behaviour is visible. The rate is illustrative; it is not a real-radio capacity.

## Run

```text
Preparing 2 virtual radios
Building a flat 2-node mesh (one shared bearer)
  mesh converged

Voice-profile flow (~160 B/20 ms) over an imposed 5mbit bottleneck
  a. voice alone               loss 0.0 %  jitter 0.011 ms  latency avg 0.151 ms  (recv 493/493)
  b. + bulk, one FIFO (no QoS) loss 0.0 %  jitter 32.356 ms  latency avg 161.467 ms  (recv 496/496)
  c. + bulk, voice prioritized loss 0.0 %  jitter 0.024 ms  latency avg 0.109 ms  (recv 495/495)

Tier: SIMULATED. hwsim models the 802.11 MAC and nothing physical.
Transport only (no audio pipeline). Advances TBR-RF-01; cannot close it.
```

## The reading

The starvation is stark and reproducible. Sharing one FIFO with a saturating
bulk flow, the voice flow's average one-way latency rises from 0.15 ms to
**161 ms** and its jitter from 0.01 ms to **32 ms** -- unusable for real-time
voice on delay and jitter alone, even though not a single packet was lost. That
is exactly `FML-ADR-021`'s failure shape: the queue, not the loss, is what
breaks the call. Putting the voice class in a protected band under the same load
returns it to 0.11 ms and 0.02 ms jitter, at parity with the idle case.

So CONOPS section 40's requirement is achievable in principle -- the
mission-critical class can be preserved ahead of bulk -- and the cost of not
doing it is a call that fails while every link looks healthy.

## What it is not

- **Not an RF capacity measurement.** The 5 Mbit bottleneck is imposed with `tc`
  because hwsim has no medium; it is not the rate of any radio. Real bearer
  capacity, and how voice and bulk actually share a real channel, is a hardware
  item (`TBR-RF-01`, `TBR-RF-02`).
- **Not a QoS mechanism decision.** The protected-class demonstration uses an
  `htb`/DSCP-EF arrangement solely to show the contention is addressable.
  `TBR-RF-01` owns the traffic-class mechanism; this selects nothing.
- **Not mouth-to-ear, and not a real codec.** The flow is a UDP packet cadence,
  not encoded audio; the RoIP pipeline is unbuilt (`TBR-VOICE-01`). A real jitter
  buffer would absorb some of the (b) jitter and add its own latency.
- **Not the routing daemon starving.** This instruments a voice flow starving,
  the user-visible half. The `batman-adv` control traffic starving under the same
  pressure -- the "looks like a radio fault" half -- is bounded by `TBR-COMP-01`
  on the target and is not measured here.
- **Not a `TBR-RF-01` closure.** It advances the traffic-preference analysis
  half (ITEP rig R0/R1); the trade closes on hardware.

## Cross-references

- `test/bench/mesh-traffic.sh`, `test/bench/udpflow.py` -- the procedure and the
  flow instrument.
- `docs/architecture/roip-voice-data-flow.md` -- the open question this answers
  the transport half of.
- `docs/trades/TBR-RF-01-high-rate-mesh-implementation.md` -- the trade, whose
  closure gate names CONOPS section 40 traffic-preference behaviour.
- `docs/change-requests/CCR-03-integrated-rf-dm32-roip-voice.md` -- the RoIP
  capability whose QoS demand this characterises.

Nothing real: no deployment location, member identity, callsign, credential, or
operational capture. The addresses, mesh id and rates are bench values. See
`SECURITY.md`.
