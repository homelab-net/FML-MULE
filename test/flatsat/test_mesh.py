"""Tests for `mule.mesh`, the reader half of loop detection.

`FML-ADR-056` disabled bridge loop avoidance and asked for a detector. The
decision (`mule.loops`) has tests of its own; these exercise the reader that
feeds it, and prove the parser turns the real `batctl transglobal` output a loop
produced (`docs/evidence/TBR-NET-01/2026-08-30-loop-detected-on-the-bench.md`)
into pairs `mule.loops` fires on.
"""

from __future__ import annotations

from pathlib import Path

from mule.loops import loop_signatures
from mule.mesh import MeshTranslationReadings, parse_transglobal

# The transglobal table node 1 showed after the induced loop (2026-08-30
# evidence). Node 1's own addresses -- be:bb...92 (wlan0) and 56:44...94 (bat0 /
# br-field) -- both appear as clients announced by the peer originator
# 1e:fa:23:ea:fb:69: frames left and came back.
LOOP_TRANSGLOBAL = """\
[B.A.T.M.A.N. adv 2024.2, MainIF/MAC: wlan0/be:bb:69:03:ea:92
                                      (bat0/56:44:6e:89:4d:94 BATMAN_IV)]
   Client             VID Flags Last ttvn     Via        ttvn
 * 56:44:6e:89:4d:94   -1 [R...] (  5) 1e:fa:23:ea:fb:69 (  5)
 * 32:ce:c9:96:a5:04   -1 [R...] (  5) 1e:fa:23:ea:fb:69 (  5)
 * 32:ce:c9:96:a5:04    1 [....] (  5) 1e:fa:23:ea:fb:69 (  5)
 * be:bb:69:03:ea:92   -1 [....] (  5) 1e:fa:23:ea:fb:69 (  5)
"""
OWN = ("be:bb:69:03:ea:92", "56:44:6e:89:4d:94")
PEER = "1e:fa:23:ea:fb:69"

# A different table: one client announced by two different originators, the other
# loop signature. Constructed, not captured; the shape mule.loops names.
DOUBLE_ORIGINATOR = """\
   Client             VID Flags Last ttvn     Via        ttvn
 * aa:aa:aa:aa:aa:aa   -1 [....] (  3) 11:11:11:11:11:11 (  3)
 * aa:aa:aa:aa:aa:aa   -1 [....] (  3) 22:22:22:22:22:22 (  3)
"""


def test_parse_transglobal_reads_client_and_via_pairs() -> None:
    """Each starred row yields (client, announcing originator)."""
    entries = parse_transglobal(LOOP_TRANSGLOBAL)

    assert (OWN[1], PEER) in entries
    assert (OWN[0], PEER) in entries
    # Header/legend lines carry no `*` and contribute no pair.
    assert all(via == PEER for _client, via in entries)
    assert len(entries) == 4


def test_parse_transglobal_of_nothing_is_empty() -> None:
    """No starred rows is an empty tuple, not an error."""
    assert parse_transglobal("") == ()
    assert parse_transglobal("   Client   VID   Via\n") == ()


def test_own_address_announced_by_a_peer_fires_on_the_real_table() -> None:
    """The reader's output makes mule.loops fire on the captured loop."""
    readings = _readings(transglobal=LOOP_TRANSGLOBAL, own=OWN)

    assert "own_address_announced_by_a_peer" in loop_signatures(readings)


def test_a_client_under_two_originators_fires_the_other_signature() -> None:
    """The reader feeds the multi-originator signature too."""
    readings = _readings(transglobal=DOUBLE_ORIGINATOR, own=("cc:cc:cc:cc:cc:cc",))

    assert "client_under_more_than_one_originator" in loop_signatures(readings)


def test_global_entries_are_none_when_batctl_cannot_run() -> None:
    """A batctl runner returning None reports None, not an empty table."""
    readings = MeshTranslationReadings(batctl_transglobal=lambda: None)

    assert readings.global_translation_entries() is None


def test_own_addresses_are_read_from_sysfs(tmp_path: Path) -> None:
    """Read every interface's MAC from /sys/class/net/*/address."""
    _write_iface(tmp_path, "wlan0", "be:bb:69:03:ea:92")
    _write_iface(tmp_path, "bat0", "56:44:6e:89:4d:94")
    readings = MeshTranslationReadings(batctl_transglobal=lambda: None, root=tmp_path)

    assert set(readings.own_addresses() or ()) == set(OWN)


def test_own_addresses_are_none_when_sysfs_is_absent(tmp_path: Path) -> None:
    """No /sys/class/net at all is 'cannot tell' (None), not 'owns nothing'."""
    readings = MeshTranslationReadings(
        batctl_transglobal=lambda: None, root=tmp_path / "nonexistent"
    )

    assert readings.own_addresses() is None


def test_an_unreadable_address_is_skipped(tmp_path: Path) -> None:
    """An interface whose address will not read is skipped, not fatal."""
    _write_iface(tmp_path, "wlan0", "be:bb:69:03:ea:92")
    # A directory named `address` raises on read_text (IsADirectoryError).
    (tmp_path / "weird").mkdir()
    (tmp_path / "weird" / "address").mkdir()
    readings = MeshTranslationReadings(batctl_transglobal=lambda: None, root=tmp_path)

    assert readings.own_addresses() == ("be:bb:69:03:ea:92",)


def _write_iface(root: Path, name: str, mac: str) -> None:
    (root / name).mkdir()
    (root / name / "address").write_text(mac + "\n", encoding="utf-8")


def _readings(transglobal: str, own: tuple[str, ...]) -> MeshTranslationReadings:
    """Build a reader with a fixed transglobal and own-address set."""
    reader = MeshTranslationReadings(batctl_transglobal=lambda: transglobal)
    reader.own_addresses = lambda: own  # type: ignore[method-assign]
    return reader
