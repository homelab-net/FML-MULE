# Bench remediation plan, 2026-10-11

How to close the distance between what the bench has shown and what the CONOPS
asks. `docs/conops-traceability.md` is the companion: it records the position,
this file records the route.

## The position, stated plainly

CONOPS v1.2 carries **185 `[SHALL]` statements**. One is demonstrated at bench
scale (section 40), one for a single stated purpose (section 33), one function
list (section 21), and two partially (sections 39 and 41). `STATUS.md` has the
program at **pre-PDR**, with nothing hardware-verified and no production
hardware selected. Nothing in this plan changes those facts; it orders the work
that would.

## A sequencing conflict to settle before spending anything

`ROADMAP.md` scopes `v0.0.1` to **one node, one service, reachable from a phone**
and says so emphatically: *"Not two nodes, not a mesh."* It also records why a
mesh milestone has not started -- it depends on `TBR-LINUX-01`, which needs
hardware nobody had.

Every measurement taken on 2026-10-11 is legitimate `TBR-RF-01` evidence, and
**none of it is on the `v0.0.1` critical path.** That is not an argument against
having taken it; the high-rate radios arrived and the runbook said what to do
with them. It is an argument for deciding deliberately, now, whether the next
effort finishes `v0.0.1` or continues building mesh evidence. Drifting between
the two is the failure this plan is most worried about, and
`docs/ROADMAP-DEV.md` has a section on how this program gets things wrong.

**This plan assumes the answer is "both, in this order: Phase 0 first, because it
is cheap and closes a deferred decision, then the `v0.0.1` call."**

## Phase 0 -- configuration defects, no hardware

Three defects found by measurement, not review. Two are open.

### 0.1 `mesh_plink_timeout` is 1800 seconds

A node whose mesh was fully torn down still appeared as an 802.11s peer on the
surviving node **302 seconds later**, and would have for half an hour: the
default `mesh_plink_timeout` is **1800 s**. Section 39 requires the network to
adapt to node loss and changing neighbours. A thirty-minute stale peer link does
not.

Action: measure node-loss detection against candidate timeouts, weigh against
the cost of re-establishing a link that was only briefly quiet, and submit the
result to `TBR-RF-01` as an ADR input. **Do not simply lower it** -- an
aggressive timeout on a lossy link churns peers, which is the opposite failure.

### 0.2 `orig_interval` is still `TBD`, and now answerable

`os/config/batman-adv.conf.template` leaves `orig_interval` undecided and says
exactly why:

> Still TBD, because the question this value actually decides is convergence
> after a TOPOLOGY CHANGE on a lossy link, which veth cannot pose. TBR-RF-01
> owns that.

**The bench can now pose it.** Two real radios, a tunable channel width, and
`tc netem` on the hard interface to make the link lossy on demand. Measuring
convergence after a topology change at several `orig_interval` values closes a
decision the program deferred for want of exactly this.

This is the highest-value cheap measurement available and should be done first.

**Attempted 2026-10-11, and it did not answer.** Recorded in addendum 5 of the
real-radio artifact: four repeats of a single condition spanned 7 to 40 seconds,
a 5.5x spread against between-condition differences of about 3x, so the sweep
across 1000/500/250 ms was noise. `orig_interval` stays `TBD`, and that
addendum lists what a valid experiment needs -- interleaved repeats, a
convergence criterion that is not first-ping-success, symmetric loss, and
controlled rate adaptation. The question is now askable on hardware, which is
the gain; it is not yet answered.

Note what it is not: batman-adv's originator purge was measured at **~165 s**,
consistent with a fixed purge timeout rather than a multiple of
`orig_interval`. So `orig_interval` is the lever for **convergence and
best-path adoption**, not for how fast a dead node is forgotten. Those are two
different complaints about section 39 and only one of them is tunable here.

### 0.3 Channel width -- fixed, but the choice is not made

`iw mesh join` defaults to `NOHT` when the width is omitted, which capped the
"high-rate" bearer at 54 MBit/s and 19.6 Mbps of goodput. Fixed; the bench now
defaults to `HT40+` at 89.5 Mbps, with 80 MHz measured at 114.7 Mbps.

Outstanding: **80 MHz buys 28% more goodput for twice the channel occupancy.**
On a field MANET that trades against spectrum reuse and interference
susceptibility. `TBR-RF-01` owns the selection; the bench default is not it. And
section 33's `[SHALL]` that the band be chosen before RF coexistence analysis
(section 36) remains unsatisfied -- 5745 MHz was a bench pick.

### 0.4 The bench is under-voltage, and that blocks valid measurement

Found 2026-10-14 and recorded in addendum 8: both nodes report
`vcgencmd get_throttled` = `0x50005` -- under-voltage now, throttled now --
pinned at **600 MHz** against a nominal 1.5 GHz, with **1271** under-voltage
events in `dmesg` on pi-mule-2 against 5 on pi-mule-1. Mesh RTT on an otherwise
healthy link moved from 0.9 ms to 61.8 ms on that account alone.

**This outranks the rest of Phase 0**, because it decides whether any number
this bench produces means anything. Two actions:

