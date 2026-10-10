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
- **MAC-based interface names** -- `wlx` or `enx` and twelve hex digits, the
  systemd name for an adapter with a fixed address. The address is in the name,
  with no colons, and the name appears as a dictionary key as well as a value.
  Redacted when it decodes to a universally administered MAC.
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

#: An interface name that carries its MAC. systemd.net-naming-scheme(7):
#: "ID_NET_NAME_MAC=prefixxAABBCCDDEEFF ... This name consists of the prefix,
#: letter x, and 12 hexadecimal digits of the MAC address." The two-character
#: prefixes it lists are en, ib, sl, wl, ww and mc. Debian names a USB Wi-Fi
#: adapter this way (`wlx...`), so `iw dev`, link records and any table keyed by
#: interface carry the address with no colons for MAC_RE to find.
MAC_NAME_RE = re.compile(
    r"(?<![0-9A-Za-z])(?P<prefix>en|ib|sl|wl|ww|mc)x(?P<hex>[0-9a-fA-F]{12})"
    r"(?![0-9A-Za-z])"
)

#: A dotted quad that is not part of a longer dotted or alphanumeric run. The
#: trailing letter exclusion is not cosmetic: `meshtastic --info` reports
#: `"firmwareVersion": "2.7.26.54e0d8d"`, whose first four components are a valid
#: dotted quad, and an earlier pattern redacted it as a public address --
#: destroying the firmware version that `docs/evidence/README.md` requires in a
#: measurement record. An address followed immediately by a letter is not an
#: address.
IPV4_RE = re.compile(r"(?<![0-9.A-Za-z])(?:\d{1,3}\.){3}\d{1,3}(?![0-9.A-Za-z])")

#: A Meshtastic node id: "!" and eight hex digits. The 2026-09-27 record scrubbed
#: these by hand ("the Meshtastic node id is scrubbed") while deliberately
#: publishing the RAK's USB board serial as a non-sensitive instrument id.
NODE_ID_RE = re.compile(r"!(?=[0-9a-f]{8}\b)[0-9a-f]{8}", re.IGNORECASE)

#: A Meshtastic channel URL. The fragment is the serialised channel set,
#: including every PSK, so the fragment is the secret and the host is not.
CHANNEL_URL_RE = re.compile(r"(https?://meshtastic\.org/e/#)([A-Za-z0-9_\-=]+)")

#: Fields whose value is a position. `AGENTS.md` forbids committing a
#: **deployment location** outright, and `meshtastic --info` prints latitude and
#: longitude to five decimals. These arrive as JSON *numbers*, which no
#: string-matching pass can see -- the reason this is keyed on the field name.
POSITION_FIELDS = frozenset(
    {"latitude", "longitude", "latitudeI", "longitudeI", "altitude"}
)

#: Fields whose value is key material or a device identifier, redacted by name
#: because their values have no distinguishing shape.
#:
#: `macaddr` is here for a specific reason: a Meshtastic node's address is often
#: **locally administered** (the lab RAK's is `d3:d1:...`), so
#: `is_equipment_mac()` correctly declines to treat it as equipment -- that rule
#: exists so 45 committed hwsim addresses are not scrubbed into noise. But a
#: Meshtastic `macaddr` *is* a real radio's identifier. Field name settles what
#: value shape cannot.
SECRET_FIELDS = frozenset({"psk", "publicKey", "privateKey", "macaddr"})

#: The compiled-in public channel PSK, base64 of the single byte 0x01. It is the
#: same on every stock device in a region -- `AGENTS.md` records that the
#: firmware source "calls the compiled-in key the `public` default channel that
#: every device powers up on" -- so it is a published constant, not a secret, and
#: redacting it would hide which channel a run actually used.
PUBLIC_DEFAULT_PSK = "AQ=="

#: `"field": value` inside a text blob, for either field set. The value may be a
#: quoted string or a bare number, because `latitude` arrives unquoted.
_TEXT_FIELD_RE = re.compile(
    r'"(?P<name>' + "|".join(sorted(POSITION_FIELDS | SECRET_FIELDS)) + r')"'
    r"\s*:\s*(?P<value>\"[^\"]*\"|-?[0-9]+(?:\.[0-9]+)?)"
)


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


def mac_name_embedded_mac(hexdigits: str) -> str:
    """Recover the MAC a MAC-based interface name carries, as colon-hex."""
    return ":".join(hexdigits[i : i + 2] for i in range(0, 12, 2)).lower()


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

        def _mac_name(match: re.Match[str]) -> str:
            mac = mac_name_embedded_mac(match.group("hex"))
            if not is_equipment_mac(mac):
                return match.group(0)
            return self._token("IFNAME", match.group(0))

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

        def _field(match: re.Match[str]) -> str:
            name, raw = match.group("name"), match.group("value")
            if name in POSITION_FIELDS:
                return f'"{name}": "{self._token("POSITION", name + raw)}"'
            if raw.strip('"') == PUBLIC_DEFAULT_PSK:
                return match.group(0)
            return f'"{name}": "{self._token("SECRET", raw)}"'

        value = EUI64_RE.sub(_eui64, value)
        value = MAC_NAME_RE.sub(_mac_name, value)
        value = MAC_RE.sub(_mac, value)
        value = IPV4_RE.sub(_v4, value)
        value = NODE_ID_RE.sub(lambda m: self._token("NODEID", m.group(0)), value)
        value = CHANNEL_URL_RE.sub(
            lambda m: m.group(1) + self._token("SECRET", m.group(2)), value
        )
        # `meshtastic --info` is text with JSON embedded in it, so the field pass
        # in walk() never sees these. Numbers are matched as well as strings:
        # latitude arrives unquoted.
        value = _TEXT_FIELD_RE.sub(_field, value)
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
            out: dict[str, object] = {}
            for key, value in node.items():
                if key in POSITION_FIELDS:
                    out[key] = self._token("POSITION", f"{key}{value}")
                elif key in SECRET_FIELDS and value != PUBLIC_DEFAULT_PSK:
                    out[key] = self._token("SECRET", str(value))
                else:
                    # Keys are scrubbed too: a station dump keyed by interface
                    # name carries a `wlx...` name as a key, not a value.
                    name = self.text(key) if isinstance(key, str) else key
                    out[name] = self.walk(value)
            return out
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
                f"the public default channel PSK {PUBLIC_DEFAULT_PSK!r}, a"
                " published constant every stock device powers up on",
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
