#!/usr/bin/env python3
"""A bench IP <-> LoRa TAK gateway that is just another client of tak.field.

    TAK EUDs (any bearer) -> tak.field ingress -> authoritative TAK server
        <- this gateway (TLS client) -> Meshtastic radio (serial) -> LoRa EUDs

WHAT THIS IS. A bench instrument for FML-ADR-048's third option -- PyTAK plus the
Meshtastic Python API, glue only -- chosen by the Program Owner on 2026-10-18
because option 1 (OpenTAKServer's Meshtastic path) is unavailable whenever a TAK
Server backend holds authority, and option 2 (TAK Meshtastic Gateway) bridges a
single TAK client over multicast rather than a server. The reasons, and what
FML-ADR-048 asks of an option-3 component before it may leave the bench, are in
the evidence note that cites this file. It is not a `services/` component.

Being a client of tak.field, it follows whichever backend the ingress makes
authoritative and reconnects across a swap. Transport is PyTAK
(`pytak.protocol_factory`, FML-ADR-033); this file adds the reconnect loop PyTAK's
workers lack, and the translation.

WHAT IT CARRIES. GeoChat and PLI only (Meshtastic bandwidth), in FML-ADR-070's
encoding: upstream's TAKPacket on the ATAK plugin port, sender in
`Contact.callsign`, recipient in `GeoChat.to`. With ``--lora-format text`` it
instead speaks plain Meshtastic text, so the stock Meshtastic app can be an EUD.

THE RULES IT HOLDS, and where they come from:

- Only the configured **rooms** are relayed (``--room``, repeatable). The
  default is "All Chat Rooms", the Program Owner's field policy (2026-10-18). A
  gateway attached to a server with users outside the test (for example a live
  pilot server) must instead name a bench-only room, so that server's shared
  room is never put on the air.
- A **direct message** is resolved with `mule.recipients.decide_delivery`. An
  unresolved recipient is **refused**, never widened to a room (CONOPS 23, the
  addressing specification's fail-closed rule).
- A message that does not fit the 231-byte usable payload is **refused**
  (`mule.recipients.fits_payload`, FML-ADR-070), not truncated.
- **One identity across bearers.** The sender's real uid rides in
  ``Contact.device_callsign``, the field OpenTAKServer's own encoder fills
  (``TBR-NET-02/2026-09-28``), and the far gateway reuses it, so an EUD keeps the
  same uid whether a client reaches it over IP or LoRa. A uid that already
  belongs to a client on this gateway's own server is refused as a claim and
  replaced by a minted one (``FMLR-<node>-<callsign>``), as is a sender that
  carried none.
- **Loop prevention** is by sender: anything whose sender uid is this gateway's
  own, or a remote EUD's uid it relays for, is an echo and is dropped; a
  chat reaching several of its sessions is acted on once (by messageId). This
  does NOT dedupe across two gateways attached to one server: with the IP mesh
  up, two gateways would each relay the same traffic. Relaying only while a node
  is partitioned from the authority is the intended fix (plan S3), not built yet.
- LoRa packets are accepted only on the named private channel, or as a direct
  message addressed to this node.
- While the server connection is down, LoRa->TAK items are held (bounded count
  and age) and sent on reconnect; on every (re)connect the gateway announces its
  own SA first, because OpenTAKServer delivers nothing to a connection that has
  not sent one.

The log is one JSON line per decision and carries no coordinates.

Usage:
  fml-lora-gw.py --host tak.field --cert C --key K --ca CA [--room R ...]
                 [--lora-format tak|text] [--no-hostname-check]
"""

from __future__ import annotations

import argparse
import asyncio
import configparser
import glob
import hashlib
import json
import re
import sys
import time
import uuid
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from mule.recipients import (
    LoraPayloadBudget,
    decide_delivery,
    fits_payload,
)

