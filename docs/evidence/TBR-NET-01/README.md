# Evidence for TBR-NET-01

**Trade:** Field address prefix

**Trade file:** `docs/trades/TBR-NET-01-field-address-prefix.md`

**Priority:** 15 of 16 (SAD v0.31 section 30.2). **Function owner:** Network.
**Named owner:** `TBD-SRR`.

**Current contents:** three artifacts. The trade is still `OPEN`: one of its
three closure-evidence items is supplied, and the decision itself is not made.

- `2026-08-30-loop-detected-on-the-bench.md`
- `2026-08-30-collision-exercise.md` -- two deployments sharing
  `10.41.0.0/16`. They conflict silently: one wins ARP, the loser sees a
  `REACHABLE` neighbour it cannot reach, and nothing reports it.
- `2026-08-30-distinct-prefix-exercise.md` -- two deployments with different
  prefixes. They coexist on one mesh and do not interoperate, failing loudly
  with `Network is unreachable`; one on-link route per side restores both
  unicast and ATAK-style multicast.

- `2026-08-30-mesh-id-separates-deployments.md` -- the default case, which the
  two above assumed away. `mesh_id` is a required mission-package field and the
  schema says network identity differs between deployments, so two deployments
  do **not** share a mesh by default. With different `mesh_id`, identical
  prefixes and identical host addresses are harmless.

- `2026-08-31-external-network-collision-analysis.md` -- the collision analysis
  over expected external networks. Any external route more specific than the
  mesh `/16` silently takes that slice of the mesh away, and the rest keeps
  working. A Tailscale subnet router advertising a `/17` takes half of it. The
  failure is not a property of `10.41.0.0/16`, so **selecting a different prefix
  cannot remove it**.

- `2026-08-31-no-routing-mechanism-fixes-an-ambiguous-address.md` -- the four
  candidate mechanisms, measured. Policy routing **moves** the loss rather than
  removing it; only a VRF separates the two networks, per application, and no
  application sees both. `10.41.5.7` is claimed by two networks and no routing
  rule can disambiguate it. Reproduced by `test/bench/route-isolation.sh`.

- `2026-08-31-the-option-the-trade-does-not-list.md` -- the trade's two stated
  options are both IPv4 and the option space is incomplete. RFC 4193 ULAs are
  the standard written for this exact question, and a venue handing out IPv4
  cannot claim an `fd00::/8` destination, so the route-stealing failure does not
  arise. Gated by SAD section 4.4 behind a parent-baseline change request, which
  the README says does not block MULE work. **Deciding question, untested:**
  whether the applications work over IPv6.

**All three closure-evidence items now exist.** The trade is still `OPEN`: it
closes when a named owner accepts the evidence and the resulting decision is
entered in the ADR register, and no decision has been made. The schema question
is reported rather than answered, and the third artifact argues that the
trade's question as written cannot be answered in a way that removes the risk
it is about.

**Read them in that order.** The collision is not what happens when two
deployments meet; it is what happens once they deliberately converge on one
mesh identifier, which is the only mechanism the architecture offers for
cooperating. Nothing in the repository decides how that convergence happens,
and `mesh_id` is the subject of no trade and no ADR.

This directory exists before the work does, deliberately. The closure gate is
written in the trade file before evidence is gathered, so the result cannot be
graded against a standard invented after seeing it.

## What belongs here

Read the **Closure evidence** and **Closure gate** sections of the trade file
named above. Those sections are transcribed from the SAD and are authoritative;
this file does not restate them, so that the two cannot drift apart.

Every artifact follows the naming and recording rules in
`docs/evidence/README.md`:

- `YYYY-MM-DD-<what>-<node-or-configuration>.<ext>`
- Measurements record instrument, date, node, image build, configuration,
  ambient conditions, and who took them.
- Vendor datasheets go in `datasheets/` with a `.SOURCE.md` recording the
  URL, retrieval date, and document revision. Archive them when you cite them;
  vendors delete PDFs. SAD section 34 is the program's external source register.
- Nothing real: no deployment location, member identity, callsign, credential,
  or operational capture. Strip photograph metadata. See `SECURITY.md`.

**Requires hardware:** No. The scheme can be analysed and the collision case exercised with virtual

## Closing

Evidence here is necessary and not sufficient. SAD section 30.2: a TBR closes
only when its listed evidence exists, **the named owner accepts the evidence**,
and the resulting architecture decision is entered into the persistent ADR
register.

Closing a trade whose named owner is still `TBD-SRR` is not possible, because
there is nobody to accept the evidence.
