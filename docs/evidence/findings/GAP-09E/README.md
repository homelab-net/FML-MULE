# GAP-09E evidence

This directory records the AP-only network-rendering decision (hostapd, DHCP/DNS,
host-network) for the v0.0.1 vertical slice.

State: OPEN -- owner decision approved on 2026-09-25 and recorded in
`FML-ADR-084`. Onboarding uses a separate isolated, enrollment-only BSS that
broadcasts during its mission-supplied credential window and hides/fails closed
at expiry or on untrusted time. The operational BSS remains non-isolated under
`FML-ADR-057`. Rendering and EUD evidence remain.

Partial render (2026-09-25, `SIMULATED`): `mule/rendering.py` renders only the
decided, sourced surface -- client isolation, onboarding broadcast/hidden
posture, the mission SSID, and the hostapd radio block (`country_code: US` plus
the `us-915` band/channel/DFS). DHCP/addressing (`TBR-NET-01`), credentials
(`TBR-SEC-01`) and multi-BSS/interface names (`TBR-LINUX-01`) stay gated and are
not rendered. The renderer is not wired into the boot oneshot. Multi-BSS on the
real radio is proven only by the Stage-9 Pi exercise (execution card below).

| Artifact | What it records |
| --- | --- |
| `decision-packet.md` | The approved two-BSS boundary, time gate, credential-reference rule, failure behavior and remaining rendering work. |
| `2026-09-27-pi-ap-bringup-execution-card.md` | The Pi bring-up checklist: the M1 dry run that captures the AP-mode / regdomain / multi-BSS evidence gating the render. |
