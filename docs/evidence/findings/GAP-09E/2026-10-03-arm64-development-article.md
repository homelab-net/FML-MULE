# A Raspberry Pi 4B as the v0.0.1 development article

**Finding:** `GAP-09E`.
**Date:** 2026-10-03.
**Taken by:** Repository agent, read-only over SSH to the lab node.
**Status of this artifact:** `UNVERIFIED`. It records a decision and the
observations behind it. Nothing was executed on the radio and no measurement was
taken.

## What this records

A Raspberry Pi 4B (`pi-mule-1`) is used as the article for `v0.0.1` / gate M1 --
one node, its EUD access point, one service reachable from a phone. Its
descriptor is `nodes/pi-mule-1/node.yml`.

**It is a development article and not a hardware selection.** The precedent is
`GAP-09A`, which recorded an Intel N150 as a development-only compute article
and said plainly that it "does not select or qualify a production article".
`TBR-HW-01` is `OPEN`; its gate requires every dependency trade `CLOSED` and a
written, repeatable block acceptance procedure, and this is neither.

`nodes/mule-v001/node.yml` is deliberately **not** edited to point at this
board. That file is the field prototype and its device map is correctly `TBD`
until one is assembled. Filling it in would make the repository assert that the
v0.0.1 node is the BOM article, which is `AGENTS.md` waste 2 committed in two
lines.

## Observations behind the descriptor

Read from the board on 2026-10-03. Device names from `/sys/class/net`, driver
from `/sys/class/ieee80211/phy0/device/driver`, channel from `iw list`.

| Field | Value | Note |
| --- | --- | --- |
| Host | Raspberry Pi 4 Model B Rev 1.4 | |
| OS / kernel | Debian 13, `6.18.50+rpt-rpi-v8` aarch64 | A stock distribution kernel, **not** an `os/image/` artifact |
| `wan` | `eth0` | Carrier present. The field prototype's WAN is also Ethernet, so this role is not a stand-in |
| `eud_ap` | `wlan0`, driver `brcmfmac` | |
| `ap_channel` | 149 | `iw list`: "5745.0 MHz [149] (20.0 dBm)", no radar flag |

Two limits read off the radio, both worth recording before anyone plans around
them:

- **One BSS.** phy0 reports `#{ AP } <= 1` and an empty "software interface
  modes" list. The second, time-bounded onboarding BSS that `FML-ADR-084`
  describes **cannot be raised on this radio**. That is a constraint for
  `TBR-HW-01` to carry into block selection, not a defect to engineer around
  here.
- **The radio's ceiling is below the profile's.** `regions/us-915/profile.yml`
  carries `wifi.ap_max_eirp_dbm: 36`; this radio advertises 20 dBm on channel
  149. The radio wins. What it actually radiates is unmeasured and no EIRP claim
  follows.

## Why the channel is written in the descriptor

`test/bench/mule-ap-up.sh` falls back to channel 36 when `ap_channel` is absent.
`regions/us-915/profile.yml` sets 149, accepted by the Program Owner in
`docs/evidence/TBR-RF-03/2026-09-21-ap-channel-and-eirp-decision-packet.md`.
Leaving the key out would have let the bring-up script and the region profile
disagree silently, with the script winning on the air and the rendered
configuration claiming the other value.

## What this does not establish

- **No hardware selection.** `TBR-HW-01` is untouched.
- **No `TBR-LINUX-01` progress beyond the interface name.** Naming `wlan0`
  closes `GAP-09H`'s G2 for this article only. Driver viability, the
  kernel-promotion pipeline and rollback are all untouched, and the kernel here
  is a vendor distribution kernel outside the `FML-ADR-040` compatibility set.
- **Nothing was run.** No AP was raised, no client associated, no packet moved.
  The execution card in this directory is still a procedure, not a result.
- **Nothing about RF, power, thermal or timing.** A bare board with a PCB
  antenna on a bench.
- **This is not `mule-v001`**, and no statement here carries to the field
  prototype except what the shared CYW43455 part supports: driver and AP-mode
  behaviour. Antenna, board layout, enclosure and thermal do not carry.
