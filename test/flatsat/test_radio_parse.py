"""Tests for `radio_parse`, against authentic `iw`/`batctl` fixtures.

The fixtures under `test/fixtures/radio/` are real `mac80211_hwsim` output, not
a hardware capture, and their README says so. They exercise the parser against
the text a real driver produces; they say nothing about RF.

The distinction these tests exist to defend is `None` (the command could not
run) versus empty (it ran and found nothing). A parser that collapses the two
is the defect roadmap item 1.6 and `docs/readings.md` both name.
"""

from __future__ import annotations

from pathlib import Path

from . import radio_parse

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures" / "radio"


def _fixture(name: str) -> str:
    return (FIXTURES / name).read_text()


# --- interfaces -------------------------------------------------------------


def test_interfaces_reads_name_and_type() -> None:
    parsed = radio_parse.interfaces(_fixture("iw-dev.txt"))
    assert parsed == [("wlan0", "mesh point")]


def test_interfaces_none_when_command_could_not_run() -> None:
    assert radio_parse.interfaces(None) is None


def test_interfaces_empty_is_a_real_reading_not_none() -> None:
    # `iw dev` ran on a node with no wireless interfaces: empty, not unknown.
    assert radio_parse.interfaces("") == []


# --- station count ----------------------------------------------------------


def test_station_count_counts_peers() -> None:
    assert radio_parse.station_count(_fixture("iw-station-dump-associated.txt")) == 1


def test_station_count_zero_when_no_peers() -> None:
    # The interface exists and has no peers; `iw` prints nothing.
    assert radio_parse.station_count(_fixture("iw-station-dump-empty.txt")) == 0


def test_station_count_none_when_command_could_not_run() -> None:
    assert radio_parse.station_count(None) is None


def test_station_count_distinguishes_none_from_zero() -> None:
    # The whole point: a node with no `iw` and a node with no peers differ.
    assert radio_parse.station_count(None) != radio_parse.station_count("")


# --- originator count -------------------------------------------------------


def test_originator_count_counts_selected_next_hops() -> None:
    assert radio_parse.originator_count(_fixture("batctl-originators.txt")) == 1


def test_originator_count_skips_the_header_line() -> None:
    # The header names the algorithm and is not an originator. A parser that
    # counted every non-blank line would return one too many here.
    header_only = (
        "[B.A.T.M.A.N. adv 2024.2, MainIF/MAC: wlan0/de:4d:71:17:c4:6d "
        "(bat0/de:4d:71:17:c4:6d BATMAN_IV)]\n"
        "   Originator        last-seen (#/255) Nexthop           [outgoingIF]\n"
    )
    assert radio_parse.originator_count(header_only) == 0


def test_originator_count_none_when_command_could_not_run() -> None:
    assert radio_parse.originator_count(None) is None
