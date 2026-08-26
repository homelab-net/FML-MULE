---
id: TBR-RF-01
title: High-rate mesh implementation
status: OPEN
owner: TBD
area: RF
critical-path: false
depends-on: [TBR-LINUX-01]
feeds: [TBR-RF-03, TBR-HW-01]
evidence: docs/evidence/TBR-RF-01/
adr: [FML-ADR-023, FML-ADR-024, FML-ADR-045]
---

# TBR-RF-01 High-rate mesh implementation

## Question

How is the high-throughput inter-node bearer implemented on conventional Wi-Fi,
and does it use the same 802.11s and `batman-adv` arrangement as the sub-GHz
bearer?

## Why it matters

`FML-ADR-024` selects 802.11s with `batman-adv` for the range-oriented sub-GHz
bearer. It does not decide the high-rate bearer. Using the same mechanism gives
one routing domain and one set of tools; using a different one may perform
better but adds a second thing to understand and debug in the field.

If both bearers join the same `batman-adv` mesh, BATMAN-V's metric must
distinguish them sensibly, or traffic will take a fast-but-absent path or a
present-but-slow one. Whether it does is unmeasured.

The answer constrains how many conventional Wi-Fi radios a block needs, which
is `TBR-RF-03` and then `TBR-HW-01`.

## Options

1. **Same mechanism, one mesh.** 802.11s plus `batman-adv` on both bearers, one
   routing domain, metric distinguishes them. Simplest operationally if the
   metric behaves.
2. **Same mechanism, separate meshes.** Two `batman-adv` instances with an
   explicit policy for which traffic uses which. More control, more
   configuration, more ways to misconfigure.
3. **Different mechanism on the high-rate bearer**, for example a point-to-point
   arrangement between known neighbours. Right answer if mesh association over
   conventional Wi-Fi proves unreliable at the ranges involved.
4. **No dedicated high-rate inter-node bearer.** Recorded because it is a real
   option: if the sub-GHz bearer plus the access point meet the operational
   need, the program saves a radio, its power, and its heat.

## Closure evidence

Committed under `docs/evidence/TBR-RF-01/`:

- Measured throughput and latency between two nodes over the candidate
  arrangement, at recorded separations and with recorded antenna configuration.
- `batctl` output showing the metric each bearer receives, and evidence of
  which path traffic actually took.
- A path-failover observation: one bearer removed, traffic continuity recorded.
- Where option 4 is under consideration, a stated operational requirement for
  inter-node throughput traced to the CONOPS, against which it can be judged.

## Closure gate

A selected arrangement carries bidirectional traffic between nodes at a rate
that meets a stated requirement, and routing selects the intended bearer under
both normal and degraded conditions, with all of it recorded.

## Dependencies

- **Depends on:** `TBR-LINUX-01`.
- **Feeds:** `TBR-RF-03`, `TBR-HW-01`.
- **Requires hardware:** yes, at least two nodes.
