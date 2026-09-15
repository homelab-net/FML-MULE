#!/usr/bin/env python3
"""Capture a machine-readable snapshot of node state for the evidence pipeline.

The first instrumentation task under `AGENTS.md`'s "evidence over architecture"
objective. A hardware test is only as useful as what it lets you reconstruct
afterwards: `docs/ROADMAP-DEV.md` M-ladder and the review behind it call for
capturing, on every run, enough state to tell whether a failure was RF, driver,
kernel, routing, power, thermal, configuration, or application. This does that,
as one JSON document.

Honest about absence. A command that is not installed, or a `sysfs` node that a
board does not expose, is recorded as absent with a reason -- not omitted, and
not guessed. On this development box `rfkill` and `/sys/class/power_supply` are
absent; the capture says so rather than pretending. That is the same discipline
`mule/` readings follow (`None` is a real answer).

Not a measurement of anything physical by itself: it records STATE, plus system
metrics. Throughput, latency and loss are a test's own outputs and belong beside
this. The `manifest` block is the evidence recording metadata
(`docs/evidence/README.md`): captured-at, node, kernel, image build if known.

Usage: sudo test/bench/capture-telemetry.py [--label TEXT] [--out FILE]
Root is needed for a full `dmesg`; without it that probe records its failure.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import socket
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

#: State probes: name -> argv. Fixed argv, no shell. Their raw stdout is kept
#: verbatim (evidence rule: commit raw output); JSON-emitting ones are parsed by
#: a consumer. `iw`/`batctl` output is not ABI-stable, which is why the raw text
#: is kept rather than a lossy parse.
COMMAND_PROBES: dict[str, list[str]] = {
    "radio_enumeration": ["iw", "dev"],
    "interfaces": ["ip", "-details", "-json", "link"],
    "addresses": ["ip", "-json", "addr"],
    "routes": ["ip", "-json", "route"],
    "batman_originators": ["batctl", "o"],
    "batman_neighbors": ["batctl", "n"],
    "rfkill": ["rfkill", "--json"],
    "services_podman": ["podman", "ps", "--all", "--format", "json"],
}

#: dmesg can be enormous; keep the tail, where a driver reset or firmware error
#: shows up. Captured separately so the line cap does not touch other probes.
KERNEL_LOG_LINES = 300


def _run(argv: list[str]) -> dict[str, object]:
    """Run one probe, capturing outcome and raw output, never raising."""
    if shutil.which(argv[0]) is None:
        return {"present": False, "reason": f"{argv[0]} not installed"}
    try:
        result = subprocess.run(  # noqa: S603 (fixed argv, no shell, a bench probe)
            argv, capture_output=True, text=True, timeout=30, check=False
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"present": True, "ran": False, "error": str(exc)}
    entry: dict[str, object] = {
        "present": True,
        "ran": True,
        "returncode": result.returncode,
        "stdout": result.stdout,
    }
    if result.returncode != 0:
        entry["stderr"] = result.stderr
    return entry


def _kernel_log() -> dict[str, object]:
    """Return the tail of dmesg, or its failure. Root is needed for the full log."""
    entry = _run(["dmesg", "--ctime"])
    stdout = entry.get("stdout")
    if isinstance(stdout, str):
        lines = stdout.splitlines()
        entry["stdout"] = "\n".join(lines[-KERNEL_LOG_LINES:])
        entry["lines_kept"] = min(len(lines), KERNEL_LOG_LINES)
    return entry


def _stations() -> dict[str, object]:
    """Per-interface `iw station dump` (signal, so a mesh/AP fault is visible).

    Best effort: enumerate interfaces from `iw dev`, dump each. Absent if `iw`
    is not installed, empty if there are no wireless interfaces -- both real.
    """
    if shutil.which("iw") is None:
        return {"present": False, "reason": "iw not installed"}
    listing = _run(["iw", "dev"])
    names = []
    stdout = listing.get("stdout")
    if isinstance(stdout, str):
        names = [
            line.split()[1]
            for line in stdout.splitlines()
            if line.strip().startswith("Interface ")
        ]
    dumps = {n: _run(["iw", "dev", n, "station", "dump"]) for n in names}
    return {"present": True, "dumps": dumps}


def _read(path: Path) -> str | None:
    """Read a sysfs/procfs file, or None if it cannot be read."""
    try:
        return path.read_text(encoding="utf-8").strip()
    except OSError:
        return None


def _thermal(root: Path = Path("/sys/class/thermal")) -> list[dict[str, object]]:
    """Every thermal zone's type and raw temperature (millidegrees C, the ABI)."""
    zones = []
    for zone in sorted(root.glob("thermal_zone*")):
        zones.append(
            {
                "zone": zone.name,
                "type": _read(zone / "type"),
                "temp_millidegrees_c": _read(zone / "temp"),
            }
        )
    return zones


def _power_supply(
    root: Path = Path("/sys/class/power_supply"),
) -> list[dict[str, object]]:
    """Every power supply's key readings, or [] where the board exposes none."""
    supplies = []
    for supply in sorted(root.glob("*")):
        supplies.append(
            {
                "supply": supply.name,
                "type": _read(supply / "type"),
                "voltage_now_uv": _read(supply / "voltage_now"),
                "current_now_ua": _read(supply / "current_now"),
                "capacity_percent": _read(supply / "capacity"),
            }
        )
    return supplies


def _manifest(label: str | None) -> dict[str, object]:
    """Return the recording metadata docs/evidence/README.md wants beside data."""
    return {
        "captured_at": datetime.now(tz=UTC).isoformat(),
        "node": socket.gethostname(),
        "kernel": platform.release(),
        "machine": platform.machine(),
        "image_build": os.environ.get("FML_IMAGE_BUILD", "unknown"),
        "label": label,
        "tier": "SIMULATED-or-HARDWARE: set by where this was run; hwsim is not RF",
        "root": os.geteuid() == 0,
    }


def capture(label: str | None) -> dict[str, object]:
    """Assemble the full telemetry document."""
    return {
        "manifest": _manifest(label),
        "system": {
            "loadavg": _read(Path("/proc/loadavg")),
            "uptime": _read(Path("/proc/uptime")),
            "meminfo": _read(Path("/proc/meminfo")),
        },
        "kernel_log": _kernel_log(),
        "commands": {name: _run(argv) for name, argv in COMMAND_PROBES.items()},
        "stations": _stations(),
        "thermal": _thermal(),
        "power_supply": _power_supply(),
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--label", help="a note for this capture, e.g. the test")
    parser.add_argument("--out", type=Path, help="write here instead of stdout")
    args = parser.parse_args(argv)

    document = json.dumps(capture(args.label), indent=2)
    if args.out is not None:
        args.out.write_text(document + "\n", encoding="utf-8")
        print(f"telemetry written to {args.out}")
    else:
        print(document)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
