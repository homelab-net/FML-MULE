# What the lab's recovery policy actually is, and where the repository disagrees

**Trade:** `TBR-HA-01`.
**Date:** 2026-10-02.
**Taken by:** Repository agent, read-only over SSH, on `pi-mule-1` and
`pi-mule-2`.
**Status of this artifact:** real-hardware observation of **service** behaviour.
It is **not** a fault injection, **not** a controlled experiment, and it closes
nothing. One failure class occurred by itself and was observed after the fact.

## Why this exists

`docs/evidence/TBR-HA-01/2026-10-02-supervised-recovery-three-nodes.md` records
that the recovery behaviour it measured rested on "private prototype
configuration; not installed by a fresh main checkout". That tells a reader the
configuration exists. It does not tell them **what it is**, so nobody reviewing
the recovery times could say what produced them, and a future fault injection
would measure an unnamed mechanism and attribute the result to this repository.

This artifact publishes the mechanism. It also records where the deployed
articles have drifted from the repository, because evidence taken on a node that
differs from `main` is uninterpretable until the difference is written down.

## The deployed recovery policy

Thirteen systemd drop-in files per node, in three families, under
`~/.config/systemd/user/<unit>.service.d/`. Identical on both Pis.

**`90-prototype-recovery.conf`** — on `cot-parser`, `eud-handler`, `martin`,
`opentakserver`, `postgresql`, `rabbitmq`:

```ini
[Unit]
StartLimitIntervalSec=infinity
StartLimitBurst=5
[Service]
Restart=always
RestartSec=10s
RestartMode=direct
```

**`91-broker-dependents.conf`** — on `cot-parser`, `eud-handler`,
`opentakserver`:

```ini
[Unit]
BindsTo=rabbitmq.service
After=rabbitmq.service
PartOf=opentakserver.target
```

**`92-target-membership.conf`** — on `martin`, `postgresql`, `rabbitmq`:

```ini
[Unit]
PartOf=opentakserver.target
```

**The policy is bounded, and that is the part worth noticing.**
`Restart=always` on its own is the loop `services/service-controller/README.md`
names as the failure mode ("A single service fault becomes total node loss").
Paired with `StartLimitIntervalSec=infinity` and `StartLimitBurst=5`, the burst
window never resets, so the unit is permitted **five restarts ever** and then
stops permanently. That is a terminating policy, not a loop.

## It fired on its own, and held

`pi-mule-1`, observed 2026-10-02 22:47 MDT:

| Unit | ActiveState | Result | NRestarts |
| --- | --- | --- | ---: |
| `cot-parser` | **failed** | `start-limit-hit` | **5** |
| `rabbitmq` | active | success | 0 |
| `postgresql` | active | success | 0 |
| `opentakserver` | active | success | 0 |
| `eud-handler` | active | success | 0 |
| `martin` | active | success | 0 |

`cot-parser` last entered active at 11:41:35 MDT and inactive at 11:42:10 MDT.
It restarted exactly `StartLimitBurst` times, gave up, and **reported the
failure** rather than continuing. Eleven hours later systemd was still refusing
to start it — `rabbitmq.service` carries
`Upholds=opentakserver.service eud-handler.service cot-parser.service` and the
journal shows the refusal repeating: *"Unit needs to be started because active
unit rabbitmq.service upholds it, but not starting since we tried this too often
recently."* So the give-up is **enforced against continuous pressure**, not a
transient state nobody retried.

Every sibling unit stayed up with zero restarts, and the host kept its default
route on `eth0`.

`pi-mule-2` is a matched control: same hardware, same image, same thirteen
drop-ins, `cot-parser` `active`/`running`, `NRestarts=0`, `Result=success`.

## What this supports, and what it does not

`TBR-HA-01`'s closure gate asks, first, that "the node either recovers the
service or **stops trying and reports that it has**, and in all cases the
network plane retains its mesh links", with "evidence that the restart policy
terminates rather than looping".

**Supported:** on this article, for this one failure, the policy terminated,
reported, and did not take the rest of the service plane or the host's
networking with it.

**Not supported, and the list matters more than the result:**

- **This was not an injected fault.** It happened; it was found afterwards. The
  gate requires five named failure classes — crash, memory exhaustion, storage
  exhaustion, dependency unavailable, starts-but-never-healthy — each injected
  deliberately. This is none of them by design, and which one it resembles is
  unknown.
- **The root cause is unrecoverable.** The user journal retains no entries for
  the unit, so why `cot-parser` failed at 11:41 is gone. An observation whose
  cause is unknown cannot be mapped to a failure class.
- **"Retains its mesh links" is untested.** There is no mesh on this node. The
  default route survived on Ethernet, which is a weaker statement about a
  different thing.
- **One sample, one unit, one node.** `pi-mule-2` did not fail, so there is no
  repetition and no distribution.
- **No reason code.** `FML-ADR-046`'s `NO_SAFE_AUTHORITY` and the rest of the
  give-up vocabulary are not emitted by anything here; systemd's
  `start-limit-hit` is a systemd state, not the operator-facing reason the trade
  asks for.
- **Split-brain, partition and rejoin are untouched**, and need radios.

**The trade remains open.** This narrows what a future injection has to
establish; it does not substitute for it.

## Where the articles differ from the repository

`services/quadlets/martin.container`, repository against both Pis:

| Line | Repository | Deployed |
| --- | --- | --- |
| `Volume=` | `/var/lib/fml/maps/mission.mbtiles` | `/home/mule_admin/mule-prototype/state/maps/mission.mbtiles` |
| `ExecStartPre=` | `/usr/bin/test -r /var/lib/fml/maps/...` | `...test -r /home/mule_admin/.../state/maps/...` |
| `[Install]` | **absent** | `WantedBy=default.target` |

Three consequences:

1. **Deploying the repository's unit onto either Pi stops Martin.**
   `/var/lib/fml` does not exist on either node, so `ExecStartPre` fails closed.
   `test/unit/test_martin_quadlet.py` pins the repository path, so the test and
   the running article disagree.
2. **`/var/lib/fml` is a system path and the unit is rootless.** A user-session
   quadlet cannot create it without root. Whether the repository's path or the
   deployed home-directory path is correct is a real question this artifact does
   not settle; it records that they differ.
3. **The repository's unit has no `[Install]` section**, so the generated
   service belongs to no boot target. On the articles the deployed unit supplies
   one and `loginctl enable-linger` is set for `mule_admin`, which is why Martin
   starts on boot there and would not from a fresh checkout.

The thirteen drop-ins have **no counterpart in the repository at all.**

## What a reader must not conclude

- Not that `TBR-HA-01` is closer to closing by a measured amount. One
  uninjected failure is not one of the five classes.
- Not that `Restart=always` is selected. It is **deployed**, by a configuration
  this repository did not carry until now, and
  `services/quadlets/martin.container` still records `# No Restart=. TBR-HA-01
  is open.` Publishing what is running is not adopting it.
- Not that the recovery times in
  `2026-10-02-supervised-recovery-three-nodes.md` are now explained. They were
  measured under this policy, which is useful context, but the mapping from
  policy to those numbers is not demonstrated here.
- Nothing about RF, power, thermal, or timing under load.
