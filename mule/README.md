# `mule/`

**The decisions a MULE node makes while it is running.**

If you want to know what the node actually does when someone turns it on, this
is the directory to read. Everything here is small, and each file answers one
question you can ask in plain English.

## One file, one question

| File | The question it answers |
| --- | --- |
| `bearers.py` | Which radios can a node have, and which ones does it need to do its job? |
| `timekeeping.py` | Can the clock be trusted? |
| `admission.py` | May this device join the network? |
| `services.py` | What does this node offer, and what name does a user reach it by? |
| `status.py` | What do we tell the operator? |

That is the whole package. If a sixth file appears, it should be because there
is a sixth question, not because a file got long.

## Run time here, build time in `tools/`

The line between this directory and `tools/` is **when** the decision is made.

- `mule/` is what the node decides **while it is running**, in the field, with
  nobody watching. Whether the clock can be trusted. Whether a phone may
  connect.
- `tools/` is what is decided **about** the node beforehand, on a builder's
  machine. `tools/gen-config.py` works out which radio channel is lawful in a
  region and refuses to guess when nobody has decided yet. That runs before the
  node exists, so it lives there.

## What does not belong here

- **Fakes, test fixtures and scenarios.** Those are `test/`.
- **The image build and configuration pipeline.** That is `os/`.
- **Repository tooling.** That is `tools/`.
- **The four placeholder components in `services/`**, which stay blocked on
  open trades and must not be implemented anywhere.
- **Anything no scenario exercises.** This is a home for logic that has been
  demonstrated, not a waiting room for logic somebody intends to write.

## Nothing installs this yet

`os/` owns installation, and the promotion gate in `os/release/README.md` does
not know this package exists. How it reaches an image, how it is packaged, and
what the node's process entry point is are left to a later implementation ADR.
`FML-ADR-051` records that gap rather than hiding it.

## How to read a file here

Each module starts with a plain-language explanation of the question it answers
and why the answer matters. The comments explain **why**, not what: what the
code does should be readable from the code.

Two habits you will see repeatedly, both deliberate:

- **`None` means "the node cannot say".** It is not a missing value or a
  placeholder. Several questions genuinely have no answer yet, because the
  measurement that would answer them has not been taken, and inventing a number
  is how an estimate ends up quoted as a fact.
- **No value is written into the code that a deployment could change.** Radio
  channels come from a region profile, service names from the mission package,
  time limits from the caller. See `AGENTS.md`.

## Why this package exists at all

An adversarial review of the flat-sat found that whether the clock could be
trusted was being decided by a **test fake**, not by the node. The tests looked
thorough and could not have failed, because no real code was deciding anything.

Moving the decisions out of the test tree is what stops that recurring. The
rule is in `FML-ADR-051`: if the node has to decide it, it lives here, and it
is held to the same standards as anything else that would ship.
