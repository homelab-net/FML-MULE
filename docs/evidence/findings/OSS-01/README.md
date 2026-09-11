# OSS-01 evidence

This directory records execution and eventual closure evidence for OSS-01, the
prior-art and reuse register.

`execution-card.md` fixes the scope and verification contract before the
registry implementation begins. A closure packet and retained machine-readable
results will be added only after the complete candidate corpus is evaluated and
an independent P0 reviewer reproduces the acceptance checks.

The work is documentation and repository-tooling evidence. It cannot establish
hardware behavior.

## Evaluation progress

As of 2026-09-10, nine of the 28 registered candidates have reached
`EVALUATED`: Project N.O.M.A.D., OpenMANET firmware, `openmanetd`, Reticulum,
NomadNet, Martin, OpenTAKServer, PyTAK and Meshtastic firmware. The first five
are retained as pattern-only prior art. Martin, PyTAK and Meshtastic firmware
record already selected narrow uses. OpenTAKServer remains preferred but not
owner-approved after exact-release simulation exposed its three-process
deployment and hardening gates. The remaining 19 records are `BASELINED`, so
OSS-01 remains `BASELINED` in the execution register and has no closure packet.
