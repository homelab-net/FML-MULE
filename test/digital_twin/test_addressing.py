"""Tests for `mule.addressing`.

`FML-ADR-063` requires an overlapping uplink to be reported and prohibits
silence. `test/bench/route-isolation.sh` reproduces the failure on veth (mesh
`10.41.0.0/16`, an uplink handing out `10.41.5.0/24` inside it); these plant the
same overlap, and the case the ADR cares about most -- "cannot tell" must not
read as "no overlap".
"""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from mule.addressing import detect_overlapping_uplink, parse_ip_addr

#: The per-deployment mesh prefix, as route-isolation.sh uses it. Config, so it
#: is passed to detect_overlapping_uplink rather than read from the fake.
MESH = "10.41.0.0/16"
#: An uplink range inside the mesh prefix: the silent-collision case.
OVERLAPPING = "10.41.5.20/24"
#: An uplink on a different range entirely: the safe case.
SEPARATE = "192.168.8.158/24"


@dataclass
class FakeUplink:
    """Scripted uplink-range readings.

    Simulates: what `ip addr show <uplink>` would report. `None` is how "the
    uplink cannot be read at all" is expressed, distinct from an empty tuple.
    """

    ranges: tuple[str, ...] | None = ()

    def uplink_ranges(self) -> tuple[str, ...] | None:
        """Report the scripted uplink ranges."""
        return self.ranges


def test_a_separate_uplink_is_clear() -> None:
    """A uplink outside the mesh prefix reports CLEAR with no offenders."""
    verdict = detect_overlapping_uplink(MESH, FakeUplink((SEPARATE,)))

    assert verdict.outcome == "CLEAR"
    assert verdict.overlapping == ()
    assert verdict.reason is None


def test_an_overlapping_uplink_is_reported() -> None:
    """The route-isolation overlap is reported, naming the offending range."""
    verdict = detect_overlapping_uplink(MESH, FakeUplink((SEPARATE, OVERLAPPING)))

    assert verdict.outcome == "OVERLAP"
    assert verdict.overlapping == (OVERLAPPING,)
    assert verdict.reason is not None
    assert OVERLAPPING in verdict.reason


def test_an_empty_uplink_is_clear_not_unknown() -> None:
    """An uplink with no address is a real reading: CLEAR, not UNKNOWN."""
    assert detect_overlapping_uplink(MESH, FakeUplink(())).outcome == "CLEAR"


@pytest.mark.parametrize(
    ("mesh_prefix", "uplink"),
    [
        (None, FakeUplink((SEPARATE,))),
        (MESH, FakeUplink(None)),
        (None, FakeUplink(None)),
    ],
)
def test_cannot_tell_is_unknown_never_clear(
    mesh_prefix: str | None, uplink: FakeUplink
) -> None:
    """A missing reading fails to UNKNOWN: silence is what FML-ADR-063 forbids."""
    assert detect_overlapping_uplink(mesh_prefix, uplink).outcome == "UNKNOWN"


def test_an_unparseable_mesh_prefix_is_unknown() -> None:
    """A prefix that is not a network is UNKNOWN, not silently CLEAR."""
    verdict = detect_overlapping_uplink("not-a-network", FakeUplink((SEPARATE,)))

    assert verdict.outcome == "UNKNOWN"
    assert verdict.reason is not None


def test_an_unparseable_uplink_range_is_unknown() -> None:
    """An uplink range that is not a network is UNKNOWN, not CLEAR."""
    verdict = detect_overlapping_uplink(MESH, FakeUplink(("garbage",)))

    assert verdict.outcome == "UNKNOWN"


def test_a_v6_uplink_does_not_overlap_a_v4_mesh() -> None:
    """Different IP versions cannot overlap, and comparing them must not raise."""
    verdict = detect_overlapping_uplink(MESH, FakeUplink(("fd00::/8",)))

    assert verdict.outcome == "CLEAR"


def test_parse_ip_addr_extracts_inet_and_inet6_cidrs() -> None:
    """Pull the CIDRs from the inet/inet6 lines, ignoring the rest."""
    sample = """\
2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UP
    link/ether 00:c0:ca:a7:41:fe brd ff:ff:ff:ff:ff:ff
    inet 10.41.5.20/24 brd 10.41.5.255 scope global dynamic eth0
       valid_lft 42sec preferred_lft 42sec
    inet6 fe80::2c0:caff:fea7:41fe/64 scope link
       valid_lft forever preferred_lft forever
"""
    assert parse_ip_addr(sample) == ("10.41.5.20/24", "fe80::2c0:caff:fea7:41fe/64")


def test_parse_ip_addr_of_nothing_is_empty() -> None:
    """No inet lines is an empty tuple, a real 'no address' reading."""
    assert parse_ip_addr("") == ()
