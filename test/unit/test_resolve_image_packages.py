"""Tests for the image package resolver's profile selection (FML-ADR-088).

The resolver talks to APT against the dated snapshot, which these tests cannot
reach. They cover what the arm64 profile changes and what it must not: where a
resolution reads its inputs, which architecture APT is told, and which
architecture a package record may carry.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
RESOLVER_PATH = REPO_ROOT / "tools" / "resolve-image-packages.py"


@pytest.fixture
def resolver() -> ModuleType:
    """Import the hyphenated resolver script as a module."""
    spec = importlib.util.spec_from_file_location("resolve_images", RESOLVER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_the_base_image_keeps_its_amd64_inputs(resolver: ModuleType) -> None:
    """Without a profile, nothing about the x86-64 resolution moves."""
    selected = resolver.plan(REPO_ROOT, None)

    assert selected.architecture == "amd64"
    assert selected.roles == ("target", "tools-tree")
    assert selected.manifest == REPO_ROOT / "os/image/manifest"
    assert selected.target_sources == (
        REPO_ROOT / "os/image/sandbox-target/etc/apt/sources.list.d/mkosi.sources"
    )


def test_the_pi_profile_resolves_only_its_arm64_target(resolver: ModuleType) -> None:
    """The profile has its own sources and manifest; the tools tree is shared."""
    selected = resolver.plan(REPO_ROOT, "pi4b-arm64")

    assert selected.architecture == "arm64"
    assert selected.roles == ("target",)
    assert selected.manifest == REPO_ROOT / "os/image/manifest/pi4b-arm64"
    assert selected.target_sources == (
        REPO_ROOT
        / "os/image/mkosi.profiles/pi4b-arm64/sandbox-target/etc/apt/sources.list.d"
        / "mkosi.sources"
    )


def test_an_unknown_profile_is_refused(resolver: ModuleType) -> None:
    """A misspelt profile must not fall back to the x86-64 inputs."""
    with pytest.raises(ValueError, match="unknown image profile"):
        resolver.plan(REPO_ROOT, "pi4-arm64")


def test_apt_is_told_the_profile_architecture(
    resolver: ModuleType, tmp_path: Path
) -> None:
    """APT resolves for the architecture it is given, not the host's."""
    sources = tmp_path / "mkosi.sources"
    sources.write_text(
        "Signed-By: /usr/share/keyrings/debian-archive-keyring.gpg\n",
        encoding="utf-8",
    )
    options = resolver._apt_options(
        tmp_path / "work", sources, tmp_path / "keyring.gpg", "arm64"
    )

    assert "APT::Architecture=arm64" in options
    assert "APT::Architectures=arm64" in options
    assert not any("amd64" in option for option in options)


def _show(architecture: str) -> str:
    return (
        "Package: udev\n"
        "Version: 257.13-1~deb13u1\n"
        f"Architecture: {architecture}\n"
        "Source: systemd\n"
        "Filename: pool/main/s/systemd/udev.deb\n"
        f"SHA256: {'a' * 64}\n"
    )


def test_an_arm64_record_is_accepted_for_the_arm64_profile(
    resolver: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The record filter follows the profile architecture."""

    def fake_run(command: list[str]) -> str:
        if "show" in command:
            return _show("arm64")
        return "  257.13-1~deb13u1 500\n     500 https://x trixie/main arm64\n"

    monkeypatch.setattr(resolver, "_run", fake_run)
    record = resolver._metadata("udev", "257.13-1~deb13u1", [], "arm64")

    assert record["architecture"] == "arm64"


def test_an_amd64_record_is_refused_for_the_arm64_profile(
    resolver: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An amd64 package cannot enter the arm64 lock."""
    monkeypatch.setattr(resolver, "_run", lambda _command: _show("amd64"))

    with pytest.raises(RuntimeError, match="APT metadata missing"):
        resolver._metadata("udev", "257.13-1~deb13u1", [], "arm64")
