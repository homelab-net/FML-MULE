#!/usr/bin/env python3
"""Validate the GAP-09B development-image build inputs.

Usage:
    tools/validate-image.py [REPOSITORY_ROOT]

Validates the x86-64 base image and the FML-ADR-088 pi4b-arm64 profile.
"""

from __future__ import annotations

import json
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
SELECTED_SBOM_VERSION = "0.10.1-1~bpo13+1"  # FML-ADR-081
SELECTED_CYCLONEDX_RUNTIME_VERSION = "9.1.0-2"  # FML-ADR-081
SELECTED_SNAPSHOT = "20260912T000000Z"  # FML-ADR-079 and FML-ADR-081
APPROVED_DIRECT_PACKAGES = {
    "dbus",
    "initramfs-tools",
    "linux-image-amd64",
    "python3",
    "python3-jsonschema",
    "python3-yaml",
    "systemd",
    "systemd-boot",
    "systemd-boot-efi",
    "systemd-sysv",
    "udev",
}
LOCK_FIELDS = {
    "name",
    "version",
    "architecture",
    "source",
    "suite",
    "filename",
    "sha256",
}
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
        "RepositoryKeyCheck",
    },
    "Output": {"Format", "CompressOutput", "ImageId", "ManifestFormat", "Seed"},
    "Content": {
        "Bootable",
        "Bootloader",
        "CleanPackageMetadata",
        "KernelCommandLine",
        "SourceDateEpoch",
        "WithDocs",
        "WithRecommends",
    },
    "Build": {
        "Environment",
        "SandboxTrees",
        "ToolsTree",
        "ToolsTreeDistribution",
        "ToolsTreeRelease",
        "ToolsTreeMirror",
        "ToolsTreePackages",
        "ToolsTreeSandboxTrees",
    },
    "Runtime": {"Console", "RuntimeNetwork", "VirtualMachineMonitor"},
}

DIRECT_RELATIVE = Path("os/image/manifest/direct-packages.list")
PACKAGES_RELATIVE = Path("os/image/manifest/packages.list")
TARGET_LOCK_RELATIVE = Path("os/image/manifest/target-lock.json")
TOOLS_LOCK_RELATIVE = Path("os/image/manifest/tools-tree-lock.json")
TOOLS_PACKAGES_RELATIVE = Path("os/image/manifest/tools-tree-packages.list")
TARGET_SOURCES_RELATIVE = Path(
    "os/image/sandbox-target/etc/apt/sources.list.d/mkosi.sources"
)
TOOLS_SOURCES_RELATIVE = Path(
    "os/image/sandbox-tools/etc/apt/sources.list.d/mkosi.sources"
)

PROFILE = "pi4b-arm64"  # FML-ADR-088
PROFILE_RELATIVE = Path("os/image/mkosi.profiles") / PROFILE
PROFILE_MANIFEST_RELATIVE = Path("os/image/manifest") / PROFILE
PROFILE_SOURCES_RELATIVE = (
    PROFILE_RELATIVE / "sandbox-target/etc/apt/sources.list.d/mkosi.sources"
)
PROFILE_APT_CONF_RELATIVE = (
    PROFILE_RELATIVE / "sandbox-target/etc/apt/apt.conf.d/50-keep-tools-tree-lists"
)
# Without it the arm64 sync erases the amd64 tools tree's package lists and the
# cache-only build cannot rebuild the tools tree; the file says why.
KEEP_TOOLS_TREE_LISTS = 'APT::Get::List-Cleanup "false";'
# FML-ADR-088: the x86-64 set without the UEFI loader, with Debian's arm64
# kernel and the Pi firmware package.
APPROVED_PROFILE_DIRECT_PACKAGES = (
    APPROVED_DIRECT_PACKAGES - {"linux-image-amd64", "systemd-boot", "systemd-boot-efi"}
) | {"linux-image-arm64", "raspi-firmware"}


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


