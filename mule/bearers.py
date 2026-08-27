"""Which radios a node can have, and which ones it needs.

A **bearer** is one radio function: a way the node carries traffic. This module
holds the list of them and the two judgements about that list which more than
one part of the node needs.

It decides nothing about radio hardware. It says which radio *functions* exist
by name, which ones the node cannot do its job without, and which ones carry
traffic to other nodes rather than to a user's phone or tablet.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Literal

#: The radio functions a node may carry. `FML-ADR-045` keeps the end user
#: access point and the inter-node mesh as separate functions whether or not
#: they end up sharing one physical radio.
Bearer = Literal["halow", "wifi_mesh", "wifi_ap", "lora"]

#: Bearers without which the node cannot do its job. CONOPS section 82 puts
#: "Connect approved EUD" between power on and everything after it: with no
#: access point there is no user-facing node, however healthy the rest is.
#:
#: Named here rather than written into a condition somewhere, so a reader can
#: see what the node treats as essential, and so it can change when a mission
#: profile eventually says otherwise.
REQUIRED_BEARERS: tuple[Bearer, ...] = ("wifi_ap",)

#: Bearers that carry traffic between nodes, rather than serving end user
#: devices. Used to tell "the mesh is broken" apart from "this node was never
#: meant to mesh".
INTER_NODE_BEARERS: tuple[Bearer, ...] = ("halow", "wifi_mesh")


def missing_required(enumerated: Iterable[Bearer]) -> list[Bearer]:
    """List required bearers whose hardware is not there.

    `enumerated` is what the platform found: hardware present, driver attached.
    """
    present = set(enumerated)
    return [bearer for bearer in REQUIRED_BEARERS if bearer not in present]


def required_not_serving(associated: Iterable[Bearer]) -> list[Bearer]:
    """List required bearers that are present but have not formed a link.

    A fitted access point that is not yet serving is a different problem from
    an absent one, and an operator needs to be able to tell them apart.
    """
    serving = set(associated)
    return [bearer for bearer in REQUIRED_BEARERS if bearer not in serving]


def inter_node_present(enumerated: Iterable[Bearer]) -> list[Bearer]:
    """List the inter-node bearers this node actually has."""
    present = set(enumerated)
    return [bearer for bearer in INTER_NODE_BEARERS if bearer in present]
