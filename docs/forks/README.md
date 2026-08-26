# Fork ledger

This program will carry patches. The kernel is the likely one, possibly the
wireless supplicant, possibly the radio driver itself. `TBR-LINUX-01` exists
partly to find out how many.

**Every carried patch is a liability with a name attached.** This ledger is
where the name goes.

## Policy

**Fix upstream first.** Carry a patch only when upstream will not take it, or
cannot take it in the time the program needs. Those are the only two reasons.
"It was faster to patch locally" is how a program acquires a fork it did not
decide to acquire.

When a patch is carried:

- It has a **named maintainer**. Not a role, a person. Not `TBD`.
- It has a **rebase cadence** and a recorded **last rebase date**.
- It has an **upstream submission status**, which is a real state: submitted
  and under review, submitted and rejected with a reason, not submitted with a
  reason, or not submittable and why.
- It states **what happens if its maintainer becomes unavailable**. This
  question is the point of the ledger. A carried patch whose owner has gone is
  a patch nobody understands blocking a kernel update nobody can perform.

A patch set with no entry here is not permitted. `tools/validate-docs.sh`
checks that every patch file in `os/kernel/patches/` has a corresponding fork
entry, and fails the build otherwise. That check exists because the failure it
prevents is silent: a patch lands, works, and is forgotten until the day it
does not apply.

## Upstream-first, in practice

Before carrying a patch, answer these in the entry:

1. Has it been sent upstream? If not, why not?
2. If it was rejected, what was the reason, and does that reason also apply to
   this program's use of it?
3. Is the patch a workaround for something the program is doing wrong? A
   surprising number are.
4. What is the cost of not having it? If the answer is "a feature is
   unavailable", that is often cheaper than a fork.
5. Who rebases it, and what happens when they stop?

## Relationship to the compatibility set

`FML-ADR-040` promotes kernel, driver, firmware and userspace as one tested
set. A carried patch is part of that set, so:

- Rebasing a patch creates a **new candidate set** that must pass the full
  promotion gate in `os/release/README.md`.
- A patch that fails to apply blocks the whole set, not just its own component.
- The version pins in `os/kernel/PINS.md` record the base the patches apply to.

This is why the rebase cadence matters. A fork rebased every release is
routine; a fork rebased after two years is a port.

## Entry template

One file per patch set, named `<component>-<short-slug>.md`.

```markdown
---
component: linux-kernel
maintainer: VACANT
upstream: <project name>
upstream-base: <commit or tag the patches apply to>
rebase-cadence: <e.g. every upstream stable release>
last-rebase: TBD
submission-status: not-submitted
patch-path: os/kernel/patches/
adr: [FML-ADR-040]
---

# <component> - <what the patch set does>

## Exact delta

What the patches change, file by file, in enough detail that someone else could
decide whether a new upstream release makes them redundant. Not "fixes HaLow
support"; which function, which behaviour, which symptom.

## Why it is carried

Which of the two permitted reasons applies: upstream will not take it, or
cannot take it in time. With evidence: a mailing list thread, a review comment,
a maintainer's response.

## Upstream submission status

Submitted and under review, submitted and rejected with the reason, not
submitted with the reason, or not submittable and why. Include the link and the
date.

## Rebase strategy

Which upstream releases this tracks, who performs the rebase, how the result is
validated, and what the promotion gate requires afterward.

## If the maintainer becomes unavailable

The consequence, stated plainly. Who could take it over, what they would need
to know, and what the program does if nobody can: drop the patch and lose the
capability, freeze the base version, or find another path. Decide this now, not
during the handover.

## Removal criteria

What would make this patch unnecessary. An upstream release, a driver change, a
hardware substitution. A fork with no removal criteria is a permanent fork, and
saying so honestly is better than implying it is temporary.
```

## Current entries

**None.** No patch set is carried today, and `os/kernel/patches/` is empty.

Whether the program acquires one is `TBR-LINUX-01`. That trade's closure gate
requires, explicitly, that if a patch set is needed then an entry exists here
with a **named owner** before the trade can be marked `CLOSED`. Closing it with
the owner recorded as `TBD` is not permitted.

`MAINTAINERS.md` records every role as `VACANT` today, which means the program
currently has nobody who could own a fork. Acquiring one in that state would be
the clearest possible instance of the failure this ledger exists to prevent.
