# Evidence for TBR-EMCON-01

**Trade:** Which transmissions does an EMCON posture class as avoidable, and which layers suppress them

**Trade file:** `docs/trades/TBR-EMCON-01-which-transmissions-does-an-emcon-posture-class-as-avoidable-and-which-layers-suppress-them.md`

**Current contents:** one artifact. This trade remains `OPEN`; an artifact's
presence is not owner acceptance.

- [2026-10-16-avoidable-transmission-class-list.md][artifact-1]

[artifact-1]: 2026-10-16-avoidable-transmission-class-list.md

It is written analysis, not a measurement: twenty-two transmission classes
partitioned by emitter and trigger, each mapped to one or more of the seven
SAD section 23 layers. It includes **EUD presence self-publish**, which
`CCR-06` (`ACCEPTED` 2026-09-29) routed here under CONOPS section 11 and which
the trade's Closure evidence requires the list to carry.

Every class maps to an existing layer, so the artifact proposes **no new
suppression layer and no ADR**. The gaps it records are in **mechanism** rather
than in the layer set: no decision selects how a posture is enforced, and the
Meshtastic radio is specified to continue its native mesh behaviour
independently of the host, so no identified means reaches that emitter.

Nothing here is a measurement of radio silence. `FML-ADR-046` and CONOPS 50.12
forbid that claim, and the trade's Closure evidence excludes radio measurement
from this gate.

Read the **Closure evidence** and **Closure gate** sections of the trade file
named above. Those sections are authoritative; this file does not restate them,
so that the two cannot drift apart.

Naming and recording rules are in `docs/evidence/README.md`. Nothing real: no
deployment location, member identity, callsign, credential, or operational
capture. See `SECURITY.md`.
