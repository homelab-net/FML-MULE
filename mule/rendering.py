"""Render the decided part of the EUD access-point configuration.

`FML-ADR-083` makes the MULE runtime a native oneshot configuration renderer.
This module answers one question: *given resolved parameters, a node's interface
names, and the current onboarding posture, what hostapd configuration does the
decided, sourced surface produce right now?*

It renders **only** what the program has actually decided and sourced:

- the radio block, from `regions/<id>/profile.yml` via `resolve()` -- band,
  channel, DFS, and the ISO 3166 `country_code` the Owner sourced (US);
- operational client isolation off (`FML-ADR-057`);
- the temporary onboarding BSS, isolated and enrollment-only, offered only while
  `mule.onboarding.decide()` returns `QUARANTINED` (`FML-ADR-084`).

It deliberately renders **nothing** that sits on an open trade, and marks each
omission in the output with the trade that gates it:

- the WPA security block and the passphrase source -- `TBR-SEC-01` (which owns
  the auth mechanism; the passphrase never enters the repository or the
  parameter document, `SECURITY.md`);
- DHCP/DNS and the address plan -- `TBR-NET-01`;
- the physical/virtual multi-BSS shape and the bridge -- `TBR-LINUX-01`.

Because the security block is intentionally absent, **the rendered file is not a
bootable hostapd configuration**; it is a `SIMULATED` partial render of the
decided surface, exercised by the digital twin and by the Pi bring-up execution
card, and is not wired into the boot oneshot. Interface names come from the node
descriptor; a name that is still `TBD` fails closed rather than being invented
(`TBR-LINUX-01`).
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .onboarding import OnboardingDecision, OnboardingState

TBD = "TBD"

#: The lowest channel number that belongs to the 5 GHz band. Channels 1-14 are
#: 2.4 GHz; 5 GHz channel numbering starts at 32. hostapd(8) hw_mode: "a" =
#: IEEE 802.11a (5 GHz), "g" = IEEE 802.11g (2.4 GHz).
_FIVE_GHZ_MIN_CHANNEL = 32


class RenderError(Exception):
    """A required value for the decided render surface is missing or TBD.

    Raised rather than emitting an invented interface name, SSID, or radio value
    -- the same fail-closed posture the rest of the runtime holds.
    """


def _require(value: Any, what: str) -> Any:  # noqa: ANN401
    """Return a present, non-TBD value, or fail closed naming what is missing."""
    if value is None or (isinstance(value, str) and value.strip() == TBD):
        message = f"cannot render: {what} is unset or TBD"
        raise RenderError(message)
    return value


def _require_interface(interfaces: Mapping[str, str], role: str) -> str:
    """Return the concrete interface name for a role, or fail closed.

    Names are `TBD` in `nodes/mule-v001/node.yml` until the prototype is
    assembled (`TBR-LINUX-01`); inventing one is the failure this prevents.
    """
    return _require(interfaces.get(role), f"interface {role!r}")


def _require_ssid(value: Any, what: str) -> str:  # noqa: ANN401
    """Return a present SSID with no control character, or fail closed.

    A hostapd directive cannot span lines, so a newline (or any control char) in
    an SSID would inject a second directive. The mission schema forbids this at
    load (the primary [CI] control); this is defense-in-depth for any caller that
    bypasses the schema, e.g. a hand-built parameter document in a test.
    """
    ssid = _require(value, what)
    if any(ord(ch) < 0x20 or 0x7F <= ord(ch) <= 0x9F for ch in ssid):
        message = f"cannot render: {what} contains a control character"
        raise RenderError(message)
    return ssid


def _hw_mode(channel: int) -> str:
    """Map a channel to the hostapd hw_mode for its band."""
    return "a" if channel >= _FIVE_GHZ_MIN_CHANNEL else "g"


def render_hostapd(
    resolved: dict[str, Any],
    interfaces: Mapping[str, str],
    onboarding: OnboardingDecision,
) -> str:
    """Render the decided hostapd surface for the EUD access point.

    ``resolved`` is a parameter document from ``configuration.resolve()``.
    ``interfaces`` maps a role (``eud_ap``, ``onboarding_ap``) to a concrete
    device name. ``onboarding`` is the current posture from
    ``mule.onboarding.decide()`` -- injected, so this function is pure and the
    broadcast/closed branches are exercised through the real decision logic
    rather than a value assumed here.

    Raises ``RenderError`` if a required decided value is missing or TBD.
    """
    wifi = _require(resolved.get("wifi"), "wifi parameters")
    network = _require(resolved.get("network"), "network parameters")
    region = _require(resolved.get("region"), "region parameters")

    ap_iface = _require_interface(interfaces, "eud_ap")
    ssid = _require_ssid(
        network.get("ap_ssid"), "operational AP SSID (network.ap_ssid)"
    )
    country = _require(region.get("country_code"), "region.country_code")
    channel = int(_require(wifi.get("ap_channel"), "wifi.ap_channel"))
    dfs_required = bool(_require(wifi.get("dfs_required"), "wifi.dfs_required"))

    lines: list[str] = [
        "# hostapd -- MULE EUD access point (PARTIAL, SIMULATED render).",
        "# Rendered by mule/rendering.py from the resolved parameter document.",
        "# NOT A BOOTABLE CONFIG: the WPA security block is intentionally absent",
        "# (gated on TBR-SEC-01). Do not flash this file as-is.",
        "",
        "# --- Operational BSS (admitted EUDs) ---",
        f"interface={ap_iface}",
        f"ssid={ssid}",
        "# Radio block from regions/<id>/profile.yml (never literals here).",
        f"country_code={country}",
        # hostapd(8): "ieee80211d: Enable IEEE 802.11d. This advertises the
        # country_code and the set of allowed channels and transmit power
        # levels." Required for the country_code to take effect. Default 0.
        "ieee80211d=1",
        f"hw_mode={_hw_mode(channel)}",
        f"channel={channel}",
        # hostapd(8): "ieee80211h: Enable IEEE 802.11h ... DFS." Default 0. The
        # profile's dfs_required drives it; ch 149 (UNII-3) is non-DFS in US.
        f"ieee80211h={1 if dfs_required else 0}",
        # hostapd(8): "ap_isolate: ... default: 0 = disabled." FML-ADR-057 keeps
        # admitted EUDs able to reach each other for peer ATAK.
        "ap_isolate=0",
        "",
        "# --- WPA security block: GATED, not rendered ---",
        "# wpa/wpa_key_mgmt/rsn_pairwise/passphrase source are undecided",
        "# (gated on TBR-SEC-01). The passphrase never enters this repository or",
        "# the parameter document (SECURITY.md).",
        "",
        "# --- DHCP/DNS and addressing: GATED (TBR-NET-01), rendered elsewhere ---",
    ]

    lines.extend(_render_onboarding(resolved, interfaces, onboarding))
    return "\n".join(lines) + "\n"


def _render_onboarding(
    resolved: dict[str, Any],
    interfaces: Mapping[str, str],
    onboarding: OnboardingDecision,
) -> list[str]:
    """Render the onboarding BSS stanza, or a closed marker, per the decision.

    `FML-ADR-084`: the onboarding BSS is offered only while `decide()` returns
    QUARANTINED. When CLOSED the BSS is not emitted at all -- the fail-closed
    static posture -- with the decision's reason recorded as a comment.
    """
    out = ["", "# --- Onboarding BSS (FML-ADR-084) ---"]

    if onboarding.state is OnboardingState.CLOSED:
        out.append(f"# Not offered: onboarding is CLOSED ({onboarding.reason}).")
        return out

    # QUARANTINED: a separate, isolated, enrollment-only BSS is offered.
    onboarding_ref = _require(
        resolved.get("network", {}).get("onboarding"),
        "network.onboarding",
    )
    onboarding_ssid = _require_ssid(onboarding_ref.get("ssid"), "onboarding SSID")
    onboarding_iface = _require_interface(interfaces, "onboarding_ap")

    out.extend(
        [
            f"bss={onboarding_iface}",
            f"ssid={onboarding_ssid}",
            # hostapd(8) ignore_broadcast_ssid: "0 = disabled (broadcast SSID)".
            # decide() broadcasts only inside the active window.
            f"ignore_broadcast_ssid={0 if onboarding.broadcast_ssid else 2}",
            # Onboarding stations are isolated from each other (FML-ADR-084);
            # only the enrollment path is reachable (firewall, TBR-NET-01).
            f"ap_isolate={1 if onboarding.client_isolated else 0}",
            "# Credential is by reference only (TBR-SEC-01); not rendered here.",
        ]
    )
    return out
