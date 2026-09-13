#!/usr/bin/env python3
"""Validate the GAP-09B development-image build inputs.

Usage:
    tools/validate-image.py [REPOSITORY_ROOT]
"""

from __future__ import annotations

import re
import sys
import uuid
from configparser import ConfigParser
from configparser import Error as ConfigError
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
INPUTS_RELATIVE = Path("os/image/build-inputs.yml")
CONFIG_RELATIVE = Path("os/image/mkosi.conf")
PACKAGE_VERSION = re.compile(r"^[0-9]+(?:\.[0-9]+)+(?:[-+~:.a-zA-Z0-9]+)?$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
GIT_OBJECT = re.compile(r"^[0-9a-f]{40}$")
SELECTED_BUILDER_VERSION = "25.3-7"  # FML-ADR-079
SELECTED_TARGET = {
    "name": "debian",
    "release": "trixie",
    "architecture": "x86-64",
}
SELECTED_OUTPUT = {
    "format": "disk",
    "compress_output": False,
    "image_id": "mule-development",
    "manifest_format": "json",
    "bootable": True,
    "bootloader": "systemd-boot",
}
EXPECTED_CONFIG_KEYS = {
    "Distribution": {
        "Distribution",
        "Release",
        "Architecture",
        "Mirror",
        "LocalMirror",
        "RepositoryKeyCheck",
    },
    "Output": {"Format", "CompressOutput", "ImageId", "ManifestFormat", "Seed"},
    "Content": {"Bootable", "Bootloader", "SourceDateEpoch"},
    "Build": {
        "ToolsTree",
        "ToolsTreeDistribution",
        "ToolsTreeRelease",
        "ToolsTreeMirror",
    },
}


def _read_yaml(path: Path, errors: list[str]) -> dict[str, Any] | None:
    """Read one YAML mapping or append a stable diagnostic."""
    try:
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        errors.append(f"cannot read image inputs: {path}: {exc}")
        return None
    if not isinstance(document, dict):
        errors.append("image build inputs shall be a YAML mapping")
        return None
    return document


def _read_config(path: Path, errors: list[str]) -> ConfigParser | None:
    """Read the mkosi INI file without lower-casing setting names."""
    config = ConfigParser(interpolation=None, strict=True)
    config.optionxform = str  # type: ignore[method-assign]
    try:
        with path.open(encoding="utf-8") as stream:
            config.read_file(stream)
    except (OSError, UnicodeError, ConfigError) as exc:
        errors.append(f"cannot read mkosi configuration: {path}: {exc}")
        return None
    return config


def _mapping(document: dict[str, Any], key: str, errors: list[str]) -> dict[str, Any]:
    """Return a required child mapping or append a diagnostic."""
    value = document.get(key)
    if not isinstance(value, dict):
        errors.append(f"image build inputs {key} shall be a mapping")
        return {}
    return value


def _config_value(
    config: ConfigParser, section: str, key: str, errors: list[str]
) -> str | None:
    """Return one required mkosi value."""
    if not config.has_option(section, key):
        errors.append(f"mkosi [{section}] {key} is required")
        return None
    return config.get(section, key)


def _expect_config(
    config: ConfigParser,
    section: str,
    key: str,
    expected: object,
    errors: list[str],
) -> None:
    """Require a mkosi value to match the governed input."""
    actual = _config_value(config, section, key, errors)
    if isinstance(expected, bool):
        rendered = "yes" if expected else "no"
    else:
        rendered = str(expected)
    if actual is not None and actual != rendered:
        errors.append(
            f"mkosi [{section}] {key} does not match build-inputs.yml: "
            f"expected {rendered}, got {actual}"
        )


def validate_repository(root: Path) -> list[str]:
    """Return all image-input defects under *root*."""
    errors: list[str] = []
    document = _read_yaml(root / INPUTS_RELATIVE, errors)
    config = _read_config(root / CONFIG_RELATIVE, errors)
    if document is None or config is None:
        return errors

    if document.get("schema_version") != "1.0":
        errors.append("image build inputs schema_version shall be 1.0")
    if document.get("governing_decision") != "FML-ADR-079":
        errors.append("image build inputs shall cite FML-ADR-079")

    builder = _mapping(document, "builder", errors)
    distribution = _mapping(document, "distribution", errors)
    output = _mapping(document, "output", errors)
    tools_tree = _mapping(document, "tools_tree", errors)

    for section, expected_keys in EXPECTED_CONFIG_KEYS.items():
        if not config.has_section(section):
            errors.append(f"mkosi [{section}] section is required")
            continue
        for key in sorted(set(config.options(section)) - expected_keys):
            errors.append(f"mkosi [{section}] {key} is not a governed v25.3 setting")

    if builder.get("package") != "mkosi":
        errors.append("builder.package shall be mkosi")
    version = builder.get("version")
    if not isinstance(version, str) or PACKAGE_VERSION.fullmatch(version) is None:
        errors.append("builder.version shall be the exact Debian package version")
    elif version != SELECTED_BUILDER_VERSION:
        errors.append(
            f"builder.version shall be selected version {SELECTED_BUILDER_VERSION}"
        )
    if SHA256.fullmatch(str(builder.get("package_sha256", ""))) is None:
        errors.append("builder.package_sha256 shall be a lowercase SHA-256")
    for key in ("upstream_commit", "upstream_tag_object"):
        if GIT_OBJECT.fullmatch(str(builder.get(key, ""))) is None:
            errors.append(f"builder.{key} shall be a 40-hex Git object")
    source = builder.get("package_source")
    if not isinstance(source, str) or not source.startswith(
        "https://packages.debian.org/"
    ):
        errors.append("builder.package_source shall be the Debian package page")

    snapshot = distribution.get("snapshot")
    mirror = distribution.get("mirror")
    expected_mirror = f"https://snapshot.debian.org/archive/debian/{snapshot}"
    if mirror != expected_mirror:
        errors.append("distribution.mirror shall be derived from the dated snapshot")
    try:
        snapshot_time = datetime.strptime(str(snapshot), "%Y%m%dT%H%M%SZ").replace(
            tzinfo=UTC
        )
    except ValueError:
        errors.append("distribution.snapshot shall be a UTC snapshot timestamp")
    else:
        if distribution.get("source_date_epoch") != int(snapshot_time.timestamp()):
            errors.append(
                "distribution.source_date_epoch shall match the snapshot date"
            )

    for key, expected in SELECTED_TARGET.items():
        if distribution.get(key) != expected:
            errors.append(f"distribution.{key} shall be selected value {expected}")
    for key, expected in SELECTED_OUTPUT.items():
        if output.get(key) != expected:
            errors.append(f"output.{key} shall be selected value {expected}")

    for key, expected in {
        "Distribution": distribution.get("name"),
        "Release": distribution.get("release"),
        "Architecture": distribution.get("architecture"),
        "Mirror": mirror,
        "LocalMirror": mirror,
    }.items():
        _expect_config(config, "Distribution", key, expected, errors)
    key_check = _config_value(config, "Distribution", "RepositoryKeyCheck", errors)
    if key_check is not None and key_check != "yes":
        errors.append("mkosi [Distribution] RepositoryKeyCheck shall be yes")

    for key, expected in {
        "Format": output.get("format"),
        "CompressOutput": output.get("compress_output"),
        "ImageId": output.get("image_id"),
        "ManifestFormat": output.get("manifest_format"),
        "Seed": output.get("seed"),
    }.items():
        _expect_config(config, "Output", key, expected, errors)
    seed_name = output.get("seed_name")
    expected_seed = str(uuid.uuid5(uuid.NAMESPACE_URL, str(seed_name)))
    if output.get("seed") != expected_seed:
        errors.append("output.seed shall be UUIDv5 derived from output.seed_name")
    for key, expected in {
        "Bootable": output.get("bootable"),
        "Bootloader": output.get("bootloader"),
        "SourceDateEpoch": distribution.get("source_date_epoch"),
    }.items():
        _expect_config(config, "Content", key, expected, errors)
    for key, expected in {
        "ToolsTree": tools_tree.get("mode"),
        "ToolsTreeDistribution": tools_tree.get("distribution"),
        "ToolsTreeRelease": tools_tree.get("release"),
        "ToolsTreeMirror": tools_tree.get("mirror"),
    }.items():
        _expect_config(config, "Build", key, expected, errors)
    if tools_tree.get("mirror") != mirror:
        errors.append("tools_tree.mirror shall match the dated distribution mirror")
    if tools_tree.get("mode") != "default":
        errors.append("tools_tree.mode shall enable the default governed tools tree")
    if tools_tree.get("distribution") != distribution.get("name"):
        errors.append("tools_tree.distribution shall match the target distribution")
    if tools_tree.get("release") != distribution.get("release"):
        errors.append("tools_tree.release shall match the target release")

    return errors


def main(argv: list[str]) -> int:
    """Validate one repository path and print stable diagnostics."""
    if len(argv) > 2:
        print("Usage: tools/validate-image.py [REPOSITORY_ROOT]", file=sys.stderr)
        return 2
    root = Path(argv[1]).resolve() if len(argv) == 2 else REPO_ROOT
    errors = validate_repository(root)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("Image build inputs: 0 defects.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
