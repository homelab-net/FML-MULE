"""Tests for `mule.capability`.

`FML-ADR-080` makes the per-peer tier a *ceiling* the passive signals do not rule
out, never an end-to-end promise, and requires `UNKNOWN` (cannot tell) to stay
distinct from `NONE` (shown unusable). These exercise each signal's ceiling, the
most-restrictive-wins rule, and the two non-tier answers.

The thresholds here are illustrative test values, not `TBR-RF-01`'s: the point is
the mapping logic, not the numbers, which the ADR keeps out of the code.
"""

from __future__ import annotations

from mule.capability import CapabilityPolicy, capability_tier

POLICY = CapabilityPolicy(
    video_min_mbps=5.0,
    voice_min_mbps=1.0,
    video_min_tq=200,
    voice_min_tq=100,
    unreachable_at_or_below_tq=0,
    video_max_hops=1,
    voice_max_hops=3,
)


# --- the two non-tier answers, and the LoRa plane ---------------------------


def test_lora_is_text_regardless_of_ip_signals() -> None:
    # A non-IP text plane; no IP-side number raises it above TEXT (FML-ADR-026).
    assert capability_tier("lora", 100.0, 255, 1, POLICY) == "TEXT"


def test_measured_dead_tq_is_none() -> None:
    assert capability_tier("wifi_mesh", None, 0, None, POLICY) == "NONE"


def test_no_signal_is_unknown_not_none() -> None:
    # Nothing readable has not shown the link is down; cannot tell says so.
    assert capability_tier("wifi_mesh", None, None, None, POLICY) == "UNKNOWN"


def test_no_signal_and_unknown_bearer_is_unknown() -> None:
    assert capability_tier(None, None, None, None, POLICY) == "UNKNOWN"


# --- each signal's ceiling, in isolation ------------------------------------


def test_bitrate_ceiling_video() -> None:
    assert capability_tier("wifi_mesh", 10.0, None, None, POLICY) == "VIDEO"


def test_bitrate_ceiling_video_is_inclusive_at_the_floor() -> None:
    # At exactly the floor the tier is not ruled out: the comparison is >=.
    assert capability_tier("wifi_mesh", 5.0, None, None, POLICY) == "VIDEO"


def test_bitrate_ceiling_voice() -> None:
    assert capability_tier("wifi_mesh", 2.0, None, None, POLICY) == "VOICE"


def test_bitrate_ceiling_text() -> None:
    assert capability_tier("wifi_mesh", 0.5, None, None, POLICY) == "TEXT"


def test_tq_ceiling_video() -> None:
    assert capability_tier("wifi_mesh", None, 255, None, POLICY) == "VIDEO"


def test_tq_ceiling_voice() -> None:
    assert capability_tier("wifi_mesh", None, 150, None, POLICY) == "VOICE"


def test_tq_ceiling_text() -> None:
    assert capability_tier("wifi_mesh", None, 50, None, POLICY) == "TEXT"


def test_hops_ceiling_video() -> None:
    assert capability_tier("wifi_mesh", None, None, 1, POLICY) == "VIDEO"


def test_hops_ceiling_voice() -> None:
    assert capability_tier("wifi_mesh", None, None, 2, POLICY) == "VOICE"


def test_hops_ceiling_text() -> None:
    assert capability_tier("wifi_mesh", None, None, 5, POLICY) == "TEXT"


# --- the ceiling is the most restrictive signal -----------------------------


def test_most_restrictive_signal_wins() -> None:
    # PHY ceiling and hop count would allow VIDEO; loss (TQ) caps it at VOICE.
    assert capability_tier("wifi_mesh", 100.0, 150, 1, POLICY) == "VOICE"
