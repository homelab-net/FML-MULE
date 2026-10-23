"""Tests for test/bench/fml-lora-gw.py's translation rules.

The Translator is the gateway's decision logic with no radio and no socket, so
every rule the bench run could not show -- room scoping, direct messages both
ways, fail-closed recipients, echo suppression, the payload budget -- is pinned
here. The protobuf encode/decode needs the meshtastic client and is skipped where
it is absent (CI); the bench host runs it.
"""

from __future__ import annotations

import importlib.util
import json
import random
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

_TOOL = Path(__file__).resolve().parents[2] / "test" / "bench" / "fml-lora-gw.py"
_SPEC = importlib.util.spec_from_file_location("fml_lora_gw", _TOOL)
assert _SPEC is not None and _SPEC.loader is not None
gw = importlib.util.module_from_spec(_SPEC)
# dataclasses look their module up in sys.modules while the class is built.
sys.modules[_SPEC.name] = gw
_SPEC.loader.exec_module(gw)

ROOM = "FML-BENCH"
GW_UID = "fml-bench-gw"
IP_UID = "ip-eud-1"
NODE = "!22509c08"


def tr(fmt: str = "tak") -> object:
    return gw.Translator(GW_UID, frozenset({ROOM}), fmt, 60.0)


def chat_xml(sender: str, uid: str, room: str, chat_id: str, text: str) -> bytes:
    return gw.build_geochat(sender, uid, room, chat_id, text)


def pli_xml(callsign: str, uid: str) -> bytes:
    return gw.build_pli(callsign, uid, (1.0, 2.0, 3.0))


def only(actions: list) -> object:
    assert len(actions) == 1, actions
    return actions[0]


# --------------------------------------------------------------- TAK -> LoRa


def test_room_chat_is_broadcast_on_the_mesh() -> None:
    out = only(tr().from_tak(chat_xml("IP1", IP_UID, ROOM, ROOM, "hello"), 0))
    assert isinstance(out, gw.LoraOut)
    assert (out.kind, out.dest, out.callsign, out.to, out.text) == (
        "chat",
        "^all",
        "IP1",
        ROOM,
        "hello",
    )


def test_a_room_that_is_not_configured_is_not_put_on_the_air() -> None:
    xml = chat_xml("IP1", IP_UID, gw.ALL_CHAT, gw.ALL_CHAT, "live room traffic")
    assert isinstance(only(tr().from_tak(xml, 0)), gw.Refused)


def test_ip_direct_message_to_a_lora_eud_goes_to_that_node_only() -> None:
    t = tr()
    t.from_lora(gw.LoraIn("chat", NODE, "LORA1", to=ROOM, text="hi"))
    mesh_uid = t.mesh_uid(NODE, "LORA1")
    xml = chat_xml("IP1", IP_UID, "LORA1", mesh_uid, "just you")
    out = only(t.from_tak(xml, 0))
    assert isinstance(out, gw.LoraOut)
    assert out.dest == NODE
    assert out.to == "LORA1"
    assert out.text == "just you"


def test_eight_euds_behind_one_mule_stay_distinct_and_addressable() -> None:
    """Up to eight EUDs share one MULE's radio; DMs must reach the right one."""
    t = tr()
    for n in range(8):
        t.from_lora(gw.LoraIn("chat", NODE, f"TEAM{n}", to=ROOM, text="up"))
    uids = {t.mesh_uid(NODE, f"TEAM{n}") for n in range(8)}
    assert len(uids) == 8
    xml = chat_xml("IP1", IP_UID, "TEAM5", t.mesh_uid(NODE, "TEAM5"), "for five")
    out = only(t.from_tak(xml, 0))
    assert isinstance(out, gw.LoraOut)
    assert (out.dest, out.to) == (NODE, "TEAM5")


def test_direct_message_between_ip_euds_is_not_for_the_mesh() -> None:
    xml = chat_xml("IP1", IP_UID, "IP2", "ip-eud-2", "private")
    assert isinstance(only(tr().from_tak(xml, 0)), gw.Refused)


def test_echo_of_the_gateways_own_chat_is_dropped() -> None:
    t = tr()
    xml = chat_xml("LORA1", t.mesh_uid(NODE, "LORA1"), ROOM, ROOM, "loop?")
    assert t.from_tak(xml, 0) == []


def test_echo_of_the_gateways_own_sa_is_dropped() -> None:
    assert tr().from_tak(pli_xml("FML-GW", GW_UID), 0) == []


