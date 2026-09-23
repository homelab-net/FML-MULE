# Three MULEs, no Layer 2

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

What would be shown: three geographically separated MULEs, each with its own
WAN. Authorized MULEs exchange approved inter-MULE traffic. The local RF mesh
is not extended across the WAN.

Pass: inter-MULE traffic uses the overlay. batman-adv originators do not
appear across the WAN. No Layer-2 loop is introduced between the mesh and the
overlay.

Fail: a mesh adjacency or a bridged broadcast domain crosses the WAN.

This is not the uplink-pooling question in FML-ADR-069 and TBR-NET-04.

Source: FML-ADR-082. CONOPS v1.1 sections 43 and 78.
