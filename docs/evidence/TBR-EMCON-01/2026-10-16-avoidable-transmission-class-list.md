# Which transmissions an EMCON posture classes as avoidable, and which layers suppress them

**Trade:** `TBR-EMCON-01`.
**Date:** 2026-10-16.
**Produced by:** written analysis against the controlling documents. No
hardware, no radio, and no measurement of any kind.
**Status of this artifact:** `UNVERIFIED`. It is reasoning, not a result.

**It does not close the trade.** The closure gate is the named owner's
acceptance of the class list and the layer map. An artifact's presence is not
acceptance.

## What this is, and what it is not

`FML-REQ-049` is binding, allocates here, and validates at Stage 10:

> While EMCON is in effect the system does not originate a transmission the
> active posture has classed as avoidable.

A posture cannot apply that requirement without a list of classes to apply it
to. SAD section 23 names seven layers that can suppress emissions; it does not
say what each layer suppresses. Individual emissions are recorded across the
CONOPS, several ADRs, the config templates and earlier evidence, but no
consolidated list existed. This file is that list.

**This is not a measurement of radio silence.** CONOPS 50.12 is explicit --
*"EMCON shall not be reported as measured radio silence. Measured silence is
a measurement, not a mode."* No transmission was observed for this artifact,
and no claim below rests on observing or failing to observe one. Where earlier
evidence in this repository records emissions that were observed, they are
cited as **existing observations under other trades**, never as a measurement
of an EMCON effect.

**It does not decide the enforcement mechanism.** See findings 3 and 4.

## The seven layers, quoted

SAD v0.32 section 23, line 1547, *"EMCON is enforced at multiple layers"*:

1. network/radio advertisement behavior;
2. high-rate bearer state;
3. HaLow update/scanning behavior;
4. service announcement behavior;
5. nonessential service activity;
6. WAN-overlay activity;
7. EUD operator policy.

The same section adds the constraint that bounds layer 7: *"The architecture
does not assume an EUD can be made fully electromagnetically silent by MULE
alone."*

`C50-01` in the SAD traceability matrix maps CONOPS section 50 onto SAD
sections **23 and 19.2**. Section 19.2 lists **EMCON policy** among the mission
configuration package contents, so a class list has a stated home: the layers
are architecture, and the policy selecting among them travels in the signed
mission package.

## How the classes are partitioned

Each class is separated by **emitter, trigger, bearer, and controlling
party** -- what originates it, on what schedule or event, over which bearer,
and whether the node, a service, or the end user device controls it.

The partition deliberately does **not** use the suppressing layer. The layer
map is this document's output, so using it to define the classes would settle
the question by construction: read layer 1 broadly and the mesh beacon, the
originator message and the LoRa housekeeping broadcast collapse into one class
too coarse to act on; read it narrowly and classes appear wherever the layer's
wording happens to be silent.

## The class list

Avoidability is the posture's *option*, not a recommendation. CONOPS 50.12
prohibits originating what the active posture **has classed** avoidable, so a
class listed as avoidable is not thereby avoidable in every posture.

