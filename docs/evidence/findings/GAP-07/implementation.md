# GAP-07 implementation record

**Finding:** GAP-07, correct integration-probe workflow triggers (P1).
**Evidence tier:** SIMULATED (CI configuration).

## Defect corrected

The mesh and LoRa probe workflows triggered (`on: push: paths:`) only on their
own workflow file. So a change to a script, configuration or toolchain pin they
exercise did not re-run the probe that verifies it. Most concretely,
`lora-probe.yml` sources the pinned meshtasticd image from
`tools/toolchain-versions.sh`, so a pin bump shipped without the probe re-running
against the new daemon build.

## Changes

- `.github/workflows/lora-probe.yml`: trigger paths now include
  `tools/toolchain-versions.sh` (the pin it sources) and
  `os/config/meshtasticd.conf.template` (the config it is coupled to).
- `.github/workflows/mesh-probe.yml`: trigger paths now include
  `os/config/batman-adv.conf.template` (the settings it verifies are decided
  there).
- `tools/validate-docs.sh`: a new check (21) fails any workflow that sources
  `tools/toolchain-versions.sh` but does not list it in its trigger paths, so
  this cannot silently regress.

## Failing-first demonstration

The bats test `validate-docs catches a probe sourcing toolchain pins without
triggering on them` removes the pin path from a sandbox `lora-probe.yml` and
asserts `validate-docs.sh` fails naming it. The check was also observed to fire
directly against the working tree before the paths were added.

## Reproduce

`bats test/unit`; `bash tools/validate-docs.sh`. SIMULATED.
