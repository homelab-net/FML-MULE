# Two-node 802.11s + batman-adv on real radios

**Tier: deferred (real-hardware bench result; formal `HARDWARE-VERIFIED` held).**
Every earlier `TBR-RF-01` *result* is `SIMULATED`; this one met a radio. One
earlier artifact there is neither a simulation nor a result --
`2026-10-10-awus036acm-one-hop-mesh-card.md`, a bench card for this same adapter
that had not been run; see **Relation to the one-hop card** below. The
program nonetheless does not stamp it: `README.md` and `test/README.md` both
still state that nothing in the repository is `HARDWARE-VERIFIED`, and flipping
that is a deliberate program-wide posture change which must reconcile those
surfaces, `STATUS.md`, `AGENTS.md` and the prebuilt public `site/` at once. That
reasoning is not new here -- it is the posture
`docs/evidence/TBR-NET-02/2026-09-27-one-lora-hop-to-a-partner-node.md` records
for the earlier real-hardware result being held the same way. This is **not**
`SIMULATED`: that word says nothing about physical behaviour and this was real
RF. It is also **node-local**: no independent receiver observed the air.

**Date:** 2026-10-11. **Nodes:** `pi-mule-1` and `pi-mule-2`, Raspberry Pi,
`6.18.50+rpt-rpi-v8 aarch64`, `batman-adv 2025.4` (`batctl debian-2025.0-2`).
**Radios:** Alfa AWUS036ACM / MediaTek `MT7612U` (USB `0e8d:7612`), driver
`mt76x2u`, two burned-in addresses under the Alfa OUI `00:c0:ca:…` differing in
the last octet, `…:67` on node 1 and `…:68` on node 2; truncated because
`SECURITY.md` forbids publishing what identifiers equipment carries and
`tools/validate-identifiers.py` enforces it. Selected by driver, not by name. **Configuration:** 802.11s mesh id `fml-bench-mesh` on 5745 MHz
(channel 149, UNII-3, non-DFS; regdomain `US: DFS-FCC`), 20 MHz, **no HT**;
`batman-adv` `BATMAN_IV` (`FML-ADR-053`), `bridge_loop_avoidance 0`
(`FML-ADR-056`), `multicast_mode 0`, hard-interface MTU 1560, `bat0` on
`10.42.0.1/24` and `10.42.0.2/24`. **Procedure:**
`test/bench/80211s-mesh-real.sh up|gate|status` and
`test/bench/mesh-traffic-real.sh recv|send` phases a, b, c.
**Taken by:** Cameron Zobrist.

## What this demonstrates

`docs/bench-hardware-bringup.md` Step 2 gates all multi-node work on a single
packet crossing real radios: "a failure here is PHY/association/config, never
routing." That gate is now passed, and the contention half of
`test/bench/mesh-traffic.sh` has been run over the real link.

Two deliberate deviations from the hwsim bench, both recorded rather than
silent. Channel is 5745 MHz instead of 2412/2437, because 2.4 GHz here already
carries `Zobrist-2.4`, the bench mule's `feralmulenet` EUD AP on channel 11, and
each node's own `wlan0` client: a 2.4 GHz run would have measured that
interference and put a live AP at risk. Addressing is `10.42.0.0/24` instead of
the bench's `10.41.0.0/16`, because `10.41.0.1/24` is already that EUD AP's
subnet. `TBR-NET-01` still owns the field prefix; this is a bench address.

### Relation to the one-hop card

`2026-10-10-awus036acm-one-hop-mesh-card.md` is a bench card for this same
adapter, written the day before this run. **This is not that card executed.** The
card specifies the least occupied of 2412, 2437 and 2462 MHz at `HT20`; this run
used 5745 MHz for the reason above. Different band, different width, so the two
are independent runs on shared hardware and **the card remains unrun.**

Two of the card's predictions, which it derived from kernel source rather than
from hardware, hold here: the adapter binds the in-tree `mt76x2u`, and the
driver offers at most two interfaces on one channel (`mt76x02u_if_comb`).

A third one bites. The card passes `HT20` on the mesh join and calls it "not
optional", citing `iw`'s `parse_freqchan` -- "If the mode/channel width is not
given the NOHT is assumed" -- and warns that omitting it runs "a different
experiment, with no error". `test/bench/80211s-mesh-real.sh` omitted the width
and got exactly that: 20 MHz, no HT, a 54 MBit/s legacy rate. The card named the
trap before this bench fell into it. See **The 54 MBit/s cap was this bench's own
doing** below for what the width is worth once set.

## The gate

| Check | Result |
| --- | --- |
| Mesh peer | `mesh plink: ESTAB`, signal −14 dBm / −12 dBm |
| batman-adv hard interface | `wlan1` on `bat0`, both nodes |
| Originators | 1 each direction, direct nexthop |
| One ICMP echo over `bat0` | **3.586 ms, 0% loss** |

The first reply arrived in milliseconds, not tens of seconds. That is the check
`.github/workflows/mesh-probe.yml` motivates (31.5 s against 2.150 s on
`bridge_loop_avoidance` alone), so it confirms `FML-ADR-056`'s setting actually
took on hardware rather than being merely written in a template.