| # | Class | Emitter | Trigger | Bearer | Party | Avoidable | Layer |
| ---: | --- | --- | --- | --- | --- | --- | --- |
| 1 | 802.11s mesh beacons and peer management | `mac80211`, mesh interface | continuous while the mesh point is up | Wi-Fi mesh | node | only by not using the bearer | 1 |
| 2 | Access point beacons and probe responses | `hostapd` | continuous while the AP is up | Wi-Fi AP | node | only by withdrawing EUD access | 1 |
| 3 | HaLow scanning, probing and reacquisition | HaLow driver | scan and reassociation | HaLow | node | yes | 3 |
| 4 | batman-adv originator messages | `batman-adv` | periodic, `orig_interval` | every enslaved hard interface | node | only by leaving the mesh | 1 |
| 5 | batman-adv gateway announcement | `batman-adv` | while `gw_mode` announces | mesh | node | yes | 1 |
| 6 | Gratuitous ARP on interface bring-up | `batman-adv` | interface bring-up | mesh | node | yes | 1 |
| 7 | DHCP and DNS answers to EUDs | `dnsmasq` | EUD request | Wi-Fi AP | node | only by withdrawing EUD access | 5 |
| 8 | Upstream DNS forwarding | `dnsmasq` | EUD query needing resolution | WAN | node | yes; already decided off under EMCON | 5, 6 |
| 9 | Time synchronisation to an upstream source | `chrony` | periodic poll | WAN or LAN | node | yes, at a stated cost | 5 |
| 10 | Observability and status telemetry export | exporters, status aggregator | periodic | any | node | yes | 5 |
| 11 | Mission service announcements | service plane | service activation | any | node, service | yes | 4 |
| 12 | Periodic TAK position reporting | TAK clients, carried by the TAK service | PLI interval | AP then mesh | EUD originates, mission profile shapes the rate | rate yes; origination not by MULE | 7 origination, 2 and 5 carriage |
| 13 | TAK session keepalive | the TAK client library | periodic while connected | AP then mesh | EUD, service | yes, with a session cost | 5 |
| 14 | Active link probe | link probe | periodic, paced | mesh | node | yes, explicitly | 5 |
| 15 | Linked voice egress from the gateway | RoIP gateway | session or PTT | mesh, external radio | node, service | yes, explicitly | 5 |
| 16 | Amateur-radio automated position or status egress | amateur egress path | periodic when activated | amateur RF | node | yes; disabled by default | 5 |
| 17 | Meshtastic native node announcement and position | Meshtastic radio firmware | periodic, firmware-scheduled | LoRa | **the radio, by design** | see finding 4 | 1 |
| 18 | LoRa mission traffic | Meshtastic service on the host | event and periodic | LoRa | node, service | selectively | 1, 4, 5 |
| 19 | WAN overlay keepalive and passthrough | overlay client | continuous while enabled | WAN | node | yes, explicitly | 6 |
| 20 | WAN tile fetch | map service | on demand | WAN | node, service | yes, explicitly | 6 |
| 21 | EUD radio behaviour | the EUD itself | continuous | the EUD's own radios | EUD | not by MULE | 7 |
| 22 | EUD presence self-publish as an online contact | not implemented in MULE software -- see below | periodic if implemented | any, *"potentially over LoRa"* | node | yes | 4, 5 |

### Notes on individual classes

**1, 2 and 4 -- the advertisement floor.** These cannot be silenced while the
capability they advertise is in use. `FML-ADR-060` records that *"An incident
mesh name is audible in beacons to anyone in range"*. For the access point,
`mule/modes.py` records that `wifi_ap` *"serves end user devices rather than
carrying traffic between nodes"*, so suppressing class 2 withdraws EUD access
rather than trimming overhead. This is finding 2.

**4 -- interval.** `os/config/batman-adv.conf.template` line 87 reads
`orig_interval=TBD`, with *"Originator message interval, ms. Default 1000."*
in a trailing comment. The configured value is `TBD`. 1000 ms is the upstream
default, not a parameter this program has selected, and is not quoted here as
one.

**6 -- a transition emission.** Line 153 reads
`gratuitous_arp_on_bringup=yes`. It fires on bring-up rather than periodically,
which matters because SAD section 23 requires EMCON transitions be *"explicit,
locally indicated, and reversible"*. Entering or leaving EMCON is itself an
event at which this class fires. See finding 5.

**8 -- already decided.** The `GAP-09E` decision packet records no upstream
DNS forwarding under EMCON, so this class has a disposition that predates this
list.

**9 -- the cost is visible, not silent.** `FML-ADR-042` requires a node to
report that its time is not credible. Suppressing class 9 therefore surfaces
rather than degrading quietly, which makes it a posture choice a reader can
audit.