ALL_CHAT = "All Chat Rooms"
CHANNEL = "MULE-TEST"
#: Not "MESH-": iTAK appears to treat MESH-* contacts as reachable only through
#: its own Meshtastic radio and silently drops replies to them (bench, 2026-10-18).
MESH_PREFIX = "FMLR-"
#: FML-ADR-070: the usable Meshtastic payload is 231 bytes.
USABLE_BYTES = 231
#: Measured 2026-10-18 on the bench's meshtastic 2.7.11 protobufs: a chat
#: TAKPacket costs 10 bytes beyond its three strings, 11 or 12 once a length
#: passes 127. 12 is the upper bound for any body inside the 231-byte budget.
TAK_FRAMING_BYTES = 12
#: Carrying the sender's uid in Contact.device_callsign costs its length plus a
#: 2-byte tag and length prefix (a uid is under 128 bytes).
UID_FRAMING_BYTES = 2
#: What a carried uid may look like: ATAK/iTAK UUIDs, ANDROID-* ids, Windows SIDs.
UID_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:@-]{0,63}")
#: Plain Meshtastic text is sent as "CALLSIGN: body".
TEXT_FRAMING_BYTES = 2
QUEUE_MAX = 50
QUEUE_AGE_S = 120.0
#: One server session per EUD behind a remote MULE (see Gateway.proxy). Up to
#: eight EUDs sit behind a MULE; the totals bound what one gateway will hold open.
PROXY_PER_NODE = 8
PROXY_TOTAL = 32
PROXY_IDLE_S = 900.0
PROXY_SA_REFRESH_S = 60.0
SEEN_MESSAGE_TTL_S = 600.0


def log(ev: str, **kw: Any) -> None:  # noqa: ANN401 (free-form JSON fields)
    """Print one JSON log line."""
    print(json.dumps({"ev": ev, "t": round(time.time(), 3), **kw}), flush=True)


def cot_time(offset: float = 0) -> str:
    """Return a CoT timestamp offset seconds from now."""
    t = datetime.now(UTC) + timedelta(seconds=offset)
    return t.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


# ---------------------------------------------------------------- CoT builders


def _event(
    typ: str, uid: str, point: tuple[float, float, float], stale: float, how: str
) -> tuple[ET.Element, ET.Element]:
    ev = ET.Element(
        "event",
        {
            "version": "2.0",
            "type": typ,
            "uid": uid,
            "how": how,
            "time": cot_time(),
            "start": cot_time(),
            "stale": cot_time(stale),
        },
    )
    lat, lon, hae = point
    ET.SubElement(
        ev,
        "point",
        {
            "lat": f"{lat:.7f}",
            "lon": f"{lon:.7f}",
            "hae": f"{hae:.1f}",
            "ce": "9999999",
            "le": "9999999",
        },
    )
    return ev, ET.SubElement(ev, "detail")


def build_geochat(
    sender: str, sender_uid: str, room: str, chat_id: str, text: str
) -> bytes:
    """Build a GeoChat event in the shape ATAK puts on the wire.

    For a room, ``room`` and ``chat_id`` are both the room name. For a direct
    message, ``room`` is the recipient's callsign and ``chat_id`` its uid.
    """
    mid = str(uuid.uuid4())
    ev, det = _event(
        "b-t-f",
        f"GeoChat.{sender_uid}.{chat_id}.{mid}",
        (0.0, 0.0, 9999999.0),
        86400,
        "h-g-i-g-o",
    )
    chat = ET.SubElement(
        det,
        "__chat",
        {
            "parent": "RootContactGroup",
            "groupOwner": "false",
            "messageId": mid,
            "chatroom": room,
            "id": chat_id,
            "senderCallsign": sender,
        },
    )
    ET.SubElement(chat, "chatgrp", {"uid0": sender_uid, "uid1": chat_id, "id": chat_id})
    ET.SubElement(
        det, "link", {"uid": sender_uid, "type": "a-f-G-U-C", "relation": "p-p"}
    )
    rem = ET.SubElement(
        det,
        "remarks",
        {"source": f"BAO.F.ATAK.{sender_uid}", "to": chat_id, "time": cot_time()},
    )
    rem.text = text
    if room != chat_id:  # a direct message: let the server route it
        ET.SubElement(ET.SubElement(det, "marti"), "dest", {"callsign": room})
    return ET.tostring(ev)


