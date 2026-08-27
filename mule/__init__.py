"""Node-resident decision logic for MULE.

`FML-ADR-051`: code that **makes a decision** the node acts on lives here and is
held to production standards. Fakes, fixtures, scenarios and flat-sat
composition scaffolding stay under `test/`.

Nothing is admitted here until the flat-sat exercises it end to end. This is a
home for demonstrated logic, not a staging area for intended logic, and the ADR
records that an accumulation of unexercised modules is the signal the decision
was wrong.

There is no service daemon and no process entry point here, and there will not
be one until an implementation ADR decides how this package is installed onto an
image and versioned against the compatibility set in `FML-ADR-040`. The four
placeholder components in `services/` remain blocked on their trades and must
not be implemented here or anywhere else.
"""