* **Fix the supply.** The 1271-against-5 split points at the node carrying two
  USB devices; an AWUS036ACM-class radio can take a large share of a Pi's USB
  budget on its own. A powered hub for the radios, or a supply rated for the
  full load, with cable quality checked. `TBR-PWR-01` and CONOPS section 59.
* **Make throttle state part of provenance.** `docs/bench-hardware-bringup.md`
  requires kernel, radio, driver and image with every result; add
  `vcgencmd get_throttled`, and treat a live throttle bit as invalidating the
  run. A throttled node under-reports the radio, which is the direction that
  makes a bearer look worse than it is and would be believed.

Until both are done, **re-measurement outranks new measurement**: addenda 1
through 7 carry numbers that cannot be proved un-throttled.

## Phase 1 -- runnable on the hardware already here

Ordered by whether they produce a definite pass or fail.

1. **Section 42, local WAN gateway** `[SHALL]`. `batctl gw_mode` is present and
   currently `off`. One node keeps its uplink and serves as gateway, the other
   drops its own and reaches WAN through the mesh. Definite outcome, runtime
   only, reversible.
2. **Section 41 remainder.** The `local EUD access` and `local S0/S1 services`
   rows, and a stricter isolation test: the first run left the LAN resolver
   reachable on-link, so it measured loss of off-site path rather than
   isolation.
3. **Section 12, EUD access.** `wlan0` on a pi is free and in managed mode and
   can associate to the EUD access point as a real client. **Blocked on the
   access point PSK**, which is held by the operator and should not be read off
   the COCON host.
4. **Section 22, multicast cost** at one hop. Partial by construction: the
   `[SHALL]` says *representative multi-hop load*, which two nodes cannot pose.

## Phase 2 -- hardware, ranked by requirements unblocked per unit

| Acquire | Rough cost | What it unblocks |
| --- | --- | --- |
| **One more MT7612U / AWUS036ACM** | $30-50 | multi-hop, and with it section 22's hop-count `[SHALL]`, section 39's failover and best-path selection, `mesh-traffic.sh latency`, and an independent monitor-mode RF witness the bench currently lacks entirely |
| **Repair the RAK path on pi-mule-1, add a second LoRa node** | cable, ~$30 | section 35, `TBR-NET-02`'s recipient path, and real-RF GeoChat instead of the docker-bridge simulation |
| **A HaLow radio** (Wio-WM6108 on WM1302, or MM8108 USB) | ~$100+ | section 34, and `TBR-LINUX-01`, which the program calls its dominant uncertainty and which blocks *"almost everything in `os/`"* |

The first is the cheapest unlock by a wide margin: one adapter converts several
"needs a third node" entries at once. The third is the most consequential,
because `TBR-LINUX-01` gates the baseline bearer, the OS work, and the mesh
milestone itself.

A note on the RAK: pi-mule-1 has enumerated exactly **one** USB device since
boot and it is the Wi-Fi adapter. No `spidev`, SPI commented out in
`config.txt`, no `meshtasticd`, and no failed-enumeration errors, which means no
electrical connection is being detected. Check the cable and port before
assuming a firmware or driver fault.

## Phase 3 -- services and trust

Sections 24-30 need OpenTAKServer actually standing. **Correction, 2026-10-14:
one already is.** `services/tak/README.md`'s *"Nothing is loadable yet"* is true
of this repository's own deployment path -- the image has no digest until the
`Containerfile` is built -- but the bench mule is running an OTS stack already,
as seven rootless podman containers (`fml-ots`, `fml-pg`, `fml-mq`,
`fml-cot_parser`, `fml-eud_handler`, `fml-eud_ssl`, `fml-tiles`) with
`opentakserver` listening on 8081 and `eud_handler` on 8088. An earlier draft of
this plan said these sections needed a server stood up first; that was wrong.

So sections 24-30 are **far more reachable than this plan first claimed**, with
one condition that is not negotiable: that instance is part of the live COCON
stack, not a test fixture. Reading from it is fine; a state, partition or
split-brain test writes to it, and `test/bench/tak-state.sh` reproduces
`TBR-TAK-01` by design. Either get explicit agreement to exercise the production
instance, or stand a second OTS from the `Containerfile` on a pi, where podman
is present and the python, postgres and rabbitmq base images are already
cached. Sections 13-18 need the enrollment path, certificates
and revocation. These are `P2`/`P3` in `docs/ROADMAP-DEV.md`'s own phasing and
nothing on 2026-10-11 touched them.

Until a server exists, every TAK result from this bench measures the **bearer
and the encoding**, never ingest, persistence or trust. That distinction should
survive into any summary that leaves the repository.

## What this plan deliberately does not promise

It does not promise that bench results extend to the field; section 22's final
`[SHALL]` forbids assuming it and every artifact says one hop, node-local,
bench range. It does not promise a tier change: `README.md` and
`test/README.md` both still state that nothing here is `HARDWARE-VERIFIED`, and
flipping that is a deliberate program-wide act, not a side effect of a good
afternoon's measurements.
