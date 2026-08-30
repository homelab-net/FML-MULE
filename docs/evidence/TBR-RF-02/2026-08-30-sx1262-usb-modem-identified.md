# What the USB LoRa dongle actually is, and what it can be used for

**Trade:** `TBR-RF-02`.
**Date:** 2026-08-30.
**Taken by:** Cameron Zobrist, on the lab development machine.
**Status of this artifact:** `UNVERIFIED` as a statement about a MULE. It
identifies one piece of real hardware and reads its configuration. **Nothing
transmitted.**

## What it is

A **Waveshare USB-TO-LoRa-HF-B**, SX1262, antenna rated 850-930 MHz.

| Item | Value |
| --- | --- |
| USB bridge | `1a86:55d3` QinHeng CH343, CDC-ACM, serial `5B5E130712` |
| Presents as | `/dev/ttyACM0` |
| Radio | Semtech SX1262 |
| Host interface | UART, AT command set, 115200 8N1 |

## Why it appeared dead, and was not

First contact found it completely silent: zero unsolicited bytes at five baud
rates, no response to the Meshtastic protocol, and nothing to an ESP32
bootloader handshake under three reset strategies.

**That was correct behaviour and the wrong question.** The board is a
transparent UART-to-LoRa bridge. In its default mode it emits only what it
hears over the air, and it transmits whatever is written to it. With no peer
on frequency there is nothing to emit, and the probe traffic was not being
parsed as commands: it was most likely being sent as LoRa payloads.

It answers after an escape into configuration mode:

```text
>>> +++\r\n        (at 115200)
<<< +++\r\n
>>> AT\r\n
<<< OK
```

The lesson generalises past this device. **A silent serial port is not a dead
one**, and a probe that assumes a protocol will read a working device as
broken. The command set was found with `AT+HELP`, which the board answers in
full.

## Configuration as found

Read-only. Nothing was set, and the radio was not keyed.

| Command | Value |
| --- | --- |
| `AT+MODE?` | `1` |
| `AT+TXCH?` | `18` |
| `AT+RXCH?` | `18` |
| `AT+SF?` | `7` |
| `AT+BW?` | `0` |
| `AT+CR?` | `1` |
| `AT+PWR?` | `10` |
| `AT+NETID?` | `0` |
| `AT+ADDR?` | `0` |
| `AT+LBT?` | `0` |
| `AT+BAUD?` | `115200` |

The units behind these are the vendor's index values, not physical quantities.
Channel 18 is not a frequency and `PWR=10` is not necessarily 10 dBm; mapping
them needs the vendor documentation and **is not done here**, because a
plausible-looking frequency is worse than a blank.

**`LBT=0`.** Listen-before-talk is off as shipped. `REGULATORY.md` and the
region profile mechanism are where that belongs as a decision, and it is
recorded here because a device that ships with it off will transmit without
one if nobody changes it.

## It is a point-to-point modem, not a mesh

The complete command set, from `AT+HELP`, is: `SF`, `BW`, `CR`, `PWR`,
`NETID`, `LBT`, `MODE`, `TXCH`, `RXCH`, `RSSI`, `ADDR`, `PORT`, `COMM`,
`BAUD`, `RESTORE`, `KEY`.

**There is no routing primitive in it.** Nothing about neighbours, hops,
forwarding, or store-and-forward. Asked for their value space, `AT+ADDR=?`
answers `UINT16` and `AT+NETID=?` answers `UINT8`, which is an addressed
point-to-point or star scheme: a sender names one destination on one network
id, and that is the whole of it.

That matters more than any other line in this artifact. `FML-ADR-026` makes
LoRa the plane that still works when the IP plane does not, and CONOPS section
5.5 puts it at the bottom of the degradation ladder for a team that is spread
out. **A link that reaches only what it can hear directly is not that.** The
value of the LoRa plane is the mesh, and this device does not have one.

## What it cannot do: it is not a Meshtastic node and cannot be flashed into one

Three reasons, and the first two are structural:

1. **Meshtastic firmware targets an MCU, not a radio.** Its supported builds
   are for ESP32/ESP32-S3, nRF52840, RP2040 and STM32 boards. The MCU behind
   this bridge runs the vendor's fixed-function firmware and no Meshtastic port
   exists for it.
2. **Meshtastic drives an SX126x over SPI.** This board exposes a UART AT and
   transparent interface. Whether the SX1262's SPI lines are physically
   reachable on the board is not determinable from software and was not
   established.
3. `meshtasticd`, the Linux daemon `FML-ADR-026` would have a node run, expects
   SPI access to the radio. A UART modem is not that.

So the silicon is right and the packaging is wrong. **SX1262 is the radio
Meshtastic uses**; this board wraps it in a modem rather than exposing it to a
programmable host.

A Meshtastic node needs a supported board: an ESP32-S3 or nRF52840 carrying an
SX1262, which is a different purchase, not a reflash of this one.

## What it is good for

**As a bench instrument for this trade.** `TBR-RF-02` needs LoRa receive
sensitivity measured with the HaLow radio idle and transmitting, at antenna
separations achievable inside an enclosure. That needs a LoRa transmitter and
receiver whose spreading factor, bandwidth, coding rate and power can be set
and stated. This device exposes all four over AT, which makes it usable for
producing a measurement, with a second unit as the other end.

**Not as part of the node.** `FML-ADR-026` selects Meshtastic and
`docs/NON-GOALS.md` refuses custom LoRa protocol development. Using this modem
as the MULE's LoRa plane would mean building a protocol on raw LoRa, which is
the thing that file says the program will not do. It is test equipment, not a
component.

## What this does not say

No frequency, no power in dBm, no sensitivity, no range, no coexistence
result. Nothing was transmitted and no measurement was taken. This artifact
identifies a device and records how to talk to it, so that whoever takes the
`TBR-RF-02` measurements does not spend a session discovering that a working
radio looks like a dead one.
