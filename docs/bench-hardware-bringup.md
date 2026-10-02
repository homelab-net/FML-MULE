# Hardware bring-up: the day the radios arrive

This is the execute-on-arrival runbook for the first real radios. Its purpose is
that bring-up follows a **known sequence instead of an experiment**: the bench
procedures in `test/bench/` already exercise the stack on `mac80211_hwsim`
(`SIMULATED`, no radio); this converts them to the first real-RF evidence.

**Status.** Every step here is a procedure to run, not a result. Nothing becomes
`HARDWARE-VERIFIED` until it is run and its evidence is recorded under
`docs/evidence/<TRADE>/`. Run on a development machine as root; none of this runs
in CI, because a hosted runner has no wireless stack (`docs/dev-machine.md`).

## Rules that apply to every step

- **Single step first.** Prove the boring case before the interesting one. This
  program spent five runs debugging "multi-hop routing" when the fault was that
  no two nodes could exchange one packet. Each section below gates on a
  one-hop/one-message success before anything multi-node.
- **Select radios by driver, never by name.** The `test/bench` scripts pick from
  the device tree under `/sys` by driver, never by interface name; do the same by
  hand. A fuzzy name match once grabbed the real WAN radio and broke it.
- **Configure the bench the way the program decided.** batman-adv is BATMAN-IV
  (`FML-ADR-053`), configured from `os/config/batman-adv.conf.template`; a wired
  or second bearer joins the mesh with `batctl interface add`, **never** a bridge
  holding the mesh interface and an uplink together (`FML-ADR-056`,
  `bridge_loop_avoidance`). A rig left at a default is testing the option the
  program rejected.
- **Record provenance.** Capture the kernel version (`uname -r`), the radio and
  driver, and the image build alongside every result; fixtures go in
  `test/fixtures/` with that metadata.

## Prerequisites

The bench cart: a Pi 4B (8 GB) node on a Debian host or the MULE image; a HaLow
radio (Wio-WM6108 on the WM1302 HAT over SPI, or an MM8108 USB dongle); the
RAK4631 LoRa node plus the partner Meshtastic node already in range; and the Alfa
AWUS036ACM for the high-rate plane. `.venv-lora/bin/meshtastic` is the LoRa
client.

## Step 1 -- HaLow driver bring-up (`TBR-LINUX-01`)

The dominant program uncertainty: does the Morse Micro driver build and load on
our Debian kernel. `FML-ADR-024` selects HaLow; `FML-ADR-023` says consume the
OpenMANET wireless configuration as reference.

1. Record `uname -r` first -- the whole question is "on *this* kernel."
2. Build/load the vendor driver + firmware for the radio (WM6108/MM8108). Confirm
   the module loads without taint and a `wlan*`/mesh-capable interface appears.
3. `iw <phy> info` -- confirm the interface advertises **mesh point** (the real
   Realtek radios on the dev box do not; that is why hwsim was necessary).
4. Bring the interface up, confirm firmware loaded, run a scan, and associate to a
   second HaLow radio.

**Gate:** driver loaded, interface up, firmware loaded, one association. Do not
proceed to the mesh until a HaLow link associates. **Evidence:**
`docs/evidence/TBR-LINUX-01/`, with the kernel version and driver revision.

## Step 2 -- real 802.11s + batman-adv mesh (`TBR-RF-01`)

Run the existing procedures on real radios instead of `mac80211_hwsim`.

1. **Single step:** two real HaLow nodes on one 802.11s mesh, joined into
   `batman-adv` per the template; assert **one** ICMP echo crosses. A failure
   here is PHY/association/config, never routing.
2. **Multi-hop:** reproduce `test/bench/80211s-mesh.sh --line`'s topology on real
   radios -- node 1 cannot hear node 3, node 2 relays -- and confirm reachability
   only through the relay. This is real-RF multi-hop, which nothing in the repo
   has yet shown.
3. **Transport:** run `test/bench/mesh-traffic.sh` (`latency`, `contention`) over
   the real link. Its numbers are `SIMULATED` on hwsim; on real radios they
   become the first real-RF transport datapoint. `TBR-RF-01` owns the QoS
   mechanism; this advances, it does not close, the trade.

**Gate:** the one-packet single step passes before multi-hop; the bench uses the
decided `batman-adv` config (`bridge_loop_avoidance`, `batctl interface add`).
**Evidence:** `docs/evidence/TBR-RF-01/`.

