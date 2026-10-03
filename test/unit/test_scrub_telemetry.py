"""Tests for tools/scrub-telemetry.py.

The point of this tool is that a capture can be filed as evidence without
leaking what `SECURITY.md` prohibits. So the tests that matter are the ones that
fail when it stops redacting -- and, just as much, the ones that fail when it
starts redacting things it should not, because a scrubber that eats the bench
topology makes the evidence unreadable and teaches people to skip it.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

_TOOL = Path(__file__).resolve().parents[2] / "tools" / "scrub-telemetry.py"
_SPEC = importlib.util.spec_from_file_location("scrub_telemetry", _TOOL)
assert _SPEC is not None and _SPEC.loader is not None
scrub = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(scrub)


def _doc(**commands: str) -> dict[str, object]:
    return {
        "manifest": {"node": "pi-mule-1", "kernel": "6.18.50+rpt-rpi-v8"},
        "commands": {name: {"stdout": text} for name, text in commands.items()},
    }


def test_real_oui_mac_is_redacted() -> None:
    """A Raspberry Pi OUI is a real equipment identifier and must not survive."""
    out = scrub.scrub_document(_doc(radio="addr dc:a6:32:12:34:56"))
    assert "dc:a6:32:12:34:56" not in str(out)
    assert out["scrub_manifest"]["redacted"]["MAC"] == 1


def test_locally_administered_mac_is_kept_and_counted() -> None:
    """Hwsim and veth addresses identify nothing; eating them loses correlation."""
    out = scrub.scrub_document(_doc(batman="orig 1e:fa:23:ea:fb:69"))
    assert "1e:fa:23:ea:fb:69" in str(out)
    assert out["scrub_manifest"]["kept_locally_administered_macs"] == 1
    assert "MAC" not in out["scrub_manifest"]["redacted"]


def test_eui64_link_local_is_redacted_because_it_encodes_the_mac() -> None:
    """fe80:: with ff:fe reconstructs the MAC exactly, so a MAC pattern misses it."""
    out = scrub.scrub_document(_doc(addrs="inet6 fe80::dea6:32ff:fe12:3456/64"))
    assert "dea6:32ff:fe12:3456" not in str(out)
    assert out["scrub_manifest"]["redacted"]["LINKLOCAL"] == 1


def test_eui64_link_local_from_a_virtual_mac_is_kept() -> None:
    """The two already committed under docs/evidence/ decode to virtual MACs."""
    out = scrub.scrub_document(_doc(addrs="inet6 fe80::4c59:ecff:fee3:6716/64"))
    assert "fe80::4c59:ecff:fee3:6716" in str(out)


def test_certificate_fingerprint_is_not_mistaken_for_a_mac() -> None:
    """A truncated fingerprint is colon-hex too; an earlier pattern matched one."""
    document = _doc(x="noise")
    document["fingerprint"] = "F7:8C:72:75:9B:4C:D7:41:71:BC:40:81"
    out = scrub.scrub_document(document)
    assert out["fingerprint"] == "F7:8C:72:75:9B:4C:D7:41:71:BC:40:81"


@pytest.mark.parametrize(
    "addr", ["10.41.0.1", "192.168.0.10", "172.16.0.5", "169.254.1.1"]
)
def test_private_addresses_are_kept(addr: str) -> None:
    """Bench topology is not identity, and routing tables must stay readable."""
    out = scrub.scrub_document(_doc(routes=f"default via {addr}"))
    assert addr in str(out)


def test_public_address_is_redacted() -> None:
    """A routable address can locate a deployment."""
    out = scrub.scrub_document(_doc(routes="inet 203.0.113.7/32"))
    assert "203.0.113.7" not in str(out)


def test_hostname_is_redacted_everywhere_it_appears() -> None:
    """The manifest is not the only place a node names itself."""
    document = _doc(log="pi-mule-1 kernel: brcmfmac: firmware loaded")
    out = scrub.scrub_document(document)
    assert "pi-mule-1" not in str(out)


def test_the_same_identifier_gets_the_same_token() -> None:
    """Correlation across a pre/post pair is the reason tokens are stable."""
    out = scrub.scrub_document(
        _doc(a="addr dc:a6:32:12:34:56", b="peer dc:a6:32:12:34:56 again")
    )
    rendered = str(out)
    assert rendered.count("<MAC-01-REDACTED>") == 2
    assert out["scrub_manifest"]["redacted"]["MAC"] == 1


def test_manifest_records_what_is_not_handled() -> None:
    """docs/evidence/README.md: a silently trimmed log is not honest."""
    out = scrub.scrub_document(_doc(x="nothing sensitive"))
    manifest = out["scrub_manifest"]
    assert manifest["tool"] == "tools/scrub-telemetry.py"
    assert manifest["not_handled"], "the tool must say what it leaves behind"
    assert manifest["kept_deliberately"]


def test_the_null_address_is_not_an_equipment_identifier() -> None:
    """`ip link` reports 00:00:00:00:00:00 for interfaces with no hardware address."""
    assert not scrub.is_equipment_mac("00:00:00:00:00:00")
    out = scrub.scrub_document(
        _doc(links="link/none 00:00:00:00:00:00 brd 00:00:00:00:00:00")
    )
    assert "00:00:00:00:00:00" in str(out)
