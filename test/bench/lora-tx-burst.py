"""Transmit a schedule of LoRa bursts so an RF witness can be correlated to them.

The transmitting half of the pair completed by test/bench/sdr-rf-witness.sh.
Both take the same start epoch and align on NTP time, so neither end has to
signal the other and no shared control channel is needed.

Usage, on the node holding the radio::

    test/bench/lora-tx-burst.py --start-epoch 1792187369 --channel-index 3

WHY A SCHEDULE RATHER THAN ONE SEND. Energy in a channel does not say which
radio produced it, and a shared ISM band has other occupants. A single spike
beside a single send is a coincidence with a plausible story. Seven sends on a
fixed cadence, each falling in its own capture interval with quiet intervals
between, is a pattern that ambient traffic does not reproduce -- and the quiet
gaps are an interleaved control taken under identical conditions, which a
separate baseline run is not.

IT REFUSES CHANNEL 0. The primary channel is the public mesh. On this bench it
carries roughly eighty real third-party nodes, and a LoRa transmission cannot
be recalled. Synthetic bench traffic belongs on a private secondary channel,
so the index is required rather than defaulted and zero is rejected outright.
This is written as a check rather than a note because a note is a suggestion.

IT TAKES AN INDEX, AND THEN READS THE NAME BACK. lora-geochat-eud.py resolves
channels by NAME, for the good reason that an index silently shifts when a
channel is added. This script takes the index anyway, because an RF witness
record has to state the exact configuration that was transmitted on and an
index is what the device reports. The risk that decision reintroduces is
closed the other way: the channel's name at that index is read off the device
BEFORE anything is sent, recorded in the transmit log, and an index whose
channel is unconfigured or disabled is refused. A shifted index therefore
shows up as the wrong name in the evidence rather than as silent traffic on
somebody else's channel.

hopLimit IS ZERO. Meshtastic's default rebroadcast mode relays a packet on an
unknown channel, so a private channel does not stop a third-party router
repeating a bench packet seven hops across somebody else's mesh -- the PSK
withholds the contents, not the airtime. Zero means the packet is transmitted
once and never relayed. It also keeps the measurement honest: one send is one
transmission, so a second spike is a second event needing its own explanation
rather than an echo of the first.

WHAT THIS PROVES ON ITS OWN. That the host handed a packet to the radio and
the radio accepted it. Nothing more. The transmit log it writes is only useful
beside a capture taken by an instrument that is not this device.
"""

import argparse
import json
import time
from datetime import UTC, datetime
from pathlib import Path

import meshtastic.serial_interface

SETTLE_S = 3
DISABLED = 0


def channel_name(iface: object, index: int) -> str:
    """Return the configured name of a channel index, or raise if unusable.

    Reads the device's own channel table rather than trusting the index to
    mean what it meant the last time somebody looked.
    """
    channels = iface.localNode.channels
    if index >= len(channels):
        msg = (
            f"the device reports only {len(channels)} channels; {index} is past the end"
        )
        raise SystemExit(msg)
    channel = channels[index]
    if channel.role == DISABLED:
        msg = f"channel index {index} is disabled on this device, so nothing would send"
        raise SystemExit(msg)
    return str(channel.settings.name)


def parse_args() -> argparse.Namespace:
    """Return the parsed command line."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--start-epoch",
        type=int,
        required=True,
        help="UNIX epoch second of the first send; pass the same value to"
        " test/bench/sdr-rf-witness.sh",
    )
    parser.add_argument(
        "--channel-index",
        type=int,
        required=True,
        help="secondary channel index to send on; 0 is the public mesh and is refused",
    )
    parser.add_argument("--port", default="/dev/ttyACM0", help="serial device")
    parser.add_argument("--count", type=int, default=7, help="number of sends")
    parser.add_argument("--spacing", type=int, default=15, help="seconds between sends")
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="transmit log path; defaults to ./lora-tx-burst-<start-epoch>.json",
    )
    return parser.parse_args()


def main() -> int:
    """Send the scheduled bursts and write the transmit log."""
    args = parse_args()

    if args.channel_index <= 0:
        msg = (
            "channel-index must be a private secondary channel. Index 0 is the"
            " public mesh, which on this bench carries real third-party nodes,"
            " and a LoRa transmission cannot be recalled."
        )
        raise SystemExit(msg)

    lead = args.start_epoch - time.time()
    if lead < SETTLE_S:
        msg = (
            f"start-epoch is {lead:.0f}s away; the radio needs longer than that"
            " to open. Choose a later start."
        )
        raise SystemExit(msg)

    iface = meshtastic.serial_interface.SerialInterface(args.port)
    log = []
    try:
        name = channel_name(iface, args.channel_index)
        print(
            json.dumps({"channel_index": args.channel_index, "channel_name": name}),
            flush=True,
        )
        for seq in range(args.count):
            target = args.start_epoch + seq * args.spacing
            while time.time() < target:
                time.sleep(0.005)
            sent_at = time.time()
            iface.sendText(
                f"RFWITNESS-{seq}",
                channelIndex=args.channel_index,
                hopLimit=0,
                wantAck=False,
            )
            record = {
                "seq": seq,
                "target_epoch": target,
                "sent_epoch": round(sent_at, 3),
                "sent_utc": datetime.fromtimestamp(sent_at, UTC).isoformat(),
                "skew_ms": round((sent_at - target) * 1000, 1),
            }
            log.append(record)
            print(json.dumps(record), flush=True)
        time.sleep(SETTLE_S)
    finally:
        iface.close()

    out = args.out or Path(f"lora-tx-burst-{args.start_epoch}.json")
    record = {
        "channel_index": args.channel_index,
        "channel_name": name,
        "hop_limit": 0,
        "sends": log,
    }
    out.write_text(json.dumps(record, indent=2) + "\n")
    print(f"wrote {out} ({len(log)} sends on {name!r})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