## The link, as it actually came up

The mesh negotiated **20 MHz with no HT**, giving a 54.0 MBit/s legacy OFDM rate
in both directions. `expected throughput` read 13.91 Mbps at idle and 27.6 to
29.6 Mbps once traffic had trained rate selection. Over the run the sender logged
1598 tx retries against 12847 tx packets with **0 tx failed**; the receiver
logged 1148 `rx drop misc`.

This is worth stating plainly because `TBR-RF-01` is titled *high-rate* mesh
implementation and `FML-ADR-025` prefers the high-rate bearer as an additional
`batman-adv` hard interface. On this chipset, driver and configuration, the
high-rate plane came up at a 54 MBit/s PHY rate. Whether that is an 802.11s
limitation in `mt76`, a missing HT/VHT capability on the mesh path, or simply
not yet configured for is **not established here** and is the obvious next
question for this trade.

## Voice against bulk on one bearer

Imposed bottleneck 5 Mbit (`tbf`/`htb`), voice profile ~160 B every 20 ms for
10 s, bulk saturating, exactly as `mesh-traffic.sh` sets them.

| Phase | Voice loss | Voice jitter | RTT avg, unmarked ICMP |
| --- | --- | --- | --- |
| a. voice alone | 0.0 % | **0.172 ms** | 1.062 ms |
| b. + bulk, one FIFO, no QoS | 0.0 % | **32.517 ms** | 155.134 ms |
| c. + bulk, voice DSCP EF prioritised | 0.0 % | **0.174 ms** | 156.817 ms |

Three things this says.

**`FML-ADR-021`'s "routing starves first" is visible on real RF.** One shared
FIFO raised voice jitter 189-fold, from 0.172 ms to 32.517 ms.

**Loss would have missed it entirely.** Loss was 0.0 % in all three phases: at
5 Mbit the queue delays rather than drops, so the whole cost of contention
appeared as jitter. A QoS result graded on loss alone would have read as "no
degradation" through phase b.

**The protected class restores voice, and the two numbers prove it separately.**
In phase c, EF-marked voice jitter returns to baseline (0.174 ms against
0.172 ms) while the unmarked ICMP probe stays at ~157 ms, because ICMP is not
EF-marked and deliberately rides the deprioritised default class. The divergence
is the evidence: the protected class is doing the work, not the bottleneck
quietly disappearing. **The qdisc remains illustrative, not a decision** --
`TBR-RF-01` owns the QoS mechanism, and 5 Mbit is imposed, not this radio's
measured capacity.

Incidentally established while diagnosing phase c: DSCP survives this path
unmodified. Markings 0, 8, 26, 46 and 56 were sent in sequence with no qdisc and
all 493 packets arrived with their TOS byte intact (0x00, 0x20, 0x68, 0xb8,
0xe0). EF is not being stripped or reclassified by 802.11s or `batman-adv` here.

## What must not be read off this

**One-way latency is withheld, and the raw JSON shows why.** `udpflow.py` says
the figure is only meaningful with both endpoints in namespaces on one clock. In
phase a it reported `latency_ms_avg` 10.775 ms while measured RTT averaged
1.062 ms -- a one-way delay cannot exceed half its round trip, so the number is
clock offset, and it drifted between runs (7.826 ms, then 10.775 ms). RTT from
`ping -D` is substituted throughout. The suppressed field is still in the raw
JSON under `/tmp/fml-mesh-real.voice.{a,b,c}.json`; it is an artefact.

**Phase c's RTT is not the voice flow's latency.** It measures the unprotected
class, by design.

**Two orchestration faults were hit and are now guarded, not tuned away.** A
receiver idle-timeout that expires before the sender's SSH, sudo and six `tc`
commands complete reports zero packets on a provably working path; and a
receiver that outlives its phase either dies on a silent `EADDRINUSE` -- the
bench's `udpflow.py` sets no `SO_REUSEADDR` -- or absorbs the following phase and
reports 1475 packets against 492 expected, a loss of −199.8 %. Both now refuse
to print a figure at all. Every number in the tables above comes from a run
where the receiver was confirmed exited before the next phase began.

**No independent witness.** Both the gate and the contention figures are read on
the nodes themselves. The bench mule cannot observe this mesh: its Alfa is an
AWUS036ACH whose `rtl8812au` driver advertises no monitor mode, and its RTL2838
SDR stops near 1.77 GHz with ~2.4 MHz of bandwidth against a 5 GHz, 20 MHz
channel. A third `MT7612U`, which does advertise `monitor`, would supply one.

**One hop.** Two nodes cannot form the line topology Step 2's multi-hop item and
`mesh-traffic.sh latency` both require, so nothing here speaks to multi-hop
latency or relay behaviour. That needs a third mesh-capable radio.

**This advances `TBR-RF-01`. It does not close it.** Per
`docs/bench-hardware-bringup.md`, the QoS mechanism stays the trade's to choose,
and `TBR-LINUX-01` -- the sub-GHz HaLow driver question this program calls the
dominant uncertainty -- is untouched by this hardware.

