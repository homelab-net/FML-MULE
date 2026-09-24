# Continuity declined

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
A flat-sat of this case, if one is later written, is SIMULATED and says
nothing about physical behaviour. Nothing here is HARDWARE-VERIFIED.

What would be shown: the EUD declines remote continuity, or an administrator
leaves the posture DISABLED. Local onboarding and local operation do not fail
for that reason.

Pass: the EUD still uses the access point and the local services the mission
already allowed. It is not on the overlay.

Fail: declining the opt-in, or leaving the default in place, blocks local
operation.

Source: FML-ADR-082. CONOPS v1.1 sections 43 and 78.
