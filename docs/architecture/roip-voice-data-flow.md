# RoIP voice data flow, and the invariants that keep it safe

**Status: CONOPS text issued in v1.2; nothing built.** This note describes the
intended architecture of the audio/PTT Radio-over-IP (RoIP) voice capability.
That capability is issued CONOPS text under
`docs/change-requests/CCR-03-integrated-rf-dm32-roip-voice.md`. Its decisions
(`FML-ADR-064` through `FML-ADR-067`) are `SELECTED`. The implementation is
`TBR-VOICE-01`, `OPEN`. So every "does" and "is" below is a statement of
design intent that no bench has yet demonstrated, not a claim about behaviour.
Where a mechanism is required but unbuilt or unproven, the note says so rather
than implying it works.

This note exists because the data flow is only implicit across four ADRs and a
change request, and it was being re-derived (and nearly gotten wrong) each time
someone read them. It is the single place the scenarios and their invariants are
written down.

## What it is, in one line

The MULE moves a gateway radio's **audio and PTT state** between nodes as IP
(`FML-ADR-065`); it never speaks DMR or any RF protocol. That makes the scheme
radio-agnostic: the DM-32UV is the selected radio (`FML-ADR-064`), but "or any
other radio" is the point.

## The elements and their interfaces

| Element | What it is | Interface |
| --- | --- | --- |
| Operator radio | The human's radio (DM-32 or other), on the local RF net | Headset + PTT (dismounted) or speaker + fist-mic (vehicle). Not wired to the MULE for voice. |
| MULE gateway radio | A **dedicated, separate** radio per node (`FML-ADR-066`), on the same local RF net as the operators | Over-the-air on the local net; wired to the MULE only through the audio interface below |
| Audio interface | The only thing the MULE touches | DigiRig Mobile: CM108 USB audio (RX/TX) + CP2102 serial RTS (PTT keying). Audio and key state only. |
| RoIP controller | A MULE service (`TBR-VOICE-01` selects the implementation) | Opus encode/decode, signalling, session/origin tagging; decides when to key the gateway; enforces `FML-ADR-067` |
| Inter-node bearers | The "mesh" for voice | Wi-Fi, HaLow, Ethernet, or Tailscale, addressed per `FML-ADR-063` |
| EUD (phone) | Receives **data**, never voice | The MULE Wi-Fi access point (a separate plane; see below) |

The structural fact the rest of the note rests on: the operator radio and the
MULE gateway radio are **two different radios talking over the air** on the
local net. The MULE bridges nets by being a station that re-keys a radio; it
never injects audio into a headset.

## The one invariant everything serves

`FML-ADR-067`, the single-audio-egress invariant: **an operator receives a
linked voice session through exactly one path, and in v1 that path is always the
operator's own radio over local RF.** Every scenario below is a consequence of
holding that line. A voice baseline that can put two copies in one ear is not
acceptable, which is why this is an invariant and not a tuning goal.

## Data flow by connectivity state

### Mesh present, MULE on (the linked case)

```text
Op A2 keys PTT  (Team A channel)
  |
  |-- heard directly by Team A radios in range (incl. team lead A1)
  |
  '-- MULE-A gateway radio (RX)
        -> DigiRig -> RoIP controller  (tag: origin=A2, net=A)
             -> Opus / IP over mesh (Wi-Fi | HaLow | Tailscale)
                  -> MULE-B RoIP controller
                       -> DigiRig -> MULE-B gateway radio (TX, Team B channel)
                            -> heard by Team B radios in range
```

Path of the bits: **local RF -> audio + PTT digitised at the gateway -> Opus
over IP across the mesh -> re-keyed onto the remote team's local RF.** Two teams
on different RF channels are linked, and neither MULE understands the waveform.

The data plane (CoT, chat, map tiles) runs in parallel over the same IP bearers
but is a different plane; see "Two planes" below.

### Mesh absent, MULE on

The local RF net is unchanged: operators talk radio-to-radio directly, as they
always could. The gateway radio is present but has no peer to bridge to, so
there is no cross-team link. The MULE may still serve **data** to phones
locally. For voice, this state is functionally "the MULE is not there."

### MULE down, radio up