def test_pli_is_rate_limited_per_uid() -> None:
    t = tr()
    assert isinstance(only(t.from_tak(pli_xml("IP1", IP_UID), 100.0)), gw.LoraOut)
    assert t.from_tak(pli_xml("IP1", IP_UID), 130.0) == []
    assert isinstance(only(t.from_tak(pli_xml("IP1", IP_UID), 161.0)), gw.LoraOut)


def test_pli_without_a_point_is_refused_not_fatal() -> None:
    ev = ET.fromstring(pli_xml("IP1", IP_UID))  # noqa: S314 (own test fixture)
    ev.remove(ev.find("point"))
    assert isinstance(only(tr().from_tak(ET.tostring(ev), 0)), gw.Refused)


def test_oversize_message_is_refused_not_truncated() -> None:
    xml = chat_xml("IP1", IP_UID, ROOM, ROOM, "x" * 300)
    out = only(tr().from_tak(xml, 0))
    assert isinstance(out, gw.Refused)
    assert "231" in out.reason


def test_malformed_cot_is_refused() -> None:
    assert isinstance(only(tr().from_tak(b"<event><detail>", 0)), gw.Refused)


def test_text_mode_sends_room_chat_as_plain_text_and_skips_pli() -> None:
    t = tr("text")
    out = only(t.from_tak(chat_xml("IP1", IP_UID, ROOM, ROOM, "hi app"), 0))
    assert isinstance(out, gw.LoraOut)
    assert out.kind == "text"
    assert t.from_tak(pli_xml("IP1", IP_UID), 0) == []


# --------------------------------------------------------------- LoRa -> TAK


def _parsed(action: object) -> ET.Element:
    assert isinstance(action, gw.TakOut)
    return ET.fromstring(action.xml)  # noqa: S314 (built by the module under test)


def test_lora_room_chat_reaches_the_relayed_room() -> None:
    ev = _parsed(only(tr().from_lora(gw.LoraIn("chat", NODE, "LORA1", ROOM, "hi"))))
    chat = ev.find("detail/__chat")
    assert chat.get("chatroom") == ROOM
    assert chat.get("id") == ROOM
    assert chat.get("senderCallsign") == "LORA1"
    assert ev.find("detail/remarks").text == "hi"


def test_lora_chat_to_all_chat_rooms_is_refused() -> None:
    m = gw.LoraIn("chat", NODE, "LORA1", gw.ALL_CHAT, "to everyone")
    assert isinstance(only(tr().from_lora(m)), gw.Refused)


def test_lora_direct_message_to_an_unknown_recipient_is_refused() -> None:
    """CONOPS 23: never widened to a room or to everyone."""
    m = gw.LoraIn("chat", NODE, "LORA1", "NOBODY", "secret")
    out = only(tr().from_lora(m))
    assert isinstance(out, gw.Refused)
    assert "unresolved" in out.reason


def test_lora_direct_message_to_a_known_ip_eud_by_callsign() -> None:
    t = tr()
    t.from_tak(pli_xml("IP1", IP_UID), 0)  # learn IP1 -> ip-eud-1
    ev = _parsed(only(t.from_lora(gw.LoraIn("chat", NODE, "LORA1", "IP1", "dm"))))
    chat = ev.find("detail/__chat")
    assert chat.get("id") == IP_UID
    assert chat.get("chatroom") == "IP1"
    assert ev.find("detail/marti/dest").get("callsign") == "IP1"


def test_lora_pli_becomes_a_tak_position_under_a_mesh_uid() -> None:
    t = tr()
    ev = _parsed(only(t.from_lora(gw.LoraIn("pli", NODE, "LORA1", point=(1, 2, 3)))))
    assert ev.get("uid") == t.mesh_uid(NODE, "LORA1")
    assert ev.find("detail/contact").get("callsign") == "LORA1"


def test_lora_plain_text_lands_in_the_relayed_room() -> None:
    ev = _parsed(
        only(tr().from_lora(gw.LoraIn("text", NODE, "Meshtastic 9c08", text="app")))
    )
    assert ev.find("detail/__chat").get("id") == ROOM


# --------------------------------------------------------------- wire format


