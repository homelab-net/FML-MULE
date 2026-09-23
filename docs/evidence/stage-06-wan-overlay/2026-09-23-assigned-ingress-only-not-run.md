# Assigned ingress only

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

What would be shown: posture ASSIGNED_MULE_ONLY, EUD authorized for one
assigned MULE. The EUD reaches that MULE's approved remote-EUD ingress and
no other overlay destination.

Pass: the only overlay destination that answers is the assigned ingress.
Another MULE, a management interface, and a peer EUD on the overlay do not.

Fail: any of those other destinations answers, or overlay membership is
treated as mission authorization by itself.

Source: FML-ADR-082. CONOPS v1.1 section 43.
