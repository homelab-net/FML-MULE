# GAP-07 evidence

Correct integration-probe workflow triggers: the mesh and LoRa probes now run
when the scripts, configurations and toolchain pins they exercise change, not
only when their own workflow file changes.

State: IMPLEMENTED. Owner: Claude. Awaiting independent red-team, then closure.

| Artifact | What it records |
| --- | --- |
| `implementation.md` | The change made, the check that enforces it, and how to reproduce it. |