def build_pli(
    callsign: str, uid: str, point: tuple[float, float, float], remarks: str = ""
) -> bytes:
    """Build a position (SA) event."""
    ev, det = _event("a-f-G-U-C", uid, point, 180, "m-g")
    # endpoint and takv are what make a TAK server register the sender as a
    # connected, routable contact (direct messages are routed to it by callsign);
    # without them OpenTAKServer and TAK Server 5.8 both relay its SA but list
    # no client endpoint for it.
    ET.SubElement(det, "contact", {"callsign": callsign, "endpoint": "*:-1:stcp"})
    ET.SubElement(
        det,
        "takv",
        {
            "device": "FML bench",
            "platform": "FML-LORA-GW",
            "os": "linux",
            "version": "0",
        },
    )
    ET.SubElement(det, "__group", {"name": "Cyan", "role": "Team Member"})
    if remarks:
        ET.SubElement(det, "remarks").text = remarks
    return ET.tostring(ev)


# ---------------------------------------------------------------- translation


@dataclass(frozen=True)
class LoraIn:
    """One accepted LoRa message, already decoded from its protobuf."""

    kind: str  # "chat" | "pli" | "text"
    node: str  # sender node id, e.g. "!22509c08"
    callsign: str
    to: str = ""  # GeoChat.to; "" for plain text
    text: str = ""
    point: tuple[float, float, float] | None = None
    uid: str = ""  # Contact.device_callsign: the sender's own uid, if carried


@dataclass(frozen=True)
class TakOut:
    """CoT to send to the TAK server.

    `via` names the remote EUD (its MESH uid) whose own server session should
    carry it; "" means the gateway's own session.
    """

    xml: bytes
    via: str = ""
    callsign: str = ""
    point: tuple[float, float, float] | None = None


@dataclass(frozen=True)
class LoraOut:
    """Something to put on the air."""

    kind: str  # "chat" | "pli" | "text"
    dest: str  # "^all" or a node id
    callsign: str
    to: str = ""
    text: str = ""
    point: tuple[float, float, float] | None = None
    uid: str = ""  # the IP-side sender's uid, carried in Contact.device_callsign


@dataclass(frozen=True)
class Refused:
    """A message the gateway declined to forward, and why."""

    reason: str


Action = TakOut | LoraOut | Refused


