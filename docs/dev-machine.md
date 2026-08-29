# Working on a development machine

## Who this is for

You have this repository checked out on a real machine rather than in hosted
CI. Read this before you start work, then `AGENTS.md`, then `STATUS.md`, then
`docs/ROADMAP-DEV.md` for what to build.

Everything in this repository up to now was produced in hosted CI or in a
container. That constrained what could be tested and it also constrained what
could be *known*. This file records which of those constraints your machine
lifts, which it does not, and the four facts you should check in your first
hour because they currently rest on one kernel this program does not control.

## The first thing, because it is the thing that will fool you

`tools/lint.sh` **skips every tool that is not installed** and then prints:

```text
All linters that ran are clean.
```

Read the wording. On a fresh machine that message appears after running almost
nothing, and the exit code is zero.

So: install the toolchain until `tools/lint.sh` reports nothing skipped.
`.github/workflows/lint.yml` installs all of them and is the authoritative
list. Until then a green run means nothing, and "a signal that looks like
success" is this repository's signature failure. It is waiting for you on line
one.

## What this machine can do that hosted CI cannot

| Capability | Why CI cannot | Roadmap item |
| --- | --- | --- |
| 802.11s association, via `mac80211_hwsim` | GitHub hosted runners ship no wireless stack at all | 1.6 |
| Real systemd units and boot ordering | No init, no boot | 1.2 |
| Real `iw` and `batctl` against a live mesh | No wireless devices to read | 1.5 |
| Meshtastic natively, no CI round trip | Nothing, this is convenience | 1.1 |
| The flat-sat, iterated in seconds | Nothing, this is convenience | all |

Item 1.6 is the one that matters. It is blocked in `docs/ROADMAP-DEV.md`
specifically on "a machine with a wireless stack", and you are that machine.

## What it still cannot do, and must not claim

- **It is not the target architecture.** `TBR-HW-01` is open and the target is
  likely ARM. A development mini PC is x86-64.
- **It exercises the portable half only.** `FML-ADR-040` and `os/README.md`
  split the system into a portable userland and a hardware-specific kernel and
  board support package. This machine says nothing about the second.
- **There are no radios.** No HaLow driver, no RF, no power, no thermal.
  `mac80211_hwsim` is a simulated device: it exercises the 802.11 stack, not a
  radio.
- **Nothing done here earns `HARDWARE-VERIFIED`.** The tier stays `SIMULATED`.

"It ran on real Debian on real hardware" is a true sentence that becomes
"verified" when somebody quotes it six months later. Do not write it.

## Setting the machine up

1. **Debian stable.** `FML-ADR-022` selects the current Debian stable release
   at build time; at SAD issue that is Debian 13.6 "trixie". Not OpenWrt, by
   decision. Not testing or unstable.
2. **The lint toolchain**, until `tools/lint.sh` skips nothing. See above.
3. **`batctl`, `iw`, `tcpdump`, `iputils-arping`** for the network plane work.
4. **Git identity, Conventional Commits and a `Signed-off-by` line.** See
   `CONTRIBUTING.md`. A `Refs:` trailer is required only where a change adds or
   removes a decision citation in code.

## Four things to check before you build anything

This is the highest-value hour available on this machine. Every item below is a
fact this repository currently holds from a single Ubuntu Azure kernel used by
GitHub hosted runners, which is not the baseline operating system.

**1. Does the stock Debian kernel carry `batman-adv`?**

```sh
modinfo batman-adv
```

`os/image/manifest/packages.list` records that it is absent from a stock cloud
kernel's base module set and ships on Ubuntu in `linux-modules-extra`. Debian
has no such package. Either answer is a finding, and it belongs in that file.

**2. Does the stock Debian kernel support `BATMAN_V`? This one is
load-bearing.**

```sh
sudo modprobe batman-adv
sudo batctl routing_algo          # lists the algorithms actually available
```

`FML-ADR-053` makes BATMAN-IV the baseline, and one half of its argument is
that `BATMAN_V` is simply not compiled into the stock kernel:

```text
batman_adv: Routing algorithm 'BATMAN_V' is not supported
```

That was observed on the Ubuntu Azure kernel. If Debian's kernel enables
`CONFIG_BATMAN_ADV_BATMAN_V`, the availability half of that argument does not
hold on the baseline operating system, and the ADR needs revisiting on the
record.

**Record the finding. Do not switch.** `FML-ADR-053` is a
`SELECTED PLANNING BASELINE` and its fallback names two criteria, both owned by
`TBR-RF-01`: evidence of a usable driver throughput estimate, **and**
demonstrably poor BATMAN-IV path selection. Availability alone is neither.

**3. Do the module and `batctl` versions agree?**

```sh
modinfo batman-adv | grep ^version
batctl -v
```

CI ran module `2025.3` against batctl `2024.0`. `FML-ADR-040` makes the kernel
module, the driver, the firmware and the required userspace one compatibility
set, versioned and promoted together. A mismatch is data for `os/kernel/PINS.md`,
not a nuisance to work around.

**4. Does `mac80211_hwsim` exist?**

```sh
modinfo mac80211_hwsim
```

It is the gate on roadmap item 1.6. If it is present, 802.11s becomes testable
for the first time in this program.

Record each answer where it belongs — `packages.list`, `os/kernel/PINS.md`, or
an ADR — not in a chat reply. A finding that lives only in a conversation is
lost the moment the session ends.

## What is already established, and exactly what it rests on

Everything below is `SIMULATED`. The basis column is there so you neither
re-derive it nor over-trust it.

| Established | Basis |
| --- | --- |
| A three-node batman-adv mesh forms and routes two hops | `veth` in network namespaces, hosted CI, `.github/workflows/mesh-probe.yml` |
| ARP resolves across the mesh unaided, caches deleted | Same run, asserted rather than printed |
| Warm-up is 2.150s at one hop, 4.391s at two | Same, and asserted on every run against a ten second bound |
| Bridge loop avoidance was the entire warm-up | 31.5s against 2.150s, one variable, both legs of one run, `FML-ADR-054` |
| Hard interface MTU is 1560 | The kernel names the figure on every interface add |
| `BATMAN_V` is unavailable | One kernel, not the baseline one. See check 2 above. |

The link layer in every one of those is a `veth` pair: a perfect wire, with no
propagation, loss, contention, rate adaptation, desense or range. Every quantity
`TBR-RF-01`, `TBR-RF-02` and `TBR-RF-03` exist to measure is absent.

## Where things stand in git

`main` carries pull requests 1 and 2. Both are merged and closed.

A merged pull request cannot track new work and must not be reused. New work
goes on a new branch and gets a new pull request. The Lint workflow triggers on
`pull_request`, so work pushed to a branch with no open pull request runs no CI
at all; do not read a quiet Actions tab as a green one.

## How not to waste the session

`docs/ROADMAP-DEV.md` has a section called "How this program actually gets
things wrong". It is six real failures from this repository, and a new
contributor will make them again. Read it; it is shorter than the time it saves.

One addition applies only on a real machine. **Your machine has state between
commands and a CI job does not.** A test can pass because of a `modprobe`, an
`ip link`, or an install you did by hand and forgot. That is how a result
becomes unreproducible without anybody noticing.

Anything that has to hold belongs in a script, a systemd unit, or a test
fixture — never in your shell history. When something works, the next step is
to prove it works from nothing.
