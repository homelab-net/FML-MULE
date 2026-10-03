#!/usr/bin/env python3
"""Redact equipment identifiers from a telemetry capture, and say what was removed.

`test/bench/capture-telemetry.py` records node state for the evidence pipeline
and warns that a capture "contains the node's real MAC and IP addresses and its
kernel log; scrub it and record what was scrubbed before filing it as evidence."
Nothing did the scrubbing. This does.

`docs/evidence/README.md`: "Record what you scrubbed. A log with an obvious
redaction is honest; a log silently trimmed is not." So every redaction is
replaced by a visible token and counted in a manifest, rather than deleted.

WHAT IT REDACTS, AND WHY NOT EVERYTHING

`SECURITY.md` prohibits publishing "what identifiers their equipment carries".
The discriminator is whether a value identifies equipment, not whether it looks
like an address:

- **Universally administered unicast MACs** -- the OUI is assigned to a
  manufacturer and the address is burned into a real part. Redacted.
- **Locally administered MACs** -- what `mac80211_hwsim`, `veth` and namespaces
  generate at random. They identify nothing and they are most of what is already
  committed under `docs/evidence/`. Kept, and counted in the manifest so a reader
  can see they were considered rather than missed.
- **IPv6 link-local in EUI-64 form** -- `fe80::` with the `ff:fe` marker encodes
  the MAC with one bit flipped, so it survives any MAC-shaped pattern and
  reconstructs the identifier exactly. Redacted when it decodes to a universally
  administered MAC; kept when it decodes to a virtual one.
- **Hostnames and SSIDs.** Redacted: a deployment's names are exactly what
  `SECURITY.md` says an adversary should not learn.
- **RFC1918 and link-local IPv4** -- bench topology, not equipment identity, and
  redacting it would destroy the readability of every routing table. Kept.
- **Public IPv4** -- can locate a deployment. Redacted.

WHAT IT DOES NOT DO

It does not make a capture safe to publish on its own. It does not read the
kernel log for firmware strings or board revisions, it does not remove timestamps
(`SECURITY.md` also names "when they exercise"), and it cannot know which SSID is
a real deployment's. A human still reads the output before it is filed.

Usage: tools/scrub-telemetry.py CAPTURE.json [-o OUT.json]
Writes the scrubbed document, and a `scrub_manifest` block recording counts.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

#: Six hex octets that are not part of a longer colon-hex run. The negative
#: look-around matters: a truncated certificate fingerprint is also
#: colon-separated hex, and an earlier version of this pattern matched one in
#: docs/evidence/TBR-TAK-01/ and reported it as a leaked MAC.
MAC_RE = re.compile(
    r"(?<![0-9a-fA-F:])([0-9a-fA-F]{2})(?::[0-9a-fA-F]{2}){5}(?![0-9a-fA-F:])"
)

#: fe80:: with the ff:fe EUI-64 marker. Four groups, so the interface id is
#: recoverable and the embedded MAC can be tested for universality.
EUI64_RE = re.compile(
    r"fe80::([0-9a-fA-F]{1,4}):([0-9a-fA-F]{1,4}ff):(fe[0-9a-fA-F]{1,2}):([0-9a-fA-F]{1,4})",
    re.IGNORECASE,
)

IPV4_RE = re.compile(r"(?<![0-9.])(?:\d{1,3}\.){3}\d{1,3}(?![0-9.])")


def is_equipment_mac(mac: str) -> bool:
    """Report whether the address identifies a real part: universal and unicast.

    The all-zero address is excluded, and finding that out is why rehearsals
    happen: `ip -details -json link` reports `00:00:00:00:00:00` for every
    interface with no hardware address, and the bit test alone calls that
    universal and unicast. A real bench capture carried three of them.
    """
    octets = mac.split(":")
    if all(int(o, 16) == 0 for o in octets):
        return False
    first = int(octets[0], 16)
    return not (first & 0x02) and not (first & 0x01)


def eui64_embedded_mac(groups: tuple[str, ...]) -> str | None:
    """Recover the MAC an EUI-64 interface id encodes, or None if malformed."""
    flat = "".join(g.zfill(4) for g in groups)
    if len(flat) != 16 or flat[6:10].lower() != "fffe":
        return None
    octets = [int(flat[i : i + 2], 16) for i in range(0, 16, 2)]
    # Forming an EUI-64 inverts the universal/local bit; invert it back.
    recovered = [octets[0] ^ 0x02, *octets[1:3], *octets[5:]]
    return ":".join(f"{o:02x}" for o in recovered)


def is_private_v4(addr: str) -> bool:
    """Report whether the address is RFC1918, loopback, link-local or multicast."""
    try:
        a, b = (int(p) for p in addr.split(".")[:2])
    except ValueError:
        return True
    if a in (10, 127) or a >= 224:
        return True
    if a == 192 and b == 168:
        return True
    if a == 172 and 16 <= b <= 31:
        return True
    return a == 169 and b == 254


class Scrubber:
    """Replaces identifiers with stable tokens, so correlation survives."""

    def __init__(self, hostname: str = "") -> None:
        """Prepare an empty token table for one capture."""
        self.tokens: dict[str, str] = {}
        self.counts: dict[str, int] = {}
        self.kept_local_macs = 0
        #: Scrubbed by literal substring, because a hostname has no shape to
        #: match on. Short names are refused rather than guessed at: replacing a
        #: two-character hostname would corrupt unrelated text.
        self.hostname = hostname if len(hostname) >= 3 else ""

    def _token(self, kind: str, value: str) -> str:
        key = f"{kind}:{value.lower()}"
        if key not in self.tokens:
            self.counts[kind] = self.counts.get(kind, 0) + 1
            self.tokens[key] = f"<{kind}-{self.counts[kind]:02d}-REDACTED>"
        return self.tokens[key]

    def text(self, value: str) -> str:
        """Scrub one string. Order matters: EUI-64 before the bare MAC pass."""

        def _eui64(match: re.Match[str]) -> str:
            mac = eui64_embedded_mac(match.groups())
            if mac is None or not is_equipment_mac(mac):
                return match.group(0)
            return self._token("LINKLOCAL", match.group(0))

        def _mac(match: re.Match[str]) -> str:
            found = match.group(0)
            if not is_equipment_mac(found):
                self.kept_local_macs += 1
                return found
            return self._token("MAC", found)

        def _v4(match: re.Match[str]) -> str:
            found = match.group(0)
            if is_private_v4(found):
                return found
            return self._token("IPV4", found)

        value = EUI64_RE.sub(_eui64, value)
        value = MAC_RE.sub(_mac, value)
        value = IPV4_RE.sub(_v4, value)
        if self.hostname and self.hostname in value:
            value = value.replace(self.hostname, self._token("NODE", self.hostname))
        return value

    def walk(self, node: object) -> object:
        """Scrub every string in a nested JSON structure."""
        if isinstance(node, str):
            return self.text(node)
        if isinstance(node, list):
            return [self.walk(item) for item in node]
        if isinstance(node, dict):
            return {key: self.walk(value) for key, value in node.items()}
        return node

    def manifest(self) -> dict[str, object]:
        """Report what was redacted, what was kept, and what is not handled."""
        return {
            "tool": "tools/scrub-telemetry.py",
            "redacted": dict(sorted(self.counts.items())),
            "kept_locally_administered_macs": self.kept_local_macs,
            "kept_deliberately": [
                "locally administered MACs (hwsim/veth; identify no equipment)",
                "RFC1918 and link-local IPv4 (bench topology, not identity)",
            ],
            "not_handled": [
                "kernel-log firmware strings and board revisions",
                "timestamps (SECURITY.md also names 'when they exercise')",
                "SSIDs, which this tool cannot distinguish from any other string",
            ],
        }


def scrub_document(document: dict[str, object]) -> dict[str, object]:
    """Scrub a capture and attach the manifest of what was removed."""
    hostname = ""
    manifest = document.get("manifest")
    if isinstance(manifest, dict):
        node = manifest.get("node")
        if isinstance(node, str):
            hostname = node
    scrubber = Scrubber(hostname)
    out = scrubber.walk(document)
    if not isinstance(out, dict):  # pragma: no cover - capture is an object
        raise TypeError("telemetry capture must be a JSON object")
    out["scrub_manifest"] = scrubber.manifest()
    return out


def main(argv: list[str]) -> int:
    """Scrub the named capture and write it out."""
    parser = argparse.ArgumentParser(description="Redact identifiers from a capture.")
    parser.add_argument("capture", type=Path, help="capture-telemetry.py JSON")
    parser.add_argument("-o", "--out", type=Path, help="write here instead of stdout")
    args = parser.parse_args(argv)

    document = json.loads(args.capture.read_text(encoding="utf-8"))
    scrubbed = json.dumps(scrub_document(document), indent=2)
    if args.out is not None:
        args.out.write_text(scrubbed + "\n", encoding="utf-8")
        print(f"scrubbed capture written to {args.out}")
    else:
        print(scrubbed)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
