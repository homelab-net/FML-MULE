---
requirements:
  - id: FML-REQ-001
    source: CONOPS 79.1
    modal: shall
    text: "Field nodes use one approved common hardware and software baseline per block."
    allocation: FML-ADR-021
    stage: STAGE-01
  - id: FML-REQ-002
    source: CONOPS 79.2
    modal: shall
    text: "A standard node supports the representative 4-8 EUD team."
    allocation: FML-ADR-024
    stage: STAGE-02
  - id: FML-REQ-003
    source: CONOPS 79.3
    modal: shall
    text: "Authorized users receive functions based on identity, role, scope, and mission profile."
    allocation: FML-ADR-037
    stage: STAGE-01
  - id: FML-REQ-004
    source: CONOPS 79.4
    modal: shall
    text: "Alternate leadership sustains team-level capability after loss of a leader or leader EUD."
    allocation: FML-ADR-035
    stage: STAGE-01
  - id: FML-REQ-005
    source: CONOPS 79.5
    modal: shall
    text: "Users can recover onto replacement EUDs without routine WAN dependence."
    allocation: FML-ADR-036
    stage: STAGE-09
  - id: FML-REQ-006
    source: CONOPS 79.6
    modal: shall
    text: "Mission-scoped credentials fail safe by expiry if revocation cannot reach a partition."
    allocation: FML-ADR-047
    stage: STAGE-09
  - id: FML-REQ-007
    source: CONOPS 79.7
    modal: shall
    text: "Peer ATAK remains usable without TAK Server within validated scale limits."
    allocation: FML-ADR-024
    stage: STAGE-02
  - id: FML-REQ-008
    source: CONOPS 79.8
    modal: shall
    text: "Shared TAK service can recover onto another eligible host without ordinary EUD reconfiguration."
    allocation: FML-ADR-031
    stage: STAGE-05
  - id: FML-REQ-009
    source: CONOPS 79.9
    modal: shall
    text: "A recovered TAK host indicates whether state is authoritative, degraded, or incomplete."
    allocation: FML-ADR-049
    stage: STAGE-05
  - id: FML-REQ-010
    source: CONOPS 79.10
    modal: shall
    text: "Split-brain is prevented or safely contained."
    allocation: TBR-HA-01
    stage: STAGE-05
  - id: FML-REQ-011
    source: CONOPS 79.11
    modal: shall
    text: "High-throughput IP supports bandwidth-intensive functions when available."
    allocation: FML-ADR-025
    stage: STAGE-04
  - id: FML-REQ-012
    source: CONOPS 79.12
    modal: shall
    text: "HaLow supports range-oriented IP."
    allocation: FML-ADR-024
    stage: STAGE-02
  - id: FML-REQ-013
    source: CONOPS 79.13
    modal: shall
    text: "LoRa preserves approved degraded communications."
    allocation: FML-ADR-026
    stage: STAGE-03
  - id: FML-REQ-014
    source: CONOPS 79.14
    modal: shall
    text: "LoRa remains usable while HaLow performs controlled recovery behavior."
    allocation: FML-ADR-027
    stage: STAGE-03
  - id: FML-REQ-015
    source: CONOPS 79.15
    modal: shall
    text: "RF coexistence and regulatory compliance are validated for the assembled device."
    allocation: FML-ADR-027
    stage: STAGE-03
  - id: FML-REQ-016
    source: CONOPS 79.16
    modal: shall
    text: "WAN remains optional."
    allocation: FML-ADR-082
    stage: STAGE-06
  - id: FML-REQ-017
    source: CONOPS 79.17
    modal: shall
    text: "Under the default posture an EUD does not join the WAN overlay. An EUD admitted to the overlay reaches only its assigned MULE's approved remote-EUD ingress and is not placed on the local RF mesh. The assigned MULE remains the security and routing boundary past that ingress, including where it reaches an approved mission service for that EUD over the local RF mesh."
    allocation: FML-ADR-082
    stage: STAGE-06
  - id: FML-REQ-018
    source: CONOPS 79.18
    modal: shall
    text: "Remote teams can reach approved field services when WAN exists."
    allocation: FML-ADR-082
    stage: STAGE-06
  - id: FML-REQ-019
    source: CONOPS 79.19
    modal: shall
    text: "Unauthorized home, private, and administrative infrastructure remains inaccessible."
    allocation: FML-ADR-082
    stage: STAGE-06
  - id: FML-REQ-020
    source: CONOPS 79.20
    modal: shall
    text: "External antennas are field replaceable using approved spare configurations."
    allocation: TBR-CARRIER-01
    stage: STAGE-08
  - id: FML-REQ-021
    source: CONOPS 79.21
    modal: shall
    text: "Mission battery planning covers more than one pack and includes cold-weather effects."
    allocation: TBR-PWR-01
    stage: STAGE-07
  - id: FML-REQ-022
    source: CONOPS 79.22
    modal: shall
    text: "Users are informed when hosting services materially affects runtime."
    allocation: FML-ADR-046
    stage: STAGE-01
  - id: FML-REQ-023
    source: CONOPS 79.23
    modal: shall
    text: "Exercise data is distinguishable from live incident data."
    allocation: FML-ADR-046
    stage: STAGE-10
  - id: FML-REQ-024
    source: CONOPS 79.24
    modal: shall
    text: "AAR and accountability data can be exported and purged according to retention policy."
    allocation: FML-ADR-050
    stage: STAGE-10
  - id: FML-REQ-025
    source: CONOPS 79.25
    modal: shall
    text: "EMCON can be deliberately entered and exited."
    allocation: FML-ADR-046
    stage: STAGE-10
  - id: FML-REQ-026
    source: CONOPS 79.26
    modal: shall
    text: "A lost node can be revoked without cooperation from that node."
    allocation: FML-ADR-047
    stage: STAGE-09
  - id: FML-REQ-027
    source: CONOPS 79.27
    modal: shall
    text: "Data at rest is protected according to downstream security requirements."
    allocation: FML-ADR-043
    stage: STAGE-09
  - id: FML-REQ-028
    source: CONOPS 79.28
    modal: shall
    text: "Non-digital PACE is trained and usable."
    allocation: N/A-SAD
    stage: STAGE-10
  - id: FML-REQ-029
    source: CONOPS 79.29
    modal: shall
    text: "Incident information can be handed off to organizations that do not use TAK."
    allocation: FML-ADR-048
    stage: STAGE-11
  - id: FML-REQ-030
    source: CONOPS 79.30
    modal: shall
    text: "Amateur-radio operation is disabled by default and governed by a distinct lawful control role."
    allocation: FML-ADR-048
    stage: STAGE-11
  - id: FML-REQ-031
    source: CONOPS 79.31
    modal: shall
    text: "Field equipment can be operated in gloves, darkness, and representative cold conditions."
    allocation: TBR-CARRIER-01
    stage: STAGE-08
  - id: FML-REQ-032
    source: CONOPS 79.32
    modal: shall
    text: "Every fielded node passes an acceptance test."
    allocation: FML-ADR-040
    stage: STAGE-13
  - id: FML-REQ-033
    source: CONOPS 79.33
    modal: shall
    text: "The program can be maintained by more than one qualified person."
    allocation: N/A-SAD
    stage: STAGE-13
  - id: FML-REQ-034
    source: CONOPS 79.34
    modal: shall
    text: "A mission observation records the time it was observed, its source, and whether it is new, active, stale, expired, merged, or superseded."
    allocation: TBR-OBS-01
    stage: STAGE-01
  - id: FML-REQ-035
    source: CONOPS 79.35
    modal: shall
    text: "A stale or expired mission observation is not presented as current."
    allocation: TBR-OBS-01
    stage: STAGE-01
  - id: FML-REQ-036
    source: CONOPS 79.36
    modal: shall
    text: "Relaying or queuing does not replace the time of observation with the time of delivery."
    allocation: TBR-OBS-01
    stage: STAGE-01
  - id: FML-REQ-037
    source: CONOPS 79.37
    modal: shall
    text: "An expired observation remains history for the mission profile's retention and is not treated as deleted."
    allocation: TBR-OBS-01
    stage: STAGE-01
  - id: FML-REQ-038
    source: CONOPS 79.38
    modal: shall
    text: "Observations of different subjects are not merged, and a possible match is not presented as a confirmed identity."
    allocation: TBR-OBS-01
    stage: STAGE-01
  - id: FML-REQ-039
    source: CONOPS 79.39
    modal: shall
    text: "A link report is not presented as proof of a usable path or as the location of an emitter."
    allocation: TBR-OBS-01
    stage: STAGE-01
  - id: FML-REQ-040
    source: CONOPS 79.40
    modal: shall
    text: "A derived product identifies its source observations and does not replace them, and a model product is labeled as one."
    allocation: TBR-OBS-01
    stage: STAGE-01
  - id: FML-REQ-041
    source: CONOPS 79.41
    modal: shall
    text: "A full local queue records the discard and does not by itself end local participation."
    allocation: TBR-OBS-01
    stage: STAGE-01
  - id: FML-REQ-042
    source: CONOPS 79.42
    modal: shall
    text: "A mission profile can mark a capability required, optional, or off."
    allocation: TBR-SENSE-01
    stage: STAGE-01
  - id: FML-REQ-043
    source: CONOPS 79.43
    modal: shall
    text: "A capability marked off is not tasked."
    allocation: TBR-SENSE-01
    stage: STAGE-01
  - id: FML-REQ-044
    source: CONOPS 79.44
    modal: shall
    text: "Refusal, failure, or absence of an optional capability does not by itself make local mission participation unsuccessful."
    allocation: TBR-SENSE-01
    stage: STAGE-01
  - id: FML-REQ-045
    source: CONOPS 79.45
    modal: shall
    text: "A required capability that is absent is shown as missing."
    allocation: TBR-SENSE-01
    stage: STAGE-01
  - id: FML-REQ-046
    source: CONOPS 79.46
    modal: shall
    text: "Authority to view a product is not authority to task a sensor, and neither is authority to administer a node."
    allocation: FML-ADR-037
    stage: STAGE-09
  - id: FML-REQ-047
    source: CONOPS 79.47
    modal: shall
    text: "A sensor task names the sensor, the duration, and the team scope, ends on those conditions, and yields an observation or a recorded failure."
    allocation: TBR-SENSE-01
    stage: STAGE-09
  - id: FML-REQ-048
    source: CONOPS 79.48
    modal: shall
    text: "A change of permission on a capability is recorded."
    allocation: FML-ADR-037
    stage: STAGE-09
  - id: FML-REQ-049
    source: CONOPS 79.49
    modal: shall
    text: "While EMCON is in effect the system does not originate a transmission the active posture has classed as avoidable."
    allocation: TBR-EMCON-01
    stage: STAGE-10
  - id: FML-REQ-050
    source: CONOPS 79.50
    modal: shall
    text: "EMCON is not reported as measured radio silence."
    allocation: FML-ADR-046
    stage: STAGE-10
  - id: FML-REQ-051
    source: CONOPS 79.51
    modal: shall
    text: "Where reception remains permitted, a prohibition on transmission is not reported as an inability to receive."
    allocation: FML-ADR-046
    stage: STAGE-10
  - id: FML-REQ-052
    source: CONOPS 79.52
    modal: shall
    text: "Integration of the gateway radio does not remove normal local RF use."
    allocation: FML-ADR-064
    stage: STAGE-08
  - id: FML-REQ-053
    source: CONOPS 79.53
    modal: shall
    text: "Linked voice crosses the local IP path between MULEs."
    allocation: FML-ADR-065
    stage: STAGE-04
  - id: FML-REQ-054
    source: CONOPS 79.54
    modal: shall
    text: "Linked voice between authorized MULEs can cross the WAN overlay, and does not require an EUD to join that overlay."
    allocation: FML-ADR-065
    stage: STAGE-06
  - id: FML-REQ-055
    source: CONOPS 79.55
    modal: shall
    text: "Gateway radios are not required to use the same RF frequency."
    allocation: FML-ADR-065
    stage: STAGE-04
  - id: FML-REQ-056
    source: CONOPS 79.56
    modal: shall
    text: "Loss of WAN or of the linked-voice path preserves local and direct RF voice."
    allocation: FML-ADR-067
    stage: STAGE-06
  - id: FML-REQ-057
    source: CONOPS 79.57
    modal: shall
    text: "A linked-voice session does not persist as a loop or a stuck transmission."
    allocation: FML-ADR-067
    stage: STAGE-04
  - id: FML-REQ-058
    source: CONOPS 79.58
    modal: shall
    text: "The ordinary user's voice control remains that user's radio and PTT."
    allocation: FML-ADR-067
    stage: STAGE-08
