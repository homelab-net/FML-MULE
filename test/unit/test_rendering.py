"""Unit tests for mule/rendering.py.

The renderer translates a resolved parameter document + the current onboarding
posture into the decided hostapd surface. Its contract is: emit only decided,
sourced values; fail closed on anything missing or TBD; and never emit a secret.

The onboarding *decision* is injected here (its own logic is tested in
test_onboarding.py); the digital-twin scenario drives it through a real clock.
"""

from __future__ import annotations

import pytest

from mule import rendering as r
from mule.onboarding import OnboardingDecision, OnboardingState


def _resolved(
    *,
    country_code: str | None = "US",
    ap_channel: int = 149,
    dfs_required: bool = False,
    ap_ssid: str | None = "example-ap",
    onboarding_ssid: str | None = "example-onboard",
) -> dict:
    """Build a minimal resolved parameter document for the AP-only surface."""
    region: dict = {"id": "xx", "regulator": "None", "status": "FIXTURE"}
    if country_code is not None:
        region["country_code"] = country_code
    network: dict = {}
    if ap_ssid is not None:
        network["ap_ssid"] = ap_ssid
    if onboarding_ssid is not None:
        network["onboarding"] = {
            "ssid": onboarding_ssid,
            "credential_ref": "ref-not-material",
            "expires_at": "2026-12-31T00:00:00Z",
        }
    return {
        "region": region,
        "network": network,
        "wifi": {
            "ap_channel": ap_channel,
            "permitted_bands": ["2.4GHz", "5GHz"],
            "dfs_required": dfs_required,
            "ap_max_eirp_dbm": 36,
        },
    }


IFACES = {"eud_ap": "wlan0", "onboarding_ap": "wlan0_1"}


def _quarantined(*, broadcast: bool = True) -> OnboardingDecision:
    return OnboardingDecision(
        state=OnboardingState.QUARANTINED,
        broadcast_ssid=broadcast,
        accepting_associations=True,
        client_isolated=True,
        enrollment_only=True,
        reason=None,
    )


def _closed(reason: str = "onboarding credential expired") -> OnboardingDecision:
    return OnboardingDecision(
        state=OnboardingState.CLOSED,
        broadcast_ssid=False,
        accepting_associations=False,
        client_isolated=True,
        enrollment_only=True,
        reason=reason,
    )


# --- the decided operational block ---------------------------------------


def test_operational_block_renders_the_decided_radio_and_isolation() -> None:
    out = r.render_hostapd(_resolved(), IFACES, _quarantined())

    assert "interface=wlan0" in out
    assert "ssid=example-ap" in out
    assert "country_code=US" in out
    assert "ieee80211d=1" in out
    assert "hw_mode=a" in out  # 5 GHz
    assert "channel=149" in out
    assert "ieee80211h=0" in out  # ch 149 is non-DFS
    assert "ap_isolate=0" in out  # FML-ADR-057, operational BSS not isolated


def test_hw_mode_is_g_for_a_24ghz_channel() -> None:
    out = r.render_hostapd(_resolved(ap_channel=6), IFACES, _quarantined())

    assert "hw_mode=g" in out
    assert "channel=6" in out


def test_dfs_channel_enables_ieee80211h() -> None:
    out = r.render_hostapd(_resolved(dfs_required=True), IFACES, _quarantined())

    assert "ieee80211h=1" in out


# --- the onboarding BSS ---------------------------------------------------


def test_onboarding_bss_is_offered_and_isolated_when_quarantined() -> None:
    out = r.render_hostapd(_resolved(), IFACES, _quarantined())

    assert "bss=wlan0_1" in out
    assert "ssid=example-onboard" in out
    assert "ignore_broadcast_ssid=0" in out  # broadcast in the active window
    assert "ap_isolate=1" in out  # onboarding stations isolated


def test_onboarding_bss_is_hidden_when_not_broadcasting() -> None:
    # decide() never returns QUARANTINED without broadcast, but the renderer must
    # still hide rather than broadcast if it ever does.
    out = r.render_hostapd(_resolved(), IFACES, _quarantined(broadcast=False))

    assert "bss=wlan0_1" in out
    assert "ignore_broadcast_ssid=2" in out


def test_onboarding_bss_is_absent_when_closed() -> None:
    out = r.render_hostapd(
        _resolved(), IFACES, _closed("onboarding credential expired")
    )

    assert "bss=" not in out
    assert "CLOSED" in out
    assert "onboarding credential expired" in out


# --- the security boundary -----------------------------------------------


def test_no_secret_is_ever_rendered() -> None:
    out = r.render_hostapd(_resolved(), IFACES, _quarantined())

    lowered = out.lower()
    assert "wpa_passphrase" not in lowered
    assert "wpa_psk" not in lowered
    assert "ref-not-material" not in out  # the credential_ref is not emitted
    assert "TBR-SEC-01" in out  # the gate is named instead


# --- fail closed ----------------------------------------------------------


def test_a_missing_operational_interface_fails_closed() -> None:
    with pytest.raises(r.RenderError, match="eud_ap"):
        r.render_hostapd(_resolved(), {"onboarding_ap": "wlan0_1"}, _quarantined())


def test_a_tbd_interface_fails_closed() -> None:
    with pytest.raises(r.RenderError, match="eud_ap"):
        r.render_hostapd(_resolved(), {"eud_ap": "TBD"}, _quarantined())


def test_a_missing_onboarding_interface_fails_closed() -> None:
    with pytest.raises(r.RenderError, match="onboarding_ap"):
        r.render_hostapd(_resolved(), {"eud_ap": "wlan0"}, _quarantined())


def test_a_missing_ssid_fails_closed() -> None:
    with pytest.raises(r.RenderError, match="SSID"):
        r.render_hostapd(_resolved(ap_ssid=None), IFACES, _quarantined())


def test_a_missing_country_code_fails_closed() -> None:
    with pytest.raises(r.RenderError, match="country_code"):
        r.render_hostapd(_resolved(country_code=None), IFACES, _quarantined())


def test_a_control_char_in_the_operational_ssid_fails_closed() -> None:
    # A newline would inject a second hostapd directive. Defense-in-depth for a
    # caller that bypasses the mission schema (which is the primary control).
    with pytest.raises(r.RenderError, match="control character"):
        r.render_hostapd(_resolved(ap_ssid="bad\nssid"), IFACES, _quarantined())


def test_a_control_char_in_the_onboarding_ssid_fails_closed() -> None:
    with pytest.raises(r.RenderError, match="control character"):
        r.render_hostapd(
            _resolved(onboarding_ssid="bad\nonboard"), IFACES, _quarantined()
        )


def test_a_missing_onboarding_block_fails_closed_when_quarantined() -> None:
    with pytest.raises(r.RenderError, match=r"network\.onboarding"):
        r.render_hostapd(_resolved(onboarding_ssid=None), IFACES, _quarantined())


def test_a_missing_onboarding_ssid_fails_closed() -> None:
    resolved = _resolved()
    del resolved["network"]["onboarding"]["ssid"]
    with pytest.raises(r.RenderError, match="onboarding SSID"):
        r.render_hostapd(resolved, IFACES, _quarantined())


@pytest.mark.parametrize("block", ["wifi", "network", "region"])
def test_a_missing_top_level_block_fails_closed(block: str) -> None:
    resolved = _resolved()
    del resolved[block]
    with pytest.raises(r.RenderError, match=block):
        r.render_hostapd(resolved, IFACES, _quarantined())
