#!/usr/bin/env python3
"""Resolve FML-ADR-081 package locks from authenticated Debian snapshots.

Usage:
    tools/resolve-image-packages.py --keyring PATH [--write] [REPOSITORY_ROOT]

The keyring is a builder input, not generated or downloaded by this script.
APT authenticates each InRelease file and its Packages checksum before this
tool records package metadata.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import tempfile
from email.parser import Parser
from pathlib import Path
from typing import Any

SNAPSHOT = "20260912T000000Z"  # FML-ADR-079 and FML-ADR-081
ROLES = ("target", "tools-tree")
PACKAGE_LINE = re.compile(r"^Inst\s+(\S+?)(?::(\S+))?\s+\((\S+)")
POLICY_VERSION = re.compile(r"^\s*(?:\*\*\*\s*)?(\S+)\s+\d+\s*$")
SUITE = re.compile(r"\b(trixie(?:-security|-backports)?)/")


def _run(command: list[str]) -> str:
    """Run one resolver command and return stdout."""
    result = subprocess.run(  # noqa: S603
        command,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"command failed ({result.returncode}): {' '.join(command)}\n"
            f"{result.stdout}{result.stderr}"
        )
    return result.stdout


def _intent(path: Path) -> list[str]:
    """Read package names or APT patterns from one reviewed intent file."""
    return [
        value
        for line in path.read_text(encoding="utf-8").splitlines()
        if (value := line.split("#", maxsplit=1)[0].strip())
    ]


def _apt_options(work: Path, sources: Path, keyring: Path) -> list[str]:
    """Create an isolated APT state and return its common arguments."""
    state = work / "state"
    cache = work / "cache"
    etc = work / "etc"
    (state / "lists/partial").mkdir(parents=True)
    (cache / "archives/partial").mkdir(parents=True)
    etc.mkdir()
    status = state / "status"
    status.touch()
    source_copy = etc / "mkosi.sources"
    source_copy.write_text(
        sources.read_text(encoding="utf-8").replace(
            "/usr/share/keyrings/debian-archive-keyring.gpg", str(keyring)
        ),
        encoding="utf-8",
    )
    return [
        "-o",
        "APT::Architecture=amd64",
        "-o",
        "APT::Architectures=amd64",
        "-o",
        "APT::Install-Recommends=false",
        "-o",
        "Acquire::AllowReleaseInfoChange=false",
        "-o",
        "Acquire::Check-Valid-Until=false",
        "-o",
        "Debug::NoLocking=true",
        "-o",
        f"Dir::Etc::sourcelist={source_copy}",
        "-o",
        "Dir::Etc::sourceparts=-",
        "-o",
        f"Dir::State={state}",
        "-o",
        f"Dir::State::status={status}",
        "-o",
        f"Dir::Cache={cache}",
    ]


def _suite(policy: str, version: str) -> str:
    """Return the snapshot suite advertising one exact package version."""
    active = False
    candidates: list[str] = []
    for line in policy.splitlines():
        match = POLICY_VERSION.match(line)
        if match:
            active = match.group(1) == version
            continue
        if not active:
            continue
        candidates.extend(SUITE.findall(line))
    if not candidates:
        raise RuntimeError(f"APT policy does not identify suite for version {version}")
    if "trixie-security" in candidates:
        return "trixie-security"
    if "trixie-backports" in candidates:
        return "trixie-backports"
    return "trixie"


def _metadata(name: str, version: str, options: list[str]) -> dict[str, str]:
    """Return the required provenance fields for one resolved package."""
    output = _run(["apt-cache", *options, "show", f"{name}={version}"])
    records = Parser().parsestr(output, headersonly=True)
    candidates = [records]
    if not records.get("Package"):
        candidates = [
            Parser().parsestr(block, headersonly=True)
            for block in output.split("\n\n")
            if block.strip()
        ]
    record = next(
        (
            item
            for item in candidates
            if item.get("Package") == name
            and item.get("Version") == version
            and item.get("Architecture") in {"amd64", "all"}
        ),
        None,
    )
    if record is None:
        raise RuntimeError(f"APT metadata missing for {name}={version}")
    source = record.get("Source", name).split(" ", maxsplit=1)[0]
    policy = _run(["apt-cache", *options, "policy", name])
    result = {
        "name": name,
        "version": version,
        "architecture": record["Architecture"],
        "source": source,
        "suite": _suite(policy, version),
        "filename": record["Filename"],
        "sha256": record["SHA256"],
    }
    if not re.fullmatch(r"[0-9a-f]{64}", result["sha256"]):
        raise RuntimeError(f"APT metadata has invalid SHA-256 for {name}={version}")
    return result


def resolve(root: Path, role: str, keyring: Path) -> dict[str, Any]:
    """Resolve one role's complete package closure."""
    sandbox_role = "target" if role == "target" else "tools"
    source = (
        root / f"os/image/sandbox-{sandbox_role}/etc/apt/sources.list.d/mkosi.sources"
    )
    intent_name = (
        "direct-packages.list"
        if role == "target"
        else "tools-tree-direct-packages.list"
    )
    intent = _intent(root / "os/image/manifest" / intent_name)
    with tempfile.TemporaryDirectory(prefix=f"fml-{role}-apt-") as temporary:
        work = Path(temporary)
        options = _apt_options(work, source, keyring)
        _run(["apt-get", *options, "update"])
        simulation = _run(
            [
                "apt-get",
                *options,
                "--simulate",
                "--no-install-recommends",
                "install",
                "?essential",
                "base-files",
                *intent,
            ]
        )
        resolved: dict[str, str] = {}
        for line in simulation.splitlines():
            match = PACKAGE_LINE.match(line)
            if match:
                resolved[match.group(1)] = match.group(3)
        if not resolved:
            raise RuntimeError(f"APT resolved no {role} packages")
        packages = [
            _metadata(name, version, options)
            for name, version in sorted(resolved.items())
            if role != "target" or name != "apt"
        ]
    if role == "target" and any(
        item["suite"] == "trixie-backports" for item in packages
    ):
        raise RuntimeError("target closure contains a backports package")
    prohibited = sorted(
        item["name"] for item in packages if item["name"] in {"apt", "debsbom"}
    )
    if role == "target" and prohibited:
        rendered = ", ".join(prohibited)
        raise RuntimeError(
            f"target closure contains prohibited build-side package(s): {rendered}"
        )
    return {
        "schema_version": "1.0",
        "governing_decision": "FML-ADR-081",
        "snapshot": SNAPSHOT,
        "role": role,
        "packages": packages,
    }


