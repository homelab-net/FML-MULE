# Procurement decision brief: getting hardware into the loop

**Purpose.** Owner decision support. Under `AGENTS.md`'s "evidence over
architecture" objective the pacing item is procurement, and this consolidates the
existing no-hardware evidence and the BOM's own acquisition gates so the calls are
actionable. It **decides nothing** -- the BOM-choosing trades close on hardware
the Owner accepts -- and it adds no architecture.

**Coordination.** The `HW-01A/B/C/D` decision-packet findings in
`docs/findings/register.yml` are Codex's register work and are not yet started.
This brief **feeds** them for the Owner's decision; it does not fork or close
them, and it must be reconciled with them before any trade closes. It does not
edit the register.

## The reframe: the current BOM already lets you order a lab article now

The single most useful thing this brief has to say: **almost none of the open
decisions blocks starting hardware.** `hardware/prototype/prototype-bom-revA.csv`
already lists an Article-0-class node and the instrumentation to characterise it,
all in `BUY NOW` (or `BUY 1 THEN VERIFY`) cells, none of which depend on the RF or
carrier decisions:

- **A node**: the `RELAY` line -- CM4 + Waveshare `CM4-IO-BASE-C` carrier, a
  printed **open frame**, and a **USB-C PD bench-power** sink -- `BUY NOW`.
- **Radios for a two-node mesh**: the HaLow `WM1302` HAT (`BUY NOW`) and the
  high-rate `QCA6174A` M.2 card (`BUY 1 THEN VERIFY` -- ordering one *to* verify
  is the point).
- **Instrumentation** the evidence phase needs (review §10): an inline DC
  power/energy logger and a thermocouple meter, both `BUY NOW`.

This is exactly the review's §4 "ugly Article 0 for diagnosis" -- bench power,
open frame, accessible connectors, test points -- and its §13 "delay cost
optimization": the battery, the enclosure, and the field radio/carrier choices
are for the **field** article and can wait. Two of these lab nodes reach M1 and
M2 on the demonstration ladder (`docs/ROADMAP-DEV.md`) and let the RF/Linux and
coexistence characterisation (review §5/§6) begin -- which is the work that
actually reduces the program's dominant uncertainty.

**Recommended action now:** order two lab nodes plus the shared instrumentation
from the existing `BUY NOW` / `BUY 1 THEN VERIFY` cells. Nothing below needs to be
decided first.

## The three field-article decisions (consolidated, not re-analysed)

These refine the **field** article. Each has some no-hardware evidence; none
closes without hardware. Directions are the Owner's to accept, not decisions.

### `TBR-RF-03` -- AP + mesh radio consolidation

- **Evidence:** one `SIMULATED` interface-combination bench
  (`docs/evidence/TBR-RF-03/2026-09-04-one-radio-ap-plus-mesh-hwsim.md`) and one
  `UNVERIFIED` analysis
  (`docs/evidence/TBR-RF-03/2026-09-06-consolidation-to-free-the-m2-slot.md`).
- **The finding that matters:** consolidation and freeing the M.2 slot are
  **separate levers**. Consolidating AP and mesh onto one radio has its own merit
  (power, panel space, one antenna set, airtime), but it frees the M.2 slot only
  if the surviving radio is off M.2 -- and the only non-M.2 options are the
  single-stream onboard part (not the high-rate mesh `FML-ADR-025` wants, mesh
  support unconfirmed) or a scarce, USB2-capped USB part. So consolidation is
  **not** the storage lever and should be decided on its own merits.
- **BOM implication:** whether the field node carries one Wi-Fi radio or two.
- **Direction:** keep AP and mesh separate for the lab article (the demonstrated,
  lower-risk path); decide consolidation for the field article on the airtime and
  power measurements the lab article produces.
- **Hardware to close:** `iw list` AP+mesh interface combination on the real
  QCA6174; `mesh point` support and rate on the onboard chip; live AP-vs-mesh
  airtime contention.

### `TBR-CARRIER-01` -- the M.2 slot: radio, or storage

- **Evidence:** none yet (`docs/evidence/TBR-CARRIER-01/` is empty); the question
  is whether repeatability justifies custom/semi-custom carrier hardware.
- **The finding that matters:** the common storage need does **not** need the M.2
  or a new carrier. The map repository is read-mostly and served a tile at a time,
  so a **USB2 SSD with the QCA6174 kept on M.2** gives high-rate mesh **and** map
  storage on the current BOM, no slot freed and no carrier change (the RF-03
  analysis, above). A second M.2/NVMe path is needed only for the **write-heavy**
  case -- PostgreSQL, the `FML-ADR-050` write-amplification concern that
  `TBR-COMP-01`'s USB2-SSD test article characterises.
- **BOM implication:** whether the field article keeps the single-slot Waveshare
  carrier (+ USB2 SSD) or moves to a carrier with a radio slot **and** NVMe.