## Addendum, same day: cold-boot restore, measured goodput, TAK traffic

Both nodes lost power at 17:25 and rebooted. Nothing persistent had to be
undone: `wlan1` came back `managed`, `batman-adv` was unloaded, and
NetworkManager was managing the radio again, which is what
`test/bench/80211s-mesh-real.sh down` aims at and what the template means by an
input to configuration generation rather than a file edited on a node. Bringing
the mesh back was the two `up` calls and the gate, from a cold boot.

One number from that restore is worth keeping. The gate's first packet took
**1277 ms**, with the originator table still empty when the gate read it. That
is batman-adv route discovery on a cold mesh, not the `bridge_loop_avoidance`
pathology, which `mesh-probe.yml` records at tens of seconds. The distinction
matters because both look like "the first packet was slow".

### Measured goodput, against the driver's own estimate

A 64 MiB payload over HTTP on `bat0`, one hop:

| Layer | Figure |
| --- | --- |
| PHY rate, both directions (no HT) | 54.0 MBit/s |
| `iw` `expected throughput` | 29.571 Mbps |
| **Measured TCP goodput** | **19.6 Mbps** (67108864 B in 27.344 s) |

`md5` matched end to end, so this is goodput and not a partial transfer. 5293 tx
retries, 0 tx failed.

This is the first measured throughput in the repository; everything before it
was a driver estimate. **The estimate overstates achieved goodput by about
1.5x.** That is directly relevant to `FML-ADR-053`, which keeps BATMAN-IV partly
because BATMAN-V needs a *usable* throughput estimate from the driver and
whether one exists is `UNVERIFIED`. One hop on one chipset does not settle that
question, and the gap here is not evidence of the sub-GHz driver's behaviour,
which is what `TBR-LINUX-01` actually owns. It is one datapoint that the
estimate and the achievable rate are not the same number.

### TAK CoT and GeoChat across the mesh

Run with `test/bench/tak-eud-ip.py`, synthetic EUDs over PyTAK
(`FML-ADR-033`), into a plain CoT sink rather than OpenTAKServer, so that this
measures the bearer and not a server's ingest.

On a quiet mesh a GeoChat arrived with `senderCallsign` and the chatroom intact
and the same `messageId` the sender queued, and a PLI arrived as `a-f-G-U-C`.
Under the contention of the table above -- the 5 Mbit `tbf` bottleneck and a
saturating bulk flow, with RTT at 165 ms against 0.905 ms quiet -- **all three
of three GeoChats still arrived**, each `messageId` matching byte for byte. TAK
chat survives the conditions that cost voice 189x its jitter.

The two identities `FML-ADR-070` rests on ride here as `contact/@callsign` and
the chatroom, so an IP-plane GeoChat and a Meshtastic `TAKPacket` carry the same
pair; the Meshtastic half is `TBR-NET-02`'s and is not shown here.

**What this addendum does not establish.** No server: no ingest, no persistence,
no enrollment, and therefore nothing about a real ATAK or iTAK client, whose UI
cannot be driven from a bench script at all. The bulk *receiver* failed to start
in the contention run through an orchestration fault on the driving host, so
there are no receive-side bulk statistics; the contention is evidenced by the RTT
and by the bulk sender having run. And the per-message wall time of about 3.1 s
is PyTAK process start-up plus a settle delay, **not** transit, and is not a
latency figure.

## Addendum 2: the link was not optimised, and a gate that could not fail

Two corrections to the figures above, one of configuration and one of method.

### The 54 MBit/s cap was this bench's own doing

`iw ... mesh join` takes `NOHT|HT20|HT40+|HT40-|80MHz` and **defaults to NOHT
when the width is omitted**. `test/bench/80211s-mesh-real.sh` omitted it,
inheriting the omission from `80211s-mesh.sh`, where it does not matter because
`mac80211_hwsim` has no PHY. So every figure above the addendum line was taken
on a link pinned to the 802.11a legacy ceiling, on a part that advertises
HT20/HT40, MCS 0-15 and VHT80. The regdomain permits 40 and 80 MHz on
149/153/157/161/165 with no `NO-HT40` or `NO-80MHZ` flag.

Re-measured, 64 MiB over HTTP on `bat0`, one hop, `md5` verified each time:

| Width | PHY rate | `iw` estimate | Measured goodput | vs NOHT |
| --- | --- | --- | --- | --- |
| NOHT | 54.0 MBit/s | 29.6 Mbps | 19.6 Mbps | 1.0x |
| HT40+ (40 MHz) | 270.0 MBit/s, VHT-MCS 6, NSS 2 | 143.5 Mbps | **89.5 Mbps** | 4.6x |
| 80 MHz | 780.0 MBit/s, VHT-MCS 8, NSS 2 | 208.9 Mbps | **114.7 Mbps** | 5.9x |

So the "high-rate bearer came up at 54 MBit/s" finding above was a
**configuration defect, not a chipset or 802.11s limitation**, and the sentence
in the body questioning whether `mt76` could do better is answered: it can, by
about six times.

