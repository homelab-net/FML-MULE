# CCR-01 Operating mode structure and transition criteria

**Type:** CONOPS change request
**Status:** `OPEN`
**Section affected:** CONOPS v1.01 section 50, Operating modes
**Raised by:** node mode determination work, `FML-ADR-052` condition 2
**Revised:** 2026-08-28, folding in Program Owner direction on axis structure
**Blocks:** `mule/modes.py`, and any status surface that reports a mode
**Does not block:** the rest of `mule/`, the SAD, the TRD or prototype work

## Statement

CONOPS section 50 names thirteen operating modes. It does not say whether a node
may be in more than one at a time, and it gives no entry or exit criteria for
any of them.

Both gaps have to be closed before a node can determine its own mode, because
code that reports a mode has answered both questions whether or not anyone
wrote the answers down.

## The first gap: are the thirteen modes concurrent?

They are, and the CONOPS demonstrates it rather than states it. Three passages
are decisive.

**Section 51 permits exercise control to "force degradation states."** EXERCISE
is section 50.13. A degradation state is section 50.7, 50.8 or 50.9. A function
operating under one mode cannot force a state belonging to a set that excludes
it. EXERCISE is therefore concurrent with degradation by the CONOPS's own
design.

**Section 50.12 requires "an EMCON entry procedure … and a re-entry
procedure."** Entry and re-entry are relative to whatever the node was doing
before. That is the shape of a posture that is turned on and off over a
continuing operating state, not a slot in an exclusive enumeration.

**Section 50.10 FIELD-ECONOMY and section 50.7 DEGRADED-IP both reduce
service.** One reduces to preserve energy, the other because IP capacity is
constrained. The causes are independent and can hold simultaneously. A node low
on battery in a congested band is in both, and a taxonomy forcing a choice
would make it report the wrong reason for the reduction an operator sees.

Nothing in the document contradicts this. Section 53.1 requires a qualified user
to "recognize degraded mode," singular, which is training language about a
capability, not a statement that only one mode is ever active. Section 0.3 lists
"EMCON mode (50.12); EXERCISE mode (50.13)" as separately named modes without
placing them in a common exclusive set.

## Proposed text, part A: mode axes

Editorial. Adds no `[SHALL]`, alters no section 79 criterion, moves no section
81 boundary. A **point revision, `v1.02`**, under section 86.

Insert as a new section 50.0, before 50.1:

> The modes below are not a single exclusive set. A node is in exactly one mode
> on each of the axes named here, concurrently. A mode name identifies its axis
> and its value on that axis.
>
> | Axis | Values | Section |
> | --- | --- | --- |
> | Environment | LAB, FIELD | 50.1 |
> | Deployment context | STANDALONE, NETWORKED | 50.2-50.3 |
> | Shared TAK service | SERVERLESS-TAK, SERVER-ENHANCED | 50.4-50.5 |
> | WAN reachability | (none), WAN-ENHANCED | 50.6 |
> | Bearer capability | (nominal), DEGRADED-IP, LOW-BANDWIDTH, ISOLATED | 50.7-50.9 |
> | Energy posture | (nominal), FIELD-ECONOMY | 50.10 |
> | Lifecycle posture | (operational), TRANSPORT / SECURE | 50.11 |
> | Emission posture | (normal), EMCON / SILENT | 50.12 |
> | Data marking | (live), EXERCISE | 50.13 |
>
> A parenthesised value is the unremarkable state of that axis. It is named so
> that every axis always has a value, and is not reported to the operator.
>
> The names FIELD-STANDALONE and FIELD-NETWORKED in sections 50.2 and 50.3 are
> compounds of the environment and deployment-context axes. They are retained as
> aliases for FIELD with STANDALONE and FIELD with NETWORKED respectively.

The bearer-capability axis is ordered. The other axes are unordered.

### The bearer-capability axis and the section 5.5 ladder

Also editorial, and part of the same point revision. Insert after the section
50.0 table:

> The bearer-capability axis is the graceful-degradation ladder of section 5.5,
> named in mode terms. The two lists are not the same length and the
> correspondence is stated here so that it is not inferred:
>
> | Section 5.5 rung | Bearer function | Axis value |
> | --- | --- | --- |
> | High-throughput IP | Conventional Wi-Fi mesh | (nominal) |
> | Range-oriented IP | Sub-GHz long-range IP | DEGRADED-IP |
> | LoRa / Meshtastic | LoRa | LOW-BANDWIDTH |
> | Local digital operation | End user access point only | ISOLATED |
> | Analog / manual PACE | None | not a node state |
>
> The lowest rung of section 5.5 is a team procedure, not a condition a node
> reports. A node that has reached it has no bearer to report through.
>
> A node's axis value is bounded by the highest-capability bearer that has
> formed a link. Link quality may place it lower; bearer association alone can
> never place it higher.

Section 50.9 corroborates the bottom node-reportable rung directly: ISOLATED is
where "the team retains local EUD and node capability only", which is the
condition of an access point still serving with no inter-node bearer linked.

This clarification is what allows a node to determine the axis today. Bearer
association is already observable; the link-quality refinement in the last
sentence needs thresholds from `TBR-RF-01` and `TBR-RF-02` and readings that do
not yet exist, and until those arrive a node reports the bound rather than
claiming precision it does not have.

