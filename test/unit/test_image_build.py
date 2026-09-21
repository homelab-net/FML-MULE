"""Tests for the GAP-09B development-image build contract."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from configparser import ConfigParser
from pathlib import Path
from types import ModuleType

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
VALIDATOR_PATH = REPO_ROOT / "tools/validate-image.py"
ROOT_VALIDATOR_PATH = REPO_ROOT / "tools/validate-image-root.py"
CACHE_VALIDATOR_PATH = REPO_ROOT / "tools/validate-package-cache.py"
REPRODUCIBILITY_SCRIPT = REPO_ROOT / "tools/verify-image-reproducibility.sh"
BUILD_SCRIPT = REPO_ROOT / "tools/build-image.sh"
BUILDER_RESOLVER = REPO_ROOT / "tools/resolve-mkosi-builder.sh"
FINALIZE_SCRIPT = REPO_ROOT / "os/image/mkosi.finalize"
DIRECT_PACKAGES = REPO_ROOT / "os/image/manifest/direct-packages.list"
TARGET_LOCK = REPO_ROOT / "os/image/manifest/target-lock.json"
TOOLS_TREE_LOCK = REPO_ROOT / "os/image/manifest/tools-tree-lock.json"
TARGET_SOURCES = (
    REPO_ROOT / "os/image/sandbox-target/etc/apt/sources.list.d/mkosi.sources"
)
TOOLS_SOURCES = (
    REPO_ROOT / "os/image/sandbox-tools/etc/apt/sources.list.d/mkosi.sources"
)
APPROVED_DIRECT_PACKAGES = {
    "dbus",
    "initramfs-tools",
    "linux-image-amd64",
    "systemd",
    "systemd-boot",
    "systemd-boot-efi",
    "systemd-sysv",
    "udev",
}
IMAGE_FILES = (
    Path("os/image/build-inputs.yml"),
    Path("os/image/mkosi.conf"),
    Path("os/image/manifest/direct-packages.list"),
    Path("os/image/manifest/packages.list"),
    Path("os/image/manifest/target-lock.json"),
    Path("os/image/manifest/tools-tree-direct-packages.list"),
    Path("os/image/manifest/tools-tree-lock.json"),
    Path("os/image/manifest/tools-tree-packages.list"),
    Path("os/image/sandbox-target/etc/apt/sources.list.d/mkosi.sources"),
    Path("os/image/sandbox-tools/etc/apt/sources.list.d/mkosi.sources"),
)


def _load_validator() -> ModuleType:
    """Import the image validator as a test module."""
    spec = importlib.util.spec_from_file_location("validate_image", VALIDATOR_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _load_root_validator() -> ModuleType:
    """Import the installed-root validator as a test module."""
    spec = importlib.util.spec_from_file_location(
        "validate_image_root", ROOT_VALIDATOR_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _load_cache_validator() -> ModuleType:
    """Import the retained-package cache validator as a test module."""
    spec = importlib.util.spec_from_file_location(
        "validate_package_cache", CACHE_VALIDATOR_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def validator() -> ModuleType:
    """Return the image-input validator module."""
    return _load_validator()


@pytest.fixture
def repository(tmp_path: Path) -> Path:
    """Copy the governed image inputs into a temporary repository."""
    for relative in IMAGE_FILES:
        destination = tmp_path / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO_ROOT / relative, destination)
    return tmp_path


def test_image_validator_exists() -> None:
    """GAP-09B shall have an executable input validator."""
    assert VALIDATOR_PATH.is_file()


def test_built_root_validator_exists() -> None:
    """GAP-09C shall inspect the installed root rather than intent alone."""
    assert ROOT_VALIDATOR_PATH.is_file()


def test_package_cache_validator_exists() -> None:
    """GAP-09C shall authenticate every retained package before replay."""
    assert CACHE_VALIDATOR_PATH.is_file()


def test_reproducibility_runner_exists() -> None:
    """GAP-09C shall execute and preserve the three-build comparison."""
    assert REPRODUCIBILITY_SCRIPT.is_file()


def test_finalize_uses_debsbom_0101_supported_schema_selector(
    tmp_path: Path,
) -> None:
    """The pinned debsbom CLI shall receive its only supported schema value."""
    buildroot = tmp_path / "root"
    output = tmp_path / "output"
    source = tmp_path / "source"
    fake_bin = tmp_path / "bin"
    (buildroot / "var/lib/dpkg").mkdir(parents=True)
    output.mkdir()
    (source / "tools").mkdir(parents=True)
    fake_bin.mkdir()
    (fake_bin / "debsbom").write_text(
        """#!/bin/sh
set -eu
previous=
found=
for argument do
  if [ "$previous" = --cdx-schema-version ]; then
    [ "$argument" = latest ] || exit 64
    found=1
  fi
  previous=$argument