Two things follow that the raw ratio hides. **80 MHz buys 28% more goodput than
HT40+ for twice the channel occupancy**, which on a field MANET trades against
spectrum reuse and interference susceptibility rather than being free;
`TBR-RF-01` owns that choice and this bench now defaults to HT40+ as the
conservative improvement over an accidental NOHT, which is not the same as the
program selecting a width. And the **driver's estimate overstates achieved
goodput at every width** -- 1.5x, 1.6x, 1.8x, worsening as the channel widens --
which is three datapoints on `FML-ADR-053`'s open question of whether a *usable*
throughput estimate exists, all pointing the same way. It remains silent about
the sub-GHz driver that `TBR-LINUX-01` actually owns.

### The gate could not fail

The one-packet gate was written as

    if ping -c 1 -W 5 -I bat0 "$peer" | sed 's/^/   /'; then

whose exit status is `sed`'s, not `ping`'s. `sed` always succeeds, so **the gate
printed `GATE PASSED` over `100% packet loss`** when a transient rejoin was
caught mid-route-discovery. Every gate result recorded above did show
`1 received, 0% packet loss` in its own output, so those passes were real and
the figures stand; what was wrong is that the check was incapable of catching a
failure, and an assertion that cannot fail is not evidence.

Now fixed: the output is captured, `ping`'s status is tested, and the receive
count is asserted as well, because `ping` can exit 0 on an error reply.
Verified both ways on hardware -- it passes against the live peer at 2.52 ms and
exits non-zero against an address nothing answers.

## Addendum 3: five synthetic EUDs behind three hosts

`test/bench/tak-eud-ip.py` gained a `--transport raw` that needs only the
standard library, so an EUD can be simulated on a host where installing PyTAK is
not wanted. The bench mule carries the COCON stack and a test EUD there should
not add packages to it. PyTAK stays the default and the preferred client
(`FML-ADR-033`); raw loses its connection management and keepalive, not the
encoding.

Five EUDs, three hosts, all into one sink, with the source address separating
the paths rather than conflating them:

| Source | Path | EUDs |
| --- | --- | --- |
| `10.42.0.1` | 802.11s/batman-adv mesh, PyTAK | `P1-ALPHA`, `P1-BRAVO` |
| `10.42.0.2` | local on the sink host, raw | `P2-CHARLIE` |
| `192.168.8.170` | **LAN, not the mesh**, raw | `BM-DELTA`, `BM-ECHO` |

All five GeoChats arrived with `senderCallsign`, chatroom and `messageId`
matching what was sent: `5 GeoChat, 0 PLI, 2 pytak keepalive, 0 unparseable`.

**The bench mule is not a mesh node and its EUDs did not cross the mesh.** It
has no mesh-capable radio -- its `rtl8812au` offers managed and AP only, and its
`phy0` does not list `mesh point` -- so its traffic reached the sink over the
LAN. That is a legitimate topology for a LAN or WAN-attached node, and it is
recorded as such here precisely so the row cannot later be read as a third mesh
node.

A defect worth recording rather than quietly fixing: the raw transport did not
work on the one host chosen because PyTAK is absent there, since the helper that
builds CoT timestamps called `pytak.cot_time()` unconditionally. A "standard
library only" path that imports the thing it is avoiding is not one. It now uses
`datetime`, and the failure surfaced only by running it on the constrained host
rather than on the two that had PyTAK installed.

## Addendum 4: CONOPS 41 WAN independence, and CONOPS 39 adaptive routing

Both tested on the same two-node link, HT40+, same provenance as above.

### Section 41, WAN independence

`[SHALL]` Loss of WAN shall not remove local EUD access, the local mesh, peer
ATAK, local S0/S1 services, or LoRa.

Default routes were removed from both nodes -- **0 routes remaining**, `1.1.1.1`
unreachable -- with a detached restorer armed so a dropped session could not
leave a node without a route. In that state:

* the **local mesh** held: `bat0` up, peer `ESTAB`, 3/3 ICMP, 0% loss;
* **peer ATAK** held: a GeoChat and a PLI both arrived at the far node with
  `senderCallsign`, chatroom and `messageId` intact.

Routes restored afterwards, internet confirmed back, route counts matching the
pre-test baseline exactly.

**Two of five rows only, and the test was weaker than full isolation.** DNS
still resolved throughout, because the LAN resolver is on-link and needs no
default route. So this measured **loss of the off-site IP path**, not isolation.
`local EUD access` had no EUD attached and `local S0/S1 services` were not
running, so neither was observed. Taking `eth0` down would have produced a
stronger test and would also have severed the SSH path being used to observe it,
which is why it was not done.

### Section 39, adaptive routing

`[SHALL]` The network shall automatically adapt to movement, node loss,
changing neighbours, link degradation, gateway availability, and recovery of
better paths, without users selecting routes.

**Link degradation: it adapts.** With 30% loss applied by `tc netem` on the
*hard* interface -- so batman-adv's own OGMs are lost, not just payload --
TQ fell monotonically **255 → 241 → 222 → 201 → 186** over 48 s, and on removal
payload loss returned to 0% immediately while TQ began climbing back. Onset is
faster than recovery, which is the OGM averaging window. This is **emulated
loss, not RF degradation**, and is labelled as such.

