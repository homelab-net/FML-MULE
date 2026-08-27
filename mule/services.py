"""What services a node offers, and the name a user reaches each one by.

A **service** is something a user opens: a map, a form, a file share. Which
ones a node offers is a property of the deployment, carried in the mission
configuration package, never a list written into the node. A deployment that
enables none gets none, and that is a valid node rather than a broken one.

`FML-ADR-031`: users reach stable logical names, not physical hosts. Whoever is
actually running a service can change without the user being told a new address.
"""

from __future__ import annotations

from collections.abc import Iterable


def identity(name: str, local_domain: str | None) -> str:
    """Compose the name a user reaches one service by.

    The domain comes from the mission package. There is deliberately no default:
    a domain fixed across every deployment makes a collision certain the first
    time two teams meet at an incident, so a package supplying none yields a
    bare name rather than an invented suffix.
    """
    return f"{name}.{local_domain}" if local_domain else name


def identities(enabled: Iterable[str], local_domain: str | None) -> list[str]:
    """Compose the reachable name for every service the deployment enabled."""
    return [identity(name, local_domain) for name in enabled]