The operator radio is independent and keeps working on the local net,
radio-to-radio. What is lost is the **bridge** (the dedicated gateway radio dies
with the MULE), not local voice. This is a `[SHALL]` in `CCR-03`: local RF works
without the MULE, and loss of the IP path returns users to local RF (CONOPS
45.1, 45.8). Voice fails **soft**, down to plain RF, never to silence.

The through-line across all three: the operator always hears through **their own
radio over local RF**. That is `FML-ADR-067` holding.

## The cross-channel bridge, worked

Take the question that motivates this note. Team A and Team B each have a MULE;
the MULEs are meshed. A2 (any operator on Team A, not necessarily the team lead)
keys up. The team lead A1 happens to carry Team A's MULE.

- A2 reaches the mesh because **MULE-A's gateway radio hears A2 over the air**
  on Team A's channel. Not because A2 routes "through" A1's personal radio, and
  not because A2 is integrated to anything. The team lead is a mounting
  location, not a router.
- A2's audio crosses to MULE-B and is re-keyed onto Team B's channel, where B2
  hears it.
- B2 hears it **exactly once.** The load-bearing reason: Team A and Team B are
  on **different RF channels** (they are bridged precisely because they cannot
  hear each other directly). B2's radio, tuned to channel B, does not pick up
  A2's channel-A transmission over the air, so the only A2 -> B2 path is the one
  mesh bridge. One path, one copy.

So yes, an operator's transmission propagates across MULE hops to a remote team.
That is the designed function, not a leak.

## The three guards against a second copy

1. **No direct MULE-to-headset audio.** The MULE only ever re-keys a radio; the
   only audio in an ear is that ear's own radio.
2. **Self-echo suppression by origin/session ID.** MULE-A tags the session
   `origin=A2, net=A`. No gateway re-keys that session back onto net A, so A2
   and A1 never hear a bounced copy of A2.
3. **Single active gateway per voice group per local net.** A net is bridged by
   exactly one gateway, so two MULEs cannot both re-key the same net.

## The case that would double, and why it is disallowed

The double-copy and loop risk does not arise from the cross-channel case above.
It arises from one specific configuration:

> **Same RF channel, in direct RF range, and both MULEs bridging.**

Then A2's transmission is heard directly by Team B (same channel) **and** MULE-A
relays it to MULE-B, which re-keys it onto that same channel: a second copy. And
MULE-B's re-key is heard by MULE-A's gateway, sent back over the mesh: a loop.

The design refuses this on two levels:

- **Voice group is not reachability** (`FML-ADR-061` shape; CONOPS 43, 44; a
  `[SHALL]` in `CCR-03`). Being reachable on the mesh is not being in a voice
  group. The MULE does not auto-bridge every net it can hear to every net it can
  reach; bridging follows a configured voice-group plan. Two radios that are
  already one RF net are one voice group with one gateway. You never bridge a net
  to itself.
- **No persistent loop or self-keying** (`CCR-03` `[SHALL]`). Even under a
  misconfiguration, the origin/session ID means a gateway drops a session it
  already originated or is already relaying, so a loop cannot sustain: it dies on
  the first lap.

## PTT arbitration and contention

Voice is half-duplex and a gateway can relay one talker at a time, so the design
needs a rule for who wins when two operators key across a bridge at once, and
whether a higher-priority talker can barge in.

**This is not settled, and it is gated on a hardware unknown.** `CCR-03` section
10.3 and roadmap item 4.3 record that reliable PTT arbitration depends on
**RX-activity detection** the software does not yet have: hardware carrier
detect (COS/COR) versus validated squelch versus audio-energy/VOX, and the
handoff explicitly warns against assuming VOX is adequate. Until that question
is answered on real hardware, arbitration logic can be written but not trusted,
because it cannot reliably know when the local net is busy.

## Partition mid-session

If a MULE or a bearer drops during a live link, the session must fall back to
local RF **and the operators must know the link is gone**, rather than a silent
loss that reads as "the far team went quiet." The fallback direction is the
`CCR-03` degrade `[SHALL]` (return to local RF); the notification is a design
obligation this note flags and that `TBR-VOICE-01` must satisfy. Silent link
loss on a voice path is a safety issue, not a UX nicety.