def test_encode_decode_round_trip() -> None:
    pytest.importorskip("meshtastic")
    payload, _port = gw.encode(gw.LoraOut("chat", "^all", "IP1", ROOM, "hi"), GW_UID)
    assert len(payload) <= gw.USABLE_BYTES
    packet = {
        "decoded": {"portnum": "ATAK_PLUGIN", "payload": payload},
        "channel": 3,
        "fromId": NODE,
    }
    m = gw.decode(packet, 3, "!172ab0c8")
    assert (m.kind, m.callsign, m.to, m.text) == ("chat", "IP1", ROOM, "hi")
    assert gw.decode({**packet, "channel": 0}, 3, "!172ab0c8") is None
    stray_dm = {**packet, "channel": 0, "pkiEncrypted": True, "toId": "!someone"}
    assert gw.decode(stray_dm, 3, "!172ab0c8") is None


def test_measured_framing_bound_holds_at_the_budget_edge() -> None:
    """The 12-byte TAK framing constant is an upper bound for any fitting body."""
    pytest.importorskip("meshtastic")
    sender, to = "C" * 20, "D" * 36
    body_len = gw.USABLE_BYTES - gw.TAK_FRAMING_BYTES - len(sender) - len(to)
    out = gw.LoraOut("chat", "^all", sender, to, "z" * body_len)
    payload, _ = gw.encode(out, GW_UID)
    assert len(payload) <= gw.USABLE_BYTES


def test_radio_listener_survives_garbage_collection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Pypubsub holds weak references; the receive callback must stay alive."""
    pytest.importorskip("pubsub")
    import gc
    import types
    from types import SimpleNamespace as NS

    from pubsub import pub

    channel = NS(index=3, role=2, settings=NS(name="MULE-TEST"))
    node = NS(channels=[channel], localConfig=NS(lora=NS(hop_limit=0)))

    class FakeIface:
        localNode = node
        nodes: dict = {}  # noqa: RUF012 (a fake's class attribute)

        def __init__(self, dev: str) -> None:
            self.dev = dev

        def getMyNodeInfo(self) -> dict:
            return {"user": {"id": "!172ab0c8"}}

    fake = types.ModuleType("meshtastic.serial_interface")
    fake.SerialInterface = FakeIface
    monkeypatch.setitem(sys.modules, "meshtastic.serial_interface", fake)
    if "meshtastic" not in sys.modules:
        monkeypatch.setitem(sys.modules, "meshtastic", types.ModuleType("meshtastic"))
    got: list = []
    inbox = NS(put_nowait=got.append)
    loop = NS(call_soon_threadsafe=lambda fn, item: fn(item))
    args = NS(uid=GW_UID, room=[ROOM], lora_format="text", pli_interval=60.0, dev="x")
    g = gw.Gateway(args)
    g.radio_up(loop, inbox)
    gc.collect()
    packet = {
        "decoded": {"portnum": "TEXT_MESSAGE_APP", "text": "hi"},
        "channel": 3,
        "fromId": NODE,
    }
    pub.sendMessage("meshtastic.receive", packet=packet, interface=FakeIface("x"))
    pub.unsubscribe(g.on_rx, "meshtastic.receive")
    assert len(got) == 1
    assert got[0].text == "hi"


def test_the_same_chat_arriving_on_several_sessions_is_relayed_once() -> None:
    """Every proxy session receives room chat; the radio must carry it once."""
    t = tr()
    xml = chat_xml("IP1", IP_UID, ROOM, ROOM, "once")
    assert isinstance(only(t.from_tak(xml, 0)), gw.LoraOut)
    assert t.from_tak(xml, 0) == []


def test_lora_traffic_names_the_remote_euds_own_session() -> None:
    t = tr()
    out = only(t.from_lora(gw.LoraIn("chat", NODE, "LORA1", to=ROOM, text="x")))
    assert isinstance(out, gw.TakOut)
    assert out.via == t.mesh_uid(NODE, "LORA1")
    assert out.callsign == "LORA1"


def test_field_default_relays_all_chat_rooms_both_ways() -> None:
    """The owner's field policy: All Chat Rooms rides LoRa."""
    t = gw.Translator(GW_UID, frozenset({gw.ALL_CHAT}), "tak", 60.0)
    xml = chat_xml("IP1", IP_UID, gw.ALL_CHAT, gw.ALL_CHAT, "team")
    out = only(t.from_tak(xml, 0))
    assert isinstance(out, gw.LoraOut)
    assert (out.dest, out.to) == ("^all", gw.ALL_CHAT)
    m = gw.LoraIn("chat", NODE, "LORA1", gw.ALL_CHAT, "back")
    ev = _parsed(only(t.from_lora(m)))
    assert ev.find("detail/__chat").get("id") == gw.ALL_CHAT


