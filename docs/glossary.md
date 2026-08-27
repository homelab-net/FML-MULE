# Glossary

Terms and acronyms used in this repository. Written for a reader who has not
worked in this domain, because a stranger reading this repository is the case
it is designed for.

CONOPS section 0.4 carries the controlling acronym and term list. This glossary
covers it and adds the implementation vocabulary the SAD introduces.

Where a term's meaning within this program differs from its general use, the
program's meaning is stated and the difference is called out.

## Program terms

**FML** - FERAL MULE. The program.

**MULE** - Multi-Bearer Utility Link Equipment. The deliverable: a
standardised, portable, team-level communications and edge-services appliance.

**Node** - one MULE appliance.

**Block** - a qualified hardware configuration. A spare node replaces any node
**within the same block**. Blocks change as components reach end of life, so
the repository holds more than one at a time. See `hardware/README.md`.

**Bearer** - one radio path a node can carry traffic over. MULE has several:
sub-GHz HaLow, conventional Wi-Fi for inter-node traffic, a separate access
point, and LoRa.

**Plane** - a functional layer. The **network plane** moves packets; the
**mission-service plane** runs the applications above it. Both share one
compute element (`FML-ADR-021`).

**Compatibility set** - the kernel, out-of-tree driver, radio firmware and
required userspace, versioned and promoted together and never independently
(`FML-ADR-040`).

**Region** - a regulatory profile: band, channel plan, permitted modules, power
and duty-cycle constraints. An input to configuration generation, never a
constant. See `regions/`.

**Promotion gate** - the checks a candidate compatibility set passes before it
may be deployed. See `os/release/README.md`.

**Cold start drill** - the quarterly exercise in which someone who did not
write the documentation follows it to a working state, and every point of
confusion becomes an issue. See `docs/verification/README.md`.

**T-MBNN** - Team Multi-Bearer Network Node. The legacy working name for MULE,
retained for history only. CONOPS v1.01 renamed the end item.

**NOMAD** - the parent Homelab mobile compute platform. It may host shared field
services, and MULE generalizes the older parent assumption that TAK and
communications-gateway functions run only there. See `PBCR-01`.

**Homelab** - the parent program. MULE is developed as its Phase 6 / WP-07 field
communications subsystem.

**PBCR** - parent-baseline change request. `PBCR-01` is the change from
NOMAD-only TAK and communications allocation to the controlled Field Service
Plane. See `docs/change-requests/`.

**Field Service Plane** - the controlled set of approved hosts that may provide
shared field services: an eligible MULE, NOMAD, a portable field-services host,
or another approved platform.

**S0 / S1 / S2 / S3** - the service criticality classes in CONOPS section 9. S0
core node services remain active whenever the node is operational; S1 local
mission services remain available without external hosts; S2 shared mission
services use shared state; S3 enhanced services are the first stopped under
constraint.

**Service host** - a node currently running an S2 shared service.

**Authoritative state** - a shared service condition in which held mission state
is complete and current enough to be relied on for tasking. A process that
restarted successfully is not thereby authoritative.

**Peer operational domain** - the set of participants reachable by common peer
CoT distribution on a given network. Traffic on it is treated as visible to all
authenticated participants.

**Mission-scoped identity** - a credential issued for a defined mission or
validity window that fails safe by expiry.

**Compatibility set version** - the single identifier naming the kernel, driver,
firmware and userspace a node is running. What makes a field fault report
actionable.

**SRR / PDR / CDR** - system requirements review, preliminary design review,
critical design review. This program is **pre-PDR**; SAD v0.31 is an SRR package
candidate.

**ITEP** - Integrated Test and Evaluation Plan. The next major program-control
document, per SAD section 33.1. Not yet written.

**RTM** - requirements traceability matrix. SAD section 35 is its predecessor.

## Process terms

**ADR** - architecture decision record. A numbered, permanent record of a
decision, its status, consequences and accepted cost. Namespace
`FML-ADR-###`. See `docs/adr/README.md`.

**TBR** - to be resolved. An open engineering question with a stable
identifier, an owner and a closure gate. Namespace `TBR-<AREA>-##`. Marks a
**question**. See `docs/trades/README.md`.

**TBD** - to be determined. Marks an unknown **value**, and always cites the
trade that will supply it. `TBR` is the question, `TBD` is the missing number.

**UNVERIFIED** - status is unknown because nothing has been tested. Used
throughout this repository, deliberately and often.

**Trade** - short for trade study. The analysis behind a `TBR`.

**Closure gate** - the condition, written before the work, under which a trade
is agreed to be answered.

**shall / should / may** - modal verbs used deliberately in
requirement-bearing documents. `shall` is binding and verifiable, `should` is
preferred and waiverable with recorded rationale, `may` is permitted and
creates no obligation. See `CONTRIBUTING.md`.

**PDR** - preliminary design review. A programme milestone at which the design
approach is reviewed before detailed design begins. This program is **pre-PDR**.

**DCO** - Developer Certificate of Origin. The sign-off every commit carries,
asserting the contributor has the right to submit the work.