def _active_lines(path: Path, errors: list[str]) -> list[str]:
    """Return uncommented non-empty lines from one governed text input."""
    try:
        return [
            value
            for line in path.read_text(encoding="utf-8").splitlines()
            if (value := line.split("#", maxsplit=1)[0].strip())
        ]
    except (OSError, UnicodeError) as exc:
        errors.append(f"cannot read image input: {path}: {exc}")
        return []


def _deb822_sources(path: Path, role: str, errors: list[str]) -> list[dict[str, str]]:
    """Parse simple Deb822 source stanzas and reject ambiguous syntax."""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as exc:
        errors.append(f"cannot read {role} snapshot sources: {path}: {exc}")
        return []
    stanzas: list[dict[str, str]] = []
    stanza: dict[str, str] = {}
    for line_number, raw_line in enumerate([*lines, ""], start=1):
        line = raw_line.strip()
        if not line:
            if stanza:
                stanzas.append(stanza)
                stanza = {}
            continue
        if line.startswith("#"):
            continue
        if raw_line[:1].isspace() or ":" not in raw_line:
            errors.append(
                f"{role} snapshot sources line {line_number} has unsupported syntax"
            )
            continue
        key, value = raw_line.split(":", maxsplit=1)
        key = key.strip()
        value = value.strip()
        if not key or not value or key in stanza:
            errors.append(
                f"{role} snapshot sources line {line_number} has an invalid field"
            )
            continue
        stanza[key] = value
    return stanzas


def _read_lock(
    path: Path, role: str, errors: list[str], architecture: str = "amd64"
) -> list[dict[str, str]]:
    """Validate one generated package lock and return its package records."""
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        errors.append(f"cannot read {role} lock: {path}: {exc}")
        return []
    if not isinstance(document, dict):
        errors.append(f"{role} lock shall be a JSON object")
        return []
    for key, expected in {
        "schema_version": "1.0",
        "governing_decision": "FML-ADR-081",
        "snapshot": SELECTED_SNAPSHOT,
        "role": role,
    }.items():
        if document.get(key) != expected:
            errors.append(f"{role} lock {key} shall be {expected}")
    packages = document.get("packages")
    if not isinstance(packages, list) or not packages:
        errors.append(f"{role} lock packages shall be a non-empty list")
        return []
    validated: list[dict[str, str]] = []
    names: list[str] = []
    for index, package in enumerate(packages):
        if not isinstance(package, dict) or set(package) != LOCK_FIELDS:
            errors.append(f"{role} lock package {index} has incomplete provenance")
            continue
        rendered = {key: str(value) for key, value in package.items()}
        names.append(rendered["name"])
        if rendered["architecture"] not in {architecture, "all"}:
            errors.append(
                f"{role} lock package architecture shall be {architecture} or all"
            )
        if rendered["suite"] not in {
            "trixie",
            "trixie-security",
            "trixie-backports",
        }:
            errors.append(
                f"{role} lock package suite is not an approved snapshot suite"
            )
        if not rendered["filename"].startswith("pool/"):
            errors.append(f"{role} lock package filename shall be a Debian pool path")
        if SHA256.fullmatch(rendered["sha256"]) is None:
            errors.append(f"{role} lock package SHA-256 shall be 64 lowercase hex")
        if not all(rendered[key] for key in ("name", "version", "source")):
            errors.append(f"{role} lock package identity fields shall not be empty")
        validated.append(rendered)
    if names != sorted(names) or len(names) != len(set(names)):
        errors.append(f"{role} lock packages shall be unique and sorted by name")
    return validated


def _snapshot_stanzas(components: str) -> list[dict[str, str]]:
    """Return the signed trixie and security snapshot stanzas."""
    common = {
        "Enabled": "yes",
        "Types": "deb",
        "Components": components,
        "Signed-By": "/usr/share/keyrings/debian-archive-keyring.gpg",
        "Check-Valid-Until": "no",
    }
    return [
        common
        | {
            "URIs": f"https://snapshot.debian.org/archive/debian/{SELECTED_SNAPSHOT}",
            "Suites": "trixie",
        },
        common
        | {
            "URIs": (
                "https://snapshot.debian.org/archive/debian-security/"
                f"{SELECTED_SNAPSHOT}"
            ),
            "Suites": "trixie-security",
        },
    ]