def test_callsigns_that_sanitise_alike_get_distinct_uids() -> None:
    t = tr()
    assert t.mesh_uid(NODE, "A B") != t.mesh_uid(NODE, "A_B")
    long_a, long_b = "X" * 40 + "1", "X" * 40 + "2"
    assert t.mesh_uid(NODE, long_a) != t.mesh_uid(NODE, long_b)


# --------------------------------------------------------------- real uids


def test_ip_side_uid_is_carried_onto_the_air() -> None:
    out = only(tr().from_tak(pli_xml("IP1", IP_UID), 0))
    assert isinstance(out, gw.LoraOut)
    assert out.uid == IP_UID
    chat = only(tr().from_tak(chat_xml("IP1", IP_UID, ROOM, ROOM, "hi"), 0))
    assert chat.uid == IP_UID


def test_remote_euds_keep_their_own_uid_on_this_side() -> None:
    """One identity across bearers: no duplicate contacts, replies by real uid."""
    t = tr()
    m = gw.LoraIn("chat", NODE, "LORA1", to=ROOM, text="hi", uid="ANDROID-abc123")
    out = only(t.from_lora(m))
    assert out.via == "ANDROID-abc123"
    ev = _parsed(out)
    assert ev.find("detail/__chat/chatgrp").get("uid0") == "ANDROID-abc123"
    dm = chat_xml("IP1", IP_UID, "LORA1", "ANDROID-abc123", "back to you")
    back = only(t.from_tak(dm, 0))
    assert (back.dest, back.to) == (NODE, "LORA1")


def test_a_remote_claim_on_a_local_clients_uid_is_refused() -> None:
    t = tr()
    t.from_tak(pli_xml("IP1", IP_UID), 0)  # IP_UID is a client of this server
    m = gw.LoraIn("chat", NODE, "LORA1", to=ROOM, text="spoof", uid=IP_UID)
    out = only(t.from_lora(m))
    assert out.via == t.mesh_uid(NODE, "LORA1")


def test_a_malformed_carried_uid_falls_back_to_a_minted_one() -> None:
    t = tr()
    m = gw.LoraIn("chat", NODE, "LORA1", to=ROOM, text="x", uid="bad uid<>")
    assert only(t.from_lora(m)).via == t.mesh_uid(NODE, "LORA1")


def test_the_echo_of_a_relayed_real_uid_is_dropped() -> None:
    t = tr()
    t.from_lora(gw.LoraIn("pli", NODE, "LORA1", point=(1, 2, 3), uid="ANDROID-x"))
    assert t.from_tak(pli_xml("LORA1", "ANDROID-x"), 0) == []


def test_a_carried_uid_shrinks_the_chat_budget() -> None:
    t = tr()
    text = "y" * 150
    assert isinstance(t._lora_chat("^all", "IP1", ROOM, text), gw.LoraOut)
    long_uid = "S-1-5-21-" + "1" * 60
    out = t._lora_chat("^all", "IP1", ROOM, text, long_uid)
    assert isinstance(out, gw.Refused)


def test_uid_round_trips_through_the_protobuf() -> None:
    pytest.importorskip("meshtastic")
    out = gw.LoraOut("chat", "^all", "IP1", ROOM, "hi", uid=IP_UID)
    payload, _port = gw.encode(out, GW_UID)
    packet = {
        "decoded": {"portnum": "ATAK_PLUGIN", "payload": payload},
        "channel": 3,
        "fromId": NODE,
    }
    assert gw.decode(packet, 3, "!172ab0c8").uid == IP_UID


# --------------------------------------------------------------- upstream TAKPackets

_DATA = Path(__file__).resolve().parent / "data"
_GOLDEN = {
    p["name"]: p
    for p in json.loads((_DATA / "upstream_takpackets.json").read_text("utf-8"))[
        "packets"
    ]
}
_COMPRESSED = {
    v["text"]: bytes.fromhex(v["hex"])
    for v in json.loads((_DATA / "unishox2_vectors.json").read_text("utf-8"))["vectors"]
}


def _v(n: int) -> bytes:
    out = b""
    while True:
        b, n = n & 0x7F, n >> 7
        out += bytes([b | (0x80 if n else 0)])
        if not n:
            return out


def _f(num: int, data: bytes | int) -> bytes:
    """One protobuf field: an int as a varint, bytes as length-delimited."""
    if isinstance(data, int):
        return _v(num << 3) + _v(data)
    return _v(num << 3 | 2) + _v(len(data)) + data


