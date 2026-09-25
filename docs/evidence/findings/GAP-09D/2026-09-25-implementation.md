# GAP-09D runtime implementation

**Date:** 2026-09-25. **Evidence tier:** `SIMULATED`.

## Uncertainty addressed

This increment asks whether the existing node decision package can become one
bounded, versioned Python distribution with an installed native oneshot,
without inventing a resident supervisor or an automatic recovery policy.

## Implemented path

- `fml-mule==0.0.1` packages only `mule/`, plus the canonical mission schema
  and static `mule-runtime.service`.
- `python -m mule` validates explicit region, mission, node, service-catalog
  and deployed-Quadlet inputs, resolves the same parameters used by the
  software digital twin, atomically writes `parameters.json`, and exits.
- The unit is `Type=oneshot`, uses a transient unprivileged identity and a
  private `/run/fml` directory, and contains neither `Restart=` nor
  `OnFailure=`. It has no `[Install]` section, so an unprovisioned base image
  does not start it.
- The dated Debian snapshot resolves an exact 118-package target closure and
  454-package tools-tree closure. pip performs no dependency resolution and no
  isolated build inside mkosi; all build and runtime dependencies come from
  those locks.
- The completed-root CycloneDX document gains one `fml-mule` application
  component. Its digest covers installed Python source, distribution metadata,
  mission schema and native unit; the root validator recomputes it.

## Focused evidence

The fail-first test run produced five failures before the entry point,
distribution metadata, unit and image wiring existed. After implementation:

- 107 focused runtime, image-contract, configuration and digital-twin tests
  passed.
- A wheel built as `fml_mule-0.0.1-py3-none-any.whl` and installed into a
  disposable root with the expected module entry point, mission schema and
  `/usr/lib/systemd/system/mule-runtime.service` layout.
- A deliberate post-SBOM mutation of installed `mule/__main__.py` is rejected
  as runtime-component drift.
- Invalid mission input returns the configuration-error exit code and leaves
  no `parameters.json` output.

## What this does not establish

This is source-tree and disposable-root evidence. It does not show the unit
running under PID 1 in the development image and says nothing about target
hardware, RF, power, thermal behaviour or automatic recovery. GAP-09D remains
open until the image-installed oneshot successfully renders and independently
refuses malformed input under systemd.
