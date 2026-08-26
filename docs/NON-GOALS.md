# Non-goals

What this program deliberately does not do, and why.

Scope creep is one of the most likely causes of failure for a volunteer
hardware program, and it does not arrive as a proposal to double the scope. It
arrives one reasonable-sounding item at a time, each individually defensible.
This list is the defence.

**Moving an item off this list requires an ADR.** Not a discussion, not a pull
request that quietly adds the capability: an ADR, with a decision, a status,
consequences, and an accepted cost. That is a deliberately high bar, and it is
meant to be.

Items here are not judgements that the thing is worthless. Several are
excellent ideas that belong to a different program, or to this one much later.
Where an idea is worth remembering without being scheduled, it goes in
`docs/parking-lot.md` instead.

## The list

### No custom radio physical layer

The program uses standardised, commercially available radio technologies:
IEEE 802.11ah, conventional IEEE 802.11, and LoRa. It does not design a
modulation, a framing scheme, or a physical layer.

*Reason:* physical layer design requires expertise, test equipment and
regulatory work that this program does not have, and a custom layer would be
unusable with any equipment anyone already owns.

### No custom routing protocol

The program uses `batman-adv` in BATMAN-V mode (`FML-ADR-024`). It does not
write a routing protocol, and it does not fork one to add a metric.

*Reason:* routing protocols are subtle, and their failure modes appear at scale
and under partition, which is exactly where this program cannot test. Existing
protocols have absorbed years of that experience.

### No cluster orchestration

Services run as rootless Podman containers under systemd (`FML-ADR-029`). The
program does not run Kubernetes, Nomad, Swarm, or any equivalent.

*Reason:* a cluster orchestrator solves scheduling across many nodes with
spare capacity. MULE has one compute element per node (`FML-ADR-021`), a
constrained budget, and a mesh that partitions by design. The orchestrator
would consume the resources it was meant to manage.

### No universal commercial-radio control

The program does not attempt to control, program or interoperate with the
general population of commercial land mobile radios.

*Reason:* the space is vendor-specific, largely proprietary, and effectively
unbounded. Each integration is a permanent maintenance commitment against a
product line the program does not control.

### No replacement for voice or manual fallback procedures

MULE is one step in a PACE structure. It does not replace voice communications,
and it does not replace the manual procedures a group falls back to when
everything electronic has failed.

*Reason:* an operational one, not a technical one. A group that has replaced
its fallback procedures with a device has no fallback. This is also a safety
matter; see `SAFETY.md`.

### No universal public-safety interoperability

The program does not attempt to be a general bridge between volunteer groups
and public-safety communications systems.

*Reason:* interoperability with a public-safety system is an organisational and
regulatory arrangement, negotiated with the agency holding the licence, not a
technical capability that can be shipped. See `REGULATORY.md`. Appearance in a
national channel plan is not authorisation.

### No certified product

The program does not produce a certified, warranted product, and does not
pursue product safety certification, environmental qualification, or
independent security evaluation.

*Reason:* stated plainly in `SAFETY.md` and `SECURITY.md`. A builder assumes
the risk. Implying otherwise would be the most consequential dishonesty this
repository could commit.

### No defence against a capable state adversary

Explicitly out of scope as a defended-against threat. See `THREAT_MODEL.md`.

*Reason:* a volunteer program cannot achieve it, and claiming coverage that
does not exist would put operators at risk in a way that no technical failure
here could match.

### No offensive or interference capability

The program does not build jamming, direction-finding for targeting, traffic
interception, or any capability whose purpose is to degrade someone else's
communications.

*Reason:* out of scope, unlawful in most jurisdictions, and incompatible with
the volunteer disaster-response context the program exists to serve.

### No hosted or cloud dependency

The system is local-first and remains useful with no internet, no central
server, and no parent infrastructure. The program does not build a hosted
service that deployments depend on.

*Reason:* a hosted dependency is a single point of failure outside the
operator's control, in exactly the conditions the equipment exists for. It is
also an ongoing cost and an ongoing liability for whoever runs it.

## Adding to this list

Adding a non-goal is cheaper than removing one, and it is encouraged. If the
program has decided not to do something and the decision is not written down,
it will be relitigated. Add the item, give it a one-line reason, and note where
the exclusion came from.

Removing an item requires an ADR. See above.
