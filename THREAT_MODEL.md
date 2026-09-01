# Threat model

Status: **draft, UNVERIFIED.** This document states design intent for a system
that is not built. Nothing here has been tested, and no claim in it should be
relied on operationally. It exists early because a threat model written after
implementation tends to describe what was built rather than what was needed.

Scope: the MULE appliance, the network plane it forms, the mission-service
plane it hosts, and the identity material it carries. Out of scope: the
organisational practices of any group that operates it, and the end-user
devices attached to it beyond their interaction with MULE.

## Assumed operating context

- Volunteer disaster response, training exercises, and communications
  experimentation. Unclassified throughout.
- Deployed by people who are not security professionals, in a hurry, tired,
  often at night, sometimes in weather.
- No internet, no central server, no parent infrastructure. Local-first is a
  requirement, so any control that depends on reachback is not a control.
- A small number of nodes, operated by a group whose members mostly know each
  other, in a physical environment they do not control.

## Assets

Ordered by what their loss actually costs, which is not the same as ordering by
what is technically interesting.

1. **Participant location.** Position and location history of volunteers, and
   through them of the people they are assisting. This is the asset whose
   compromise causes direct physical harm to a person. Position reporting is a
   core function, so this asset is generated continuously by design.
2. **Participant identity and association.** Who is a member, who deployed,
   who was where with whom. Damaging even when position is not disclosed.
3. **Mission data.** Situational-awareness content: markers, tasking, notes,
   imagery, casualty or subject information where a group's procedures put it
   on the system.
4. **Credentials and key material.** Node identity keys, mission trust material,
   service credentials, access-point secrets. Compromise converts an outsider
   into an authenticated insider.
5. **The nodes themselves.** Physical hardware, scarce and expensive for a
   volunteer group, and a source of assets 1 through 4 when taken.
6. **Availability of the link.** Degraded communications during an incident is
   an operational harm even with no confidentiality loss.

## Adversaries assumed

- **The opportunist.** Someone who finds or steals a node, or wanders into
  radio range with commodity equipment. No specific interest in the group.
  Most likely adversary by a wide margin.
- **The curious local.** A scanner hobbyist, a journalist, or a neighbour who
  notices unusual emissions and investigates. Capable of passive observation
  and basic direction finding.
- **The motivated individual.** Someone with a specific interest in a
  participant or in the operation: a domestic abuser looking for a person, a
  subject of a search who does not want to be found, someone with a grievance
  against the organisation. Willing to spend money and time, and the adversary
  whose success does the most harm.
- **The insider.** A credentialed participant, current or former, who is
  careless, disgruntled, or compromised. Holds valid credentials by definition.
- **A capable state or commercial signals-intelligence capability.** Explicitly
  **out of scope as a defended-against adversary.** A volunteer project cannot
  defend against one, and pretending otherwise would mislead operators. Stated
  so nobody assumes coverage that does not exist.

## What the design is intended to defend against

Each of these is intent. None is demonstrated.

- **Passive interception of mission content in transit** across the IP mesh and
  the access point, by transport confidentiality between authenticated peers.
  **Program Owner principle, 2026-08-31: anything that leaves a MULE is
  encrypted.** That is the consolidation of mechanisms already chosen -- the
  keyed 802.11s mesh (`FML-ADR-061`, WPA2/SAE), the EUD access point (WPA2, not
  open), the WAN overlay (`FML-ADR-039`, Tailscale), browser and API services
  (`services/ingress/` TLS), and RoIP voice as an encrypted IP session (below).
  The rule is stated as a boundary: at the edge of a node, in the clear is a
  defect. It does not extend to an external RF bearer that regulation forbids
  encrypting -- see the RoIP note.
- **Unauthorised participation**, by requiring node and participant admission
  through a program PKI and a mission trust layer, so an unadmitted device
  cannot join the operational domain and read or inject mission data.
