# Stage 6 evidence

**Decision:** `FML-ADR-082` (`SELECTED`). **Change:** `CCR-04`, accepted
2026-09-23. **Stage:** `test/stages/stage-06-wan-overlay/`.

This directory is stage evidence, not a trade's. The stage definition does
not exist. Nothing in this directory is a measurement.

The files other than this README are the cases `FML-ADR-082` says the stage
shall eventually prove. Each one states the pass condition and records that
the case has **not been run**. That is `UNVERIFIED`. It is not `SIMULATED`.
It is not `HARDWARE-VERIFIED`. A later run replaces the "not run" file with a
log that names the instrument, the node, the image build, and who ran it.
Do not edit a not-run file into a result without that log.

`2026-09-23-ccr-04-acceptance.md` is a decision record, not a test. It says
who accepted the posture. It does not say the posture works.

`2026-09-29-firewall-boundary-flat-sat.md` is a `SIMULATED` netns + nftables run
(`test/bench/wan-overlay-posture.sh`). It **advances** the firewall-boundary half of
several cases -- it shows the boundary in `os/config/nftables.conf.template` drops the
cross-plane paths and admits only the ingress port on the overlay interface -- but it
**closes none of them**: each case keeps an owed half (the tailnet-identity half, the
full CONOPS section 41 service set, RF, or a second MULE), so every `*-not-run.md`
stays not-run. It says nothing about *which* peer is the assigned MULE; that identity
half is the Tailscale policy (`os/config/tailscale-acl.hujson.template`), run on a real
tailnet, not the firewall.

`2026-09-29-assigned-ingress-only-real-tailnet.md` is a `SIMULATED` run on the **real
coordination server** with a **real tagged EUD** (the Owner's iOS device). It
**advances** the *identity half* of `assigned-ingress-only` and `one-mission-team-tag`:
the server's own ACL tests confirm the EUD tag reaches only `tag:mule-bench:8089` and is
denied the admin port, a non-ingress port, and the shared `tag:mule` (the per-MULE-scoping
proof from `FML-ADR-086`), and the EUD device carries exactly one mission-and-team tag.
It **closes neither**: the live dataplane connection, `assigned-mule-lost-no-reattach`,
and RF all stay owed, so those `*-not-run.md` stay not-run.

`2026-09-29-assigned-mule-lost-two-mule.md` adds a **second MULE** (`tag:mule-bench2`, a
userspace `tailscaled` node, tag read back from the device API) and confirms on the
coordination server that the applied policy has **no** EUD grant to it (the tested ports
`:8089`/`:22` are denied) -- the `assigned-mule-lost-no-reattach` negative at the **policy
layer**, structural (the grant targets the assigned MULE's identity, not the shared
class) rather than stateful. Still owed and not-run: the live dataplane with the assigned
MULE taken down (not run, to avoid interrupting the Owner's own overlay access to that
MULE), `three-mules-no-layer2-extension` (the sim nodes carry no mesh), and RF.

No file here supports a claim about RF or a fielded EUD on the selected hardware.
