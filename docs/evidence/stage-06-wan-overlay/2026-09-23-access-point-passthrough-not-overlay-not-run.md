# Passthrough is not enrollment

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

What would be shown: an EUD on the access point is forwarded to the general
WAN uplink, and that traffic is not routed into the secure overlay.

Pass: uplink forwarding matches FML-ADR-068. The forwarded flow does not
appear as overlay membership and does not reach other MULEs through the
overlay.

Fail: access-point traffic is masqueraded onto the tailnet.

Remote-EUD membership, when the posture allows it, is the EUD's own
enrollment. It is not this path.

Source: FML-ADR-068 and FML-ADR-082. The nftables comment states the same
boundary and changes no rule.
