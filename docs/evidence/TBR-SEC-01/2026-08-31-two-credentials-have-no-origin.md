# Two credentials the design requires and nothing issues

**Trade:** `TBR-SEC-01`.
**Date:** 2026-08-31.
**Taken by:** Cameron Zobrist.
**Status of this artifact:** analysis of the repository as it stands. No
measurement, and nothing here selects a mechanism.

## What this reports

Two configuration values are required by decisions that are already `SELECTED`,
and **nothing in this program says where either comes from**. Both are now
marked as such in the templates that need them.

| Value | Required by | Template | State |
| --- | --- | --- | --- |
| Mesh credential | `FML-ADR-061`, `key_mgmt=SAE` | `os/config/wpa_supplicant.conf.template` | `sae_password=TBD` |
| Access point passphrase | `FML-ADR-038` admission model | `os/config/hostapd.conf.template` | `wpa_passphrase=TBD` |

## The obvious answer is structurally unavailable

`hostapd.conf.template` said, until 2026-08-31, that the passphrase "comes from
the mission configuration package at generation time". It cannot:

- `mission/schema/mission-package.schema.json` sets `additionalProperties:
  false` at the root **and** on `network`.
- Its own `ap_ssid` entry states the passphrase "is NOT part of this schema and
  never appears in a committed package".
- `mission/local/`, where a real package goes on a builder's machine, validates
  against that same schema. Being git-ignored does not widen it.

So a mission package cannot carry either credential, and the claim that one of
them arrives that way was wrong rather than merely unimplemented.

## What `TBR-SEC-01` already owns, and what it does not

**SAD section 27.5.2 puts `fleet rekey` in this trade's mandated scope**, in the
list of things the unlock trade "must address", alongside unattended restart, a
captured intact node and loss of the authorized operator. `FML-ADR-061`
additionally assigns the mesh credential to this trade as a protected asset,
because it is a credential at rest on every node.

**That covers the credential where it sits. It does not cover how it got
there.** Section 27.5.2 is the *unlock* trade: its subject is how a headless
node opens protected storage, and its four compared options are an operator
passphrase, a TPM-sealed key, a secure element, and combinations. Issuing a
shared mesh credential to a fleet, and rotating it, is a neighbouring question
that the section's `fleet rekey` line touches without defining.

**This artifact does not decide whether that stretch is acceptable.** Either
this trade's scope absorbs credential issuance and rotation, or a separate trade
owns it. That is a register decision and it belongs to the Program Owner. What
is not acceptable is the current state, where two `SELECTED` decisions require
values that no artifact undertakes to supply.

## Why it is load-bearing now rather than later

`FML-ADR-061` states the cost in its own text: **one credential per mesh and no
per-device keys**, measured. A node configured with two `sae_password` entries
and two identifiers did not authenticate a peer holding the second credential.

Therefore:

- A captured node yields the mesh credential, and `THREAT_MODEL.md` makes
  physical capture an expected condition rather than an edge case.
- Revoking one node means **rekeying every node**.
- `THREAT_MODEL.md` also records that "credential revocation in a disconnected
  network is hard and its effectiveness is `TBD`", and that a revoked credential
  should be assumed usable on a partition that has not learned of the
  revocation.

So the fleet rekey line in section 27.5.2 is not a formality here. It is the
control that limits the blast radius of a single lost node, and it has no
mechanism.

## What this does not establish

**No mechanism is proposed and none is ruled out.** Naming a distribution scheme
here would be inventing a specification, which is precisely what this
repository's rules forbid and what `FML-ADR-060` was superseded for doing.

**No measurement.** This is a reading of the schema, two templates, one ADR and
one SAD clause.

**The zeroize interaction is untouched.** `FML-ADR-044` and SAD section 27.5.3
cover cryptographic invalidation, and whether zeroizing a node invalidates the
mesh credential for the rest of the fleet, or only for that node, is not
examined here.

**Nothing about the LoRa bearer**, which has its own credential model, converges
by default on a published constant, and is recorded in
`docs/evidence/TBR-NET-03/2026-08-30-what-happens-with-no-configuration.md`.
