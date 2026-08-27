# Channel plan - region template

Replace this file with the region's channel plan.

**Status: `TBD`.** No channel plan exists in the template, because a channel
plan is a regulatory statement and inventing one would be exactly the kind of
plausible-looking fabrication this repository forbids.

## What to write

One table per bearer. Every row traces to the rule it derives from.

| Bearer | Channel | Centre frequency | Width | Max EIRP | Duty cycle | Source |
| --- | --- | --- | --- | --- | --- | --- |
| HaLow | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` |
| LoRa | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` | `TBD` |
| Wi-Fi mesh | `TBD` | `TBD` | `TBD` | `TBD` | n/a | `TBD` |
| Wi-Fi AP | `TBD` | `TBD` | `TBD` | `TBD` | n/a | `TBD` |

## Selection rationale

Which channels this program selects from the permitted set, and why.

Coexistence between the HaLow bearer and the LoRa plane is an open trade,
`TBR-RF-02`, and its outcome may constrain channel selection within the band.
Do not finalise a plan that assumes the two do not interact; they share an
enclosure.

## What this document is not

A channel plan describes an allocation. It does not authorise transmission on
any frequency, and it does not make a device compliant. See `REGULATORY.md`.
