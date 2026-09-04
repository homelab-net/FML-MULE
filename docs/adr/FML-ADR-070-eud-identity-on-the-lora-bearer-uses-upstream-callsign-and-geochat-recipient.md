---
id: FML-ADR-070
title: EUD identity on the LoRa bearer uses upstream callsign and GeoChat recipient
status: SELECTED
date: 2026-09-04
supersedes: none
superseded-by: none
trades: [TBR-NET-02]
verification: TBD
---

# FML-ADR-070 EUD identity on the LoRa bearer uses upstream callsign and GeoChat recipient

## Context

`TBR-NET-02` asks how a node addresses the EUDs behind it. Its addressing
specification (`docs/evidence/TBR-NET-02/2026-08-29-addressing-specification.md`)
selected a **custom one-byte member index** carried in the Meshtastic payload,
on airtime grounds: costed against `DATA_PAYLOAD_LEN`, the index is 0.43% of the
payload against roughly 3.4% for a short callsign string. In isolation that
reasoning was sound.

Two later findings undercut the encoding, not the reasoning.
`docs/evidence/TBR-NET-02/2026-08-30-tag-payload-measurement.md` confirmed the
index is carriable but also that the **usable payload is 231 bytes, not the 233
the protobuf advertises** -- 232 and 233 do not arrive.
`docs/evidence/TBR-NET-02/2026-08-30-opentakserver-meshtastic-path.md` then read
the first of `FML-ADR-048`'s gateways and found that a payload on a private port
is **discarded**, and that the ATAK-plugin protobuf the gateway does handle
already carries `Contact.callsign` (a per-person human identity) and
`GeoChat.to` (a named recipient). There is no spare field for the index, so
adding it means **replacing** upstream's encoding -- which `FML-ADR-048` orders
the program not to do first.

So the choice was never "one byte or eight". It was: use what upstream already
carries, at more airtime and no custom gateway code, staying upstream-first
(`FML-ADR-048`); or keep the index and stop being upstream-first, which needs an
ADR written against `FML-ADR-048`. The Program Owner decided on 2026-09-04 for
upstream's fields.

## Decision

EUD identity and recipient on the LoRa bearer **shall** be carried by upstream's
existing fields: the sender **shall** be identified by `Contact.callsign` and
the intended recipient, where one is named, by `GeoChat.to`. The program
**shall not** introduce a custom member index that replaces upstream's Meshtastic
encoding; this keeps the gateway upstream-first as `FML-ADR-048` requires.

Because the usable payload is 231 bytes and a callsign now shares it with the
message, composed messages **shall** be constrained by an artificial character
limit in the Meshtastic and EUD-facing paths so a message plus its identity
fields fits the usable payload. The node is now off the stock Meshtastic packet
size from the operator's point of view, and the limit makes that visible at
composition rather than silently truncating in flight.

## Status

`SELECTED`. Architecture direction accepted by the Program Owner for the current
package on 2026-09-04. It resolves item 4 (the LoRa tag encoding) of
`TBR-NET-02`'s closure evidence, superseding the addressing specification's
selection of the one-byte index; the other four items of that specification
stand.

## Consequences

- **More airtime per addressed message.** A short callsign is roughly 3.4% of
  the usable payload against the index's 0.43%. On the CONOPS section 50.8
  lifeline bearer that is real cost, measured only in the simulated payload
  study so far; its RF effect is a hardware item.
- **An artificial message-length limit becomes work.** The Meshtastic and
  EUD-facing composition paths must enforce a character limit sized to the
  231-byte usable payload minus the identity fields. This did not exist and is
  new work; it lands against `docs/ROADMAP-DEV.md` item 1.1 step 2, which
  `TBR-NET-02` feeds. Until it exists, a long message plus identity can exceed
  the usable payload and fail to arrive, which the measurement showed happens at
  232 bytes.
- **`GeoChat.to`'s contents are not yet established.** Whether it holds a
  callsign, a CoT UID, or something else was not determined because the server
  was not run (`2026-08-30-opentakserver-meshtastic-path.md` records this). The
  recipient-resolution step cannot be implemented until a follow-up establishes
  it; that follow-up is verification below, not a reason to defer the encoding
  decision.
- **No custom gateway code and no fork against `FML-ADR-048`.** The gateway
  keeps upstream's format, which is less to maintain for volunteers and removes
  a standing divergence from upstream.
- **Threat model: per-person identity travels on the wire.** `Contact.callsign`
  identifies the sender per person rather than per MULE. The callsign is already
  the deployment-scoped human name and already travels in the ATAK-plugin
  protobuf, so this discloses nothing the bearer did not already carry; it is
  recorded here rather than left implicit. See `THREAT_MODEL.md`.

## Accepted cost

The program knowingly accepts more airtime on its longest-range, lowest-rate
bearer, and a message-length cap that operators will feel as shorter than stock
Meshtastic. Someone will later argue the index's airtime saving was worth a
one-time fork of the encoding. It is accepted because being upstream-first
(`FML-ADR-048`) is a standing decision, a custom encoding on a private port was
measured to be discarded, and the identity upstream carries is sufficient for
addressing; the saving did not justify owning a divergence from upstream on the
lifeline path.

## Fallback

Reversible, not structural. If airtime contention on the LoRa bearer proves
prohibitive at a real deployment's member count, the index option returns -- but
taking it then requires the ADR against `FML-ADR-048` that this decision avoided,
and the gateway work to replace upstream's encoding. The signal to revisit is
measured airtime saturation attributable to identity fields on real radios, a
`TBR-RF-01`-class measurement, not a bench result.

## Superseded by

None.

## Verification dependency

`TBD`. Two checks: that `GeoChat.to` resolves to an EUD the node can name
(needs the server run, an analysis task on rig R0/R1), and that the composition
character limit holds a message plus identity within the 231-byte usable
payload. Both belong to stage 3 (LoRa continuity); neither needs a radio to
start.
