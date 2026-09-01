"""Parse `iw` and `batctl` output into radio-state readings.

This is the board-independent core of a `RadioState` implementation
(`interfaces.py`): the text-to-reading step, and only that. It does **not** map
an interface to a `Bearer`, because that map is per board and
`TBR-HW-01`/`TBR-RF-03` own it, and it does **not** shell out, because the
command layer is where the platform can fail and belongs behind the injected
`run` seam a full reader will add. Both are why this stops at parsing: the parts
above it are the blocked half of the interface, and this is the half that is
not blocked.

**The `None` / empty distinction is the whole point.** Every function takes the
command's output as `str | None`:

- `None` means the command could not run -- absent binary, permission, no such
  interface. The reading is unknown, and every function returns `None`.
- `""` or output with no entries means the command ran and found nothing -- no
  interfaces, no peers, no originators. The reading is a real zero, and the
  function returns `[]` or `0`.

A node with no `iw` and a node with `iw` and no peers are different states, and a
reader that cannot tell them apart is the defect `docs/readings.md` and roadmap
item 1.6 both name. Distinguishing them here, at the parse boundary, is how the
full reader inherits it for free.

Fixtures under `test/fixtures/radio/` are authentic `mac80211_hwsim` output, not
a hardware capture; see their README.
"""

from __future__ import annotations


def interfaces(iw_dev_output: str | None) -> list[tuple[str, str]] | None:
    """Interfaces and their type, from `iw dev`.

    Returns `(name, type)` pairs -- for example `("wlan0", "mesh point")`,
    `("wlan1", "AP")`. `None` if `iw dev` could not run. An empty list is a real
    reading: `iw` ran and the node has no wireless interfaces.

    Type is what `iw` prints, unnormalised. Mapping `mesh point` or `AP` onto a
    `Bearer` is the per-board step this deliberately does not take.
    """
    if iw_dev_output is None:
        return None
    result: list[tuple[str, str]] = []
    name: str | None = None
    for raw in iw_dev_output.splitlines():
        line = raw.strip()
        if line.startswith("Interface "):
            name = line[len("Interface ") :].strip()
        elif line.startswith("type ") and name is not None:
            result.append((name, line[len("type ") :].strip()))
            name = None
    return result


def station_count(station_dump_output: str | None) -> int | None:
    """Count stations from `iw dev <iface> station dump`.

    For a mesh point this is the number of peers; for an AP, associated clients.
    `None` if the command could not run -- which includes there being no such
    interface. `0` is a real reading: the interface exists and has no peers, and
    `iw` prints nothing, so an empty string is a legitimate zero.
    """
    if station_dump_output is None:
        return None
    return sum(
        1 for line in station_dump_output.splitlines() if line.startswith("Station ")
    )


def originator_count(batctl_originators_output: str | None) -> int | None:
    """Count originators from `batctl meshif <if> originators`.

    Counts only the lines batman-adv marks with `*`, the currently selected best
    next hop for an originator, so a node that appears several times through
    different neighbours is counted once. `None` if `batctl` could not run. `0`
    is a real reading: the mesh is up and this node has no originators yet.

    The leading header line names the algorithm and is not an originator; it is
    skipped because it does not start with the `*` marker.
    """
    if batctl_originators_output is None:
        return None
    return sum(
        1
        for line in batctl_originators_output.splitlines()
        if line.lstrip().startswith("*")
    )
