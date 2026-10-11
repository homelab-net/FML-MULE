#!/usr/bin/env python3
"""A synthetic TAK EUD on the Meshtastic bearer.

Sends and receives FML-ADR-070's encoding over a real LoRa radio: the sender in
``Contact.callsign`` and the recipient in ``GeoChat.to``, carried in a
``TAKPacket`` on the ATAK plugin port (72). Those are upstream's own TAK fields,
which is why FML-ADR-070 chose them -- a custom tag on a private port is
discarded by the FML-ADR-048 gateway.

Usage:
  lora-geochat-eud.py listen  [--dev DEV] [--seconds N]
  lora-geochat-eud.py send    --to CALLSIGN --message TEXT
                              [--from CALLSIGN] [--dev DEV]
                              [--channel NAME | --ch-index N] [--no-ack]

WHAT THIS IS FOR. ``test/bench/geochat-survival.sh`` asserts that these two
fields survive the Meshtastic bearer, but over a docker bridge: UDP multicast on
a perfect wire, tier SIMULATED, "no LoRa RF, no modulation, no airtime, no
range". This is the same assertion with a radio actually in the path. The EUD is
synthetic -- it is this script, not ATAK -- so it exercises the ENCODING and the
bearer, not a TAK application and not enrollment.

WHAT IT CANNOT DO ALONE. Delivery needs two radios: one to transmit and one to
receive. With a single node, ``send`` proves only that the packet was handed to
the radio and transmitted; nothing observes it arriving. ``listen`` on a second
node is the other half.

CHANNEL SAFETY, AND WHY IT IS NOT A SUGGESTION. Channel index 0 is the public
LongFast channel for the region, and on this bench it carries roughly eighty
third-party nodes -- named solar routers and private handhelds belonging to
other people. Synthetic test traffic does not belong on their hardware, and a
LoRa transmission cannot be recalled. So this script defaults to the private
MULE-TEST channel, resolves channels by NAME rather than by a numeric index that
can silently shift when a channel is added, and refuses index 0 outright unless
--i-really-mean-the-public-mesh is passed. The public mesh is a legitimate
contingency BEARER for the program; that is a different thing from being a
legitimate place to put test chatter.
"""

from __future__ import annotations

import argparse
import sys
import time

DEFAULT_DEV = "/dev/ttyACM0"
DEFAULT_CHANNEL = "MULE-TEST"
#: The ATAK plugin port. FML-ADR-070 rides upstream's fields on upstream's port.
ATAK_PLUGIN = 72


def fail(msg: str) -> "None":
    print("FAIL: " + msg, file=sys.stderr)
    raise SystemExit(1)


def resolve_channel(iface, name: str | None, index: int | None, allow_public: bool) -> int:
    """Return a channel index, by name where possible, and never 0 by accident."""
    chans = getattr(iface.localNode, "channels", None) or []
    if index is None:
        if not name:
            fail("give --channel NAME or --ch-index N")
        for i, ch in enumerate(chans):
            if getattr(getattr(ch, "settings", None), "name", "") == name:
                index = i
                break
        if index is None:
            # Label the nameless ones honestly: index 0 is the primary, and a
            # later slot with no name is an unused slot, not another primary.
            have = []
            for i, c in enumerate(chans):
                nm = getattr(getattr(c, "settings", None), "name", "")
                have.append(nm if nm else ("<primary>" if i == 0 else "<unused:%d>" % i))
            fail("no channel named %r on this radio; it has: %s" % (name, ", ".join(have)))
    if index == 0 and not allow_public:
        fail(
            "channel index 0 is the PUBLIC LongFast channel and carries third-party "
            "nodes. Use the private %s channel, or pass "
            "--i-really-mean-the-public-mesh if putting test traffic on other "
            "people's radios is genuinely intended." % DEFAULT_CHANNEL
        )
    return index


