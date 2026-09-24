# One mission-and-team tag

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

What would be shown: posture ASSIGNED_MULE_ONLY. The admitted EUD has one
Tailscale tag. That tag names the mission and the assigned team. It does not
name an operational role. The assigned MULE is reached only through the
approved remote-EUD ingress. The spelling of the tag is not frozen by this
file. An illustrative form is tag:eud-mission-NAME-team-NAME. The words
NAME are placeholders. They are not a frozen spelling.

Pass: one tag is sufficient for the ingress grant, and a role is not in it.
Removing that tag removes the grant. Adding a second broad tag is not what
makes the ingress answer.

Fail: the grant exists only when several broad tags are all present, or a
grant fires because any one broad tag is present, or the tag names a role,
or a MULE infrastructure tag names a mission or a team, or the tag by itself
is treated as mission-data authorization.

Source: FML-ADR-082. CONOPS v1.1 section 43 keeps overlay authentication
separate from mission authorization. CONOPS does not freeze the tag spelling.