- **Injection or spoofing of position and mission data** by an unadmitted party,
  through the same admission mechanism plus origin authentication.
- **Trust validation against a bad clock.** A node whose time is not credible
  refuses to validate credentials rather than accepting expired or
  not-yet-valid material. Fail closed, not open. See `FML-ADR-042`,
  `TBR-TIME-01`.
- **Silent compromise of the software supply chain**, by pinning package
  manifests, referencing container images by immutable digest, promoting
  kernel, driver, firmware, and userspace as one tested set, and signing image
  artifacts. See `FML-ADR-040` and `os/release/`.
- **Persistent compromise through a bad update**, by an A/B slot scheme with a
  bootable known-good rollback path independent of the active root. See
  `FML-ADR-041`, `TBR-REC-01`.
- **Casual data recovery from a lost node**, by encrypting data at rest. The
  strength of this depends entirely on how the volume is unlocked, which is
  unsolved; see below.
- **Lateral movement from a compromised service**, by running services rootless
  under Podman with per-service isolation. See `FML-ADR-029`.

## What the design does not defend against

This section matters more than the one above it. An operator who reads only one
part of this document should read this part.

### The device has a detectable radio signature

MULE is a **multi-bearer device by design**: sub-GHz HaLow, conventional Wi-Fi
for an inter-node bearer, a separate access point, and LoRa. Several distinct
emitters, in several bands, transmitting concurrently, in a pattern that is not
what ordinary consumer equipment produces.

Consequences that no amount of encryption changes:

- **Presence is detectable.** Something is transmitting there.
- **The emissions pattern is distinctive.** The specific combination of bearers
  is close to a fingerprint for this class of device, and it will become more
  so as the design is published and copied.
- **Location is obtainable.** Direction finding on sub-GHz and 2.4/5 GHz is
  within reach of a determined individual with commodity hardware and public
  software. Multiple emitters make it easier, not harder.
- **Traffic analysis works on encrypted traffic.** Volume, timing, and
  addressing reveal activity level, node count, and often which node is the
  coordination point. Position reporting is periodic, which is exactly the
  regularity that makes analysis easy.
- **Operating implies emitting.** An EMCON profile exists in `mission/profiles/`
  precisely because the only reliable way to not be detected is to not
  transmit. What that profile can actually achieve is `TBD`.

If a participant's safety depends on their location not being discoverable,
this system does not provide that, and no configuration of it will.

### Peer traffic is visible to authenticated participants

The operational domain is a **shared trust environment**. A participant admitted
to a mission can see the position and mission traffic of other participants on
that mission. That is the function of the system, not a flaw in it.

Therefore:

- **There is no meaningful compartmentation between admitted participants.**
  Admission is close to all-or-nothing at the mission level.
- **An insider is inside.** A credentialed participant who is careless,
  compromised, or acting in bad faith has legitimate access to assets 1, 2, and
  3, and no technical control here prevents that. Vetting whom you admit is an
  organisational control, and it is the primary one.
- **Credential revocation in a disconnected network is hard** and its
  effectiveness is `TBD`. Assume a revoked credential remains usable on a
  partition that has not learned of the revocation.
- Whether any mission-critical state can be compartmented at all is an open
  trade: `TBR-TAK-01`.

### A client certificate is weaker than it looks, in the software we selected

**Added 2026-08-31**, measured against `OpenTAKServer` 1.7.13, which
`FML-ADR-032` selects. Three properties compound, and none is a MULE defect:
they are what the chosen implementation does by default.

- **A certificate authenticates on possession of public data.** The Marti API
  path does not perform a TLS handshake. It reads a certificate from an
  `X-Ssl-Cert` header and checks that it chains to the server CA, so it proves
  the certificate is valid and **not** that the sender holds the private key. A
  certificate is public. `services/ingress/` now records what the reverse proxy
  must therefore guarantee.
