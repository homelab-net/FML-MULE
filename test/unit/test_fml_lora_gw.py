"""Tests for test/bench/fml-lora-gw.py's translation rules.

The Translator is the gateway's decision logic with no radio and no socket, so
every rule the bench run could not show -- room scoping, direct messages both
ways, fail-closed recipients, echo suppression, the payload budget -- is pinned
here. The protobuf encode/decode needs the meshtastic client and is skipped where
it is absent (CI); the bench host runs it.
"""

from __future__ import annotations

import importlib.util
import sys
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
