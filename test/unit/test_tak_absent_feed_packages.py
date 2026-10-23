"""The withdrawn feed packages are replaced by placeholders that refuse."""

import importlib.metadata
import importlib.util
import runpy
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SCRIPT = runpy.run_path(str(REPO / "services/tak/absent_feed_packages.py"))
# OpenTAKServer 1.7.13's own pins, from its published requires_dist.
PINS = {"adsbxcot": "6.0.4", "aiscot": "7.0.10"}


def load(site: Path, name: str) -> object:
    """Import a placeholder module from ``site`` without touching sys.path."""
    spec = importlib.util.spec_from_file_location(name, site / name / "__init__.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_placeholders_carry_the_pinned_public_version(tmp_path: Path) -> None:
    SCRIPT["install"](tmp_path)
    found = {
        d.metadata["Name"]: d.version
        for d in importlib.metadata.distributions(path=[str(tmp_path)])
    }
    assert found == {name: f"{v}+fml.absent" for name, v in PINS.items()}


@pytest.mark.parametrize(
    ("name", "function"), [("adsbxcot", "adsbx_to_cot"), ("aiscot", "ais_to_cot")]
)
def test_the_entry_point_refuses(tmp_path: Path, name: str, function: str) -> None:
    SCRIPT["install"](tmp_path)
    with pytest.raises(RuntimeError, match="withdrawn from PyPI"):
        getattr(load(tmp_path, name), function)({"hex": "000000"}, None)


def test_record_lists_every_written_file(tmp_path: Path) -> None:
    SCRIPT["install"](tmp_path)
    listed = set()
    for info in tmp_path.glob("*.dist-info"):
        listed |= {row.split(",")[0] for row in (info / "RECORD").read_text().split()}
    on_disk = {p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob("*")}
    assert listed == {p for p in on_disk if (tmp_path / p).is_file()}


def test_an_existing_install_is_not_overwritten(tmp_path: Path) -> None:
    (tmp_path / "adsbxcot-6.0.4.dist-info").mkdir()
    with pytest.raises(FileExistsError):
        SCRIPT["install"](tmp_path)


def test_containerfile_installs_placeholders_before_the_server() -> None:
    lines = (REPO / "services/tak/Containerfile").read_text().splitlines()
    placeholder = lines.index("RUN python /usr/local/bin/fml-absent-feed-packages.py")
    server = lines.index('RUN pip install --no-cache-dir "opentakserver==1.7.13"')
    assert placeholder < server