done
[ "$found" = 1 ]
""",
        encoding="utf-8",
    )
    (fake_bin / "python3").write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    for executable in fake_bin.iterdir():
        executable.chmod(0o755)

    shell = shutil.which("sh")
    assert shell is not None
    result = subprocess.run(  # noqa: S603
        [shell, str(FINALIZE_SCRIPT)],
        env=os.environ
        | {
            "PATH": f"{fake_bin}{os.pathsep}{os.environ['PATH']}",
            "BUILDROOT": str(buildroot),
            "OUTPUTDIR": str(output),
            "SRCDIR": str(source),
        },
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr


def test_package_cache_validator_detects_missing_and_corrupt_packages(
    tmp_path: Path,
) -> None:
    """The retained cache shall fail on either absence or checksum drift."""
    cache = tmp_path / "cache"
    cache.mkdir()
    package = cache / "fixture_1%3a1.0_amd64.deb"
    package.write_bytes(b"authenticated fixture")
    checksum = hashlib.sha256(package.read_bytes()).hexdigest()
    lock = tmp_path / "lock.json"
    lock.write_text(
        json.dumps(
            {
                "packages": [
                    {
                        "name": "fixture",
                        "version": "1:1.0",
                        "architecture": "amd64",
                        "filename": "pool/main/f/fixture/fixture_1.0_amd64.deb",
                        "sha256": checksum,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    validator = _load_cache_validator()
    assert validator.validate(cache, [lock]) == []

    package.write_bytes(b"corrupt fixture")
    assert any(
        "checksum mismatch" in error for error in validator.validate(cache, [lock])
    )
    package.unlink()
    assert any(
        "missing expected package" in error
        for error in validator.validate(cache, [lock])
    )


def test_package_cache_rejects_decoy_name_and_modified_expected_file(
    tmp_path: Path,
) -> None:
    """A valid hash under another name shall not authenticate a package filename."""
    cache = tmp_path / "cache"
    cache.mkdir()
    expected = cache / "fixture_1.0_amd64.deb"
    decoy = cache / "decoy_1.0_amd64.deb"
    authenticated = b"authenticated fixture"
    expected.write_bytes(b"modified fixture")
    decoy.write_bytes(authenticated)
    lock = tmp_path / "lock.json"
    lock.write_text(
        json.dumps(
            {
                "packages": [
                    {
                        "name": "fixture",
                        "version": "1.0",
                        "architecture": "amd64",
                        "filename": f"pool/main/f/fixture/{expected.name}",
                        "sha256": hashlib.sha256(authenticated).hexdigest(),
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    errors = _load_cache_validator().validate(cache, [lock])
    assert f"package cache checksum mismatch for {expected.name}" in errors
    assert f"package cache contains unexpected package: {decoy.name}" in errors


def _root_fixture(tmp_path: Path) -> tuple[Path, Path, Path]:
    """Create one minimal locked root and matching CycloneDX fixture."""
    root = tmp_path / "root"
    status = root / "var/lib/dpkg/status"
    status.parent.mkdir(parents=True)
    status.write_text(
        """Package: systemd
Status: install ok installed
Architecture: amd64
Version: fixture-version

