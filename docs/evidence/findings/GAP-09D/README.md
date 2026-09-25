# GAP-09D evidence

This directory records the MULE runtime-packaging decision (entry point,
installation/versioning model, systemd unit shape) for the v0.0.1 vertical slice.

State: OPEN -- owner decision approved on 2026-09-25 and recorded in
`FML-ADR-083`. The package entry point, native static oneshot, image install
wiring, exact package locks and installed-root SBOM coverage are implemented.
The remaining gate is execution of the installed unit under the development
image's systemd, including successful render and malformed-input refusal.

| Artifact | What it records |
| --- | --- |
| `decision-packet.md` | Approved entry-point, installation/versioning model and unit shape, with restart/naming still deferred to `TBR-HA-01`/`TBR-LINUX-01`. |
| `2026-09-25-implementation.md` | Source-tree, wheel-layout, digital-twin and installed-root SBOM implementation evidence; records the image execution still required. |