## Networking and radio

**MANET** - mobile ad hoc network. A network whose nodes route for each other
and which forms without fixed infrastructure.

**HaLow** - the marketing name for IEEE 802.11ah, a sub-GHz Wi-Fi variant
trading throughput for range and penetration. Operates in 902-928 MHz in some
regions and 863-868 MHz in others; the bands are not interchangeable. See
`REGULATORY.md`.

**802.11s** - the IEEE mesh networking amendment to Wi-Fi. Provides mesh
association at layer 2. Used with `batman-adv` in this program
(`FML-ADR-024`).

**batman-adv** - Better Approach To Mobile Ad-hoc Networking, advanced. A
layer 2 mesh routing implementation in the Linux kernel. Routes Ethernet frames
rather than IP packets, so the mesh appears as one flat broadcast domain.

**BATMAN-V** - the fifth routing algorithm version in `batman-adv`, using a
throughput-based metric rather than packet loss. Requires a usable throughput
estimate from the driver; whether the HaLow driver provides one is
`UNVERIFIED`.

**LoRa** - a long-range, low-bandwidth sub-GHz modulation. In MULE it carries
an independent degraded-communications plane, not IP.

**Meshtastic** - an open mesh messaging project built on LoRa. The
low-bandwidth plane's reference implementation.

**AP** - access point. The Wi-Fi function end-user devices associate with.
Treated as a separate logical radio function from the inter-node mesh
(`FML-ADR-045`).

**EUD** - end user device. The phone or tablet an operator carries and
associates with the node's access point.

**EMCON** - emission control. Restricting or ceasing transmission to reduce
detectability. A mission profile in `mission/profiles/`. The only reliable way
not to be detected is not to transmit; see `THREAT_MODEL.md`.

**PACE** - Primary, Alternate, Contingency, Emergency. A communications
planning structure that names what you use when each preceding option fails.
MULE occupies steps within a PACE plan; it does not replace one. See
`docs/NON-GOALS.md`.

**Duty cycle** - the fraction of time a transmitter may occupy a channel. A
regulatory constraint in the European 863-868 MHz sub-bands with no analogue in
the US 902-928 MHz rules.

**Coexistence** - two radios in one enclosure not degrading each other.
`TBR-RF-02`.

**Desense** - desensitization. Reduction in a receiver's sensitivity caused by a
nearby transmitter. The specific mechanism by which HaLow could silently disable
the LoRa fallback.

**OpenMANET** - an OpenWrt-based open firmware project integrating ATAK
multicast behaviour with supported SBC and HaLow configurations. Consumed by
this program as a **reference and configuration source, not production
firmware**; see `FML-ADR-023`.

**openmanetd** - OpenMANET's mesh, topology and configuration API daemon.
Permitted as a prototype and reference telemetry source. Production observability
does not depend on it, and `FML-ADR-027` forbids assuming it provides
deterministic scan or transmit-suppression primitives.

**Morse Micro** - the vendor of the MM6108 and MM8108-class HaLow silicon this
program references. Its Linux driver is out-of-tree, which is the basis of the
kernel lifecycle risk in `FML-ADR-040`.

**UCI** - OpenWrt's Unified Configuration Interface. Production MULE has no UCI
dependency.

**mac80211 / cfg80211** - the Linux kernel's soft-MAC and configuration APIs for
wireless. **nl80211** is the netlink interface user space uses to drive them.

**hostapd** - the Linux access point and 802.1X authenticator daemon. Its
**integrated EAP server** is the preferred initial EUD admission implementation,
so admission does not depend on a central RADIUS server. See `FML-ADR-038`.

**wpa_supplicant** - the Linux station and mesh association daemon.

**PPSK** - per-device pre-shared key. Permitted for prototype work only; it is
not the final authorization architecture.

**EAP-TLS** - certificate-based 802.1X authentication. The production EUD
admission target.

**Split brain** - two hosts each believing they hold authoritative state, having
diverged during a partition. CONOPS section 29 requires preferring loss of
shared-service authority over divergent authoritative databases.

**Fencing** - preventing a host that may still believe it is authoritative from
acting. One of the mechanisms `TBR-HA-01` may select; none is selected yet.

**Modular certification** - a radio module's approval, granted against a
specific test configuration including its antenna. Substituting an antenna can
void it, and compliance of the assembled device remains the builder's
responsibility. See `REGULATORY.md`.

## Situational awareness

**TAK** - Team Awareness Kit. A family of situational-awareness applications
and an associated server ecosystem, originally military, now widely used by
civilian response organisations. MULE hosts a **TAK-compatible** service.

**ATAK** - Android Team Awareness Kit. The Android client.

**CoT** - Cursor on Target. The XML message format TAK clients exchange:
position reports, markers, chat, tasking.

**PLI** - position location information. A participant's reported position.
Generated continuously by design, which makes it the asset most at risk. See
`THREAT_MODEL.md`.

**Marker** - an operator-placed object on the shared map. Whether markers are
durable across node loss is `TBR-TAK-01`.

