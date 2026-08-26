# Glossary

Terms and acronyms used in this repository. Written for a reader who has not
worked in this domain, because a stranger reading this repository is the case
it is designed for.

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
