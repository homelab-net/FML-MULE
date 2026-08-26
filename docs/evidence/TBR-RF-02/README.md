# Evidence for TBR-RF-02

**Trade:** Sub-GHz coexistence controls

**Trade file:** `docs/trades/TBR-RF-02-sub-ghz-coexistence-controls.md`

**Current contents:** none. This trade is `OPEN` and no evidence has been
produced.

This directory exists before the work does, deliberately. The closure gate is
written in the trade file before evidence is gathered, so the result cannot be
graded against a standard invented after seeing it.

## What belongs here

Read the **Closure evidence** and **Closure gate** sections of the trade file
named above. Those sections are authoritative; this file does not restate them,
so that the two cannot drift apart.

Every artifact follows the naming and recording rules in
`docs/evidence/README.md`:

- `YYYY-MM-DD-<what>-<node-or-configuration>.<ext>`
- Measurements record instrument, date, node, image build, configuration,
  ambient conditions, and who took them.
- Vendor datasheets go in `datasheets/` with a `.SOURCE.md` recording the
  URL, retrieval date, and document revision. Archive them when you cite them;
  vendors delete PDFs.
- Nothing real: no deployment location, member identity, callsign, credential,
  or operational capture. Strip photograph metadata. See `SECURITY.md`.

**Requires hardware:** yes, including the assembled enclosure. Bench

## Closing

Evidence here is necessary and not sufficient. Closure also needs an ADR
recording the decision and citing this path, the trade status set to
`CLOSED`, and `tools/validate-docs.sh` passing. See
`docs/trades/README.md`.
