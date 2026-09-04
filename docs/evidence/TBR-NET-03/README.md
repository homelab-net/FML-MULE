# Evidence for TBR-NET-03

**Trade:** How do two deployments converge on one mesh

**Trade file:** `docs/trades/TBR-NET-03-how-do-two-deployments-converge-on-one-mesh.md`

**Current contents:** one artifact. The trade is `OPEN`: this supplies part of
one of its four closure-evidence items and selects nothing.

- `2026-08-30-liaison-routing-exercise.md` -- the routed-liaison option
  exercised end to end. Two deployments on different meshes interoperate
  through one routing node each, with layer 2 never merging, for one route per
  liaison. Withdrawal is instant and contained. **The mesh heals by
  itself and a hand-typed route does not**: 802.11s re-peers, `batman-adv`
  reconverges and the liaisons pass traffic, while the kernel has deleted the
  static route with its interface and does not restore it. A configuration
  management finding, not a networking one. Identical prefixes defeat the option twice over: the
  route cannot be installed, and no address exists that names the other
  deployment.

- `2026-08-30-what-happens-with-no-configuration.md` -- what a node does with
  nothing configured, and what the LoRa bearer does not have. Unconfigured IPv6
  link-local already works and cannot collide, which is a counterexample to the
  trade's claim that every mechanism forces per-deployment prefixes. The
  mission package has no LoRa identity field at all, and two default Meshtastic
  deployments **do** converge: the firmware's compiled-in key is described in
  its own source as `our _public_ default channel that all devices power up on`.
  A node is separated from another deployment on 802.11s and joined to it on
  LoRa at the same time.

- `2026-08-31-a-keyed-mesh-admits-only-key-holders.md` -- the question
  `FML-ADR-060` skipped. On a keyed mesh only credential holders reach `ESTAB`;
  a different key stays at `LISTEN` with 100% loss; and there is one credential
  per mesh, so a captured node means rekeying everyone. `FML-ADR-061`
  supersedes `FML-ADR-060` on the strength of it.

The operator-facing statement and the `THREAT_MODEL.md` assessment are in
`2026-08-31-what-it-discloses-and-what-an-operator-does.md`; the decision is
`FML-ADR-061`; and the statement of what a liaison may forward and who authorises
one is `2026-09-04-what-a-liaison-forwards-and-who-authorises.md`. Every
closure-evidence item is now supplied. What remains is not evidence but the
sequencing gate: the trade's own gate holds that a liaison mechanism is not
accepted while `TBR-NET-01` is open, so acceptance follows `TBR-NET-01`'s closure.

Read the **Closure evidence** and **Closure gate** sections of the trade file
named above. Those sections are authoritative; this file does not restate them,
so that the two cannot drift apart.

Naming and recording rules are in `docs/evidence/README.md`. Nothing real: no
deployment location, member identity, callsign, credential, or operational
capture. See `SECURITY.md`.
