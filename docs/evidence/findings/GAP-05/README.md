# GAP-05 evidence

Handle unknown radio enumeration safely: an enumeration that returns `None`
(the platform could not determine which radios are present) is a distinct fault
and the node fails closed to FAULT, rather than crashing or being read as "no
radios present" (FML-ADR-077).

State: IMPLEMENTED. Owner: Claude. Awaiting independent red-team, then closure.

| Artifact | What it records |
| --- | --- |
| `implementation.md` | The change made, the failing-first demonstration, and how to reproduce it. |