**12 and 13 -- periodicity is the exposure, and suppression costs
addressability.** `services/tak/README.md` states the problem plainly:
*"**Position reporting is periodic**, which is exactly the regularity that
makes traffic analysis easy on encrypted traffic"*, and that the service
*"generates it continuously by design"*. CONOPS 22 records that *"mission
profiles may adjust PLI intervals and other update rates"*, so the rate is
within program control even though the origination is the EUD's. The cost of
suppressing announcement is concrete: `test/bench/eud-chat-id-capture.py`
records that *"A TAK server streams nothing to a client that has not announced
itself"*. A posture that forbids announcement forbids addressability with it.

**14 and 15 -- these already carry an explicit suppression requirement.** The
link probe policy in `docs/ROADMAP-DEV.md` states the probe *"**shall** be
suppressed under EMCON"*. CONOPS 50.12's fifth `[SHALL]` states that *"EMCON
shall be able to suppress linked voice without disabling the operator's
physical radio"*. The second clause sets the boundary: what is suppressible is
the MULE's gateway path, not the operator's handheld.

**16 -- gated before EMCON reaches it.** CONOPS 46 makes amateur egress
*"disabled by default"*, requires a mission profile and an authorized control
operator to activate it, and separately requires that *"Automated position or
status egress shall not mirror TAK update rates onto shared amateur
networks"*. A posture forbidding it reinforces a default rather than
overriding one.

**17 -- the radio is autonomous by design.** SAD section 7.2: *"The Meshtastic
radio continues its own mesh behavior independently of the service
processor."* `os/config/meshtasticd.conf.template` sets no node-announcement,
position or telemetry interval, so the firmware's native schedule applies
unaltered. Native node-announcement traffic of this kind has been observed on
real hardware under `TBR-NET-02`, and `docs/bench-hardware-bringup.md` makes a
node-information exchange a bring-up step. Those are existing observations
under other trades, cited here to establish that the class is real rather than
hypothetical. Finding 4 covers what follows for suppression.

**19 and 20 -- the cleanest existing mappings.** `FML-ADR-068` states *"The
path **shall** remain subject to the node's emission posture: a mission or
EMCON profile that forbids emission on the WAN bearer suppresses the
passthrough"*. `FML-ADR-072` states *"**EMCON-gated.** The fetch emits DNS and
HTTPS, so it **shall** be suppressed under an EMCON or radio-silent mode,
exactly as `FML-ADR-068` suppresses the WAN passthrough on an
emission-forbidding profile, reading the `FML-ADR-046` EMCON state."* Both
classes were mapped by accepted decisions before this list existed.

**21 -- the limit of MULE's reach.** CONOPS 71 opens *"MULE EMCON does not help
if connected EUDs continue unnecessary wireless behavior"* and assigns the
remedy to *"Operator procedures and mobile-device hardening guidance"*
covering Wi-Fi probing, unnecessary Bluetooth, unused radios, unnecessary
background network traffic, device lock and unattended device access. That is
layer 7, and SAD section 23's disclaimer applies directly.

**22 -- the class the gate requires, stated carefully.** `CCR-06`
(`ACCEPTED` 2026-09-29) distinguished *"seeding a **static roster** (Part A)
versus **broadcasting live presence** (periodic situational-awareness,
potentially over LoRa) so the EUD shows as an online contact"*. It accepted
Part A, recorded in `FML-ADR-087`, and routed Part B here, stating that
*"Auto-presence is a transmission class `TBR-EMCON-01` must be able to
suppress"*. `FML-ADR-087` confirms the split: *"Presence self-publish -- a
separate, transmitting behaviour -- is deliberately **not** in this
decision"*.

The class is therefore listed, as the closure evidence requires, and the
accurate entry is narrow: **no MULE software or configuration implements a
periodic broadcast of an EUD as an online contact.** That is not a claim that
the system emits no presence-like traffic. It does, and those emissions are
separate classes above -- periodic TAK position reporting (12), session
keepalive (13), and the Meshtastic radio's native node announcement (17).
Bench harnesses under `test/bench/` also emit presence events deliberately, as
bench instruments rather than product behaviour.

