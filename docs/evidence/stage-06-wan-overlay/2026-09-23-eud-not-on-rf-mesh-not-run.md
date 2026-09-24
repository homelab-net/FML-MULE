# EUD is not on the RF mesh

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

What would be shown: an EUD admitted under ASSIGNED_MULE_ONLY is not a
participant of the local RF mesh and holds no route onto it. An approved
mission service that the assigned MULE itself reaches over that mesh is still
reached through the assigned ingress. The path past the ingress is the MULE's.

Pass: the EUD has no batman-adv membership and no mesh address. A service the
MULE reaches over the mesh, if approved, is reachable at the assigned ingress
without the EUD holding a mesh route.

Fail: the EUD is bridged onto batman-adv, or the EUD holds a route whose next
hop is a mesh node. Reaching the service through the MULE is not this failure.

This case does not decide whether a local access-point EUD is forwarded onto
batman-adv. That remains FML-ADR-068 and TBR-TAK-01.

Source: FML-ADR-082. CONOPS v1.1 section 43.
