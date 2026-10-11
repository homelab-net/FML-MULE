# Two-node 802.11s + batman-adv on real radios

**Tier: deferred (real-hardware bench result; formal `HARDWARE-VERIFIED` held).**
Every earlier `TBR-RF-01` artifact is `SIMULATED`; this one met a radio. The
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
`mt76x2u`, `00:c0:ca:be:28:67` and `00:c0:ca:be:28:68`; selected by driver, not
by name. **Configuration:** 802.11s mesh id `fml-bench-mesh` on 5745 MHz
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
