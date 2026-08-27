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
REGIONS_DIR = REPO_ROOT / "regions"

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
    """Load a mission configuration package."""
    resolved = Path(path)
    if not resolved.is_file():
        message = f"mission package not found: {resolved}"
        raise MissingParameterError(message)
    with resolved.open(encoding="utf-8") as handle:
        loaded = json.load(handle)
    if not isinstance(loaded, dict):
        message = f"mission package is not a mapping: {resolved}"
        raise MissingParameterError(message)
    return loaded


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


def resolve(region: dict[str, Any], mission: dict[str, Any]) -> dict[str, Any]:
    """Resolve the parameter set, refusing if any required value is TBD.

    Raises UnresolvedValueError naming every gap and its trade, rather than
    substituting a default for any of them.
    """
    for dotted in REGION_IDENTITY:
        value = _get(region, dotted)
        if _is_tbd(value):
            message = (
                f"region profile identity is incomplete: {dotted} is {TBD}. "
                "A profile that cannot name its own regulator cannot be used to "
                "generate configuration."
            )
            raise UnresolvedValueError(message)

    gaps = unresolved(region)
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

    return {
        "region": {
            "id": _get(region, "region.id"),
            "regulator": _get(region, "region.regulator"),
            "status": region.get("region", {}).get("status", "UNVERIFIED"),
        },
        "mission": {
            "id": _get(mission, "mission.id"),
            "example": _get(mission, "mission.example"),
            "profile": _get(mission, "profile"),
        },
        "halow": {
            "channel": _get(region, "halow.default_channel"),
            "max_eirp_dbm": _get(region, "halow.max_eirp_dbm"),
            "band_low_hz": _get(region, "halow.band_low_hz"),
            "band_high_hz": _get(region, "halow.band_high_hz"),
            "duty_cycle_percent": region.get("halow", {}).get("duty_cycle_percent"),
        },
        "lora": {
            "channel": _get(region, "lora.default_channel"),
            "max_eirp_dbm": _get(region, "lora.max_eirp_dbm"),
            "band_low_hz": _get(region, "lora.band_low_hz"),
            "band_high_hz": _get(region, "lora.band_high_hz"),
        },
        "wifi": {
            "mesh_channel": _get(region, "wifi.mesh_channel"),
            "ap_channel": _get(region, "wifi.ap_channel"),
            "max_eirp_dbm": _get(region, "wifi.max_eirp_dbm"),
        },
        "amateur": {
            # Amateur integration is disabled by default in every region.
            # A profile that enables it is rejected by validate().
            "enabled": region.get("amateur", {}).get("enabled", False),
        },
    }


def validate(resolved_params: dict[str, Any], region: dict[str, Any]) -> list[str]:
    """Check every resolved value against the region profile's own limits.

    Returns a list of violations. A generated channel outside the permitted set
    is a regulatory problem, not a bug, so callers raise on a non-empty result.
    """
    errors: list[str] = []

    for bearer in ("halow", "lora"):
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

        eirp = resolved_params[bearer]["max_eirp_dbm"]
        profile_eirp = region.get(bearer, {}).get("max_eirp_dbm")
        both_numeric = isinstance(eirp, (int, float)) and isinstance(
            profile_eirp, (int, float)
        )
        if both_numeric and eirp > profile_eirp:
            errors.append(
                f"{bearer}: resolved EIRP {eirp} dBm exceeds the region limit "
                f"{profile_eirp} dBm"
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
) -> dict[str, Any]:
    """Resolve, validate and optionally write the parameter document."""
    region = load_region(region_ref)
    mission = load_mission(mission_path)
    resolved_params = resolve(region, mission)

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
        "--check",
        action="store_true",
        help="report unresolved parameters and exit; do not treat TBD as an error",
    )
    args = parser.parse_args(argv)

    if args.check:
        try:
            region = load_region(args.region)
        except ConfigError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2
        gaps = unresolved(region)
        if not gaps:
            print(f"{args.region}: all required parameters are resolved.")
            return 0
        print(f"{args.region}: {len(gaps)} required parameter(s) still {TBD}.\n")
        for dotted, trade in gaps:
            print(f"  {dotted:34s} supplied by {trade}")
        print("\nThis is the expected state. No region profile is resolvable yet.")
        return 0

    try:
        params = generate(args.region, args.mission, args.out)
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