**OpenTAKServer (OTS)** - the preferred initial TAK-compatible server
implementation; see `FML-ADR-032`. The architecture remains TAK-compatible, not
OpenTAKServer-exclusive.

**PyTAK** - the preferred library for custom CoT clients and translation
gateways; see `FML-ADR-033`.

**DataSync / Mission API** - TAK server functions for shared mission content.
Whether their state is mission-critical is part of `TBR-TAK-01`.

**iTAK / WinTAK** - the iOS and Windows TAK clients.

**Data package** - a bundled set of TAK content distributed to clients.

**AHJ** - authority having jurisdiction.

**COML** - Communications Unit Leader, an ICS position.

**ICS** - Incident Command System. **ICS-205** is its communications plan. MULE
sits alongside it and does not replace it.

**NIFOG** - National Interoperability Field Operations Guide. Appearance of a
frequency in it is not authorization to transmit on it.

**RTO / RPO** - recovery time objective and recovery point objective. The CONOPS
section 27 objective is 60 seconds under healthy IP-mesh conditions, and remains
conditional on `TBR-TAK-01`.

## Platform and build

**BSP** - board support package. The kernel, bootloader, device tree and
vendor-specific pieces that make an operating system run on a particular board.
Hardware-specific, and the half of the two-layer split that may require vendor
patches. See `os/README.md`.

**Out-of-tree** - a kernel module maintained outside the mainline Linux source.
Coupled to a specific kernel version, which is why the compatibility-set rule
exists.

**DKMS** - Dynamic Kernel Module Support. Rebuilds out-of-tree modules
automatically when the kernel changes. Useful, and not a substitute for
promoting the whole set together.

**Device tree overlay** - a fragment describing hardware the base device tree
does not, used to enable a peripheral on a carrier board. See `os/overlays/`.

**Podman** - a container engine that runs containers without a persistent
daemon and, importantly here, without root. See `FML-ADR-029`.

**Quadlet** - a declarative format for describing Podman containers as systemd
units. See `services/quadlets/`.

**Rootless** - running containers as an unprivileged user, so a compromised
service does not begin with root on the host.

**OCI** - Open Container Initiative. The container image and runtime standards.

**Digest** - the immutable content hash identifying an exact container image.
This program references images **by digest, never by tag**, so the reviewed
artifact is the artifact that runs.

**A/B slots** - two root filesystem partitions, one active and one holding the
previous version, permitting rollback. One candidate mechanism for
`FML-ADR-041`; the mechanism is `TBR-REC-01`.

**SBOM** - software bill of materials. A machine-readable inventory of what is
in a build. See `os/release/SBOM.md`.

**RTC** - real-time clock. A battery-backed clock that retains time across
power loss. Mandatory on every node (`FML-ADR-042`).

**Holdover** - how long a clock stays accurate enough without an external time
reference. `TBR-TIME-01`.

**Fixture** - recorded output captured from real hardware, replayed so that
code can be tested without that hardware. Stored in `test/fixtures/` with the
node, date and image build recorded. See `AGENTS.md`.

**Fake** - a stand-in implementation of a hardware interface, used so that
service-plane code runs on an ordinary laptop with no radios present.

**HAProxy** - the preferred initial TCP and HTTP proxy providing stable local
service ingress; see `FML-ADR-031`. **TCP passthrough** is preferred for
end-to-end protected protocols, so the proxy is not a decryption point.

**step-ca** - Smallstep's open-source certificate authority, the preferred
initial PKI; see `FML-ADR-036`.

**chrony** - the NTP implementation disciplining local time; see `FML-ADR-042`.

**LUKS2** - the Linux block-encryption format used for protected mission state;
see `FML-ADR-043`.

**Cryptographic erase** - invalidating key material so encrypted data becomes
unrecoverable, rather than overwriting the medium. The basis of `FML-ADR-044`.

**TPM** - trusted platform module. One candidate for protected storage unlock in
`TBR-SEC-01`; it protects against removing the storage medium, not against a
captured node being powered on.

**RabbitMQ** - the message broker OpenTAKServer uses internally. Treated as
**local transient service infrastructure**, not a field-wide clustered bus.

**cgroups** - the Linux control groups mechanism used to reserve CPU and memory
for the Network Plane so a service-plane peak cannot starve routing.

**nftables** - the Linux firewall framework enforcing policy between the EUD,
service, management, WAN and external-RF domains.

**HIL** - hardware in the loop. The permanent two-node release bench required by
SAD section 20.4, without which `TBR-LINUX-01` cannot close.

**Write amplification** - the multiplication of physical flash writes by
database, journal and telemetry activity. Bounded by design under
`FML-ADR-050`.

**TIME_DEGRADED** - the node state when retained time is implausible or exceeds
the approved skew. Trust validation refuses rather than failing open.

**NO_SAFE_AUTHORITY** - the Status Aggregator reason code when no host can be
shown safe to act as authoritative. SAD section 33.6 defines the operator
action: continue peer ATAK and local PACE, do not treat stale state as
authoritative, and contact the recovery authority.
