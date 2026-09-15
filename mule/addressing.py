"""Whether an uplink's address range overlaps the node's mesh prefix.

`FML-ADR-063` makes the field prefix per-deployment and then requires:

    A node shall never carry an uplink whose address range overlaps its mesh
    prefix without reporting it. Detection is the requirement; silence is what
    is prohibited.

and names where the check belongs:

    A detection requirement with no implementation. ... the check belongs behind
    a reading interface with a fake rather than being written into an ADR as
    though it existed.

This is that check. It **detects and reports**; it does not refuse the uplink or
drop the mesh, because `FML-ADR-063` leaves that to service-plane policy
(`TBR-TAK-01`, `services/`): "what a node does beyond reporting is not decided
here." It reads nothing and commands nothing; a caller hands it the readings.

The failure it guards is the one `test/bench/route-isolation.sh` reproduces: an
uplink handing out a range inside the mesh prefix silently steals mesh
destinations, with nothing in `batctl` to show for it. `FML-ADR-061`'s automatic
merge makes that collision the normal case, which is why silence is the thing
prohibited.
"""

from __future__ import annotations

import ipaddress
from dataclasses import dataclass
from typing import Literal, Protocol, runtime_checkable

#: The outcome of the check. `UNKNOWN` is not `CLEAR`: a node that cannot read
#: its prefix or its uplink has not shown the uplink is safe, and `FML-ADR-063`
#: prohibits treating "cannot tell" as "no overlap".
Outcome = Literal["CLEAR", "OVERLAP", "UNKNOWN"]


@runtime_checkable
class AddressReadings(Protocol):
    """What the node can read from its uplink interface.

    Only the uplink is a reading; the mesh prefix is configuration, carried in
    the mission package (`network.address_prefix`, `FML-ADR-063`), and is passed
    to `detect_overlapping_uplink` as an argument -- the same readings-versus-
    policy split `mule.timekeeping.assess` uses.
    """

    def uplink_ranges(self) -> tuple[str, ...] | None:
        """Return the uplink's address ranges (CIDRs), or None if unreadable.

        `None` if the uplink cannot be read at all (distinct from an empty tuple,
        which is a real reading: an uplink with no address). See `parse_ip_addr`.
        """
        ...


@dataclass(frozen=True)
class OverlapAssessment:
    """The verdict, with the offending ranges and a diagnosable reason.

    `overlapping` lists the uplink ranges that overlap the mesh prefix, so an
    operator handed an `OVERLAP` knows which range to change rather than a bare
    `True`. `reason` is populated for `OVERLAP` and `UNKNOWN` and `None` for
    `CLEAR`, the same shape `mule.timekeeping.TimeAssessment` uses.
    """

    outcome: Outcome
    overlapping: tuple[str, ...]
    reason: str | None


def parse_ip_addr(text: str) -> tuple[str, ...]:
    """Extract the CIDRs from `ip addr` output: its `inet` and `inet6` lines.

    Pure, so it is tested against captured output rather than a running `ip`.
    The `ip` invocation itself stays out of `mule/` (nothing here shells out),
    the same way `mule.sysfs.parse_chronyc_tracking` keeps `chronyc` out; a
    caller runs `ip addr show <uplink>` and hands the text here. Package
    `iproute2`.
    """
    ranges: list[str] = []
    for line in text.splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[0] in ("inet", "inet6"):
            ranges.append(parts[1])
    return tuple(ranges)


def detect_overlapping_uplink(
    mesh_prefix: str | None, observed: AddressReadings
) -> OverlapAssessment:
    """Report whether any uplink range overlaps the mesh prefix.

    `mesh_prefix` is the node's per-deployment prefix from the mission package
    (`FML-ADR-063`), `None` where none is configured. Fails to `UNKNOWN`, never
    silently to `CLEAR`, when the prefix or the reading is missing or
    unparseable: `FML-ADR-063` prohibits silence, and "cannot tell" is not "no
    overlap". A `CLEAR` verdict means the node actually read both sides and they
    do not overlap.
    """
    prefix = mesh_prefix
    ranges = observed.uplink_ranges()
    if prefix is None or ranges is None:
        return OverlapAssessment(
            "UNKNOWN", (), "mesh prefix or uplink ranges could not be read"
        )

    try:
        mesh = ipaddress.ip_network(prefix, strict=False)
    except ValueError:
        return OverlapAssessment(
            "UNKNOWN", (), f"mesh prefix {prefix!r} is not a network"
        )

    overlapping: list[str] = []
    for candidate in ranges:
        try:
            net = ipaddress.ip_network(candidate, strict=False)
        except ValueError:
            return OverlapAssessment(
                "UNKNOWN", (), f"uplink range {candidate!r} is not a network"
            )
        # Different IP versions cannot overlap; comparing them would raise.
        if net.version == mesh.version and net.overlaps(mesh):
            overlapping.append(candidate)

    if overlapping:
        joined = ", ".join(overlapping)
        return OverlapAssessment(
            "OVERLAP",
            tuple(overlapping),
            f"uplink range(s) {joined} overlap mesh prefix {prefix}",
        )
    return OverlapAssessment("CLEAR", (), None)