@dataclass
class Translator:
    """The gateway's decisions, as a pure state machine (no radio, no socket).

    The roster is keyed by recipient key (a uid by ATAK convention). Mapping a
    human callsign to that key is a separate client binding
    (`mule/recipients.py`); here it is learned from the SA the server relays,
    which is bench contact-seeding, not the Mission Trust Service roster
    FML-ADR-087 calls for.
    """

    own_uid: str
    rooms: frozenset[str]
    lora_format: str = "tak"
    pli_interval_s: float = 60.0
    roster: dict[str, str] = field(default_factory=dict)  # uid -> uid (IP side)
    callsign_key: dict[str, str] = field(default_factory=dict)  # callsign -> uid
    # MESH uid -> (node, callsign): one entry per EUD behind a remote MULE
    mesh_eud: dict[str, tuple[str, str]] = field(default_factory=dict)
    last_pli: dict[str, float] = field(default_factory=dict)
    seen_chat: dict[str, float] = field(default_factory=dict)  # messageId -> t

    def mesh_uid(self, node: str, callsign: str) -> str:
        """Return the uid this gateway mints for one EUD behind a remote MULE.

        Up to eight EUDs sit behind each MULE and share its radio, so the node id
        alone would merge them; the callsign the sender carried (FML-ADR-070's
        `Contact.callsign`) keeps each one distinct and addressable.
        """
        slug = re.sub(r"[^A-Za-z0-9_.-]", "_", callsign)
        if slug != callsign or len(slug) > 32:
            # Sanitising or truncating can make two callsigns collide; a short
            # digest of the original keeps them distinct.
            digest = hashlib.sha256(callsign.encode()).hexdigest()[:8]
            slug = f"{slug[:24]}~{digest}"
        return f"{MESH_PREFIX}{node.lstrip('!')}-{slug}"

    @property
    def text_room(self) -> str:
        """The room plain Meshtastic text lands in (the stock app has no rooms)."""
        return ALL_CHAT if ALL_CHAT in self.rooms else min(self.rooms)

    def is_echo(self, sender_uid: str) -> bool:
        """Whether a server event came from this gateway, for itself or a node."""
        return (
            sender_uid == self.own_uid
            or sender_uid.startswith(MESH_PREFIX)
            or sender_uid in self.mesh_eud
        )

    def remote_uid(self, m: LoraIn) -> str:
        """Return the uid a remote EUD appears under on this side.

        Its own uid when it carried a well-formed one that no client of this
        server already holds; otherwise a minted one. Reusing a local client's
        uid would let anyone with the channel key impersonate that client.
        """
        uid = m.uid
        if (
            uid
            and UID_PATTERN.fullmatch(uid)
            and uid != self.own_uid
            and uid not in self.roster
        ):
            return uid
        return self.mesh_uid(m.node, m.callsign)

    # LoRa -> TAK -------------------------------------------------------------

    def from_lora(self, m: LoraIn) -> list[Action]:
        """Decide what one accepted LoRa message becomes on the TAK side."""
        uid = self.remote_uid(m)
        self.mesh_eud[uid] = (m.node, m.callsign)
        if m.kind == "pli":
            if m.point is None:
                return [Refused("LoRa PLI without a position")]
            xml = build_pli(m.callsign, uid, m.point, "via LoRa gateway")
            return [TakOut(xml, uid, m.callsign, m.point)]
        if m.kind == "text" or m.to in self.rooms:  # text: stock app, room only
            room = self.text_room if m.kind == "text" else m.to
            xml = build_geochat(m.callsign, uid, room, room, m.text)
            return [TakOut(xml, uid, m.callsign)]
        if m.to == ALL_CHAT or m.to == "":
            return [Refused(f"room {m.to or '(none)'!r} is not relayed here")]
        key = self.callsign_key.get(m.to, m.to)  # callsign -> key binding
        decision = decide_delivery(key, self.roster, default_recipient=None)
        if decision.delivery != "DELIVER" or decision.target is None:
            return [Refused(decision.reason or "unresolved")]
        to_callsign = next(
            (c for c, k in self.callsign_key.items() if k == decision.target),
            decision.target,
        )
        xml = build_geochat(m.callsign, uid, to_callsign, decision.target, m.text)
        return [TakOut(xml, uid, m.callsign)]

    # TAK -> LoRa -------------------------------------------------------------

    def from_tak(self, xml: bytes, now: float) -> list[Action]:
        """Decide what one server CoT event becomes on the LoRa side."""
        try:
            # Expat resolves no external entities, so this is not an XXE path;
            # a hostile frame can at worst raise, which is handled.
            ev = ET.fromstring(xml)  # noqa: S314
        except ET.ParseError:
            return [Refused("unparseable CoT")]
        typ, uid = ev.get("type", ""), ev.get("uid", "")
        det = ev.find("detail")
        if det is None:
            return []
        if typ == "b-t-f":
            return self._chat(det)
        if typ.startswith("a-f-"):
            return self._pli(ev, det, uid, now)
        return []

    def _chat(self, det: ET.Element) -> list[Action]:
        chat, rem = det.find("__chat"), det.find("remarks")
        if chat is None or rem is None or not (rem.text or "").strip():
            return []
        grp, link = chat.find("chatgrp"), det.find("link")
        sender_uid = (grp.get("uid0") if grp is not None else None) or (
            link.get("uid") if link is not None else ""
        )
        if self.is_echo(sender_uid or ""):
            return []  # an echo: expected on every session the gateway holds
        # The same chat reaches every proxy session the gateway holds; act once.
        mid = chat.get("messageId", "")
        if mid:
            now = time.time()
            self.seen_chat = {
                k: t for k, t in self.seen_chat.items() if now - t < SEEN_MESSAGE_TTL_S
            }
            if mid in self.seen_chat:
                return []
            self.seen_chat[mid] = now
        sender = chat.get("senderCallsign", "?")
        if sender_uid:
            self.roster[sender_uid] = sender_uid
            self.callsign_key[sender] = sender_uid
        room, chat_id = chat.get("chatroom", ""), chat.get("id", "")
        text = rem.text.strip()
        if chat_id in self.rooms:
            return [self._lora_chat("^all", sender, chat_id, text, sender_uid)]
        remote = self.mesh_eud.get(chat_id)
        if remote is not None:  # a direct message to one EUD behind a remote MULE
            node, callsign = remote
            return [self._lora_chat(node, sender, callsign, text, sender_uid)]
        return [Refused(f"chat for {room!r} is not for the mesh")]

    def _lora_chat(
        self, dest: str, sender: str, to: str, text: str, uid: str = ""
    ) -> Action:
        if self.lora_format == "text":
            budget = LoraPayloadBudget(USABLE_BYTES, TEXT_FRAMING_BYTES)
            if not fits_payload(text, sender, "", budget):
                return Refused("message exceeds the 231-byte LoRa payload")
            return LoraOut("text", dest, sender, text=text)
        framing = TAK_FRAMING_BYTES + (UID_FRAMING_BYTES if uid else 0)
        budget = LoraPayloadBudget(USABLE_BYTES, framing)
        if not fits_payload(text, sender + uid, to, budget):
            return Refused("message exceeds the 231-byte LoRa payload")
        return LoraOut("chat", dest, sender, to=to, text=text, uid=uid)

    def _pli(
        self, ev: ET.Element, det: ET.Element, uid: str, now: float
    ) -> list[Action]:
        if self.is_echo(uid):
            return []  # an echo: expected on every session the gateway holds
        contact = det.find("contact")
        callsign = contact.get("callsign", uid) if contact is not None else uid
        self.roster[uid] = uid
        self.callsign_key[callsign] = uid
        if self.lora_format == "text":
            return []  # the stock app cannot show a TAK position
        last = self.last_pli.get(uid)
        if last is not None and now - last < self.pli_interval_s:
            return []
        pt = ev.find("point")
        try:
            point = (
                float(pt.get("lat", "")),
                float(pt.get("lon", "")),
                float(pt.get("hae", "0")),
            )
        except (AttributeError, ValueError):
            return [Refused("PLI without a usable point")]
        self.last_pli[uid] = now
        return [LoraOut("pli", "^all", callsign, point=point, uid=uid)]


