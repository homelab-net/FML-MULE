# Option A's detection thresholds: a partition sweep against a node probe

**Tier: real-hardware bench result; formal `HARDWARE-VERIFIED` held** (see
`docs/evidence/TBR-NET-02/2026-09-27-one-lora-hop-to-a-partner-node.md` for why).
**Every timing figure is provisional:** the probe's host read `0x50005`
(under-voltage, throttled) in 103 of 114 samples.

**What this answers.** Parameter 2 of the [decision packet][packet] makes
detection an application-level probe of the authority, "a TLS session plus an SA
round trip", and leaves "the entry threshold, exit threshold and hold time
`TBD`, set by measurement". This run measures the first two. It cuts the server
silently for 5 s to 120 s, runs a probe through every cut, and replays the
probe's record against each candidate setting.

**Proposed for the Owner's acceptance:**

| Parameter | Proposed | Measured basis |
| --- | --- | --- |
| Entry | **20 s** with no relayed probe | Detected 19.5 to 19.6 s into every cut of 20 s or longer; no false entry at any threshold. A client with a 25 s stream timeout kept its session through every cut of 20 s or less. |
| Exit | **3** consecutive relayed probes | 1.5 to 3.6 s after each lift; 1 probe exits 0.1 to 1.7 s after. |
| Hold time | **Still `TBD`** | Needs a lossy link; this LAN lost no probe. |