**Power control cannot degrade this link, and that is a measurement.** Dropping
one node from 20 dBm to the driver floor of 3 dBm moved the *far* node's
received signal from **-13 dBm to -30 dBm**, exactly the 17 dB applied, and the
link did not care: still VHT-MCS 9, TQ 251/255, 0% loss. So the bench link
carries **at least 17 dB of margin at this separation**, and section 39's
degradation case cannot be posed with transmit power here. Emulated loss or real
separation is required. Useful to know before anyone plans a range test.

**Node loss is slow, in two different ways.** After one node's mesh was fully
torn down:

| Layer | Time to forget the dead node |
| --- | --- |
| batman-adv originator table | **~165 s** (purged between t+161 s and t+171 s) |
| 802.11s peer entry (`station dump`) | **still present at t+302 s** |

The second is explained by `mesh_plink_timeout`, which reads **1800 s**. A
thirty-minute stale peer link is hard to reconcile with a requirement to adapt
to node loss and changing neighbours. The first is consistent with a fixed
purge timeout rather than a multiple of `orig_interval` (1000 ms here), so
**faster forgetting is not simply an `orig_interval` tuning exercise** -- that
value governs convergence and best-path adoption instead. Remediation for both
is in `docs/bench-remediation-plan-2026-10-11.md` Phase 0.

**What section 39 still has no evidence for:** movement, failover, and
best-path selection. All three need an alternate path, and two nodes have
exactly one. Nothing here should be read as showing the network reroutes,
because there was nowhere to reroute to.

### Three measurement faults in this addendum's own runs

Recorded because each produced a plausible-looking wrong answer.

`iw dev <dev> set txpower` is a **silent no-op** on this driver -- it reports
success and the power does not change. The first degradation run therefore
changed nothing, and would have been written up as "TQ 239 unchanged, no
degradation observed" when the independent variable had never moved. The
phy-level form, `iw phy <phy> set txpower`, works.

The first run also measured **at the wrong end**: `station dump` reports the
signal *received from* the peer, which depends on the peer's transmit power, so
reducing the local node's power is invisible locally. The far node is the
observation point.

A loss-reporting `grep` matched fractional percentages wrongly, rendering
"66.67% packet loss" as "6667%". The packet-loss figures in the degradation
sweep are therefore reported as a band, 33% to 67%, rather than as the garbled
exact values.

## Addendum 5: posing the `orig_interval` question, and failing to answer it

`os/config/batman-adv.conf.template` leaves `orig_interval` `TBD` and says why:

> Still TBD, because the question this value actually decides is convergence
> after a TOPOLOGY CHANGE on a lossy link, which veth cannot pose. TBR-RF-01
> owns that.

The bench can now pose it. One radio leaves the mesh and rejoins while `tc
netem` makes the link lossy, and the clock runs from interface-up-and-joined to
the first packet crossing. Procedure: `test/bench/80211s-mesh-real.sh` plus a
convergence timer on one host, so that elapsed time comes from a single clock.

### What was measured

| Run | Link | `orig_interval` | Convergence |
| --- | --- | --- | --- |
| A | clean | 1000 ms | 4049 ms |
| B | 20% egress loss | 1000 ms | 9170 ms |
| C | 20% egress loss | 500 ms | 29322 ms |
| D | 20% egress loss | 250 ms | 11269 ms |

Read as a sweep, that says 500 ms is catastrophic and 250 ms is fine, which is
not a believable shape. So the same condition was repeated.

| Repeats, 20% loss, `orig_interval` 1000 ms |
| --- |
| 9170 ms, 20366 ms, 7139 ms, 39539 ms |

**A 5.5x spread inside one condition**, against between-condition differences of
roughly 3x. The variance swamps the signal.

### The finding, which is a negative one

**This experiment cannot distinguish `orig_interval` values, and no
recommendation should be drawn from it.** Had runs A through D been reported as
a sweep -- which is exactly what a single pass per value invites -- the program
would have received "500 ms is three times worse than 1000 ms" as an ADR input,
from noise. `orig_interval` remains `TBD`, and this addendum is the reason to
keep it there rather than evidence for a value.

What has changed is that the question is now **askable on hardware**, which it
was not when the template was written. That is the part worth keeping.

### What a valid experiment needs

Recorded so the next attempt does not repeat this one:

* **Many repeats per condition, order randomised.** Four samples at one setting
  already span 7 to 40 seconds; a dozen per condition is the floor, and
  conditions must be interleaved rather than run in blocks, because anything
  drifting over the session otherwise lands entirely on one setting.
* **A convergence criterion that is not first-ping-success.** `ping -c1 -W1`
  quantises the result into one-second steps -- the attempt counts are simply
  elapsed seconds -- and it conflates neighbour resolution with routing
  convergence. Poll the originator table, or timestamp the first OGM accepted
  from the returning node.
* **Loss applied in both directions.** Here `netem` sat on one node's egress
  only, so the link was asymmetrically lossy and OGMs were impaired in one
  direction more than the other.
* **Rate adaptation controlled or recorded.** The link moved between MCS rates
  during these runs, which changes airtime per OGM independently of the
  interval under test.
