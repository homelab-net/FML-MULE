# Real EUD rendering maps sourced from a peer over the mesh (fallback)

**Tier:** `SIMULATED`. A **real** iTAK EUD and **real** HTTP serving, but the
inter-node hop is `mac80211_hwsim` batman-adv with no RF, so nothing here is a
serve rate or a range result.

**Date:** 2026-09-05. **Node:** the live bench host (`docs/dev-machine.md`),
`6.12.105+deb13-amd64`, `batman-adv 2024.2`. **Client:** a real iTAK EUD
(iOS/Darwin) associated to the node's RTL8812AU access point. **Configuration:**
MULE-1 = the host (real AP + an `hwsim` mesh leg in the root namespace, running a
pure `nginx` proxy with no local tiles); MULE-2 = an `hwsim` namespace holding
the tile store and serving `z/x/y`; batman-adv `BATMAN_IV`,
`bridge_loop_avoidance 0` (`FML-ADR-056`). **Procedure:** the persistent bench at
`/home/mule1/mule/` (`mule1-proxy.conf`, MULE-2 `http.server`). **Taken by:**
Cameron Zobrist.

## What this demonstrates

The storage fallback in `services/map/serving-across-the-mesh.md`, with a real
client: an EUD whose serving MULE holds **no tiles** still renders a map, because
that MULE sources every tile from a peer (MULE-2) over the mesh. It also
exercises the design's **"invisible to the EUD"** property -- the EUD kept its
existing map source (`http://<node>/v5/{z}/{x}/{y}.jpg`) unchanged; only what sat
behind that URL on the node changed from a local store to a mesh proxy.

MULE-1's proxy is a pure `proxy_pass` with no tile files of its own, so a `200`
it returns can only be a successful cross-mesh fetch from MULE-2. The local tile
server was stopped for the test window, so during the run the node had **no local
tile source at all**.

## Run

Read live from the proxy's access log (client = the EUD's AP address) and MULE-2's
access log (the cross-mesh fetches), which correlate tile for tile, for example
the EUD's `GET /v5/18/54808/100244.jpg` against MULE-2's `GET /18/54808/100244.png`.

```text
phase              EUD (real iTAK)                MULE-2 (storage node)
working            z18 tiles, HTTP 200            serves the identical tiles over the mesh
MULE-2 killed      fresh pans -> HTTP 502         log frozen; serves nothing
MULE-2 restored    200s resume on scroll          serving again

totals over the run: 982 EUD tile requests
  395 x 200  served across the mesh from MULE-2
  153 x 502  during the kill window (MULE-2 down; nothing local to fall back on)
  remainder  404 for tiles outside this store's coverage (honest miss)
```

The kill test is the decisive part: with MULE-2 stopped, every fresh tile the EUD
requested failed `502` and MULE-2's log did not advance, so the tiles were
genuinely coming from MULE-2 across the mesh and not from any cache or store on
MULE-1. Restoring MULE-2 resumed serving.

## The reading

The fallback transport works with a real client: a storage-less serving node
renders a real EUD's map by sourcing tiles from a peer over batman-adv, and the
capability fails closed and cleanly when the peer leaves. The "invisible to the
EUD" addressing model holds -- the client's source URL never changed.

## What it is not

- **Not the fallback, only its transport.** MULE-1's proxy has a **hardcoded**
  upstream. There is no coverage discovery (which peer holds the area), no holder
  selection, and no failover to a second holder. Those are the open question in
  `serving-across-the-mesh.md`, inside `TBR-MAP-01` scope and touching
  `FML-ADR-049`; none is exercised here.
- **Not the S1-local primary model.** CONOPS section 9.2 makes maps S1-local; the
  primary model is a node serving its **own** repository. This is the
  storage-constrained fallback, which degrades map availability to mesh-path
  availability -- the `502`s during the kill window are exactly that degradation.
- **Not a serve rate, not RF.** The inter-node hop is `hwsim`: no propagation,
  loss or rate adaptation. No byte count or timing here is a real-radio result.
- **Not a store or server selection**, and no CM4 footprint (`TBR-COMP-01`). It
  is one machine, so MULE-2's store shares the host filesystem; the rigor is the
  pure-proxy config, the two correlated logs, and the kill test, not physical
  separation.

## Cross-references

- `services/map/serving-across-the-mesh.md` -- the model this exercises the
  transport half of, and the open discovery/failover question.
- `docs/evidence/TBR-MAP-01/2026-09-05-map-server-over-mesh-hwsim.md` -- the
  hwsim-only `SIMULATED` core (`test/bench/map-server-mesh.sh`).
- `docs/evidence/TBR-MAP-01/2026-09-04-real-eud-offline-map-and-storage.md` -- the
  real-EUD local render and the storage arithmetic.

Nothing real: no deployment location, member identity, callsign, credential, or
operational capture. The imagery is a public metropolitan-area set, the addresses
and the store are bench values, and the EUD is a test device. See `SECURITY.md`.
