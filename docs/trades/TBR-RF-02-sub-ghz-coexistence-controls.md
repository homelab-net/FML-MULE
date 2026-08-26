---
id: TBR-RF-02
title: Sub-GHz coexistence controls
status: OPEN
owner: TBD
area: RF
critical-path: false
depends-on: []
feeds: [TBR-HW-01, TBR-RF-03]
evidence: docs/evidence/TBR-RF-02/
adr: []
---

# TBR-RF-02 Sub-GHz coexistence controls

## Question

How do the HaLow bearer and the LoRa plane coexist in the same sub-GHz band, in
the same enclosure, without degrading each other?

## Why it matters

Two transmitters in one band, centimetres apart, sharing an enclosure and
possibly a ground plane. The HaLow bearer is the range-oriented IP MANET; the
LoRa plane is the independent degraded-communications fallback whose whole
value is that it still works when the IP plane does not. If HaLow desensitises
the LoRa receiver, the fallback fails at exactly the moment it is needed, and
it fails silently.

Coexistence is also a regional matter. The 902-928 MHz channel plan differs
from the 863-868 MHz one, and the European sub-bands carry duty-cycle
constraints with no analogue in the US rules. Any control decided here must be
expressible as a region parameter; see `regions/README.md` and `REGULATORY.md`.

There is a further constraint from `REGULATORY.md`: where a builder enables
amateur-band operation, encryption is unlawful in many jurisdictions, so
coexistence policy cannot assume every sub-GHz emission is confidential.

## Options

Axes: physical separation and antenna placement, filtering, a coexistence
policy service that schedules or gates transmissions between the two radios,
channel plan separation within the band, duty-cycle limits, and simply
accepting degradation and characterising it.

A coexistence policy service is one of the four placeholder components in
`services/`, and it is not to be implemented before this trade closes. See
`services/gateways/README.md` and `AGENTS.md`.

## Closure evidence

Committed under `docs/evidence/TBR-RF-02/`:

- Measured LoRa receive sensitivity with the HaLow radio idle, and with it
  transmitting at maximum duty, in the assembled enclosure, with antenna
  positions recorded.
- The reciprocal measurement: HaLow link quality with the LoRa radio
  transmitting.
- Measurements at the antenna separations physically achievable in the
  candidate enclosure, not on a bench with the radios far apart.
- The region profile each measurement was taken under.

## Closure gate

Measured degradation of each bearer in the presence of the other is
characterised and stated, and either falls within a stated acceptable limit, or
a control is selected and demonstrated to bring it within that limit. The limit
is written before the measurement.

"No interference was observed" is not closure. The measurement must show the
sensitivity figure with and without the interferer.

## Dependencies

- **Depends on:** none, though it needs a candidate enclosure to be meaningful.
- **Feeds:** `TBR-HW-01`, `TBR-RF-03`.
- **Requires hardware:** yes, including the assembled enclosure. Bench
  measurements with separated radios do not answer this question.