* **A stated topology-change model.** "Radio leaves and rejoins" is one event;
  a node moving out of range and a node losing power converge differently, and
  section 39 names movement separately from node loss.

### Why this is reported rather than quietly re-run

The template's whole posture on this value is that an unmeasurable number should
stay `TBD` instead of acquiring a plausible one. Recording four runs that look
like a sweep and are actually noise is the specific way a deferred decision
gets closed by accident.

## Addendum 6: the plink timeout, and why L2 recovery is not IP recovery

Phase 0.1 of `docs/bench-remediation-plan-2026-10-11.md`.

### `mesh_plink_timeout`

Addendum 4 recorded that a node whose mesh was fully torn down still appeared as
an 802.11s peer **302 seconds later**, because the default
`mesh_plink_timeout` is **1800 s**.

Measured against a candidate value, same teardown, same observation point:

| `mesh_plink_timeout` | Peer entry cleared |
| --- | --- |
| 1800 s (default) | still present at t+302 s |
| 60 s | **t+111 s** |

Note that 60 s does not mean 60 s: the plink state machine has its own holding
and retry timers on top of the inactivity timeout, so the observed figure is
roughly double the value set. Anyone tuning this should measure rather than
assume the number means what it says.

**Left at the default.** 1800 s is the mac80211 default, not an accident like
the omitted channel width was, so changing it is a program decision and
`TBR-RF-01` owns it. This is an input to that decision, not the decision.

What this measurement cannot tell you is the cost of an aggressive timeout:
whether a short inactivity window churns peers on a marginal link, which is the
opposite failure and the reason the default is generous. Posing that needs a
genuinely marginal link, and addendum 4 established that this bench has at least
17 dB of margin at its current separation.

### The finding that matters more: L2 recovery is not IP recovery

After the teardown-and-rejoin cycles above, the mesh came back **healthy by
every mesh-layer measure** -- `mesh plink: ESTAB`, one originator at TQ 236,
nexthop direct, hard interface active -- while IP over `bat0` was **100% packet
loss**.

The cause: **`bat0` receives a new random MAC address every time it is
created.** Across repeated rejoin cycles the peer's neighbour cache still held
the previous one:

    node1: 10.42.0.2 lladdr 1a:46:ef:99:e1:4d REACHABLE
    node2: bat0 MAC is de:4e:7c:8e:db:ac

The entry was stale and still marked `REACHABLE`, so nothing retried it.
`ip neigh flush dev bat0` restored connectivity immediately: 0% loss, 1.280 ms
average.

Three consequences worth carrying forward.

**Section 39 is affected.** A requirement to adapt to node loss and recover is
not met by the routing layer reconverging if the IP path stays dead behind a
stale neighbour entry. Recovery has to be judged end to end, not from
`batctl originators`.

**This is an addressing concern, not a routing one.** The remediation is a
**stable, deterministic `bat0` MAC** derived from node identity rather than a
fresh random one per creation. That belongs with `TBR-NET-01`, the addressing
plan, and it would also make packet captures and translation tables comparable
across restarts, which they currently are not.

**It is partly an artefact of bench churn, and partly not.** A field node does
not recreate `bat0` a dozen times an hour. But it does reboot, and a reboot
produces exactly the same new-MAC-with-stale-peer-cache condition, with the
stale side being whichever node stayed up.

### The gate fix earned itself here

This failure was caught by the one-packet gate returning a non-zero status.
The version of that gate shipped earlier in the day tested `sed`'s exit status
rather than `ping`'s and would have printed `GATE PASSED` over 100% packet loss,
and the mesh-layer indicators all looked correct, so nothing else in the
procedure would have objected. See addendum 2.

## Addendum 7: CONOPS 42 gateway, and the stale-ARP cause found and fixed

Phase 1 item 1 and a resolution for the defect addendum 6 reported.

### Section 42, local WAN gateway: passes

`[SHALL]` Any standard MULE shall be technically capable of assuming an
authorized local WAN-gateway role.

Node 1 kept its uplink, enabled forwarding, masqueraded the mesh subnet out
`eth0`, and set `batctl gw_mode server`. Node 2 removed **all** of its own
default routes, set `gw_mode client`, and routed through the mesh.

| Check | Result |
| --- | --- |
| Node 2's own uplink | **0** default routes |
| batman gateway discovery | node 1 selected: TQ 251, announced 10.0/2.0 MBit |
| Route to off-site | `1.1.1.1 via 10.42.0.1 dev bat0` |
| ICMP to 1.1.1.1 / 8.8.8.8 | 0% loss both |
| DNS | resolves |
| HTTP | **301 in 0.222 s** |
| Gateway NAT counters | 3 masqueraded flows from `10.42.0.0/24` out `eth0`; FORWARD 12 packets `bat0→eth0`, 10 back |

The NAT and FORWARD counters are the part that matters: they show the traffic
actually traversed node 1's forwarding path from the mesh subnet, rather than the
client finding some other route. Both nodes restored afterwards; node 1 back to
`ip_forward=0`, no NAT rules, `gw_mode off`.