---

# Requirements

**Generated-from-source, hand-maintained.** This file transcribes the **58
operational success criteria of CONOPS v1.2 section 79** as structured
requirements, with the validating stage taken from the **CONOPS section 85
verification traceability matrix**.

`tools/gen-traceability.sh` reads the frontmatter above and produces
`docs/verification/traceability.md`. `--check` fails the build for any binding
requirement with no allocation or no validating stage.

## Scope, and what this file is not

This is **not** the full requirement set. CONOPS v1.2 carries **185 `[SHALL]`
markers**. SAD v0.32 section 35.1 still traces the v1.1 set. The v1.2 clauses
are not yet transcribed into a SAD. Criteria 34-41 allocate to `TBR-OBS-01`.
A comparison dated 2026-09-24 does not move them: no representation is
selected. Criteria 42-45 and 47 allocate to `TBR-SENSE-01`. Criterion 49 allocates to
`TBR-EMCON-01`. Those trades are open. They are not a selected design.
Criteria 46 and 48 allocate to `FML-ADR-037`. Criteria 50 and 51 allocate to
`FML-ADR-046`. None of criteria 34 through 58 have been run.

That clause-level decomposition lives in **SAD section 35.2** and belongs in the
TRD. It is not duplicated here, because a second hand-maintained copy of a
146-row table is exactly the drift this program's traceability rules exist to
prevent.

