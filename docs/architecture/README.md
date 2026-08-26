# System architecture description

**Status: drafted. Controlling document not yet in this repository.**

The system architecture description is drafted and is the **source of rationale
for the ADR register**. It has not been transcribed here yet.

This README is a placeholder and says so. The seed ADRs in `docs/adr/` record
decisions, statuses and consequences accurately, and each one states that the
architecture document holds the reasoning. Where an ADR body reads thin, that
is why: the reasoning exists, it is not here yet, and writing a plausible
substitute would misrepresent invented reasoning as the program's own.

Do not attempt to reconstruct the architecture from the ADRs. The ADRs are the
decisions, not the design.

## What the architecture description governs

- The plane structure: the network plane, the mission-service plane, and how
  they share one compute element (`FML-ADR-021`).
- The bearer set and how traffic is allocated across it: sub-GHz HaLow as the
  range-oriented IP MANET, conventional Wi-Fi for a high-throughput inter-node
  bearer and a separate EUD access point, and LoRa as an independent
  low-bandwidth degraded-communications plane.
- The two-layer split between a portable Debian-family userland and a
  hardware-specific kernel and board support package. See `os/README.md`, which
  is the operating summary of that split.
- The service architecture above the network plane: the TAK-compatible
  situational-awareness service, browser-based field services, the identity and
  mission-trust layer, and the operator status surface.
- Allocation of requirements to components, which is what
  `tools/gen-traceability.sh` will consume once requirements are populated.

## Relationship to the ADR register

The architecture document explains **why**. The ADR register records **what was
decided, when, with what status, and at what cost**, with a permanent
identifier so it can be cited, superseded and traced.

Neither replaces the other. A decision described only in the architecture
document is not citable; a decision recorded only as an ADR has lost its
reasoning.

When the architecture document lands, the seed ADRs are expected to gain
citations into it rather than to be rewritten. Their decisions do not change
because their rationale became readable.

## Document control

The architecture description is a **controlling document**, drafted rather than
baselined. Until it is baselined:

- Changes are ordinary pull requests, reviewed by the relevant maintainer.
- A change that alters a `SELECTED` decision still requires a superseding ADR.
  Drafted status affects the document's own stability, not the permanence of
  decisions taken from it.
- Once baselined, it moves to the change request process described in
  `docs/conops/README.md`.

## Diagrams

Architecture diagrams are committed as **Mermaid or plain SVG** so they diff
and review as text. An exported image with no source can only be corrected by
its author. See `docs/README.md`.
