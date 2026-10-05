# HW-01 decision packet: order the lab articles now

**State:** `AWAITING_USER_DECISION`. **Finding:** `HW-01`, "Establish a
qualified hardware path". **Prepared:** 2026-10-05. **Author:** Claude agent,
cloud session. **Independent verifier:** a separate agent reviewed this draft
before submission. **Tier:** analysis only; nothing exercised.

## 1. Decision requested

Approve ordering the lab articles that
`hardware/prototype/procurement-decision-brief.md` recommends as its step 1:
two lab nodes, one high-rate radio to verify, and the shared instruments, all
from cells of `hardware/prototype/prototype-bom-revA.csv` gated `BUY NOW` or
`BUY 1 THEN VERIFY`. The Program Owner confirmed on 2026-10-05 that this order
has not been placed.

This approves a purchase for a **lab** article. It decides none of
`TBR-RF-03`, `TBR-CARRIER-01` or `TBR-COMP-01`, and it is not the `HW-01D`
field-BOM authorization.

## 2. Why now

- Procurement is the pacing item ahead of M1 (`docs/ROADMAP-DEV.md`, the
  demonstration ladder).
- M2, two nodes forming the selected mesh, cannot run on the current lab: no
  radio there supports `mesh point` mode, checked 2026-10-02
  (`docs/ROADMAP-DEV.md`, item 1.7). The radios below are the selected bearers'
  radios.
- The brief's own finding: "almost none of the open decisions blocks starting
  hardware." Its sequence makes the three field decisions **on** the evidence
  these articles produce (brief, "Recommended procurement sequence", step 3).
- Roadmap Bank C says to make those three decisions before the purchase:
  "Making them after the purchase is how the wrong parts get bought." That
  applies to the field BOM. This order buys none of the parts those decisions
  choose between beyond the single gated radio, which the BOM already orders
  one of in order to verify it.

## 3. What to order

Quantities and prices are the BOM's, row by row. The `Price Basis` column is
reproduced because several prices are estimates, not quotes.

| Line | BOM row | Qty | Unit | Extended | Price basis |
| --- | --- | ---: | ---: | ---: | --- |
| Compute Module 4, 2 GB, Lite, Wi-Fi (`CM4102000`) | `RELAY` row 28 | 2 | 60.00 | 120.00 | Estimate (Claude) |
| Waveshare `CM4-IO-BASE-C` carrier | row 29 | 2 | 21.99 | 43.98 | v0.2 sourced |
| microSD 32 GB industrial | row 30 | 2 | 10.00 | 20.00 | Estimate (Claude) |
| Seeed Wio-WM6108 US915-SPI HaLow module | row 31 | 2 | 14.99 | 29.98 | v0.2 sourced |
| Seeed WM1302 Pi HAT | row 32 | 2 | 19.90 | 39.80 | v0.2 sourced |
| HaLow pigtail + 902-928 MHz antenna | row 33 | 2 | 9.90 | 19.80 | v0.2 sourced |
| USB-C PD sink / bench power | row 34 | 2 | 8.00 | 16.00 | Estimate (Claude) |
| Printed open frame / mount | row 35 | 2 | 8.00 | 16.00 | Estimate (Claude) |
| SparkLAN QCA6174A M.2 2230 | `NODE-CORE` row 8 | 1 | 36.90 | 36.90 | v0.2 sourced |
| Passive M.2 M-key to A/E-key adapter | row 9 | 1 | 9.68 | 9.68 | v0.2 sourced |
| Inline DC power meter / logger | `SHARED` row 36 | 1 | 35.00 | 35.00 | v0.2 sourced |
| Thermocouple meter + probes | row 37 | 1 | 35.00 | 35.00 | v0.2 sourced |
| USB-C 100 W PD source | row 38 | 1 | 30.00 | 30.00 | Estimate (Claude) |
| **Total** | | | | **452.14** | 202.00 of it estimated |

Row numbers count the CSV's header as row 1. The `RELAY` rows are a set the
BOM lists once; this packet orders two sets, because the brief's "two lab
nodes" are two of that set. The BOM's `RELAY` note calls the class "a test
asset, not a field article".

**The fit checks the BOM already carries go with the order, not after it:**

- QCA6174A (row 8): "Highest-risk item in the BOM; correctly gated to one unit."
- M.2 adapter (row 9): "Verify PCIe routing, stack height, and kernel
  enumeration before quantity two."
- WM1302 HAT (row 6, the same part as row 32): "FIT CHECK: confirm the HAT
  passes through or stacks the GPIO header."
- WM6108 (row 5): "SPI caps HaLow throughput below the radio's capability -
  measure the ceiling in Stage 2."

## 4. What it unblocks

- **M2** on the HaLow bearer: two nodes and the selected mesh. Whether the
  WM6108's driver fields 802.11s on these kernels is `TBR-LINUX-01`'s question
  and the first thing the articles answer; this packet does not assume it.
- **`TBR-RF-01` and `TBR-RF-03`**: the brief's "Hardware to close" for
  `TBR-RF-03` is `iw list` on the real QCA6174, `mesh point` support, and live
  AP-versus-mesh contention. One QCA6174A on one node answers the first two.
- **`TBR-PWR-01` and `TBR-THERM-01`**: the meter and thermocouple logger are
  the instruments their measurements need.
- **`TBR-COMP-01`**: the arm64 resident and CPU figures the brief says close the
  memory call, on a CM4.

## 5. Consequences

- The lab gains CM4 articles beside the two Pi 4Bs. `FML-ADR-088`'s profile is
  for the Pi 4B. A CM4 boots from a different device tree, so running the
  repository image on these articles is a follow-on to that profile, not part
  of it. The arm64 profile work does not wait on this order, and this order does
  not wait on the profile.
- The `RELAY` compute is the 2 GB Lite CM4, which the brief calls "adequate for
  the network-plane demonstrations". It is not the 4 GB versus 8 GB
  `TBR-COMP-01` call, and its figures are lab figures.
- Lab reconciliation is deferred by the Program Owner (2026-10-04). New articles
  should be provisioned from the repository, not by hand, so they do not join
  the divergence recorded in
  `docs/evidence/TBR-HA-01/2026-10-02-deployed-recovery-policy-and-repo-divergence.md`.

## 6. Alternatives

- **Wait for the three field decisions first** (Bank C read strictly). Each of
  them names hardware evidence to close (brief, "Hardware to close" under each),
  so waiting defers the order without making the decisions closable.
- **Fewer parts**: one lab node instead of two. M2 needs two nodes, so this buys
  RF and power characterisation but not the mesh.

## 7. Recommendation

Approve the order in section 3 as written, including the two estimated price
basis lines, which the order itself will replace with real prices. Record the
real prices and the received parts in a follow-up `HW-01` artifact.

## 8. Owner disposition

Pending.
