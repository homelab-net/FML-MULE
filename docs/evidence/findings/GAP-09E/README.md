# GAP-09E evidence

This directory records the AP-only network-rendering decision (hostapd, DHCP/DNS,
host-network) for the v0.0.1 vertical slice.

State: OPEN -- owner decision approved on 2026-09-25 and recorded in
`FML-ADR-084`. Onboarding uses a separate isolated, enrollment-only BSS that
broadcasts during its mission-supplied credential window and hides/fails closed
at expiry or on untrusted time. The operational BSS remains non-isolated under
`FML-ADR-057`. Rendering and EUD evidence remain.

| Artifact | What it records |
| --- | --- |
| `decision-packet.md` | The approved two-BSS boundary, time gate, credential-reference rule, failure behavior and remaining rendering work. |