- **Issued certificates are valid for ten years.** `OTS_CA_EXPIRATION_TIME`
  defaults to 3650 days and applies to client certificates. CONOPS plans
  volunteer-owned EUDs, and a decade outlasts the volunteer, the device, and any
  plausible interval before one is lost or handed on.
- **Revocation is not consulted on that path.** A CRL is maintained on disk and
  the verification store is loaded with the CA and nothing else, so a revoked
  certificate verifies exactly as an unrevoked one does.

The bullet above says to assume a revoked credential remains usable on a
partition that has not learned of the revocation. **On this path it remains
usable on a node that has learned**, because the node does not look.

The SSL streaming port performs a real handshake and was not tested; this
applies to the API path. See
`docs/evidence/TBR-TAK-01/2026-08-31-certificate-enrollment.md`. Nothing here is
a decision about what MULE will do instead, which is `FML-ADR-038`,
`TBR-ID-01` and `services/ingress/`.

### Physical capture is an expected condition

A node will be lost, stolen, left behind in a hurry, or taken. Plan for it as a
normal event, not an edge case.

- **Assume a captured node yields its keys.** No secure element, no tamper
  response, and no anti-removal design has been selected, and none is assumed.
  Data-at-rest encryption protects a node that is powered off; a node captured
  while running is captured unlocked.
- **Unattended unlock is unsolved.** A field device that boots without a human
  present must obtain its unlock secret from somewhere. Every local answer
  reduces to storing the key near the data. `TBR-SEC-01` is open, and until it
  closes, treat at-rest encryption as protecting against a casual finder and
  not against a motivated one.
- **Capture is a credential compromise for the whole mission**, because a
  captured node holds material that admits it to the operational domain. The
  recovery procedure for that is `TBD`.
- **Capture discloses history**, not only current state: cached position
  history, mission data, and logs.
- Operationally: a lost node is reported immediately, and mission credentials
  are rotated. That procedure does not exist yet and belongs in the CONOPS.

### Other explicit non-defences

- **No defence against jamming or denial of service.** Any of the bearers can
  be denied by a transmitter in band. The PACE structure and the independent
  LoRa plane are mitigations at the operational level, not technical defences.
  Voice and manual fallback remain necessary; see `docs/NON-GOALS.md`.
- **No defence against a capable state adversary**, as stated above.
- **No defence against a compromised end-user device.** A phone running the
  situational-awareness client, already compromised, sees everything the
  participant sees. MULE cannot detect or contain that.
- **No defence against the operator's own configuration errors**, beyond
  validation of the mission package schema.
- **No protection for amateur-band operation.** Where a builder enables it,
  encryption is unlawful in many jurisdictions, so traffic on that bearer is
  in the clear by regulatory requirement. See `REGULATORY.md`.
- **No assurance of the upstream supply chain.** Pinning gives reproducibility
  and a reviewable change, not trustworthiness of the pinned artifact.

## Residual risk, stated plainly

A participant carrying a MULE node can be located by a motivated individual
with commodity equipment. A node that is captured discloses its mission's
credentials and history. An admitted insider sees everything on the mission.
None of these has a technical fix within this program's scope, and each is a
condition an operating group must decide it can accept before deploying.

## Open questions feeding this model

| Question | Trade |
| --- | --- |
| Mission-critical state boundary and compartmentation | `TBR-TAK-01` |
| Protected storage unlock for an unattended device | `TBR-SEC-01` |
| Clock holdover, skew tolerance, fail-closed behaviour | `TBR-TIME-01` |
| Sub-GHz coexistence and emissions control | `TBR-RF-02` |
| Rollback implementation and its trust properties | `TBR-REC-01` |
| Client-certificate authentication, lifetime and revocation on the API path | `TBR-ID-01`, `services/ingress/` |

## Review

This document is reviewed when any trade in the table above closes, when a new
bearer or service is added, and at each qualification stage. Changes that alter
what the system defends against require an ADR.
