# How a node addresses the EUDs behind it

**Trade:** `TBR-NET-02`.
**Date:** 2026-08-29.
**Produced by:** analysis against controlling documents, the Meshtastic
protobuf definitions, and two probes that run in CI. No hardware.
**Status of this artifact:** `UNVERIFIED`. It is reasoning plus two
`SIMULATED` results, not a field result.

## What this is and what it is not

`TBR-NET-02` asks how a node decides which of the four to eight EUDs behind it
a message is for. This is the specification its closure evidence calls for: the
mapping table, a worked trace per plane, the operator-facing statement of what
is lost at the plane boundary, the tag encoding costed in bytes, and the
unresolved-recipient rule.

**It does not close the trade.** Two reasons, both written down in advance.
Every trade owner in this repository is `TBD-SRR`, and a trade closes when a
**named** owner accepts the evidence. And the empirical half does not exist:
nothing anywhere exercises an EUD behind one MULE reaching an EUD behind
another. `test/flatsat/` builds exactly one node.

## Finding 1: the IP plane does not need this trade for delivery

An earlier draft of the trade said it did. That was wrong and is corrected
here.

SAD section 4.3 bridges local EUD access into the BATMAN domain, so every EUD
behind every MULE is in one flat layer 2 domain with its own MAC and address.
`FML-ADR-056` keeps that domain flat and constrains only what else may share
the bridge. An EUD reaching another EUD two MULEs away is therefore a layer 2
path that `batman-adv` forwards, with ARP resolving across the mesh.

That ARP resolution is not assumed. `.github/workflows/mesh-probe.yml` deletes
every neighbour cache and asserts that a three-node mesh re-resolves unaided,
then routes two hops.

So on IP there is no recipient to look up. **What the IP plane still lacks is
not routing but identity**: which *user* a device belongs to, for policy and
for gateway-mediated traffic. That is `TBR-ID-01`, and `mule/admission.py`
already records that no identity, credential or enrollment exists anywhere yet.

## Finding 2: the identifier must be deployment-scoped, not node-local

Option B in the trade proposed a **node-local** handle. That does not work, and
the reason is worth stating because it is not obvious.

For MULE A to address a person behind MULE B, the name it puts on the wire must
be resolvable **at B**. A handle allocated locally by A means nothing at B. Any
identifier that crosses the mesh is therefore deployment-scoped by necessity.

This is not a new mechanism. `AGENTS.md` already requires that a value a
deployment could vary is read from the region profile, mission package or
service catalog rather than being a literal. A member identifier is exactly
such a value, and the mission package is where it belongs.

**The mission package has no participant roster today.** Its `network` object
carries `mesh_id`, `local_domain`, `address_prefix` and `ap_ssid`, and nothing
enumerates members. The schema sets `additionalProperties: false`, so adding
one is a deliberate schema change rather than an incidental field. That change
is named here and **not made**, because the trade has no owner and implementing
ahead of closure is the failure this repository has already recorded.

## The mapping table

| Namespace | Carries | Maps to the member identifier by |
| --- | --- | --- |
| CoT (ATAK) | UID and callsign | Callsign is already the deployment-scoped human name. The mission package binds callsign to member identifier. |
| Browser services | Whatever `TBR-ID-01` selects; `FML-ADR-037` prefers application-native RBAC | Deferred. Browser services are S2 and shed before LoRa carries traffic; see finding 4. |
| Meshtastic | Node number, and `Data.source` / `Data.dest` inside the payload | Node number identifies the **MULE**, never a person. The member identifier rides as an application tag inside the payload. |

Resolution is local at the receiving node: member identifier to the device that
member is currently associated from. That binding is the part `TBR-ID-01`
replaces later.

## Worked traces

**IP, EUD to EUD across two MULEs.** No resolution step exists.

```text
EUD-A1 --wifi--> AP-A --br-field--> bat0-A ==mesh== bat0-B --br-field--> AP-B --wifi--> EUD-B3
```

One layer 2 domain end to end. ARP resolves across the mesh, `batman-adv`
forwards the frame. The node performs no lookup because there is nothing to
look up. `FML-ADR-057` still applies: this traffic transits the node and may be
observed, but nothing about delivery depends on that.

**LoRa, outbound.** EUD-A1 sends a CoT message addressed to a callsign.

1. The gateway on MULE A receives it over IP, per `FML-ADR-048`.
2. It maps callsign to member identifier using the mission package.
3. It encodes the member identifier as a tag in the Meshtastic payload.
4. The packet leaves MULE A's Meshtastic node addressed to MULE B's node.

**LoRa, inbound.** MULE B receives that packet.

1. `Data.dest` names MULE B's node. The packet is for this MULE.
2. The gateway reads the member tag from the payload.
3. It resolves the member identifier to a currently associated device.
4. It delivers over IP to that device only.

Step 3 is where an unresolved recipient arises, and step 4 is where the
fail-closed rule below applies.

## The tag encoding, costed

`DATA_PAYLOAD_LEN` is **233 bytes**, from the Meshtastic protobuf `Constants`
enum. Every tag byte is airtime on the bearer CONOPS section 50.8 makes the
lifeline, so the encoding is a real decision rather than a formality.

**Amended 2026-08-30: the usable payload is 231 bytes, not 233.** The protobuf
constant is 233 and that is correct as a constant, but a 233-byte payload does
not arrive, and neither does 232. 231 does. Measured on two `meshtasticd`
instances; see `2026-08-30-tag-payload-measurement.md` for the sweep and the
configuration.