""",
        encoding="utf-8",
    )
    copyright_file = root / "usr/share/doc/systemd/copyright"
    copyright_file.parent.mkdir(parents=True)
    copyright_file.write_text("Fixture licence.\n", encoding="utf-8")
    lock = tmp_path / "target-lock.json"
    lock.write_text(
        json.dumps(
            {
                "packages": [
                    {
                        "name": "systemd",
                        "version": "fixture-version",
                        "architecture": "amd64",
                        "source": "systemd",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    sbom = tmp_path / "sbom.cdx.json"
    sbom.write_text(
        json.dumps(
            {
                "bomFormat": "CycloneDX",
                "specVersion": "1.6",
                "components": [
                    {
                        "purl": "pkg:deb/debian/systemd@fixture-version?arch=amd64",
                        "licenses": [{"expression": "LGPL-2.1-or-later"}],
                    },
                    {"purl": "pkg:deb/debian/systemd@fixture-version?arch=source"},
                ],
            }
        ),
        encoding="utf-8",
    )
    return root, lock, sbom


def test_built_root_validator_accepts_matching_installed_content(
    tmp_path: Path,
) -> None:
    """A matching installed root and source-aware SBOM shall pass."""
    root, lock, sbom = _root_fixture(tmp_path)
    errors, exceptions = _load_root_validator().validate(root, lock, sbom)
    assert errors == []
    assert exceptions == []


def test_built_root_validator_detects_prohibited_and_missing_content(
    tmp_path: Path,
) -> None:
    """APT, repository files, missing licences, and SBOM drift shall fail."""
    root, lock, sbom = _root_fixture(tmp_path)
    status = root / "var/lib/dpkg/status"
    status.write_text(
        status.read_text(encoding="utf-8")
        + "Package: apt\nStatus: install ok installed\n"
        + "Architecture: amd64\nVersion: fixture-version\n\n",
        encoding="utf-8",
    )
    (root / "usr/share/doc/systemd/copyright").unlink()
    sources = root / "etc/apt/sources.list.d/live.list"
    sources.parent.mkdir(parents=True)
    sources.write_text(
        "deb https://deb.debian.org/debian trixie main\n", encoding="utf-8"
    )
    sbom.write_text(
        json.dumps({"bomFormat": "CycloneDX", "specVersion": "1.6", "components": []}),
        encoding="utf-8",
    )

    errors, _exceptions = _load_root_validator().validate(root, lock, sbom)
    assert any("extra=['apt']" in error for error in errors)
    assert "target contains prohibited package apt" in errors
    assert "target contains an APT repository file" in errors
    assert "target package lacks Debian copyright file: systemd" in errors
    assert any("SBOM lacks target binary package" in error for error in errors)
    assert any("SBOM lacks source-package components" in error for error in errors)


@pytest.mark.parametrize(
    "licenses",
    [
        [{"license": {"name": "custom licence text"}}],
        [{"expression": "custom licence text"}],
        [{"license": {"id": "NotARealLicense"}}],
        [{"expression": "MIT AND NotARealLicense"}],
        [],
    ],
)
def test_built_root_reports_non_spdx_licence_choices(
    tmp_path: Path, licenses: list[dict[str, object]]
) -> None:
    """Name-only or malformed licence choices shall remain explicit exceptions."""
    root, lock, sbom = _root_fixture(tmp_path)
    document = json.loads(sbom.read_text(encoding="utf-8"))
    document["components"][0]["licenses"] = licenses
    sbom.write_text(json.dumps(document), encoding="utf-8")

    errors, exceptions = _load_root_validator().validate(root, lock, sbom)
    assert errors == []
    assert exceptions == [
        {
            "name": "systemd",
            "version": "fixture-version",
            "reason": "no SPDX-normalized declared licence",
        }
    ]


def test_build_script_check_mode() -> None:
    """The builder shall expose a non-privileged contract check."""
    shell = shutil.which("sh")
    assert shell is not None
    result = subprocess.run(  # noqa: S603
        [shell, str(BUILD_SCRIPT), "--check"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_repository_image_inputs_are_valid(validator: ModuleType) -> None:
    """The committed builder inputs shall be internally consistent."""
    assert validator.validate_repository(REPO_ROOT) == []


def test_governed_tools_tree_is_enabled() -> None:
    """Pinned tools-tree metadata shall activate rather than describe a fallback."""
    config = ConfigParser(interpolation=None)
    config.optionxform = str  # type: ignore[method-assign]
    config.read(REPO_ROOT / "os/image/mkosi.conf", encoding="utf-8")
    assert config["Build"]["ToolsTree"] == "default"


def test_approved_direct_package_intent_is_complete() -> None:
    """FML-ADR-081 shall expose exactly the owner-approved boot foundation."""
    packages = {
        line.split("#", maxsplit=1)[0].strip()
        for line in DIRECT_PACKAGES.read_text(encoding="utf-8").splitlines()
        if line.split("#", maxsplit=1)[0].strip()
    }
    assert packages == APPROVED_DIRECT_PACKAGES


def test_snapshot_sources_are_scoped_by_build_role() -> None:
    """Target and tools package managers shall not inherit a live feed."""
    target = TARGET_SOURCES.read_text(encoding="utf-8")
    tools_tree = TOOLS_SOURCES.read_text(encoding="utf-8")
    snapshot = "20260912T000000Z"

    assert f"archive/debian/{snapshot}" in target
    assert f"archive/debian-security/{snapshot}" in target
    assert "trixie-security" in target
    assert "trixie-backports" not in target
    assert "deb.debian.org" not in target
    assert "security.debian.org" not in target

    assert target in tools_tree
    assert "trixie-backports" in tools_tree
    assert "deb.debian.org" not in tools_tree
    assert "security.debian.org" not in tools_tree


@pytest.mark.parametrize("lock_path", [TARGET_LOCK, TOOLS_TREE_LOCK])
def test_package_locks_have_complete_provenance(lock_path: Path) -> None:
    """Every resolved package shall carry the provenance needed for replay."""
    document = yaml.safe_load(lock_path.read_text(encoding="utf-8"))
    assert document["schema_version"] == "1.0"
    assert document["snapshot"] == "20260912T000000Z"
    assert document["packages"]
    required = {
        "name",
        "version",
        "architecture",
        "source",
        "suite",
        "filename",
        "sha256",
    }
    assert all(required == set(package) for package in document["packages"])


def test_direct_package_and_source_drift_are_rejected(
    repository: Path, validator: ModuleType
) -> None:
    """Both the owner-approved intent and dated source boundary shall bind."""
    direct = repository / "os/image/manifest/direct-packages.list"
    direct.write_text(
        direct.read_text(encoding="utf-8").replace("dbus", "curl", 1),
        encoding="utf-8",
    )
    sources = repository / TARGET_SOURCES.relative_to(REPO_ROOT)
    sources.write_text(
        sources.read_text(encoding="utf-8").replace(
            "https://snapshot.debian.org/archive/debian/20260912T000000Z",
            "https://deb.debian.org/debian",
        ),
        encoding="utf-8",
    )

    errors = validator.validate_repository(repository)
    assert any("direct target packages" in error for error in errors)
    assert any(
        "target snapshot sources shall be exactly signed" in error for error in errors
    )


def test_prohibited_target_and_lock_checksum_are_rejected(
    repository: Path, validator: ModuleType
) -> None:
    """A plausible lock cannot add apt or lose package integrity."""
    lock_path = repository / TARGET_LOCK.relative_to(REPO_ROOT)
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    lock["packages"][0]["name"] = "apt"
    lock["packages"][0]["sha256"] = "0" * 63
    lock_path.write_text(json.dumps(lock), encoding="utf-8")

    errors = validator.validate_repository(repository)
    assert any("target lock prohibits apt" in error for error in errors)
    assert any("package SHA-256" in error for error in errors)


def test_tools_tree_lock_requires_selected_sbom_generator(
    repository: Path, validator: ModuleType
) -> None:
    """The build environment shall lock the selected builder-only generator."""
    lock_path = repository / TOOLS_TREE_LOCK.relative_to(REPO_ROOT)
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    lock["packages"] = [
        package for package in lock["packages"] if package["name"] != "debsbom"
    ]
    lock_path.write_text(json.dumps(lock), encoding="utf-8")

    assert any(
        "tools-tree lock shall contain debsbom" in error
        for error in validator.validate_repository(repository)
    )


def test_tools_tree_lock_requires_cyclonedx_runtime(
    repository: Path, validator: ModuleType
) -> None:
    """The locked generator shall include the runtime its CDX path imports."""
    lock_path = repository / TOOLS_TREE_LOCK.relative_to(REPO_ROOT)
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    lock["packages"] = [
        package
        for package in lock["packages"]
        if package["name"] != "python3-cyclonedx-lib"
    ]
    lock_path.write_text(json.dumps(lock), encoding="utf-8")

    assert any(
        "tools-tree lock shall contain the CycloneDX runtime" in error
        for error in validator.validate_repository(repository)
    )


def test_live_mirror_and_disabled_key_check_are_rejected(
    repository: Path, validator: ModuleType
) -> None:
    """The build cannot silently resolve from a live or unsigned source."""
    config_path = repository / "os/image/mkosi.conf"
    config = ConfigParser(interpolation=None)
    config.optionxform = str  # type: ignore[method-assign]
    config.read(config_path, encoding="utf-8")
    config["Distribution"]["Mirror"] = "https://deb.debian.org/debian"
    config["Distribution"]["RepositoryKeyCheck"] = "no"
    config["Output"]["Seed"] = "random"
    config["Content"]["Environment"] = (
        'SYSTEMD_REPART_MKFS_OPTIONS_EXT4="-E hash_seed=random"'
    )
    config["Output"]["Compression"] = "none"
    with config_path.open("w", encoding="utf-8") as stream:
        config.write(stream, space_around_delimiters=False)

    errors = validator.validate_repository(repository)
    assert any("Mirror does not match" in error for error in errors)
    assert any("RepositoryKeyCheck shall be yes" in error for error in errors)
    assert any("[Output] Seed does not match" in error for error in errors)
    assert any("[Content] Environment does not match" in error for error in errors)
    assert any("[Output] Compression is not a governed" in error for error in errors)


@pytest.mark.parametrize("mutation", ["trusted", "extra"])
def test_snapshot_sources_reject_bypass_fields_and_extra_stanzas(
    repository: Path, validator: ModuleType, mutation: str
) -> None:
    """Only the exact signed Deb822 source set shall enter either role."""
    source_path = repository / TARGET_SOURCES.relative_to(REPO_ROOT)
    content = source_path.read_text(encoding="utf-8")
    if mutation == "trusted":
        content = content.replace("Enabled: yes\n", "Enabled: yes\nTrusted: yes\n", 1)
    else:
        content += """

