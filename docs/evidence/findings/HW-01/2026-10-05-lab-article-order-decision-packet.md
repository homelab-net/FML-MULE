# HW-01 decision packet: radios and instruments for the existing lab

**State:** `AWAITING_USER_DECISION`. **Finding:** `HW-01`, "Establish a
qualified hardware path". **Prepared:** 2026-10-05. **Author:** Claude agent,
cloud session. **Independent verifier:** a separate agent reviewed this draft
before submission and its corrections are applied. **Tier:** analysis only;
nothing exercised.

## 1. Decision requested

`hardware/prototype/procurement-decision-brief.md` recommends, as its step 1,
ordering "two lab nodes and the shared instrumentation" from the prototype
BOM's `BUY NOW` and `BUY 1 THEN VERIFY` cells. The Program Owner confirmed on
2026-10-05 that this has not been ordered. This packet narrows that
recommendation to what the next demonstration needs, and asks for one
decision, with two options the Owner may add:

- **A (recommended):** two HaLow kits for the two Pi 4B lab articles already
  owned, plus the shared instruments.
- **B (option):** one CM4 node carrying the QCA6174A to verify, for the
  `TBR-RF-03` hardware questions.
- **C (option):** a third HaLow node, for multi-hop and topology change.

It decides none of `TBR-RF-03`, `TBR-CARRIER-01` or `TBR-COMP-01`, and it is
not the `HW-01D` field-BOM authorization.

## 2. The sequencing this has to respect

The Program Owner's goal (2026-09-05, `docs/ROADMAP-DEV.md`, "Before the BOM"):
"use the current bench to de-risk as much as possible **before any prototype
material is ordered**". Bank C applies it to the decisions that choose the BOM:
"Making them after the purchase is how the wrong parts get bought. None needs
the prototype", and its last bullet names "The prototype BOM itself
(`hardware/prototype/`)".

The brief instead recommends ordering lab nodes before those decisions.

- **Option A does not depart from Bank C.** The HaLow radio is already selected
  (`FML-ADR-024`), and Bank B already makes the Pi 4B the test compute: "The
  **prototype/test compute is the Raspberry Pi 4B (8GB)** ... Its **core
  configuration** is onboard Wi-Fi as the EUD AP, HaLow (WM1302 HAT over SPI) as
  the long-range backbone". The instruments choose no BOM part.
- **Option B departs from it.** It buys a CM4 and a Waveshare `CM4-IO-BASE-C`
  carrier, which sit on the `TBR-COMP-01` and `TBR-CARRIER-01` axes. It also
  goes against Bank B, which defers the high-rate plane because "the Pi 4B
  exposes no PCIe for the QCA6174". Approving B is approving that departure.

## 3. Why A now

- M2 needs two nodes forming the selected mesh. No radio in the lab supports
  `mesh point`, checked 2026-10-02 (`docs/ROADMAP-DEV.md`, item 1.7).
- `docs/bench-hardware-bringup.md` already plans this cart: "a Pi 4B (8 GB) node
  ... a HaLow radio (Wio-WM6108 on the WM1302 HAT over SPI, ...)". Its step 1 is
  HaLow driver bring-up on our Debian kernel (`TBR-LINUX-01`), "the dominant
  program uncertainty". Its step 2 starts with "two real HaLow nodes on one
  802.11s mesh", single hop first.
- The meter and thermocouple logger are the instruments `TBR-PWR-01` and
  `TBR-THERM-01` need. The brief lists both as instrumentation the evidence
  phase needs.

## 4. What to order

Quantities and prices are the BOM's. Row numbers count the CSV header as row 1.
The `Price Basis` column is reproduced because several prices are estimates,
not quotes.

### Option A (recommended)

| Line | BOM row | Qty | Unit | Extended | Price basis |
| --- | --- | ---: | ---: | ---: | --- |
| Seeed Wio-WM6108 US915-SPI HaLow module | 31 | 2 | 14.99 | 29.98 | v0.2 sourced |
| Seeed WM1302 Pi HAT | 32 | 2 | 19.90 | 39.80 | v0.2 sourced |
| HaLow pigtail + 902-928 MHz antenna | 33 | 2 | 9.90 | 19.80 | v0.2 sourced |
| Inline DC power meter / logger | 36 | 1 | 35.00 | 35.00 | v0.2 sourced |
| Thermocouple meter + probes | 37 | 1 | 35.00 | 35.00 | v0.2 sourced |
| USB-C 100 W PD source | 38 | 1 | 30.00 | 30.00 | Estimate (Claude) |
| **Total** | | | | **189.58** | 30.00 of it estimated |

### Option B adds one CM4 node for the QCA6174A

