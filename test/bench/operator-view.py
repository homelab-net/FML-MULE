#!/usr/bin/env python3
"""Bench demonstration of the operator status view, from real readings.

The "is the MULE working?" page. This is the buildable Phase-1 slice of the
Status Aggregator (`FML-ADR-046`,
CONOPS section 67), unblocked when `TBR-TAK-01` closed (`FML-ADR-071`) and
defined the mission-state data model. It reuses the pure reasoning that already
exists -- `mule.status.derive` and `mule.modes.assess` -- and adds only what the
component's README said did not exist: collection from the readers, and a local
transport.

Discipline (from services/status-aggregator/README.md and the 2026-09-14
independent verification):
  * The served schema is exactly `mule.status.NodeStatus`. It invents no state
    vocabulary. `shared_data_authoritative` and `data_stale` are emitted as
    explicit null; they stay null until `TBR-HA-01` (the Service Authority
    Registry) closes.
  * It is a BENCH INCREMENT, not a fielded daemon: no resource commitment
    (`TBR-COMP-01`), no promoted production mesh-links reader (that interface is
    parked on `TBR-RF-01`/`TBR-RF-03`/`TBR-LINUX-01`). The mesh-link counts here
    are a bench readout over `iw`/`batctl`, shown alongside the status, not part
    of the status contract.
  * The per-peer capability tier (`FML-ADR-080`) is the same kind of bench
    readout: derived from the passive signals (the `iw` PHY-rate ceiling and
    batman-adv TQ) by `mule.capability`, shown alongside the status, not part of
    it. Its thresholds are the illustrative `BENCH_POLICY`, not `TBR-RF-01`'s, and
    a tier is a ceiling, never an end-to-end guarantee (item 1.9's probe confirms).
  * Readings that cannot be taken report absence honestly: power has no reader on
    this bench, thermal has no zone map until `TBR-HW-01`, so both say "cannot
    tell", not a made-up value.

Tier: SIMULATED. Run it inside a bench network namespace on the mac80211_hwsim
mesh (see test/bench/operator-view.sh); the numbers are stack behaviour, not RF.
"""

from __future__ import annotations

import argparse
import dataclasses
import http.server
import json
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

from mule import modes, power, status, thermal, timekeeping
from mule.bearers import Bearer
from mule.capability import CapabilityPolicy, capability_tier
from mule.sysfs import SysfsThermalReadings, SysfsTimeReadings, ZoneMap

# radio_parse is the software digital twin's tested iw/batctl parser
# (PR #146). test/ and test/bench/ are not packages, and `test` shadows a
# stdlib package, so add the software digital twin directory to the path
# and import the module directly rather than as test.digital_twin.radio_parse.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "digital_twin"))
import radio_parse

# Interface-type substrings iw reports, mapped to the bearer they carry. This is
# a bench convenience, not the per-board interface map TBR-HW-01 will supply.
_TYPE_TO_BEARER: dict[str, Bearer] = {"mesh point": "wifi_mesh", "AP": "wifi_ap"}

# Illustrative capability thresholds so the bench can name a per-peer tier. These
# are NOT TBR-RF-01's values, which FML-ADR-080 keeps out of the code; a tier
# derived from them is a ceiling, not a guarantee (the paced probe of item 1.9 is
# what would confirm one end to end).
BENCH_POLICY = CapabilityPolicy(
    video_min_mbps=5.0,
    voice_min_mbps=0.5,
    video_min_tq=200,
    voice_min_tq=120,
    unreachable_at_or_below_tq=0,
    video_max_hops=1,
    voice_max_hops=4,
)


def _run(cmd: list[str]) -> str | None:
    """Run a command, returning stdout, or None if it could not run."""
    try:
        # Fixed iw/batctl argv, no shell, no untrusted input: a bench readout.
        out = subprocess.run(cmd, capture_output=True, text=True, check=False)  # noqa: S603
    except OSError:
        return None
    return out.stdout if out.returncode == 0 else None


