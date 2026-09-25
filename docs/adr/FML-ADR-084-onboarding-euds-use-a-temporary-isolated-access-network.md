---
id: FML-ADR-084
title: Onboarding EUDs use a temporary isolated access network
status: SELECTED
date: 2026-09-25
supersedes: none
superseded-by: none
trades: [TBR-ID-01, TBR-TIME-01, TBR-SEC-01, TBR-LINUX-01]
verification: Stage 9
---

# FML-ADR-084 Onboarding EUDs use a temporary isolated access network

## Context

Production EUD admission targets per-device EAP-TLS (`FML-ADR-038`), which
creates a bootstrap problem: a device without a valid credential cannot reach
the endpoint that issues one. A reusable WLAN password is not sufficient
authorization, and placing an onboarding device directly on the operational
peer domain would bypass the admission boundary.

The operational EUD BSS cannot simply enable station isolation. `FML-ADR-057`
keeps peer ATAK available between admitted EUDs on the same access point and
records that `ap_isolate=1` would remove that S1 capability.

The Program Owner decided on 2026-09-25 that the SSID should be broadcast while
onboarding is active, hidden after the mission-generated onboarding key or time
window expires, and that EUDs remain partitioned until actually admitted.

## Decision

Onboarding shall use a temporary BSS and layer-2 domain distinct from the
operational EUD BSS.

While a mission-supplied absolute expiry is in the future, protected onboarding
credential material is available by reference, and node time is credible, the
onboarding BSS shall:

- broadcast its mission-specific SSID;
- accept the temporary onboarding credential;
- isolate associated stations from one another; and
- permit traffic only to the enrollment endpoint and the minimum name,
  addressing and time services required to reach it.

At expiry, or whenever credential material or credible time is unavailable, the
node shall stop accepting the onboarding credential, stop forwarding existing
onboarding clients, and hide the onboarding SSID. Hidden-SSID behavior is an
emission and usability property, not an access control. Credential invalidation
and the quarantine boundary are the security controls.

The mission package shall carry the onboarding SSID, an absolute UTC expiry,
and a reference to protected credential material. It shall never carry the
credential. No fixed lifetime is compiled into the node.

QR codes or managed EUD profiles may carry the temporary join information so an
operator need not select or type the network manually. Their use does not
change the quarantine or admission rules.

Admission is a transition to the operational EUD BSS, not a firewall exception
on the onboarding BSS. The operational BSS retains `ap_isolate=0` under
`FML-ADR-057`. Production admission remains EAP-TLS; per-device PPSK remains
the permitted prototype path in `FML-ADR-038`.

## Status

`SELECTED`.

The two-network boundary, time gate, broadcast behavior and fail-closed posture
are decided. `TBR-ID-01` still owns who may enroll and how identity becomes an
admission credential; `TBR-SEC-01` still owns protected credential storage; and
`TBR-LINUX-01` still has to establish the selected driver's multi-BSS behavior.

## Consequences

- An onboarding credential never grants access to the operational peer domain.
- Admitted EUDs retain local peer ATAK because their BSS is not isolated.
- The AP configuration needs a second BSS or equivalent interface, a quarantine
  bridge or VLAN, DHCP/DNS scoped to it, and fail-closed firewall rules.
- Expiry enforcement depends on credible time and an explicit invocation of the
  bounded runtime selected by `FML-ADR-083`.
- QR/profile generation handles secret material outside the committed mission
  package and repository.

## Accepted cost

Two BSS contexts and a quarantine network are more complex than one shared AP.
They consume driver resources, add an operator-visible transition between
onboarding and operational access, and require phone testing on every supported
EUD platform. Hiding an expired SSID can also make recovery less discoverable;
the operator shall deliberately reopen a bounded onboarding window.

## Fallback

If the selected driver cannot field the two BSS contexts reliably, use a
physically separate onboarding radio for the same quarantine boundary. Do not
collapse onboarding into the operational peer domain. If QR/profile import is
not portable enough, retain broadcast discovery during the active window and
use manually provided temporary credentials.

## Superseded by

None.

## Verification dependency

The software digital twin shall exercise active, expired and time-degraded
windows. Stage 9 shall demonstrate on a supported EUD that an onboarding client
can reach enrollment but cannot reach another client, the operational peer
domain or other node services; that an admitted EUD retains peer ATAK; and that
expiry removes forwarding, rejects the temporary credential and hides the
SSID. RF and driver behavior remain unverified until that hardware exercise.
