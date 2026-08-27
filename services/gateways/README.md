# Gateways

**PARTLY APPROVED, NOT YET IMPLEMENTABLE. This directory contains this
`README.md` and nothing else.**

Two distinct functions sit here, and they have different statuses.

## Gateway translation - `FML-ADR-048`, SELECTED RULE

**Source:** SAD v0.31 sections 29.5, 7.3 and 24.

Translation uses **existing integrations first**. For the LoRa path the priority
is fixed by SAD section 7.3:

1. existing OpenTAKServer Meshtastic support where it satisfies the mission
   need;
2. the TAK Meshtastic Gateway;
3. PyTAK plus the Meshtastic Python API for only the translation logic not
   already provided upstream.

**Custom translation is protocol-specific glue only.** Custom LoRa protocol
development is out of scope, and `FML-ADR-033` keeps generic CoT transport out
of scope too: PyTAK is the preferred library and CoT transport is not
reimplemented without cause.

External VHF/UHF/HF integrations connect through standard interfaces where
possible — USB serial, audio, TNC, Bluetooth, TCP/UDP, or a documented vendor
API — normalizing native radio protocol to CoT and/or MQTT. Dire Wolf is the
preferred initial AX.25/APRS software modem candidate.

**Owner:** TAK / Integration.

## RF coexistence policy service - `TBR-RF-02`, NOT YET SELECTED

**Source:** SAD v0.31 section 8.2, and the MULE-original software inventory in
section 29.5, which lists this as **NOT YET SELECTED**.

`FML-ADR-027` requires coexistence to be controlled through **documented
supported host and radio interfaces**, and forbids assuming that the
`openmanetd` API provides deterministic scan or transmit-suppression primitives.

`TBR-RF-02` first determines whether supported driver, netlink/nl80211, `iw`,
`wpa_supplicant`, Morse Micro or equivalent controls are sufficient. **Original
coexistence software is permitted only if a thin policy layer is still necessary
after that test**, and no driver fork is authorised.

Its closure evidence must include a **supported-control inventory**, so the
program knows what it can actually command rather than what it wishes it could.

## What must close before implementation starts

| Question | Trade | Priority |
| --- | --- | ---: |
| Which mission state matters, and therefore what is worth translating | `TBR-TAK-01` | 9, `CRITICAL` |
| Whether a coexistence policy service is the selected control at all | `TBR-RF-02` | 11 |

## Why not build either anyway

**Translation.** Deciding what crosses to the degraded LoRa plane is deciding
what matters when everything else has failed. That is a CONOPS question about
operational priorities, informed by the `TBR-TAK-01` state classification. A
gateway written first answers it by implication, in code, and the answer becomes
whatever was easiest to translate.

**Coexistence.** `TBR-RF-02` may close on physical separation, filtering,
channel plan separation, or accepting and characterising the degradation. A
policy service is one option among several. Building it now makes it the answer
by making it the thing that exists.

**Plane independence.** The LoRa plane's value is that it works when the IP plane
does not (`FML-ADR-026`). A gateway is a coupling between them, and every
coupling is a way for failure to propagate. That is a reason for caution, not a
reason against gateways, and it belongs in the trade.

## Regulatory constraint

Where a builder enables amateur-band operation, encryption is unlawful in many
jurisdictions, so a gateway cannot assume every sub-GHz emission is
confidential. Amateur egress is **disabled by default** and requires the
distinct control operator role in CONOPS section 7.8. CONOPS section 46 forbids
mirroring TAK update rates onto shared amateur networks. See `REGULATORY.md`.

## What can be done now

- **Close `TBR-TAK-01`**, which needs no hardware.
- **Take the `TBR-RF-02` measurements**, which need an assembled enclosure: LoRa
  receive sensitivity with the HaLow radio idle and transmitting, at the antenna
  separations physically achievable there. Bench measurements with the radios
  far apart do not answer the question.
