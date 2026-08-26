---
id: TBR-THERM-01
title: Thermal architecture
status: OPEN
owner: TBD
area: THERM
critical-path: false
depends-on: [TBR-PWR-01, TBR-COMP-01]
feeds: [TBR-HW-01]
evidence: docs/evidence/TBR-THERM-01/
adr: []
---

# TBR-THERM-01 Thermal architecture

## Question

How does a sealed, portable enclosure holding a compute element, several
transmitting radios and a lithium pack reject heat, at what ambient, and for
how long?

## Why it matters

Sealing and cooling are in direct tension, and both are required. Ingress
protection removes the airflow every component inside was characterised with. A
module rated for a given ambient in free air is not rated for that ambient
inside a closed box in direct sun.

Three consequences, all bad if unmanaged: silicon throttles and the node's
capability quietly drops during an incident; cells age fast or, at the extreme,
enter thermal runaway next to the thing heating them; external surfaces reach
temperatures that burn.

`SAFETY.md` states plainly that no thermal claim, ambient rating, duty-cycle
limit, or surface-temperature figure appears in this repository. That remains
true until this trade closes.

## Options

Axes rather than invented options: passive conduction to the enclosure wall,
internal air circulation with a sealed loop, a heat spreader or heat pipe to an
external fin, derating the duty cycle instead of improving cooling, and
accepting throttling as designed behaviour with the operator informed.

Cell placement relative to heat sources is a separate axis and is a safety
matter, not only a performance one.

## Closure evidence

Committed under `docs/evidence/TBR-THERM-01/`:

- Measured internal air and component surface temperatures at sustained
  representative load, with ambient, insolation condition, orientation and
  enclosure configuration recorded.
- The same at the worst-case ambient the CONOPS states, or a documented
  extrapolation with its method shown.
- Cell temperature measured separately, at the pack, throughout the run.
- External surface temperature at the hottest accessible point.
- Evidence of whether and when the compute element throttles, from the kernel's
  own thermal reporting, with timestamps aligned to the temperature log.

## Closure gate

At the worst-case ambient stated by the CONOPS, the node sustains its
representative duty cycle without the compute element throttling below the
budget set by `TBR-COMP-01`, with cell temperature inside the manufacturer's
operating range and external surfaces below a stated touch-safe limit.

Where any of those cannot be met, the closure records the duty-cycle derating
required instead, and that derating becomes a stated operating limit rather
than a footnote.

## Dependencies

- **Depends on:** `TBR-PWR-01` (dissipated power), `TBR-COMP-01` (load).
- **Feeds:** `TBR-HW-01`, and directly constrains enclosure selection.
- **Requires hardware:** yes, including an enclosure. This trade cannot start
  before a candidate block exists in some physical form.