Enabled: yes
Types: deb
URIs: https://packages.example.invalid/debian
Suites: trixie
Components: main
Signed-By: /usr/share/keyrings/debian-archive-keyring.gpg
Check-Valid-Until: no
"""
    source_path.write_text(content, encoding="utf-8")

    assert any(
        "target snapshot sources shall be exactly signed" in error
        for error in validator.validate_repository(repository)
    )


def test_snapshot_sources_reject_sibling_source_file(
    repository: Path, validator: ModuleType
) -> None:
    """The sandbox source directory shall contain only the governed file."""
    sibling = (
        repository / TARGET_SOURCES.relative_to(REPO_ROOT).parent / "untrusted.sources"
    )
    sibling.write_text(
        """Enabled: yes
Types: deb
URIs: https://deb.debian.org/debian
Suites: trixie
Components: main
Trusted: yes
""",
        encoding="utf-8",
    )

    assert any(
        "target sources.list.d shall contain only mkosi.sources" in error
        for error in validator.validate_repository(repository)
    )


def test_floating_builder_version_is_rejected(
    repository: Path, validator: ModuleType
) -> None:
    """A channel name cannot stand in for the Debian builder package pin."""
    inputs_path = repository / "os/image/build-inputs.yml"
    inputs = yaml.safe_load(inputs_path.read_text(encoding="utf-8"))
    inputs["builder"]["version"] = "latest"
    inputs_path.write_text(yaml.safe_dump(inputs, sort_keys=False), encoding="utf-8")

    assert any(
        "builder.version shall be the exact Debian package version" in error
        for error in validator.validate_repository(repository)
    )


def test_approved_target_and_tools_tree_cannot_drift(
    repository: Path, validator: ModuleType
) -> None:
    """Changing both representations cannot evade the approved target."""
    inputs_path = repository / "os/image/build-inputs.yml"
    inputs = yaml.safe_load(inputs_path.read_text(encoding="utf-8"))
    inputs["distribution"]["name"] = "ubuntu"
    inputs["output"]["format"] = "directory"
    inputs["tools_tree"]["release"] = "testing"
    inputs_path.write_text(yaml.safe_dump(inputs, sort_keys=False), encoding="utf-8")

    errors = validator.validate_repository(repository)
    assert "distribution.name shall be selected value debian" in errors
    assert "output.format shall be selected value disk" in errors
    assert "tools_tree.release shall match the target release" in errors


def test_offline_wrapper_names_raw_artifact_and_forbids_network(
    repository: Path, tmp_path: Path
) -> None:
    """The wrapper shall request one raw basename and cache-only package use."""
    for relative in (
        Path("tools/build-image.sh"),
        Path("tools/resolve-mkosi-builder.sh"),
        Path("tools/validate-image.py"),
    ):
        destination = repository / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO_ROOT / relative, destination)
        destination.chmod(0o755)
    fake_bin = tmp_path / "bin"
    packaged_bin = tmp_path / "package/bin"
    fake_bin.mkdir()
    packaged_bin.mkdir(parents=True)
    (fake_bin / "id").write_text("#!/bin/sh\nprintf '0\\n'\n", encoding="utf-8")
    (fake_bin / "dpkg-query").write_text(
        """#!/bin/sh