def _contact(callsign: bytes, uid: bytes = b"") -> bytes:
    return _f(2, _f(1, callsign) + (_f(2, uid) if uid else b""))


def _rx(payload: bytes) -> object:
    packet = {
        "decoded": {"portnum": "ATAK_PLUGIN", "payload": payload},
        "channel": 3,
        "fromId": NODE,
    }
    return gw.decode(packet, 3, "!172ab0c8")


def test_upstream_golden_packets_decode_to_their_sender() -> None:
    for name, p in _GOLDEN.items():
        m = _rx(bytes.fromhex(p["payload_hex"]))
        e = p["expect"]
        assert m is not None, name
        assert (m.kind, m.callsign, m.uid) == (e["kind"], e["callsign"], e["uid"]), name
        if m.kind == "chat":
            assert (m.text, m.to) == (e["text"], e["to"]), name
        else:
            assert m.point == pytest.approx((e["lat"], e["lon"], e["alt"])), name


def test_the_gateways_own_plain_format_still_decodes_without_meshtastic() -> None:
    chat = _f(6, _f(1, b"hi") + _f(2, ROOM.encode()))
    m = _rx(_contact(b"IP1", IP_UID.encode()) + chat)
    got = (m.kind, m.callsign, m.uid, m.to, m.text)
    assert got == ("chat", "IP1", IP_UID, ROOM, "hi")


def test_a_plain_string_that_is_not_utf8_is_refused() -> None:
    assert _rx(_contact(b"\xff\xfe") + _f(6, _f(1, b"x") + _f(2, b"R"))) is None


def test_a_compressed_callsign_over_the_upstream_limit_is_refused() -> None:
    chat = _f(6, _f(1, _COMPRESSED["a"]))
    assert _rx(_f(1, 1) + _contact(_COMPRESSED["a" * 300]) + chat) is None


def test_a_callsign_with_control_characters_is_refused() -> None:
    assert _rx(_contact(b"EVIL\x1b[2J") + _f(6, _f(1, b"x") + _f(2, b"R"))) is None


def test_the_last_member_of_the_payload_oneof_wins() -> None:
    lat, lon = (1).to_bytes(4, "little"), (2).to_bytes(4, "little")
    pli = _f(5, b"\x0d" + lat + b"\x15" + lon)
    chat = _f(6, _f(1, b"later") + _f(2, ROOM.encode()))
    assert _rx(_contact(b"C") + pli + chat).kind == "chat"
    assert _rx(_contact(b"C") + chat + pli).kind == "pli"


def test_a_pli_outside_the_globe_is_refused() -> None:
    lat = (95 * 10**7).to_bytes(4, "little", signed=True)
    pli = _f(5, b"\x0d" + lat + b"\x15" + (0).to_bytes(4, "little"))
    assert _rx(_contact(b"C") + pli) is None


def test_random_payloads_never_raise_out_of_decode() -> None:
    rng = random.Random(20261023)  # noqa: S311 (seeded test input, not crypto)
    for _ in range(3000):
        payload = bytes(rng.getrandbits(8) for _ in range(rng.randint(0, 231)))
        m = _rx(payload)
        assert m is None or m.kind in ("chat", "pli")


def test_the_wire_reader_uses_the_upstream_field_numbers() -> None:
    pytest.importorskip("meshtastic")
    from meshtastic.protobuf import atak_pb2

    def num(msg: object, name: str) -> int:
        return msg.DESCRIPTOR.fields_by_name[name].number

    t, c, g, p = atak_pb2.TAKPacket, atak_pb2.Contact, atak_pb2.GeoChat, atak_pb2.PLI
    top = ("is_compressed", "contact", "pli", "chat", "detail")
    assert [num(t, n) for n in top] == [1, 2, 5, 6, 7]
    assert [num(c, n) for n in ("callsign", "device_callsign")] == [1, 2]
    assert [num(g, n) for n in ("message", "to")] == [1, 2]
    assert [num(p, n) for n in ("latitude_i", "longitude_i", "altitude")] == [1, 2, 3]


# --------------------------------------------------------------- bare-text attribution


def _pli_in(node: str, callsign: str, uid: str) -> object:
    return gw.LoraIn("pli", node, callsign, point=(0.0, 0.0, 0.0), uid=uid)


def _text_in(node: str = NODE, text: str = "room text") -> object:
    return gw.LoraIn("text", node, node, text=text)


