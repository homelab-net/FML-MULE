# Prototype and test BOM

**This is not a production baseline. No hardware block is qualified and no
component is selected.**

SAD v0.31 section 33.3 is explicit about what this artifact is for:

> The next BOM is a **prototype/test BOM**, not a production baseline. It should
> buy the minimum alternatives and instrumentation required to resolve the
> critical TBRs.
>
> The prototype BOM answers: *what must be purchased to make the architecture
> decisions?* It is not the production answer.

| File | Contents |
| --- | --- |
| `prototype-bom-revA.csv` | 42 line items, transcribed from the source workbook. |
| `BOM-v0.4-DM32-RoIP-handoff.txt` | A received draft change package adding the DM-32UV voice radio and an audio/PTT RoIP gateway. **Received input, not an accepted baseline** -- see its `.README.md` for what it proposes and the blocking issues found on receipt, including a hard ADR-number collision. |

## Source and provenance

**FML/MULE Prototype BOM - Review Alternate (Claude), rev A**, derived from
FML/MULE Prototype BOM v0.2.

The source is an `.xlsx` workbook with four sheets: Summary, BOM, Gates and
Assumptions. The line items are committed here as **CSV** so they diff and
review as text, and the Summary, Gates and Assumptions content is transcribed
into this README.

The workbook itself is not committed. `.gitattributes` tracks `*.xlsx` with Git
LFS so that a future spreadsheet lands correctly, but a binary that cannot be
reviewed line by line is a poor home for a bill of material.

**Transcription check:** the CSV extended costs sum to 645.23 for `NODE-CORE`,
95.00 for `NODE-HOLD`, 152.78 for `RELAY` and 200.00 for `SHARED`, matching the
Summary sheet exactly.

## Price basis, and what these numbers are worth

This matters more than the totals.

| Basis | Meaning |
| --- | --- |
| `v0.2 sourced` | Carried forward verbatim from Prototype BOM v0.2, which records them as checked 2026-08-25. **Not independently re-verified.** |
| `Estimate (Claude)` | Estimates or allowances. **None are sourced quotes. Every one must be replaced with a real quote before procurement.** |

Excluded from every figure: shipping, tax, a final charger for the selected
pack, EUDs, and the time cost of volunteer assembly.

**The power figures behind the reasoning in this BOM — roughly 6-8 W idle with
radios, 9-11 W normal, 13-15 W hosting plus transfer — are engineering
estimates, not measurements. `TBR-PWR-01` supersedes them.** They do not appear
in the CSV and must not be quoted as MULE specifications.

## Test set composition

| Element | Qty | Note |
| --- | ---: | --- |
| Full field-configuration nodes | 2 | Complete build. Both are fit and function articles. |
| Minimal HaLow relay node | 1 | Bench-powered, no enclosure, no pack. Exists only to make multi-hop testable. |
| Shared test assets | 1 | Power, thermal, PD source, storage article, RF spares, consumables. |

## Cost model

| Line | Amount | Basis |
| --- | ---: | --- |
| Node core, per node (no pack) | 645.23 | All `NODE-CORE` lines |
| Battery allowance, per node | 95.00 | **HELD.** Not purchased at Gate 1. |
| Node with pack, per node | 740.23 | Core plus battery allowance |
| Two full nodes (no packs) | 1290.46 | |
| Minimal relay node | 152.78 | One unit |
| Shared test assets | 200.00 | One set |
| **Program total, three nodes, no packs** | **1643.24** | What is actually bought first |
| Program total, with two packs | 1833.24 | After the pack decision closes |

### Delta against Prototype BOM v0.2

| Metric | v0.2 | This BOM | Delta |
| --- | ---: | ---: | ---: |
| Node core, no pack | 541.10 | 645.23 | +104.13 |
| Node with pack | 633.25 | 740.23 | +106.98 |
| Nodes in test set | 2 | 3 | +1 |
| Program total, no packs | 1227.20 | 1643.24 | +416.04 |

Packs are excluded from both for a like-for-like comparison.

## What the delta buys

- **Third relay node.** Two nodes give one hop and no rerouting. CONOPS Stage 2
  asks about multi-hop, hop-count limits, topology change and multicast
  scaling — **none are testable with two nodes.** The highest-value line in this
  BOM.
- **USB-C PD power path.** Moves `TBR-PWR-01` off the critical path of a pack
  with zero stock and an unresolved charger. Measures power now rather than
  after the pack decision. `TBR-PWR-01` is priority 1 in the SAD register, so
  unblocking it is worth more than the part costs.
- **Taller enclosure section.** The v0.2 stack does not close in the available
  internal height before any pack. Same vendor, same IP rating, same STEP files.
- **Operator display and sealed button.** Closes the CONOPS section 67 status
  questions and the section 65 suppressible-illumination requirement, and gives
  EMCON a confirmation path that does not require a browser. Dark by default,
  momentary wake. A module of the Status Aggregator (`FML-ADR-046`), **not a new
  daemon**.