case "$1" in
  -W) printf '25.3-7' ;;
  -L) printf '%s\\n' "$FML_TEST_MKOSI_BIN" ;;
  -S) printf 'mkosi: %s\\n' "$2" ;;
  *) exit 2 ;;
esac
""",
        encoding="utf-8",
    )
    (fake_bin / "dpkg-deb").write_text(
        """#!/bin/sh
set -eu
[ "$1" = -x ]
target="$3$FML_TEST_MKOSI_BIN"
mkdir -p "$(dirname "$target")"
cp "$FML_TEST_MKOSI_BIN" "$target"
""",
        encoding="utf-8",
    )
    (fake_bin / "python3").write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    (fake_bin / "sha256sum").write_text(
        """#!/bin/sh
if [ "$1" = "$FML_MKOSI_PACKAGE_DEB" ]; then
  printf '%s  %s\\n' "$FML_TEST_MKOSI_SHA256" "$1"
else
  /usr/bin/sha256sum "$@"
fi
""",
        encoding="utf-8",
    )
    (fake_bin / "mkosi").write_text(
        '#!/bin/sh\n: >"$TMPDIR/shadow-mkosi-ran"\nexit 91\n',
        encoding="utf-8",
    )
    packaged_mkosi = packaged_bin / "mkosi"
    packaged_mkosi.write_text(
        """#!/bin/sh