Splitting environment from deployment context is what allows the LAB values the
CONOPS already implies. Section 50.1 lists interoperability testing among LAB
activities, and interoperability testing requires more than one node, so a bench
node must be able to be both LAB and NETWORKED. A single three-valued axis
cannot express that.

## Proposed text, part B: transition criteria

Adds binding clauses. A **minor version increment, `v1.1`, with stakeholder
re-approval**, under section 86.

Part A can be approved without part B. Doing so is worth considering: part A is
what a node needs in order to report a mode honestly, and part B is what it
needs in order to change one. Approving part A alone unblocks the reporting work
while the criteria are still being measured.

Insert as a new section 50.14:

> [SHALL] Each mode axis shall define, for every value it may take, the
> observations that cause entry and the observations that cause exit.
>
> [SHALL] Every automatic transition shall be hysteretic: the observation that
> causes entry to a more degraded value shall differ from the observation that
> causes return, and the difference shall be recorded.
>
> [SHALL] A node shall not require operator action to change any automatically
> determined axis, and shall present the current value of any axis in a degraded
> or deliberate state to the operator without the operator requesting it.
>
> [SHALL] The lifecycle, emission and data-marking axes shall be entered and
> exited only by authorized action, never automatically.

The fourth clause reflects what the CONOPS already implies. Section 50.12
requires an authorized override for EMCON; TRANSPORT / SECURE describes a node
being prepared for movement, which is a human act; and section 50.13 requires
exercise data to be distinguishable from live data, which a node cannot decide
for itself.

The threshold **values** the first two clauses require are deliberately not
proposed here. They are measurements nobody has taken. `TBR-RF-01` and
`TBR-RF-02` govern the bearer-capability axis, `TBR-PWR-01` the energy axis.
This change request asks for the criteria to exist and to be hysteretic; the
trades supply the numbers.

## The three ambiguities, and how each was settled

The first draft of this change request raised three questions and assumed an
answer to each. All three are now settled, from two different sources, and the
distinction between those sources matters at signature.

**1. Does section 50.2's "No WAN, NOMAD, or home dependency" couple the
deployment-context and WAN axes?** No, and this was never ambiguous. The
document answers it three times, and the first draft simply had not read far
enough.

- Section 41, WAN independence: "WAN is optional", and `[SHALL]` loss of WAN
  shall not remove local EUD access, local mesh, peer ATAK, local S0 and S1
  services, or LoRa/Meshtastic degraded communications.
- Section 5.4, Local first: `[SHALL]` required field capability shall not depend
  on Internet, cellular, Starlink, an overlay, home connectivity, NOMAD or a
  central TAK Server. "WAN enhances the local environment but does not create
  it."
- Section 2: `[SHALL]` the system shall be local-first and WAN-independent.

WAN is an enhancer program-wide. Section 50.2's clause describes the situation
in which a node finds itself, not a constraint one axis places on another. The
axes are independent, and no capability may be predicated on the WAN axis
holding any particular value.

**2. Are SERVER-ENHANCED and WAN-ENHANCED independent?** Yes. Program Owner
direction, 2026-08-28:

- SERVER-ENHANCED means a MULE or another mesh device is running a shared TAK
  service, which enables additional capability.
- WAN-ENHANCED means the internet is reachable **in the mesh**, which enables
  further additional capability.

Both may hold at once, and neither implies the other. This has a consequence for
what a node observes, recorded here because it is easy to get backwards: the WAN
axis is a property of the **mesh**, not of this node's own uplink. Section 42
makes any standard MULE capable of the authorized local WAN-gateway role, with
one active gateway at a time in the initial baseline. So a node with no uplink of
its own is WAN-ENHANCED when an authorized gateway is reachable through the mesh.
The observation is reachability, not possession.

**3. Is LAB a deployment context or a lifecycle posture?** Neither. Program
Owner direction, 2026-08-28: LAB is an **environment**, a test bench. It is
therefore its own axis, opposed to FIELD, and the table above reflects that.

### What this means at signature

Answer 1 is a reading of the baseline and changes nothing. Answers 2 and 3 are
program direction recorded in conversation, not yet in a signed document. They
are the reason the axis table takes the shape it does, and a signatory who
disagrees with either should expect the table to change rather than the code to
absorb the difference quietly.

`mule/modes.py` cites this file at each point where it relies on answer 2 or 3.

## Downstream documents affected

| Document | Effect |
| --- | --- |
| CONOPS sections 50.2, 50.3 | Mode names shortened; old names retained as aliases |
| SAD section 22 | The operator status surface reports axes, not one mode |
| `docs/verification/requirements.md` | Part B adds four binding clauses to decompose |
| `test/stages/stage-10-exercise-and-aar/` | Exercise concurrency becomes explicit |
| `mule/modes.py` | Implements part A; part B's criteria arrive with the trades |
| `services/status-aggregator/README.md` | Blocked; inherits the axis vocabulary |

## Verification impact against section 85

Part A is editorial and adds no verification obligation.

Part B adds four `[SHALL]` clauses. Hysteresis and automatic transition are
exercised on the flat-sat without hardware, and are `SIMULATED` there. The
threshold values are not verifiable until `TBR-RF-01`, `TBR-RF-02` and
`TBR-PWR-01` close and a node exists to measure, which is stage 4 and stage 7
under section 78.

## Approval

Not approved. No signature has been sought.

CONOPS section 87 records the baseline as pending stakeholder signature, so this
change request is raised against an unsigned baseline and can be folded into
that signature rather than processed as a post-signature change.
