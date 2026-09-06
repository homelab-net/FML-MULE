# Reticulum (RNS)

**Evaluated:** 2026-09-06, from the Reticulum manual
(`reticulum.network/manual`, retrieved 2026-09-06). **Verdict:** does **not**
fit as an adoption; worth keeping as prior art and a benchmark for two
sub-problems.

## What it is

Reticulum is a complete networking stack **independent of IP** (it can tunnel
over IP but replaces it). Its properties, from its own manual:

- **Cryptographic, coordination-less addressing.** Every identity is a
  self-generated 512-bit elliptic-curve keyset (X25519 for encryption, Ed25519
  for signatures); addresses are derived from keys, with no authority or
  registry. Packets carry no source address; initiator anonymity is supported.
- **Encryption by default.** AES-256 with HMAC-SHA256, and forward secrecy from
  ephemeral per-packet and per-link ECDH on Curve25519.
- **Self-configuring multi-hop routing over heterogeneous carriers.** One routed
  layer spans LoRa (via RNode), packet-radio TNCs (KISS), Ethernet/Wi-Fi, serial,
  I2P, TCP/UDP, and custom interfaces.
- **Built for scarcity.** Runs in userland on a Pi Zero, over links as slow as
  a few bits per second, with a 500-byte MTU.
- **Public domain / permissive** (the Reticulum License), so its ideas are freely
  usable.
- Ships higher-level tools of its **own** ecosystem -- LXMF messaging, Nomad
  Network. It has **no relationship to ATAK, TAK, CoT, or Meshtastic**; the
  manual does not mention them.

## Does it fit FML-MULE? No, and why

FML-MULE is committed to the ATAK/TAK ecosystem: the EUDs are ATAK and iTAK
clients speaking CoT to OpenTAKServer over IP; the high-rate plane is IP over
`batman-adv`; the LoRa lifeline is Meshtastic, chosen **because** it carries ATAK
through the upstream Meshtastic plugin (`FML-ADR-026`, `FML-ADR-070`). Reticulum
is a parallel stack that intersects none of that:

- It is not IP, so it cannot carry the ATAK-to-TAK-server traffic that needs IP;
  it would not replace `batman-adv` for the plane the mission actually runs on.
- Its LoRa (RNode) is not the Meshtastic path ATAK speaks, so swapping the LoRa
  lifeline to Reticulum would **lose** the ATAK integration that was the reason
  to pick Meshtastic.
- Adopting it as a bearer or routing layer is exactly the "parallel mechanism
  beside the standard" that `AGENTS.md` rule 6 exists to prevent.

So Reticulum is not a component to integrate into the current architecture.

## Does it provide work we need not repeat? As a reference, for two things

Its value here is as **prior art and a benchmark**, not code to pull in:

- **Decentralised, CA-free cryptographic identity (`TBR-ID-01`).** Reticulum's
  self-sovereign keypair-as-address model is a mature, public-domain treatment of
  the identity problem `TBR-ID-01` opens, and a sharp contrast to the TAK
  certificate model whose failure modes the `TBR-TAK-01` work recorded (a CA per
  node, indistinguishable same-CN certs, no revocation path). It is a **reference
  for the trade**, not a drop-in: ATAK authenticates with certificates, and a
  keypair-address scheme does not speak to a TAK client. `TBR-ID-01` may cite it
  as an option considered.
- **Multi-bearer routing over heterogeneous carriers.** Unifying LoRa, serial and
  IP links into one self-configuring routed layer is the MULE's own premise.
  FML-MULE keeps the bearers as separate planes with a gateway between them
  (`FML-ADR-048`) because ATAK needs IP; Reticulum shows the other design point --
  one crypto-native layer across all bearers -- and is a useful benchmark when
  `TBR-NET-04` and the routing ADRs are revisited.

## The one concrete "don't build it" candidate

If a future need arises for a **non-TAK, crypto-native, bearer-agnostic operator
messaging fallback** -- text and small files that must move when IP and the TAK
server are both gone, beyond what Meshtastic covers -- Reticulum's LXMF is a
ready, public-domain implementation to evaluate rather than build. That need is
not in scope now (`docs/NON-GOALS.md`, CONOPS S1/S2 tiers), and raising it is a
change request, not a quiet adoption. Recorded so the option is not forgotten.

## Bearing

- **`TBR-ID-01`:** a reference for the CA-free identity option.
- **`TBR-NET-04` and the routing ADRs:** a benchmark for the single-layer
  multi-bearer alternative the program did not take.
- Not adopted; if a decision to record that is wanted, it is a `docs/NON-GOALS.md`
  entry or an ADR, per this directory's README.
