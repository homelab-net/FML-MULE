# Does the stock Debian kernel support BATMAN_V

**Trade:** `TBR-LINUX-01`.
**Date:** 2026-08-30.
**Taken by:** Cameron Zobrist, on the lab development machine.
**Status of this artifact:** a real result on the baseline operating system,
`SIMULATED` in the sense that no radio was involved. The kernel and the module
are the ones a MULE would run under `FML-ADR-022`; the interface created was a
bare `batadv` device with no hard interface attached.

## The question, and who asked it

`docs/dev-machine.md` check 2, which that file marks **"This one is
load-bearing"**:

> **Does the stock Debian kernel support `BATMAN_V`?**
>
> `FML-ADR-053` makes BATMAN-IV the baseline, and one half of its argument is
> that `BATMAN_V` is simply not compiled into the stock kernel [...] That was
> observed on the Ubuntu Azure kernel. If Debian's kernel enables
> `CONFIG_BATMAN_ADV_BATMAN_V`, the availability half of that argument does not
> hold on the baseline operating system, and the ADR needs revisiting on the
> record.

## Answer: it does

| Item | Value |
| --- | --- |
| Host | Debian 13, kernel `6.12.105+deb13-amd64`, x86_64 |
| Module | `batman-adv` 2024.2, `kernel/net/batman-adv/batman-adv.ko.xz` |

The module's default, as loaded:

```text
# cat /sys/module/batman_adv/parameters/routing_algo
BATMAN_IV
```

Selecting `BATMAN_V` succeeds, where on the Ubuntu Azure kernel it fails:

```text
# echo BATMAN_V > /sys/module/batman_adv/parameters/routing_algo
# cat /sys/module/batman_adv/parameters/routing_algo
BATMAN_V
```

And an interface created while it is selected comes up with no complaint:

```text
# ip link add name bat_v type batadv
# (exit 0, and dmesg carries no "Routing algorithm ... is not supported")
```

For contrast, `.github/workflows/mesh-probe.yml` on the GitHub runner reports:

```text
BATMAN_V is NOT available in this module build.
```

**Both are true.** They are different kernels, and `FML-ADR-053` and
`docs/dev-machine.md` both already said the Ubuntu Azure kernel "is not the
baseline operating system". The check existed because somebody expected this
to differ, and it does.

The system was restored to `BATMAN_IV` and the interface removed.

## What this changes, and what it does not

**Half of `FML-ADR-053`'s argument does not hold on the baseline OS.** The ADR
states that selecting BATMAN-V "means a custom kernel or the out-of-tree
`batman-adv` module, permanently, in the compatibility set `FML-ADR-040`
governs, maintained by volunteers." **On Debian 13 it means neither.** The
algorithm is in the stock module and costs nothing to select.

**The decision still stands, on its other leg.** `FML-ADR-053` rests on two
arguments and is explicit that availability was one of them. The other is
untouched, and it is the stronger one:

> BATMAN-V's throughput-based metric needs a usable throughput estimate from
> the driver. Whether the HaLow driver provides one is **UNVERIFIED** [...] If
> it does not, path selection may be effectively arbitrary.

Nothing here says anything about a HaLow driver, because no HaLow radio was
involved. The revisit criteria in `FML-ADR-053` require **both** `TBR-RF-01`
evidence of a usable driver throughput estimate **and** measurement showing
BATMAN-IV selecting materially worse paths. This is neither.

**Do not switch.** `docs/dev-machine.md` says so in the same paragraph that
asks the question, and it is right: availability alone is not a criterion.
What has changed is the cost of a future switch, not the case for one.

## What should happen to the ADR

`FML-ADR-053` carries a statement about the stock kernel that is false for the
operating system `FML-ADR-022` selects. That is not a typographical error and
`docs/adr/README.md` does not permit editing a `SELECTED` decision's reasoning
in place.

The options are for the decision's owner, and this artifact takes neither:

1. Leave the ADR and let this evidence stand as the correction, which is what
   `docs/dev-machine.md` anticipated by saying "record the finding".
2. Supersede it with an ADR that reaches the same decision on the surviving
   argument alone, so that nobody later reads the availability claim and acts
   on it.

The second is worth considering for one reason: the availability argument is
the more concrete of the two and therefore the more likely to be quoted, and a
future reader deciding whether to revisit BATMAN-V would be reasoning from a
statement that is not true on their own hardware.
