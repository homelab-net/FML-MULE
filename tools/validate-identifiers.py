#!/usr/bin/env python3
"""Fail when committed evidence carries an identifier SECURITY.md prohibits.

`SECURITY.md` forbids publishing what identifiers a deployment's equipment
carries, and `test/bench/capture-telemetry.py` warns that its own output
"contains the node's real MAC and IP addresses and its kernel log; scrub it and
record what was scrubbed before filing it as evidence."

That was a `[review]` rule with nothing behind it. `tools/scrub-telemetry.py`
does the scrubbing; this refuses the commit when somebody forgets to run it,
because `AGENTS.md` is explicit that a rule nothing checks is a suggestion. The
secret scanner in CI does not look for MAC addresses.

It also refuses **position, key material and Meshtastic node identity**, added
2026-10-03 after `meshtastic --info` was run against the lab T1000-E: its output
carried the node's latitude and longitude to five decimals, two secret channel
PSKs, public keys, a channel URL whose fragment serialises every PSK, and 80
third-party node ids. `AGENTS.md` forbids committing a **deployment location**
outright and nothing checked for one, which is the `[review]`-rule-found-broken
case that this file exists to close.

The public default channel PSK is **not** refused: it is base64 of a single byte,
identical on every stock device, and redacting it would hide which channel a run
actually used.

WHY IT DOES NOT FLAG EVERY MAC-SHAPED STRING

Checked against the tree on 2026-10-03: 45 of the MAC-shaped values already
under `docs/evidence/` are **locally administered** -- the random addresses
`mac80211_hwsim`, `veth` and network namespaces generate. They identify no
equipment, and failing on them would mean scrubbing meaningless values across
most of the evidence base, which is how a check gets ignored. Only a
universally administered unicast address names a real part, so only that fails.

The detection lives in `tools/scrub-telemetry.py` and is imported rather than
copied, so the thing that redacts and the thing that refuses can never disagree
about what counts.

Two traps this has already fallen into, both now pinned by tests:

- A truncated **certificate fingerprint** is colon-separated hex too. An earlier
  pattern matched one in `docs/evidence/TBR-TAK-01/` and called it a leaked MAC.
- A **four-part firmware version** is a valid dotted quad. `meshtastic --info`
  reports `"firmwareVersion": "2.7.26.54e0d8d"` and an earlier IPv4 pattern
  redacted it, destroying a value the measurement-record contract requires.
- **IPv6 link-local in EUI-64 form** contains no MAC-shaped text at all, and
  reconstructs the address exactly: `fe80::dea6:32ff:fe12:3456` decodes to
  `dc:a6:32:12:34:56`, a Raspberry Pi OUI. A MAC-only check misses the leak that
  a real capture from an arm64 article would actually produce.
- A **MAC-based interface name** (`wlx` and twelve hex digits) carries the
  address with no colons. Debian names a USB Wi-Fi adapter that way, and the
  AWUS036ACM bench card anticipates it. Added 2026-10-10, after Codex review on
  PR #224 found the scrub-and-commit route would have let one through.

A note for anyone documenting this: `docs/evidence/` is itself scanned, so a
README under it cannot carry a realistic example. Writing the two addresses
above in full tripped this check inside `docs/evidence/README.md` the first time
it ran -- which was a fair result, and the reason the examples there are
truncated. Illustrate the shape; do not carry a whole identifier.

Usage: tools/validate-identifiers.py [repo-root]
Exits non-zero when any identifier is found, after reporting every one.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

#: Directories whose contents are published evidence. A capture living outside
#: these is a working file; one inside them is a commitment.
SCANNED = ("docs/evidence", "test/fixtures", "test/results")

#: Skipped wholesale: archived upstream source carries vendor addresses that are
#: documentation, not this deployment's equipment.
SKIP_SUFFIXES = (".proto", ".cpp", ".c", ".h", ".patch")


def _load_scrubber(root: Path) -> ModuleType:
    """Import the detection from scrub-telemetry.py, which owns it."""
    tool = root / "tools" / "scrub-telemetry.py"
    spec = importlib.util.spec_from_file_location("scrub_telemetry", tool)
    if spec is None or spec.loader is None:  # pragma: no cover - packaging fault
        raise RuntimeError(f"cannot load {tool}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def findings(root: Path) -> list[str]:
    """Return one line per identifier found under the scanned directories."""
    scrub = _load_scrubber(root)
    found: list[str] = []
    for name in SCANNED:
        base = root / name
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*")):
            if not path.is_file() or path.suffix in SKIP_SUFFIXES:
                continue
            try:
                text = path.read_text(errors="ignore")
            except OSError:  # pragma: no cover - unreadable file
                continue
            rel = path.relative_to(root)
            for number, line in enumerate(text.splitlines(), 1):
                for match in scrub._TEXT_FIELD_RE.finditer(line):
                    name = match.group("name")
                    raw = match.group("value")
                    if raw.strip('"') == scrub.PUBLIC_DEFAULT_PSK:
                        continue
                    if "REDACTED" in raw:
                        continue
                    kind = (
                        "position"
                        if name in scrub.POSITION_FIELDS
                        else "key material or device id"
                    )
                    found.append(
                        f"{rel}:{number}: {kind} in field {name!r} "
                        f"-- scrub with tools/scrub-telemetry.py"
                    )
                for match in scrub.NODE_ID_RE.finditer(line):
                    found.append(
                        f"{rel}:{number}: Meshtastic node id {match.group(0)} "
                        f"-- scrub with tools/scrub-telemetry.py"
                    )
                for match in scrub.CHANNEL_URL_RE.finditer(line):
                    if "REDACTED" in match.group(2):
                        continue
                    found.append(
                        f"{rel}:{number}: Meshtastic channel URL fragment "
                        f"(serialises every PSK) "
                        f"-- scrub with tools/scrub-telemetry.py"
                    )
                for match in scrub.MAC_RE.finditer(line):
                    if scrub.is_equipment_mac(match.group(0)):
                        found.append(
                            f"{rel}:{number}: equipment MAC {match.group(0)} "
                            f"-- scrub with tools/scrub-telemetry.py"
                        )
                for match in scrub.MAC_NAME_RE.finditer(line):
                    mac = scrub.mac_name_embedded_mac(match.group("hex"))
                    if scrub.is_equipment_mac(mac):
                        found.append(
                            f"{rel}:{number}: interface name {match.group(0)} "
                            f"carries equipment MAC {mac} "
                            f"-- scrub with tools/scrub-telemetry.py"
                        )
                for match in scrub.EUI64_RE.finditer(line):
                    mac = scrub.eui64_embedded_mac(match.groups())
                    if mac is not None and scrub.is_equipment_mac(mac):
                        found.append(
                            f"{rel}:{number}: IPv6 link-local encoding equipment "
                            f"MAC {mac} -- scrub with tools/scrub-telemetry.py"
                        )
    return found


def main(argv: list[str]) -> int:
    """Scan the repository and report every identifier found."""
    root = Path(argv[0] if argv else ".").resolve()
    found = findings(root)
    for line in found:
        print(f"FAIL: {line}", file=sys.stderr)
    if found:
        print(f"\n{len(found)} identifier(s) in committed evidence.", file=sys.stderr)
        return 1
    print("  no equipment identifiers in committed evidence")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
