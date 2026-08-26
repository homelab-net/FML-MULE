# RF

Antennas, placement, module approvals, and the RF characteristics of this
block.

**Status: `TBD`. No radio module or antenna selected.** See `TBR-HW-01`,
`TBR-RF-01`, `TBR-RF-02`, `TBR-RF-03`.

## What belongs here

- **Every radio module**, with its manufacturer part number and the bearer it
  serves.
- **Regulatory approval identifiers**, exactly as issued, per region. Not
  "certified": the identifier.
- **The antenna each approval was granted with**, or the antenna class it
  permits, and the **maximum gain**.
- **Integration conditions** attached to each approval: shielding, ground
  plane, separation distance from a user, labelling.
- **Antenna placement and separation**, as built, with a drawing. Coexistence
  measurements are meaningless without it.
- **Measured RF performance** once it exists, per `docs/evidence/`.
- **Which region profiles this block is valid under.**

## Why the approval detail matters here specifically

Modular approval is granted against a specific test configuration, and the
antenna is part of that configuration. **Substituting an antenna can void the
approval.** A higher-gain antenna raises radiated power; an antenna of a
different type may fall outside the permitted class. "It has the same
connector" is not a compliance argument.

Combining several individually approved modules in one enclosure does not
automatically produce a compliant device, particularly where emitters interact
or where the assembly must be labelled as a whole. **Compliance of the
assembled device is the builder's responsibility.** See `REGULATORY.md`.

## Coexistence

This block carries a sub-GHz HaLow bearer and a LoRa plane in the same band,
centimetres apart, sharing an enclosure and possibly a ground plane. If HaLow
desensitises the LoRa receiver, the degraded-communications fallback fails at
exactly the moment it is needed, and it fails silently.

`TBR-RF-02` measures this, and it must be measured **in the assembled
enclosure**, at the antenna separations physically achievable there. Bench
measurements with the radios far apart do not answer the question.

## Exposure

Radiofrequency exposure evaluation for a multi-emitter device carried or
operated near people is `TBD`. Simultaneous transmission from several bearers
is the normal operating mode, not an edge case. **No exposure claim of any kind
appears in this repository.**
