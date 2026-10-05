# GAP-09H evidence

This directory records the operator procedure for the v0.0.1 milestone: the
build-and-bring-up steps a person who did not write the documentation follows to
reach one node, one service (Martin map tiles), reachable from a phone.

State: OPEN -- a `DRAFT` procedure exists. It assembles the ready steps and names
the gaps that still block a clean end-to-end run (arm64 image, a complete AP
render, AP credential, ingress/TLS, DHCP addressing, the runtime and AP stack on
the image). Interface naming is met for the Pi article and the render is wired
into the oneshot; the procedure's gap register is the current list.
v0.0.1 is accepted only when the cold-start drill in `docs/verification/README.md`
runs on real hardware and its issues are resolved; that is not done, and nothing
here is `HARDWARE-VERIFIED`. Independent review is required before this finding can
close.

| Artifact | What it records |
| --- | --- |
| `2026-09-26-operator-procedure.md` | The v0.0.1 build/bring-up procedure, the cold-start acceptance drill, and the register of gaps that block a hands-free run. |
| `2026-10-04-m1-runtime-on-the-image-decision-packet.md` | Gap G8 decision packet, approved 2026-10-04 and recorded as `FML-ADR-089`: the M1 package set on the image, and how Martin runs on it (account, per-UID Quadlet directory, state path, boot start). |
| `2026-10-05-first-build-cloud-session.md` | First build and QEMU boot of the current x86 closure (`SIMULATED`), in a cloud session: found and fixed the runtime install defect that stopped every build since #176; boots to `multi-user.target`, three `systemd-pcrlock` units failing. One build, not the three-build sequence. Boot log beside it. |
| `2026-10-04-bc0-x86-image-execution-card.md` | Bench card BC-0: build and QEMU-boot the current x86 118/454 closure on the N150, the "any arch" half of gap G1. A procedure, not a result. |

Naming and recording rules are in `docs/evidence/README.md`. Nothing real: no
deployment location, member identity, callsign, credential, or operational
capture. See `SECURITY.md`.
