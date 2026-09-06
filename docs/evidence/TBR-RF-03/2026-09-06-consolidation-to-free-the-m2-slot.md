# Can AP-plus-mesh consolidation free the M.2 slot for a storage SSD?

**Tier:** analysis, `UNVERIFIED`. No hardware; reasoning from the BOM, the driver
capabilities, and the `SIMULATED` interface-combination evidence
(`2026-09-04-one-radio-ap-plus-mesh-hwsim.md`). Every capability claim below
about a specific chip is marked as needing confirmation on that chip.

## The question, and why it is really two trades

The prototype carrier (Waveshare CM4-IO-BASE-C) has **one** M.2 M-key slot, and
the BOM spends it on the QCA6174A high-rate radio, so there is no NVMe path --
only 32 GB eMMC and a USB2 SSD. The Program Owner asked whether the EUD access
point and the high-rate mesh could share **one radio and its antennas**, freeing
the M.2 slot for a storage SSD.

The answer splits the request in two: `TBR-RF-03` (does one radio do AP and mesh
at once) and `TBR-CARRIER-01` (does the freed slot, or a different carrier, carry
the SSD). They interact, and the interaction is the finding.

## What is already established

`2026-09-04-one-radio-ap-plus-mesh-hwsim.md` (`SIMULATED`): a mesh-capable
`mac80211` chip advertises `{ managed, AP, mesh point }` concurrent on one
channel, and an AP interface, an 802.11s mesh interface and an associated EUD ran
on one radio. **Two hard facts carry from it:** the RTL8812AU (the common
high-rate USB radio) has **no mesh mode** at all, and `hwsim` shows nothing about
RF, so the airtime contention between AP and mesh that `TBR-RF-03` names is
unmeasured and needs real radios.

## The radios in play, and which bus each sits on

- **Onboard CYW43455** (`brcmfmac`): today's EUD AP. Single spatial stream. Not
  on M.2 -- it is on the CM4 module itself. **Does `brcmfmac` on this chip
  advertise `mesh point`?** `brcmfmac` mesh support is partial and
  firmware-dependent; this must be read from `iw phy` on a real CM4, not assumed.
- **QCA6174A** (`ath10k`, 2x2): today's high-rate mesh radio, and the thing
  consuming the M.2 slot. Whether `ath10k` on this part advertises AP+mesh
  concurrent is an interface-combination question to read from `iw list` on the
  real card.

## The options, and what each costs

1. **Onboard CYW43455 carries AP and mesh; drop the QCA6174; M.2 frees for the
   SSD.** This is the only option that frees the slot with no new radio. Two
   costs, both to verify: `brcmfmac` may not offer `mesh point` on this chip at
   all; and even if it does, a single-stream 2.4/5 GHz part is **not the
   high-rate mesh** the plane exists for (`FML-ADR-025`). So this most likely
   buys the SSD by giving up the high-rate mesh -- a different node, not a
   consolidated one.
2. **A high-rate USB radio carries AP and mesh; the M.2 frees for the SSD.**
   Keeps throughput and frees the slot, *if* such a radio exists: it must
   advertise AP+mesh concurrent (the RTL8812AU does not), which points at an
   `ath10k`/`ath11k` or `mt76` USB part, and it is then USB2-capped on this
   carrier, which bounds the very throughput the swap was meant to keep. Sourcing
   and verifying that part is the real work here.
3. **Keep the QCA6174 on M.2 for the high-rate mesh; get the storage elsewhere.**
   This sidesteps consolidation and is, on the evidence, the cleaner path to the
   SSD: a **carrier with a second M.2 or an NVMe slot** (a `TBR-CARRIER-01`
   choice away from the single-slot Waveshare board) keeps the high-rate radio
   and adds NVMe; failing that, the USB2 SSD already in the BOM, or larger eMMC.

## The finding

**Radio consolidation and freeing the M.2 are not the same lever.** Consolidating
AP and mesh onto one radio has independent merit -- fewer radios, less power,
less panel space, one antenna set, and the airtime question `TBR-RF-03` owns --
but it frees the M.2 slot **only if the surviving radio is not on M.2**, and the
only non-M.2 radios available are the single-stream onboard part (not high-rate,
mesh support unconfirmed) or a USB part that is scarce for AP+mesh and USB2-capped
here. So the request as posed trades the high-rate mesh for the SSD.

If the goal is a storage SSD **without** losing the high-rate mesh, the evidence
points at `TBR-CARRIER-01` -- a carrier that offers a radio slot **and** an NVMe
path -- rather than at RF consolidation. Consolidation should be decided on its
own merits (power, space, airtime), not as the storage lever it cannot cleanly
be.

**But the storage need is not one need, and the common one does not need the
M.2 at all.** The CM4 has a single PCIe lane, spent on the QCA6174; NVMe and USB3
both want that lane, so neither is available while the high-rate radio holds it.
The CM4's **native USB2** does not touch the lane, and the BOM already frees both
USB2 ports (the RAK LoRa moved to UART for exactly this). A **USB2 SSD** with the
QCA6174 still on M.2 therefore gives **high-rate mesh plus mass storage on the
current BOM**, no slot freed and no carrier change. USB2's ~40 MB/s is tolerable
for the map repository, which is read-mostly and served a tile at a time. NVMe is
needed only for the **write-heavy** case -- PostgreSQL -- which is `FML-ADR-050`'s
write-amplification concern and what the BOM's USB2 SSD test article characterises
(`TBR-COMP-01`). So the M.2-versus-storage question is really about *fast* storage;
the **map store does not need it**, and neither the carrier change nor RF
consolidation is required to carry maps.

## What would confirm or overturn this, all needing hardware

- `iw phy` on a real CM4: does `brcmfmac`/CYW43455 advertise `mesh point`, and at
  what rate.
- `iw list` on the real QCA6174: the AP+mesh interface combination and channel
  constraint.
- A survey of USB parts (`ath10k`/`ath11k`/`mt76`) advertising AP+mesh concurrent,
  and their real throughput over USB2.
- Airtime contention between a live AP and a live mesh on one radio (`TBR-RF-03`'s
  own closure item).
- Whether a candidate carrier exposes a second M.2/NVMe alongside a radio slot
  (`TBR-CARRIER-01`).

## Bearing on the trades

- **`TBR-RF-03`:** consolidation is feasible at the interface-combination level on
  a mesh-capable chip, but it is not the M.2-freeing mechanism unless the radio
  moves off M.2, which costs either rate or a scarce USB part.
- **`TBR-CARRIER-01`:** the M.2-for-storage goal is more cleanly a carrier
  decision -- a board with radio *and* NVMe -- than an RF one.

Nothing real: no deployment detail; the parts named are BOM line items. See
`SECURITY.md`.