def _validate_sources(root: Path, errors: list[str]) -> None:
    """Require role-scoped, same-time Debian snapshot sources."""
    target_expected = _snapshot_stanzas("main")
    tools_expected = [
        *target_expected,
        target_expected[0] | {"Suites": "trixie-backports"},
    ]
    for role, relative in (
        ("target", TARGET_SOURCES_RELATIVE),
        ("tools-tree", TOOLS_SOURCES_RELATIVE),
        (f"{PROFILE} target", PROFILE_SOURCES_RELATIVE),
    ):
        governed = root / relative
        source_parts = governed.parent
        legacy = source_parts.parent / "sources.list"
        if legacy.exists() or legacy.is_symlink():
            errors.append(f"{role} sandbox shall not contain legacy sources.list")
        try:
            entries = {entry.name for entry in source_parts.iterdir()}
        except OSError as exc:
            errors.append(f"cannot inventory {role} snapshot sources: {exc}")
            entries = set()
        if entries != {governed.name}:
            errors.append(f"{role} sources.list.d shall contain only {governed.name}")
        if governed.is_symlink():
            errors.append(f"{role} governed snapshot source shall not be a symlink")
    target = _deb822_sources(root / TARGET_SOURCES_RELATIVE, "target", errors)
    tools = _deb822_sources(root / TOOLS_SOURCES_RELATIVE, "tools-tree", errors)
    if target != target_expected:
        errors.append(
            "target snapshot sources shall be exactly signed trixie and security"
        )
    if tools != tools_expected:
        errors.append(
            "tools-tree snapshot sources shall be exactly signed trixie, security, "
            "and builder-only backports"
        )
    # FML-ADR-088: "The target repositories shall enable the non-free-firmware
    # component, because raspi-firmware lives there."
    profile = _deb822_sources(
        root / PROFILE_SOURCES_RELATIVE, f"{PROFILE} target", errors
    )
    if profile != _snapshot_stanzas("main non-free-firmware"):
        errors.append(
            f"{PROFILE} target snapshot sources shall be exactly signed trixie and "
            "security with main and non-free-firmware"
        )


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


def _assignments(path: Path, errors: list[str]) -> list[tuple[str, str, str]]:
    """Return every mkosi assignment in order, repeats included.

    ConfigParser keeps only the last of repeated keys, and a profile's list
    settings depend on the empty assignment that precedes the value.
    """
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as exc:
        errors.append(f"cannot read mkosi configuration: {path}: {exc}")
        return []
    section = ""
    found: list[tuple[str, str, str]] = []
    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1]
        elif "=" in line and section:
            key, value = line.split("=", maxsplit=1)
            found.append((section, key.strip(), value.strip()))
        else:
            errors.append(f"mkosi configuration has unsupported syntax: {path}")
    return found


