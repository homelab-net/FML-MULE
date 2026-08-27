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
    allocation: FML-ADR-039
    stage: STAGE-06
  - id: FML-REQ-017
    source: CONOPS 79.17
    modal: shall
    text: "MULE remains the WAN-overlay boundary for EUDs."
    allocation: FML-ADR-039
    stage: STAGE-06
  - id: FML-REQ-018
    source: CONOPS 79.18
    modal: shall
    text: "Remote teams can reach approved field services when WAN exists."
    allocation: FML-ADR-039
    stage: STAGE-06
  - id: FML-REQ-019
    source: CONOPS 79.19
    modal: shall
    text: "Unauthorized home, private, and administrative infrastructure remains inaccessible."
    allocation: FML-ADR-039
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
---

# Requirements

**Generated-from-source, hand-maintained.** This file transcribes the **33
operational success criteria of CONOPS v1.01 section 79** as structured
requirements, with the validating stage taken from the **CONOPS section 85
verification traceability matrix**.

`tools/gen-traceability.sh` reads the frontmatter above and produces
`docs/verification/traceability.md`. `--check` fails the build for any binding
requirement with no allocation or no validating stage.

## Scope, and what this file is not

This is **not** the full requirement set. CONOPS v1.01 carries **145 `[SHALL]`
markers**, of which SAD section 35.1 traces **140** as system, operational or
policy clauses and handles 4 as document governance.

That clause-level decomposition lives in **SAD section 35.2** and belongs in the
TRD. It is not duplicated here, because a second hand-maintained copy of a
140-row table is exactly the drift this program's traceability rules exist to
prevent.

What is transcribed here is the **section 79 criteria**, because:

- they are the level at which CONOPS section 85 already assigns a validating
  stage, so the chain is complete without invention;
- there are 33 of them, which is checkable by a second reviewer;
- CONOPS section 85 makes them binding: **every criterion shall have at least
  one validating stage**, and a criterion whose stage is later removed triggers
  a change request under section 86.

## Field meanings

- **`source`** - the CONOPS section 79 criterion number.
- **`modal`** - all 33 are `shall`. Section 85 makes each one verification-bearing.
- **`allocation`** - the architecture element that owns it. Where the SAD marks
  a clause `N/A-SAD` because it is an organizational or training obligation
  rather than a system behaviour, the allocation records that honestly rather
  than inventing a component.
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
so a reader does not assume 33 criteria means complete coverage.

## Verification status

**None of these criteria has been verified.** No stage is defined, no hardware
is selected, and nothing has been measured. The traceability chain is complete
in the sense that every criterion has an allocation and a stage; it says nothing
about whether any of them holds.
