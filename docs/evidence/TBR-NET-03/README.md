# Evidence for TBR-NET-03

**Trade:** How do two deployments converge on one mesh

**Trade file:** `docs/trades/TBR-NET-03-how-do-two-deployments-converge-on-one-mesh.md`

**Current contents:** one artifact. The trade is `OPEN`: this supplies part of
one of its four closure-evidence items and selects nothing.

- `2026-08-30-liaison-routing-exercise.md` -- the routed-liaison option
  exercised end to end. Two deployments on different meshes interoperate
  through one routing node each, with layer 2 never merging, for one route per
  liaison. Withdrawal is instant and contained; **restoration is not
  automatic**, because the kernel deletes a static route with its interface and
  does not restore it. Identical prefixes defeat the option twice over: the
  route cannot be installed, and no address exists that names the other
  deployment.

Still missing: the operator-facing statement of the procedure, the
`THREAT_MODEL.md` assessment, the statement of what a liaison may forward and
who authorises one, and the decision itself.

Read the **Closure evidence** and **Closure gate** sections of the trade file
named above. Those sections are authoritative; this file does not restate them,
so that the two cannot drift apart.

Naming and recording rules are in `docs/evidence/README.md`. Nothing real: no
deployment location, member identity, callsign, credential, or operational
capture. See `SECURITY.md`.
