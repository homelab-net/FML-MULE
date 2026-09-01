"""Tests for `CommandRadio`, the real `RadioState` reader.

The command runner is injected, so these feed it authentic `iw`/`batctl`
fixtures without a radio, exactly as `test_sysfs` builds a synthetic tree. What
is exercised is the reader's logic -- mapping, presence, association, and the
`None`-versus-real-reading discipline -- against the text a driver produces.
"""

from __future__ import annotations

from pathlib import Path

from mule.bearers import Bearer

from .radio import CommandRadio, CommandRunner

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures" / "radio"


def _fixture(name: str) -> str:
    return (FIXTURES / name).read_text()


def _runner(table: dict[tuple[str, ...], str | None]) -> CommandRunner:
    """Build a command runner backed by a fixed table, `None` for anything absent."""

    def run(argv: list[str]) -> str | None:
        return table.get(tuple(argv))

    return run


# A board where wlan0 is the halow mesh bearer. The map is what TBR-HW-01
# supplies; here it is a fixture map, not a claim about any real board.
MAP: dict[str, Bearer] = {"wlan0": "halow"}


# --- enumerated -------------------------------------------------------------


def test_enumerated_lists_mapped_present_bearers() -> None:
    radio = CommandRadio(MAP, _runner({("iw", "dev"): _fixture("iw-dev.txt")}))
    assert radio.enumerated() == ["halow"]


def test_enumerated_none_when_iw_could_not_run() -> None:
    radio = CommandRadio(MAP, _runner({}))  # no "iw dev" entry -> None
    assert radio.enumerated() is None


def test_enumerated_empty_when_no_mapped_interface_present() -> None:
    # iw ran and lists wlan0, but the map points at wlan9: nothing enumerated,
    # and that is a real empty reading, not None.
    radio = CommandRadio(
        {"wlan9": "halow"}, _runner({("iw", "dev"): _fixture("iw-dev.txt")})
    )
    assert radio.enumerated() == []


def test_enumerated_empty_under_an_empty_board_map() -> None:
    # The state before TBR-HW-01: iw sees interfaces, the node knows no bearers.
    radio = CommandRadio({}, _runner({("iw", "dev"): _fixture("iw-dev.txt")}))
    assert radio.enumerated() == []


# --- associated -------------------------------------------------------------


def test_associated_true_with_a_mesh_peer() -> None:
    radio = CommandRadio(
        MAP,
        _runner(
            {
                ("iw", "dev", "wlan0", "station", "dump"): _fixture(
                    "iw-station-dump-associated.txt"
                )
            }
        ),
    )
    assert radio.associated("halow") is True


def test_associated_false_with_no_peer() -> None:
    radio = CommandRadio(
        MAP,
        _runner(
            {
                ("iw", "dev", "wlan0", "station", "dump"): _fixture(
                    "iw-station-dump-empty.txt"
                )
            }
        ),
    )
    assert radio.associated("halow") is False


def test_associated_none_when_bearer_maps_to_no_interface() -> None:
    # lora is not in the map: the node cannot tell, which is None, not False.
    radio = CommandRadio(MAP, _runner({}))
    assert radio.associated("lora") is None


def test_associated_none_when_command_could_not_run() -> None:
    # halow maps to wlan0, but the station dump command is absent from the table.
    radio = CommandRadio(MAP, _runner({}))
    assert radio.associated("halow") is None


def test_associated_distinguishes_none_from_false() -> None:
    unmapped = CommandRadio(MAP, _runner({}))
    present = CommandRadio(
        MAP,
        _runner(
            {
                ("iw", "dev", "wlan0", "station", "dump"): _fixture(
                    "iw-station-dump-empty.txt"
                )
            }
        ),
    )
    # "cannot tell" and "present, no peer" are different answers.
    assert unmapped.associated("lora") is None
    assert present.associated("halow") is False


# --- it satisfies the Protocol ----------------------------------------------


def test_is_a_radiostate() -> None:
    from .interfaces import RadioState

    radio = CommandRadio(MAP, _runner({}))
    assert isinstance(radio, RadioState)
