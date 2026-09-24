"""The TAK service units share one data folder and do not invent recovery.

The five runtime proofs in Roadmap 4.1 are not these tests. Nothing here
starts a container.
"""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
QUADLETS = REPO / "services" / "quadlets"
OTS_UNITS = ("opentakserver", "eud-handler", "cot-parser")
DATA = "Volume=/var/lib/fml/ots:/var/lib/opentakserver:Z"
BASE = (
    "docker.io/library/python@sha256:"
    "dbbe4ceb97851e2e5fa83798b239811f871cb743b259ba3563737349f6bcfaa0"
)


def _text(name: str) -> str:
    return (QUADLETS / f"{name}.container.disabled").read_text(encoding="utf-8")


def _assignments(text: str) -> list[str]:
    return [line for line in text.splitlines() if not line.startswith("#")]


def test_three_processes_share_the_data_folder() -> None:
    for name in OTS_UNITS:
        text = _text(name)
        assert DATA in text
        assert "Environment=OTS_DATA_FOLDER=/var/lib/opentakserver" in text
        assert not any(line.startswith("Restart=") for line in _assignments(text))
        assert "Image=TBD" in text


def test_workers_wait_for_the_api_database_and_broker() -> None:
    for name in ("eud-handler", "cot-parser"):
        text = _text(name)
        assert (
            "Requires=postgresql.service rabbitmq.service "
            "opentakserver.service"
        ) in text


def test_listener_is_the_client_port() -> None:
    assert "Exec=eud_handler" in _text("eud-handler")
    assert "PublishPort=8088:8088" in _text("eud-handler")
    assert "Exec=cot_parser" in _text("cot-parser")
    assert "Exec=opentakserver" in _text("opentakserver")


def test_dependencies_use_the_recorded_digests() -> None:
    postgres = _text("postgresql")
    rabbit = _text("rabbitmq")
    assert (
        "docker.io/library/postgres@sha256:"
        "485935f94cc7165afa896978809c37b592dc07f0a37d2c8f645f12412d0212c8"
        in postgres
    )
    assert (
        "docker.io/library/rabbitmq@sha256:"
        "9cfb7e92ae7d296aec4d1ae799e431209f7ed57d55f9c929d95667d0ccf1c920"
        in rabbit
    )
    assert not any(line.startswith("Restart=") for line in _assignments(postgres))
    assert not any(line.startswith("Restart=") for line in _assignments(rabbit))


def test_no_credential_is_written_into_a_unit() -> None:
    banned = ("password", "guest", "atakatak", "administrator")
    for path in QUADLETS.glob("*.container.disabled"):
        lowered = path.read_text(encoding="utf-8").lower()
        for word in banned:
            assert word not in lowered, path.name


def test_build_pins_the_release_and_the_base() -> None:
    text = (REPO / "services" / "tak" / "Containerfile").read_text(encoding="utf-8")
    assert f"FROM {BASE}" in text
    assert "opentakserver==1.7.13" in text
    assert "git+" not in text
