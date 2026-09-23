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

No file here supports a claim about RF, Tailscale, or a fielded EUD.
