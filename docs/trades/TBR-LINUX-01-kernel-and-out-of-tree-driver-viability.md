---
id: TBR-LINUX-01
title: Kernel and out-of-tree driver viability
status: OPEN
owner: TBD-SRR
area: LINUX
priority: 8
function-owner: Linux/Platform
critical-path: false
depends-on: [TBR-HW-01, TBR-REC-01]
feeds: [TBR-RF-01, TBR-RF-03]
requires-hardware: yes
evidence: docs/evidence/TBR-LINUX-01/
adr: [FML-ADR-040, FML-ADR-022, FML-ADR-023, FML-ADR-024]
target-date: TBD-SRR
---

# TBR-LINUX-01 Kernel and out-of-tree driver viability

**Source:** SAD v0.31 section 20.2, and the TBR register in SAD section
30.2 (priority 8 of 16).

**Function owner:** Linux/Platform. **Named owner:** `TBD-SRR`.

SAD section 30.2 records an SRR exit action: the Program Owner assigns one named
individual and one calendar target date to every open TBR. `TBD-SRR` marks the
gap explicitly rather than hiding it behind a functional organization.

## Question

Can HaLow remain reliable across the controlled kernel lifecycle?

## Why it matters

The Wi-Fi HaLow driver path is out-of-tree (source `SR-011`). Almost everything
in `os/` waits behind this.

SAD section 20.2 changes what closure means: **`TBR-LINUX-01` closes on a
repeatable kernel-promotion pipeline, not merely a one-time successful driver
build.** A driver that builds once proves nothing about the next kernel.

If a patched vendor tree is required, the program acquires a **maintained kernel
fork** with a named owner, a rebase cadence and an entry under `docs/forks/`.
SAD section 20.1 records a local fork as a program liability.

`FML-ADR-024` further assumes BATMAN-V can obtain a usable throughput estimate
from the HaLow driver. Whether it does is `UNVERIFIED` and is part of this
trade.

## Options

1. **Stock distribution kernel plus DKMS out-of-tree driver.** The best outcome:
   no fork, ordinary security updates within the compatibility-set rule, widest
   hardware choice. SAD section 20.2 item 3 prefers DKMS where the driver
   package supports it cleanly.
2. **Stock upstream kernel with a small carried patch set.** Acceptable if the
   delta is small and plausibly acceptable upstream. Requires a fork entry and a
   named owner from day one.
3. **Vendor kernel tree.** Only if the radio cannot be made to work otherwise.
   Vendor trees lag, and moving to a newer base is often a port rather than a
   rebase.

Where DKMS is not the supported path, SAD section 20.2 item 4 requires the
driver build to be pinned to the approved kernel package.

## Closure evidence

SAD section 30.2: driver install and rebuild; mesh formation; the HIL
kernel-promotion pipeline; reboot; rollback; sustained traffic.

The pipeline requires the permanent hardware-in-the-loop bench of SAD section
20.4 and its twelve-step release suite, from clean boot through rollback to the
known-good image.

Where a patch set is required: the patch files, the upstream base commit they
apply to, and a written assessment of upstream acceptability.

Also `batctl` output showing whether BATMAN-V obtains a throughput estimate from
the driver, or evidence that it falls back to a default.

Evidence is committed under `docs/evidence/TBR-LINUX-01/`.

## Closure gate

A repeatable kernel-promotion pipeline exists and has been exercised: a candidate
kernel rebuilds and loads all required out-of-tree modules, passes the automated
smoke tests, survives a reboot, and demonstrates rollback.

The closure states explicitly whether a carried patch set is required, and if so
a `docs/forks/` entry exists with a **named owner** before the trade is marked
`CLOSED`. Closing it with the owner recorded as `TBD` is not permitted.

**Closure gate per SAD section 30.2:** Before production software PDR / Stage 2.

No TBR closes on document wording alone. It closes only when its listed evidence
exists, the named owner accepts the evidence, and the resulting architecture
decision is entered into the persistent ADR register.

## Dependencies

- **Depends on:** `TBR-HW-01`, `TBR-REC-01`
- **Feeds:** `TBR-RF-01`, `TBR-RF-03`
- **Related decisions:** `FML-ADR-040`, `FML-ADR-022`, `FML-ADR-023`, `FML-ADR-024`
- **Validating stage:** Stage 2 (CONOPS section 78)
- **Requires hardware:** Requires a candidate compute module, a HaLow radio,
  and the two-node HIL bench.
SAD section 20.4 requires bench hardware to be a reserved program asset, not
borrowed from the deployable fleet.