Were class 22 implemented, its emitter would be the MULE's own enrollment or
trust path rather than the EUD -- `CCR-06` describes *"Auto-publishing every
EUD's presence"* as a system behaviour. That is why it maps to layers 4 and 5
and **not** to layer 7: a MULE service announcing an EUD's liveness is service
announcement behaviour, which the node controls. The constraint it was routed
under is CONOPS section 11's `[SHALL]` that *"Service activation shall not
create externally observable behavior that directly and unnecessarily reveals
privileged-user login, leadership presence, or command structure"*.

## Classes a posture cannot sensibly class as avoidable

Classing everything avoidable would make the list useless, and CONOPS 50.12
only prohibits originating what a posture **has** classed avoidable. These are
avoidable only by surrendering the capability that depends on them:

- **1 and 4** -- silencing the mesh advertisement means not having a mesh.
- **2 and 7** -- silencing the access point, or refusing DHCP and DNS, means
  EUDs cannot attach or be addressed. `mule/modes.py` describes CONOPS 50.9's
  ISOLATED state as *"an access point still serving with no inter-node bearer
  linked"*, so local EUD service is expected to survive states in which
  inter-node bearers do not.
- **12 and 13** -- suppressing announcement costs addressability, per the note
  above.

CONOPS 50.12's own framing supports treating these as bearer and capability
decisions rather than per-message ones: its listed potential behaviours include
*"disabling unnecessary high-rate bearers"* and *"receive-dominant operation
where technically feasible"*.

## Not in scope

**Indicator lights are not transmissions.** CONOPS 65 requires that *"Status
illumination shall be suppressible to off"* and that the design *"avoid
uncontrolled always-on indicator lights"*, calling it *"a BOM and
component-selection constraint as well as a software behavior"*. That is a
real signature concern with its own binding text and its own standing risk row
in the SAD, but `FML-REQ-049` binds origination of a **transmission**, and an
indicator is not one. Excluded here rather than renamed as a gap.

**What a radio can physically be made to do is `TBR-RF-02`'s.** Its option
axes include transmit suppression and duty-cycle limits.
`mission/profiles/README.md` and `mission/schema/mission-package.schema.json`
both point there for enforcement, and that pointer is correct: *which*
transmissions a posture classes avoidable is this trade; *what a radio can be
made to do about it* is that one.

## Findings

**1. The layer set in SAD section 23 is complete for the classes identified.**
Every class above maps to at least one of the seven layers. No class lacks a
layer, so no new suppression layer is proposed and **no ADR accompanies this
artifact**. `TBR-EMCON-01`'s Options section anticipated a new layer only *"if
a class has no existing layer"*, and that condition is not met. The gaps found
are in mechanism, not in the layer set, and findings 3 and 4 record them as
such.

**2. Layer 1 suppression is bearer-granular, not emission-granular.** For
classes 1, 2 and 4 the only available action is to stop using the bearer. A
posture can decide *whether a bearer is in use*; it cannot keep a bearer
usable and silence the advertisement that makes it usable. A posture
definition implying otherwise for these classes would be undeliverable.

**3. A suppression pattern is already selected for service-level classes; the
wiring is not.** `FML-ADR-068` and `FML-ADR-072` both require specific
emitters to be gated by *"reading the `FML-ADR-046` EMCON state"*, and
`FML-ADR-072` explicitly leaves *"the emission-gate wiring"* to
implementation. So classes 19 and 20 have an accepted pattern and no
mechanism. Separately, `os/config/nftables.conf.template` carries an `output`
chain with `policy drop` whose comment states the reason is EMCON, that *"a
service that transmits despite the profile is a safety problem, not a bug"*,
and that *"Whether this is enforceable here or belongs elsewhere is TBD"*.
That is the only location named as a candidate for a **general** enforcement
point, and `mission/profiles/README.md` says it may be the wrong place.
Nothing in `mule/` or `os/` acts on the emission posture beyond reporting it.

