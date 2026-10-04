# Evidence for TBR-LINUX-01

**Trade:** Kernel and out-of-tree driver viability

**Trade file:** `docs/trades/TBR-LINUX-01-kernel-and-out-of-tree-driver-viability.md`

**Priority:** 8 of 16 (SAD v0.31 section 30.2). **Function owner:** Linux/Platform.
**Named owner:** Cameron Zobrist.

**Current contents:** the following artifacts. This trade remains `OPEN`;
an artifact's presence is not owner acceptance.

- [2026-08-30-80211s-mesh-in-software.md][artifact-1]
- [2026-08-30-batman-v-available-on-debian.md][artifact-2]
- [2026-08-30-wireless-adapter-survey.md][artifact-3]
- [2026-08-31-halow-driver-mesh-and-sae-support.md][artifact-4]
- [2026-08-31-originator-count-differs-by-interface-order.md][artifact-5]
- [2026-10-01-infrastructure-wifi-prototype.json][artifact-6]
- [2026-10-01-infrastructure-wifi-prototype.md][artifact-7]
- [2026-10-01-infrastructure-wifi-prototype.txt][artifact-8]

- [2026-10-01-power-ble-followup-node-a.md][ble-followup]

The [October 2 follow-up][radio-followup] records successful retained-bond
BLE API access and actual LoRa carriage after a normal physical RAK reset.
The USB descriptor fault and current undervoltage observations remain unresolved;
successful BLE is not USB repair or a power-envelope result.

[radio-followup]: ../TBR-NET-02/2026-10-02-three-node-lab-boundaries.md
[ble-followup]: 2026-10-01-power-ble-followup-node-a.md

[artifact-1]: 2026-08-30-80211s-mesh-in-software.md
[artifact-2]: 2026-08-30-batman-v-available-on-debian.md
[artifact-3]: 2026-08-30-wireless-adapter-survey.md
[artifact-4]: 2026-08-31-halow-driver-mesh-and-sae-support.md
[artifact-5]: 2026-08-31-originator-count-differs-by-interface-order.md
[artifact-6]: 2026-10-01-infrastructure-wifi-prototype.json
[artifact-7]: 2026-10-01-infrastructure-wifi-prototype.md
[artifact-8]: 2026-10-01-infrastructure-wifi-prototype.txt

This directory exists before the work does, deliberately. The closure gate is
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

**Requires hardware:** Requires a candidate compute module, a HaLow radio, and the two-node HIL bench.

## Closing

Evidence here is necessary and not sufficient. SAD section 30.2: a TBR closes
only when its listed evidence exists, **the named owner accepts the evidence**,
and the resulting architecture decision is entered into the persistent ADR
register.

Closing a trade whose named owner is still `TBD-SRR` is not possible, because
there is nobody to accept the evidence. This trade's owner was named on
2026-10-02, so that bar is cleared; it says nothing about whether the evidence
below meets the gate.
