"""Stand in for the two feed packages withdrawn from PyPI.

OpenTAKServer 1.7.13 pins ``adsbxcot==6.0.4`` and ``aiscot==7.0.10``. Both
projects were withdrawn from PyPI and their source repositories removed, so a
clean build can no longer resolve the release. Only the ADS-B and AIS feed jobs
use them. Those jobs pull internet data, sit outside this topology, and ship
paused. This writes an installed distribution for each, at the pinned version
with a ``+fml.absent`` local label, which satisfies the pin (PEP 440 ignores a
local label against a public specifier). Each module raises if called, so a
feed job enabled by mistake fails loudly instead of publishing nothing. Run it
before installing OpenTAKServer. It writes no upstream code.
"""

import sys
import sysconfig
from pathlib import Path

LABEL = "fml.absent"
MESSAGE = (
    "{name} was withdrawn from PyPI. This image installs a placeholder, so "
    "OpenTAKServer's {feed} feed job is unavailable. See "
    "services/tak/README.md."
)
PACKAGES = {
    "adsbxcot": ("6.0.4", "ADS-B", "adsbx_to_cot"),
    "aiscot": ("7.0.10", "AIS", "ais_to_cot"),
}


def module_source(name: str, feed: str, function: str) -> str:
    """Return a module whose one entry point refuses to run."""
    message = MESSAGE.format(name=name, feed=feed)
    return (
        f'"""Placeholder for the withdrawn {name} package."""\n\n'
        f"MESSAGE = {message!r}\n\n\n"
        f"def {function}(*args, **kwargs):\n"
        f'    """Refuse: the real package is not installed."""\n'
        "    raise RuntimeError(MESSAGE)\n"
    )


def metadata(name: str, version: str) -> str:
    """Return core metadata naming the placeholder and its local label."""
    return (
        "Metadata-Version: 2.1\n"
        f"Name: {name}\n"
        f"Version: {version}+{LABEL}\n"
        f"Summary: FML-MULE placeholder for the withdrawn {name} {version}\n"
    )


def install(site: Path) -> list[Path]:
    """Write each placeholder package and its dist-info into ``site``."""
    written = []
    for name, (version, feed, function) in PACKAGES.items():
        package = site / name
        info = site / f"{name}-{version}+{LABEL}.dist-info"
        if package.exists() or any(site.glob(f"{name}-*.dist-info")):
            raise FileExistsError(f"{name} is already installed in {site}")
        package.mkdir()
        info.mkdir()
        files = {
            package / "__init__.py": module_source(name, feed, function),
            info / "METADATA": metadata(name, version),
            info / "INSTALLER": "fml-absent-feed-packages\n",
            info / "top_level.txt": f"{name}\n",
        }
        for path, text in files.items():
            path.write_text(text, encoding="utf-8")
        record = "".join(f"{p.relative_to(site).as_posix()},,\n" for p in files)
        record += f"{(info / 'RECORD').relative_to(site).as_posix()},,\n"
        (info / "RECORD").write_text(record, encoding="utf-8")
        written.extend([package, info])
    return written


def main() -> None:
    """Install the placeholders into this interpreter's site-packages."""
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    install(target or Path(sysconfig.get_paths()["purelib"]))


if __name__ == "__main__":
    main()