**4. The sharpest gap is class 17, and the architecture creates it
deliberately.** SAD section 7.2 states that *"The Meshtastic radio continues
its own mesh behavior independently of the service processor"*, and adds that
where the hardware has its own controller and native firmware, *"host failure
should not prevent that radio from continuing its native Meshtastic
participation while independently powered"*. That autonomy is a resilience
property for the degraded-communications lifeline. It also means the host has
no identified means of silencing the radio's native node announcement. Layer 1
names the behaviour; what is absent is any mechanism by which a posture
reaches an autonomously scheduled emitter. Recorded as a named gap for the
owner, with the observation that suppressing it and preserving the LoRa
lifeline may be in tension: SAD section 8 gives priority to *preserving LoRa
degraded communications*, and `TBR-RF-02` owns what that radio can be made to
do.

**5. No layer names the LoRa plane explicitly.** Layer 3 is the only
bearer-named layer and it names HaLow. Classes 17 and 18 fall under the
bearer-unqualified wording of layers 1, 4 and 5 rather than a layer of their
own, and no SAD section assigns LoRa suppression anywhere else. Layer 2 does
not reach them: CONOPS 35 makes LoRa the *"degraded low-bandwidth"* bearer,
the opposite of a high-rate bearer. Stating layer 1's bearer scope explicitly
would remove the ambiguity. Offered as a drafting observation on section 23,
not as a claim that the classes are unsuppressible in principle.

**6. A posture needs a transition rule, not only a class list.** Class 6 fires
on interface bring-up, and SAD section 23 requires transitions be *"explicit,
locally indicated, and reversible"*. Entering and leaving EMCON are themselves
emission events for at least one class. Named here, not resolved.

## What this does not establish

- It does not show that any transmission was absent, or present. No radio was
  involved in producing it.
- It does not select an enforcement mechanism. Findings 3 and 4 state the open
  questions. `mission/profiles/README.md` already records the `emcon` profile
  as *"`TBD`, and the least well understood of the three"*, and this artifact
  does not change that.
- It does not define postures. Which classes a given posture forbids is a
  mission-profile decision travelling in the SAD section 19.2 package.
- It does not satisfy Stage 10. The trade is explicit that a software digital
  twin of what the node reports *"is not this gate"*.
- It does not close `TBR-EMCON-01`.

## Sources

- `docs/conops/FML-MULE-CONOPS-v1.2.txt` sections 11, 19, 21, 22, 34, 35, 46,
  50.12, 65, 71, 72, and the Stage 10 criteria.
- `docs/architecture/FML-MULE-SAD-v0.32.md` sections 7.2, 8, 19.2 and 23, and
  the `C50-01` traceability row.
- `docs/verification/requirements.md`, `FML-REQ-049`.
- `docs/change-requests/CCR-06-eud-roster-and-contact-seeding.md`, Part B.
- `FML-ADR-042`, `FML-ADR-046`, `FML-ADR-060`, `FML-ADR-068`, `FML-ADR-072`,
  `FML-ADR-087`, and the `GAP-09E` decision packet.
- `os/config/batman-adv.conf.template`, `os/config/nftables.conf.template`,
  `os/config/chrony.conf.template`, `os/config/meshtasticd.conf.template`.
- `mule/modes.py`, `services/tak/README.md`,
  `test/bench/eud-chat-id-capture.py`, `docs/bench-hardware-bringup.md`.
- `docs/ROADMAP-DEV.md`, for the active link probe policy.

The argument that a transmitting node cannot be made undiscoverable is made in
`THREAT_MODEL.md`, `mission/profiles/README.md` and SAD section 23. It is cited
rather than restated.