# ---------------------------------------------------------------- runtime


def encode(out: LoraOut, own_uid: str) -> tuple[bytes, int]:
    """Encode a LoraOut as (payload, Meshtastic port number)."""
    from meshtastic.protobuf import atak_pb2, portnums_pb2

    if out.kind == "text":
        payload = f"{out.callsign}: {out.text}".encode()
        return payload, portnums_pb2.PortNum.TEXT_MESSAGE_APP
    t = atak_pb2.TAKPacket()
    t.contact.callsign = out.callsign
    if out.uid:
        t.contact.device_callsign = out.uid
    if out.kind == "chat":
        t.chat.message = out.text
        t.chat.to = out.to
    else:
        lat, lon, hae = out.point or (0.0, 0.0, 0.0)
        t.pli.latitude_i = int(lat * 1e7)
        t.pli.longitude_i = int(lon * 1e7)
        t.pli.altitude = int(hae) if abs(hae) < 9e6 else 0
    return t.SerializeToString(), portnums_pb2.PortNum.ATAK_PLUGIN


def decode(packet: dict[str, Any], channel: int, me: str) -> LoraIn | None:
    """Turn a received Meshtastic packet into a LoraIn, or None if not accepted."""
    d = packet.get("decoded") or {}
    on_channel = packet.get("channel", 0) == channel
    direct_to_me = bool(packet.get("pkiEncrypted")) and packet.get("toId") == me
    if not (on_channel or direct_to_me):
        return None
    node = packet.get("fromId") or ""
    if d.get("portnum") == "TEXT_MESSAGE_APP" and on_channel:
        name = ((packet.get("_user") or {}).get("longName")) or node
        return LoraIn("text", node, name, text=d.get("text", ""))
    if d.get("portnum") != "ATAK_PLUGIN":
        return None
    from meshtastic.protobuf import atak_pb2

    t = atak_pb2.TAKPacket()
    try:
        t.ParseFromString(d["payload"])
    except Exception:
        return None
    cs = t.contact.callsign or node
    uid = t.contact.device_callsign
    if t.HasField("chat"):
        return LoraIn("chat", node, cs, to=t.chat.to, text=t.chat.message, uid=uid)
    if t.HasField("pli"):
        p = t.pli
        point = (p.latitude_i * 1e-7, p.longitude_i * 1e-7, float(p.altitude))
        return LoraIn("pli", node, cs, point=point, uid=uid)
    return None