## Headset versus vehicle: topology independence, and the one real risk

Switching an operator from a plate-carrier headset+PTT to a vehicle
speaker+fist-mic **does not change the architecture or the data flow.** The
audio accessory is just how the operator's own radio presents audio; every trace
above is identical.

What changes is the risk you must engineer against:

- **Dismounted:** the handheld is obviously separate from the MULE's gateway
  radio. The invariant holds trivially.
- **Vehicle:** the temptation is to make one vehicle-mounted radio serve as both
  the operator's speaker radio and the MULE's gateway radio, because it is wired
  in already. That is exactly the double-audio case `FML-ADR-067` forbids: the
  operator would hear the direct RF and a re-keyed copy. The design's answers all
  aim here: a **dedicated** gateway radio (`FML-ADR-066`, keep it separate),
  self-echo suppression, and one active gateway per net. The safe pattern is the
  same in both mountings: operator radio is not the gateway radio.

## Two planes: voice and data are separate

Data and voice are separate planes that share only the inter-node IP transport.

| Plane | Rides | Lands on |
| --- | --- | --- |
| Data (CoT, chat, map tiles) | IP mesh, node to node | Phones, via the MULE Wi-Fi access point |
| Voice | Local RF, bridged as RoIP over the same IP transport | Radios |

In v1, voice never lands on the phone and data never lands on the radio. Keeping
this explicit prevents the reflex to "just send voice to the EUD," which would
break the single-egress invariant and drag the MULE into the RF-protocol
business `docs/NON-GOALS.md` keeps it out of.

## What enforces this, and what is still a gap

The invariants above are **stated requirements, not demonstrated behaviour.**
The mechanisms that would enforce them are open:

- **Which nets form one voice group**, and the credential that authorises a MULE
  to bridge one net to another, is `TBR-SEC-01` territory (voice-group
  credential distribution, recorded as an open gap) plus `TBR-VOICE-01` (the
  gateway implementation). Without it, "voice group is not reachability" is a
  principle with nothing implementing it.
- **PTT arbitration** waits on the RX-activity-detection hardware question
  above.
- **RF coexistence** of a transmitting gateway radio in the enclosure beside
  HaLow and LoRa is `TBR-RF-02`; the mitigation architecture can be designed now
  but the measurement needs the BOM.
- **Compute under a live session** is a `TBR-COMP-01` gate (the 4 GB versus 8 GB
  fail-back), and a live RoIP session competes for QoS with the routing daemon on
  a bearer whose behaviour under load is untested (`TBR-RF-01`).

## Open questions this note surfaces

Recorded so they become work items rather than surprises, and none needs the
BOM to begin:

- **Multi-hop mouth-to-ear latency**: voice across several MULE hops and mixed
  bearers, with the Opus jitter buffer, and whether it stays usable. The
  *transport* half is now measured (`SIMULATED`) in
  `docs/evidence/TBR-RF-01/2026-09-14-mesh-multihop-latency-hwsim.md`; the audio
  pipeline that makes it mouth-to-ear is unbuilt (`TBR-VOICE-01`).
- **Voice and data QoS contention** on one bearer under load. Now shown on the
  bench (`SIMULATED`):
  `docs/evidence/TBR-RF-01/2026-09-14-voice-data-contention-hwsim.md` -- voice
  starves behind bulk in one FIFO and is preserved by a protected class; the QoS
  mechanism remains `TBR-RF-01`'s.
- **Voice groups across a mesh merge**: when two deployments converge
  (`FML-ADR-061`, `TBR-NET-03`), voice-group membership must not merge just
  because the networks did. Now tracked as `TBR-VOICE-02`.

## Where this sits in the records

- Concept and scope: `CCR-03`.
- Decisions: `FML-ADR-064` (radio), `FML-ADR-065` (audio/PTT over IP, not native
  DMR), `FML-ADR-066` (dedicated gateway radio), `FML-ADR-067` (single audio
  egress).
- Implementation trade: `TBR-VOICE-01`. Roadmap: `docs/ROADMAP-DEV.md` items 4.2
  and 4.3. CONOPS basis: section 45, with 43 and 44 for authorisation and 9 for
  service shedding.
