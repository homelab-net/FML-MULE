# Evidence for TBR-TAK-01

**Trade:** Mission-critical state boundary

**Trade file:** `docs/trades/TBR-TAK-01-mission-critical-state-boundary.md`

**Priority:** 9 of 16 (SAD v0.31 section 30.2). **Function owner:** TAK + SRE.
**Named owner:** `TBD-SRR`.

**Current contents:** the analysis half only. This trade remains `OPEN`.

| Artifact | What it is | Status |
| --- | --- | --- |
| `2026-08-27-state-classification-analysis.md` | The ten SAD section 14.1 categories placed into the three CONOPS section 26 classes, with the durable set and its partition and rejoin behaviour | `UNVERIFIED` |

**That artifact does not close this trade**, and says so in its own opening
section. The listed evidence also requires a different-node restore and the
DataSync, mission-package, certificate and map-cache tests, none of which has
been performed. SAD section 14.2 is explicit that support claimed rather than
demonstrated is not acceptance evidence, and a classification derived from
documentation is a claim about what state *is*, not about where an
implementation *puts* it.

Five findings in it are worth a reader's attention before the empirical half
runs, particularly the fifth: at least two members of the durable set appear to
sit outside any plausible SQL backend, which would make database high
availability necessary and not sufficient, and would change the shape of
`TBR-HA-01`.

This directory existed before the work did, deliberately. The closure gate is
written in the trade file before evidence is gathered, so the result cannot be
graded against a standard invented after seeing it.

## What belongs here

Read the **Closure evidence** and **Closure gate** sections of the trade file
named above. Those sections are transcribed from the SAD and are authoritative;
this file does not restate them, so that the two cannot drift apart.

Every artifact follows the naming and recording rules in
`docs/evidence/README.md`:

- `YYYY-MM-DD-<what>-<node-or-configuration>.<ext>`
- Measurements record instrument, date, node, image build, configuration,
  ambient conditions, and who took them.
- Vendor datasheets go in `datasheets/` with a `.SOURCE.md` recording the
  URL, retrieval date, and document revision. Archive them when you cite them;
  vendors delete PDFs. SAD section 34 is the program's external source register.
- Nothing real: no deployment location, member identity, callsign, credential,
  or operational capture. Strip photograph metadata. See `SECURITY.md`.

**Requires hardware:** No. A design and analysis trade, resolvable against documentation, protocol

## Closing

Evidence here is necessary and not sufficient. SAD section 30.2: a TBR closes
only when its listed evidence exists, **the named owner accepts the evidence**,
and the resulting architecture decision is entered into the persistent ADR
register.

Closing a trade whose named owner is still `TBD-SRR` is not possible, because
there is nobody to accept the evidence.
