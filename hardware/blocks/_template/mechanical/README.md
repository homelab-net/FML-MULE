# Mechanical

Enclosure, mounting, internal layout, and cable routing for this block.

**Status: `TBD`. No enclosure selected.** See `TBR-THERM-01` and `TBR-HW-01`.

## What belongs here

- **Enclosure selection**, with its ingress protection rating and its
  dimensions.
- **Internal layout**: where each board, radio, antenna and the pack sit.
- **Mounting**: how components are retained, and how the node itself is
  mounted or carried.
- **Cable routing and strain relief.** Vibration and handling break wires at
  the joint, and a broken conductor inside a sealed enclosure can short.
- **Thermal paths**: contact surfaces, spreaders, standoffs. Cross-reference
  `TBR-THERM-01`.
- **Cell placement relative to heat sources.** This is a safety matter, not a
  packaging preference. See `SAFETY.md`.

## Source and render

Commit **both** the native CAD source and a rendered PDF or PNG. Both are
tracked by Git LFS; check `.gitattributes` before introducing a format that is
not already listed.

A drawing that exists only as an exported image can be corrected by nobody but
its author. That is the same failure the hardware abstraction rule guards
against in code, and it is worse here because the author is usually the only
person with the CAD licence.

Prefer a format that others can open. A design in a proprietary format with a
subscription requirement excludes contributors as effectively as no design at
all. Where that is unavoidable, also commit a neutral export such as STEP.

## The tension this directory holds

Sealing and cooling work against each other, and both are required. Ingress
protection removes the airflow every component inside was characterised with.
A module rated for a given ambient in free air is not rated for that ambient
inside a closed box in sun.

Nothing in this repository states a thermal rating, an ambient limit, a
duty-cycle limit, or a surface temperature, because none has been measured.
`TBR-THERM-01` is where that changes.