set -eu
output_dir=
output=
printf '%s\\n' "$@" >"$TMPDIR/mkosi-arguments.txt"
while [ "$#" -gt 0 ]; do
  case "$1" in
    --output-directory) output_dir=$2; shift 2 ;;
    --output) output=$2; shift 2 ;;
    *) shift ;;
  esac
done
mkdir -p "$output_dir"
: >"$output_dir/$output.raw"
printf '{}\n' >"$output_dir/$output.sbom.cdx.json"
printf '{}\n' >"$output_dir/$output.license-exceptions.json"
""",
        encoding="utf-8",
    )
    (fake_bin / "unshare").write_text(
        """#!/bin/sh
set -eu
printf '%s\n' "$@" >"$TMPDIR/unshare-arguments.txt"
[ "$1" = --net ]
shift
[ "$1" = -- ]
shift
exec "$@"
""",
        encoding="utf-8",
    )
    for executable in [*fake_bin.iterdir(), packaged_mkosi]:
        executable.chmod(0o755)

    builder_deb = tmp_path / "mkosi_25.3-7_all.deb"
    builder_deb.write_bytes(b"authenticated mkosi package fixture")
    inputs_path = repository / "os/image/build-inputs.yml"
    inputs = yaml.safe_load(inputs_path.read_text(encoding="utf-8"))

    shell = shutil.which("sh")
    assert shell is not None
    environment = os.environ | {
        "PATH": f"{fake_bin}{os.pathsep}{os.environ['PATH']}",
        "TMPDIR": str(tmp_path),
        "FML_MKOSI_PACKAGE_DEB": str(builder_deb),
        "FML_TEST_MKOSI_SHA256": inputs["builder"]["package_sha256"],
        "FML_TEST_MKOSI_BIN": str(packaged_mkosi),
    }
    result = subprocess.run(  # noqa: S603
        [shell, str(repository / "tools/build-image.sh"), "--offline"],
        cwd=repository,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert not (tmp_path / "shadow-mkosi-ran").exists()
    assert (repository / "out/image/mule-development.raw").is_file()
    arguments = (tmp_path / "mkosi-arguments.txt").read_text(encoding="utf-8")
    assert "--cache-only=always" in arguments
    assert "--tools-tree-package=\n" in arguments
    assert (
        "--tools-tree-package\n"
        "/var/cache/apt/archives/debsbom_0.10.1-1~bpo13+1_all.deb\n" in arguments
    )
    assert f"--build-sources\n{repository}\n" in arguments
    isolation = (tmp_path / "unshare-arguments.txt").read_text(encoding="utf-8")
    assert isolation.startswith(f"--net\n--\n{packaged_mkosi}\n")
    systemd = next(
        package
        for package in json.loads(TARGET_LOCK.read_text(encoding="utf-8"))["packages"]
        if package["name"] == "systemd"
    )
    assert f"--package\nsystemd={systemd['version']}" in arguments
    checksum = (repository / "out/image/mule-development.raw.sha256").read_text(
        encoding="utf-8"
    )
    assert str(repository) not in checksum
    assert checksum.rstrip().endswith("  mule-development.raw")


def _reproducibility_fixture(tmp_path: Path) -> tuple[Path, dict[str, str]]:
    """Create a fake three-build/QEMU environment for the orchestration path."""
    repository = tmp_path / "repository"
    tools = repository / "tools"
    image = repository / "os/image"
    fake_bin = tmp_path / "bin"
    packaged_bin = tmp_path / "package/bin"
    tools.mkdir(parents=True)
    image.mkdir(parents=True)
    fake_bin.mkdir()
    packaged_bin.mkdir(parents=True)
    shutil.copy2(REPRODUCIBILITY_SCRIPT, tools / REPRODUCIBILITY_SCRIPT.name)
    (tools / REPRODUCIBILITY_SCRIPT.name).chmod(0o755)
    (image / "build-inputs.yml").write_text("fixture: true\n", encoding="utf-8")

    (tools / "resolve-mkosi-builder.sh").write_text(
        "#!/bin/sh\nprintf '%s\\n' \"$FML_TEST_PACKAGED_MKOSI\"\n",
        encoding="utf-8",
    )
    (tools / "build-image.sh").write_text(
        """#!/bin/sh
set -eu
: "${FML_IMAGE_OUTPUT_DIR:?}"
: "${FML_IMAGE_PACKAGE_CACHE:?}"
printf '%s|%s|%s\n' "$FML_IMAGE_OUTPUT_DIR" "$FML_IMAGE_PACKAGE_CACHE" "$1" \
  >>"$FML_TEST_BUILD_CALLS"
mkdir -p "$FML_IMAGE_OUTPUT_DIR" "$FML_IMAGE_PACKAGE_CACHE"
content=identical-image
case "${FML_TEST_DIFFER:-}:$FML_IMAGE_OUTPUT_DIR" in
  1:*networked-2) content=different-image ;;
