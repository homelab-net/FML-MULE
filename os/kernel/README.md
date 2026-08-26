# Kernel and board support package

The hardware-specific half of the two-layer split described in `os/README.md`.
Kernel, device tree, out-of-tree radio driver, radio firmware, bootloader.

## The open question

**The Wi-Fi HaLow driver path is out-of-tree.** Whether a stock
Debian-family kernel suffices, or whether a patched vendor tree is required, is
**an open question**: `TBR-LINUX-01`. It is on the critical path and almost
everything in `os/` waits behind it.

Three outcomes are possible, in decreasing order of preference:

1. **Stock distribution kernel plus a DKMS out-of-tree driver.** No fork.
   Ordinary security updates, within the compatibility-set rule. Widest choice
   of compute module.
2. **Stock upstream kernel with a small carried patch set.** Acceptable if the
   delta is small, understood, and plausibly acceptable upstream. Requires a
   fork entry and a named owner from the first commit.
3. **A vendor kernel tree.** Only if the radio cannot be made to work
   otherwise. Vendor trees lag, and moving to a newer base is often not a rebase
   but a port.

## If a patch set is required

**It constitutes a maintained fork.** That is not a figure of speech; it is a
permanent commitment with a person's name on it.

Every carried patch set requires, before it lands:

- A **named maintainer**. Not a role, not `TBD`.
- A **rebase cadence** and a recorded last rebase date.
- An **upstream submission status**: submitted and under review, rejected with
  a reason, or not submitted with a reason.
- A statement of **what happens if the maintainer becomes unavailable**.

The policy is **upstream first**: carry a patch only when upstream will not
take it, or cannot take it in the time the program needs. "It was faster to
patch locally" is how a program acquires a fork it never decided to acquire.

`docs/forks/README.md` holds the ledger and the entry template.
`tools/validate-docs.sh` **fails the build** if a patch file exists here with
no fork entry, because that failure is otherwise silent: the patch lands,
works, and is forgotten until the day it does not apply.

Note that `MAINTAINERS.md` currently records every role as `VACANT`. The
program has nobody who could own a fork today. Acquiring one in that state
would be the clearest possible instance of the failure the ledger exists to
prevent.

## `patches/`

Patch files applied to the kernel tree, in apply order. Currently **empty**,
holding only `.gitkeep`.

Naming: `NNNN-short-description.patch`, four digits, applied in numeric order.
`.gitattributes` marks `*.patch` as text with diffing suppressed, so a patch
does not produce a diff of a diff in review.

Every patch file here needs a corresponding entry in `docs/forks/`.

## `PINS.md`

The version pins for the compatibility set: kernel, driver, firmware, and the
tools that configure the radio. All `TBD`.

A change to any pin creates a **new candidate set** that must pass the full
promotion gate in `os/release/README.md`. See `FML-ADR-040`.

## Out-of-tree module build

The driver is built either through DKMS, so it rebuilds when the kernel
changes, or as part of the image build against a pinned kernel. Which is `TBD`
and depends on `TBR-LINUX-01`.

DKMS is convenient and is **not** a substitute for promoting the whole set
together. A module that rebuilds successfully against a new kernel has not been
shown to work with it; the promotion gate requires that the radio actually
enumerates and forms a mesh.

## Device tree

Overlays live in `os/overlays/`. Which overlays are needed depends on the
selected compute module and carrier, both `TBD`. See `TBR-HW-01` and
`TBR-CARRIER-01`.
