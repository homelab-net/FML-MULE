# No reattach

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

What would be shown: the assigned MULE is unavailable. The remote EUD does
not obtain overlay ingress through another MULE that is still up.

Pass: remote ingress for that EUD stops. Other MULEs stay on the overlay for
their own inter-MULE traffic. The EUD is not granted one of them.

Fail: the EUD is attached, routed, or enrolled to a different MULE without a
new authorization that names that MULE.

Source: FML-ADR-082. CONOPS v1.1 section 43.
