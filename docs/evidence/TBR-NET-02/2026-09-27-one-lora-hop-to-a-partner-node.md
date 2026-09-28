# One real LoRa hop to a partner node

**Tier: deferred (real-hardware bench result; formal `HARDWARE-VERIFIED` held).**
This is a real-hardware result -- a Meshtastic text message crossed one real
sub-GHz LoRa RF hop between two physical nodes, both ways, with a returned
delivery ACK -- which by `docs/evidence/README.md`'s vocabulary would be
`HARDWARE-VERIFIED` for that one sentence. The program is **not** stamping it
`HARDWARE-VERIFIED` yet: it would be the repository's **first** such result, and
that flip is a program-wide posture change that must reconcile every "nothing is
hardware-verified" surface at once -- `STATUS.md`, `README.md`, `test/README.md`,
`AGENTS.md`, and the prebuilt public `site/` (rebuilt outside this repo). It is
recorded here as a **complete real-hardware bench result pending that deliberate
flip**; until then nothing in the repository claims `HARDWARE-VERIFIED`. It is
**not** `SIMULATED` -- that word says nothing about physical behaviour and this
was real RF.

**What was measured:** that a Meshtastic text message is delivered across one real
LoRa RF hop between two physical nodes in each direction, each confirmed by a
returned delivery ACK, with the received signal quality recorded. Repeatable by
`docs/bench-hardware-bringup.md` Step 3 (Meshtastic/LoRa).

**Date/time:** 2026-09-27, ~18:20-18:45 local (US Mountain). **Taken by:** Cameron
Zobrist. **Article:** flat-sat / bench hardware (two physical nodes on real RF),
not selected production hardware. It complements the `SIMULATED`
`2026-09-06-geochat-to-survives-the-meshtastic-bearer.md` (two `meshtasticd` sim
nodes over a UDP bridge -- a perfect wire, encoding *carriable*); this shows a
message actually *crosses real LoRa RF*.

## Provenance

- **Instrument / MULE bench node:** RAKwireless WisCore **RAK4631** (nRF52840 +
  SX1262), USB board serial **`A90224B334EBDD73`** (the non-sensitive instrument
  identifier; the Meshtastic node id is scrubbed, see below). Attached to the dev
  host over USB serial by its stable `/dev/serial/by-id/usb-RAKwireless_WisCore_RAK4631_Board_A90224B334EBDD73-if00`
  path (never `ttyACM0`). No RF calibration -- signal figures are the node's own
  reported RSSI/SNR, not calibrated measurements.
- **Node "image build":** Meshtastic firmware **2.7.15.567b8ea** (VANILLA), role
  CLIENT, PKI-capable (`hasPKC: true`).