**What this does not show.** Section 42 says *authorized*, and `FML-ADR-069`
makes WAN a mesh-wide capability held by a node permitted to hold it. Nothing
here checks permission, so this is the plumbing, not the policy. It is also one
gateway; section 42 explicitly does not require competing multi-gateway
operation for v1, and none was tested.

### Why the stale neighbour entry never timed out

Addendum 6 recorded that after a rejoin the mesh looked healthy while IP was
100% dead, and that a manual `ip neigh flush` fixed it. What it did not
establish is whether the entry would have recovered on its own. Measured:
**it does not.** Over 121 seconds the entry went `STALE` to `DELAY` and then
back to **`REACHABLE`**, still pointing at a bat0 MAC that no longer existed.

The mechanism is **batman-adv's distributed ARP table**:

    distributed_arp_table: enabled
    DAT cache:  * 10.42.0.2  de:4e:7c:8e:db:ac  last-seen 3:39     <- dead MAC
    transglobal: * fe:24:00:fa:74:39 ... via <MAC-01-REDACTED>      <- correct MAC

batman-adv **knew the new address** -- the global translation table had it -- and
**answered ARP with the old one** from DAT. So the neighbour probe that should
have invalidated the entry got a reply instead, which re-confirmed it as
`REACHABLE`. The failure is self-reinforcing: the recovery mechanism is what
keeps it broken. That is why it "fails to time out" rather than merely being
slow.

DAT entries do age, so recovery was probably coming at the DAT entry timeout
rather than never; that bound was not measured and should not be quoted.

### The resolution

**Primary fix: a stable `bat0` address.** The kernel assigns `bat0` a fresh
random MAC on every creation, which is what makes every rejoin and every reboot
produce a stale mapping. `test/bench/80211s-mesh-real.sh` now derives one from
the node's own radio, setting the locally-administered bit in the first octet and
keeping every other octet: the radio's `00:…` becomes `02:…`, which on node 1
gives `02:c0:ca:be:28:67`. Stable per node, distinct between nodes, cannot
collide with the radio's real address, and applied while `bat0` is still down.
The derived address is locally administered, so it names no equipment and is
recorded in full; the radio's own address is not.

**Secondary fix: announce the address.** After `bat0` comes up the node sends a
gratuitous ARP (`arping -U`), so peers and DAT learn the mapping immediately
instead of when something expires. This covers the cases where the address
legitimately does change -- a first join, or a swapped radio -- for which a
stable derivation is no help.

Verified across three teardown-and-rejoin cycles:

| Trial | `bat0` MAC after rejoin | IP recovery, no flush |
| --- | --- | --- |
| 1 | `02:c0:ca:be:28:68` unchanged | 24 s |
| 2 | `02:c0:ca:be:28:68` unchanged | 12 s |
| 3 | `02:c0:ca:be:28:68` unchanged | 24 s |

Against the pre-fix behaviour -- dead beyond 121 s and requiring manual
intervention -- recovery now lands inside the ordinary convergence band this
bench already measured at 7 to 40 seconds. **The claim is that the
self-reinforcing stale case is gone, not that recovery is fast:** three trials
cannot bound a figure whose natural spread is already 5.5x, and addendum 5 is
the reason not to pretend otherwise.

**Not a program decision.** The field addressing plan belongs to `TBR-NET-01`,
which may prefer an address derived from node identity over one borrowed from a
radio that can be swapped. This is the bench fixing a bench defect in a way that
makes the underlying problem visible to that trade.

## Addendum 8: multicast measured, strict isolation, and the bench is under-voltage

Three things, and the third one qualifies everything above it.

### The bench is under-voltage and throttled, and provenance never recorded it

Returning to the bench on 2026-10-14 after it had been left running, a packet
over `bat0` took **290 ms** and steady state settled at **61.8 ms average**
(41.8 / 61.8 / 78.1 min/avg/max, 0% loss) -- against **0.9 ms** measured on
2026-10-11 on the same link. Every radio indicator looked healthy: 400 MBit/s
VHT-MCS 9, -13 dBm, 28 tx retries, 1 failed, and `power_save` off with
`mesh_power_mode active` on both nodes, so powersave was ruled out.

The cause is power, not radio:

| | pi-mule-1 | pi-mule-2 |
| --- | --- | --- |
| `vcgencmd get_throttled` | `0x50005` | `0x50005` |
| under-voltage **now** (bit 0) | yes | yes |
| **throttled now** (bit 2) | yes | yes |
| under-voltage has occurred (bit 16) | yes | yes |
| ARM clock | **600 MHz** | **600 MHz** |
| core voltage | 0.86 V | 0.88 V |
| under-voltage events in `dmesg` | 5 | **1271** |

A Pi 4 runs at 1.5 GHz or above. Both nodes are pinned at **600 MHz**, roughly
a third of nominal, by sustained under-voltage. That is enough to account for a
60x latency increase on its own, with no radio fault involved.

