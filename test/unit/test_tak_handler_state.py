"""Exercise connection lifecycle, including dispatch during construction."""

import runpy
from pathlib import Path

import pytest

PATCH = runpy.run_path(
    Path(__file__).resolve().parents[2] / "services/tak/isolate_handler_state.py"
)["isolate_handler_state"]
# Minimal constructor/list fixture transcribed from OpenTAKServer 1.7.13,
# opentakserver/eud_handler/EudHandler.py, captured 2026-10-01. No traffic.
# Upstream tag object: 67903c26d95552738d85be4bc3c3ff3321378dbe.
# https://github.com/brian7704/OpenTAKServer/tree/1.7.13
SOURCE = """class Handler(Base):
    cached_messages = []
    bound_queues = []
    group_memberships = []

    def __init__(self, request: socket, client_address, server):
        super().__init__(request, client_address, server)
"""


class Base:
    """Model BaseRequestHandler dispatch before __init__ returns."""

    def __init__(self, request: object, client_address: str, server: object) -> None:
        """Populate bookkeeping as setup/handle would during construction."""
        self.cached_messages.append(request)
        self.bound_queues.append(client_address)
        self.group_memberships.append(server)


def handler(source: str) -> type:
    """Execute the transcribed constructor against the dispatching base."""
    namespace = {"Base": Base, "socket": object}
    exec(compile(source, "upstream-constructor-fixture", "exec"), namespace)  # noqa: S102
    return namespace["Handler"]


def test_connections_own_lists_before_setup_dispatch() -> None:
    cls = handler(PATCH(SOURCE))
    first, second = cls(object(), "first", object()), cls(object(), "second", object())
    for name in ("cached_messages", "bound_queues", "group_memberships"):
        left, right = getattr(first, name), getattr(second, name)
        assert left is not right
        assert len(left) == len(right) == 1
        left.clear()
        assert len(right) == 1


def test_unpatched_constructor_shares_connection_state() -> None:
    cls = handler(SOURCE)
    first, second = cls(object(), "first", object()), cls(object(), "second", object())
    assert first.bound_queues is second.bound_queues
    first.bound_queues.clear()
    assert not second.bound_queues


def test_patch_is_idempotent() -> None:
    patched = PATCH(SOURCE)
    assert PATCH(patched) == patched


def test_changed_upstream_constructor_is_rejected() -> None:
    with pytest.raises(ValueError, match="Unsupported upstream"):
        PATCH("class Handler: pass\n")


def test_ambiguous_upstream_constructor_is_rejected() -> None:
    with pytest.raises(ValueError, match="Unsupported upstream"):
        PATCH(SOURCE + SOURCE)