@dataclass
class Proxy:
    """A server session held on behalf of one EUD behind a remote MULE.

    A TAK server binds one identity to one connection and routes a direct
    message (`<marti><dest>`) to the connection holding that callsign. An EUD
    that exists on the server only as events the gateway relays over its own
    connection is therefore unreachable by direct message -- measured on the
    bench on 2026-10-18 with OpenTAKServer and an iTAK client. Giving each
    remote EUD its own session, opened with the gateway's certificate and
    announced with that EUD's SA, makes the server bind it like any EUD.
    """

    uid: str
    node: str
    callsign: str
    point: tuple[float, float, float] | None = None
    writer: asyncio.StreamWriter | None = None
    last_used: float = 0.0
    ready: asyncio.Event = field(default_factory=asyncio.Event)
    task: asyncio.Task | None = None


class Gateway:
    """Radio + PyTAK connections around a Translator."""

    def __init__(self, a: argparse.Namespace) -> None:
        """Hold arguments and state; nothing connects until run()."""
        self.a = a
        self.tr = Translator(a.uid, frozenset(a.room), a.lora_format, a.pli_interval)
        self.writer: asyncio.StreamWriter | None = None
        self.pending: list[tuple[float, bytes]] = []
        self.proxies: dict[str, Proxy] = {}
        self.stats = dict.fromkeys(
            ("to_tak", "to_lora", "refused", "flushed", "overflow", "connects"), 0
        )
        self.stats.update(proxies=0, proxy_fallback=0)

    def radio_up(self, loop: asyncio.AbstractEventLoop, inbox: asyncio.Queue) -> None:
        """Open the radio and route accepted packets into the event loop."""
        from meshtastic.serial_interface import SerialInterface
        from pubsub import pub

        self.iface = SerialInterface(self.a.dev or glob.glob("/dev/ttyACM*")[0])
        idx = [
            c.index
            for c in self.iface.localNode.channels
            if c.role and c.settings.name == CHANNEL
        ]
        if len(idx) != 1 or idx[0] == 0:
            raise SystemExit("FAIL: MULE-TEST not found exactly once off index 0")
        self.ch, self.me = idx[0], self.iface.getMyNodeInfo()["user"]["id"]

        def on_rx(packet: dict[str, Any], interface: Any) -> None:  # noqa: ANN401
            user = (interface.nodes or {}).get(packet.get("fromId"), {}).get("user")
            m = decode({**packet, "_user": user}, self.ch, self.me)
            if m is not None:
                loop.call_soon_threadsafe(inbox.put_nowait, m)
                return
            port = (packet.get("decoded") or {}).get("portnum")
            if port in ("ATAK_PLUGIN", "TEXT_MESSAGE_APP"):
                # Metadata only, never content: shows where an EUD's traffic
                # lands when it is not on the relayed channel.
                log(
                    "ignored",
                    frm=packet.get("fromId"),
                    channel=packet.get("channel", 0),
                    port=port,
                    pki=bool(packet.get("pkiEncrypted")),
                    to=packet.get("toId"),
                )

        # pypubsub holds listeners by weak reference: without this attribute the
        # closure is collected when radio_up returns and nothing is ever received.
        self.on_rx = on_rx
        pub.subscribe(self.on_rx, "meshtastic.receive")
        log(
            "radio",
            node=self.me,
            channel=self.ch,
            hop_limit=self.iface.localNode.localConfig.lora.hop_limit,
            lora_format=self.a.lora_format,
            rooms=sorted(self.a.room),
        )

    def lora_send(self, out: LoraOut) -> None:
        """Put one LoraOut on the air."""
        payload, port = encode(out, self.a.uid)
        self.iface.sendData(
            payload,
            destinationId=out.dest,
            portNum=port,
            channelIndex=self.ch,
            wantAck=out.dest != "^all",
        )
        self.stats["to_lora"] += 1
        log("tak->lora", kind=out.kind, sender=out.callsign, to=out.to, dest=out.dest)

    async def tak_send(self, data: bytes, hold: bool = True) -> None:
        """Send to the server, or hold it while disconnected."""
        if self.writer is not None:
            try:
                self.writer.write(data)
                await self.writer.drain()
                return
            except OSError as e:
                log("tak send error", err=str(e)[:120])
        if not hold:
            return
        now = time.time()
        self.pending = [(t, d) for t, d in self.pending if now - t < QUEUE_AGE_S]
        if len(self.pending) >= QUEUE_MAX:
            self.pending.pop(0)
            self.stats["overflow"] += 1
        self.pending.append((now, data))
        log("tak held (disconnected)", depth=len(self.pending))

    def announce(self) -> bytes:
        """Return this gateway's own SA."""
        return build_pli(
            self.a.callsign, self.a.uid, (0.0, 0.0, 0.0), "FML bench gateway"
        )

    def apply(self, actions: list[Action], source: str) -> list[TakOut]:
        """Carry out LoRa-side actions now; return TAK-side items to send."""
        to_tak = []
        for act in actions:
            if isinstance(act, Refused):
                self.stats["refused"] += 1
                log("refused", source=source, reason=act.reason)
            elif isinstance(act, LoraOut):
                self.lora_send(act)
            else:
                to_tak.append(act)
        return to_tak

    async def pump_lora(self, inbox: asyncio.Queue) -> None:
        """Forward accepted LoRa messages to the server."""
        while True:
            m: LoraIn = await inbox.get()
            log("lora->tak", kind=m.kind, sender=m.callsign, to=m.to)
            for out in self.apply(self.tr.from_lora(m), "lora"):
                self.stats["to_tak"] += 1
                if not (out.via and await self.proxy_send(out)):
                    await self.tak_send(out.xml)

    # ---- per-remote-EUD sessions -------------------------------------------

    def proxy_sa(self, p: Proxy) -> bytes:
        """Return the SA a proxy session announces for its EUD."""
        return build_pli(p.callsign, p.uid, p.point or (0.0, 0.0, 0.0), "via LoRa")

    async def proxy_send(self, out: TakOut) -> bool:
        """Send on the remote EUD's own session; False means use the main one."""
        p = self.proxies.get(out.via)
        if p is None:
            node = self.tr.mesh_eud.get(out.via, ("", ""))[0]
            same_node = sum(1 for q in self.proxies.values() if q.node == node)
            if len(self.proxies) >= PROXY_TOTAL or same_node >= PROXY_PER_NODE:
                log("proxy cap reached", uid=out.via)
                self.stats["proxy_fallback"] += 1
                return False
            p = Proxy(out.via, node, out.callsign, out.point)
            self.proxies[p.uid] = p
            p.task = asyncio.create_task(self.proxy_loop(p))
            self.stats["proxies"] += 1
            log("proxy open", uid=p.uid, callsign=p.callsign)
        if out.point is not None:
            p.point = out.point
        p.last_used = time.time()
        try:
            await asyncio.wait_for(p.ready.wait(), 10)
        except TimeoutError:
            self.stats["proxy_fallback"] += 1
            log("proxy not ready; sent on the gateway session", uid=p.uid)
            return False
        try:
            p.writer.write(out.xml)
            await p.writer.drain()
        except (OSError, AttributeError):
            self.stats["proxy_fallback"] += 1
            return False
        return True

    async def proxy_loop(self, p: Proxy) -> None:
        """Hold one remote EUD's session open, reconnecting, until it goes idle."""
        while time.time() - p.last_used < PROXY_IDLE_S:
            try:
                reader, p.writer = await self.connect()
                p.writer.write(self.proxy_sa(p))
                await p.writer.drain()
                p.ready.set()
                log("proxy connected", uid=p.uid)
                last_sa = time.time()
                while time.time() - p.last_used < PROXY_IDLE_S:
                    if time.time() - last_sa >= PROXY_SA_REFRESH_S:
                        # On a timer, not on a quiet read: a busy server never
                        # goes quiet, and the SA goes stale after 180 s.
                        p.writer.write(self.proxy_sa(p))
                        await p.writer.drain()
                        last_sa = time.time()
                    wait = max(1.0, PROXY_SA_REFRESH_S - (time.time() - last_sa))
                    try:
                        frame = await asyncio.wait_for(
                            reader.readuntil(b"</event>"), wait
                        )
                    except TimeoutError:
                        continue
                    start = frame.find(b"<event")
                    if start >= 0:
                        actions = self.tr.from_tak(frame[start:], time.time())
                        self.apply(actions, "proxy")
            except (
                OSError,
                ConnectionError,
                asyncio.IncompleteReadError,
                asyncio.LimitOverrunError,
            ) as e:
                log("proxy disconnected", uid=p.uid, err=str(e)[:80])
            p.ready.clear()
            if p.writer is not None:
                p.writer.close()
            p.writer = None
            await asyncio.sleep(2)
        self.proxies.pop(p.uid, None)
        log("proxy closed (idle)", uid=p.uid)

    async def connect(self) -> tuple[asyncio.StreamReader, asyncio.StreamWriter]:
        """Open the TLS stream with PyTAK (FML-ADR-033)."""
        import pytak

        cp = configparser.ConfigParser()
        cp["gw"] = {
            "COT_URL": f"tls://{self.a.host}:{self.a.port}",
            "PYTAK_TLS_CLIENT_CERT": self.a.cert,
            "PYTAK_TLS_CLIENT_KEY": self.a.key,
            "PYTAK_TLS_CLIENT_CAFILE": self.a.ca,
            "PYTAK_TLS_DONT_CHECK_HOSTNAME": "1" if self.a.no_hostname_check else "",
        }
        return await pytak.protocol_factory(cp["gw"])

    async def session(self) -> None:
        """One server session: announce, flush held items, then read until loss."""
        reader, writer = await self.connect()
        self.writer = writer
        self.stats["connects"] += 1
        log("tak connected", host=self.a.host)
        await self.tak_send(self.announce(), hold=False)
        held, self.pending = self.pending, []
        for t, data in held:
            if time.time() - t < QUEUE_AGE_S:
                self.stats["flushed"] += 1
                await self.tak_send(data)
        while True:
            try:
                frame = await reader.readuntil(b"</event>")
            except asyncio.IncompleteReadError:
                raise ConnectionError("server closed") from None
            start = frame.find(b"<event")
            if start >= 0:
                self.apply(self.tr.from_tak(frame[start:], time.time()), "tak")

    async def keepalive(self) -> None:
        """Re-send this gateway's SA every 30 s."""
        while True:
            await asyncio.sleep(30)
            await self.tak_send(self.announce(), hold=False)

    async def report(self) -> None:
        """Log counters every 60 s."""
        while True:
            await asyncio.sleep(60)
            log("stats", **self.stats)

    async def run(self) -> None:
        """Run until killed, reconnecting across authority swaps."""
        loop, inbox = asyncio.get_running_loop(), asyncio.Queue()
        self.radio_up(loop, inbox)
        tasks = [self.pump_lora(inbox), self.keepalive(), self.report()]
        self.background = [asyncio.create_task(c) for c in tasks]
        while True:
            try:
                await self.session()
            except (OSError, ConnectionError, asyncio.LimitOverrunError) as e:
                log("tak disconnected", err=str(e)[:120])
            if self.writer is not None:
                self.writer.close()
            self.writer = None
            await asyncio.sleep(2)


def main() -> None:
    """Parse arguments and run the gateway."""
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--host", default="tak.field")
    p.add_argument("--port", type=int, default=8089)
    p.add_argument("--cert", required=True)
    p.add_argument("--key", required=True)
    p.add_argument("--ca", required=True)
    p.add_argument(
        "--no-hostname-check",
        action="store_true",
        help="for a backend whose certificate does not name tak.field",
    )
    p.add_argument("--dev", default=None)
    p.add_argument("--callsign", default="FML-GW")
    p.add_argument("--uid", default="fml-bench-gw")
    p.add_argument(
        "--room",
        action="append",
        help='relayed room, repeatable (default: "All Chat Rooms")',
    )
    p.add_argument("--lora-format", choices=["tak", "text"], default="tak")
    p.add_argument("--pli-interval", type=float, default=60.0)
    a = p.parse_args()
    a.room = a.room or [ALL_CHAT]
    asyncio.run(Gateway(a).run())


if __name__ == "__main__":
    main()
