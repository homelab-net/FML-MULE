# A keyed mesh admits only key holders, and one key is all there is

**Trade:** `TBR-NET-03`.
**Date:** 2026-08-31.
**Taken by:** Cameron Zobrist, on the lab development machine.
**Status of this artifact:** `SIMULATED`. Three `mac80211_hwsim` radios in
network namespaces, `wpa_supplicant` 2.10 from Debian. **No radio was
involved.**

## Why this exists

`FML-ADR-060` prohibited merging meshes, arguing that merging admits another
organization's members to a shared trust environment by typing a mesh name into
a radio, and so bypasses admission control.

**The argument assumed an open mesh.**
`os/config/wpa_supplicant.conf.template` carries `key_mgmt=TBD` and says "Mesh
security is not decided. An open mesh admits any device in range, which
conflicts with the admission model." The ADR decided a consequence of an
undecided question without checking it.

This tests the question the ADR skipped.

## Result 1: only key holders join

Three nodes, one mesh identifier, one channel, all in range. Two configured
`key_mgmt=SAE` with the same passphrase, one with `key_mgmt=NONE`:

```text
node 1 (program key) peers with: node2(keyed)
node 2 (program key) peers with: node1(keyed)
node 3 (NO KEY)      peers with: (none)
```

The key holders find each other and peer with no operator action. The unkeyed
node in the same mesh on the same channel establishes no peer link at all.

`wpa_supplicant` on a key holder:

```text
wlan0: mesh plink with 9e:66:e0:91:4c:a8 established
wlan0: MESH-PEER-CONNECTED 9e:66:e0:91:4c:a8
```

**So the key is the admission control**, and `FML-ADR-060`'s premise does not
hold on a keyed mesh.

## Result 2: a different key does not get in, and a peer list does not tell you

Three nodes all using `key_mgmt=SAE`, two sharing one passphrase and one with a
different passphrase. Reading the peer *state* rather than counting peers:

| Pair | `mesh plink` | authenticated | authorized | traffic |
| --- | --- | --- | --- | --- |
| same key | `ESTAB` | yes | yes | 0% packet loss |
| different key | `LISTEN` | no | no | 100% packet loss |

**This corrects an earlier reading in this same investigation.** A first pass
counted `Station` lines from `iw station dump` and concluded that two
differently-keyed nodes had peered, which would have meant per-organization
credentials worked. They had not. `LISTEN` is a node the radio has *seen*, not a
peering, and the flags and the traffic both say so.

Recorded because the mistake is easy, the output looks like success, and getting
it wrong would have put a false security claim into an ADR.

## Result 3: no per-device or per-organization keys

A node configured with two `sae_password` entries and two `sae_password_id`
identifiers did **not** authenticate a peer holding the second credential. Every
cross-credential pairing stayed at `LISTEN`.

`sae_password_id` is documented in the `wpa_supplicant.conf` reference shipped
with Debian's `wpasupplicant` 2.10 -- "the specified identifier value is used by
the other peer to select which password to use" -- so the mechanism exists in
the configuration language. **Whether some configuration makes it work in mesh
mode is not established here**, and nothing should be built assuming it does.

What is established is that the configuration tried did not work, so the working
assumption is **one credential per mesh**.

### What that costs

`THREAT_MODEL.md` makes physical capture an expected condition and records that
"credential revocation in a disconnected network is hard and its effectiveness
is `TBD`". With one credential per mesh:

- A captured node yields the mesh credential.
- Revoking one node means rekeying every node.
- A partner given the credential cannot be removed without rekeying the whole
  fleet.

**That last point decides the cross-organization question.** Handing a partner a
configured MULE and handing them the key are the same act, because a MULE can
only join by holding the key. A separate keyed mesh on a liaison node is the
only arrangement measured here that lets a partner be removed without touching
the deployment's own nodes.

## What this does not establish

**Nothing about the HaLow bearer**, which is the one that matters most. The
template already warns that "whether the HaLow driver honours standard
`wpa_supplicant` mesh options at all" is unverified. This ran on 2.4 GHz
`mac80211_hwsim`. If HaLow does not support SAE, the decision built on this
result does not apply to the bearer it was written for. `TBR-LINUX-01`.

**No real driver, no radio, no propagation.** `hwsim` models the MAC.

**Nothing about key distribution or rotation.** No mechanism exists in this
program for either, and this artifact does not propose one.

**Nothing about the LoRa bearer**, which has its own credential model and
converges by default. See
`2026-08-30-what-happens-with-no-configuration.md`.

**The passphrases used were bench values** and appear nowhere in the repository.
`SECURITY.md` forbids committing a credential and none is committed.
