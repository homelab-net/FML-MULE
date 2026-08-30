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

```sh
tools/install-deps.sh
```

`.github/workflows/lint.yml` installs all of them and remains the authoritative
list; `install-deps.sh` mirrors it so you do not have to transcribe it by hand,
and `tools/install-deps.sh --check` tells you what is still missing without
installing anything. Until nothing is skipped a green run means nothing, and "a
signal that looks like success" is this repository's signature failure. It is
waiting for you on line one.

## What this machine can do that hosted CI cannot

| Capability | Why CI cannot | Roadmap item |
| --- | --- | --- |
| 802.11s association, via `mac80211_hwsim` | GitHub hosted runners ship no wireless stack at all | 1.7 |
| Real systemd units and boot ordering | No init, no boot | 1.2 |
| Real `iw` and `batctl` against a live mesh | No wireless devices to read | 1.6 |
| Meshtastic on real interfaces rather than a Docker bridge | CI has no radio and no serial | 1.1 |
| The flat-sat, iterated in seconds | Nothing, this is convenience | all |

Item 1.7 is the one that matters. It is blocked in `docs/ROADMAP-DEV.md`
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
2. **The lint toolchain**, until `tools/lint.sh` skips nothing.
   `tools/install-deps.sh` installs it. See above.
3. **`batctl`, `iw`, `tcpdump`, `iputils-arping`** for the network plane work.
   These are still not installed by `tools/install-deps.sh`: it installs what
   checks the repository, and these drive a node.
4. **The LoRa bench**, if you are working that plane:
   `tools/install-deps.sh --only lora`. It installs `docker.io`, the pinned
   `meshtasticd` image and the pinned Meshtastic client into `.venv-lora`.
5. **Git identity, Conventional Commits and a `Signed-off-by` line.** See
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

It is the gate on roadmap item 1.7. If it is present, 802.11s becomes testable
for the first time in this program.

**5. Is there a container runtime, and can it pull by digest?**

```sh
docker run --rm hello-world
```

`.github/workflows/lora-probe.yml` runs `meshtasticd` from an OCI image pinned
by digest, because the daemon is in neither the Debian nor the Ubuntu archive.
Reproducing that probe locally needs a runtime. If Debian's packaging differs
from the runner's, say so in the probe rather than working around it silently.

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
| Bridge loop avoidance was the entire warm-up | 31.5s against 2.150s, one variable, both legs of one run, `FML-ADR-056` |
| Hard interface MTU is 1560 | The kernel names the figure on every interface add |
| `BATMAN_V` is unavailable | One kernel, not the baseline one. See check 2 above. |
| The LoRa plane runs with no radio | Two `meshtasticd` nodes in simulation, a text message asserted across, `.github/workflows/lora-probe.yml` |
| An EUD behind one MULE reaches an EUD behind another | Two hops over `veth`, with a negative control proving the bridge is what carries it, and the far node holding the EUD as a **global** translation-table entry |
| Changing a node's configuration reboots `meshtasticd` | Same probe. The re-exec fails in the container, so the process exits; the probe supervises its nodes for that reason |

The link layer in every one of those is a `veth` pair: a perfect wire, with no
propagation, loss, contention, rate adaptation, desense or range. Every quantity
`TBR-RF-01`, `TBR-RF-02` and `TBR-RF-03` exist to measure is absent.

## The pattern worth copying

Both probes assert rather than print, and the EUD test goes one better: it
carries its **own negative control**. Before the mesh interface joins the
bridge, the run fails if the two EUDs can already reach each other, because a
passing ping afterwards would then prove nothing about the bridge.

`AGENTS.md` requires a new check to be watched failing. That is usually done
once, by hand, and then trusted forever. A check that watches itself fail on
every run is strictly better, costs one extra step, and is the shape to reach
for when you add the next one.

## One thing to read before you touch networking

**The EUD access point is bridged into the mesh's layer 2 domain.** SAD section
4.3 says so directly, and it is the reason peer ATAK multicast traverses the
mesh and clients need no MANET routing awareness. Two MULEs with five EUDs each
are one flat broadcast domain: a frame from one team member to another two
nodes away is a layer 2 path that `batman-adv` forwards.

This was got wrong once, in this repository, by reading `FML-ADR-045` — which
separates *radio functions* — as though it separated layer 2 domains. Two ADRs
were written on the false premise and both are superseded, by `FML-ADR-056` and
`FML-ADR-057`. A validation check was written from the same premise and
forbade the baselined architecture until it was corrected.

So before designing anything that touches the access point, the bridge, or
addressing: read SAD section 4.3 first, then `FML-ADR-056`. They are short and
they settle more than the surrounding ADRs do.

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
