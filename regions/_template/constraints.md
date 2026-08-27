# Constraints - region template

Replace this file with the region's binding limits.

**Status: `TBD`.**

## Binding limits

| Constraint | Value | Applies to | Source |
| --- | --- | --- | --- |
| Maximum EIRP | `TBD` | `TBD` | `TBD` |
| Maximum antenna gain | `TBD` | `TBD` | `TBD` |
| Duty cycle | `TBD` | `TBD` | `TBD` |
| Channel dwell or hopping requirement | `TBD` | `TBD` | `TBD` |
| Listen-before-talk requirement | `TBD` | `TBD` | `TBD` |
| Indoor-only restriction | `TBD` | `TBD` | `TBD` |
| Labelling requirement | `TBD` | `TBD` | `TBD` |

## Constraints with design consequences

Some limits change configuration. Others change whether the operational concept
works at all, and those need to be called out rather than filed as a number.

A **duty-cycle limit** is the clearest example. A bearer permitted to transmit
only a small fraction of the time behaves differently from one that is not
limited: routing protocol overhead, position reporting rate, and mesh
convergence all interact with it. A region with a duty-cycle constraint may not
support the same operational concept as one without, and that is a program-level
finding, not a configuration value.

Record any such constraint here **and** raise it, so it can become a trade.

## Exposure

Radiofrequency exposure obligations for a multi-emitter device carried or
operated near people. `TBD` for every region; see `REGULATORY.md`. No exposure
claim is made anywhere in this repository.

## Amateur allocations

Whether amateur integration is permitted in this region, under what licence
class, with what identification obligation, and whether encrypted traffic is
permitted. Amateur integration is **disabled by default** everywhere and is
never defaulted to enabled in a region profile.
