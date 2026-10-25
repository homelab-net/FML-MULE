# Option A's smallest prototype: peer mode under a server cut, on WinTAK and iTAK

**Tier: real-hardware bench result; formal `HARDWARE-VERIFIED` held** (see
`docs/evidence/TBR-NET-02/2026-09-27-one-lora-hop-to-a-partner-node.md` for why).
**Every timing figure is provisional:** the host of the simulated client read
`0x50005` (under-voltage, throttled) in 73 of 84 samples during the scored run.

**What this answers.** Section 6 of the [decision packet][packet] makes one
prototype the gate before anything else is built: "two real clients on one
network, with the server made unreachable. Does peer SA and chat continue, and
does the server stream resume on heal? If not, option A fails on these clients
and this packet returns to the Owner."

**Answer, per client:**

| Client | Peer SA and chat continue under the cut | Server stream resumes on heal |
| --- | --- | --- |
| WinTAK 5.8.0.147 (Windows 11) | **Yes.** Every multicast chat both ways and every multicast SA crossed during both cuts. | **Yes,** 0.3 s and 1.7 s after each lift. |
| iTAK (iOS, the owner's, version not recorded) | **No.** It sent no multicast or broadcast at all; a counter on the access point proved it. | **Yes,** about 49 s and 38 s after each lift. |

So the gate is **met for WinTAK and not met for iTAK**. Under the packet's own
rule, option A fails on iTAK and the question returns to the Owner (section 6
below). The packet asked for two real clients; the second peer here was a
simulated EUD, because iTAK has no peer path to test.

| Item | Value |
| --- | --- |
| Date | 2026-10-24; scored run 23:31 to 23:46 UTC |
| Taken by | Cameron Zobrist (the Program Owner), with Claude Code operating the bench at the Owner's direction |
| Server | Official TAK Server 5.8 on `pi-mule-2`, TLS stream on 8089 |
| Network | One LAN segment: a consumer access point with client isolation off and IGMP snooping off, bridging Wi-Fi and wired ports. The best case for multicast. |
| Peer settings | TAK defaults: SA on `239.2.3.1:6969`, GeoChat on `224.10.10.1:17012` |
| Instruments | Bench scripts kept outside the repository for this run, since added to `test/bench`: the cut (`tak-partition-cut.sh`), a simulated EUD (`tak-partition-eud.py`), a server session sampler (`tak-session-sample.sh`), a WinTAK log and chat-database exporter (`wintak-export.js`), and an analyzer whose gate checks were written before the run (`tak-partition-analyze.py`) |

## How the cut was made

On the server host, an nftables table **dropped** (did not reject) every TCP
segment to or from 8089, 8443 and 8446 on every interface except loopback. A
client therefore saw a silent partition, as on a lost radio link, not a refused
connection. The server kept running, multicast was untouched, and each cut
lifted itself through a transient systemd timer. Each transition was logged with
a millisecond UTC timestamp, so no figure below depends on an operator's notes.

The scored run made two cuts: 23:35:45.653 to 23:38:48.971 (183 s) and
23:41:49.039 to 23:44:49.354 (180 s). The timers fired about 3 s late, which is
systemd's default timer accuracy; the analysis uses the logged times.

## Roles

- **WinTAK**, real, on the cut side. Peer mode on, sending on both of its host's
  interfaces (wired and Wi-Fi).
- **iTAK**, real, on the cut side.
- **Simulated EUD** on `pi-mule-1`, on the cut side: TLS stream plus multicast,
  SA every 5 s, and a chat every 20 s on **one** path at a time, named in its
  text (`m` multicast or `s` server), so a receipt shows which path carried it.
- **Control EUD** on the server host over loopback, which the cut spares: on the
  server side of the cut, server path only. It shows the cut is real, and what
  the far side's traffic does.
- The operator sent one WinTAK chat per phase. WinTAK's own log and chat
  database supplied its times, not screenshots.

## Gate checks, fixed before the run

| Check | Result | Detail |
| --- | --- | --- |
| A1 peer chat during the cut, both ways | **PASS** | Simulated EUD to WinTAK over multicast: 10 of 10. WinTAK to simulated EUD over multicast: 3 of 3. |
| A2 peer SA during the cut | **PASS** | WinTAK's multicast SA kept arriving every 30 s through both cuts; largest gap 30 s against a limit of 65 s. |
| A3 the cut is real | **PASS** | 0 of 44 server-path chats crossed during a cut. |
| A4 the server stream resumes on heal | **FAIL as written** | Both streams resumed within 5 s. The criterion also required the first server-path chat each way after the lift to arrive, and after cut 1 that chat was sent 2 to 5 s **before** the simulated EUD had reconnected, so it was dropped. The check stays FAIL: the criterion was fixed before the run. The cause is finding 1. |

A1 was first scored FAIL by an instrument defect, not by the network. The
operator's cut-1 chat ended in a non-ASCII character, and the simulated EUD
decoded multicast text as Latin-1, so its copy did not match WinTAK's. The
decoder now uses UTF-8, the analyzer repairs that misreading, and the rescored
result is above. No criterion changed.

## Timing

| Cut | Client | Noticed the cut after | Stream back after the lift |
| --- | --- | ---: | ---: |
| 1 | WinTAK | 36.1 s | 0.3 s |
| 1 | simulated EUD | 22.8 s | 4.5 s |
| 1 | iTAK | not logged | about 49 s |
| 2 | WinTAK | 34.9 s | 1.7 s |
| 2 | simulated EUD | 23.4 s | 0.2 s |
| 2 | iTAK | not logged | about 38 s |

- WinTAK's "noticed" time is its first reconnect attempt in its own log. It
  then retried on a fixed cycle of about 35 s (a 20 s connect timeout plus a
  15 s wait). Its sub-2 s resumes are partly luck: both retries fell just before
  a lift, so its worst case is about 35 s.
- The simulated EUD's 23 s is its own 25 s receive timeout.
- iTAK's times come from the server's session table, sampled every 2 s.

## Findings

1. **Nothing sent through the server during a partition arrives later.**
   - The control EUD sent 36 server-path chats to the cut clients during the
     cuts. **None** arrived after the heal.
   - Chats sent in the seconds before a client had reconnected were dropped too.
     This is what failed A4.
   - iTAK marked as sent four chats that never arrived: one in each cut, and
     both copies of one sent in the minute after a lift, while iTAK took about
     49 s to reconnect. It gave no failure indication.
   - WinTAK did not resend its own cut-period chats over the server after the
     heal.

   This extends the [single-front record][front]'s "a message in flight at a
   hard cut is lost" to the whole partition. Option A's peer path carries what
   is sent while partitioned; anything that must cross the partition has to be
   held and resent by something else: the gateway or the clients.
2. **iTAK has no peer path on this network.**
   - The simulated EUD heard nothing from it in two runs and an earlier session,
     even with its Local Network permission granted.
   - To exclude the network, a count-only nftables probe on the access point
     counted frames by the phone's hardware address for 83 s, with iTAK in the
     foreground and a chat sent: **251 frames, none to a multicast or broadcast
     address.** In the same window the probe counted WinTAK's multicast SA from
     both of its host's interfaces, 3 each, matching its 30 s interval, so the
     probe sees multicast when it is there. The probe was then removed.
   - Not excluded: an iTAK peer setting not found on this build.
3. **The server held dead sessions.**
   - It kept the simulated EUD's pre-cut session about 3 minutes after each cut
     (186 s and 182 s).
   - It kept **each** of WinTAK's earlier sessions open to the end of
     observation, with unsent data queued (a send queue of about 80 KB on the
     first). At the end it held three sessions for one WinTAK. This bears on
     D-1 acceptance item 4 ("no uid holds two sessions"): the server alone does
     not prevent it.
4. **WinTAK sends each peer packet on every interface.** Every WinTAK multicast
   chat reached the simulated EUD twice, once from each of its host's
   interfaces. A receiver that bridges peer traffic must deduplicate by message
   id, as the packet's gateway rule already requires for LoRa.
5. **The cut-side clients never heard the control EUD during a cut.** That is
   correct (A3), but it is also what a partitioned user sees of the other side.
   Option A's LoRa bridge exists to carry it, and it was not in this prototype.

## An earlier, unscored run the same day

A first run at 16:20 to 16:26 UTC used one cut of 5 min 43 s, a single chat each
way per phase, and the same WinTAK. Peer chat crossed both ways during the cut,
WinTAK's multicast SA kept arriving (18 packets), WinTAK noticed the cut in
21 s and resumed 12 s after the lift, and the simulated EUD resumed in 4 s. Its
design could not show which path carried a chat, and it read WinTAK by eye, so
the scored run above replaced it. It agrees with the scored run.

## What this does not show

- **A second real peer client.** ATAK on Android would be the reference; none
  was available.
- **Multicast across MULEs.** Everything ran on one LAN segment. Whether peer
  traffic crosses the mesh (`bat0`) between MULEs is untested, and so are the
  LoRa bridge, the mode indication and the beacon.
- **What WinTAK did with the simulated EUD's SA.** WinTAK keeps no SA log.
- **Detection thresholds.** The packet leaves entry, exit and hold `TBD, set by
  measurement`; these client timings inform them but are not node-probe
  measurements. The [detection sweep][sweep] measures entry and exit.

## For the Owner

Section 6 returns the packet to the Owner when the prototype fails on a client.
Three courses, which can be combined:

1. **Scope option A to clients with a peer path** (WinTAK, ATAK), and record iTAK
   as without partition service. D-1's "a user with iTAK or WinTAK" changes.
2. **Serve partitioned iTAK users from their own MULE:** while partitioned, iTAK
   reconnects to a local relay that carries its chat and SA to local peers and
   to the gateway. This reverses parameter 7 ("no local TAK server is started on
   any node") and needs its own packet.
3. **Close the gate for peer-capable clients** with a second real one (ATAK).

Finding 1 applies to all three: something must hold and resend what is sent
across a partition, or users lose it without being told.

[packet]: 2026-10-18-degraded-mode-when-no-safe-authority-decision-packet.md
[front]: 2026-10-18-single-tak-field-front-on-a-live-server-retired.md
[sweep]: 2026-10-25-partition-detection-threshold-sweep.md
