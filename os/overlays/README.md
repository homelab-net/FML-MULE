# Device tree overlays

Device tree overlays enabling peripherals that the base device tree for a
compute module does not describe: radio interfaces on a carrier or adapter, the
real-time clock, and anything else wired to the module's expansion header.

**Empty. No overlay exists.**

Which overlays are needed depends on the selected compute module and on whether
the program has a carrier board at all. Both are open: `TBR-HW-01` and
`TBR-CARRIER-01`.

## When overlays land here

- One file per peripheral or per logical function, not one large overlay.
- A comment header naming what it enables, which hardware block it applies to,
  and the pins or buses it claims.
- Overlays are part of the **compatibility set**. An overlay change is a set
  change and requires the promotion gate. See `FML-ADR-040`.
- An overlay that conflicts with another over a bus or pin is a defect that
  must be caught at build time, not at boot on a node in a field.

## The real-time clock

`FML-ADR-042` makes a battery-backed RTC mandatory on every node, and a compute
module without one is disqualified. Where the RTC is fitted rather than
built in, an overlay describing it will live here, and its absence from a build
is the difference between a node that keeps time and a node that quietly does
not.
