"""The TAK capability owns its internal units and does not publish them.

The five runtime proofs in Roadmap 4.1 are not these tests. Nothing here
starts a container.
"""

from __future__ import annotations

from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
QUADLETS = REPO / "services" / "quadlets"
APP_UNITS = ("opentakserver", "eud-handler", "cot-parser")
DEPENDENCIES = ("postgresql", "rabbitmq")
CONTAINERS = APP_UNITS + DEPENDENCIES
DATA = "Volume=/var/lib/fml/ots:/var/lib/opentakserver:Z"
MESH = "systemd-networkd-wait-online@TBD.service"
DEPS = f"Requires={MESH} ots-network.service postgresql.service rabbitmq.service"
BASE = (
    "docker.io/library/python@sha256:"
    "dbbe4ceb97851e2e5fa83798b239811f871cb743b259ba3563737349f6bcfaa0"
)
BUNDLE = (
    "ots.network",
    "postgresql.container",
    "rabbitmq.container",
    "opentakserver.container",
    "eud-handler.container",
    "cot-parser.container",
)


def _text(name: str) -> str:
    return (QUADLETS / name).read_text(encoding="utf-8")


def _unit(name: str) -> str:
    return _text(f"{name}.container.disabled")


def _assignments(text: str) -> list[str]:
    return [line for line in text.splitlines() if not line.startswith("#")]


def test_one_capability_owns_the_internal_units() -> None:
    catalog = yaml.safe_load(
        (REPO / "services" / "catalog" / "catalog.yml").read_text()
    )
    names = [entry["name"] for entry in catalog["services"]]
    assert names == ["opentakserver", "martin"]
    owned = catalog["services"][0]
    assert owned["enabled"] is False
    assert owned["unit"] == "opentakserver.target"
    assert owned["image"] == "TBD"
    assert owned["bundle"] == list(BUNDLE)
    assert "bundle" not in catalog["services"][1]


def test_three_processes_share_the_data_folder() -> None:
    for name in APP_UNITS:
        text = _unit(name)
        assert DATA in text
        assert "Environment=OTS_DATA_FOLDER=/var/lib/opentakserver" in text
        assert not any(line.startswith("Restart=") for line in _assignments(text))
        assert "Image=TBD" in text
        assert "Environment=OTS_MEDIAMTX_ENABLE=false" in text


def test_workers_wait_for_a_ready_api_without_requiring_it() -> None:
    for name in ("eud-handler", "cot-parser"):
        text = _unit(name)
        assert DEPS in text
        requires = [line for line in _assignments(text) if line.startswith("Requires=")]
        after = [line for line in _assignments(text) if line.startswith("After=")]
        assert all("opentakserver.service" not in line for line in requires)
        assert any("opentakserver.service" in line for line in after)


def test_backend_ports_stay_off_the_host() -> None:
    for name in CONTAINERS:
        assignments = _assignments(_unit(name))
        assert not any(line.startswith("PublishPort=") for line in assignments)
        assert not any("network-online.target" in line for line in assignments)
        assert not any(
            line.strip() in {"Network=host", "--network=host"} for line in assignments
        )
        assert "--network host" not in "\n".join(assignments)
        assert "Network=ots.network" in assignments
    api = _unit("opentakserver")
    listener = _unit("eud-handler")
    assert "Environment=OTS_LISTENER_ADDRESS=0.0.0.0" in api
    assert "Environment=OTS_STREAMING_INTERFACE=0.0.0.0" in listener
    assert "PublishPort=8081:8081" not in api
    assert "PublishPort=8088:8088" not in listener


def test_internal_network_names_the_endpoints() -> None:
    network = _text("ots.network.disabled")
    assert "Internal=true" in _assignments(network)
    assert "Network=host" not in network
    for name in APP_UNITS:
        text = _unit(name)
        assert "Environment=OTS_RABBITMQ_SERVER_ADDRESS=rabbitmq" in text
        assert "# SQLALCHEMY_DATABASE_URI host=postgresql" in text
        assert not any("127.0.0.1" in line for line in _assignments(text))
    assert "ContainerName=postgresql" in _unit("postgresql")
    assert "ContainerName=rabbitmq" in _unit("rabbitmq")


def test_mesh_gate_holds_the_members() -> None:
    target = _text("opentakserver.target.disabled")
    assert MESH not in target
    assert "After=ots-network.service postgresql.service rabbitmq.service " in target
    assert not any("network-online.target" in line for line in _assignments(target))
    members = (
        "ots.network.disabled",
        "postgresql.container.disabled",
        "rabbitmq.container.disabled",
        "opentakserver.container.disabled",
        "eud-handler.container.disabled",
        "cot-parser.container.disabled",
    )
    for name in members:
        assignments = _assignments(_text(name))
        assert any(
            line.startswith("Requires=") and MESH in line for line in assignments
        )
        assert any(line.startswith("After=") and MESH in line for line in assignments)


def test_dependencies_use_the_recorded_digests() -> None:
    postgres = _unit("postgresql")
    rabbit = _unit("rabbitmq")
    assert (
        "docker.io/library/postgres@sha256:"
        "485935f94cc7165afa896978809c37b592dc07f0a37d2c8f645f12412d0212c8" in postgres
    )
    assert (
        "docker.io/library/rabbitmq@sha256:"
        "9cfb7e92ae7d296aec4d1ae799e431209f7ed57d55f9c929d95667d0ccf1c920" in rabbit
    )
    assert not any(line.startswith("Restart=") for line in _assignments(postgres))
    assert not any(line.startswith("Restart=") for line in _assignments(rabbit))
    rabbit_assignments = _assignments(rabbit)
    assert not any(line.startswith("Volume=") for line in rabbit_assignments)
    assert not any(line.startswith("Tmpfs=") for line in rabbit_assignments)
    assert "/var/lib/fml/rabbitmq" not in rabbit


def test_no_credential_is_written_into_a_unit() -> None:
    banned = ("password", "guest", "atakatak", "administrator")
    for path in QUADLETS.glob("*"):
        if not path.is_file() or path.name == "README.md":
            continue
        lowered = path.read_text(encoding="utf-8").lower()
        for word in banned:
            assert word not in lowered, path.name


def test_build_pins_the_release_and_the_base() -> None:
    text = (REPO / "services" / "tak" / "Containerfile").read_text(encoding="utf-8")
    assert f"FROM {BASE}" in text
    assert "opentakserver==1.7.13" in text
    assert "COPY listen_ready.py /usr/local/bin/fml-listen-ready.py" in text
    assert "git+" not in text


def test_readiness_is_a_health_notification() -> None:
    probes = {
        "postgresql": "HealthCmd=pg_isready",
        "rabbitmq": "HealthCmd=rabbitmq-diagnostics -q ping",
        "opentakserver": "HealthCmd=python /usr/local/bin/fml-listen-ready.py 8081",
        "eud-handler": "HealthCmd=python /usr/local/bin/fml-listen-ready.py 8088",
    }
    for name, probe in probes.items():
        assignments = _assignments(_unit(name))
        assert probe in assignments
        assert "Notify=healthy" in assignments
        assert any(line.startswith("TimeoutStartSec=") for line in assignments)
    parser = _assignments(_unit("cot-parser"))
    assert "Notify=healthy" not in parser
    for name in DEPENDENCIES:
        assert "User=0" in _assignments(_unit(name))
