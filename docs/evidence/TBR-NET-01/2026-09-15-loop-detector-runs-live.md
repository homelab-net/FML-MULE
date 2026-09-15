# The loop detector runs, on a live induced loop (hwsim)

**Tier:** `SIMULATED`. `mac80211_hwsim` models the 802.11 MAC and nothing
physical.

**Date:** 2026-09-15. **Node:** development machine (see `docs/dev-machine.md`),
`6.12.105+deb13-amd64 x86_64`, `batman-adv 2024.2` (`batctl debian-2025.0-2`).
**Configuration:** two `mac80211_hwsim` radios, two network namespaces, 802.11s
mesh (`fml-loop-lab`, 2412 MHz), a `veth` pair as a shared segment, and on both
nodes a bridge holding `bat0` **and** the veth, with `bridge_loop_avoidance 0`
(`FML-ADR-056`) -- the violation, built on purpose, MTU 1560. **Procedure:**
`test/bench/loop-detect.sh`. **Taken by:** Cameron Zobrist.

## What this demonstrates

`FML-ADR-056` disabled `batman-adv`'s bridge loop avoidance and, verifying the
exchange, said the stronger half is "a loop that is deliberately created and then
detected." The companion artifact
`docs/evidence/TBR-NET-01/2026-08-30-loop-detected-on-the-bench.md` did the first
half -- the loop *appeared* -- by reading `batctl transglobal` by hand. This does
the second half: the **detector runs**. `mule/loops.py` (the decision) now has a
concrete reader, `mule/mesh.py` (added this session), and here they run **live**
inside a node namespace over real `batctl`/sysfs, and `loop_signatures` fires.

## Run

```text
== Building the loop (bat0 + a shared veth in one bridge, on both nodes) ==
== Traffic, so the translation table populates on both paths ==
  traffic crossed; giving batman-adv a moment to announce translations
== Detecting the loop live with mule.loops over mule.mesh ==
  signature: own_address_announced_by_a_peer
  mule.loops detected the induced loop from live batctl/sysfs readings

PASS. A deliberate batman-adv loop was induced and detected live by
mule.loops over mule.mesh -- the stronger half of FML-ADR-056 verification.
```

## The reading

`mule/mesh.py:MeshTranslationReadings` turned live `batctl meshif bat0
transglobal` (parsed by `parse_transglobal`) and the node's own addresses from
`/sys/class/net/*/address` into the `(client, originator)` pairs and address set
`mule/loops.py` judges. It fired `own_address_announced_by_a_peer`: one of the
node's own addresses appeared in the table announced by the peer originator,
which means a frame left this node and came back -- the loop `FML-ADR-056`
accepts the risk of, now visible rather than inferred from a dead mesh.

The single-step case holds first: the two nodes exchanged traffic before the
detector was trusted, so a fired signature is not being read off a mesh that
never carried anything.

## What it is not

- **Not RF.** `hwsim` has no medium; the loop is a bridging/topology loop, and
  the demonstration is that the detector reads it, not anything physical.
- **Not a proof that a signature always means a loop.** `mule/loops.py` is
  explicit that a signature is a "look", not a diagnosis (a roamed client is an
  innocent explanation for the other signature). Here we know a loop exists
  because we built one; the point is the detector fires on it.
- **Not the operator-facing surface.** Turning a signature into something an
  operator sees is the status aggregator (`FML-ADR-046`), gated separately; this
  is the reader and the decision, not the presentation.
- **Not a `batman-adv` timing statement.** The table is a snapshot; ageing and
  stale entries are real, which is why `mule/loops.py` treats a signature as a
  prompt to look.

## Cross-references

- `mule/mesh.py` (the reader), `mule/loops.py` (the decision),
  `test/bench/loop-detect.sh` (the procedure).
- `docs/evidence/TBR-NET-01/2026-08-30-loop-detected-on-the-bench.md` -- the
  companion "loop appears" half.
- `docs/adr/FML-ADR-056-what-may-share-a-bridge-with-the-mesh-interface.md` --
  the decision that disabled loop avoidance and asked for this detector.
- `docs/readings.md` (Translation table) -- the two readings, now `READER`.

Nothing real: no deployment location, member identity, callsign, credential, or
operational capture. The MACs, addresses and mesh id are bench values. See
`SECURITY.md`.