What is transcribed here is the **section 79 criteria**, because:

- they are the level at which CONOPS section 85 already assigns a validating
  stage, so the chain is complete without invention;
- there are 58 of them, which is checkable by a second reviewer;
- CONOPS section 85 makes them binding: **every criterion shall have at least
  one validating stage**, and a criterion whose stage is later removed triggers
  a change request under section 86.

## Field meanings

- **`source`** - the CONOPS section 79 criterion number.
- **`modal`** - all 58 are `shall`. Section 85 makes each one verification-bearing.
- **`allocation`** - the architecture element that owns it. Where the SAD marks
  a clause `N/A-SAD` because it is an organizational or training obligation
  rather than a system behaviour, the allocation records that honestly rather
  than inventing a component. An open trade is an owner when the
  mechanism is not selected. `N/A-CONOPS` is not used.
- **`stage`** - the **first** validating stage from CONOPS section 85. Where
  section 85 lists several, the others are recorded in the stage README under
  `test/stages/`.

## Two allocations that are deliberately not components

- **`FML-REQ-028`**, non-digital PACE trained and usable, allocates to
  `N/A-SAD`. CONOPS section 4 makes it an organizational obligation. No system
  change can satisfy it, and pretending otherwise would let the program claim a
  fallback it has not trained.
- **`FML-REQ-033`**, the program maintainable by more than one qualified person,
  likewise. It is verified by inspection at Stage 13, and `MAINTAINERS.md`
  currently records it as unmet.

## Coverage gaps the CONOPS itself records

CONOPS section 85 carries three coverage notes, transcribed here so they are not
lost:

- **Section 23, peer data privacy**, is a training and design rule validated
  indirectly through Stage 10 and the section 53 qualification standards. It has
  **no dedicated criterion**, and the CONOPS recommends considering one in the
  TRD.
- **Section 18, auditability**, has **no section 79 criterion at all**. The
  CONOPS recommends adding a verification requirement in the Security
  Architecture.
- **Section 57, participant notice**, is a policy obligation rather than a
  testable system behaviour, verified by inspection of organizational policy.

These are gaps in the criteria set, not in this transcription. They are listed
so a reader does not assume 58 criteria means complete coverage. Criteria 34
through 58 are accepted text. None of them have been run.

## Verification status

**None of these criteria has been verified.** No stage is defined, no hardware
is selected, and nothing has been measured. The traceability chain is complete
in the sense that every criterion has an allocation and a stage; it says nothing
about whether any of them holds.
