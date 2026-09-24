# WAN loss

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

What would be shown: WAN, or the overlay, is lost. Local EUD access, the
local mesh, peer ATAK, local services, and LoRa continue.

Pass: each of those local functions still operates, and the node does not
require the overlay to keep them.

Fail: loss of WAN removes one of those local functions.

Source: FML-ADR-082. CONOPS v1.1 section 41. FML-REQ-016.