def _validate_profile(root: Path, errors: list[str]) -> None:
    """Validate the FML-ADR-088 pi4b-arm64 profile inputs."""
    document = _read_yaml(root / PROFILE_RELATIVE / "build-inputs.yml", errors)
    if document is None:
        return
    prefix = f"{PROFILE} build inputs"
    for key, expected in {
        "schema_version": "1.0",
        "governing_decision": "FML-ADR-088",
        "profile": PROFILE,
    }.items():
        if document.get(key) != expected:
            errors.append(f"{prefix} {key} shall be {expected}")
    if document.get("distribution") != {
        "architecture": "arm64",
        "debian_architecture": "arm64",
        "components": ["main", "non-free-firmware"],
    }:
        errors.append(f"{prefix} distribution shall be arm64 with non-free-firmware")
    if document.get("package_policy") != {
        "direct_intent": str(PROFILE_MANIFEST_RELATIVE / "direct-packages.list"),
        "target_lock": str(PROFILE_MANIFEST_RELATIVE / "target-lock.json"),
        "tools_tree_lock": str(TOOLS_LOCK_RELATIVE),
    }:
        errors.append(f"{prefix} package_policy shall name the profile manifest")
    output = document.get("output")
    output = output if isinstance(output, dict) else {}
    seed = output.get("seed")
    if seed != str(uuid.uuid5(uuid.NAMESPACE_URL, str(output.get("seed_name")))):
        errors.append(f"{prefix} output.seed shall be UUIDv5 of output.seed_name")
    if output.get("image_id") in {None, SELECTED_OUTPUT["image_id"]}:
        errors.append(f"{prefix} output.image_id shall differ from the base image")
    # FML-ADR-088: "No UEFI bootloader shall be installed: Bootable=no."
    if output.get("bootable") is not False or output.get("bootloader") != "none":
        errors.append(f"{prefix} output shall be Bootable=no with no bootloader")
    acceptance = document.get("acceptance")
    if acceptance != {"qemu_boot_is_acceptance": False}:
        errors.append(f"{prefix} shall not accept a QEMU boot as acceptance")
    firmware = document.get("firmware")
    firmware = firmware if isinstance(firmware, dict) else {}

    expected_assignments = [
        ("Distribution", "Architecture", "arm64"),
        ("Output", "ImageId", str(output.get("image_id"))),
        ("Output", "Seed", str(seed)),
        ("Content", "Bootable", "no"),
        ("Content", "Bootloader", "none"),
        ("Content", "KernelCommandLine", ""),
        ("Build", "Environment", ""),
        (
            "Build",
            "Environment",
            f'SYSTEMD_REPART_MKFS_OPTIONS_EXT4="-E hash_seed={seed}"',
        ),
        ("Build", "SandboxTrees", ""),
        ("Build", "SandboxTrees", "sandbox-target"),
    ]
    if _assignments(root / PROFILE_RELATIVE / "mkosi.conf", errors) != (
        expected_assignments
    ):
        errors.append(
            f"{PROFILE} mkosi.conf shall assign exactly the governed profile "
            "settings, emptying each list setting before setting it"
        )

    # The root label is written in two places the build cannot cross-check:
    # the partition definition and the cmdline.txt root= the firmware hook
    # writes from /etc/default/raspi-firmware.
    label = firmware.get("root_label")
    repart_dir = root / PROFILE_RELATIVE / "mkosi.repart"
    repart = _active_lines(repart_dir / "10-root.conf", errors)
    if f"Label={label}" not in repart:
        errors.append(f"{PROFILE} root partition shall carry label {label}")
    elif repart != [
        "[Partition]",
        "Type=root",
        "Format=ext4",
        f"Label={label}",
        "CopyFiles=/",
        "Minimize=guess",
    ]:
        errors.append(f"{PROFILE} root partition shall be the governed ext4 root")
    # finalize checks /boot/firmware in the build root, not the GPT, and the
    # profile is never booted in CI, so nothing else notices a missing or
    # altered FAT partition: the image would build, compare and not boot.
    if _active_lines(repart_dir / "00-firmware.conf", errors) != [
        "[Partition]",
        "Type=esp",
        "Format=vfat",
        "CopyFiles=/boot/firmware:/",
        "SizeMinBytes=512M",
        "SizeMaxBytes=512M",
    ]:
        errors.append(
            f"{PROFILE} firmware partition shall be the governed 512M FAT "
            "partition holding /boot/firmware"
        )
    try:
        repart_entries = {entry.name for entry in repart_dir.iterdir()}
    except OSError:
        repart_entries = set()
    if repart_entries != {"00-firmware.conf", "10-root.conf", "README.md"}:
        errors.append(
            f"{PROFILE} mkosi.repart shall hold only the firmware and root partitions"
        )
    postinst = _active_lines(root / PROFILE_RELATIVE / "mkosi.postinst.chroot", errors)
    for line in (
        f"ROOTPART=LABEL={label}",
        f'CONSOLES="{firmware.get("consoles")}"',
        f"CMA={firmware.get('cma')}",
    ):
        if line not in postinst:
            errors.append(f"{PROFILE} firmware configuration shall write {line}")

    apt_conf = root / PROFILE_APT_CONF_RELATIVE
    try:
        conf_entries = {entry.name for entry in apt_conf.parent.iterdir()}
        conf_lines = [
            line.strip()
            for line in apt_conf.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.strip().startswith("//")
        ]
    except OSError:
        conf_entries, conf_lines = set(), []
    if conf_entries != {apt_conf.name} or conf_lines != [KEEP_TOOLS_TREE_LISTS]:
        errors.append(
            f"{PROFILE} sandbox apt.conf.d shall hold only {apt_conf.name}, "
            f"setting {KEEP_TOOLS_TREE_LISTS}"
        )

    direct = set(
        _active_lines(root / PROFILE_MANIFEST_RELATIVE / "direct-packages.list", errors)
    )
    if direct != APPROVED_PROFILE_DIRECT_PACKAGES:
        errors.append(
            f"{PROFILE} direct target packages shall match the owner-approved set"
        )
    packages = _read_lock(
        root / PROFILE_MANIFEST_RELATIVE / "target-lock.json",
        "target",
        errors,
        architecture="arm64",
    )
    names = {package["name"] for package in packages}
    if not APPROVED_PROFILE_DIRECT_PACKAGES.issubset(names):
        errors.append(f"{PROFILE} target lock shall contain every direct package")
    for prohibited in ("apt", "debsbom", "systemd-boot"):
        if prohibited in names:
            errors.append(f"{PROFILE} target lock prohibits {prohibited}")
    if any(package["suite"] == "trixie-backports" for package in packages):
        errors.append(f"{PROFILE} target lock prohibits trixie-backports")
    lines = _active_lines(root / PROFILE_MANIFEST_RELATIVE / "packages.list", errors)
    if lines != [f"{package['name']}={package['version']}" for package in packages]:
        errors.append(
            f"{PROFILE} packages.list shall be generated exactly from its lock"
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
    if document.get("package_decision") != "FML-ADR-081":
        errors.append("image package inputs shall cite FML-ADR-081")

    builder = _mapping(document, "builder", errors)
    distribution = _mapping(document, "distribution", errors)
    output = _mapping(document, "output", errors)
    tools_tree = _mapping(document, "tools_tree", errors)
    package_policy = _mapping(document, "package_policy", errors)
    mule_runtime = _mapping(document, "mule_runtime", errors)
    sbom = _mapping(document, "sbom", errors)
    runtime = _mapping(document, "runtime_verification", errors)

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
    if distribution.get("security_mirror") != (
        f"https://snapshot.debian.org/archive/debian-security/{snapshot}"
    ):
        errors.append(
            "distribution.security_mirror shall use the dated security snapshot"
        )
    if distribution.get("suites") != ["trixie", "trixie-security"]:
        errors.append("distribution.suites shall contain trixie and trixie-security")
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
        "WithRecommends": False,
        "WithDocs": True,
        "CleanPackageMetadata": False,
        "KernelCommandLine": (
            "console=ttyS0 systemd.unit=multi-user.target systemd.show_status=yes "
            "systemd.firstboot=no"
        ),
        "SourceDateEpoch": distribution.get("source_date_epoch"),
    }.items():
        _expect_config(config, "Content", key, expected, errors)
    for key, expected in {
        "Environment": (
            f'SYSTEMD_REPART_MKFS_OPTIONS_EXT4="-E hash_seed={output.get("seed")}"'
        ),
        "ToolsTree": tools_tree.get("mode"),
        "ToolsTreeDistribution": tools_tree.get("distribution"),
        "ToolsTreeRelease": tools_tree.get("release"),
        "ToolsTreeMirror": tools_tree.get("mirror"),
        "SandboxTrees": "sandbox-target",
        "ToolsTreeSandboxTrees": "sandbox-tools",
        "ToolsTreePackages": f"debsbom={SELECTED_SBOM_VERSION}",
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

    if tools_tree.get("suites") != [
        "trixie",
        "trixie-security",
        "trixie-backports",
    ]:
        errors.append("tools_tree.suites shall add only trixie-backports")
    if (
        tools_tree.get("sbom_package") != "debsbom"
        or tools_tree.get("sbom_package_version") != SELECTED_SBOM_VERSION
    ):
        errors.append("tools_tree shall pin the selected debsbom package")
    if package_policy != {
        "direct_intent": "os/image/manifest/direct-packages.list",
        "target_lock": "os/image/manifest/target-lock.json",
        "tools_tree_lock": "os/image/manifest/tools-tree-lock.json",
        "remove_after_install": ["apt"],
        "with_recommends": False,
        "retain_copyright": True,
    }:
        errors.append("package_policy shall match the FML-ADR-081 target boundary")
    if mule_runtime != {
        "governing_decision": "FML-ADR-083",
        "distribution": "fml-mule",
        "distribution_version": "0.0.1",
        "entry_point": "python3 -m mule",
        "unit": "mule-runtime.service",
    }:
        errors.append("mule_runtime shall bind FML-ADR-083 version and entry point")
    if sbom != {
        "generator": "debsbom",
        "format": "cyclonedx-json",
        "schema_version": "1.6",
        "source": "built-root",
        "include_declared_licenses": True,
        "license_exceptions": "required",
    }:
        errors.append("sbom policy shall match the FML-ADR-081 selection")
    if runtime != {
        "monitor": "qemu",
        "console": "native",
        "console_input": "none",
        "network": "none",
        "systemd_target": "multi-user.target",
    }:
        errors.append("runtime verification shall use QEMU without networking or input")
    for key, expected in {
        "VirtualMachineMonitor": runtime.get("monitor"),
        "Console": runtime.get("console"),
        "RuntimeNetwork": runtime.get("network"),
    }.items():
        _expect_config(config, "Runtime", key, expected, errors)

    direct = set(_active_lines(root / DIRECT_RELATIVE, errors))
    if direct != APPROVED_DIRECT_PACKAGES:
        errors.append("direct target packages shall match the owner-approved set")
    _validate_sources(root, errors)
    target_packages = _read_lock(root / TARGET_LOCK_RELATIVE, "target", errors)
    tools_packages = _read_lock(root / TOOLS_LOCK_RELATIVE, "tools-tree", errors)
    target_names = {package["name"] for package in target_packages}
    if not APPROVED_DIRECT_PACKAGES.issubset(target_names):
        errors.append("target lock shall contain every approved direct package")
    if "apt" in target_names:
        errors.append("target lock prohibits apt")
    if "debsbom" in target_names:
        errors.append("target lock prohibits debsbom")
    if any(package["suite"] == "trixie-backports" for package in target_packages):
        errors.append("target lock prohibits trixie-backports")
    debsbom_packages = [
        package for package in tools_packages if package["name"] == "debsbom"
    ]
    if len(debsbom_packages) != 1:
        errors.append("tools-tree lock shall contain debsbom exactly once")
    elif (
        debsbom_packages[0]["version"] != SELECTED_SBOM_VERSION
        or debsbom_packages[0]["suite"] != "trixie-backports"
    ):
        errors.append("tools-tree lock shall pin debsbom from trixie-backports")
    cyclonedx_packages = [
        package
        for package in tools_packages
        if package["name"] == "python3-cyclonedx-lib"
    ]
    if len(cyclonedx_packages) != 1:
        errors.append(
            "tools-tree lock shall contain the CycloneDX runtime exactly once"
        )
    elif (
        cyclonedx_packages[0]["version"] != SELECTED_CYCLONEDX_RUNTIME_VERSION
        or cyclonedx_packages[0]["suite"] != "trixie"
    ):
        errors.append("tools-tree lock shall pin the selected CycloneDX runtime")
    package_lines = _active_lines(root / PACKAGES_RELATIVE, errors)
    locked_specs = [
        f"{package['name']}={package['version']}" for package in target_packages
    ]
    if package_lines != locked_specs:
        errors.append("packages.list shall be generated exactly from target-lock.json")
    tools_package_lines = _active_lines(root / TOOLS_PACKAGES_RELATIVE, errors)
    tools_locked_specs = [
        f"{package['name']}={package['version']}" for package in tools_packages
    ]
    if tools_package_lines != tools_locked_specs:
        errors.append(
            "tools-tree-packages.list shall be generated exactly from its lock"
        )
    _validate_profile(root, errors)

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