| Line | BOM row | Qty | Unit | Extended | Price basis |
| --- | --- | ---: | ---: | ---: | --- |
| Compute Module 4, 2 GB, Lite, Wi-Fi (`CM4102000`) | 28 | 1 | 60.00 | 60.00 | Estimate (Claude) |
| Waveshare `CM4-IO-BASE-C` carrier | 29 | 1 | 21.99 | 21.99 | v0.2 sourced |
| microSD 32 GB industrial | 30 | 1 | 10.00 | 10.00 | Estimate (Claude) |
| USB-C PD sink / bench power | 34 | 1 | 8.00 | 8.00 | Estimate (Claude) |
| Printed open frame / mount | 35 | 1 | 8.00 | 8.00 | Estimate (Claude) |
| SparkLAN QCA6174A M.2 2230 | 8 | 1 | 36.90 | 36.90 | v0.2 sourced |
| Passive M.2 M-key to A/E-key adapter | 9 | 1 | 9.68 | 9.68 | v0.2 sourced |
| **Total** | | | | **154.57** | 86.00 of it estimated |

This is this packet's own composition, not a BOM class. It takes the BOM's
`RELAY` compute, carrier, boot and power lines, which row 31 describes as
"HaLow only. No high-rate radio", and puts the `NODE-CORE` radio on it instead
of HaLow. It answers the first two items of the brief's "Hardware to close" for
`TBR-RF-03`: "`iw list` AP+mesh interface combination on the real QCA6174" and
"`mesh point` support and rate on the onboard chip". The second comes from the
CM4's onboard radio, not the QCA6174A. It does not answer `TBR-RF-01`: no
high-rate antennas are ordered (row 10 is `BUY AFTER RADIO VERIFY`), so no link
can be measured, only driver enumeration.

### Option C adds one more HaLow kit

Rows 31-33, 44.79. Option C needs a
third host with a 40-pin header. The BOM's `RELAY` class is "Minimal third node
so Stage 2 can test multi-hop, relay, topology change, and BATMAN
reconvergence. Two nodes cannot answer any of those." With B, the CM4 node is
that host if its carrier exposes the 40-pin header the HAT needs (a fit check).
Without B, the host is a `RELAY` set (rows 28-35, 152.78 for one).

### Fit checks the BOM already carries go with the order

- WM1302 HAT (row 6, the same part as row 32): "FIT CHECK: confirm the HAT
  passes through or stacks the GPIO header - the I2C display and EMCON button
  need it."
- WM6108 (row 5): "SPI caps HaLow throughput below the radio's capability -
  measure the ceiling in Stage 2; it constrains voice-over-HaLow."
- For B, QCA6174A (row 8): "Highest-risk item in the BOM; correctly gated to one
  unit." M.2 adapter (row 9): "Verify PCIe routing, stack height, and kernel
  enumeration before quantity two."
- For B, the PD sink (row 34) and the 20 V/5 A source (row 38): confirm the
  carrier's supply input before first power-on. The BOM does not state it.

## 5. Consequences

- Whether the Morse Micro driver loads and fields 802.11s on the stock Debian
  kernel is `TBR-LINUX-01`'s question, and the first thing A answers. This packet
  does not assume it.
- The Pi 4Bs gain HaLow. They are the `FML-ADR-088` article, so the repository
  image and the HaLow bring-up meet on the same hardware.
- For B: `FML-ADR-088`'s boot-file check names `bcm2711-rpi-4-b.dtb`. A CM4 boots
  from a different device tree, so running the repository image on it means
  extending that check. The `raspi-firmware` hook copies every `bcm*.dtb`.
- Lab reconciliation is deferred by the Program Owner (2026-10-04). Newly
  provisioned radios should be configured from the repository, not by hand, so
  they do not join the divergence recorded in
  `docs/evidence/TBR-HA-01/2026-10-02-deployed-recovery-policy-and-repo-divergence.md`.

## 6. Recommendation

Approve option A. It is the cheapest order that reaches M2 on the selected
backbone, and it stays inside the Owner's own sequencing. Take B only as a
deliberate departure, if `TBR-RF-03`'s direction is wanted from a real QCA6174
before the BOM decisions rather than after. Take C when multi-hop is next.
Record real prices and received parts in a follow-up `HW-01` artifact.

## 7. Owner disposition

Pending. On 2026-10-10 the Program Owner said option A is "not yet" ordered.
The same day the Owner reported buying two ALFA AWUS036ACM adapters, which are
in none of options A, B or C. They are bench radios for the 802.11s single step
(`docs/evidence/TBR-RF-01/2026-10-10-awus036acm-one-hop-mesh-card.md`), and
they do not change this packet's recommendation: they are not HaLow, and they
are not the `TBR-RF-03` radio. Their price and receipt go in the follow-up
`HW-01` artifact section 6 asks for, once they are received.
