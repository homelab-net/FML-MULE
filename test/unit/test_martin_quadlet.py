"""The selected v0.0.1 map service is one loadable, read-only unit."""

from __future__ import annotations

from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
CATALOG = REPO / "services" / "catalog" / "catalog.yml"
UNIT = REPO / "services" / "quadlets" / "martin.container"
IMAGE = (
    "ghcr.io/maplibre/martin@sha256:"
    "59902019bf9038926ff0c71174237d6852e64c457830a6349abe7090be8818ca"
)
STORE = "/var/lib/fml/maps/mission.mbtiles"


def _assignments(text: str) -> list[str]:
    return [line for line in text.splitlines() if line and not line.startswith("#")]


def test_martin_is_the_enabled_milestone_service() -> None:
    """The owner-selected contract names the immutable loadable unit."""
    catalog = yaml.safe_load(CATALOG.read_text(encoding="utf-8"))
    martin = next(entry for entry in catalog["services"] if entry["name"] == "martin")

    assert martin["enabled"] is True
    assert martin["unit"] == "martin.container"
    assert martin["image"] == IMAGE
    assert martin["rootless"] is True


def test_martin_unit_keeps_the_store_and_backend_private() -> None:
    """The service reads one store and exposes only a loopback backend."""
    assignments = _assignments(UNIT.read_text(encoding="utf-8"))

    assert f"Image={IMAGE}" in assignments
    assert "PublishPort=127.0.0.1:3000:3000" in assignments
    assert f"Volume={STORE}:/data/mission.mbtiles:ro" in assignments
    assert "Exec=/data/mission.mbtiles" in assignments
    assert "ReadOnly=true" in assignments
    assert f"ExecStartPre=/usr/bin/test -r {STORE}" in assignments
    assert not any(line.startswith("Restart=") for line in assignments)
    assert not any(line.startswith("AutoUpdate=") for line in assignments)
