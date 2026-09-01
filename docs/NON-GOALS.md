# Non-goals

What this program deliberately does not do, and why.

This list is transcribed from **CONOPS v1.01 section 81, "Initial baseline out of
scope"**, which is controlling. The reasons are drawn from the CONOPS and the
SAD; the exclusions themselves are not this repository's to invent.

## Moving an item off this list

**Items in this list may be promoted only through a change request under CONOPS
section 86.**

That is a higher bar than an ADR. Section 86 requires a change request recording
the section affected, the current text, the proposed text, the operational
rationale, downstream documents affected, verification impact against section
85, and approval. Adding, removing or altering a section 81 scope exclusion
requires a **minor version increment** of the CONOPS (`v1.1`) and **stakeholder
re-approval**.

An architecture decision cannot promote an item off this list on its own.

## The list

### No custom RF modem development

*Reason:* modem design requires expertise, test equipment and regulatory work
this program does not have, and a custom modem would be unusable with equipment
anyone already owns.

### No custom MANET routing protocol

The program uses `batman-adv` in BATMAN-IV mode; see `FML-ADR-053`.

*Reason:* routing protocols are subtle, and their failure modes appear at scale
and under partition, which is exactly where this program cannot test.

### No custom LoRa PHY

*Reason:* CONOPS section 35 scopes LoRa to degraded low-bandwidth
communications. SAD section 7.3 states custom LoRa protocol development is out
of scope; integration uses the Meshtastic supported serial or TCP API.

### No arbitrary encrypted IP over amateur spectrum

*Reason:* encryption, and more broadly any transmission whose purpose is to
obscure meaning, is not permitted on amateur allocations in many jurisdictions.
Amateur egress is disabled by default and governed by CONOPS section 46 and a
distinct control operator role. See `REGULATORY.md`.

### No packet-level multipath striping

*Reason:* CONOPS section 39 requires best-path selection and failover, not
striping of a single flow. `FML-ADR-025` records that striping is not required.

### No unrestricted simultaneous RF transmission

*Reason:* CONOPS section 36 states that unrestricted simultaneous transmission
is not a baseline requirement, because HaLow and LoRa may share the sub-GHz
band. Coexistence may suppress or schedule transmission; see `FML-ADR-027` and
`TBR-RF-02`.

### No competing automatic WAN gateways

*Reason:* CONOPS section 42 permits any standard MULE to assume an authorized
local WAN-gateway role, with **one active gateway at a time** as the initial
baseline. Automatic competing multi-gateway operation is not required for v1.
This is a v1 boundary, not a permanent refusal: `FML-ADR-069` makes pooled
mesh-wide WAN sharing the end-state target, and `TBR-NET-04` holds the
mechanism. What stays out of v1 is the *automatic competing* multi-gateway
operation, not the capability.

### No custom role-encrypted peer multicast

*Reason:* CONOPS section 23 makes the peer operational domain a shared trust
environment: information sent through it is treated as visible to all
authenticated participants. Role-restricted information uses an authenticated
service instead. Building per-role encryption into peer multicast would be a
custom protocol solving a problem the service plane already solves.

### No database replication across every node

*Reason:* SAD section 14.3 establishes an authoritative primary with a **named
recovery-capable standby**, not fleet-wide replication. Replicating to every
node would multiply the write load that `FML-ADR-050` exists to bound, over a
bearer whose capacity is `TBD`.

### No Kubernetes-scale orchestration

Services run as rootless Podman containers under systemd; see `FML-ADR-029` and
`FML-ADR-035`.

*Reason:* a cluster orchestrator solves scheduling across many nodes with spare
capacity. MULE has one compute element per node, a constrained budget, and a
mesh that partitions by design.

### No universal commercial-radio control

*Reason:* CONOPS section 45 reserves an integration boundary for VHF/UHF/HF
radios but states that specific commercial-radio support is not a v1
requirement. Vendor-specific CAT control and broad automation remain downstream
or stretch capabilities. Each integration is a permanent maintenance commitment
against a product line the program does not control.

### No automatic remote PTT or audio bridging

*Reason:* CONOPS section 45 places remote PTT and audio bridging outside v1. The
prototype BOM records team PTT and VoIP as a deferred feature with no BOM
addition, needing software, QoS and test work rather than hardware.

### No custom PCB unless prototype results justify it

*Reason:* a custom carrier is the point at which a volunteer software program
becomes a hardware manufacturing program. SAD section 25.6 defers it, and
`TBR-CARRIER-01` approves one **only if** prototype evidence shows a commercial
carrier or wiring approach materially harms repeatability, fieldability or
safety.

### No replacement of voice or manual PACE

*Reason:* CONOPS section 4 requires organizations to maintain PACE procedures
that do not depend on MULE, and requires training periods in which MULE is
deliberately unavailable. CONOPS section 32 states MULE is a data capability
that does not by itself satisfy a voice requirement. A group that has replaced
its fallback with a device has no fallback.

### No universal interoperability with every public-safety system

*Reason:* CONOPS section 47 states the objective is not universal protocol
compatibility but providing information in a form useful to the supported
incident organization. Interoperability with a public-safety system is an
organizational and regulatory arrangement, not a shippable capability. CONOPS
section 48 adds that no public-safety or interoperability frequency is presumed
authorized merely because it appears in a reference document.

## Architecture-level exclusions

SAD section 32 additionally records that the architecture **does not require**
OpenWrt in production, a hypervisor, a proprietary service mesh, a new TAK
protocol, a custom PKI, EUD Tailscale membership, Patroni or etcd specifically,
or two general-purpose compute boards.

These are architecture consequences rather than CONOPS scope exclusions. They
change through a superseding ADR, not a CONOPS change request. The dual-board
architecture in particular is a retained **FALLBACK**, not an exclusion; see
`FML-ADR-021` and SAD section 2.3.

## Related

Ideas worth remembering but not scheduled go in `docs/parking-lot.md`. Recording
an idea there is not adopting it, and an item that conflicts with this list still
requires a CONOPS change request to move.
