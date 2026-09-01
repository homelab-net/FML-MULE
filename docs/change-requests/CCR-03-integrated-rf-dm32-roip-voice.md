# CCR-03 Integrated RF: the DM-32UV and audio/PTT Radio-over-IP become baseline voice

**Type:** CONOPS change request
**Status:** `OPEN`
**Target version:** CONOPS **v1.1** (minor increment, stakeholder re-approval)
**Sections affected:** 1, 3, 5, 8, 9, 39, 40, 41, 42, 43, 44, 45 (primary), 46,
50, 53, 54, 78, 79, 81, 83, 85
**Raised by:** received architecture-change handoff, 2026-08-31
**Source:** `CCR-03-source-dm32-roip-handoff.txt`, committed verbatim
**Blocks:** any `VOICE` trade area, any voice ADR, and a voice gateway service
**Does not block:** the rest of the program; committing this record adopts
nothing, exactly as `CCR-01` and `CCR-02` are `OPEN` and unadopted

## Statement

A handoff proposes making handheld voice a first-class MULE capability: the
Baofeng DM-32UV as the group-standard external radio, and an **audio/PTT-level**
Radio-over-IP gateway that carries a gateway radio's audio and PTT state between
MULEs as IP, so teams on different RF channels can be linked without the MULE
understanding DMR. Direct radio-to-radio operation is preserved when the MULE is
absent.

It is correctly scoped as a **minor CONOPS increment**, not a point revision: it
adds `[SHALL]` statements (Section 45.8 failback, the voice-authorization
separation), adds Section 79 success criteria, touches a Section 78 stage, and
**removes remote PTT/audio bridging from the Section 81 stretch/exclusion
wording**. CONOPS Section 86 makes each of those a `v1.1` change requiring
stakeholder re-approval. This record receives the proposal; it does not approve
it.

The companion hardware package is
`hardware/prototype/BOM-v0.4-DM32-RoIP-handoff.txt`, received the same day.

## Blocking issue that must be resolved before any of it enters the register

**The four proposed ADR numbers are already assigned and in force.** The handoff
names `FML-ADR-051` through `FML-ADR-054` for the voice decisions. Every one is
taken:

| Proposed | Actually assigned to |
| --- | --- |
| `FML-ADR-051` | node decision logic lives in an importable package |
| `FML-ADR-052` | boundary between decision functions and blocked services |
| `FML-ADR-053` | **BATMAN-IV is the baseline routing algorithm** |
| `FML-ADR-054` | **bridge loop avoidance disabled on the mesh** (superseded by `FML-ADR-056`, retained permanently) |

Identifiers here are permanent and never reused, and two of these are load-
bearing across `mule/`, the config templates and the benches. **Resolved
2026-08-31: the four voice decisions were allocated fresh**, never reusing
051-054:

| Handoff number | Deconflicted number | Subject |
| --- | --- | --- |
| `FML-ADR-051` | `FML-ADR-064` | DM-32UV is the group-standard external voice radio |
| `FML-ADR-052` | `FML-ADR-065` | audio and PTT over IP, not native DMR |
| `FML-ADR-053` | `FML-ADR-066` | integrated dedicated gateway radio per node |
| `FML-ADR-054` | `FML-ADR-067` | an operator receives linked voice through exactly one audio path |

All four are `PROPOSED` and carry no weight until this change request is
approved. `FML-ADR-067` in particular states the single-audio-egress invariant
as a baseline requirement: an operator's headset receives a linked session
through exactly one path. The `VOICE` trade area exists as `TBR-VOICE-01` (the
handoff's `TBR-VOICE-SW-01`, renamed to the repository's `TBR-<AREA>-<NN>`
convention).

## What it changes, so the change is scoped rather than open-ended

**New `[SHALL]` statements**, at least: local RF works without the MULE
(45.1/45.8); loss of the IP path returns users to local RF (45.8, the new
failback SHALL); voice-group authorization is distinct from network
reachability (45.1, Section 43); the amateur profile gates RoIP egress off by
default (Section 46).

