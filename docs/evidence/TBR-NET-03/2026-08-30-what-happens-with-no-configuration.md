# What two unconfigured nodes do, and what LoRa does not have

**Trade:** `TBR-NET-03`.
**Date:** 2026-08-30.
**Taken by:** Cameron Zobrist, on the lab development machine.
**Status of this artifact:** `SIMULATED` for the IPv6 result. The LoRa finding
is read from the Meshtastic firmware source, retrieved 2026-08-30, and is
`UNVERIFIED` on hardware: no radio was involved and no packet was sent.

## The question

`2026-08-30-liaison-routing-exercise.md` and the `TBR-NET-01` artifacts all
configure addressing before asking anything. None of them asks what a node does
when nothing has been configured, and none of them looks at the LoRa bearer at
all.

## Unconfigured IPv6 already works, and cannot collide

Two `batman-adv` interfaces, brought up with no address assigned and no
configuration of any kind:

```text
node 1 bat0 : inet6 fe80::a8c2:3aff:fe0f:6f8e/64 scope link proto kernel_ll
node 2 bat0 : inet6 fe80::4c59:ecff:fee3:6716/64 scope link proto kernel_ll

ping6 fe80::4c59:ecff:fee3:6716%bat0
  2 packets transmitted, 2 received, 0% packet loss
```

The kernel assigns an IPv6 link-local address to every interface, derived from
its MAC, and two nodes that have never met reach each other immediately.

**These cannot collide.** A link-local address is unique by construction within
a link, so two deployments merging on one mesh have working addressing whatever
they each chose for IPv4. That is the opposite of the situation in
`docs/evidence/TBR-NET-01/2026-08-30-collision-exercise.md`.

### This corrects a claim made in `TBR-NET-03`

The trade says every convergence mechanism except deferral forces
`address_prefix` to be per-deployment, because two deployments holding one
prefix cannot be routed between or even named. **Link-local is a counterexample
and the trade does not consider it.** It needs no prefix agreement at all.

The correction is narrower than it first looks, and the limits are real:

- **Link-local is not routable.** It is on-link only, so it does nothing for the
  liaison option, where the whole mechanism is forwarding between two separate
  layer 2 domains. It applies only where two deployments share one mesh.
- **Every address must carry a scope**, `%bat0` above. Software that stores or
  forwards a bare address string will not work with it, and this was not tested
  with any real service.
- **Whether ATAK, a TAK server or `meshtasticd` can use it is untested.** That
  is the question that decides whether this is useful, and it is not answered
  here.
- **CONOPS section 5.4 and SAD section 4.4 make MULE v1 IPv4-first** and do not
  introduce a managed IPv6 architecture. Link-local is not a managed
  architecture, it is automatic and unmanaged, so this is adjacent to that
  decision rather than against it. Using it deliberately would still need an
  ADR.
- **`THREAT_MODEL.md` applies.** The address embeds the interface MAC, and an
  address derived from a durable node identifier is a durable identifier. Note
  that a `batadv` interface's MAC appeared to be randomly generated at creation
  across every run in this campaign, which would make it not durable across a
  restart, but that was observed in passing and never measured.

## LoRa has no deployment identity in this repository

The mission package's `network` object is described as holding values that
"differ between deployments so that two independently built deployments meeting
at an incident do not collide". It contains exactly four fields:

```text
mesh_id   local_domain   address_prefix   ap_ssid
```

**None of them is a LoRa field.** A grep across the repository for a Meshtastic
channel name, a pre-shared key or any equivalent returns nothing. `regions/`
carries `lora.default_channel` and related values, but those are regulatory RF
parameters, every one currently `TBD`, and an RF channel is not a logical
identity: two deployments on the same frequency are not thereby separated or
joined.

So the object whose stated purpose is preventing collision between deployments
covers the Wi-Fi mesh, the DNS domain, the IPv4 prefix and the access point,
and is silent about the LoRa bearer entirely.

### Two default Meshtastic deployments DO converge, verified in the firmware

The protobuf defaults in the pinned `meshtastic` package are proto3 zero values
and say nothing about behaviour. The firmware source does, and states it
outright. From `src/mesh/Channels.h`, retrieved 2026-08-30 from
`meshtastic/firmware` at `master`:

```c
/// 16 bytes of random PSK for our _public_ default channel that all devices
/// power up on (AES128)
static const uint8_t defaultpsk[] = {0xd4, 0xf1, 0xbb, 0x3a, 0x20, 0x29, 0x07, 0x59,
                                     0xf0, 0xbc, 0xff, 0xab, 0xcf, 0x4e, 0x69, 0x01};
```

The chain, all in `src/mesh/Channels.cpp`:

1. `initDefaultChannel` sets a **one-byte** pre-shared key with value 1, and an
   **empty** channel name:

   ```c
   uint8_t defaultpskIndex = 1;
   channelSettings.psk.bytes[0] = defaultpskIndex;
   channelSettings.psk.size = 1;
   strncpy(channelSettings.name, "", sizeof(channelSettings.name));
   ```

2. `getKey` expands a one-byte key into the compiled-in constant, and index 1
   means no change to it:

   ```c
   } else if (k.length == 1) {
       uint8_t pskIndex = k.bytes[0];
       if (pskIndex == 0)
           k.length = 0; // Turn off encryption
       else {
           memcpy(k.bytes, defaultpsk, sizeof(defaultpsk));
           k.length = sizeof(defaultpsk);
           uint8_t *last = k.bytes + sizeof(defaultpsk) - 1;
           *last = *last + pskIndex - 1; // index of 1 means no change vs defaultPSK
       }
   ```

3. `generateHash` derives the channel from the name and the key:
   `h = xorHash(name) ^ xorHash(key)`.

Two stock nodes in the same region with the same modem preset therefore hold an
identical name, an identical key and an identical channel hash. **They are on
one channel and decrypt each other's traffic, without anyone configuring
anything.**

### What that means for this program

**The two bearers are opposites, and a node runs both at once.** `mesh_id` is
required and differs, so two deployments are **separated** on the 802.11s mesh
unless somebody acts. The LoRa default channel is common to every device, so the
same two deployments are **joined** on LoRa unless somebody acts. Every
conclusion in the `TBR-NET-01` artifacts about deployments not meeting by
default is true of one bearer on a node and false of another on the same node.

**The default key is published.** It is a constant in a public repository, so
traffic on the default channel is encrypted against a passive listener who has
not read the source and against nobody else. `THREAT_MODEL.md` should be asked
about that directly; this artifact does not assess it.

**Nothing here selects a fix.** Meshtastic has channel names and keys that a
deployment can set, which is the obvious lever, and choosing one is a decision
this artifact does not make.

**Nothing here tested LoRa on hardware.** No `meshtasticd`, no radio, no
packet. The convergence finding is read from source, which is stronger than the
protobuf defaults it replaces and weaker than two nodes on a bench. Source can
be misread and a build can differ from `master`; `TBR-RF-02` is blocked on a
second SX1262 and that purchase would confirm it.

**The IPv6 result used `veth`, not a wireless mesh**, because it needed no
radio. Nothing about it should depend on the bearer, and that was not checked.
