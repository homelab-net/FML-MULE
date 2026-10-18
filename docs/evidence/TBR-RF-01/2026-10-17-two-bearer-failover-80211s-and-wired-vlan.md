# Failover and best-path selection between two batman-adv bearers

**Tier: deferred (real-hardware bench result; formal `HARDWARE-VERIFIED` held).**
Held for the reasons `2026-10-11-two-node-80211s-batman-real-radio.md` gives,
unchanged. It is not `SIMULATED`: the 802.11s bearer was real RF and the
routing ran on the bench nodes. It is **node-local**: no independent instrument
observed either bearer.

**Trade:** `TBR-RF-01`, and CONOPS section 39.
**Date:** 2026-10-17, 14:44 to 15:06 MDT. **Nodes:** `pi-mule-1` and
`pi-mule-2`, Raspberry Pi 4B, `6.18.50+rpt-rpi-v8 aarch64`, `batman-adv
2025.4` (`batctl debian-2025.0-2`), `BATMAN_IV` (`FML-ADR-053`),
`hop_penalty 30`, `bridge_loop_avoidance` disabled.
**Bearer 1:** the 802.11s mesh point `wlan1` from the 2026-10-11 artifact,
5745 MHz, 40 MHz, VHT-MCS 9 at 400 Mbit/s, signal about -14 dBm.
**Bearer 2:** `eth0.3942`, a VLAN subinterface of each node's `eth0`, 1000
Mbit/s full duplex, through the operator's home LAN switch, added to the same
`bat0` as a second hard interface. **Procedure:**
`test/bench/bearer-failover-real.sh up|measure|monitor|down`.
**Taken by:** Cameron Zobrist, on the mule bench, with Claude, with the
operator's consent to put tagged batman-adv frames on the home LAN.

## Why this exists

The 2026-10-11 artifact recorded what CONOPS section 39 still lacked:
*"movement, failover, and best-path selection. All three need an alternate path,
and two nodes have exactly one."* A third mesh-capable node is not on the bench.
A second bearer between the same two nodes is: it gives batman-adv two paths to
choose between, without a third radio.

It also bears on a value the repository leaves open.
`os/config/batman-adv.conf.template` sets `orig_interval=TBD` and says why: the
question that value decides is *"convergence after a TOPOLOGY CHANGE on a lossy
link, which veth cannot pose. TBR-RF-01 owns that."* This poses a topology
change on real links at two values of it.

## What this does not establish

Read this first, because each limit is large.

- **The second bearer is wired.** It stands in for a second radio so that the
  routing can be observed. Nothing here describes a second radio's physics, and
  the CONOPS sub-GHz bearers are not in it.
- **Two nodes.** This is failover between two interfaces to the same
  neighbour, not rerouting around a lost relay. Multi-hop failover and
  **movement** still need a third node.
- **Failure is emulated.** A silent failure is `tc` dropping everything in both
  directions on one node while the interface stays up. A real fade degrades
  first; this does not.
- **Small samples.** Two silent-failure runs at the default `orig_interval`, one
  administrative failure, one degradation, one control, and **one** run at 250
  ms. Ranges, not distributions.
- **Under-voltage throughout.** Both throttle states, `0x50005` and `0x50000`,
  were sampled in every case. The times below are set by originator messages at
  second scale, but a throttled CPU can add delay this run did not separate.
- **The probe failed partway.** See the instrument section. No figure below
  rests on ping alone.

## Results

`orig_interval` 1000 ms, the module default, unless stated. "Outage" is the
longest gap between ping replies across the fault. "Left" and "back" are when
each node's selected outgoing interface toward the peer changed, from a 100 ms
poll on each node. Probe spacing before every fault was 24 ms median, 28 ms
p90, so outages resolve to roughly 25 ms.

| Case | Outage | Near node left | Far node left | Agrees? |
| --- | --- | --- | --- | --- |
| Wired bearer silently cut, run 1 | **4.98 s** | 4.88 s | 4.45 s | yes |
| Wired bearer silently cut, run 2 | **6.01 s** | 6.01 s | 4.28 s | yes |
| Wired bearer taken down on the near node | **4.12 s** | 0.97 s | 4.14 s | yes |
| Wired bearer silently cut, `orig_interval` 250 ms | **1.22 s** | already on wlan1 | 1.30 s | yes |
| Wi-Fi bearer silently cut while wired carried traffic | **none**, 35 ms longest gap | no change | no change | yes |
| 30% loss on the wired bearer, near egress | no gap over 0.93 s | 7.47 s | 29.9 s, and returned at 37.1 s | see below |

**Agrees** means the ping outage matches the later of the two nodes' route
changes to within the probe and poll resolution. A round trip needs both
directions, so it recovers only when the slower node has moved. That is the
check that each outage is a routing event and not the probe stalling.

### Failover works, in seconds, and scales with the originator interval

At the default interval a silently failed bearer cost **4.1 to 6.0 seconds** of
round trip, then traffic moved to the remaining bearer with no operator action.
At 250 ms it cost **1.2 seconds**. That is one run, so the scaling is suggested,
not established, but it is the direction `orig_interval` predicts: batman-adv
notices silence by counting missed originator messages.

