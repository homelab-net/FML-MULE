"""Tests for the GAP-09B development-image build contract."""

from __future__ import annotations

import importlib.util
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
BUILD_SCRIPT = REPO_ROOT / "tools/build-image.sh"
IMAGE_FILES = (
    Path("os/image/build-inputs.yml"),
    Path("os/image/mkosi.conf"),
    Path("os/image/manifest/packages.list"),
)


def _load_validator() -> ModuleType:
    """Import the image validator as a test module."""
    spec = importlib.util.spec_from_file_location("validate_image", VALIDATOR_PATH)
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
    config["Output"]["Compression"] = "none"
    with config_path.open("w", encoding="utf-8") as stream:
        config.write(stream, space_around_delimiters=False)

    errors = validator.validate_repository(repository)
    assert any("Mirror does not match" in error for error in errors)
    assert any("RepositoryKeyCheck shall be yes" in error for error in errors)
    assert any("[Output] Seed does not match" in error for error in errors)
    assert any("[Output] Compression is not a governed" in error for error in errors)


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
        Path("tools/validate-image.py"),
    ):
        destination = repository / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO_ROOT / relative, destination)
        destination.chmod(0o755)
    (repository / "os/image/manifest/packages.list").write_text(
        "systemd=fixture-version  # fixture package\n", encoding="utf-8"
    )

    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    (fake_bin / "id").write_text("#!/bin/sh\nprintf '0\\n'\n", encoding="utf-8")
    (fake_bin / "dpkg-query").write_text(
        "#!/bin/sh\nprintf '25.3-7'\n", encoding="utf-8"
    )
    (fake_bin / "mkosi").write_text(
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
""",
        encoding="utf-8",
    )
    for executable in fake_bin.iterdir():
        executable.chmod(0o755)

    shell = shutil.which("sh")
    assert shell is not None
    environment = os.environ | {
        "PATH": f"{fake_bin}{os.pathsep}{os.environ['PATH']}",
        "TMPDIR": str(tmp_path),
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
    assert (repository / "out/image/mule-development.raw").is_file()
    arguments = (tmp_path / "mkosi-arguments.txt").read_text(encoding="utf-8")
    assert "--cache-only=always" in arguments
    assert "--package\nsystemd=fixture-version" in arguments
