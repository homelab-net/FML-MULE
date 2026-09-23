# CCR-04 acceptance

Result: decision accepted. Not a test.
Classification: UNVERIFIED as to behaviour.
Date: 2026-09-23
Who: Program Owner
Instrument: none
Node: none
Image build: none

What was decided: CONOPS v1.1, FML-ADR-082 SELECTED, FML-ADR-039 SUPERSEDED.
Mission creation may select remote-EUD overlay posture ASSIGNED_MULE_ONLY.
The default is DISABLED. An admitted EUD is granted only the approved
remote-EUD ingress of its assigned MULE. The admitted EUD's tag names the
mission and the assigned team and does not name a role. The grant does not place the EUD on
the local RF mesh. The MULE may reach an approved mission service for that
EUD over that mesh. That reach is the MULE's.

What was not done: no overlay was built, no EUD was enrolled, no grant was
written, no mesh was formed, and no service was fetched. The other files in
this directory are the cases that would have to be run before anyone claims
the posture works. None of them has been run.

v0.0.1 is unchanged. mule/ was not edited. The mission schema was not edited.