### The far end sees an orderly shutdown as a silent failure

Taking the wired interface down on one node moved that node off it in under a
second, because the kernel tells batman-adv at once. The other node was told
nothing, and took 4.1 seconds, the same as a silent cut. So an orderly local
action protects one direction only, and the round trip pays the silent-failure
price.

### Losing the unused bearer costs nothing

Cutting the Wi-Fi bearer while the wired one carried the traffic produced no
outage and no route change on either node. That is the control: the outages
above belong to losing the path in use, not to disturbing the mesh.

### Recovery of the better path is slow, and "better" means loss, not capacity

CONOPS section 39 lists *"recovery of better paths"*. After each fault cleared,
the wired bearer was re-adopted, but slowly:

| Case | Near node back | Far node back |
| --- | --- | --- |
| Silent cut, run 1 | 60.0 s | 44.3 s |
| Silent cut, run 2 | 30.4 s | 55.2 s |
| Taken down | 50.2 s | 33.1 s |
| Silent cut, 250 ms | 13.2 s | 9.2 s |

Failover took about five seconds and failback took 30 to 60. This is the same
asymmetry the 2026-10-11 degradation run recorded, onset faster than recovery,
now seen on a path change: a link's quality is rebuilt over a window of
originator messages.

**Which bearer is "better" was decided by loss.** Both bearers reached TQ 255.
After start-up the wired bearer was selected about 34 seconds into the steady
case, and kept by incumbency. `FML-ADR-053` records that `BATMAN_IV` *"is
derived from packet loss rather than throughput"* and may prefer a lossless
slow path over a lossy fast one. Nothing here measured that case, because both
bearers were lossless and both fast. The run is consistent with the ADR and
adds nothing to its revisit criteria.

### Degradation: the near node left the lossy path, the far node went back

With 30% loss on the near node's wired egress, the near node moved to Wi-Fi
after 7.5 seconds, as link quality decayed. About 3% of probes were lost over
the case, concentrated before that move, and no gap exceeded 0.93 s. The far
node left at 29.9 seconds and **returned to the lossy bearer at 37.1 seconds**,
staying there until the loss was removed. The loss was applied in one
direction only, near to far, so the far node's own direction on that bearer was
clean. That may be the right choice for its direction. It is recorded as
observed, not judged.

### A faster interval flaps between equal bearers

At 250 ms the near node changed bearer **17 times in 180 seconds**, three of
them before any fault, against one or two per case at 1000 ms. With both
bearers at TQ 254 to 255, small jitter moves the choice back and forth. The
three changes before the fault cost no measurable outage (longest gap 32 ms).
The changes after the fault fell in a window the probe no longer covered, so
their cost is **unknown**.

So `orig_interval` trades the two things CONOPS 39 asks for against each other:
faster failover and failback, and less stable selection between near-equal
paths. More originator messages are also more emissions, which
`TBR-EMCON-01` classes. This artifact proposes no value. The template stays
`TBD`.

## The instrument failed, and how that was handled

The ping, `-i 0.02`, stopped sending partway through six of the seven cases
while the process stayed alive. Its log ends at +6.8 s in the steady case and
between +30.8 s and +72.2 s in the others; only the control case ran to the end.
The same stall reproduced afterwards on `pi-mule-2` alone, with no fault
applied: 148, 309 and 517 probes in 12 to 20 seconds where 600 to 1000 were
due, at no consistent point. It is a property of this probe on this throttled
node (iputils 20240905), not of the mesh. The route polls ran to the end in
every case.

What that changes:

- **Every outage above is cross-checked** against the route polls, and every one
  agrees. A stall inside a fault window would show as a gap with no route change
  behind it; none did.
- **Failback costs are unknown** except in the control case and the pre-fault
  part of the 250 ms case. The route polls show when traffic moved back, not
  whether moving back lost anything.
- **Loss counts are not comparable** between cases, because the number of
  probes sent varies with the stall. Only the 30% case's loss is quoted, and
  only as an approximate share.

`test/bench/bearer-failover-real.sh` records the defect in its header. A
sequence-numbered probe, `udpflow.py`, should replace ping before the next run.

## What CONOPS section 39 now has

| Section 39 asks the network to adapt to | State |
| --- | --- |
| node loss | 2026-10-11: detected after about 165 s at the routing layer |
| link degradation | 2026-10-11, and here: the near node left a 30%-loss path in 7.5 s |
| changing neighbours | not posed |
| gateway availability | not posed |
| recovery of better paths | **here**: 30 to 60 s at 1000 ms, 9 to 13 s at 250 ms, with "better" meaning loss |
| movement | not posed; needs a third node |
| *"best-path selection and failover"* | **here**: failover 4.1 to 6.0 s at 1000 ms and 1.2 s at 250 ms, between two bearers to one neighbour, with no manual route selection |

*"Normal users shall not be required to select routes manually"* held
throughout: nothing was selected by hand.

## Clean-up

The second bearer was removed from both nodes at the end of the run. Both
`bat0` interfaces returned to `wlan1` only, `orig_interval` returned to 1000,
and both `eth0` interfaces and default routes were as before. The 802.11s
bearer was left running, as the 2026-10-11 artifact left it.
