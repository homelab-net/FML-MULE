# Roadmap

## Why this file is short

A large, well-governed structure that runs nothing is how volunteer projects
quietly stop. The governance in this repository is real work and it is worth
having, but it produces nothing a person can point at, and contributors and
authors both need something they can point at.

So the roadmap has **one milestone**, and nothing is scheduled before it.

## `v0.0.1` — one node, one service, reachable from a phone

**The whole milestone:**

> One node. One service. Reachable from a phone. Documented end to end. Built
> by following this repository alone.

That is all. Not two nodes, not a mesh, not the situational-awareness service,
not identity, not rollback. One node, one service, a phone that can reach it.

### Why so small

Every instinct pulls the other way. The mesh is the interesting part; a single
node with no mesh is not what MULE is. That is exactly why the first milestone
must not include it.

A milestone that requires two nodes requires two of everything, and doubles the
hardware needed before anyone sees anything work. A milestone that includes the
mesh depends on `TBR-LINUX-01`, which needs hardware nobody has, which is why it
has not started. A milestone that includes the mission-service plane depends on
`TBR-TAK-01`, which is open.

`v0.0.1` is scoped to what can be finished, so that it is finished.

### Acceptance

`v0.0.1` is done when **someone who did not write the documentation** follows
this repository and reaches a working node. Not when the author thinks it is
ready.

That is the cold start drill in `docs/verification/README.md`, scoped to this
milestone. The participant may not ask questions during the drill; every point
of confusion becomes an issue.

### What it needs

Roughly, and not as a schedule:

- **Hardware, at all.** A compute element and a way to power it. This does not
  need `TBR-HW-01` to have closed: `v0.0.1` needs *a* node, not a *qualified
  block*. Distinguishing those two is what makes the milestone reachable.
- **An image that boots.** The first real exercise of `os/image/`.
- **Conventional Wi-Fi access point only.** No sub-GHz, no mesh, no LoRa. The
  access point is the bearer a phone can already talk to.
- **One service**, running rootless under Podman as a Quadlet unit
  (`FML-ADR-029`), referenced by immutable digest, with a catalog entry.
- **Ingress**, enough that the phone reaches the service by name. The TLS
  question in `services/ingress/README.md` will have to be confronted or
  consciously deferred here.
- **A build guide** that a stranger can follow.

### What it deliberately excludes

- The sub-GHz HaLow bearer and the IP mesh.
- The LoRa plane.
- The TAK-compatible service.
- Identity, mission trust, and admission.
- A/B update and rollback.
- Any qualification of the hardware as a block.
- All four placeholder services, which must not be implemented.

Excluding these is not a claim they are unimportant. They are most of the
program. They are excluded so that something ships.

### What blocks it

`v0.0.1` does not wait on the critical-path trades, which is the point of its
scope. It waits on **a person with a compute element and time**.

That said, `TBR-TAK-01` can be closed in parallel by anyone, with no hardware,
and doing so unblocks a large amount of what comes after. It is the best use of
a contributor who is waiting.

## After `v0.0.1`

**Nothing else is scheduled.** Not vaguely scheduled, not provisionally
scheduled: nothing.

What comes next depends on which trades have closed and who is available, and
writing a sequence now would be inventing a plan rather than recording one. The
order will follow the dependency structure in `docs/trades/README.md`, where
`TBR-HW-01` sits behind almost every other hardware trade.

Ideas that are worth remembering but are not commitments go in
`docs/parking-lot.md`.

## Versioning

`v<MAJOR>.<MINOR>.<PATCH>` as git tags, for repository releases. Image artifacts
are versioned separately, by build date and content hash, because an image is
not an API and a semantic version would imply a compatibility promise the
program cannot make across hardware blocks and region profiles. See
`os/release/README.md`.

`v0.0.1` is a `0.0.x` version deliberately. It promises nothing about stability
and nothing about the interfaces it exercises.
