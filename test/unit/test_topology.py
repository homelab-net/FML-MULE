"""The static topology check, including the mutations that must fail."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType


def _load() -> ModuleType:
    path = Path(__file__).resolve().parents[2] / "test" / "topology" / "validate.py"
    spec = importlib.util.spec_from_file_location("topology_validate", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_tak_topology_holds_and_mutations_fail() -> None:
    validator = _load()
    assert validator.main() == 0


def test_cold_start_starts_at_the_repository_root() -> None:
    root = Path(__file__).resolve().parents[2]
    script = (root / "test/topology/cases/tak/cold-start.sh").read_text()
    assert '"$here/../../../.."' in script
    assert "exec sudo sh" in script
    assert "services/tak/Containerfile" in script
    assert 'systemctl start "user@${account_uid}.service"' in script
    assert "systemctl --user start opentakserver.target" in script
    assert "env -i" in script
    assert 'XDG_CONFIG_HOME="$home/.config"' in script
    assert 'cd "$home"' in script
    assert 'chmod -R go-w "$home/.config"' in script
    assert "systemctl --user set-environment" in script
    assert "account-home.conf" in script
    assert "--user 0" not in script
    assert ".erlang.cookie" not in script
    run_lines = [line for line in script.splitlines() if "podman run" in line]
    assert run_lines
    for line in run_lines:
        for name in (
            "postgresql",
            "rabbitmq",
            "opentakserver",
            "eud-handler",
            "cot-parser",
        ):
            assert name not in line


def test_static_podman_may_create_a_user_namespace() -> None:
    root = Path(__file__).resolve().parents[2]
    script = (root / "test/topology/ensure-podman.sh").read_text()
    assert "apparmor_restrict_unprivileged_userns" in script
    assert "ln -sfn /usr/local/bin/crun /usr/bin/crun" in script
    assert "/usr/lib/systemd/user-generators/podman-user-generator" in script


def test_quadlet_check_reads_generated_service_names() -> None:
    root = Path(__file__).resolve().parents[2]
    script = (root / "test/topology/quadlet-dry-run.sh").read_text()
    assert "QUADLET_UNIT_DIRS" in script
    assert "ots-network.service" in script
    assert "grep -q 'ots.network'" not in script
