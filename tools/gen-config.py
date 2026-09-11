#!/usr/bin/env python3
"""Resolve node configuration parameters from a region profile and a mission package.

Usage:
    tools/gen-config.py --region <id-or-path> --mission <path> [--out <dir>]
    tools/gen-config.py --region <id-or-path> --mission <path> --check

**Region is a parameter, not a constant.** No file in ``os/config/`` contains a
frequency, channel, bandwidth or transmit power. Those come from
``regions/<region-id>/profile.yml``, and this is the tool that moves them.

What this tool does today, in order:

1. **Resolve.** Collect the parameters each configuration target needs, from the
   region profile and the mission package.
2. **Refuse on TBD.** If a required value is still ``TBD``, generation stops and
   the error names the trade that will supply it. This is the "do not invent
   specifications" rule expressed as code: the failure mode it prevents is a
   plausible default silently becoming a fielded channel.
3. **Validate.** Every resolved value is checked against the region profile's
   own permitted set and limits. A generated channel outside the permitted set
   is a regulatory problem, not a bug.
4. **Emit.** A resolved parameter document that template rendering consumes.

What it deliberately does not do yet: render the ``os/config/*.template`` files.
Those carry no substitution placeholders, because every value they need is
currently ``TBD``. Adding placeholder syntax to templates whose values do not
exist would be adding structure ahead of content. Rendering is the next
increment and consumes this tool's output unchanged.

Status: SIMULATED against the synthetic fixture region in
``test/fixtures/regions/``. No region profile in ``regions/`` is resolvable
today, and that is the correct result.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# Region profiles are YAML. PyYAML is the one third-party import in this file;
# it is packaged by every Debian-family release the userland targets
# (python3-yaml) and is declared in pyproject.toml.
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    # Direct execution starts with tools/ on sys.path. FML-ADR-051 keeps shared
    # runtime decisions in the importable mule/ package.
    sys.path.insert(0, str(REPO_ROOT))

from mule.mission import (  # noqa: E402
    MissionLoadError,
    MissionValidationError,
)
from mule.mission import (  # noqa: E402
    load_mission as load_validated_mission,
)

REGIONS_DIR = REPO_ROOT / "regions"
NODES_DIR = REPO_ROOT / "nodes"

#: Marker for a value the program has not determined. Never a default.
TBD = "TBD"


class ConfigError(Exception):
    """Base for every failure this tool reports."""


class UnresolvedValueError(ConfigError):
    """A required parameter is still TBD, so configuration cannot be generated.

    This is the expected outcome for every region profile in the repository
    today. It is a correct refusal, not a defect.
    """


class RegionViolationError(ConfigError):
    """A resolved value falls outside what the region profile permits.

    A generated channel outside the permitted set is a regulatory problem, not a
    bug, so this is raised rather than warned about.
    """


class MissingParameterError(ConfigError):
    """A required key is absent from the profile or package entirely."""


#: Required parameters per configuration target.
#:
#: Each entry maps a dotted path in the region profile to the trade that will
#: supply it. The trade reference is what makes an UnresolvedValueError useful:
#: it tells the reader who to ask rather than inviting them to guess.
REQUIRED: dict[str, dict[str, str]] = {
    "halow": {
        "halow.permitted": "TBR-RF-02",
        "halow.band_low_hz": "TBR-RF-02",
        "halow.band_high_hz": "TBR-RF-02",
        "halow.default_channel": "TBR-RF-02",
        "halow.max_eirp_dbm": "TBR-RF-02",
    },
    "lora": {
        "lora.permitted": "TBR-RF-02",
        "lora.band_low_hz": "TBR-RF-02",
        "lora.band_high_hz": "TBR-RF-02",
        "lora.default_channel": "TBR-RF-02",
        "lora.max_eirp_dbm": "TBR-RF-02",
    },
    "wifi_mesh": {
        "wifi.mesh_channel": "TBR-RF-01",
        "wifi.max_eirp_dbm": "TBR-RF-01",
    },
    "wifi_ap": {
        "wifi.ap_channel": "TBR-RF-03",
        "wifi.max_eirp_dbm": "TBR-RF-03",
    },
}

#: Region profile keys that must be present for any generation at all.
REGION_IDENTITY: dict[str, str] = {
    "region.id": "n/a",
    "region.regulator": "n/a",
}


def _get(document: dict[str, Any], dotted: str) -> Any:  # noqa: ANN401
    """Return the value at a dotted path, or raise MissingParameterError."""
    node: Any = document
    for part in dotted.split("."):
        if not isinstance(node, dict) or part not in node:
            message = f"key {dotted!r} is absent from the document"
            raise MissingParameterError(message)
        node = node[part]
    return node


def _is_tbd(value: Any) -> bool:  # noqa: ANN401
    """Whether a value is the TBD marker.

    Compared as a string so that a profile written with unquoted TBD, which
    YAML loads as a string anyway, behaves the same as a quoted one.
    """
    return isinstance(value, str) and value.strip() == TBD


def load_region(region: str) -> dict[str, Any]:
    """Load a region profile by identifier or path.

    A bare identifier resolves under ``regions/``. A path is used as given, so
    that a synthetic fixture profile outside ``regions/`` can be loaded for
    testing without ever appearing to be a deployable region.
    """
    candidate = Path(region)
    if candidate.suffix in {".yml", ".yaml"}:
        path = candidate
    else:
        path = REGIONS_DIR / region / "profile.yml"
    if not path.is_file():
        message = f"region profile not found: {path}"
        raise MissingParameterError(message)
    with path.open(encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle)
    if not isinstance(loaded, dict):
        message = f"region profile is not a mapping: {path}"
        raise MissingParameterError(message)
    return loaded


def load_mission(path: str | Path) -> dict[str, Any]:
    """Load a mission package through the canonical runtime schema validator."""
    try:
        return load_validated_mission(path)
    except MissionValidationError as exc:
        raise ConfigError(str(exc)) from exc
    except MissionLoadError as exc:
        raise MissingParameterError(str(exc)) from exc


def load_node(node: str) -> dict[str, Any]:
    """Load a node descriptor by identifier or path.

    Mirrors load_region: a bare identifier resolves under ``nodes/``; a path is
    used as given so a synthetic fixture outside ``nodes/`` can be loaded for
    testing without appearing to be a deployable node.
    """
    candidate = Path(node)
    if candidate.suffix in {".yml", ".yaml"}:
        path = candidate
    else:
        path = NODES_DIR / node / "node.yml"
    if not path.is_file():
        message = f"node descriptor not found: {path}"
        raise MissingParameterError(message)
    with path.open(encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle)
    if not isinstance(loaded, dict):
        message = f"node descriptor is not a mapping: {path}"
        raise MissingParameterError(message)
    return loaded


def active_targets(node: dict[str, Any]) -> list[str]:
    """Return the configuration targets a node fields, from its active bearer set.

    FML-ADR-075. The active bearer set scopes which targets gen-config resolves,
    validates and emits. An active bearer that is not a known target is a hard
    error, not a silent skip: a node asking for configuration of a bearer this
    tool does not understand is a mistake to surface, not to drop.

    Distinct from mule/bearers.py REQUIRED_BEARERS (what the node cannot work
    without). This is what it fields.
    """
    bearers = node.get("active_bearers")
    if not isinstance(bearers, list) or not bearers:
        message = (
            "node descriptor declares no active_bearers. A node must field at "
            "least one bearer for configuration to be generated."
        )
        raise ConfigError(message)
    unknown = [b for b in bearers if b not in REQUIRED]
    if unknown:
        message = (
            f"node declares active bearer(s) with no configuration target: "
            f"{', '.join(str(b) for b in unknown)}. "
            f"Known targets: {', '.join(sorted(REQUIRED))}."
        )
        raise ConfigError(message)
    return list(bearers)


def unresolved(
    region: dict[str, Any],
    targets: list[str] | None = None,
) -> list[tuple[str, str]]:
    """Return required parameters that are still TBD, with the trade for each.

    The list is the useful output, not the boolean: a caller reporting "three
    values are TBD" helps nobody, and "halow.default_channel, TBR-RF-02" tells
    the reader exactly which question is in their way.
    """
    selected = targets if targets is not None else list(REQUIRED)
    gaps: list[tuple[str, str]] = []
    for target in selected:
        for dotted, trade in REQUIRED[target].items():
            try:
                value = _get(region, dotted)
            except MissingParameterError:
                gaps.append((dotted, trade))
                continue
            if _is_tbd(value):
                gaps.append((dotted, trade))
    return gaps


def resolve(
    region: dict[str, Any],
    mission: dict[str, Any],
    active: list[str] | None = None,
) -> dict[str, Any]:
    """Resolve the parameter set, refusing if any required value is TBD.

    Raises UnresolvedValueError naming every gap and its trade, rather than
    substituting a default for any of them.

    ``active`` is the node's active bearer set (FML-ADR-075): resolution
    requires, validates and emits only those targets. ``None`` means every
    target, the whole-catalogue behaviour used when no node scopes the call.
    A TBD on a bearer outside the active set is not a gap, and its parameter
    block is not emitted.
    """
    selected = list(REQUIRED) if active is None else active

    for dotted in REGION_IDENTITY:
        value = _get(region, dotted)
        if _is_tbd(value):
            message = (
                f"region profile identity is incomplete: {dotted} is {TBD}. "
                "A profile that cannot name its own regulator cannot be used to "
                "generate configuration."
            )
            raise UnresolvedValueError(message)

    gaps = unresolved(region, selected)
    if gaps:
        lines = [f"  {dotted}  (supplied by {trade})" for dotted, trade in gaps]
        message = (
            f"{len(gaps)} required parameter(s) are still {TBD} in region "
            f"{_get(region, 'region.id')!r}:\n" + "\n".join(lines) + "\n\n"
            "Configuration is not generated. A plausible default here becomes a "
            "fielded channel, and no value in this repository is invented. "
            "Close the trades above, or generate against a different region."
        )
        raise UnresolvedValueError(message)

    resolved: dict[str, Any] = {
        "region": {
            "id": _get(region, "region.id"),
            "regulator": _get(region, "region.regulator"),
            "status": region.get("region", {}).get("status", "UNVERIFIED"),
        },
        "mission": {
            "id": _get(mission, "mission.id"),
            "example": _get(mission, "mission.example"),
            "profile": _get(mission, "profile"),
            # Which services a node serves is a deployment choice carried by the
            # package, never a list compiled into the node. A package that
            # enables none is a valid package: it describes a node with no
            # mission services, not a node with default ones.
            "services": list(mission.get("services", [])),
        },
        "network": {
            "mesh_id": _get(mission, "network.mesh_id"),
            # Optional in the schema. None means services resolve by bare name;
            # a fixed domain across every deployment makes collision certain,
            # which is why there is no default. See services/ingress/.
            "local_domain": mission.get("network", {}).get("local_domain"),
            # Per-deployment IPv4 mesh prefix (FML-ADR-063). Carried through from
            # the mission package: the schema validates its CIDR form on load, so
            # a present value is well-formed. It was previously dropped here, so a
            # valid prefix never reached the generated configuration (GAP-03).
            "address_prefix": mission.get("network", {}).get("address_prefix"),
            "ap_ssid": mission.get("network", {}).get("ap_ssid"),
        },
        "amateur": {
            # Amateur integration is disabled by default in every region.
            # A profile that enables it is rejected by validate().
            "enabled": region.get("amateur", {}).get("enabled", False),
        },
    }

    # Only the active bearers' parameter blocks are emitted. A bearer the node
    # does not field contributes no block: its values are legitimately TBD and
    # emitting them would put a TBD into a resolved document. FML-ADR-075.
    if "halow" in selected:
        resolved["halow"] = {
            "channel": _get(region, "halow.default_channel"),
            "max_eirp_dbm": _get(region, "halow.max_eirp_dbm"),
            "band_low_hz": _get(region, "halow.band_low_hz"),
            "band_high_hz": _get(region, "halow.band_high_hz"),
            "duty_cycle_percent": region.get("halow", {}).get("duty_cycle_percent"),
        }
    if "lora" in selected:
        resolved["lora"] = {
            "channel": _get(region, "lora.default_channel"),
            "max_eirp_dbm": _get(region, "lora.max_eirp_dbm"),
            "band_low_hz": _get(region, "lora.band_low_hz"),
            "band_high_hz": _get(region, "lora.band_high_hz"),
        }
    wifi: dict[str, Any] = {}
    if "wifi_mesh" in selected:
        wifi["mesh_channel"] = _get(region, "wifi.mesh_channel")
    if "wifi_ap" in selected:
        wifi["ap_channel"] = _get(region, "wifi.ap_channel")
    if "wifi_mesh" in selected or "wifi_ap" in selected:
        wifi["max_eirp_dbm"] = _get(region, "wifi.max_eirp_dbm")
    if wifi:
        resolved["wifi"] = wifi

    return resolved


def validate(resolved_params: dict[str, Any], region: dict[str, Any]) -> list[str]:
    """Check every resolved value against the region profile's own limits.

    Returns a list of violations. A generated channel outside the permitted set
    is a regulatory problem, not a bug, so callers raise on a non-empty result.
    """
    errors: list[str] = []

    for bearer in ("halow", "lora"):
        # Only bearers the node fields were resolved and emitted (FML-ADR-075).
        # A bearer not in the resolved document is one this node does not field,
        # so there is no channel to check against the band.
        if bearer not in resolved_params:
            continue
        permitted = region.get(bearer, {}).get("permitted")
        if permitted is not True:
            errors.append(
                f"{bearer}: region {resolved_params['region']['id']!r} does not "
                f"permit this bearer (permitted={permitted!r}), but a channel "
                "was resolved for it"
            )
            continue
        channel = resolved_params[bearer]["channel"]
        low = resolved_params[bearer]["band_low_hz"]
        high = resolved_params[bearer]["band_high_hz"]
        if not isinstance(channel, (int, float)):
            errors.append(f"{bearer}: channel {channel!r} is not a frequency")
        elif not (low <= channel <= high):
            errors.append(
                f"{bearer}: channel {channel} Hz is outside the permitted band "
                f"{low}-{high} Hz for region "
                f"{resolved_params['region']['id']!r}"
            )

        # The EIRP ceiling must be a number the node can enforce against. It
        # is deliberately NOT compared to the region's own limit: resolution
        # copies that value straight from the profile, so such a comparison
        # can never fail and would read as a regulatory control while being
        # dead code. Enforcing an *effective* EIRP needs a selected radio and
        # antenna to compute conducted power plus gain, which is TBR-RF-01,
        # TBR-RF-02, TBR-RF-03 and TBR-HW-01. Until those close there is no
        # input to check, and a check with no input is not written.
        eirp = resolved_params[bearer]["max_eirp_dbm"]
        if not isinstance(eirp, (int, float)):
            errors.append(
                f"{bearer}: EIRP ceiling {eirp!r} is not a number, so no "
                "transmit limit can be enforced"
            )

    # Amateur integration is disabled by default in every region profile.
    # REGULATORY.md: enabling it requires a licensed control operator, station
    # identification and lawful content handling, none of which a config
    # generator can establish.
    if resolved_params["amateur"]["enabled"]:
        errors.append(
            "amateur: enabled in the region profile. Amateur integration is "
            "disabled by default in every region and is never enabled by a "
            "region profile. See REGULATORY.md and CONOPS section 46."
        )

    return errors


def generate(
    region_ref: str,
    mission_path: str | Path,
    out_dir: Path | None = None,
    node_ref: str | None = None,
) -> dict[str, Any]:
    """Resolve, validate and optionally write the parameter document.

    ``node_ref`` scopes generation to the node's active bearer set
    (FML-ADR-075); ``None`` resolves every target, the whole-catalogue behaviour.
    """
    region = load_region(region_ref)
    mission = load_mission(mission_path)
    active = active_targets(load_node(node_ref)) if node_ref is not None else None
    resolved_params = resolve(region, mission, active)

    violations = validate(resolved_params, region)
    if violations:
        detail = "\n".join(f"  {v}" for v in violations)
        message = "region validation failed:\n" + detail
        raise RegionViolationError(message)

    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        target = out_dir / "parameters.json"
        with target.open("w", encoding="utf-8") as handle:
            json.dump(resolved_params, handle, indent=2, sort_keys=True)
            handle.write("\n")

    return resolved_params


def main(argv: list[str]) -> int:
    """Resolve configuration parameters, or explain why they cannot be."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--region",
        required=True,
        help="region id under regions/, or a path to a profile",
    )
    parser.add_argument(
        "--mission",
        required=True,
        help="path to a mission configuration package",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="directory to write parameters.json into",
    )
    parser.add_argument(
        "--node",
        default=None,
        help=(
            "node id under nodes/, or a path to a node descriptor. Scopes "
            "resolution to the node's active bearers. Omit to resolve every target."
        ),
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="report unresolved parameters and exit; do not treat TBD as an error",
    )
    args = parser.parse_args(argv)

    if args.check:
        try:
            load_mission(args.mission)
            region = load_region(args.region)
            active = (
                active_targets(load_node(args.node)) if args.node is not None else None
            )
        except ConfigError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2
        gaps = unresolved(region, active)
        if not gaps:
            print(f"{args.region}: all required parameters are resolved.")
            return 0
        print(f"{args.region}: {len(gaps)} required parameter(s) still {TBD}.\n")
        for dotted, trade in gaps:
            print(f"  {dotted:34s} supplied by {trade}")
        print("\nThis is the expected state. No region profile is resolvable yet.")
        return 0

    try:
        params = generate(args.region, args.mission, args.out, args.node)
    except UnresolvedValueError as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 3
    except RegionViolationError as exc:
        print(f"REJECTED: {exc}", file=sys.stderr)
        return 4
    except ConfigError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    where = f" -> {args.out / 'parameters.json'}" if args.out else ""
    print(f"Resolved configuration for region {params['region']['id']!r}{where}")
    print(f"  region status: {params['region']['status']}")
    print("  SIMULATED. Not validated on hardware.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