- **Radio configuration:** region **US** (902-928 MHz, **Part 15.247 ISM** -- not
  amateur, so Part 97's obscuring rule and the EU duty cycle do not apply); modem
  preset **LONG_FAST**; `channelNum` 0, primary channel matched to the partner's
  **private** channel (its URL/PSK is key material, used only at the bench and
  scrubbed); configured tx power 30 dBm (a register setting, not a measured EIRP);
  **stock antenna**, vertical.
- **Partner node:** a second physical Meshtastic node in range, firmware 2.7.26,
  same region/preset/channel, **~1 room away (one interior wall), roughly
  co-planar/vertical antennas**.
- **Ambient:** indoor, room temperature, static (both nodes stationary on a
  bench/handheld); no deliberate obstruction beyond the one interior wall.
- **Host / client:** kernel `6.12.105+deb13-amd64`; `meshtastic` CLI 2.7.11 and
  `pyserial` 3.5 in `.venv-lora`.
- **Link geometry observed:** direct, **1 hop**; **SNR 6-7 dB**, **RSSI approx
  -52 to -60 dBm** at the RAK for the partner's transmissions.

## What this verifies

Both directions crossed one real LoRa hop, PKI-encrypted, with delivery
confirmation:

- **MULE -> partner:** a broadcast marker (`fml-bench-probe`) was received by the
  partner (operator-confirmed on the partner device); and a **direct message**
  (`fml-bench-dm-bravo`) returned **"Received an ACK"** -- delivered to the
  destination node's radio stack and acknowledged. The operator confirmed the
  message displayed on the partner device.
- **partner -> MULE:** the RAK received a direct text from the partner
  (`TEXT_MESSAGE_APP`) at RSSI approx -60 dBm / SNR 6-7 dB, plus the partner's
  `NODEINFO_APP` packet. On the partner device the return messages show
  "Delivered to recipient" (ACK from the RAK).

The claim is about **message carriage on the real bearer**, demonstrated on real
Meshtastic LoRa nodes -- which by `docs/evidence/README.md` (a claim demonstrated
on the hardware it is about can be hardware evidence, regardless of article) would
be hardware evidence for that sentence. The formal tier is held per the deferral
above.

## Run (raw output, scrubbed)

Partner node id shown as `!<partner>`; third-party public-mesh nodes heard on air
are omitted (see scrub note). From `.venv-lora/bin/meshtastic` and an ad-hoc
receive listener on the RAK:

```text
# MULE -> partner broadcast (seeds discovery; operator confirmed receipt on partner)
Sending text message fml-bench-probe to ^all on channelIndex:0

# partner -> MULE, captured on the RAK's receive callback:
RX from=!<partner> port=TEXT_MESSAGE_APP rssi=-60 snr=6.0 hopStart=7 'Direct message from <partner>'
RX from=!<partner> port=NODEINFO_APP    rssi=-52 snr=6.0 hopStart=7
RX from=!<partner> port=ROUTING_APP     rssi=-61 snr=6.0            # delivery ACK

# MULE -> partner direct message, first attempt (no partner pubkey yet):
Sending text message fml-bench-dm-bravo to !<partner> on channelIndex:0
Waiting for an acknowledgment from remote node (this could take a while)
Received a NAK, error reason: NO_CHANNEL

# after the partner's NODEINFO_APP populated its public key on the RAK:
Sending text message fml-bench-dm-bravo to !<partner> on channelIndex:0
Waiting for an acknowledgment from remote node (this could take a while)
Received an ACK.
```

The partner device (screenshot, not committed) showed `fml-bench-dm-bravo`
received and the partner's own messages marked "Delivered to recipient."

**Caveat (bench contention, not an RF fault).** During the same session, some
*later* return direct messages from the partner showed "relayed, not confirmed by
recipient" (no delivery ACK) rather than "delivered." Cause: opening the RAK's USB
serial port resets the nRF52840 (DTR toggle), so each `meshtastic` CLI invocation
rebooted the node; messages sent while the RAK was mid-reboot were transmitted into
the mesh but not received-and-acknowledged. This result rests **only on the
confirmed exchange above** (a returned ACK each way plus a captured inbound
packet), not on those unconfirmed later sends. It is recorded here so the partial
results are not read as a contradiction.

## Finding: a PKI direct message needs a NodeInfo key exchange first

The first `MULE -> partner` direct message **NAK'd `NO_CHANNEL`**. Cause: the RAK
had heard only a data packet from the partner, so it held **no public key** for
it (`Pubkey: N/A`); a PKI direct message cannot then be decrypted by the
recipient. A **broadcast on the shared channel worked immediately** (channel-PSK
encryption, no per-node key needed). Once the partner's `NODEINFO_APP` arrived and
its public key populated the RAK's node DB, the identical direct message returned
an ACK.

**Consequence for the config/bring-up path (`FML-ADR-026`, the operator
procedure):** a node must complete a NodeInfo exchange with a recipient before a
PKI direct message to it is expected to succeed; broadcast and channel-addressed
traffic do not need it. This is a real behaviour the sim wire could not surface.

## What this does not establish

`SIMULATED` or open, unchanged by this result:

- **Range** -- one interior wall only; says nothing about field distances.
- **Duty cycle, airtime, throughput, and HaLow coexistence** -- `TBR-RF-02`.
- **Multi-hop** routing -- this was a single direct hop.
- **The 231-byte recipient-payload budget** in `mule/recipients.py` /
  `FML-ADR-070` composition limit -- untested here; still `SIMULATED`.
- **`GeoChat.to` / `Contact.callsign` contents from a real ATAK client** -- the
  upstream-encoding grounding (`FML-ADR-070`, `mule/recipients.py`) needs the
  OTS-native ATAK -> OpenTAKServer -> Meshtastic path; deferred (the `FML-ADR-048`
  gateway is unbuilt). This run used synthetic text markers, not a real GeoChat.
- **Production hardware** -- the RAK4631 is a representative Meshtastic node, not a
  selected compute/radio (no selection is final; `TBR-RF-02`, `TBR-HW-01`).

`TBR-NET-02` is already **CLOSED** on `FML-ADR-070`; this is confirming bearer
evidence on real RF, and does not reopen it.

## What was scrubbed (SECURITY.md)

Per `SECURITY.md` and `docs/evidence/README.md`, member/deployment identifiers and
locations are not committed. Redacted from this record: both nodes' Meshtastic
node IDs, short/long names and MAC addresses; the partner's channel URL/PSK (key
material, used only at the bench); the partner device screenshot; and every
third-party public-mesh node and its position that the RAK incidentally heard on
air. Retained because they are non-identifying program-equipment/measurement
provenance: the RAK's own USB board serial (the instrument identifier
`docs/evidence/README.md` requires), RSSI/SNR, hop count, firmware/region/preset,
and the synthetic payload markers.