**New Section 79 success criteria**, seven, from the handoff's Section 8-R:
integration does not break local RF; voice crosses the local IP path; voice
crosses Tailscale; different local frequencies are permitted; WAN loss preserves
local RF; no persistent loop/self-keying; the user interface stays radio/PTT.

**A Section 81 change:** remote PTT/audio bridging moves from stretch to
baseline. Native DMR/MMDVM routing stays out of baseline, correctly.

**A new functional element:** a Voice/RF Gateway service under the network
plane, explicitly *not* a general-purpose telephony platform.

## How it interacts with decisions made the week it arrived

- **`FML-ADR-061` (keyed mesh, automatic merge).** The handoff's requirement
  that voice-group authorization be distinct from network reachability is the
  same shape as the finding that being on the keyed mesh is not admission. Being
  reachable must not be being in the voice group. The handoff states the
  principle; nothing implements it, and the credential to express it has the
  distribution gap `TBR-SEC-01` records.
- **`FML-ADR-063` (per-deployment prefix, silent uplink overlap).** RoIP is a
  real-time flow across the same bearer whose addressing is per-deployment and
  whose uplink can silently steal part of the mesh. The Tailscale and WAN voice
  paths in the handoff ride exactly the routes the route-stealing analysis
  covers.
- **QoS (handoff Section 40, 12).** Preferring voice over bulk is new traffic
  policy on a bearer whose behaviour under load is untested (`TBR-RF-01`), and it
  competes with the routing daemon `services/catalog/` warns is starved first.
- **`services/catalog/` and `FML-ADR-029`.** The gateway is a service. The
  catalog is empty by decision; adding it is a catalog entry, a Quadlet, and the
  `TBR-VOICE-01` selection trade (thin native vs SvxLink vs AllStar) before
  anything runs. It also adds a worst-case contributor to `TBR-COMP-01`, which
  the handoff correctly folds into that trade rather than asserting the 4 GB CM4
  suffices.

## What is sound

The audio/PTT gateway over native DMR tunnelling keeps the MULE out of the RF-
protocol business, consistent with `docs/NON-GOALS.md`. The radio-primary
headset rule (`FML-ADR-067`) and the
double-audio prohibition are good human-factors calls that prevent echo and keep
the MULE off the critical path for ordinary voice. Local-first degradation is
stated as a `[SHALL]`, not a hope. No frequencies are hard-coded; regulatory
configuration is pushed to the mission plan and codeplug, consistent with
`regions/` and `REGULATORY.md`. Amateur governance is explicitly preserved and
default-off.

## Unresolved, and returned explicitly as the handoff's own Section 18 asks

- **RX activity detection is a `TBR` in the handoff itself:** hardware COS/COR
  versus validated squelch, with a warning not to assume VOX is adequate. This
  is a real hardware-interface unknown, not a software preference.
- **Whether RoIP is in MULE v1 at all**, or a v-next capability, is the Program
  Owner's scope call and is not decided by receiving the document.
- **The ADR renumbering and `VOICE` trade creation** are mechanical but must
  happen before any voice decision is cited anywhere.
- **RF coexistence** of a transmitting gateway radio inside the enclosure with
  HaLow and LoRa in the same band is `TBR-RF-02`/`FML-ADR-027` territory and the
  BOM's GATE VOICE-01 and VOICE-09 are where it gets measured.

## Next actions if the Program Owner accepts the direction

1. Approve or defer the `v1.1` scope. Committing this record does neither.
2. The four voice ADRs (`FML-ADR-064`-`067`, `PROPOSED`) and the `VOICE` trade
   area (`TBR-VOICE-01`) are allocated. On approval they move from `PROPOSED`
   to a selected status.
3. Fold the seven new Section 79 criteria into
   `docs/verification/requirements.md` and the ITEP, since that file tracks the
   Section 79 set.
4. Run the BOM's GATE VOICE-01 to close the DM-32 electrical-interface unknown
   before committing to the DigiRig path.
