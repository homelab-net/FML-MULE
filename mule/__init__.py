"""The decisions a MULE node makes while it is running.

Small modules, one question each:

- `bearers.py` - which radios can a node have, and which does it need?
- `power.py` - how long can the node keep running, and can it say?
- `thermal.py` - is the node inside its thermal envelope, and can it tell?
- `sysfs.py` - reading the machine's own sensors. The one module here
  that produces readings rather than judging them.
- `timekeeping.py` - can the clock be trusted?
- `admission.py` - may this device join the network?
- `onboarding.py` - may an unadmitted device reach enrollment?
- `services.py` - what does this node offer, and by what name?
- `status.py` - what do we tell the operator?

`FML-ADR-051`: code that **makes a decision** the node acts on lives here and is
held to production standards. Fakes, fixtures, scenarios and software digital twin
composition stay under `test/`. Decisions made *about* the node beforehand, on a
builder's machine, live in `tools/`.

Nothing is admitted here until the software digital twin exercises it end
to end. This is a home for demonstrated logic, not a staging area for
intended logic, and the ADR records that an accumulation of unexercised
modules is the signal the decision was wrong.

There is no long-running service daemon. `FML-ADR-083` selects a bounded native
oneshot entry point for configuration rendering, installed and versioned with
the compatibility set in `FML-ADR-040`. The four
placeholder components in `services/` remain blocked on their trades and must
not be implemented here or anywhere else.

See `README.md` in this directory.
"""