- **Non-metallic end panel.** One part serves the display window, an internal
  GNSS patch and RF transparency, removing an external GNSS feed from the
  six-feed envelope in SAD section 25.4.1. Attenuation must be tested, not
  assumed.
- **Connector keying, vent and thermal bridge.** Keying closes CONOPS section 38
  mechanically rather than by marking. The pressure-equalisation vent prevents
  moisture pumping in a sealed metal shell that heats under load and cools
  overnight. The thermal bridge makes the aluminium actually function as a heat
  path, which the enclosure card guides do not provide on their own.
- **USB2 storage test article.** Characterises the unresolved M.2 conflict: the
  carrier's single M-key slot is spent on the Wi-Fi card, leaving 32 GB eMMC for
  PostgreSQL, journald and Prometheus. Feeds `FML-ADR-050` and `TBR-COMP-01`.

## Procurement gates

Carried forward from v0.2 with two additions. The gate rules are the strongest
part of the original BOM and are unchanged in intent.

| Gate | Rule | Disposition |
| ---: | --- | --- |
| 1 | Buy RF and compute items that remain useful regardless of packaging outcome. | `BUY NOW` |
| 2 | Buy one enclosure and one M.2 key adapter first. Measure the stack and CAD-fit before quantity two. | `FIT ARTICLE` |
| 3 | **Do not buy any battery** until pack spec, charger path and enclosure integration close. Power the prototype from USB-C PD. | `HOLD POWER` |
| 4 | Do not call node recurring cost final until the pack decision and `TBR-PWR-01` close. | `COST RANGE ONLY` |
| 5 | **New.** Buy the relay node at Gate 1. It gates Stage 2, which gates the mesh scaling answer everything else depends on. | `BUY NOW` |
| 6 | **New.** Do not buy the connector panel hardware until the stack measurement fixes the panel layout and the four connector families are chosen. | `PANEL LAST` |

## Key assumptions, stated as assumptions

| Item | Assumption |
| --- | --- |
| Taller enclosure, $55 | Same enclosure family, one height step up, single-unit pricing scaled from the v0.2 part. Exact SKU selected only after the physical stack is measured. |
| Battery allowance, $95 | Placeholder for a flat 4S1P 18650 smart pack of roughly 50 Wh with BMS and fuel gauge. **No vendor identified.** A planning allowance, not a candidate. |
| Relay CM4 at $60 | A 2 GB Lite variant with Wi-Fi. Any spare CM4 or Pi 4 already on hand substitutes and reduces this to near zero. |
| Charge stage, $30 | An off-the-shelf wide-input CC/CV module. **If the selected pack requires SMBus-negotiated charging, this becomes a designed circuit and both cost and schedule rise.** |

## Engineering notes carried in the line items

Several notes in the CSV are findings rather than descriptions, and are worth
reading before ordering:

- **SPI caps HaLow throughput** below the radio's capability. Measure the
  ceiling in Stage 2; it constrains voice over HaLow.
- **The M.2 M-key slot is consumed** by the Wi-Fi adapter, so there is no NVMe
  path and 32 GB eMMC carries the database. See `FML-ADR-050`.
- **The LoRa module attaches by UART, not USB**, preserving both USB2 ports for
  TNC, storage or audio.
- **The printed internal sled must not sit between the compute module and the
  extrusion wall.** Printed plastic is an insulator, and the aluminium is the
  intended heat path.
- **A buck-only charge design silently fails the vehicle case**: 12-13.8 V is
  below a 4S 16.8 V termination. Hence the wide-input buck-boost stage.
- **21 mm cells give a pack that cannot stack inside the shell**, which is why
  the allowance assumes 18650 rather than 21700. A fuel gauge is a requirement
  driver from CONOPS section 67, not a luxury.
- **The integrated compute-module Wi-Fi is single-stream.** Adequate for 4-8
  EUDs; the exit criterion is Stage 1 client-count testing. This is the
  `FML-ADR-045` preference for the integrated radio in the EUD AP role.

## Deferred, with no BOM addition

- **Team PTT, Team Lead to Team Lead, and WAN VoIP.** EUD provides audio I/O.
  Software, QoS and test work only. Prefer wired headsets over Bluetooth for
  EMCON (CONOPS section 71).
- **Peer EUD video over the high-rate mesh.** Requires DSCP and WMM enforcement,
  not politeness.

Both are out of scope for v1 under CONOPS section 81 and remain so.

## Before any of this is ordered

- Every `Estimate (Claude)` price is replaced with a real quote.
- Every `v0.2 sourced` price is re-verified; it was checked 2026-08-25 and
  prices age.
- Every part is entered in `hardware/lifecycle/` with its lifecycle status.
- Every datasheet is archived under `docs/evidence/` at the moment it is cited.
  See SAD section 34 for the program's external source register.
- The regulatory position of each radio module is checked against
  `REGULATORY.md` and `regions/us-915/`.
