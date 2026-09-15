"""Reading batman-adv mesh state that `mule.loops` judges.

`mule.loops` decides whether the node is in a bridging loop; it reads nothing.
This is the other half: the concrete reader for its `TranslationReadings`
Protocol, the one `FML-ADR-056` asked for when it disabled `batman-adv`'s bridge
loop avoidance and named a detector in exchange. Same split as `mule.timekeeping`
(decides) to `mule.sysfs` (reads).

Two readings, two sources, exactly as `docs/readings.md` records:

* `own_addresses` is a kernel read of `/sys/class/net/*/address` -- every
  interface's MAC, because `FML-ADR-056` names "the node's own bridge address
  arriving from the mesh" and a bench loop announced the mesh hard interface's
  address first.
* `global_translation_entries` is `batctl meshif <if> transglobal` over netlink;
  `batctl` is a command, so its invocation is **injected**, not shelled out from
  here -- `mule/` shells out nowhere, the same rule the chronyc probe in
  `mule.sysfs` follows.

Nothing here concludes. A signature is a "look", not a diagnosis; `mule.loops`
says which and why.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

#: Where the kernel lists the node's network interfaces. A parameter so tests can
#: point at a synthetic tree, not because it is expected to move.
NET_ROOT = Path("/sys/class/net")

#: A MAC address, no capturing groups so `findall` returns the whole match.
_MAC = re.compile(r"(?:[0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}")


def parse_transglobal(text: str) -> tuple[tuple[str, str], ...]:
    """Parse `(client, originator)` pairs from `batctl ... transglobal` output.

    Each translation row batman-adv marks with `*` names a client and, in its
    `Via` column, the originator announcing it -- the pair `mule.loops` reasons
    about. A row carries exactly two MAC addresses, the client first and the
    `Via` originator last. Header and legend lines carry no `*` and are skipped,
    the same way `radio_parse.originator_count` skips the algorithm header.
    """
    entries: list[tuple[str, str]] = []
    for line in text.splitlines():
        if not line.strip().startswith("*"):
            continue
        macs = _MAC.findall(line)
        if len(macs) >= 2:
            entries.append((macs[0], macs[-1]))
    return tuple(entries)


@dataclass
class MeshTranslationReadings:
    """`mule.loops.TranslationReadings` read from sysfs and `batctl`.

    `batctl_transglobal` is injected: it runs `batctl meshif <if> transglobal`
    and returns its stdout, or `None` if it could not run. Keeping the command
    out of this module is the same discipline `mule.sysfs` keeps for chronyc.
    """

    batctl_transglobal: Callable[[], str | None]
    root: Path = NET_ROOT

    def own_addresses(self) -> tuple[str, ...] | None:
        """Report every address belonging to this node, or None if unknown.

        `None` where `/sys/class/net` is not present at all: the node cannot say
        what it owns, which is not the same as owning nothing. An interface whose
        address cannot be read is skipped rather than failing the whole reading.
        """
        if not self.root.is_dir():
            return None
        addresses: list[str] = []
        for path in sorted(self.root.glob("*/address")):
            try:
                value = path.read_text(encoding="utf-8").strip()
            except OSError:
                continue
            if value:
                addresses.append(value)
        return tuple(addresses)

    def global_translation_entries(self) -> tuple[tuple[str, str], ...] | None:
        """Report (client, originator) pairs, or None if `batctl` could not run.

        `None` is distinct from an empty tuple: a node without `batctl` is not a
        node whose translation table is empty, and `mule.loops` treats `None` as
        no signal rather than as a healthy table.
        """
        output = self.batctl_transglobal()
        if output is None:
            return None
        return parse_transglobal(output)