def test_bare_text_right_after_a_pli_is_attributed_to_that_sender() -> None:
    t = gw.Translator(GW_UID, frozenset({gw.ALL_CHAT}), "tak", 60.0)
    t.from_lora(_pli_in(NODE, "OTS-USER", "ANDROID-ots1"), now=100.0)
    chat = _parsed(only(t.from_lora(_text_in(), now=104.5))).find("detail/__chat")
    assert chat.get("senderCallsign") == "OTS-USER"
    assert chat.find("chatgrp").get("uid0") == "ANDROID-ots1"


def test_bare_text_after_a_stale_pli_keeps_the_radio_name() -> None:
    t = tr()
    t.from_lora(_pli_in(NODE, "OTS-USER", "ANDROID-ots1"), now=100.0)
    later = 100.0 + gw.ATTRIBUTION_WINDOW_S + 1
    ev = _parsed(only(t.from_lora(_text_in(), now=later)))
    assert ev.find("detail/__chat").get("senderCallsign") == NODE


def test_a_node_carrying_several_identities_is_never_attributed() -> None:
    """A MULE radio relays for up to eight EUDs; its text names none of them."""
    t = tr()
    t.from_lora(_pli_in(NODE, "EUD-A", "ANDROID-a"), now=100.0)
    t.from_lora(_pli_in(NODE, "EUD-B", "ANDROID-b"), now=101.0)
    ev = _parsed(only(t.from_lora(_text_in(), now=102.0)))
    assert ev.find("detail/__chat").get("senderCallsign") == NODE


def test_a_rebound_node_stays_unattributed_when_the_first_identity_returns() -> None:
    t = tr()
    t.from_lora(_pli_in(NODE, "EUD-A", "ANDROID-a"), now=100.0)
    t.from_lora(_pli_in(NODE, "FORGED", "ANDROID-f"), now=101.0)
    t.from_lora(_pli_in(NODE, "EUD-A", "ANDROID-a"), now=102.0)
    ev = _parsed(only(t.from_lora(_text_in(), now=103.0)))
    assert ev.find("detail/__chat").get("senderCallsign") == NODE


def test_attributed_text_cannot_take_a_local_client_uid() -> None:
    t = tr()
    t.from_tak(pli_xml("IP1", IP_UID), 0.0)  # IP_UID is a client of this server
    t.sent_uid.clear()  # isolate the claim rule from the echo rule
    t.from_lora(_pli_in(NODE, "IP1", IP_UID), now=10_000.0)
    out = only(t.from_lora(_text_in(), now=10_001.0))
    assert out.via == t.mesh_uid(NODE, "IP1")


def test_the_attribution_map_is_bounded() -> None:
    t = tr()
    for i in range(gw.ATTRIBUTION_MAX_NODES + 50):
        t.from_lora(_pli_in(f"!{i:08x}", f"C{i}", f"ANDROID-{i}"), now=100.0)
    assert len(t.node_seen) == gw.ATTRIBUTION_MAX_NODES
    assert "!00000000" not in t.node_seen


# --------------------------------------------------------------- loop guard


def test_our_own_traffic_coming_back_from_lora_is_refused() -> None:
    """An OpenTAKServer Meshtastic path on the channel re-sends what we sent."""
    t = gw.Translator(GW_UID, frozenset({gw.ALL_CHAT}), "tak", 60.0)
    sent = only(t.from_tak(pli_xml("IP1", IP_UID), time.time()))
    assert isinstance(sent, gw.LoraOut)
    back = only(t.from_lora(_pli_in("!0badf00d", "IP1", IP_UID)))
    assert isinstance(back, gw.Refused)
    assert "echo" in back.reason


# --------------------------------------------------------------- encoded length


def test_an_oversize_position_is_refused_before_transmission() -> None:
    """The chat budget is a pre-check; the encoded payload is the real limit."""
    pytest.importorskip("meshtastic")
    from types import SimpleNamespace as NS

    sent: list = []
    args = NS(uid=GW_UID, room=[ROOM], lora_format="tak", pli_interval=60.0, dev="x")
    g = gw.Gateway(args)
    g.iface = NS(sendData=lambda *a, **k: sent.append((a, k)))
    g.ch = 3
    g.lora_send(gw.LoraOut("pli", "^all", "C" * 150, point=(1, 2, 3), uid="U" * 100))
    assert sent == []
    assert g.stats["refused"] == 1
    g.lora_send(gw.LoraOut("pli", "^all", "IP1", point=(1, 2, 3), uid=IP_UID))
    assert len(sent) == 1
