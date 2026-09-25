"""Tests for the FML-ADR-083 bounded runtime entry point."""

from __future__ import annotations

import json
import runpy
import subprocess
import sys
import tomllib
from configparser import ConfigParser
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_REGION = REPO_ROOT / "test/fixtures/regions/xx-testfixture/profile.yml"
FIXTURE_NODE = REPO_ROOT / "test/fixtures/nodes/ap-only/node.yml"
MISSION = REPO_ROOT / "mission/examples/valid-minimal.json"
INVALID_MISSION = REPO_ROOT / "mission/examples/invalid-unknown-field.json"
CATALOG = REPO_ROOT / "services/catalog/catalog.yml"
CATALOG_SCHEMA = REPO_ROOT / "services/catalog/catalog.schema.json"
QUADLETS = REPO_ROOT / "services/quadlets"
UNIT = REPO_ROOT / "os/systemd/mule-runtime.service"


def _command(mission: Path, output: Path) -> list[str]:
    """Return one complete runtime invocation using only explicit inputs."""
    return [
        sys.executable,
        "-m",
        "mule",
        "--region",
        str(FIXTURE_REGION),
        "--mission",
        str(mission),
        "--node",
        str(FIXTURE_NODE),
        "--catalog",
        str(CATALOG),
        "--catalog-schema",
        str(CATALOG_SCHEMA),
        "--quadlets",
        str(QUADLETS),
        "--out",
        str(output),
    ]


def test_python_module_entrypoint_renders_then_exits(tmp_path: Path) -> None:
    """The installed-form command shall do bounded real work and terminate."""
    output = tmp_path / "runtime"

    result = subprocess.run(  # noqa: S603
        _command(MISSION, output),
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    rendered = json.loads((output / "parameters.json").read_text(encoding="utf-8"))
    mission = json.loads(MISSION.read_text(encoding="utf-8"))
    region = yaml.safe_load(FIXTURE_REGION.read_text(encoding="utf-8"))
    assert rendered["region"]["id"] == region["region"]["id"]
    assert rendered["mission"]["id"] == mission["mission"]["id"]
    assert rendered["wifi"] == {
        "ap_channel": region["wifi"]["ap_channel"],
        "max_eirp_dbm": region["wifi"]["max_eirp_dbm"],
    }
    assert "SIMULATED" in result.stdout


def test_python_module_entrypoint_refuses_invalid_input_without_output(
    tmp_path: Path,
) -> None:
    """A malformed mission shall fail before any runtime artifact appears."""
    output = tmp_path / "runtime"

    result = subprocess.run(  # noqa: S603
        _command(INVALID_MISSION, output),
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )

    assert result.returncode == 2
    assert "schema validation" in result.stderr
    assert not (output / "parameters.json").exists()


def test_runtime_is_a_distributable_python_package() -> None:
    """The selected package model shall be declared rather than implied."""
    document = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    assert document["build-system"]["build-backend"] == "setuptools.build_meta"
    assert document["project"]["name"] == "fml-mule"
    assert document["project"]["version"] == "0.0.1"
    assert document["tool"]["setuptools"]["packages"] == ["mule"]


def test_native_unit_is_static_bounded_and_has_no_recovery_policy() -> None:
    """Open recovery and interface trades shall stay absent from the unit."""
    unit_text = UNIT.read_text(encoding="utf-8")
    unit = ConfigParser(interpolation=None, strict=True)
    unit.optionxform = str  # type: ignore[method-assign]
    unit.read_string(unit_text)

    assert unit["Service"]["Type"] == "oneshot"
    assert unit["Service"]["DynamicUser"] == "yes"
    assert unit["Service"]["User"] == "mule-runtime"
    assert unit["Service"]["RuntimeDirectory"] == "fml"
    assert unit["Service"]["UMask"] == "0077"
    command = unit["Service"]["ExecStart"]
    assert command.startswith("/usr/bin/python3 -m mule ")
    for required in (
        "--region /etc/fml/region.yml",
        "--mission /etc/fml/mission.json",
        "--node /etc/fml/node.yml",
        "--catalog /etc/fml/catalog.yml",
        "--catalog-schema /etc/fml/catalog.schema.json",
        "--quadlets /etc/containers/systemd/users",
        "--out /run/fml",
    ):
        assert required in command
    assert "Restart" not in unit["Service"]
    assert "OnFailure" not in unit["Unit"]
    assert "Install" not in unit


def test_image_build_installs_the_distribution_and_static_unit() -> None:
    """Repository success shall include image wiring, not source-tree imports."""
    postinst = (REPO_ROOT / "os/image/mkosi.postinst").read_text(encoding="utf-8")

    assert "python3 -m pip install" in postinst
    assert "--no-build-isolation" in postinst
    assert "--no-deps" in postinst
    assert '"$SRCDIR"' in postinst
    assert "mule-runtime.service" in postinst


def test_module_main_exits_with_renderer_status(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The executable module shall pass its arguments and exit status through."""
    import mule.configuration

    seen: list[str] = []

    def fake_main(arguments: list[str]) -> int:
        seen.extend(arguments)
        return 7

    monkeypatch.setattr(mule.configuration, "main", fake_main)
    monkeypatch.setattr(sys, "argv", ["mule", "--fixture"])

    try:
        runpy.run_module("mule.__main__", run_name="__main__")
    except SystemExit as exc:
        assert exc.code == 7
    else:
        raise AssertionError("mule.__main__ did not exit")
    assert seen == ["--fixture"]