## Step 3 -- Meshtastic / LoRa (`FML-ADR-026`)

1. Identify the RAK's serial device by driver, not by guessing `/dev/ttyACM*`
   (the Waveshare SX1262 DTU may hold `ttyACM0`; it is test equipment, not a
   node). `meshtastic --port <dev> --info` -- confirm firmware, `hwModel`, region;
   set region US if unset.
2. Put the RAK on the same channel/preset/region as the partner (if the partner is
   off the default public channel, match its channel URL/PSK -- bench-only, never
   committed). A stock node holds the compiled-in public LongFast channel for its
   region.
3. **Wait for the NodeInfo exchange before any direct message.** A PKI **direct**
   message NAKs `NO_CHANNEL` until the sender holds the recipient's public key,
   which arrives in a `NODEINFO_APP` packet -- so confirm the partner appears in
   `meshtastic --port <dev> --nodes` **with a public key** first (a broadcast from
   the RAK, or from the partner, seeds this; it can take minutes). Broadcast and
   channel-addressed traffic do **not** need it and work immediately; only the PKI
   DM does. (Evidence:
   `docs/evidence/TBR-NET-02/2026-09-27-one-lora-hop-to-a-partner-node.md`.)
4. **Single step:** assert one text message crosses **both ways** -- a broadcast
   the partner receives, and a direct message that returns a delivery ACK once the
   key exchange (step 3) is done. Note: opening the RAK's USB serial port resets
   the nRF52840, so leave it undisturbed while the partner replies. Do not proceed
   until one message crosses each way.
5. **Grounding:** attach the RAK to the live OTS bench, send a GeoChat DM and a
   group message, and capture how `GeoChat.to` (recipient) and `Contact.callsign`
   (sender) ride the wire -- the real encoding `mule/recipients.py` and
   `FML-ADR-070` are waiting on. **Evidence:** `docs/evidence/TBR-NET-02/`.

### Current lab result and next repeat

The [October three-node record][lab-carriers] completed an addressed real LoRa
hop to the phone through Wi-Fi and bench TAK, and received the actual phone reply
back over RF while the synthetic sender stayed connected. This used private
controlled-fixture instrumentation and desktop coordination; it does not
complete the persistent upstream gateway part of Step 3 or its group/unknown
recipient controls. Antenna geometry and ambient conditions were not recorded,
so the radio-reported RSSI/SNR from that run are **not published** as
measurements.

For the next repeat, keep the intended EUD identity in native GeoChat.to,
correlate a unique reply with source/destination UID and received RF bytes, and
keep clients live through the reply. Record configuration differences from main
and interventions before assigning a result. **Record the measurement
configuration before the first packet**, not after: antenna model, orientation,
separation and ambient conditions, alongside the LoRa settings. That is the one
thing the October run cannot be corrected into supplying, and it is why its
signal-strength numbers are unpublishable. The next autonomous demonstration is
boot-to-gateway plus radio reconnect and intended-only/unknown-recipient RF
controls, using the selected upstream integration rather than a new protocol.

[lab-carriers]: evidence/TBR-NET-02/2026-10-02-three-node-lab-boundaries.md

## Step 4 -- compute and service plane under load (`TBR-COMP-01`, hardware half)

The size half is banked (~650 MB idle,
`docs/evidence/TBR-COMP-01/2026-09-06-service-plane-steady-state-footprint.md`).
The open half is the **peak** on real arm64 hardware.

1. Bring the service plane up on the Pi node (`test/bench/service-plane-footprint.sh`
   as the idle baseline on arm64).
2. Measure the peak under startup, an EUD association storm, and a CoT flood with
   the network plane co-resident -- the figures the 4 GB-vs-8 GB call is made
   against. **Evidence:** `docs/evidence/TBR-COMP-01/`.

## What closes, and what only advances

| Step | Trade | On success |
| --- | --- | --- |
| 1 | `TBR-LINUX-01` | the dominant uncertainty gets its first real answer |
| 2 | `TBR-RF-01` | advances (QoS mechanism stays the trade's); first real-RF mesh |
| 3 | `FML-ADR-026` / `TBR-NET-02` | grounds the LoRa recipient path on the wire |
| 4 | `TBR-COMP-01` | the memory-class/BOM call gets its hardware half |

None of these close a hardware-gated trade on their own; each records the
evidence a closure will cite, and each ends in a demonstration rather than a
document.
