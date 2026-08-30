# `mule/`

**The decisions a MULE node makes while it is running.**

If you want to know what the node actually does when someone turns it on, this
is the directory to read. Everything here is small, and each file answers one
question you can ask in plain English.

## One file, one question

| File | The question it answers |
| --- | --- |
| `bearers.py` | Which radios can a node have, and which ones does it need to do its job? |
| `bringup.py` | What order does the network plane come up in, and what did a sequence break? |
| `power.py` | How long can the node keep running, and can it even say? |
| `thermal.py` | Is the node inside its thermal envelope, and can it tell? |
| `sysfs.py` | Reading the machine's own sensors through the Linux kernel. |
| `timekeeping.py` | Can the clock be trusted? |
| `admission.py` | May this device join the network? |
| `services.py` | What does this node offer, and what name does a user reach it by? |
| `modes.py` | Which operating modes is the node in, and which can it not tell? |
| `status.py` | What do we tell the operator? |

That is the whole package. If another file appears, it should be because there
is another question, not because a file got long.

## One file is not a decision

`sysfs.py` is the exception, and it is deliberate. Everything else here judges;
that file produces the readings the judgements consume, by reading the kernel's
own interfaces. It sits in `mule/` because it is node-resident production code
that runs in the field, which is what `FML-ADR-051` is about, even though it
decides nothing.

It is also the first thing that will behave differently on hardware than it does
in development, so it is worth knowing what is decided about it and what is not:

| | |
| --- | --- |
| **Decided** | `/sys/class/thermal/thermal_zone<N>/temp` in millidegrees Celsius, `type` naming the zone. Kernel ABI, identical on every Debian-family node (`FML-ADR-022`). Needs no trade. |
| **Per board** | Which zone is the processor and which the radio. Zone type strings are driver-supplied and unstandardised. `TBR-HW-01` selects the board, so the map is configuration and is empty today. |
| **Not portable at all** | Thermal throttling. Linux has no general flag; it is per-SoC. The probe is injected, and a platform with none reports `None`, never `False`. |
| **Not yet possible** | Battery, enclosure and ambient temperature. Those need a BMS and an enclosure that do not exist. `TBR-PWR-01`, `TBR-THERM-01`, `TBR-CARRIER-01`. |

Nothing in it has run against real hardware. Its tests build a synthetic sysfs
tree, faithful to the documented interface and silent about any board. A capture
from a real node belongs in `test/fixtures/`, with the node identifier, capture
date and image build recorded.

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

### Code before numbers

`power.py` is the pattern this package is built on, and it is worth
understanding before adding anything here.

CONOPS sections 59 to 61 specify a complete **procedure**: pack capacity, a
reserve margin, a service-host power penalty, cold derating. `TBR-PWR-01` has
measured none of the **inputs**. So the procedure is written now and the inputs
arrive later, as a `PowerModel` the caller supplies. With no model the node says
it cannot tell, and names the trade. With one, it answers.

Nothing about the node changes on the day that trade closes. Two of the
thirteen CONOPS section 67 questions stop answering "cannot say" because
somebody measured a battery, not because somebody wrote software.

The same shape holds for `timekeeping.py`, where `TimePolicy` carries the
bounds `TBR-TIME-01` will set, and for `thermal.py`, where `ThermalLimits`
carries `TBR-THERM-01`'s. **An open trade blocks a value, not a decision.**
Where you can name the procedure, write it; where you would have to name a
number, take it as a parameter.

Each of the three also draws the same line through its inputs: what a sensor
can state directly is a **reading**, and what somebody has to conclude is a
**decision**. A radio has associated, an RTC holds a timestamp, a pack reports
a charge, an SoC says it throttled: readings. Whether time is credible, how long
the battery lasts, whether a temperature is inside an envelope: decisions. Fakes
supply the first kind only, which is what makes the second kind testable.

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