The table below is unchanged, because the constant is what a reader will find
in the protobuf and the percentages move by less than a tenth of a point. What
changes is the **usable message length**, which is 230 bytes beside a one-byte
tag rather than 232.

**The sender does not report the failure.** `sendData` accepts an oversized
payload and returns without error; the packet simply never appears at the other
node. An implementation that fills the documented 233 bytes would therefore
drop messages **silently**, on the lifeline bearer. Whatever writes the tag
**shall** refuse a payload over 231 bytes rather than hand it to a sender that
accepts and discards it.

Why two bytes are unavailable is not established. Protobuf field overhead is
the obvious candidate and it was not measured, so it is not claimed here.

| Encoding | Bytes | Members addressable | Share of 233 |
| --- | ---: | ---: | ---: |
| One-byte index | 1 | 255 | 0.43% |
| Two-byte index | 2 | 65,535 | 0.86% |
| Callsign string, short | ~8 | unbounded | 3.4% |
| UUID string | 36 | unbounded | 15.5% |

**A one-byte index is sufficient and is what this specification selects.**
CONOPS section 6 plans four to eight EUDs per MULE. A twenty-MULE deployment is
therefore around 160 members, inside 255. A two-byte index is available if a
deployment ever exceeds that, at a cost that is still under one percent.

A UUID costs fifteen percent of every packet to carry a name nobody reads, on
the bearer with the least capacity. It is listed to be ruled out.

The index is allocated per deployment in the mission package. It is not a
durable identity: `THREAT_MODEL.md` records that an identifier derived from a
durable node identity is itself a durable identifier visible to anyone
observing traffic, and a per-deployment index avoids that.

## What an operator loses at the plane boundary

Written for the operator rather than the protocol, because this is the part
that will surprise someone in a car park.

**On IP, every teammate is individually reachable.** Direct messages work,
each person appears separately, and the MULE they are behind is invisible.

**On LoRa, only the MULE is reachable.** A MULE has one LoRa chain by CONOPS
section 36, so it is one Meshtastic node. Without the tag specified above, a
six-person team behind one MULE is **one address**: a message can be sent to
that MULE, not to a person behind it.

So at CONOPS section 50.8 `LOW-BANDWIDTH`, person-to-person messaging degrades
to MULE-to-MULE unless the tag is implemented. Someone who could message one
teammate at 09:00 cannot at 09:05, and until this specification is implemented
nothing tells them so.

This is a capability cliff at a degradation step, not a defect. It should
appear in Team Lead training material and in the quick-reference, on the same
grounds CONOPS section 23 requires its peer-visibility rule to appear there.

## The unresolved-recipient rule

**A node that cannot resolve the intended member shall not deliver to every
EUD.** Delivering to everyone is the natural implementation, it looks like
helpfulness, and CONOPS section 23 makes it wrong: role-restricted information
shall use an authenticated service rather than relying on peer distribution
behaviour.

The rule, in order:

1. If the mission package names a **default recipient** for the deployment,
   deliver there and mark the message as having been redirected.
2. Otherwise, do not deliver. Record the event where node status will surface
   it.

Both branches fail closed relative to broadcasting. The first exists because
silently dropping a message on the lifeline bearer is its own failure, and a
team lead receiving a message meant for someone whose device is off is a better
outcome than nobody receiving it. Which branch a deployment gets is a mission
package decision, not a node decision.

## What changes when `TBR-ID-01` closes, and what does not

This is the condition the closure gate adds, and it is the reason to run this
trade first.

**Changes:** the binding from a member identifier to a device. Today that can
only be association, which is a claim about a MAC address and should be
labelled as such. After `TBR-ID-01` it becomes an authenticated identity.

**Does not change:** the member identifier itself, its allocation in the
mission package, the tag encoding and its byte cost, the resolution path
through the gateway, the fail-closed rule, or any of the traces above.

Addressing and authentication are therefore separable, and this specification
separates them. Work done against it now does not need rebuilding when
`TBR-ID-01` closes.

## What would falsify this

Three things, named so a reviewer can look for them rather than take the
document's word.

1. **If EUD-to-EUD across two MULEs does not actually work at layer 2**, finding
   1 collapses and the IP plane needs this trade after all. Nothing has
   demonstrated that path. The mesh probe proves MULE to MULE; the EUD leg is
   untested and is the obvious next test.
2. **If a deployment needs more than 255 members**, the one-byte index is wrong.
   Two bytes is the answer and costs 0.86%.
3. **If the gateway cannot carry an application tag** in the payload alongside
   the message, the encoding above is unimplementable and option D, one radio
   per EUD, becomes the serious alternative. `FML-ADR-048` fixes the gateway
   order and none of the three has been exercised.

   **Partly tested, 2026-08-30, and it did not fire.** A one-byte tag followed
   by the message crossed between two `meshtasticd` nodes byte-intact, so the
   *transport* carries it. See `2026-08-30-tag-payload-measurement.md`.

   **The gateway half remains untested and is the half this item names.** A
   gateway that parses CoT and re-emits a canned Meshtastic message would drop
   the tag whatever the transport can carry. None of `FML-ADR-048`'s three has
   been exercised. Do not read the transport result as closing this.
