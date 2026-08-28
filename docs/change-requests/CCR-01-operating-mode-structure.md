# CCR-01 Operating mode structure and transition criteria

**Type:** CONOPS change request
**Status:** `OPEN`
**Section affected:** CONOPS v1.01 section 50, Operating modes
**Raised by:** node mode determination work, `FML-ADR-052` condition 2
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
> | Deployment context | LAB, FIELD-STANDALONE, FIELD-NETWORKED | 50.1-50.3 |
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

The bearer-capability axis is ordered, and is the degradation ladder CONOPS
section 5.5 describes. The other axes are unordered.

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

## Questions this change request cannot answer

Three ambiguities in the current text need the signatories, not an editor.

1. **Section 50.2 FIELD-STANDALONE says "No WAN, NOMAD, or home dependency."**
   That constrains the WAN axis from inside a deployment-context value. Either
   FIELD-STANDALONE means "no inter-MULE network" and the WAN clause is
   descriptive of the common case, or the two axes are coupled. Part A assumes
   the former.
2. **Whether SERVER-ENHANCED and WAN-ENHANCED are independent.** A node with a
   local shared TAK service and an approved WAN path appears to be both. Part A
   assumes they are separate axes.
3. **Whether LAB is a deployment context or a lifecycle posture.** Section 50.1
   describes activities rather than a network condition. Part A places it with
   FIELD-STANDALONE and FIELD-NETWORKED because those three answer "where is
   this node and what is it connected to."

Each assumption is recorded in `mule/modes.py` as a comment citing this file, so
that a different answer is a findable change rather than a rediscovery.

## Downstream documents affected

| Document | Effect |
| --- | --- |
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