def _write(root: Path, locks: dict[str, dict[str, Any]]) -> None:
    """Write generated locks and mkosi's exact target package input."""
    manifest = root / "os/image/manifest"
    for role, document in locks.items():
        destination = manifest / f"{role}-lock.json"
        destination.write_text(
            json.dumps(document, indent=2, sort_keys=False) + "\n",
            encoding="utf-8",
        )
    target_lines = [
        "# Generated from target-lock.json by tools/resolve-image-packages.py.",
        "# FML-ADR-081. Do not edit this file by hand.",
        "",
        *(
            f"{package['name']}={package['version']}  # Exact target closure."
            for package in locks["target"]["packages"]
        ),
    ]
    (manifest / "packages.list").write_text(
        "\n".join(target_lines) + "\n", encoding="utf-8"
    )
    tools_lines = [
        "# Generated from tools-tree-lock.json by tools/resolve-image-packages.py.",
        "# FML-ADR-081. Do not edit this file by hand.",
        "",
        *(
            f"{package['name']}={package['version']}  # Exact tools-tree closure."
            for package in locks["tools-tree"]["packages"]
        ),
    ]
    (manifest / "tools-tree-packages.list").write_text(
        "\n".join(tools_lines) + "\n", encoding="utf-8"
    )


def main() -> int:
    """Resolve package roles and optionally update the governed lock files."""
    parser = argparse.ArgumentParser()
    parser.add_argument("repository_root", nargs="?", type=Path, default=Path.cwd())
    parser.add_argument("--keyring", required=True, type=Path)
    parser.add_argument("--write", action="store_true")
    arguments = parser.parse_args()
    root = arguments.repository_root.resolve()
    keyring = arguments.keyring.resolve()
    if not keyring.is_file():
        parser.error(f"keyring does not exist: {keyring}")
    missing = [
        command for command in ("apt-get", "apt-cache") if not shutil.which(command)
    ]
    if missing:
        parser.error(f"missing command(s): {', '.join(missing)}")
    locks = {role: resolve(root, role, keyring) for role in ROLES}
    if arguments.write:
        _write(root, locks)
    else:
        print(json.dumps(locks, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