esac
printf '%s\n' "$content" >"$FML_IMAGE_OUTPUT_DIR/mule-development.raw"
printf 'fixture checksum\n' >"$FML_IMAGE_OUTPUT_DIR/mule-development.raw.sha256"
printf '{}\n' >"$FML_IMAGE_OUTPUT_DIR/mule-development.sbom.cdx.json"
printf '{}\n' >"$FML_IMAGE_OUTPUT_DIR/mule-development.license-exceptions.json"
printf 'cached package\n' >"$FML_IMAGE_PACKAGE_CACHE/fixture.deb"
""",
        encoding="utf-8",
    )
    packaged_mkosi = packaged_bin / "mkosi"
    packaged_mkosi.write_text(
        """#!/bin/sh
set -eu
: >"$FML_TEST_PACKAGED_MKOSI_RAN"
if [ "${FML_TEST_NO_BOOT_MARKER:-}" != 1 ]; then
  printf '%s\n' 'Reached target multi-user.target'
fi
""",
        encoding="utf-8",
    )
    (fake_bin / "id").write_text("#!/bin/sh\nprintf '0\\n'\n", encoding="utf-8")
    (fake_bin / "timeout").write_text('#!/bin/sh\nshift\nexec "$@"\n', encoding="utf-8")
    (fake_bin / "mkosi").write_text(
        '#!/bin/sh\n: >"$FML_TEST_SHADOW_MKOSI_RAN"\nexit 91\n',
        encoding="utf-8",
    )
    for executable in [
        tools / "resolve-mkosi-builder.sh",
        tools / "build-image.sh",
        packaged_mkosi,
        *fake_bin.iterdir(),
    ]:
        executable.chmod(0o755)

    environment = os.environ | {
        "PATH": f"{fake_bin}{os.pathsep}{os.environ['PATH']}",
        "FML_TEST_BUILD_CALLS": str(tmp_path / "build-calls.txt"),
        "FML_TEST_PACKAGED_MKOSI": str(packaged_mkosi),
        "FML_TEST_PACKAGED_MKOSI_RAN": str(tmp_path / "packaged-mkosi-ran"),
        "FML_TEST_SHADOW_MKOSI_RAN": str(tmp_path / "shadow-mkosi-ran"),
    }
    return repository, environment


def _run_reproducibility_fixture(
    repository: Path, environment: dict[str, str]
) -> subprocess.CompletedProcess[str]:
    """Execute the fake three-build harness."""
    shell = shutil.which("sh")
    assert shell is not None
    return subprocess.run(  # noqa: S603
        [shell, str(repository / "tools/verify-image-reproducibility.sh")],
        cwd=repository,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )


def test_reproducibility_runner_uses_clean_builds_and_authenticated_vm(
    tmp_path: Path,
) -> None:
    """Networked builds shall be independent and QEMU shall use packaged mkosi."""
    repository, environment = _reproducibility_fixture(tmp_path)
    result = _run_reproducibility_fixture(repository, environment)

    assert result.returncode == 0, result.stdout + result.stderr
    calls = [
        line.split("|")
        for line in (tmp_path / "build-calls.txt")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    assert len(calls) == 3
    assert len({call[0] for call in calls}) == 3
    assert calls[0][1] != calls[1][1]
    assert calls[2][1] == calls[0][1]
    assert calls[0][2] == calls[1][2] == "--populate-cache"
    assert calls[2][2] == "--offline"
    assert (tmp_path / "packaged-mkosi-ran").is_file()
    assert not (tmp_path / "shadow-mkosi-ran").exists()
    assert "Three identical raw images" in result.stdout


def test_reproducibility_runner_rejects_image_drift(tmp_path: Path) -> None:
    """A differing clean build shall fail before QEMU acceptance."""
    repository, environment = _reproducibility_fixture(tmp_path)
    environment["FML_TEST_DIFFER"] = "1"
    result = _run_reproducibility_fixture(repository, environment)

    assert result.returncode != 0
    assert "Raw image identities differ" in result.stderr
    assert not (tmp_path / "packaged-mkosi-ran").exists()


def test_reproducibility_runner_requires_boot_target_marker(tmp_path: Path) -> None:
    """A zero-status VM without the systemd target marker shall still fail."""
    repository, environment = _reproducibility_fixture(tmp_path)
    environment["FML_TEST_NO_BOOT_MARKER"] = "1"
    result = _run_reproducibility_fixture(repository, environment)

    assert result.returncode != 0
    assert "QEMU did not report the selected systemd target" in result.stderr


def _builder_resolver_fixture(
    tmp_path: Path,
    *,
    installed_payload: str,
    packaged_payload: str,
    installed_module_payload: str = "expected module\n",
    packaged_module_payload: str = "expected module\n",
) -> tuple[Path, dict[str, str]]:
    """Create a fake dpkg database and authenticated package payload."""
    fake_bin = tmp_path / "bin"
    installed_bin = tmp_path / "installed/usr/bin/mkosi"
    installed_module = (
        tmp_path / "installed/usr/lib/python3/dist-packages/mkosi/__init__.py"
    )
    packaged_bin = tmp_path / "packaged-mkosi"
    packaged_module = tmp_path / "packaged-mkosi-module"
    package_deb = tmp_path / "mkosi_25.3-7_all.deb"
    inputs = tmp_path / "build-inputs.yml"
    fake_bin.mkdir()
    installed_bin.parent.mkdir(parents=True)
    installed_bin.write_text(installed_payload, encoding="utf-8")
    installed_bin.chmod(0o755)
    installed_module.parent.mkdir(parents=True)
    installed_module.write_text(installed_module_payload, encoding="utf-8")
    packaged_bin.write_text(packaged_payload, encoding="utf-8")
    packaged_module.write_text(packaged_module_payload, encoding="utf-8")
    package_deb.write_text("authenticated package fixture\n", encoding="utf-8")
    package_sha = hashlib.sha256(package_deb.read_bytes()).hexdigest()
    inputs.write_text(
        f"builder:\n  version: 25.3-7\n  package_sha256: {package_sha}\n",
        encoding="utf-8",
    )

    (fake_bin / "dpkg-query").write_text(
        """#!/bin/sh
