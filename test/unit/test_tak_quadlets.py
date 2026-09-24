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
DEPS = "Requires=ots-network.service postgresql.service rabbitmq.service"
BASE = (
    "docker.io/library/python@sha256:"
    "dbbe4ceb97851e2e5fa83798b239811f871cb743b259ba3563737349f6bcfaa0"
)
BUNDLE = (
    "opentakserver.target.disabled",
    "ots.network.disabled",
    "postgresql.container.disabled",
    "rabbitmq.container.disabled",
    "opentakserver.container.disabled",
    "eud-handler.container.disabled",
    "cot-parser.container.disabled",
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
    assert owned["unit"] == "TBD"
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


def test_workers_depend_on_the_database_and_the_broker_only() -> None:
    for name in ("eud-handler", "cot-parser"):
        text = _unit(name)
        assert DEPS in text
        assert "opentakserver.service" not in text


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


def test_mesh_interface_ordering_stays_unnamed() -> None:
    text = _text("opentakserver.target.disabled")
    assert "systemd-networkd-wait-online@TBD.service" in text
    assert not any("network-online.target" in line for line in _assignments(text))
    assert "Wants=ots-network.service postgresql.service rabbitmq.service " in text
    assert "opentakserver.service eud-handler.service cot-parser.service" in text


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
    assert "git+" not in text
