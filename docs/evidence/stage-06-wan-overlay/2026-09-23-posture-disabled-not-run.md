# Posture DISABLED

Result: NOT RUN
Classification: UNVERIFIED
Attempted: no
Instrument: none
Node: none
Image build: none
Configuration: none
Ambient: none
Who ran it: nobody

This file is the pass condition written before the run. It is not a result.
A software digital twin of this case, if one is later written, is SIMULATED and says
nothing about physical behaviour. Nothing here is HARDWARE-VERIFIED.

What would be shown: with remote-EUD overlay posture DISABLED, an EUD does
not join the WAN overlay.

Pass: the EUD has no overlay interface, no overlay address, and no grant to
any MULE ingress. Local access-point operation is unaffected.

Fail: the EUD appears on the tailnet, or local onboarding fails because the
posture is DISABLED.

Source: FML-ADR-082. CONOPS v1.1 section 43. FML-REQ-017, default clause.