- **Root of trust (from `TBR-SEC-01`):** per the unlock-method analysis
  (`docs/evidence/TBR-SEC-01/2026-09-20-unlock-method-comparison.md`, trade still
  `OPEN`), **if** the Owner accepts unattended field restart, a hardware root of
  trust -- **TPM 2.0 or a secure element; which one is `TBR-SEC-01`'s to select** --
  becomes a carrier-provision requirement. Unlike the NVMe question above, this
  footprint (a TPM header, or a secure-element part on SPI/I2C) **cannot be
  deferred past board lock**, and it contends for the 40-pin header the WM1302
  HaLow HAT uses. This records the provision the Owner must decide; it neither
  selects the mechanism nor asserts unattended restart is required.
- **Direction:** the current single-slot carrier + USB2 SSD suffices for the lab
  article and for maps; defer the NVMe/carrier question to the write-heavy service
  evidence -- **but decide the root-of-trust provision before board lock**, since a
  TPM/secure-element footprint cannot be added after the board is chosen.
- **Hardware to close:** whether a candidate carrier exposes radio + NVMe
  together, and whether it can also carry a TPM/secure-element without losing the
  40-pin header; the USB2 SSD read/write behaviour under the real service load.

### `TBR-COMP-01` -- compute memory and storage class

- **Evidence:** the service plane sizes at **~650 MB resident** at idle,
  `SIMULATED`, measured from the running reference stack
  (`docs/evidence/TBR-COMP-01/2026-09-06-service-plane-steady-state-footprint.md`).
- **BOM implication:** 4 GB versus 8 GB CM4. The BOM's `NODE-CORE` compute is the
  8 GB CM4; the `RELAY` lab node is a 2 GB CM4, adequate for the network-plane
  demonstrations.
- **Direction:** the ~650 MB idle figure plus the network-plane reserve, the OS,
  and headroom is the input to the class call. The roadmap Bank C two-tier model
  splits it: the **carry node** targets **4 GB (core profile)**, while **8 GB (the
  media profile)** is the **TOC/aggregation** node where the heavy contributors
  concentrate -- a live RoIP session (post-`CCR-03`), an SFU, or multiple video
  streams. So RoIP pushes the **media/TOC** profile toward 8 GB, not necessarily
  the carry node. The Owner makes the per-profile class call with the arm64 peak
  below; **8 GB is a profile assignment pending that peak, not a measured figure.**
- **Image arch (GAP-09F/G, noted not owned here):** the stack must run on the
  arm64 carrier, so image selection must pin **arm64 or multi-arch** digests; the
  upstream base images are multi-arch, so the OTS custom build is the only arch
  risk. Tracked in roadmap Bank C and owned by GAP-09F/G.
- **Hardware to close:** the arm64/CM4 resident and CPU figures, and the **peak**
  under start-up, mesh reconfiguration, an association storm, and (post-`CCR-03`)
  a live RoIP session, with the network plane co-resident.

## Recommended procurement sequence

1. **Now:** order two lab nodes and the shared instrumentation from the existing
   `BUY NOW` / `BUY 1 THEN VERIFY` cells. No field decision required.
2. **On arrival:** characterise the RF/Linux boundary and coexistence on them
   (review §5/§6; the `HW-01E/F/G/H` findings), and run the existing benches and
   software digital twin against the real interfaces to find which fakes were lying
   (`docs/ROADMAP-DEV.md`, Track 2 day one).
3. **Then:** make `TBR-RF-03`, `TBR-CARRIER-01` and `TBR-COMP-01` on **that**
   evidence, reconciled with Codex's `HW-01A/B/C` packets.
4. **Then:** authorise the field BOM (`TBR-HW-01`; the `HW-01D` finding).

Hardware paces steps 2-4; only step 1 is available today, which is why step 1 is
the recommendation.

## Honesty guards (review §14)

- `SIMULATED` is not RF evidence. The RF-03 interface-combination result is
  `mac80211_hwsim`; it says nothing about a real radio's airtime or rate.
- The RF-03 analysis is `UNVERIFIED`, and every chip-capability claim in it is
  marked as needing confirmation on that specific chip. A datasheet is not
  integrated RF performance.
- The `~650 MB` footprint is an x86 container measurement, not the arm64/CM4
  figure and not a peak.
- This brief enables a **prototype** decision on current evidence; the trades
  **close** only on hardware accepted by the Owner.

## Sources

`hardware/prototype/prototype-bom-revA.csv`; the evidence artifacts cited above;
`docs/trades/TBR-RF-03-*`, `TBR-CARRIER-01-*`, `TBR-COMP-01-*`, `TBR-HW-01-*`;
`docs/ROADMAP-DEV.md` ("Before the BOM", "Phase intent"); the `HW-01*` findings in
`docs/findings/register.yml`. Nothing real: the parts named are BOM line items.
See `SECURITY.md`.