def do_listen(args) -> int:
    """Receive and decode. Transmits nothing, so it is safe on any channel."""
    from meshtastic.protobuf import atak_pb2
    from meshtastic.serial_interface import SerialInterface
    from pubsub import pub

    seen = {"packets": 0, "tak": 0}

    def on_receive(packet, interface):  # noqa: ARG001
        seen["packets"] += 1
        dec = packet.get("decoded") or {}
        port = dec.get("portnum")
        frm = packet.get("fromId") or packet.get("from")
        if port == "ATAK_PLUGIN" or port == ATAK_PLUGIN:
            seen["tak"] += 1
            tak = atak_pb2.TAKPacket()
            try:
                tak.ParseFromString(dec.get("payload", b""))
            except Exception as exc:  # noqa: BLE001
                print("  [%s] ATAK_PLUGIN payload did not parse: %s" % (frm, exc))
                return
            # The two fields FML-ADR-070 rests on, printed verbatim so a
            # byte-for-byte comparison against what was sent is possible.
            print("  [%s] TAKPacket  Contact.callsign=%r  GeoChat.to=%r  message=%r"
                  % (frm, tak.contact.callsign, tak.chat.to, tak.chat.message))
        else:
            text = dec.get("text")
            print("  [%s] %s%s" % (frm, port, (" text=%r" % text) if text else ""))

    pub.subscribe(on_receive, "meshtastic.receive")
    iface = SerialInterface(args.dev)
    print("listening on %s for %ss (transmitting nothing)" % (args.dev, args.seconds))
    try:
        time.sleep(args.seconds)
    finally:
        iface.close()
    print("heard %d packet(s), of which %d were ATAK_PLUGIN TAKPackets"
          % (seen["packets"], seen["tak"]))
    return 0


def do_send(args) -> int:
    from meshtastic.protobuf import atak_pb2
    from meshtastic.serial_interface import SerialInterface

    iface = SerialInterface(args.dev)
    try:
        idx = resolve_channel(iface, args.channel, args.ch_index, args.i_really_mean_the_public_mesh)

        tak = atak_pb2.TAKPacket()
        tak.is_compressed = False
        tak.contact.callsign = args.from_callsign       # sender  (FML-ADR-070)
        tak.contact.device_callsign = args.from_callsign
        tak.chat.to = args.to                           # recipient (FML-ADR-070)
        tak.chat.message = args.message
        payload = tak.SerializeToString()

        print("sending on channel index %d, ATAK plugin port %d, %d bytes"
              % (idx, ATAK_PLUGIN, len(payload)))
        print("  Contact.callsign=%r  GeoChat.to=%r  message=%r"
              % (args.from_callsign, args.to, args.message))
        iface.sendData(
            payload,
            portNum=ATAK_PLUGIN,
            channelIndex=idx,
            wantAck=not args.no_ack,
        )
        # The transmit is queued on another thread; leave the radio time to
        # actually put it on the air before the process exits.
        time.sleep(args.settle)
        print("handed to the radio. NOTE: with one radio this proves transmission,")
        print("not delivery -- a second node running `listen` is the other half.")
    finally:
        iface.close()
    return 0


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="mode", required=True)

    pl = sub.add_parser("listen", help="receive and decode; transmits nothing")
    pl.add_argument("--dev", default=DEFAULT_DEV)
    pl.add_argument("--seconds", type=float, default=60.0)

    ps = sub.add_parser("send", help="send one synthetic GeoChat")
    ps.add_argument("--dev", default=DEFAULT_DEV)
    ps.add_argument("--to", required=True, help="recipient callsign -> GeoChat.to")
    ps.add_argument("--message", required=True)
    ps.add_argument("--from", dest="from_callsign", default="FMLEUD1",
                    help="sender callsign -> Contact.callsign")
    ps.add_argument("--channel", default=DEFAULT_CHANNEL, help="channel by NAME")
    ps.add_argument("--ch-index", type=int, default=None, help="channel by index")
    ps.add_argument("--no-ack", action="store_true")
    ps.add_argument("--settle", type=float, default=12.0)
    ps.add_argument("--i-really-mean-the-public-mesh", action="store_true",
                    help="permit channel index 0, the public mesh")

    args = p.parse_args(argv)
    if args.mode == "listen":
        return do_listen(args)
    return do_send(args)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
