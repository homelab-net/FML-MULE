# CONOPS traceability

What the CONOPS asks for, against what this repository has actually measured.

**Why this file exists.** `docs/conops/FML-MULE-CONOPS-v1.2.txt` carries **185
`[SHALL]` statements**. Until this file, answering "which of them have we shown?"
meant reading the CONOPS and every artifact under `docs/evidence/` side by side
and holding the result in your head. That is how a program comes to believe it
has demonstrated more than it has.

**Scope and honesty rules.** This file records only what an artifact in this
repository supports, with the artifact named. It is deliberately not a
self-assessment of maturity: `STATUS.md` says the program is pre-PDR and that
nothing is hardware-verified, and nothing here contradicts that. A row saying
*demonstrated* means one artifact supports one reading at one scale, usually one
hop on a bench. It does not mean the requirement is satisfied for the field, and
`CONOPS` section 22's last `[SHALL]` forbids reading it that way.

## Demonstrated, at bench scale

| CONOPS | What it asks | Evidence | Scope limit |
| --- | --- | --- | --- |
| **40** Traffic preference | `[SHALL]` traffic policy shall preserve mission-critical communications before bandwidth-intensive services | `TBR-RF-01/2026-10-11-two-node-80211s-batman-real-radio.md` | one hop; qdisc is illustrative, mechanism is `TBR-RF-01`'s; imposed 5 Mbit bottleneck, not measured capacity |
| **40** GeoChat row | GeoChat → stable viable IP path | same, addendum 1 | 3 of 3 under contention, one hop |
| **40** Large files row | Large files → high-throughput IP | same, addendum 1 and 2 | 64 MiB, md5 verified, one hop |
| **33** High-throughput IP bearer | `[SHALL]` capable of exploiting a higher-throughput IP path | same, addendum 2 | **one** of its six stated purposes (large file transfer). 114.7 Mbps at 80 MHz, 89.5 at HT40+. Bench range only; the propagation half is untested |
| **21** Peer-to-peer ATAK | peer functions without a TAK Server: PLI, GeoChat, selected CoT | same, addendum 1 and 3 | synthetic EUDs, not ATAK; a plain sink, not a server |
| **41** WAN independence | `[SHALL]` loss of WAN shall not remove local mesh, peer ATAK | same artifact, addenda 4 and 8 | re-run in addendum 8 with DNS and the LAN gateway blocked too, so isolation this time, not just loss of the off-site path. Still only the local-mesh and peer-ATAK rows: `local EUD access` had no EUD, and **no S0/S1 services are deployed on these nodes** (`mule-runtime` inactive, no `chrony`), so that row cannot be exercised at all |
| **42** Local WAN gateway | `[SHALL]` any standard MULE shall be technically capable of assuming an authorized local WAN-gateway role | same artifact, addendum 7 | plumbing only: nothing checks *authorization*, which is what section 42 and FML-ADR-069 actually require. One gateway, not competing gateways |

## A caveat that applies to every number above

On 2026-10-14 both bench nodes were found **under-voltage and throttled to
600 MHz** (`vcgencmd get_throttled` = `0x50005`, 1271 under-voltage events on
one of them), which alone moved mesh RTT from 0.9 ms to 61.8 ms. No earlier
artifact recorded throttle state, so while the 2026-10-11 figures are internally
consistent with un-throttled nodes -- a node at 600 MHz cannot produce
114.7 Mbps -- none of them can be *proved* un-throttled after the fact. Treat
every quantity in this file as pending re-measurement on a node that is not
power-starved. See addendum 8. The qualitative findings are unaffected.

## Partially shown, and weaker than the row above suggests

| CONOPS | Shown | Not shown |
| --- | --- | --- |
| **39** Adaptive routing | no manual route selection; link degradation tracked (TQ 255 to 186 under 30% emulated loss) and recovered; node loss eventually detected; **failover between two bearers to one neighbour**, 4.1 to 6.0 s at the default `orig_interval` and 1.2 s at 250 ms, and recovery of the better path in 30 to 60 s, with "better" meaning loss (`TBR-RF-01/2026-10-17-two-bearer-failover-80211s-and-wired-vlan.md`; the second bearer is wired) | **movement**, and **failover around a lost relay**, which need a third node. Node loss took ~165 s at the routing layer and the 802.11s peer entry did not clear at all inside 302 s |
| **22** Peer-to-peer scaling | 5 synthetic EUDs across 3 hosts | `[SHALL]` multicast under representative **multi-hop** load; `[SHALL]` usable network size and hop-count limits. Both need multi-hop |

## Not addressed at all

Sections **13-18** (authentication, mission-scoped trust, revocation, EUD
recovery, credential lifecycle), **24-30** (server-enhanced TAK, authoritative
state, continuity, split-brain, promotion), **34** (HaLow IP bearer), **35**
(LoRa/Meshtastic bearer, encoding harness built but no delivery), **36** (dual
sub-GHz chains and coexistence), **43-48** (WAN overlay, remote team, external
VHF/UHF/HF, amateur-radio governance, interoperability, incident command),
**49-58** (browser services, modes, exercise control, training, AAR, privacy,
retention), **59+** (power, thermal, physical capture).

Also explicitly **not** satisfied: section 33's last `[SHALL]`, that the
high-throughput band be selected before RF coexistence analysis. 5745 MHz was a
bench channel choice, not a program band selection, and section 36's coexistence
analysis has not started.

## A correction this file should carry

Earlier bench writing, including commit messages, used the word "voice" for the
traffic class measured in the contention runs. Section 32 says plainly that
**MULE is a data capability and does not by itself satisfy a voice
communications requirement**. What was measured is a voice-*profile* UDP flow,
~160 B every 20 ms, which is the class section 40's table prioritises. There is
no audio pipeline; that is `TBR-VOICE-01`.