class _NoBattery:
    """PowerReadings for a bench with no battery: it says so, it does not guess."""

    def pack_present(self) -> bool:
        return False

    def pack_healthy(self) -> bool:
        return False

    def state_of_charge_fraction(self) -> float | None:
        return None

    def pack_temperature_c(self) -> float | None:
        return None


def _peer_capability(
    bearer: Bearer, dump: str | None, orig: str | None
) -> dict[str, dict[str, object]]:
    """Per-peer capability tier for the mesh, with the signals it came from.

    Bench telemetry, `SIMULATED`, and a ceiling not a guarantee (`FML-ADR-080`):
    the active probe of item 1.9 is what would confirm a tier end to end. The
    signals come from the software digital twin's tested parser and the tier from
    `mule.capability`; hops are not in `station dump`/`originators`, so `None` is
    passed and that ceiling is skipped. The signals ride alongside the tier so an
    operator, and this evidence, can see why the tier is what it is.
    """
    bitrates = radio_parse.station_bitrates_mbps(dump) or {}
    tqs = radio_parse.originator_tqs(orig) or {}
    peers: dict[str, dict[str, object]] = {}
    for mac in sorted(set(bitrates) | set(tqs)):
        mbps = bitrates.get(mac)
        tq = tqs.get(mac)
        peers[mac] = {
            "tier": capability_tier(bearer, mbps, tq, None, BENCH_POLICY),
            "mbps": mbps,
            "tq": tq,
        }
    return peers


def _radios() -> tuple[
    list[Bearer] | None, list[Bearer], dict[str, int], dict[str, dict[str, object]]
]:
    """Read bearers present, live links, mesh-link counts, and per-peer tiers.

    `enumerated` is None if `iw` could not run at all -- "cannot tell what is
    present" is not "nothing is". `mesh_counts` and `peer_tiers` are bench
    telemetry, not part of the status. Parsing is the software digital twin's tested
    `radio_parse`, not re-inlined here.
    """
    interfaces = radio_parse.interfaces(_run(["iw", "dev"]))
    if interfaces is None:
        return None, [], {}, {}

    enumerated: list[Bearer] = []
    associated: list[Bearer] = []
    mesh_counts: dict[str, int] = {}
    peer_caps: dict[str, dict[str, object]] = {}
    for iface, iftype in interfaces:
        bearer = _TYPE_TO_BEARER.get(iftype)
        if bearer is None:
            continue
        enumerated.append(bearer)
        dump = _run(["iw", "dev", iface, "station", "dump"])
        peers = radio_parse.station_count(dump) or 0
        if peers > 0:
            associated.append(bearer)
        if bearer == "wifi_mesh":
            orig = _run(["batctl", "meshif", "bat0", "originators"])
            mesh_counts["peers"] = peers
            mesh_counts["originators"] = radio_parse.originator_count(orig) or 0
            peer_caps = _peer_capability(bearer, dump, orig)
    return enumerated, associated, mesh_counts, peer_caps


def observe() -> tuple[status.NodeStatus, dict[str, int], dict[str, dict[str, object]]]:
    """Assemble Observations from the node's real readings and derive the view."""
    enumerated, associated, mesh_counts, peer_caps = _radios()

    # Bench time policy. These are placeholders so the roll-up runs; the real
    # values are TBR-TIME-01 and are not decided here.
    time_policy = timekeeping.TimePolicy(
        image_build_time=datetime(2026, 1, 1, tzinfo=UTC),
        max_plausible_forward=timedelta(days=3650),
        max_system_rtc_skew=timedelta(seconds=60),
    )
    time_assessment = timekeeping.assess(SysfsTimeReadings(), time_policy)
    power_assessment = power.assess(_NoBattery(), None, hosting_shared_services=False)

    mode_assessment = modes.assess(
        modes.ModeInputs(
            environment="LAB",
            enumerated=tuple(enumerated or ()),
            associated=tuple(associated),
            hosting_shared_services=False,
            wan_reachable=None,
            peer_reachable=None,
            power=power_assessment,
            lifecycle="OPERATIONAL",
            emission="NORMAL-EMISSION",
            data_marking="EXERCISE",
        ),
        economy_below_minutes=None,
    )

    observations = status.Observations(
        booted=True,
        config_error=None,
        time=time_assessment,
        enumerated=enumerated,
        associated=associated,
        battery_present=False,
        battery_healthy=False,
        power=power_assessment,
        thermal=thermal.assess(SysfsThermalReadings(ZoneMap()), None),
        hosting_shared_services=False,
        modes=mode_assessment,
        lora_stack_responding=None,
    )
    return status.derive(observations), mesh_counts, peer_caps


