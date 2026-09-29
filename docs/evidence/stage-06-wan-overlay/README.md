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

No file here supports a claim about RF, Tailscale, or a fielded EUD.