**This is the important part: it means the bench has a measurement-validity
problem, not just a slow node.** The 2026-10-11 figures -- 89.5 Mbps at HT40+,
114.7 Mbps at 80 MHz, 0.9 ms RTT, 0.172 ms jitter -- are internally consistent
with nodes that were *not* throttled, because a node at 600 MHz cannot produce
them. So those numbers are probably sound. **Probably is not a provenance
record.** `docs/bench-hardware-bringup.md` requires capturing the kernel, radio,
driver and image alongside every result; it does not mention throttle state, and
neither did any artifact here, so no earlier measurement can be *proved*
un-throttled after the fact.

Two actions follow, and the first is not optional:

* **Record `vcgencmd get_throttled` with every performance measurement**, and
  treat a non-zero current-throttle bit as invalidating the run rather than as
  a footnote. A throttled node under-reports the radio, which is the direction
  that quietly makes a bearer look worse than it is.
* **Fix the supply before re-measuring.** pi-mule-2's 1271 under-voltage events
  against pi-mule-1's 5 points at the node carrying two USB devices (the
  MT7612U and the T1000-E); an AWUS036ACM-class adapter alone can draw a large
  share of a Pi's USB budget. A powered hub for the radios, or a supply rated
  for the full load, is the remedy. This is `TBR-PWR-01` territory and CONOPS
  section 59's concern, arriving via the back door.

Everything in addenda 1 through 7 should be read as **pending confirmation on a
node that is not power-starved.** The qualitative findings do not move -- a
configuration defect is still a defect, a gate that cannot fail is still broken,
and DAT answering with a dead MAC is still the cause -- but every *number*
wants re-taking.

### CONOPS 22: multicast cost, and the template's own TBD

`os/config/batman-adv.conf.template` sets `multicast_mode=0`, optimisation off,
and says of it: "A REASONED DEFAULT, NOT A MEASURED ONE. The mesh does carry
traffic with it disabled, which is not the same as evidence that disabling it
helps. Revisit under TBR-RF-01." Measured, 500 datagrams of 1200 bytes to a
group with one receiver, one hop:

| `multicast_mode` | Delivered | `wlan1` tx bytes for 600 KB payload | Receive span |
| --- | --- | --- | --- |
| **disabled** (current default) | 463/500 (92.6%) | **1,944,092 (3.24x)** | **4.08 s** |
| **enabled** | 484/500 (96.8%) | **653,000 (1.09x)** | **0.06 s** |

Optimisation enabled was better on every axis measured: about **3x less
airtime**, slightly *better* delivery, and a receive span 68x shorter. The
mechanism is unsurprising once stated -- 802.11 sends multicast and broadcast at
a basic rate rather than the negotiated MCS, so flooding 600 KB serialised at
roughly **1.2 Mbit/s**, around 70x slower than the unicast goodput measured on
the same link.

**Left at the template default of 0.** This is one hop with one receiver on a
throttled node, and CONOPS 22's `[SHALL]` asks for multicast "under
representative multi-hop load", which two nodes cannot pose. The number that
would actually decide the default is how flooding scales with hop count and
receiver count, and that needs a third node. So this is an input pointing
against the current default, not grounds to change it; `TBR-RF-01` owns it.

Also noted: `multicast_fanout` is 16 on both nodes, untouched and unmeasured.

### CONOPS 41: the stricter isolation run

Addendum 4's section 41 test removed only default routes, so the LAN resolver
stayed reachable on-link and DNS kept working -- it measured loss of the
off-site path, not isolation. Repeated with DNS and the LAN gateway blocked
outright as well:

| Condition | Verified |
| --- | --- |
| off-site IP | unreachable |
| LAN gateway | blocked |
| DNS | **fails** |

Under that, on both nodes:

* **S0 routing** held: `bat0` up, peer `ESTAB`, 3/3 ICMP, 0% loss.
* **S1 peer ATAK** held: a GeoChat and a PLI arrived at the far node with
  `senderCallsign`, chatroom and `messageId` intact (`1 GeoChat, 1 PLI, 2
  keepalive, 0 unparseable`).
* **The configuration plane** ran with no network at all: `python -m mule
  --region us-915 --mission mission/examples/valid-minimal.json --check`
  exited 0.

Restored afterwards with routes, DNS and off-site reachability confirmed back
and **no leftover firewall rules** on either node.

**The `local S0 and S1 services` row of section 41 remains untested, because
there are no such services deployed on these nodes.** `mule-runtime` is
inactive, `chrony` is absent so section 9's "required local time functions" do
not exist here, and the operator readout runs on the bench mule, which is not a
mesh node. Until the runtime is deployed, that row cannot be exercised, and
routing plus peer ATAK are the only S0/S1 examples this bench can speak to.

### An incidental finding worth more than it looks

The configuration renderer above exits 0 but reports that **no region profile is
resolvable**, because `wifi.mesh_channel` and `wifi.mesh_max_eirp_dbm` are
"supplied by `TBR-RF-01`" (with the LoRa equivalents owed by `TBR-RF-02`).

So the config plane is blocked on exactly the two values this bench has been
measuring. The channel work in addendum 2 and the transmit-power behaviour in
addendum 4 are inputs to unblocking `os/`, not merely mesh characterisation --
which is the most direct line yet from this bench to the program's own stated
bottleneck.