set -eu
case "$1" in
  -W) printf '%s' '25.3-7' ;;
  -L) printf '%s\n' "$FML_TEST_INSTALLED_MKOSI" ;;
  -S) printf 'mkosi: %s\n' "$2" ;;
  *) exit 2 ;;
esac
""",
        encoding="utf-8",
    )
    (fake_bin / "dpkg-deb").write_text(
        """#!/bin/sh
set -eu
[ "$1" = -x ]
destination=$3
target="$destination$FML_TEST_INSTALLED_MKOSI"
mkdir -p "$(dirname "$target")"
cp "$FML_TEST_PACKAGED_MKOSI" "$target"
module="$destination$FML_TEST_INSTALLED_MKOSI_MODULE"
mkdir -p "$(dirname "$module")"
cp "$FML_TEST_PACKAGED_MKOSI_MODULE" "$module"
""",
        encoding="utf-8",
    )
    for executable in fake_bin.iterdir():
        executable.chmod(0o755)

    environment = os.environ | {
        "PATH": f"{fake_bin}{os.pathsep}{os.environ['PATH']}",
        "FML_MKOSI_PACKAGE_DEB": str(package_deb),
        "FML_TEST_INSTALLED_MKOSI": str(installed_bin),
        "FML_TEST_INSTALLED_MKOSI_MODULE": str(installed_module),
        "FML_TEST_PACKAGED_MKOSI": str(packaged_bin),
        "FML_TEST_PACKAGED_MKOSI_MODULE": str(packaged_module),
    }
    return inputs, environment


def test_builder_resolver_binds_installed_executable_to_package(tmp_path: Path) -> None:
    """The executable shall contain the bytes from the authenticated archive."""
    inputs, environment = _builder_resolver_fixture(
        tmp_path, installed_payload="expected\n", packaged_payload="expected\n"
    )
    shell = shutil.which("sh")
    assert shell is not None

    result = subprocess.run(  # noqa: S603
        [shell, str(BUILDER_RESOLVER), str(inputs)],
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.strip() == environment["FML_TEST_INSTALLED_MKOSI"]


def test_builder_resolver_rejects_modified_installed_executable(
    tmp_path: Path,
) -> None:
    """Package ownership alone shall not admit a modified builder payload."""
    inputs, environment = _builder_resolver_fixture(
        tmp_path, installed_payload="modified\n", packaged_payload="expected\n"
    )
    shell = shutil.which("sh")
    assert shell is not None

    result = subprocess.run(  # noqa: S603
        [shell, str(BUILDER_RESOLVER), str(inputs)],
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "differs from the authenticated package" in result.stderr


def test_builder_resolver_rejects_modified_installed_module(tmp_path: Path) -> None:
    """The authenticated launcher shall not load a modified package module."""
    inputs, environment = _builder_resolver_fixture(
        tmp_path,
        installed_payload="expected\n",
        packaged_payload="expected\n",
        installed_module_payload="modified module\n",
        packaged_module_payload="expected module\n",
    )
    shell = shutil.which("sh")
    assert shell is not None

    result = subprocess.run(  # noqa: S603
        [shell, str(BUILDER_RESOLVER), str(inputs)],
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "differs from the authenticated package" in result.stderr