The reasoning for 20 s is in [Choosing the values](#choosing-the-values). The
sweep sets no lower bound on its own: on this LAN, every threshold from 2 s up
behaved perfectly, because nothing but the cuts ever stopped a probe.

| Item | Value |
| --- | --- |
| Date | 2026-10-25, 01:14 to 01:33 UTC |
| Taken by | Cameron Zobrist (the Program Owner), with Claude Code operating the bench at the Owner's direction |
| Server | Official TAK Server 5.8 on `pi-mule-2`, TLS stream on 8089 |
| Network | One LAN segment, as in the [prototype][prototype]: not the mesh |
| Instruments | `test/bench/tak-blackhole-relay.py` (the cut), `tak-partition-probe.py` (the probe), `tak-partition-eud.py` (a simulated EUD), `tak-session-sample.sh`, and `tak-partition-sweep-analyze.py`, whose candidate settings were fixed before the run |

## How the cut was made

The prototype's cut is an nftables drop, which needs root on the server host.
This run used a **relay** instead, which needs none: a TCP relay on `pi-mule-2`
in front of the server's 8089, through which the probe and the simulated EUD
connected (the TLS passes through untouched). During a cut it stops reading,
writing and accepting, but closes nothing. So a client sees what the drop
gives it: its sends back up, nothing arrives, and a new connection completes
TCP in the kernel's backlog but its TLS handshake hangs.

The relay ran the schedule itself, logging each transition with a millisecond
UTC timestamp: a 60 s baseline, then cuts of 5, 10, 15, 20, 30, 45, 60, 90 and
120 s, 75 s apart. Every cut lasted its planned length to within 0.1 s.

**The price of not using root:** only clients that connect through the relay
are cut. WinTAK and iTAK connected directly and were **not** cut, so this run
says nothing new about them.

## The probe

`tak-partition-probe.py` holds two TLS sessions to the server as two uids, one
sending and one listening. Every second the sender sends an SA whose remarks
carry a sequence number; the listener logs each one the server relays. A probe
is "relayed" when the listener receives it, so a server that accepts
connections but relays nothing counts as down. That is the packet's reason for
an application-level probe: on 2026-10-17 a port check passed 13 s before the
server relayed.

Each session gives up on 5 s of silence and reconnects with a 3 s timeout, so
the probe recovers on its own after a lift. While the sending session is down
the probe records the second as skipped, not as lost.

It is not `tak-probe.py`, the failover trials' probe. That probe's listener has
no silence timeout, so a silent cut leaves it waiting on a dead session, and its
positions carry a random tag rather than a sequence number, so it cannot count
loss or time a round trip.

## Candidate settings

The analyzer replays one rule over the probe's record. **Entry E:** the node
declares a partition when no probe has been relayed for E seconds. **Exit K:**
it declares the partition over at the K-th consecutive relayed probe. Each cell
below is seconds from the cut's start to entry / seconds from the lift to exit;
`-` means the setting never entered.

| E | K | 5 s | 10 s | 15 s | 20 s | 30 s | 45 s | 60 s | 90 s | 120 s | False |
| ---: | ---: | --- | --- | --- | --- | --- | --- | --- | --- | --- | ---: |
| 2 | 1 | 1.7 / 0.8 | 1.6 / 0.1 | 1.5 / 0.1 | 1.6 / 0.2 | 1.5 / 0.2 | 1.5 / 0.7 | 1.6 / 0.6 | 1.6 / 0.3 | 1.5 / 1.7 | 0 |
| 2 | 3 | 1.7 / 2.6 | 1.6 / 1.5 | 1.5 / 1.5 | 1.6 / 1.6 | 1.5 / 1.6 | 1.5 / 2.5 | 1.6 / 1.6 | 1.6 / 1.5 | 1.5 / 3.6 | 0 |
| 5 | 3 | 4.7 / 2.6 | 4.6 / 1.5 | 4.5 / 1.5 | 4.6 / 1.6 | 4.5 / 1.6 | 4.5 / 2.5 | 4.6 / 1.6 | 4.6 / 1.5 | 4.5 / 3.6 | 0 |
| 10 | 3 | - | 9.6 / 1.5 | 9.5 / 1.5 | 9.6 / 1.6 | 9.5 / 1.6 | 9.5 / 2.5 | 9.6 / 1.6 | 9.6 / 1.5 | 9.5 / 3.6 | 0 |
| 15 | 3 | - | - | 14.5 / 1.5 | 14.6 / 1.6 | 14.5 / 1.6 | 14.5 / 2.5 | 14.6 / 1.6 | 14.6 / 1.5 | 14.5 / 3.6 | 0 |
| **20** | **1** | - | - | - | 19.6 / 0.2 | 19.5 / 0.2 | 19.5 / 0.7 | 19.6 / 0.6 | 19.6 / 0.3 | 19.5 / 1.7 | 0 |
| **20** | **3** | - | - | - | 19.6 / 1.6 | 19.5 / 1.6 | 19.5 / 2.5 | 19.6 / 1.6 | 19.6 / 1.5 | 19.5 / 3.6 | 0 |
| 30 | 3 | - | - | - | - | 29.5 / 1.6 | 29.5 / 2.5 | 29.6 / 1.6 | 29.6 / 1.5 | 29.5 / 3.6 | 0 |

The analyzer's full table, with E of 3 and 8 and K of 1 at every E, is the same
pattern: entry always comes 0.3 to 0.5 s before E seconds into the cut (the
last probe relayed before the cut was that much older), and exit depends only on
K and how fast the probe's sessions came back.

**With no cut in force,** 184 probes were sent and every one was relayed. The
round trip had a median of 4 ms, a 99th percentile of 19 ms and a maximum of
68 ms. No setting entered outside a cut.

The analyzer stops at the relay's "sweep done", because the relay exits there
and its clients see that as one last cut. The first analysis did not, and
counted one false entry at every threshold for it.

## What a client did

The simulated EUD gives up on a stream after 25 s of silence, about where
WinTAK did in the prototype (35 s to its first reconnect attempt).

| Cut | 5 s | 10 s | 15 s | 20 s | 30 s | 45 s | 60 s | 90 s | 120 s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Simulated EUD | kept | kept | kept | kept | 24.6 / 0.1 | 24.6 / 4.6 | 24.6 / 0.5 | 24.6 / 0.2 | 24.6 / 0.7 |

`kept` means the client never noticed: its session survived the cut. Otherwise the
cell is seconds into the cut when it gave up / seconds after the lift when its
stream was back.

## Choosing the values

Parameter 2 rate-limits transitions "because each one cuts sessions", and
parameter 6 closes proxies on mode exit. So an entry is not free: entering on a
cut the clients would have ridden out costs them a session they would have kept.

- **Entry at 20 s** declares every cut that outlasts a 25 s client timeout, and
  none that a client survives. It enters about 5 s before such a client gives
  up, and about 15 s before WinTAK did, so the indication and the LoRa bridge
  are ready when they are needed.
- **A lower entry** (5 or 10 s) would have declared the 5 to 15 s cuts, which
  the client rode out. Its only gain is 10 to 15 s of earlier indication on
  long cuts.
- **A higher entry** (30 s) would leave a client 5 s without service before the
  node noticed.
- **Exit at 3** probes costs 1.0 to 1.9 s over exiting on the first, and
  guards against one probe leaking through a flapping link. A flapping link is
  the lossy-link run's question; on this LAN, K = 1 would also have been exact.

The sweep can only show that 20 s is safe on a clean link. On a lossy one,
probe loss shortens the margin between a run of lost probes and a real cut,
which is what the hold time is for.

## What this does not show

- **WinTAK and iTAK under these cuts.** The relay cuts only its own clients. A
  re-run with the nftables cut needs root on the server host.
- **A lossy or flapping link.** Nothing here lost a probe outside a cut, so the
  false-entry count of 0 says nothing about radio. The hold time stays `TBD`
  until a run with induced loss (for example `netem`) sets it.
- **The mesh.** The packet asks for a probe over mesh addresses only; this ran
  on one LAN segment.
- **Repetition.** One pass per cut length. The timings are consistent across
  lengths, but each length was cut once.
- **The node.** The probe is a bench instrument. No node holds a mode, raises an
  indication or starts a bridge yet.

## For the Owner

1. **Accept or change entry 20 s and exit 3 probes.** Once accepted, parameter 2
   cites this record and the two values are no longer `TBD`.
2. **The hold time** waits on a lossy-link run.

[packet]: 2026-10-18-degraded-mode-when-no-safe-authority-decision-packet.md
[prototype]: 2026-10-24-option-a-prototype-peer-mode-under-a-server-cut.md