def _payload() -> dict[str, object]:
    """Build the served document: NodeStatus plus a freshness timestamp.

    The bench mesh-link counts ride alongside under a clearly separate key so the
    status schema stays exactly NodeStatus (see the module docstring).
    """
    node_status, mesh_counts, peer_caps = observe()
    return {
        # Exactly mule.status.NodeStatus. shared_data_authoritative and
        # data_stale are null until TBR-HA-01 (the Service Authority Registry).
        "status": dataclasses.asdict(node_status),
        "as_of": datetime.now(tz=UTC).isoformat(),
        "_bench_mesh_links": mesh_counts,  # bench telemetry, not the contract
        "_bench_peer_capability": peer_caps,  # bench telemetry, not the contract
    }


def _render(payload: dict[str, object]) -> str:
    """Render a minimal operator page: state, live mesh links, peer tiers."""
    s = payload["status"]
    assert isinstance(s, dict)
    mesh = payload["_bench_mesh_links"]
    assert isinstance(mesh, dict)
    caps = payload["_bench_peer_capability"]
    assert isinstance(caps, dict)
    peer_caps = (
        "; ".join(
            f"{mac} {c['tier']} ({c['mbps']} Mb/s, TQ {c['tq']})"
            for mac, c in caps.items()
        )
        or "(none)"
    )
    lines = [
        "MULE operator view (bench, SIMULATED)",
        f"  state:        {s['state']}",
        f"  operational:  {s['operational']}",
        f"  network:      {'DEGRADED' if s['network_degraded'] else 'ok'}",
        f"  tak:          {'available' if s['tak_available'] else 'no'}",
        f"  fault:        {s['fault'] or 'none'}",
        f"  authoritative:{s['shared_data_authoritative']}  (null until TBR-HA-01)",
        f"  live mesh:    {mesh.get('peers', 0)} peer(s), "
        f"{mesh.get('originators', 0)} originator(s)",
        f"  peer tiers:   {peer_caps}  (ceiling, not a guarantee)",
        f"  as of:        {payload['as_of']}",
    ]
    return "\n".join(lines)


class _Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # http.server's required handler name
        payload = _payload()
        body: bytes
        if self.path.startswith("/status.json"):
            body = json.dumps(payload, indent=2).encode()
            ctype = "application/json"
        else:
            body = (_render(payload) + "\n").encode()
            ctype = "text/plain; charset=utf-8"
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args: object) -> None:
        pass  # quiet


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--once", action="store_true", help="print once and exit")
    parser.add_argument("--json", action="store_true", help="with --once, emit JSON")
    parser.add_argument("--port", type=int, default=8088, help="loopback serve port")
    args = parser.parse_args(argv)

    if args.once:
        payload = _payload()
        print(json.dumps(payload, indent=2) if args.json else _render(payload))
        return 0

    # Loopback only: no remote configuration surface (FML-ADR-049 preference).
    server = http.server.HTTPServer(("127.0.0.1", args.port), _Handler)
    print(f"operator view on http://127.0.0.1:{args.port}/ (/status.json for JSON)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
