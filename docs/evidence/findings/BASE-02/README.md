# BASE-02 evidence

This directory records the clean verification baseline and red-team evidence
for BASE-02.

`2026-09-09-verification.json` identifies the exact source commit, normal-user
environment, toolchain, commands, exit codes, timing, test counts, coverage,
mutation score, generated-output recovery, and temporary fault result. A
closure packet will be added only after an independent P0 reviewer reproduces
the acceptance steps.

The evidence is `SIMULATED`. It verifies repository behavior on a development
host and in hosted CI. It makes no claim about the target system or hardware.
