# Gateways

**PLACEHOLDER. DO NOT IMPLEMENT.**

This directory contains this `README.md` and nothing else, by decision. See
`AGENTS.md`, constraint one, and `services/README.md`, the placeholder rule.

## What this component will do

Translate between planes that do not share a data model, and enforce the
coexistence policy between radios that share a band.

Two related jobs, both open:

**Translation.** The IP mission-service plane carries CoT and browser-based
services. The LoRa plane carries an independent low-bandwidth
degraded-communications channel and is not IP. A gateway decides what, if
anything, crosses between them. The bandwidth ratio is severe: a low-rate
bearer cannot carry the IP plane's traffic, so a gateway is necessarily a
lossy, selective translation, and deciding what survives it is a mission
decision rather than a technical one.

**Coexistence policy.** The HaLow bearer and the LoRa plane occupy the same
sub-GHz band, centimetres apart, sharing an enclosure. A coexistence policy
service would schedule or gate transmissions between them. That is one of the
options in `TBR-RF-02`, and it may not be the selected one.

## Decision reference

No ADR selects a gateway design. `FML-ADR-024` fixes the IP MANET arrangement
on one side; the LoRa plane is deliberately independent of it. Execution model
follows `FML-ADR-029`.

## What must close before implementation starts

| Question | Trade |
| --- | --- |
| Which mission state matters, and therefore what is worth translating | `TBR-TAK-01` |
| Whether a coexistence policy service is the selected control at all | `TBR-RF-02` |

## Why not build it anyway

**Translation.** Deciding what crosses to the degraded plane is deciding what
matters when everything else has failed. That is a CONOPS question about
operational priorities, informed by the state classification in `TBR-TAK-01`. A
gateway written first would answer it by implication, in code, and the answer
would be whatever was easiest to translate.

**Coexistence.** `TBR-RF-02` may close on physical separation, filtering,
channel plan separation, or accepting characterised degradation. A policy
service is one option among several. Building it now would make it the answer
by making it the thing that exists.

There is also a plane-independence argument. The LoRa plane's value is that it
works when the IP plane does not. A gateway is a coupling between them, and
every coupling is a way for a failure to propagate. That is a reason for
caution, not a reason against gateways, and it belongs in the trade.

## What can be done now

- **Close `TBR-TAK-01`**, which requires no hardware.
- **Take the `TBR-RF-02` measurements**, which need an assembled enclosure:
  LoRa receive sensitivity with the HaLow radio idle and transmitting, at the
  antenna separations physically achievable in the candidate enclosure. Bench
  measurements with the radios far apart do not answer the question.
- **Note the regulatory constraint.** Where a builder enables amateur-band
  operation, encryption is unlawful in many jurisdictions, so a gateway cannot
  assume every sub-GHz emission is confidential. See `REGULATORY.md`.
